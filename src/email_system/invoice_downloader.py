"""
Invoice Downloader
==================

Simulates downloading invoices from Polaroo property details pages.
In offline mode, this creates mock invoice data and URLs.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json
from pathlib import Path
from src.pdf_storage import pdf_storage

logger = logging.getLogger(__name__)

class InvoiceDownloader:
    """Downloads electricity and water invoices from Polaroo property details."""
    
    def __init__(self, offline_mode: bool = True, storage_path: str = "_debug/invoices"):
        """
        Initialize the invoice downloader.
        
        Parameters
        ----------
        offline_mode : bool
            If True, creates mock invoices instead of downloading from Polaroo
        storage_path : str
            Path to store downloaded invoices
        """
        self.offline_mode = offline_mode
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.downloaded_invoices = {}  # Store invoice metadata in memory
    
    def download_invoices_for_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download electricity and water invoices for a property.
        
        Parameters
        ----------
        property_data : dict
            Property data including name, codes, etc.
            
        Returns
        -------
        dict
            Invoice download results with URLs and metadata
        """
        try:
            property_name = property_data.get('name', 'Unknown Property')
            property_id = property_data.get('id', str(uuid.uuid4()))
            
            logger.info(f"Downloading invoices for property: {property_name}")
            
            if self.offline_mode:
                return self._create_mock_invoices(property_data)
            else:
                return self._download_real_invoices(property_data)
                
        except Exception as e:
            logger.error(f"Error downloading invoices for property {property_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'electricity_invoice': None,
                'water_invoice': None
            }
    
    def _create_mock_invoices(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create mock invoices for offline testing.
        
        Parameters
        ----------
        property_data : dict
            Property data
            
        Returns
        -------
        dict
            Mock invoice data
        """
        property_name = property_data.get('name', 'Unknown Property')
        property_id = property_data.get('id', str(uuid.uuid4()))
        
        # Create mock invoice data
        now = datetime.now()
        invoice_id = str(uuid.uuid4())
        
        # Mock electricity invoice
        elec_invoice = {
            'id': f"elec_{invoice_id}",
            'type': 'electricity',
            'property_name': property_name,
            'property_id': property_id,
            'amount': property_data.get('elec_cost', 0.0),
            'consumption': property_data.get('elec_consumption', 0.0),
            'provider': property_data.get('electricity_provider', 'Gana Energía'),
            'code': property_data.get('elec_code', ''),
            'period': f"{now.strftime('%B %Y')}",
            'file_path': f"{self.storage_path}/elec_{property_id}_{now.strftime('%Y%m%d')}.pdf",
            'download_url': f"/api/invoices/elec_{invoice_id}",
            'created_at': now.isoformat(),
            'expires_at': (now + timedelta(minutes=10)).isoformat()  # 10-minute expiry
        }
        
        # Mock water invoice
        water_invoice = {
            'id': f"water_{invoice_id}",
            'type': 'water',
            'property_name': property_name,
            'property_id': property_id,
            'amount': property_data.get('water_cost', 0.0),
            'consumption': property_data.get('water_consumption', 0.0),
            'provider': property_data.get('water_provider', 'Aigües de Barcelona'),
            'code': property_data.get('water_code', ''),
            'period': f"{now.strftime('%B %Y')}",
            'file_path': f"{self.storage_path}/water_{property_id}_{now.strftime('%Y%m%d')}.pdf",
            'download_url': f"/api/invoices/water_{invoice_id}",
            'created_at': now.isoformat(),
            'expires_at': (now + timedelta(minutes=10)).isoformat()  # 10-minute expiry
        }
        
        # Create mock PDF files and upload to Supabase
        elec_pdf_data = self._create_mock_pdf_content(elec_invoice)
        water_pdf_data = self._create_mock_pdf_content(water_invoice)
        
        # Upload to PDF storage
        elec_upload = pdf_storage.upload_pdf(
            file_data=elec_pdf_data,
            filename=f"elec_{property_id}_{now.strftime('%Y%m%d')}.pdf",
            property_name=property_name,
            invoice_type="electricity"
        )
        
        water_upload = pdf_storage.upload_pdf(
            file_data=water_pdf_data,
            filename=f"water_{property_id}_{now.strftime('%Y%m%d')}.pdf",
            property_name=property_name,
            invoice_type="water"
        )
        
        # Update invoice metadata with storage info
        if elec_upload.get('success'):
            elec_invoice['storage_info'] = elec_upload
            elec_invoice['download_url'] = elec_upload.get('public_url', elec_invoice['download_url'])
        
        if water_upload.get('success'):
            water_invoice['storage_info'] = water_upload
            water_invoice['download_url'] = water_upload.get('public_url', water_invoice['download_url'])
        
        # Store invoice metadata
        invoice_data = {
            'property_name': property_name,
            'property_id': property_id,
            'electricity_invoice': elec_invoice,
            'water_invoice': water_invoice,
            'success': True,
            'created_at': now.isoformat()
        }
        
        self.downloaded_invoices[property_id] = invoice_data
        
        logger.info(f"Created mock invoices for property: {property_name}")
        return invoice_data
    
    def _create_mock_pdf_content(self, invoice_data: Dict[str, Any]) -> bytes:
        """
        Create mock PDF content as bytes.
        
        Parameters
        ----------
        invoice_data : dict
            Invoice data to include in the mock file
            
        Returns
        -------
        bytes
            Mock PDF content as bytes
        """
        try:
            # Create a simple text content that simulates a PDF
            mock_content = f"""
MOCK INVOICE - {invoice_data['type'].upper()}
==========================================

Property: {invoice_data['property_name']}
Provider: {invoice_data['provider']}
Code: {invoice_data['code']}
Period: {invoice_data['period']}
Amount: €{invoice_data['amount']:.2f}
Consumption: {invoice_data['consumption']:.2f}

Generated at: {invoice_data['created_at']}
Expires at: {invoice_data['expires_at']}

This is a mock invoice for testing purposes.
In production, this would be a real PDF from the utility provider.
"""
            
            # Convert to bytes (simulating PDF content)
            return mock_content.encode('utf-8')
                
        except Exception as e:
            logger.error(f"Error creating mock PDF content: {e}")
            return b"Mock PDF content error"
    
    def _download_real_invoices(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download real invoices from Polaroo (for production use).
        
        Parameters
        ----------
        property_data : dict
            Property data
            
        Returns
        -------
        dict
            Real invoice data
        """
        try:
            property_name = property_data.get('name', 'Unknown Property')
            property_id = property_data.get('id', str(uuid.uuid4()))
            
            logger.info(f"Downloading real invoices from Polaroo for property: {property_name}")
            
            # Import the real Polaroo scraper
            from src.polaroo_scrape import download_invoices_for_property_sync
            
            # Download invoices using the real scraper
            downloaded_files = download_invoices_for_property_sync(property_name)
            
            if not downloaded_files:
                logger.warning(f"No invoices found for property: {property_name}")
                return {
                    'success': False,
                    'error': 'No invoices found for this property',
                    'electricity_invoice': None,
                    'water_invoice': None
                }
            
            # Process downloaded files and create invoice metadata
            now = datetime.now()
            invoice_id = str(uuid.uuid4())
            
            # Separate electricity and water invoices based on filename or content
            elec_files = []
            water_files = []
            
            for file_path in downloaded_files:
                file_name = Path(file_path).name.lower()
                if 'elec' in file_name or 'electricity' in file_name:
                    elec_files.append(file_path)
                elif 'water' in file_name:
                    water_files.append(file_path)
                else:
                    # If we can't determine type, assume it's electricity
                    elec_files.append(file_path)
            
            # Create electricity invoice metadata and upload to PDF storage
            elec_invoice = None
            if elec_files:
                elec_file = elec_files[0]  # Take the first electricity invoice
                
                # Read the downloaded file and upload to PDF storage
                try:
                    with open(elec_file, 'rb') as f:
                        elec_file_data = f.read()
                    
                    elec_upload = pdf_storage.upload_pdf(
                        file_data=elec_file_data,
                        filename=Path(elec_file).name,
                        property_name=property_name,
                        invoice_type="electricity"
                    )
                except Exception as e:
                    logger.error(f"Error reading electricity file {elec_file}: {e}")
                    elec_upload = {'success': False, 'error': str(e)}
                
                elec_invoice = {
                    'id': f"elec_{invoice_id}",
                    'type': 'electricity',
                    'property_name': property_name,
                    'property_id': property_id,
                    'amount': property_data.get('elec_cost', 0.0),
                    'consumption': property_data.get('elec_consumption', 0.0),
                    'provider': property_data.get('electricity_provider', 'Gana Energía'),
                    'code': property_data.get('elec_code', ''),
                    'period': f"{now.strftime('%B %Y')}",
                    'file_path': elec_file,
                    'download_url': elec_upload.get('public_url', f"/api/invoices/elec_{invoice_id}") if elec_upload.get('success') else f"/api/invoices/elec_{invoice_id}",
                    'created_at': now.isoformat(),
                    'expires_at': (now + timedelta(minutes=10)).isoformat(),
                    'storage_info': elec_upload if elec_upload.get('success') else None
                }
            
            # Create water invoice metadata and upload to PDF storage
            water_invoice = None
            if water_files:
                water_file = water_files[0]  # Take the first water invoice
                
                # Read the downloaded file and upload to PDF storage
                try:
                    with open(water_file, 'rb') as f:
                        water_file_data = f.read()
                    
                    water_upload = pdf_storage.upload_pdf(
                        file_data=water_file_data,
                        filename=Path(water_file).name,
                        property_name=property_name,
                        invoice_type="water"
                    )
                except Exception as e:
                    logger.error(f"Error reading water file {water_file}: {e}")
                    water_upload = {'success': False, 'error': str(e)}
                
                water_invoice = {
                    'id': f"water_{invoice_id}",
                    'type': 'water',
                    'property_name': property_name,
                    'property_id': property_id,
                    'amount': property_data.get('water_cost', 0.0),
                    'consumption': property_data.get('water_consumption', 0.0),
                    'provider': property_data.get('water_provider', 'Aigües de Barcelona'),
                    'code': property_data.get('water_code', ''),
                    'period': f"{now.strftime('%B %Y')}",
                    'file_path': water_file,
                    'download_url': water_upload.get('public_url', f"/api/invoices/water_{invoice_id}") if water_upload.get('success') else f"/api/invoices/water_{invoice_id}",
                    'created_at': now.isoformat(),
                    'expires_at': (now + timedelta(minutes=10)).isoformat(),
                    'storage_info': water_upload if water_upload.get('success') else None
                }
            
            # Store invoice metadata
            invoice_data = {
                'property_name': property_name,
                'property_id': property_id,
                'electricity_invoice': elec_invoice,
                'water_invoice': water_invoice,
                'success': True,
                'created_at': now.isoformat(),
                'downloaded_files': downloaded_files
            }
            
            self.downloaded_invoices[property_id] = invoice_data
            
            logger.info(f"Successfully downloaded {len(downloaded_files)} invoices for property: {property_name}")
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error downloading real invoices for property {property_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'electricity_invoice': None,
                'water_invoice': None
            }
    
    def get_invoice_download_status(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the download status for a property's invoices.
        
        Parameters
        ----------
        property_id : str
            Property ID
            
        Returns
        -------
        dict or None
            Invoice download status
        """
        return self.downloaded_invoices.get(property_id)
    
    def get_invoice_url(self, invoice_id: str) -> Optional[str]:
        """
        Get the download URL for a specific invoice.
        
        Parameters
        ----------
        invoice_id : str
            Invoice ID
            
        Returns
        -------
        str or None
            Invoice download URL
        """
        for property_id, invoice_data in self.downloaded_invoices.items():
            if invoice_data.get('electricity_invoice', {}).get('id') == invoice_id:
                return invoice_data['electricity_invoice']['download_url']
            if invoice_data.get('water_invoice', {}).get('id') == invoice_id:
                return invoice_data['water_invoice']['download_url']
        return None
    
    def cleanup_expired_invoices(self) -> int:
        """
        Clean up expired invoices (older than 10 minutes).
        
        Returns
        -------
        int
            Number of invoices cleaned up
        """
        now = datetime.now()
        expired_properties = []
        
        for property_id, invoice_data in self.downloaded_invoices.items():
            elec_invoice = invoice_data.get('electricity_invoice', {})
            water_invoice = invoice_data.get('water_invoice', {})
            
            # Check if either invoice is expired
            elec_expired = False
            water_expired = False
            
            if elec_invoice.get('expires_at'):
                elec_expires = datetime.fromisoformat(elec_invoice['expires_at'])
                if now > elec_expires:
                    elec_expired = True
            
            if water_invoice.get('expires_at'):
                water_expires = datetime.fromisoformat(water_invoice['expires_at'])
                if now > water_expires:
                    water_expired = True
            
            if elec_expired or water_expired:
                expired_properties.append(property_id)
        
        # Remove expired invoices
        for property_id in expired_properties:
            invoice_data = self.downloaded_invoices[property_id]
            
            # Delete files and clean up PDF storage
            for invoice_type in ['electricity_invoice', 'water_invoice']:
                invoice = invoice_data.get(invoice_type, {})
                
                # Delete local file if it exists
                file_path = invoice.get('file_path')
                if file_path and Path(file_path).exists():
                    try:
                        Path(file_path).unlink()
                        logger.info(f"Deleted expired local invoice file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting local file {file_path}: {e}")
                
                # Delete from PDF storage if it was uploaded
                storage_info = invoice.get('storage_info')
                if storage_info and storage_info.get('success'):
                    object_key = storage_info.get('object_key')
                    if object_key:
                        try:
                            pdf_storage.delete_pdf(object_key)
                            logger.info(f"Deleted expired PDF from storage: {object_key}")
                        except Exception as e:
                            logger.error(f"Error deleting PDF from storage {object_key}: {e}")
            
            # Remove from memory
            del self.downloaded_invoices[property_id]
            logger.info(f"Cleaned up expired invoices for property: {property_id}")
        
        return len(expired_properties)
    
    def get_all_downloaded_invoices(self) -> Dict[str, Any]:
        """
        Get all downloaded invoices.
        
        Returns
        -------
        dict
            All downloaded invoice data
        """
        return self.downloaded_invoices.copy()
    
    def get_invoice_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about downloaded invoices.
        
        Returns
        -------
        dict
            Invoice statistics
        """
        total_properties = len(self.downloaded_invoices)
        total_invoices = total_properties * 2  # Each property has 2 invoices
        
        # Count by type
        elec_count = sum(1 for data in self.downloaded_invoices.values() 
                        if data.get('electricity_invoice'))
        water_count = sum(1 for data in self.downloaded_invoices.values() 
                         if data.get('water_invoice'))
        
        return {
            'total_properties': total_properties,
            'total_invoices': total_invoices,
            'electricity_invoices': elec_count,
            'water_invoices': water_count,
            'storage_path': str(self.storage_path),
            'offline_mode': self.offline_mode
        }
