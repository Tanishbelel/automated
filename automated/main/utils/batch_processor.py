from .metadata_extractor import MetadataExtractor
from .metadata_remover import MetadataRemover
from .risk_analyzer import RiskAnalyzer
from ..models import FileAnalysis, MetadataEntry
from django.db import transaction

class BatchProcessor:
    
    @staticmethod
    def process_multiple_files(files, platform='general', user=None):
        results = []
        
        for file in files:
            try:
                result = BatchProcessor.process_single_file(file, platform, user)
                results.append({
                    'filename': file.name,
                    'status': 'success',
                    'data': result
                })
            except Exception as e:
                results.append({
                    'filename': file.name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
    
    @staticmethod
    @transaction.atomic
    def process_single_file(file, platform, user):
        file_analysis = FileAnalysis.objects.create(
            user=user,
            original_filename=file.name,
            file_type=file.content_type,
            file_size=file.size,
            platform=platform,
            status='pending'
        )
        
        metadata = MetadataExtractor.extract_metadata(file, file.content_type)
        
        metadata_entries = []
        for key, value in metadata.items():
            category = MetadataExtractor.categorize_metadata(key, value)
            risk_level = RiskAnalyzer.get_risk_level(category)
            
            entry = MetadataEntry.objects.create(
                file_analysis=file_analysis,
                key=key,
                value=value,
                category=category,
                risk_level=risk_level
            )
            metadata_entries.append(entry)
        
        metadata_entries_data = [
            {
                'key': e.key,
                'value': e.value,
                'category': e.category,
                'risk_level': e.risk_level
            }
            for e in metadata_entries
        ]
        
        risk_score = RiskAnalyzer.calculate_risk_score(metadata_entries_data)
        
        file_analysis.metadata_count = len(metadata_entries)
        file_analysis.risk_score = risk_score
        file_analysis.status = 'analyzed'
        file_analysis.save()
        
        return {
            'analysis_id': file_analysis.id,
            'risk_score': risk_score,
            'metadata_count': len(metadata_entries)
        }
    
    @staticmethod
    def clean_multiple_files(files):
        cleaned_files = []
        
        for file in files:
            try:
                cleaned = MetadataRemover.remove_metadata(file, file.content_type)
                cleaned_files.append({
                    'filename': file.name,
                    'status': 'success',
                    'file': cleaned
                })
            except Exception as e:
                cleaned_files.append({
                    'filename': file.name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return cleaned_files