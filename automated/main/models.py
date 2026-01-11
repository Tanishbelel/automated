from django.db import models
from django.contrib.auth.models import User

class FileAnalysis(models.Model):
    PLATFORM_CHOICES = [
        ('general', 'General'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('analyzed', 'Analyzed'),
        ('cleaned', 'Cleaned'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField()
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    risk_score = models.IntegerField(default=0)
    metadata_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} - {self.status}"


class MetadataEntry(models.Model):
    CATEGORY_CHOICES = [
        ('location', 'Location'),
        ('device', 'Device'),
        ('author', 'Author'),
        ('timestamp', 'Timestamp'),
        ('camera', 'Camera'),
        ('software', 'Software'),
        ('other', 'Other'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    file_analysis = models.ForeignKey(FileAnalysis, on_delete=models.CASCADE, related_name='metadata_entries')
    key = models.CharField(max_length=255)
    value = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='low')
    is_removed = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['file_analysis', 'category']),
        ]
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class PlatformRule(models.Model):
    platform = models.CharField(max_length=20, unique=True)
    risky_metadata_keys = models.TextField(default='[]')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Rules for {self.platform}"
    
    def get_risky_keys(self):
        import json
        try:
            return json.loads(self.risky_metadata_keys)
        except:
            return []
    
    def set_risky_keys(self, keys_list):
        import json
        self.risky_metadata_keys = json.dumps(keys_list)