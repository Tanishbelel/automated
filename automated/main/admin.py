from django.contrib import admin
from .models import FileAnalysis, MetadataEntry, PlatformRule

@admin.register(FileAnalysis)
class FileAnalysisAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'file_type', 'platform', 'status', 'risk_score', 'metadata_count', 'is_public', 'created_at']
    list_filter = ['status', 'platform', 'is_public', 'created_at']
    search_fields = ['original_filename', 'user__username', 'share_token']
    readonly_fields = ['created_at', 'updated_at', 'share_token', 'id']
    date_hierarchy = 'created_at'

@admin.register(MetadataEntry)
class MetadataEntryAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'risk_level', 'is_removed', 'file_analysis']
    list_filter = ['category', 'risk_level', 'is_removed']
    search_fields = ['key', 'value']

@admin.register(PlatformRule)
class PlatformRuleAdmin(admin.ModelAdmin):
    list_display = ['platform', 'is_active', 'created_at']
    list_filter = ['is_active', 'platform']
    search_fields = ['platform', 'description']