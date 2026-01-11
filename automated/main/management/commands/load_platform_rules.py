from django.core.management.base import BaseCommand
from main.models import PlatformRule

class Command(BaseCommand):
    help = 'Load default platform rules into database'

    def handle(self, *args, **kwargs):
        platforms = [
            {
                'platform': 'instagram',
                'risky_metadata_keys': [
                    'gps', 'gpsinfo', 'latitude', 'longitude', 'location',
                    'author', 'artist', 'copyright', 'owner', 'creator',
                    'make', 'model', 'software'
                ],
                'description': 'Instagram removes some EXIF but location data is risky'
            },
            {
                'platform': 'facebook',
                'risky_metadata_keys': [
                    'gps', 'gpsinfo', 'latitude', 'longitude', 'location',
                    'author', 'artist', 'copyright', 'owner'
                ],
                'description': 'Facebook strips most EXIF but author info can leak'
            },
            {
                'platform': 'twitter',
                'risky_metadata_keys': [
                    'gps', 'gpsinfo', 'latitude', 'longitude', 'location',
                    'author', 'artist', 'copyright', 'owner', 'creator'
                ],
                'description': 'Twitter removes EXIF but location is critical'
            },
            {
                'platform': 'linkedin',
                'risky_metadata_keys': [
                    'gps', 'gpsinfo', 'latitude', 'longitude', 'location'
                ],
                'description': 'LinkedIn professional context - location most risky'
            },
            {
                'platform': 'general',
                'risky_metadata_keys': [
                    'gps', 'gpsinfo', 'latitude', 'longitude', 'location',
                    'author', 'artist', 'copyright', 'owner', 'creator',
                    'make', 'model', 'software', 'datetime', 'datetimeoriginal'
                ],
                'description': 'General sharing - comprehensive metadata removal'
            }
        ]

        for platform_data in platforms:
            rule, created = PlatformRule.objects.get_or_create(
                platform=platform_data['platform'],
                defaults={
                    'description': platform_data['description'],
                    'is_active': True
                }
            )
            
            rule.set_risky_keys(platform_data['risky_metadata_keys'])
            rule.save()
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created platform rule: {platform_data["platform"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Updated platform rule: {platform_data["platform"]}')
                )