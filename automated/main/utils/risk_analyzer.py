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
        """
        Calculate risk score based on presence of sensitive metadata categories
        and overall metadata exposure.
        """
        if not metadata_entries:
            return 0
        
        # Track categories found
        categories_found = set()
        critical_items = []
        high_items = []
        medium_items = []
        low_items = []
        
        for entry in metadata_entries:
            category = entry.get('category', 'other')
            categories_found.add(category)
            weight = RiskAnalyzer.RISK_WEIGHTS.get(category, 10)
            
            if weight >= 80:
                critical_items.append(category)
            elif weight >= 60:
                high_items.append(category)
            elif weight >= 40:
                medium_items.append(category)
            else:
                low_items.append(category)
        
        # Calculate base score
        risk_score = 0
        
        # Critical metadata has huge impact
        if critical_items:
            risk_score = 85  # Start high if ANY critical metadata exists
            # Add more for multiple critical items
            if len(critical_items) > 1:
                risk_score = min(95, risk_score + (len(critical_items) - 1) * 5)
        
        # High risk metadata
        elif high_items:
            risk_score = 65  # Start at high level
            # Add more for multiple high items
            if len(high_items) > 1:
                risk_score = min(75, risk_score + (len(high_items) - 1) * 3)
        
        # Medium risk metadata
        elif medium_items:
            risk_score = 40  # Medium baseline
            # More medium items = higher risk
            if len(medium_items) > 2:
                risk_score = min(55, risk_score + (len(medium_items) - 2) * 3)
        
        # Only low risk metadata
        elif low_items:
            # Base score depends on how much low-risk metadata
            if len(low_items) > 10:
                risk_score = 25
            elif len(low_items) > 5:
                risk_score = 15
            else:
                risk_score = 10
        
        # Adjust based on total metadata volume
        total_count = len(metadata_entries)
        if total_count > 20:
            # Lots of metadata = more exposure
            risk_score = min(100, risk_score + 5)
        
        return risk_score
    
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
    def get_detailed_risk_info(metadata_entries):
        """
        Provides detailed breakdown of what risky metadata was found.
        """
        if not metadata_entries:
            return {
                'has_location': False,
                'has_personal': False,
                'has_author': False,
                'has_device': False,
                'metadata_count': 0,
                'risk_factors': []
            }
        
        categories = {}
        for entry in metadata_entries:
            category = entry.get('category', 'other')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        risk_factors = []
        
        if 'location' in categories:
            risk_factors.append(f"GPS/Location data ({categories['location']} fields)")
        
        if 'personal' in categories:
            risk_factors.append(f"Personal information ({categories['personal']} fields)")
        
        if 'author' in categories:
            risk_factors.append(f"Author/Creator data ({categories['author']} fields)")
        
        if 'device' in categories:
            risk_factors.append(f"Device information ({categories['device']} fields)")
        
        if 'camera' in categories:
            risk_factors.append(f"Camera/Hardware details ({categories['camera']} fields)")
        
        return {
            'has_location': 'location' in categories,
            'has_personal': 'personal' in categories,
            'has_author': 'author' in categories,
            'has_device': 'device' in categories,
            'has_camera': 'camera' in categories,
            'metadata_count': len(metadata_entries),
            'risk_factors': risk_factors,
            'categories': categories
        }
    
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