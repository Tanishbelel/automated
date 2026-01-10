# apps/metadata/services/platform_rules.py
from django.conf import settings

class PlatformRules:
    """Manages platform-specific metadata rules"""
    
    def __init__(self, platform_name):
        self.platform_name = platform_name.lower() if platform_name else 'general'
        self.rules = settings.PLATFORM_RULES.get(self.platform_name, settings.PLATFORM_RULES['general'])
    
    def get_risky_metadata(self, metadata):
        """
        Returns metadata that should be removed for this platform
        """
        risky_data = {}
        remove_rules = self.rules.get('remove', [])
        
        if 'all' in remove_rules:
            # Remove everything except what's in keep_rules
            keep_rules = self.rules.get('keep', [])
            
            for category in ['gps', 'camera', 'software', 'author', 'datetime']:
                if category not in keep_rules and metadata.get(category):
                    risky_data[category] = metadata[category]
        else:
            # Remove only specified categories
            for category in remove_rules:
                if metadata.get(category):
                    risky_data[category] = metadata[category]
        
        return risky_data
    
    def should_remove_category(self, category):
        """Check if a category should be removed for this platform"""
        remove_rules = self.rules.get('remove', [])
        keep_rules = self.rules.get('keep', [])
        
        if category in keep_rules:
            return False
        
        if 'all' in remove_rules or category in remove_rules:
            return True
        
        return False
    
    def get_platform_info(self):
        """Get information about this platform's rules"""
        return {
            'platform': self.platform_name,
            'remove': self.rules.get('remove', []),
            'keep': self.rules.get('keep', []),
            'description': self._get_platform_description()
        }
    
    def _get_platform_description(self):
        """Get a description of platform's privacy approach"""
        descriptions = {
            'instagram': 'Instagram automatically removes most EXIF data, but it\'s best to clean it yourself',
            'facebook': 'Facebook may retain some metadata. Remove GPS and device info before uploading',
            'twitter': 'Twitter strips some metadata but not all. Remove GPS and author info',
            'linkedin': 'LinkedIn keeps some professional metadata. Remove GPS and device info',
            'general': 'Complete metadata removal for maximum privacy'
        }
        
        return descriptions.get(self.platform_name, 'Platform-specific metadata cleaning')
    
    @staticmethod
    def get_all_platforms():
        """Get list of all supported platforms"""
        return [
            {'name': 'instagram', 'display': 'Instagram', 'icon': '📷'},
            {'name': 'facebook', 'display': 'Facebook', 'icon': '👥'},
            {'name': 'twitter', 'display': 'Twitter/X', 'icon': '🐦'},
            {'name': 'linkedin', 'display': 'LinkedIn', 'icon': '💼'},
            {'name': 'general', 'display': 'General (Remove All)', 'icon': '🔒'},
        ]