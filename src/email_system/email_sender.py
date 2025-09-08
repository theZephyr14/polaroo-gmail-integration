"""
Email Sender
============

Handles sending emails with approval workflow and status tracking.
In offline mode, simulates email sending for testing.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

logger = logging.getLogger(__name__)

class EmailSender:
    """Handles email sending with approval workflow."""
    
    def __init__(self, offline_mode: bool = True, smtp_config: Optional[Dict[str, str]] = None):
        """
        Initialize the email sender.
        
        Parameters
        ----------
        offline_mode : bool
            If True, simulates email sending instead of actually sending
        smtp_config : dict, optional
            SMTP configuration for real email sending
        """
        self.offline_mode = offline_mode
        self.smtp_config = smtp_config or {}
        self.sent_emails = {}  # Store sent email records in memory
        self.pending_approvals = {}  # Store emails pending approval
    
    def send_email(self, email_data: Dict[str, Any], require_approval: bool = True) -> Dict[str, Any]:
        """
        Send an email with optional approval workflow.
        
        Parameters
        ----------
        email_data : dict
            Email data from EmailGenerator
        require_approval : bool
            If True, requires manual approval before sending
            
        Returns
        -------
        dict
            Send result with status and metadata
        """
        try:
            email_id = email_data.get('id')
            if not email_id:
                return {
                    'success': False,
                    'error': 'Email ID is required',
                    'email_id': None
                }
            
            if require_approval:
                return self._queue_for_approval(email_data)
            else:
                return self._send_email_directly(email_data)
                
        except Exception as e:
            logger.error(f"Error sending email {email_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'email_id': email_id
            }
    
    def _queue_for_approval(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queue email for manual approval.
        
        Parameters
        ----------
        email_data : dict
            Email data
            
        Returns
        -------
        dict
            Approval queue result
        """
        email_id = email_data['id']
        
        approval_data = {
            'email_id': email_id,
            'email_data': email_data,
            'status': 'pending_approval',
            'queued_at': datetime.now().isoformat(),
            'approved_at': None,
            'sent_at': None
        }
        
        self.pending_approvals[email_id] = approval_data
        
        logger.info(f"Email {email_id} queued for approval")
        
        return {
            'success': True,
            'status': 'pending_approval',
            'email_id': email_id,
            'message': 'Email queued for approval',
            'approval_required': True
        }
    
    def _send_email_directly(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email directly without approval.
        
        Parameters
        ----------
        email_data : dict
            Email data
            
        Returns
        -------
        dict
            Send result
        """
        email_id = email_data['id']
        
        if self.offline_mode:
            return self._simulate_email_sending(email_data)
        else:
            return self._send_real_email(email_data)
    
    def _simulate_email_sending(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate email sending for offline testing.
        
        Parameters
        ----------
        email_data : dict
            Email data
            
        Returns
        -------
        dict
            Simulated send result
        """
        email_id = email_data['id']
        
        # Simulate sending delay
        import time
        time.sleep(0.5)  # Simulate network delay
        
        # Create sent email record
        sent_email = {
            'id': email_id,
            'property_name': email_data['property_name'],
            'email_address': email_data['email_address'],
            'subject': email_data['subject'],
            'body': email_data['body'],
            'status': 'sent',
            'sent_at': datetime.now().isoformat(),
            'total_extra': email_data['total_extra'],
            'simulated': True
        }
        
        self.sent_emails[email_id] = sent_email
        
        logger.info(f"Simulated sending email {email_id} to {email_data['email_address']}")
        
        return {
            'success': True,
            'status': 'sent',
            'email_id': email_id,
            'message': 'Email sent successfully (simulated)',
            'sent_at': sent_email['sent_at']
        }
    
    def _send_real_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send real email using SMTP.
        
        Parameters
        ----------
        email_data : dict
            Email data
            
        Returns
        -------
        dict
            Send result
        """
        email_id = email_data['id']
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config.get('from_email', 'noreply@example.com')
            msg['To'] = email_data['email_address']
            msg['Subject'] = email_data['subject']
            
            # Add body
            msg.attach(MIMEText(email_data['body'], 'html'))
            
            # Add attachments if any
            if email_data.get('electricity_invoice_url'):
                self._add_attachment(msg, email_data['electricity_invoice_url'], 'electricity_invoice.pdf')
            if email_data.get('water_invoice_url'):
                self._add_attachment(msg, email_data['water_invoice_url'], 'water_invoice.pdf')
            
            # Send email
            server = smtplib.SMTP(
                self.smtp_config.get('smtp_server', 'localhost'),
                self.smtp_config.get('smtp_port', 587)
            )
            server.starttls()
            server.login(
                self.smtp_config.get('username', ''),
                self.smtp_config.get('password', '')
            )
            
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)
            server.quit()
            
            # Create sent email record
            sent_email = {
                'id': email_id,
                'property_name': email_data['property_name'],
                'email_address': email_data['email_address'],
                'subject': email_data['subject'],
                'body': email_data['body'],
                'status': 'sent',
                'sent_at': datetime.now().isoformat(),
                'total_extra': email_data['total_extra'],
                'simulated': False
            }
            
            self.sent_emails[email_id] = sent_email
            
            logger.info(f"Sent email {email_id} to {email_data['email_address']}")
            
            return {
                'success': True,
                'status': 'sent',
                'email_id': email_id,
                'message': 'Email sent successfully',
                'sent_at': sent_email['sent_at']
            }
            
        except Exception as e:
            logger.error(f"Error sending real email {email_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'email_id': email_id
            }
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str, filename: str):
        """
        Add attachment to email message.
        
        Parameters
        ----------
        msg : MIMEMultipart
            Email message
        file_path : str
            Path to attachment file
        filename : str
            Filename for attachment
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {e}")
    
    def approve_email(self, email_id: str) -> Dict[str, Any]:
        """
        Approve a pending email for sending.
        
        Parameters
        ----------
        email_id : str
            Email ID to approve
            
        Returns
        -------
        dict
            Approval result
        """
        if email_id not in self.pending_approvals:
            return {
                'success': False,
                'error': 'Email not found in pending approvals',
                'email_id': email_id
            }
        
        approval_data = self.pending_approvals[email_id]
        email_data = approval_data['email_data']
        
        # Update approval status
        approval_data['status'] = 'approved'
        approval_data['approved_at'] = datetime.now().isoformat()
        
        # Send the email
        send_result = self._send_email_directly(email_data)
        
        if send_result['success']:
            approval_data['status'] = 'sent'
            approval_data['sent_at'] = send_result.get('sent_at')
            
            # Move to sent emails
            self.sent_emails[email_id] = {
                'id': email_id,
                'property_name': email_data['property_name'],
                'email_address': email_data['email_address'],
                'subject': email_data['subject'],
                'body': email_data['body'],
                'status': 'sent',
                'sent_at': send_result.get('sent_at'),
                'total_extra': email_data['total_extra'],
                'approved_at': approval_data['approved_at']
            }
            
            # Remove from pending
            del self.pending_approvals[email_id]
            
            logger.info(f"Approved and sent email {email_id}")
            
            return {
                'success': True,
                'status': 'sent',
                'email_id': email_id,
                'message': 'Email approved and sent successfully',
                'sent_at': send_result.get('sent_at')
            }
        else:
            approval_data['status'] = 'failed'
            approval_data['error'] = send_result.get('error')
            
            logger.error(f"Failed to send approved email {email_id}: {send_result.get('error')}")
            
            return {
                'success': False,
                'error': send_result.get('error'),
                'email_id': email_id
            }
    
    def reject_email(self, email_id: str, reason: str = "Rejected by operator") -> Dict[str, Any]:
        """
        Reject a pending email.
        
        Parameters
        ----------
        email_id : str
            Email ID to reject
        reason : str
            Reason for rejection
            
        Returns
        -------
        dict
            Rejection result
        """
        if email_id not in self.pending_approvals:
            return {
                'success': False,
                'error': 'Email not found in pending approvals',
                'email_id': email_id
            }
        
        approval_data = self.pending_approvals[email_id]
        approval_data['status'] = 'rejected'
        approval_data['rejected_at'] = datetime.now().isoformat()
        approval_data['rejection_reason'] = reason
        
        # Remove from pending
        del self.pending_approvals[email_id]
        
        logger.info(f"Rejected email {email_id}: {reason}")
        
        return {
            'success': True,
            'status': 'rejected',
            'email_id': email_id,
            'message': f'Email rejected: {reason}'
        }
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """
        Get all emails pending approval.
        
        Returns
        -------
        list
            List of pending approval emails
        """
        return list(self.pending_approvals.values())
    
    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """
        Get all sent emails.
        
        Returns
        -------
        list
            List of sent emails
        """
        return list(self.sent_emails.values())
    
    def get_email_status(self, email_id: str) -> Optional[str]:
        """
        Get the status of an email.
        
        Parameters
        ----------
        email_id : str
            Email ID
            
        Returns
        -------
        str or None
            Email status
        """
        if email_id in self.pending_approvals:
            return self.pending_approvals[email_id]['status']
        elif email_id in self.sent_emails:
            return self.sent_emails[email_id]['status']
        else:
            return None
    
    def get_email_statistics(self) -> Dict[str, Any]:
        """
        Get email sending statistics.
        
        Returns
        -------
        dict
            Email statistics
        """
        pending_count = len(self.pending_approvals)
        sent_count = len(self.sent_emails)
        
        # Count by status
        status_counts = {}
        for email in self.sent_emails.values():
            status = email.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'pending_approvals': pending_count,
            'sent_emails': sent_count,
            'total_emails': pending_count + sent_count,
            'status_breakdown': status_counts,
            'offline_mode': self.offline_mode
        }
