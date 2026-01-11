from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import FileAnalysis, MetadataEntry, PlatformRule
from .utils.metadata_extractor import MetadataExtractor
from .utils.risk_analyzer import RiskAnalyzer
from PIL import Image
import io

class MetadataExtractorTests(TestCase):
    
    def create_test_image(self):
        image = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        image.save(img_io, format='JPEG')
        img_io.seek(0)
        return img_io
    
    def test_extract_metadata_from_image(self):
        img_io = self.create_test_image()
        metadata = MetadataExtractor.extract_from_image(img_io)
        self.assertIsInstance(metadata, dict)
    
    def test_categorize_metadata(self):
        category = MetadataExtractor.categorize_metadata('GPSLatitude', '37.7749')
        self.assertEqual(category, 'location')
        
        category = MetadataExtractor.categorize_metadata('Make', 'Canon')
        self.assertEqual(category, 'device')
        
        category = MetadataExtractor.categorize_metadata('Artist', 'John Doe')
        self.assertEqual(category, 'author')


class RiskAnalyzerTests(TestCase):
    
    def test_calculate_risk_score(self):
        metadata_entries = [
            {'category': 'location', 'key': 'GPS', 'value': 'test'},
            {'category': 'author', 'key': 'Artist', 'value': 'test'},
            {'category': 'device', 'key': 'Make', 'value': 'test'},
        ]
        
        risk_score = RiskAnalyzer.calculate_risk_score(metadata_entries)
        self.assertGreater(risk_score, 0)
        self.assertLessEqual(risk_score, 100)
    
    def test_get_risk_level(self):
        self.assertEqual(RiskAnalyzer.get_risk_level('location'), 'critical')
        self.assertEqual(RiskAnalyzer.get_risk_level('author'), 'high')
        self.assertEqual(RiskAnalyzer.get_risk_level('timestamp'), 'low')
    
    def test_get_risk_recommendation(self):
        rec = RiskAnalyzer.get_risk_recommendation(85)
        self.assertEqual(rec['level'], 'critical')
        
        rec = RiskAnalyzer.get_risk_recommendation(25)
        self.assertEqual(rec['level'], 'low')


class FileAnalysisModelTests(TestCase):
    
    def test_create_file_analysis(self):
        analysis = FileAnalysis.objects.create(
            original_filename='test.jpg',
            file_type='image/jpeg',
            file_size=1024,
            platform='instagram'
        )
        self.assertEqual(analysis.status, 'pending')
        self.assertEqual(analysis.risk_score, 0)
    
    def test_metadata_entry_creation(self):
        analysis = FileAnalysis.objects.create(
            original_filename='test.jpg',
            file_type='image/jpeg',
            file_size=1024
        )
        
        entry = MetadataEntry.objects.create(
            file_analysis=analysis,
            key='GPSLatitude',
            value='37.7749',
            category='location',
            risk_level='critical'
        )
        
        self.assertEqual(entry.file_analysis, analysis)
        self.assertEqual(entry.category, 'location')


class APITests(APITestCase):
    
    def setUp(self):
        self.client = APIClient()
        
        PlatformRule.objects.create(
            platform='instagram',
            risky_metadata_keys=['gps', 'location'],
            is_active=True
        )
    
    def create_test_image_file(self):
        image = Image.new('RGB', (100, 100), color='blue')
        img_io = io.BytesIO()
        image.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            'test.jpg',
            img_io.read(),
            content_type='image/jpeg'
        )
    
    def test_health_check(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
    
    def test_analyze_file(self):
        test_file = self.create_test_image_file()
        
        response = self.client.post('/api/analyze/', {
            'file': test_file,
            'platform': 'instagram'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('analysis_id', response.data)
        self.assertIn('risk_score', response.data)
        self.assertIn('metadata_count', response.data)
    
    def test_clean_and_download(self):
        test_file = self.create_test_image_file()
        
        response = self.client.post('/api/clean-download/', {
            'file': test_file,
            'platform': 'general'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_analyses(self):
        response = self.client.get('/api/analyses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_platform_rules(self):
        response = self.client.get('/api/platform-rules/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_invalid_file_type(self):
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'test content',
            content_type='text/plain'
        )
        
        response = self.client.post('/api/analyze/', {
            'file': invalid_file,
            'platform': 'general'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)