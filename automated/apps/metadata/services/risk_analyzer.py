# apps/metadata/services/risk_analyzer.py
from django.conf import settings

class RiskAnalyzer:
    """Analyzes privacy risks based on metadata"""
    
    def __init__(self, metadata):
        self.metadata = metadata
        self.risk_weights = settings.RISK_WEIGHTS
    
    def analyze(self):
        """Calculate risk score and level"""
        risk_score = 0
        risk_factors = []
        
        # Check for GPS data
        if self.metadata.get('gps') and len(self.metadata['gps']) > 0:
            risk_score += self.risk_weights.get('gps', 10)
            risk_factors.append({
                'category': 'GPS Location',
                'severity': 'critical',
                'description': 'File contains GPS coordinates revealing exact location',
                'data': self.metadata['gps']
            })
        
        # Check for camera/device info
        if self.metadata.get('camera') and len(self.metadata['camera']) > 0:
            risk_score += self.risk_weights.get('camera', 5)
            risk_factors.append({
                'category': 'Camera/Device Info',
                'severity': 'medium',
                'description': 'File contains camera or device information',
                'data': self.metadata['camera']
            })
        
        # Check for software info
        if self.metadata.get('software') and len(self.metadata['software']) > 0:
            risk_score += self.risk_weights.get('software', 3)
            risk_factors.append({
                'category': 'Software Info',
                'severity': 'low',
                'description': 'File contains software information',
                'data': self.metadata['software']
            })
        
        # Check for author/creator info
        if self.metadata.get('author') and len(self.metadata['author']) > 0:
            risk_score += self.risk_weights.get('author', 7)
            risk_factors.append({
                'category': 'Author/Creator',
                'severity': 'high',
                'description': 'File contains author or creator information',
                'data': self.metadata['author']
            })
        
        # Check for datetime info
        if self.metadata.get('datetime') and len(self.metadata['datetime']) > 0:
            risk_score += self.risk_weights.get('datetime', 2)
            risk_factors.append({
                'category': 'Date/Time',
                'severity': 'low',
                'description': 'File contains timestamp information',
                'data': self.metadata['datetime']
            })
        
        # Determine risk level
        risk_level = self._calculate_risk_level(risk_score)
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'total_factors': len(risk_factors),
            'has_gps': len(self.metadata.get('gps', {})) > 0,
            'has_camera_info': len(self.metadata.get('camera', {})) > 0,
            'has_author_info': len(self.metadata.get('author', {})) > 0,
            'has_software_info': len(self.metadata.get('software', {})) > 0,
        }
    
    def _calculate_risk_level(self, score):
        """Determine risk level based on score"""
        if score >= 15:
            return 'critical'
        elif score >= 10:
            return 'high'
        elif score >= 5:
            return 'medium'
        elif score > 0:
            return 'low'
        else:
            return 'none'
    
    def get_recommendations(self, risk_level):
        """Get recommendations based on risk level"""
        recommendations = {
            'critical': [
                'DO NOT share this file without removing metadata',
                'GPS coordinates expose your exact location',
                'Remove all metadata before sharing',
                'Consider when and where this file was created'
            ],
            'high': [
                'Remove metadata before sharing on social media',
                'Personal information may be exposed',
                'Use Social Media Safe Mode for platform-specific cleaning'
            ],
            'medium': [
                'Some metadata may reveal information about you',
                'Consider removing metadata for sensitive shares',
                'Safe for most private sharing'
            ],
            'low': [
                'Minimal privacy risk detected',
                'Basic metadata present',
                'Generally safe to share'
            ],
            'none': [
                'No significant metadata detected',
                'File appears clean',
                'Safe to share'
            ]
        }
        
        return recommendations.get(risk_level, [])
    
    def analyze_for_platform(self, platform):
        """Analyze risks specific to a platform"""
        from .platform_rules import PlatformRules
        
        platform_rules = PlatformRules(platform)
        risky_metadata = platform_rules.get_risky_metadata(self.metadata)
        
        platform_risk_score = 0
        platform_factors = []
        
        for category, data in risky_metadata.items():
            if data and len(data) > 0:
                weight = self.risk_weights.get(category, 1)
                platform_risk_score += weight
                platform_factors.append({
                    'category': category,
                    'data': data,
                    'reason': f'Not allowed on {platform}'
                })
        
        return {
            'platform': platform,
            'risk_score': platform_risk_score,
            'risk_level': self._calculate_risk_level(platform_risk_score),
            'risky_metadata': risky_metadata,
            'factors': platform_factors,
        }