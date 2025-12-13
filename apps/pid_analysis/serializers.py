from rest_framework import serializers
from .models import PIDDrawing, PIDAnalysisReport, PIDIssue


class PIDIssueSerializer(serializers.ModelSerializer):
    """Serializer for P&ID issues"""
    
    class Meta:
        model = PIDIssue
        fields = [
            'id', 'serial_number', 'pid_reference', 'issue_observed',
            'action_required', 'severity', 'category', 'status',
            'approval', 'remark', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PIDAnalysisReportSerializer(serializers.ModelSerializer):
    """Serializer for P&ID analysis reports"""
    
    issues = PIDIssueSerializer(many=True, read_only=True)
    pid_drawing_number = serializers.CharField(source='pid_drawing.drawing_number', read_only=True)
    
    class Meta:
        model = PIDAnalysisReport
        fields = [
            'id', 'pid_drawing', 'pid_drawing_number', 'total_issues',
            'approved_count', 'ignored_count', 'pending_count',
            'report_data', 'pdf_report', 'excel_report',
            'issues', 'generated_at', 'updated_at'
        ]
        read_only_fields = ['id', 'generated_at', 'updated_at']


class PIDDrawingSerializer(serializers.ModelSerializer):
    """Serializer for P&ID drawings"""
    
    analysis_report = PIDAnalysisReportSerializer(read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = PIDDrawing
        fields = [
            'id', 'file', 'original_filename', 'file_size',
            'drawing_number', 'drawing_title', 'revision', 'project_name',
            'status', 'analysis_started_at', 'analysis_completed_at',
            'uploaded_by', 'uploaded_by_username', 'analysis_report',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_size', 'uploaded_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create PIDDrawing with file metadata"""
        file = validated_data['file']
        validated_data['original_filename'] = file.name
        validated_data['file_size'] = file.size
        return super().create(validated_data)


class PIDDrawingUploadSerializer(serializers.Serializer):
    """Serializer for P&ID drawing upload"""
    
    file = serializers.FileField(
        help_text='P&ID drawing in PDF format',
        required=True
    )
    drawing_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    drawing_title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    revision = serializers.CharField(max_length=20, required=False, allow_blank=True)
    project_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    auto_analyze = serializers.BooleanField(default=True, help_text='Automatically start analysis after upload')
    
    def to_internal_value(self, data):
        """Override to handle FormData boolean strings"""
        # Convert string booleans to actual booleans (FormData sends 'true'/'false' as strings)
        if 'auto_analyze' in data:
            value = data.get('auto_analyze')
            if isinstance(value, str):
                data = data.copy() if hasattr(data, 'copy') else dict(data)
                data['auto_analyze'] = value.lower() in ('true', '1', 'yes')
        
        return super().to_internal_value(data)
    
    def validate_file(self, value):
        """Validate PDF file"""
        if not value:
            raise serializers.ValidationError("File is required")
        
        # Get filename
        filename = getattr(value, 'name', '')
        if not filename:
            raise serializers.ValidationError("File must have a name")
        
        # Check file extension
        if not filename.lower().endswith('.pdf'):
            raise serializers.ValidationError(
                f"Only PDF files are allowed. Received: {filename}"
            )
        
        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        file_size = getattr(value, 'size', 0)
        if file_size > max_size:
            raise serializers.ValidationError(
                f"File size cannot exceed 50MB. Current size: {file_size / (1024*1024):.2f}MB"
            )
        
        if file_size == 0:
            raise serializers.ValidationError("File cannot be empty")
        
        return value


class IssueUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating issue status"""
    
    class Meta:
        model = PIDIssue
        fields = ['status', 'approval', 'remark']
