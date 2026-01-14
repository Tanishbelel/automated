class RiskAnalyzer:
    
    RISK_WEIGHTS = {
        'location': 90,
        'device': 50,
        'personal': 85,
        'author': 70,
        'timestamp': 30,
        'camera': 20,
        'software': 40,
        'other': 10
    }
    
    @staticmethod
    def get_risk_level(category):
        weight = RiskAnalyzer.RISK_WEIGHTS.get(category, 10)
        
        if weight >= 80:
            return 'critical'
        elif weight >= 60:
            return 'high'
        elif weight >= 40:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def calculate_risk_score(metadata_entries):
        if not metadata_entries:
            return 0
        
        total_weight = 0
        for entry in metadata_entries:
            category = entry.get('category', 'other')
            weight = RiskAnalyzer.RISK_WEIGHTS.get(category, 10)
            total_weight += weight
        
        max_possible_score = len(metadata_entries) * 90
        
        if max_possible_score == 0:
            return 0
        
        risk_score = int((total_weight / max_possible_score) * 100)
        return min(risk_score, 100)
    
    @staticmethod
    def get_risk_recommendation(risk_score):
        if risk_score >= 75:
            return "Critical Risk: This file contains highly sensitive metadata including location data or personal information. We strongly recommend removing all metadata before sharing."
        elif risk_score >= 50:
            return "High Risk: This file contains metadata that could reveal sensitive information about you or your device. Consider removing metadata before sharing publicly."
        elif risk_score >= 25:
            return "Medium Risk: This file contains some metadata that might reveal information about when and how it was created. Review the metadata and decide if you want to remove it."
        else:
            return "Low Risk: This file contains minimal metadata. The information present is generally not sensitive, but you can still remove it for extra privacy."
    
    @staticmethod
    def get_platform_risky_keys(platform='general'):
        platform_rules = {
            'instagram': ['GPSInfo', 'GPS', 'location', 'Make', 'Model'],
            'facebook': ['GPSInfo', 'GPS', 'location', 'Author', 'Copyright'],
            'twitter': ['GPSInfo', 'GPS', 'location', 'Software'],
            'linkedin': ['GPSInfo', 'GPS', 'location', 'Author'],
            'general': ['GPSInfo', 'GPS', 'location', 'Author', 'Copyright', 'Make', 'Model']
        }
        
        return platform_rules.get(platform, platform_rules['general'])