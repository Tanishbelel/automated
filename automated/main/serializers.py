from rest_framework import serializers
from .models import FileAnalysis, MetadataEntry, PlatformRule

class MetadataEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataEntry
        fields = ['id', 'key', 'value', 'category', 'risk_level', 'is_removed']


class FileAnalysisSerializer(serializers.ModelSerializer):
    metadata_entries = MetadataEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = FileAnalysis
        fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'platform', 'status', 'risk_score', 'metadata_count',
            'metadata_entries', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'risk_score', 'metadata_count']


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    platform = serializers.ChoiceField(
        choices=['general', 'instagram', 'facebook', 'twitter', 'linkedin'],
        default='general'
    )
    
    def validate_file(self, value):
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 50MB")
        
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif',
            'image/webp', 'image/tiff', 'application/pdf'
        ]
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(f"File type {value.content_type} is not supported")
        
        return value


class MetadataAnalysisResponseSerializer(serializers.Serializer):
    analysis_id = serializers.IntegerField()
    filename = serializers.CharField()
    file_type = serializers.CharField()
    file_size = serializers.IntegerField()
    platform = serializers.CharField()
    risk_score = serializers.IntegerField()
    metadata_count = serializers.IntegerField()
    metadata_entries = MetadataEntrySerializer(many=True)
    risk_recommendation = serializers.DictField()


class CleanFileRequestSerializer(serializers.Serializer):
    analysis_id = serializers.IntegerField()
    remove_all = serializers.BooleanField(default=True)
    metadata_keys = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )


class PlatformRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformRule
        fields = ['id', 'platform', 'risky_metadata_keys', 'description', 'is_active']