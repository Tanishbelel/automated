import io
import os
import tempfile
from django.core.files.base import ContentFile
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # FIXED
from cryptography.hazmat.backends import default_backend
import base64
from PyPDF2 import PdfReader, PdfWriter
import zipfile
import pyminizip


class EncryptionHandler:
    
    @staticmethod
    def generate_key_from_password(password: str, salt: bytes = None) -> tuple:
        """Generate encryption key from password"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(  # FIXED
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def encrypt_file(file_obj, password: str, original_filename: str = None):
        """Encrypt any file with password and store original filename"""
        try:
            file_obj.seek(0)
            file_data = file_obj.read()
            
            # Store original filename (if not provided, use 'file')
            if not original_filename:
                original_filename = 'file'
            
            # Encode filename
            filename_bytes = original_filename.encode('utf-8')
            filename_length = len(filename_bytes).to_bytes(2, 'big')  # 2 bytes for length
            
            # Generate key from password
            key, salt = EncryptionHandler.generate_key_from_password(password)
            
            # Encrypt the file
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(file_data)
            
            # Combine: salt + filename_length + filename + encrypted_data
            output_data = salt + filename_length + filename_bytes + encrypted_data
            
            return ContentFile(output_data)
        
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    @staticmethod
    def decrypt_file(file_obj, password: str):
        """Decrypt file with password and extract original filename"""
        try:
            file_obj.seek(0)
            encrypted_data = file_obj.read()
            
            # Extract salt (first 16 bytes)
            salt = encrypted_data[:16]
            
            # Extract filename length (next 2 bytes)
            filename_length = int.from_bytes(encrypted_data[16:18], 'big')
            
            # Extract filename
            filename_bytes = encrypted_data[18:18+filename_length]
            original_filename = filename_bytes.decode('utf-8')
            
            # Extract encrypted content
            encrypted_content = encrypted_data[18+filename_length:]
            
            # Generate key from password
            key, _ = EncryptionHandler.generate_key_from_password(password, salt)
            
            # Decrypt
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_content)
            
            return ContentFile(decrypted_data), original_filename
        
        except Exception as e:
            raise Exception(f"Decryption failed: Wrong password or corrupted file")
    
    @staticmethod
    def password_protect_pdf(file_obj, password: str):
        """Add password protection to PDF"""
        try:
            file_obj.seek(0)
            pdf_reader = PdfReader(file_obj)
            pdf_writer = PdfWriter()
            
            # Copy all pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Add password protection
            pdf_writer.encrypt(user_password=password, owner_password=password)
            
            # Write to bytes
            output = io.BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            return ContentFile(output.read())
        
        except Exception as e:
            raise Exception(f"PDF password protection failed: {str(e)}")
    
    @staticmethod
    def create_password_protected_zip(file_obj, filename: str, password: str):
        """Create password-protected ZIP file"""
        try:
            file_obj.seek(0)
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix='_input') as temp_input:
                temp_input.write(file_obj.read())
                temp_input_path = temp_input.name
            
            temp_output_path = temp_input_path + '.zip'
            
            try:
                # Create password-protected zip using pyminizip
                compression_level = 5  # 0-9
                pyminizip.compress(
                    temp_input_path,
                    None,  # path prefix
                    temp_output_path,
                    password,
                    compression_level
                )
                
                # Read the encrypted zip
                with open(temp_output_path, 'rb') as f:
                    encrypted_zip = f.read()
                
                return ContentFile(encrypted_zip)
            
            finally:
                # Clean up temporary files
                if os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
        
        except Exception as e:
            raise Exception(f"ZIP encryption failed: {str(e)}")
    
    @staticmethod
    def protect_file(file_obj, filename: str, password: str, method: str = 'encrypt'):
        """
        Main method to protect files with password
        
        Methods:
        - 'encrypt': Universal encryption for any file type
        - 'pdf': Native PDF password protection (PDF files only)
        - 'zip': Create password-protected ZIP archive
        """
        if method == 'pdf' and 'pdf' in filename.lower():
            return EncryptionHandler.password_protect_pdf(file_obj, password)
        elif method == 'zip':
            return EncryptionHandler.create_password_protected_zip(file_obj, filename, password)
        else:
            return EncryptionHandler.encrypt_file(file_obj, password, filename)


class PasswordStrengthValidator:
    """Validate password strength"""
    
    @staticmethod
    def validate_password(password: str) -> dict:
        """Check password strength and return validation result"""
        errors = []
        strength = 0
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        else:
            strength += 1
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        else:
            strength += 1
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            strength += 1
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        else:
            strength += 1
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            errors.append("Password must contain at least one special character")
        else:
            strength += 1
        
        strength_labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong']
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'strength': strength,
            'strength_label': strength_labels[strength]
        }