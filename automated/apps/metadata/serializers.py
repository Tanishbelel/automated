# apps/metadata/serializers.py
from rest_framework import serializers
from .models import FileAnalysis, PlatformRule, ProcessingLog
import json


class FileAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for file analysis results"""
    metadata_before = serializers.SerializerMethodField()
    metadata_after = serializers.SerializerMethodField()
    
    class Meta:
        model = FileAnalysis
        fields = [
            'id', 'file_name', 'file_type', 'file_size',
            'risk_score', 'risk_level',
            'has_gps', 'has_camera_info', 'has_author_info', 'has_software_info',
            'metadata_before', 'metadata_after',
            'target_platform', 'created_at', 'processed', 'processed_at'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at']
    
    def get_metadata_before(self, obj):
        """Convert JSON string to dict"""
        return obj.get_metadata_before()
    
    def get_metadata_after(self, obj):
        """Convert JSON string to dict"""
        return obj.get_metadata_after()


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload and analysis"""
    file = serializers.FileField()
    platform = serializers.CharField(required=False, allow_blank=True)
    
    def validate_file(self, value):
        """Validate uploaded file"""
        from django.conf import settings
        
        # Check file size
        if value.size > settings.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Check file extension
        import os
        ext = os.path.splitext(value.name)[1].lower()
        
        supported_extensions = []
        for formats in settings.SUPPORTED_FILE_FORMATS.values():
            supported_extensions.extend(formats)
        
        if ext not in supported_extensions:
            raise serializers.ValidationError(
                f"File type '{ext}' is not supported. Supported types: {', '.join(supported_extensions)}"
            )
        
        return value


class MetadataAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for metadata analysis response"""
    analysis_id = serializers.UUIDField()
    file_name = serializers.CharField()
    file_type = serializers.CharField()
    file_size = serializers.IntegerField()
    
    # Risk assessment
    risk_score = serializers.IntegerField()
    risk_level = serializers.CharField()
    risk_factors = serializers.ListField()
    recommendations = serializers.ListField()
    
    # Metadata details
    metadata = serializers.DictField()
    
    # Privacy indicators
    has_gps = serializers.BooleanField()
    has_camera_info = serializers.BooleanField()
    has_author_info = serializers.BooleanField()
    has_software_info = serializers.BooleanField()
    
    # Platform specific
    platform = serializers.CharField(required=False, allow_null=True)
    platform_risk = serializers.DictField(required=False)


class MetadataRemovalRequestSerializer(serializers.Serializer):
    """Serializer for metadata removal request"""
    analysis_id = serializers.UUIDField()
    platform = serializers.CharField(required=False, allow_blank=True)


class PlatformRuleSerializer(serializers.ModelSerializer):
    """Serializer for platform rules"""
    remove_rules = serializers.SerializerMethodField()
    keep_rules = serializers.SerializerMethodField()
    
    class Meta:
        model = PlatformRule
        fields = [
            'id', 'platform_name', 'display_name', 'description',
            'remove_rules', 'keep_rules', 'icon_url', 'is_active'
        ]
    
    def get_remove_rules(self, obj):
        """Convert JSON string to list"""
        return obj.get_remove_rules()
    
    def get_keep_rules(self, obj):
        """Convert JSON string to list"""
        return obj.get_keep_rules()


class ProcessingLogSerializer(serializers.ModelSerializer):
    """Serializer for processing logs"""
    
    class Meta:
        model = ProcessingLog
        fields = [
            'id', 'action', 'status', 'message', 
            'error_details', 'processing_time_ms', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class PlatformListSerializer(serializers.Serializer):
    """Serializer for platform list"""
    name = serializers.CharField()
    display = serializers.CharField()
    icon = serializers.CharField()
    description = serializers.CharField(required=False)