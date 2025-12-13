from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import PIDDrawing, PIDAnalysisReport, PIDIssue
from .serializers import (
    PIDDrawingSerializer,
    PIDDrawingUploadSerializer,
    PIDAnalysisReportSerializer,
    PIDIssueSerializer,
    IssueUpdateSerializer
)
from .services import PIDAnalysisService


class PIDDrawingViewSet(viewsets.ModelViewSet):
    """ViewSet for P&ID drawings"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PIDDrawingSerializer
    
    def get_queryset(self):
        """Return drawings for current user"""
        return PIDDrawing.objects.filter(uploaded_by=self.request.user)
    
    def perform_create(self, serializer):
        """Create drawing with current user"""
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload P&ID drawing and optionally start analysis
        
        POST /api/v1/pid/drawings/upload/
        """
        serializer = PIDDrawingUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create PIDDrawing
        file = serializer.validated_data['file']
        drawing = PIDDrawing.objects.create(
            file=file,
            original_filename=file.name,
            file_size=file.size,
            drawing_number=serializer.validated_data.get('drawing_number', ''),
            drawing_title=serializer.validated_data.get('drawing_title', ''),
            revision=serializer.validated_data.get('revision', ''),
            project_name=serializer.validated_data.get('project_name', ''),
            uploaded_by=request.user,
            status='uploaded'
        )
        
        # Auto-analyze if requested
        if serializer.validated_data.get('auto_analyze', True):
            try:
                # Start analysis
                drawing.status = 'processing'
                drawing.analysis_started_at = timezone.now()
                drawing.save()
                
                # Perform analysis
                analysis_service = PIDAnalysisService()
                analysis_result = analysis_service.analyze_pid_drawing(drawing.file.path)
                
                # Create report
                report = PIDAnalysisReport.objects.create(
                    pid_drawing=drawing,
                    report_data=analysis_result,
                    total_issues=len(analysis_result.get('issues', [])),
                )
                
                # Create issues
                for issue_data in analysis_result.get('issues', []):
                    PIDIssue.objects.create(
                        report=report,
                        serial_number=issue_data.get('serial_number', 0),
                        pid_reference=issue_data.get('pid_reference', ''),
                        issue_observed=issue_data.get('issue_observed', ''),
                        action_required=issue_data.get('action_required', ''),
                        severity=issue_data.get('severity', 'observation'),
                        category=issue_data.get('category', ''),
                        status=issue_data.get('status', 'pending'),
                        approval=issue_data.get('approval', 'Pending'),
                        remark=issue_data.get('remark', 'Pending'),
                    )
                
                # Update report summary
                summary = analysis_service.generate_report_summary(analysis_result.get('issues', []))
                report.approved_count = summary['approved_count']
                report.ignored_count = summary['ignored_count']
                report.pending_count = summary['pending_count']
                report.save()
                
                # Update drawing
                drawing.status = 'completed'
                drawing.analysis_completed_at = timezone.now()
                
                # Update drawing metadata from analysis if available
                if 'drawing_info' in analysis_result:
                    drawing_info = analysis_result['drawing_info']
                    if not drawing.drawing_number and drawing_info.get('drawing_number'):
                        drawing.drawing_number = drawing_info['drawing_number']
                    if not drawing.drawing_title and drawing_info.get('drawing_title'):
                        drawing.drawing_title = drawing_info['drawing_title']
                    if not drawing.revision and drawing_info.get('revision'):
                        drawing.revision = drawing_info['revision']
                
                drawing.save()
                
            except Exception as e:
                drawing.status = 'failed'
                drawing.save()
                return Response(
                    {'error': f'Analysis failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Return created drawing
        return Response(
            PIDDrawingSerializer(drawing).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """
        Trigger analysis for a specific drawing
        
        POST /api/v1/pid/drawings/{id}/analyze/
        """
        drawing = self.get_object()
        
        if drawing.status == 'processing':
            return Response(
                {'error': 'Analysis already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Start analysis
            drawing.status = 'processing'
            drawing.analysis_started_at = timezone.now()
            drawing.save()
            
            # Perform analysis
            analysis_service = PIDAnalysisService()
            analysis_result = analysis_service.analyze_pid_drawing(drawing.file.path)
            
            # Delete existing report if any
            if hasattr(drawing, 'analysis_report'):
                drawing.analysis_report.delete()
            
            # Create new report
            report = PIDAnalysisReport.objects.create(
                pid_drawing=drawing,
                report_data=analysis_result,
                total_issues=len(analysis_result.get('issues', [])),
            )
            
            # Create issues
            for issue_data in analysis_result.get('issues', []):
                PIDIssue.objects.create(
                    report=report,
                    serial_number=issue_data.get('serial_number', 0),
                    pid_reference=issue_data.get('pid_reference', ''),
                    issue_observed=issue_data.get('issue_observed', ''),
                    action_required=issue_data.get('action_required', ''),
                    severity=issue_data.get('severity', 'observation'),
                    category=issue_data.get('category', ''),
                    status=issue_data.get('status', 'pending'),
                    approval=issue_data.get('approval', 'Pending'),
                    remark=issue_data.get('remark', 'Pending'),
                )
            
            # Update report summary
            summary = analysis_service.generate_report_summary(analysis_result.get('issues', []))
            report.approved_count = summary['approved_count']
            report.ignored_count = summary['ignored_count']
            report.pending_count = summary['pending_count']
            report.save()
            
            # Update drawing status
            drawing.status = 'completed'
            drawing.analysis_completed_at = timezone.now()
            drawing.save()
            
            return Response(
                PIDDrawingSerializer(drawing).data,
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            drawing.status = 'failed'
            drawing.save()
            return Response(
                {'error': f'Analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """
        Get analysis report for a drawing
        
        GET /api/v1/pid/drawings/{id}/report/
        """
        drawing = self.get_object()
        
        if not hasattr(drawing, 'analysis_report'):
            return Response(
                {'error': 'No analysis report available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            PIDAnalysisReportSerializer(drawing.analysis_report).data,
            status=status.HTTP_200_OK
        )


class PIDAnalysisReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for P&ID analysis reports (read-only)"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PIDAnalysisReportSerializer
    
    def get_queryset(self):
        """Return reports for current user's drawings"""
        return PIDAnalysisReport.objects.filter(
            pid_drawing__uploaded_by=self.request.user
        )


class PIDIssueViewSet(viewsets.ModelViewSet):
    """ViewSet for P&ID issues"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PIDIssueSerializer
    
    def get_queryset(self):
        """Return issues for current user's reports"""
        return PIDIssue.objects.filter(
            report__pid_drawing__uploaded_by=self.request.user
        )
    
    def get_serializer_class(self):
        """Use different serializer for updates"""
        if self.action in ['update', 'partial_update']:
            return IssueUpdateSerializer
        return PIDIssueSerializer
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve an issue
        
        POST /api/v1/pid/issues/{id}/approve/
        """
        issue = self.get_object()
        issue.status = 'approved'
        issue.approval = 'Approved'
        if 'remark' in request.data:
            issue.remark = request.data['remark']
        issue.save()
        
        # Update report counts
        self._update_report_counts(issue.report)
        
        return Response(
            PIDIssueSerializer(issue).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def ignore(self, request, pk=None):
        """
        Ignore an issue
        
        POST /api/v1/pid/issues/{id}/ignore/
        """
        issue = self.get_object()
        issue.status = 'ignored'
        issue.approval = 'Ignored'
        if 'remark' in request.data:
            issue.remark = request.data['remark']
        issue.save()
        
        # Update report counts
        self._update_report_counts(issue.report)
        
        return Response(
            PIDIssueSerializer(issue).data,
            status=status.HTTP_200_OK
        )
    
    def _update_report_counts(self, report):
        """Update report summary counts"""
        issues = report.issues.all()
        report.approved_count = issues.filter(status='approved').count()
        report.ignored_count = issues.filter(status='ignored').count()
        report.pending_count = issues.filter(status='pending').count()
        report.save()
