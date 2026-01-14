from rest_framework import serializers
from .models import FileAnalysis, MetadataEntry, PlatformRule
import json


class MetadataEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MetadataEntry
        fields = ['id', 'key', 'value', 'category', 'risk_level', 'is_removed']


class FileAnalysisSerializer(serializers.ModelSerializer):
    metadata_entries = MetadataEntrySerializer(many=True, read_only=True)
    original_file_url = serializers.SerializerMethodField()
    cleaned_file_url = serializers.SerializerMethodField()
    share_url = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FileAnalysis
        fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'platform', 'status', 'risk_score', 'metadata_count',
            'metadata_entries', 'original_file_url', 'cleaned_file_url',
            'share_token', 'share_url', 'qr_code_url', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'risk_score', 'metadata_count', 'share_token']
    
    def get_original_file_url(self, obj):
        if obj.original_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.original_file.url)
        return None
    
    def get_cleaned_file_url(self, obj):
        if obj.cleaned_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cleaned_file.url)
        return None
    
    def get_share_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/share/{obj.share_token}/')
        return None
    
    def get_qr_code_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/analyses/{obj.id}/qr_code/')
        return None


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


class PlatformRuleSerializer(serializers.ModelSerializer):
    risky_metadata_keys = serializers.SerializerMethodField()
    
    class Meta:
        model = PlatformRule
        fields = ['id', 'platform', 'risky_metadata_keys', 'description', 'is_active']
    
    def get_risky_metadata_keys(self, obj):
        return obj.get_risky_keys()
    
    def create(self, validated_data):
        risky_keys = validated_data.pop('risky_metadata_keys', [])
        instance = PlatformRule.objects.create(**validated_data)
        instance.set_risky_keys(risky_keys)
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        risky_keys = validated_data.pop('risky_metadata_keys', None)
        if risky_keys is not None:
            instance.set_risky_keys(risky_keys)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance