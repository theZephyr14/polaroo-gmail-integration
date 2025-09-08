"""
Email System Module
==================

This module provides functionality for generating and managing emails
for utility bill overages, including invoice downloads and email templates.
"""

from .email_generator import EmailGenerator
from .invoice_downloader import InvoiceDownloader
from .email_sender import EmailSender
from .template_manager import TemplateManager

__all__ = [
    'EmailGenerator',
    'InvoiceDownloader', 
    'EmailSender',
    'TemplateManager'
]
