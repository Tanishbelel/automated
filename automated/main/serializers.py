from rest_framework import serializers
from .models import FileAnalysis, MetadataEntry, PlatformRule
import json
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.'
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.'
                )
        else:
            raise serializers.ValidationError(
                'Must include "username" and "password".'
            )

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True, 
        write_only=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        
    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    
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