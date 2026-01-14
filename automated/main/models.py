from django.db import models
from django.contrib.auth.models import User
import uuid
import json


class FileAnalysis(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('analyzed', 'Analyzed'),
        ('cleaned', 'Cleaned'),
        ('failed', 'Failed'),
    ]
    
    PLATFORM_CHOICES = [
        ('general', 'General'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    original_file = models.FileField(upload_to='original_files/', null=True, blank=True)
    cleaned_file = models.FileField(upload_to='cleaned_files/', null=True, blank=True)
    file_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    risk_score = models.IntegerField(default=0)
    metadata_count = models.IntegerField(default=0)
    share_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['share_token']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} - {self.status}"


class MetadataEntry(models.Model):
    CATEGORY_CHOICES = [
        ('location', 'Location'),
        ('device', 'Device'),
        ('software', 'Software'),
        ('camera', 'Camera'),
        ('personal', 'Personal'),
        ('temporal', 'Temporal'),
        ('other', 'Other'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    file_analysis = models.ForeignKey(
        FileAnalysis,
        on_delete=models.CASCADE,
        related_name='metadata_entries'
    )
    key = models.CharField(max_length=255)
    value = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES)
    is_removed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-risk_level', 'category']
        verbose_name_plural = 'Metadata entries'
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class PlatformRule(models.Model):
    platform = models.CharField(max_length=50, unique=True)
    risky_metadata_keys = models.TextField(default='[]')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_risky_keys(self):
        try:
            return json.loads(self.risky_metadata_keys)
        except:
            return []
    
    def set_risky_keys(self, keys_list):
        self.risky_metadata_keys = json.dumps(keys_list)
    
    def __str__(self):
        return f"Rules for {self.platform}"