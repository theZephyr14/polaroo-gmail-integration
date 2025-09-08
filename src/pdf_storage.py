"""
PDF Storage Utility
==================

Handles uploading and managing PDF invoices in a separate Supabase bucket.
Provides automatic cleanup and expiry management for invoice files.
"""

import io
import hashlib
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import quote
import logging

from src.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, PDF_BUCKET, PDF_PREFIX, PDF_EXPIRY_MINUTES

logger = logging.getLogger(__name__)

class PDFStorage:
    """Manages PDF invoice storage in Supabase with automatic cleanup."""
    
    def __init__(self):
        """Initialize PDF storage with Supabase configuration."""
        if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, PDF_BUCKET]):
            raise RuntimeError("PDF storage requires SUPABASE_URL, SUPABASE_SERVICE_KEY, and PDF_BUCKET")
        
        self.bucket = PDF_BUCKET
        self.prefix = PDF_PREFIX
        self.expiry_minutes = PDF_EXPIRY_MINUTES
    
    def _md5(self, data: bytes) -> str:
        """Generate MD5 hash for file content."""
        return hashlib.md5(data).hexdigest()
    
    def _infer_content_type(self, filename: str) -> str:
        """Infer content type from filename."""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.csv': 'text/csv',
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def _sanitize_object_key(self, text: str) -> str:
        """Sanitize text for use as object key."""
        # Remove special characters and replace spaces with underscores
        sanitized = text.replace('º', '').replace('ª', '').replace(' ', '_')
        # Remove any other special characters that might cause issues
        import re
        sanitized = re.sub(r'[^\w\-_.]', '', sanitized)
        return sanitized
    
    def upload_pdf(self, 
                   file_data: bytes, 
                   filename: str, 
                   property_name: str,
                   invoice_type: str = "unknown",
                   custom_expiry_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Upload a PDF invoice to Supabase storage.
        
        Parameters
        ----------
        file_data : bytes
            PDF file data
        filename : str
            Original filename
        property_name : str
            Property name for organization
        invoice_type : str
            Type of invoice (electricity, water, etc.)
        custom_expiry_minutes : int, optional
            Custom expiry time in minutes (overrides default)
            
        Returns
        -------
        dict
            Upload result with URL, expiry, and metadata
        """
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            file_hash = self._md5(file_data)[:8]  # Short hash for uniqueness
            
            # Properly sanitize property name for object key
            safe_property = property_name.replace('º', '').replace('ª', '').replace(' ', '_')
            safe_property = "".join(c for c in safe_property if c.isalnum() or c in ('_', '-')).rstrip('_')
            
            # Sanitize filename for object key
            safe_filename = filename.replace('º', '').replace('ª', '').replace(' ', '_')
            safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ('.', '_', '-')).rstrip('_')
            
            # Create organized path structure
            object_key = f"{self.prefix}/{safe_property}/{invoice_type}_{timestamp}_{file_hash}_{safe_filename}"
            
            # Upload to Supabase
            url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/{quote(self.bucket)}/{quote(object_key)}"
            headers = {
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": self._infer_content_type(filename),
                "x-upsert": "true",
            }
            
            response = requests.post(url, headers=headers, data=file_data, timeout=60)
            
            if response.status_code not in (200, 201):
                raise RuntimeError(f"Supabase PDF upload failed [{response.status_code}]: {response.text}")
            
            # Calculate expiry time
            expiry_minutes = custom_expiry_minutes or self.expiry_minutes
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(minutes=expiry_minutes)
            
            # Generate public URL for download
            public_url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{self.bucket}/{object_key}"
            
            result = {
                'success': True,
                'object_key': object_key,
                'public_url': public_url,
                'filename': filename,
                'property_name': property_name,
                'invoice_type': invoice_type,
                'file_size': len(file_data),
                'content_type': self._infer_content_type(filename),
                'created_at': created_at.isoformat(),
                'expires_at': expires_at.isoformat(),
                'expiry_minutes': expiry_minutes,
                'bucket': self.bucket
            }
            
            logger.info(f"Successfully uploaded PDF: {filename} for {property_name} ({invoice_type})")
            return result
            
        except Exception as e:
            logger.error(f"Error uploading PDF {filename}: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename,
                'property_name': property_name
            }
    
    def delete_pdf(self, object_key: str) -> bool:
        """
        Delete a PDF from Supabase storage.
        
        Parameters
        ----------
        object_key : str
            Object key in the bucket
            
        Returns
        -------
        bool
            True if deletion was successful
        """
        try:
            url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/{self.bucket}/{quote(object_key)}"
            headers = {
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            }
            
            response = requests.delete(url, headers=headers, timeout=30)
            
            if response.status_code in (200, 204):
                logger.info(f"Successfully deleted PDF: {object_key}")
                return True
            else:
                logger.warning(f"Failed to delete PDF {object_key}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting PDF {object_key}: {e}")
            return False
    
    def list_expired_pdfs(self) -> list:
        """
        List PDFs that have expired (for cleanup purposes).
        Note: This is a simplified implementation. In production, you might want
        to use Supabase's built-in lifecycle policies or a scheduled job.
        
        Returns
        -------
        list
            List of expired PDF object keys
        """
        # This is a placeholder implementation
        # In a real scenario, you'd query your database or use Supabase's
        # metadata to find expired files
        logger.info("PDF expiry check requested - implement based on your metadata storage")
        return []
    
    def list_pdfs_for_property(self, property_name: str) -> list:
        """
        List all PDFs for a specific property.
        
        Parameters
        ----------
        property_name : str
            Name of the property to find PDFs for
            
        Returns
        -------
        list
            List of PDF info dictionaries with object_key, filename, etc.
        """
        try:
            # Sanitize property name for object key matching
            sanitized_property = self._sanitize_object_key(property_name)
            
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            
            pdfs = []
            
            # Try different possible paths for the property
            possible_paths = [
                f"invoices/{sanitized_property}",
                sanitized_property,
                f"invoices/{sanitized_property}/invoices"
            ]
            
            for path in possible_paths:
                try:
                    # List objects in this path
                    response = supabase.storage.from_(self.bucket).list(path)
                    
                    for obj in response:
                        obj_name = obj.get('name', '')
                        # Check if it's a PDF file
                        if obj_name.lower().endswith('.pdf'):
                            # Create full object key with path
                            full_object_key = f"{path}/{obj_name}" if path else obj_name
                            pdfs.append({
                                'object_key': full_object_key,
                                'filename': obj_name.split('/')[-1],  # Get just the filename
                                'size': obj.get('metadata', {}).get('size', 0),
                                'created_at': obj.get('created_at'),
                                'updated_at': obj.get('updated_at')
                            })
                    
                    # If we found PDFs in this path, we're done
                    if pdfs:
                        break
                        
                except Exception as e:
                    logger.debug(f"Could not list path {path}: {e}")
                    continue
            
            logger.info(f"Found {len(pdfs)} PDFs for property: {property_name}")
            return pdfs
            
        except Exception as e:
            logger.error(f"Error listing PDFs for property {property_name}: {e}")
            return []
    
    def get_pdf_info(self, object_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a stored PDF.
        
        Parameters
        ----------
        object_key : str
            Object key in the bucket
            
        Returns
        -------
        dict or None
            PDF information if found
        """
        try:
            url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/info/{self.bucket}/{quote(object_key)}"
            headers = {
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                info = response.json()
                return {
                    'object_key': object_key,
                    'filename': info.get('name', ''),
                    'size': info.get('metadata', {}).get('size', 0),
                    'content_type': info.get('metadata', {}).get('mimetype', ''),
                    'created_at': info.get('created_at', ''),
                    'updated_at': info.get('updated_at', ''),
                    'bucket': self.bucket
                }
            else:
                logger.warning(f"PDF info not found: {object_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting PDF info for {object_key}: {e}")
            return None
    
    def create_download_url(self, object_key: str, expires_in_minutes: int = 60) -> Optional[str]:
        """
        Create a signed download URL for a PDF.
        
        Parameters
        ----------
        object_key : str
            Object key in the bucket
        expires_in_minutes : int
            URL expiry time in minutes
            
        Returns
        -------
        str or None
            Signed download URL
        """
        try:
            from supabase import create_client
            
            supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            
            # Get the public URL using Supabase client
            public_url = supabase.storage.from_(self.bucket).get_public_url(object_key)
            
            if public_url:
                logger.info(f"Created download URL for {object_key}")
                return public_url
            else:
                logger.warning(f"Could not create download URL for {object_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating download URL for {object_key}: {e}")
            return None

# Global instance for easy access
pdf_storage = PDFStorage()
