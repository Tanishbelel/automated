import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
import tempfile
from datetime import datetime

from pipeline.orchestrator import run_pipeline

class TestOrchestrator(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory and a dummy file
        self.test_dir = tempfile.mkdtemp()
        self.dummy_file = os.path.join(self.test_dir, "test_image.jpg")
        with open(self.dummy_file, "wb") as f:
            f.write(b"dummy image content")
            
    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    @patch('pipeline.orchestrator.Image.open')
    @patch('pipeline.orchestrator.scan_file_vt')
    @patch('pipeline.orchestrator.MetadataRemover.remove_metadata')
    @patch('pipeline.orchestrator.detect_sensitive_regions')
    @patch('pipeline.orchestrator.redact_image')
    @patch('pipeline.orchestrator.image_to_png_bytes')
    @patch('pipeline.orchestrator.apply_platform_profile')
    @patch('pipeline.orchestrator.inject_signature')
    def test_run_pipeline_happy_path(self, mock_inject, mock_profile, mock_img_to_bytes, mock_redact_img, mock_detect, mock_remove_meta, mock_scan, mock_image_open):
        # Setup mocks
        mock_scan.return_value = {"status": "clean", "threat_name": None}
        
        mock_content_file = MagicMock()
        mock_content_file.read.return_value = b"cleaned image content"
        mock_remove_meta.return_value = mock_content_file
        
        mock_image_open.return_value = MagicMock()
        
        mock_detection = MagicMock()
        mock_detection.label = "PAN"
        mock_detection.confidence = 99.0
        mock_detect.return_value = [mock_detection]
        
        mock_redact_img.return_value = MagicMock()
        mock_img_to_bytes.return_value = b"redacted image content"
        
        mock_profile.return_value = {"stripped": [], "replaced": {"Camera": "Canon EOS R50"}}
        mock_inject.return_value = self.dummy_file
        
        # Run pipeline
        result = run_pipeline(self.dummy_file, platform="instagram")
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result.original_filename, "test_image.jpg")
        self.assertEqual(result.platform_profile_applied, "instagram")
        self.assertIn("GPS", result.fields_removed)
        self.assertEqual(len(result.pii_patterns_found), 1)
        self.assertEqual(result.pii_patterns_found[0]["type"], "PAN")
        self.assertTrue(hasattr(result, 'sha256_hash'))
        
        # Verify calls
        mock_scan.assert_called_once_with(self.dummy_file)
        mock_remove_meta.assert_called_once()
        mock_detect.assert_called_once()
        mock_redact_img.assert_called_once()
        mock_profile.assert_called_once_with(self.dummy_file, "instagram")
        mock_inject.assert_called_once_with(self.dummy_file, {"Camera": "Canon EOS R50"})
        
    @patch('pipeline.orchestrator.scan_file_vt')
    @patch('pipeline.orchestrator.MetadataRemover.remove_metadata')
    def test_run_pipeline_quarantine(self, mock_remove_meta, mock_scan):
        # Setup mocks to return infected
        mock_scan.return_value = {"status": "infected", "threat_name": "EICAR-Test-Signature"}
        
        # Run pipeline
        result = run_pipeline(self.dummy_file)
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "quarantined")
        self.assertEqual(result.get("reason"), "EICAR-Test-Signature")
        
        # Verify that strip_metadata was NEVER called
        mock_remove_meta.assert_not_called()
        
        # Verify file was moved to quarantine
        quarantine_dir = os.path.join(self.test_dir, "quarantine")
        quarantine_path = os.path.join(quarantine_dir, "test_image.jpg")
        self.assertTrue(os.path.exists(quarantine_path))
        self.assertFalse(os.path.exists(self.dummy_file))

if __name__ == '__main__':
    unittest.main()
