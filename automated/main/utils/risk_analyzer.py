class RiskAnalyzer:
    
    RISK_WEIGHTS = {
        'location': 40,
        'device': 20,
        'author': 30,
        'timestamp': 10,
        'camera': 5,
        'software': 15,
        'other': 5,
    }
    
    CATEGORY_RISK_LEVELS = {
        'location': 'critical',
        'author': 'high',
        'device': 'medium',
        'software': 'medium',
        'timestamp': 'low',
        'camera': 'low',
        'other': 'low',
    }
    
    @staticmethod
    def calculate_risk_score(metadata_entries):
        total_score = 0
        
        for entry in metadata_entries:
            category = entry.get('category', 'other')
            weight = RiskAnalyzer.RISK_WEIGHTS.get(category, 5)
            total_score += weight
        
        risk_score = min(100, total_score)
        
        return risk_score
    
    @staticmethod
    def get_risk_level(category):
        return RiskAnalyzer.CATEGORY_RISK_LEVELS.get(category, 'low')
    
    @staticmethod
    def analyze_platform_risk(metadata_entries, platform):
        platform_risky_keys = RiskAnalyzer.get_platform_risky_keys(platform)
        
        risky_entries = []
        for entry in metadata_entries:
            key = entry.get('key', '').lower()
            category = entry.get('category', 'other')
            
            if any(risky_key in key for risky_key in platform_risky_keys):
                risky_entries.append(entry)
            elif category in ['location', 'author']:
                risky_entries.append(entry)
        
        return risky_entries
    
    @staticmethod
    def get_platform_risky_keys(platform):
        platform_rules = {
            'instagram': ['gps', 'location', 'latitude', 'longitude', 'author', 'artist', 'copyright'],
            'facebook': ['gps', 'location', 'latitude', 'longitude', 'author', 'artist'],
            'twitter': ['gps', 'location', 'latitude', 'longitude', 'author', 'artist', 'copyright'],
            'linkedin': ['gps', 'location', 'latitude', 'longitude'],
            'general': ['gps', 'location', 'latitude', 'longitude', 'author', 'artist', 'copyright', 'owner'],
        }
        
        return platform_rules.get(platform, platform_rules['general'])
    
    @staticmethod
    def get_risk_recommendation(risk_score):
        if risk_score >= 75:
            return {
                'level': 'critical',
                'message': 'High privacy risk detected. Remove metadata before sharing.',
                'color': 'red'
            }
        elif risk_score >= 50:
            return {
                'level': 'high',
                'message': 'Significant metadata found. Consider removing before sharing.',
                'color': 'orange'
            }
        elif risk_score >= 25:
            return {
                'level': 'medium',
                'message': 'Some metadata detected. Review before sharing on social media.',
                'color': 'yellow'
            }
        else:
            return {
                'level': 'low',
                'message': 'Minimal metadata detected. Relatively safe to share.',
                'color': 'green'
            }