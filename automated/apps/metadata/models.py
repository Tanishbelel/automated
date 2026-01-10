# apps/metadata/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid
import json

class FileAnalysis(models.Model):
    """Stores file analysis results (temporary, for analytics only)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField()
    
    # Privacy risk assessment
    risk_score = models.IntegerField(default=0)
    risk_level = models.CharField(max_length=20)  # low, medium, high, critical
    
    # Metadata found
    has_gps = models.BooleanField(default=False)
    has_camera_info = models.BooleanField(default=False)
    has_author_info = models.BooleanField(default=False)
    has_software_info = models.BooleanField(default=False)
    
    # Metadata details (stored as JSON text for Python 3.7 compatibility)
    metadata_before = models.TextField(default='{}')
    metadata_after = models.TextField(default='{}', null=True, blank=True)
    
    # Platform specific
    target_platform = models.CharField(max_length=50, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['risk_level']),
        ]
    
    def __str__(self):
        return f"{self.file_name} - {self.risk_level}"
    
    def get_metadata_before(self):
        """Get metadata_before as dict"""
        try:
            return json.loads(self.metadata_before) if self.metadata_before else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_metadata_before(self, data):
        """Set metadata_before from dict"""
        self.metadata_before = json.dumps(data) if data else '{}'
    
    def get_metadata_after(self):
        """Get metadata_after as dict"""
        try:
            return json.loads(self.metadata_after) if self.metadata_after else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_metadata_after(self, data):
        """Set metadata_after from dict"""
        self.metadata_after = json.dumps(data) if data else '{}'


class MetadataCategory(models.Model):
    """Categorizes different types of metadata"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    risk_weight = models.IntegerField(default=1)
    icon = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Metadata Categories"
    
    def __str__(self):
        return self.name


class PlatformRule(models.Model):
    """Platform-specific metadata removal rules"""
    platform_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Rules (stored as JSON text for Python 3.7 compatibility)
    remove_rules = models.TextField(default='[]')
    keep_rules = models.TextField(default='[]')
    
    # Icon/Logo
    icon_url = models.URLField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name
    
    def get_remove_rules(self):
        """Get remove_rules as list"""
        try:
            return json.loads(self.remove_rules) if self.remove_rules else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_remove_rules(self, data):
        """Set remove_rules from list"""
        self.remove_rules = json.dumps(data) if data else '[]'
    
    def get_keep_rules(self):
        """Get keep_rules as list"""
        try:
            return json.loads(self.keep_rules) if self.keep_rules else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_keep_rules(self, data):
        """Set keep_rules from list"""
        self.keep_rules = json.dumps(data) if data else '[]'


class ProcessingLog(models.Model):
    """Logs for debugging and analytics (no file content stored)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_analysis = models.ForeignKey(
        FileAnalysis, 
        on_delete=models.CASCADE, 
        related_name='logs'
    )
    
    action = models.CharField(max_length=100)  # analyze, remove, download
    status = models.CharField(max_length=20)  # success, error
    message = models.TextField(null=True, blank=True)
    error_details = models.TextField(null=True, blank=True)
    
    processing_time_ms = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} - {self.status}"