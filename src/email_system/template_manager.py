"""
Template Manager
===============

Manages email templates stored in Excel files and provides template
rendering functionality with property-specific data.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TemplateManager:
    """Manages email templates and tenant contact information."""
    
    def __init__(self, template_file: str = "email_templates.xlsx"):
        """
        Initialize the template manager.
        
        Parameters
        ----------
        template_file : str
            Path to the Excel file containing email templates and tenant info
        """
        self.template_file = Path(template_file)
        self.templates_df = None
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from Excel file."""
        try:
            if self.template_file.exists():
                self.templates_df = pd.read_excel(self.template_file, engine='openpyxl')
                logger.info(f"Loaded {len(self.templates_df)} email templates from {self.template_file}")
            else:
                logger.warning(f"Template file {self.template_file} not found, creating default template")
                self._create_default_template()
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            self._create_default_template()
    
    def _create_default_template(self):
        """Create a default template if none exists."""
        default_data = {
            'Property Name': ['Sample Property'],
            'Email Address': ['tenant@example.com'],
            'Subject': ['Utility Bill Overage - {property_name}'],
            'Body': ["""Dear Tenant,

We hope this email finds you well.

We are writing to inform you about your utility bill for {property_name} for the month of {month_year}.

**Bill Summary:**
- Property: {property_name}
- Electricity Cost: €{electricity_cost:.2f}
- Water Cost: €{water_cost:.2f}
- Total Cost: €{total_cost:.2f}
- Allowance: €{allowance:.2f}
- **Overage Amount: €{total_extra:.2f}**

As per your rental agreement, you are responsible for any utility costs exceeding the monthly allowance of €{allowance:.2f}.

**Payment Information:**
Please make payment of €{total_extra:.2f} by {due_date} using the following payment link:
{payment_link}

**Invoice Attachments:**
- Electricity Invoice: {electricity_invoice_url}
- Water Invoice: {water_invoice_url}

If you have any questions about this bill, please don't hesitate to contact us.

Best regards,
Property Management Team"""]
        }
        self.templates_df = pd.DataFrame(default_data)
        logger.info("Created default email template")
    
    def get_template_for_property(self, property_name: str) -> Optional[Dict[str, str]]:
        """
        Get email template for a specific property.
        
        Parameters
        ----------
        property_name : str
            Name of the property
            
        Returns
        -------
        dict or None
            Template data including subject, body, and email address
        """
        if self.templates_df is None:
            return None
        
        # Try exact match first
        exact_match = self.templates_df[self.templates_df['Property Name'] == property_name]
        if not exact_match.empty:
            row = exact_match.iloc[0]
            return {
                'email_address': row['Email Address'],
                'subject': row['Subject'],
                'body': row['Body']
            }
        
        # Try partial match (in case property names don't match exactly)
        for _, row in self.templates_df.iterrows():
            template_property = row['Property Name']
            if property_name.lower() in template_property.lower() or template_property.lower() in property_name.lower():
                return {
                    'email_address': row['Email Address'],
                    'subject': row['Subject'],
                    'body': row['Body']
                }
        
        # Return default template if no match found
        if not self.templates_df.empty:
            default_row = self.templates_df.iloc[0]
            return {
                'email_address': 'tenant@example.com',  # Default email
                'subject': default_row['Subject'],
                'body': default_row['Body']
            }
        
        return None
    
    def render_template(self, template_data: Dict[str, str], property_data: Dict[str, any]) -> Dict[str, str]:
        """
        Render email template with property-specific data.
        
        Parameters
        ----------
        template_data : dict
            Template data from get_template_for_property
        property_data : dict
            Property data including costs, allowances, etc.
            
        Returns
        -------
        dict
            Rendered email with subject and body
        """
        if not template_data:
            return {}
        
        # Prepare template variables
        now = datetime.now()
        template_vars = {
            'property_name': property_data.get('name', 'Unknown Property'),
            'month_year': now.strftime('%B %Y'),
            'electricity_cost': property_data.get('elec_cost', 0.0),
            'water_cost': property_data.get('water_cost', 0.0),
            'total_cost': property_data.get('elec_cost', 0.0) + property_data.get('water_cost', 0.0),
            'allowance': property_data.get('allowance', 0.0),
            'total_extra': property_data.get('total_extra', 0.0),
            'due_date': (now + timedelta(days=14)).strftime('%B %d, %Y'),
            'payment_link': property_data.get('payment_link', 'https://payment.example.com'),
            'electricity_invoice_url': property_data.get('electricity_invoice_url', ''),
            'water_invoice_url': property_data.get('water_invoice_url', '')
        }
        
        # Render subject and body
        try:
            subject = template_data['subject'].format(**template_vars)
            body = template_data['body'].format(**template_vars)
            
            return {
                'email_address': template_data['email_address'],
                'subject': subject,
                'body': body,
                'template_vars': template_vars
            }
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return {
                'email_address': template_data['email_address'],
                'subject': f"Utility Bill Overage - {property_data.get('name', 'Property')}",
                'body': f"Please pay €{property_data.get('total_extra', 0.0):.2f} for utility overages.",
                'template_vars': template_vars
            }
    
    def add_property_template(self, property_name: str, email_address: str, 
                            subject: str, body: str) -> bool:
        """
        Add a new property template.
        
        Parameters
        ----------
        property_name : str
            Name of the property
        email_address : str
            Tenant's email address
        subject : str
            Email subject template
        body : str
            Email body template
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            new_row = pd.DataFrame({
                'Property Name': [property_name],
                'Email Address': [email_address],
                'Subject': [subject],
                'Body': [body]
            })
            
            if self.templates_df is None:
                self.templates_df = new_row
            else:
                self.templates_df = pd.concat([self.templates_df, new_row], ignore_index=True)
            
            # Save to file
            self.templates_df.to_excel(self.template_file, index=False, engine='openpyxl')
            logger.info(f"Added template for property: {property_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding template: {e}")
            return False
    
    def get_all_properties(self) -> List[str]:
        """
        Get list of all properties with templates.
        
        Returns
        -------
        list
            List of property names
        """
        if self.templates_df is None:
            return []
        return self.templates_df['Property Name'].tolist()
    
    def update_property_email(self, property_name: str, new_email: str) -> bool:
        """
        Update email address for a property.
        
        Parameters
        ----------
        property_name : str
            Name of the property
        new_email : str
            New email address
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            if self.templates_df is None:
                return False
            
            mask = self.templates_df['Property Name'] == property_name
            if mask.any():
                self.templates_df.loc[mask, 'Email Address'] = new_email
                self.templates_df.to_excel(self.template_file, index=False, engine='openpyxl')
                logger.info(f"Updated email for property: {property_name}")
                return True
            else:
                logger.warning(f"Property not found: {property_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating email: {e}")
            return False
