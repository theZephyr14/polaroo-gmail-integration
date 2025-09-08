"""
Email Generator
==============

Generates personalized emails for utility bill overages using templates
and property-specific data.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .template_manager import TemplateManager

logger = logging.getLogger(__name__)

class EmailGenerator:
    """Generates personalized emails for utility bill overages."""
    
    def __init__(self, template_file: str = "email_templates.xlsx"):
        """
        Initialize the email generator.
        
        Parameters
        ----------
        template_file : str
            Path to the Excel file containing email templates
        """
        self.template_manager = TemplateManager(template_file)
        self.generated_emails = {}  # Store generated emails in memory
    
    def generate_email_for_property(self, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate email for a specific property with overages.
        
        Parameters
        ----------
        property_data : dict
            Property data including name, costs, allowances, etc.
            
        Returns
        -------
        dict or None
            Generated email data with subject, body, and metadata
        """
        try:
            property_name = property_data.get('name', 'Unknown Property')
            
            # Check if property has overages
            total_extra = property_data.get('total_extra', 0.0)
            if total_extra <= 0:
                logger.info(f"No overages for property {property_name}, skipping email generation")
                return None
            
            # Get template for this property
            template_data = self.template_manager.get_template_for_property(property_name)
            if not template_data:
                logger.warning(f"No template found for property: {property_name}")
                return None
            
            # Render the template
            rendered_email = self.template_manager.render_template(template_data, property_data)
            if not rendered_email:
                logger.error(f"Failed to render template for property: {property_name}")
                return None
            
            # Generate unique email ID
            email_id = str(uuid.uuid4())
            
            # Create email data
            email_data = {
                'id': email_id,
                'property_name': property_name,
                'property_data': property_data,
                'email_address': rendered_email['email_address'],
                'subject': rendered_email['subject'],
                'body': rendered_email['body'],
                'template_vars': rendered_email['template_vars'],
                'status': 'generated',
                'created_at': datetime.now().isoformat(),
                'total_extra': total_extra,
                'payment_link': property_data.get('payment_link', 'https://payment.example.com'),
                'electricity_invoice_url': property_data.get('electricity_invoice_url', ''),
                'water_invoice_url': property_data.get('water_invoice_url', '')
            }
            
            # Store in memory
            self.generated_emails[email_id] = email_data
            
            logger.info(f"Generated email for property: {property_name} (ID: {email_id})")
            return email_data
            
        except Exception as e:
            logger.error(f"Error generating email for property {property_name}: {e}")
            return None
    
    def generate_emails_for_overages(self, properties_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate emails for all properties with overages.
        
        Parameters
        ----------
        properties_data : list
            List of property data dictionaries
            
        Returns
        -------
        list
            List of generated email data
        """
        generated_emails = []
        
        for property_data in properties_data:
            email_data = self.generate_email_for_property(property_data)
            if email_data:
                generated_emails.append(email_data)
        
        logger.info(f"Generated {len(generated_emails)} emails for properties with overages")
        return generated_emails
    
    def get_generated_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a generated email by ID.
        
        Parameters
        ----------
        email_id : str
            Email ID
            
        Returns
        -------
        dict or None
            Email data if found
        """
        return self.generated_emails.get(email_id)
    
    def get_all_generated_emails(self) -> List[Dict[str, Any]]:
        """
        Get all generated emails.
        
        Returns
        -------
        list
            List of all generated email data
        """
        return list(self.generated_emails.values())
    
    def update_email_status(self, email_id: str, status: str) -> bool:
        """
        Update the status of a generated email.
        
        Parameters
        ----------
        email_id : str
            Email ID
        status : str
            New status (e.g., 'approved', 'sent', 'failed')
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if email_id in self.generated_emails:
            self.generated_emails[email_id]['status'] = status
            self.generated_emails[email_id]['updated_at'] = datetime.now().isoformat()
            logger.info(f"Updated email {email_id} status to: {status}")
            return True
        else:
            logger.warning(f"Email ID not found: {email_id}")
            return False
    
    def delete_generated_email(self, email_id: str) -> bool:
        """
        Delete a generated email.
        
        Parameters
        ----------
        email_id : str
            Email ID to delete
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if email_id in self.generated_emails:
            del self.generated_emails[email_id]
            logger.info(f"Deleted email: {email_id}")
            return True
        else:
            logger.warning(f"Email ID not found: {email_id}")
            return False
    
    def get_emails_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get emails by status.
        
        Parameters
        ----------
        status : str
            Status to filter by
            
        Returns
        -------
        list
            List of emails with the specified status
        """
        return [email for email in self.generated_emails.values() if email.get('status') == status]
    
    def get_emails_by_property(self, property_name: str) -> List[Dict[str, Any]]:
        """
        Get emails for a specific property.
        
        Parameters
        ----------
        property_name : str
            Property name to filter by
            
        Returns
        -------
        list
            List of emails for the specified property
        """
        return [email for email in self.generated_emails.values() 
                if email.get('property_name') == property_name]
    
    def preview_email(self, email_id: str) -> Optional[Dict[str, str]]:
        """
        Get email preview data for display in UI.
        
        Parameters
        ----------
        email_id : str
            Email ID
            
        Returns
        -------
        dict or None
            Email preview data
        """
        email_data = self.get_generated_email(email_id)
        if not email_data:
            return None
        
        return {
            'id': email_data['id'],
            'property_name': email_data['property_name'],
            'email_address': email_data['email_address'],
            'subject': email_data['subject'],
            'body': email_data['body'],
            'total_extra': email_data['total_extra'],
            'status': email_data['status'],
            'created_at': email_data['created_at']
        }
    
    def validate_email_data(self, email_data: Dict[str, Any]) -> List[str]:
        """
        Validate email data for completeness and correctness.
        
        Parameters
        ----------
        email_data : dict
            Email data to validate
            
        Returns
        -------
        list
            List of validation errors (empty if valid)
        """
        errors = []
        
        required_fields = ['property_name', 'email_address', 'subject', 'body', 'total_extra']
        for field in required_fields:
            if field not in email_data or not email_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate email address format
        if 'email_address' in email_data:
            email = email_data['email_address']
            if '@' not in email or '.' not in email.split('@')[-1]:
                errors.append("Invalid email address format")
        
        # Validate total_extra is positive
        if 'total_extra' in email_data:
            try:
                total_extra = float(email_data['total_extra'])
                if total_extra <= 0:
                    errors.append("Total extra must be positive")
            except (ValueError, TypeError):
                errors.append("Total extra must be a valid number")
        
        return errors
