#!/usr/bin/env python3
"""
Email System GUI Demo
====================

A visual demonstration of the email system with popup windows
showing the email generation and sending process in real-time.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Email System Demo - Visual Test")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Email system components
        self.email_generator = None
        self.email_sender = None
        self.generated_emails = []
        
        self.setup_ui()
        self.initialize_email_system()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Title
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(pady=10)
        
        title_label = tk.Label(
            title_frame, 
            text="🚀 Email System Visual Demo", 
            font=('Arial', 16, 'bold'),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Watch the email system generate and send emails in real-time",
            font=('Arial', 10),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        subtitle_label.pack()
        
        # Control buttons
        button_frame = tk.Frame(self.root, bg='#f0f0f0')
        button_frame.pack(pady=10)
        
        self.start_button = tk.Button(
            button_frame,
            text="🚀 Start Email Demo",
            command=self.start_demo,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = tk.Button(
            button_frame,
            text="🗑️ Clear Log",
            command=self.clear_log,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.progress_frame.pack(pady=10, fill='x', padx=20)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="Ready to start demo...",
            font=('Arial', 10),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=5)
        
        # Log display
        log_frame = tk.Frame(self.root, bg='#f0f0f0')
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        log_label = tk.Label(
            log_frame,
            text="📋 Demo Log:",
            font=('Arial', 12, 'bold'),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        log_label.pack(anchor='w')
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            font=('Consolas', 9),
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='white',
            wrap=tk.WORD
        )
        self.log_text.pack(fill='both', expand=True, pady=5)
        
        # Statistics frame
        stats_frame = tk.Frame(self.root, bg='#f0f0f0')
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        self.stats_label = tk.Label(
            stats_frame,
            text="📊 Statistics: No emails processed yet",
            font=('Arial', 10),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        self.stats_label.pack()
    
    def initialize_email_system(self):
        """Initialize the email system components."""
        try:
            from src.email_system.email_generator import EmailGenerator
            from src.email_system.email_sender import EmailSender
            
            self.email_generator = EmailGenerator("email_templates.xlsx")
            self.email_sender = EmailSender(offline_mode=True)
            
            self.log("✅ Email system initialized successfully!")
        except Exception as e:
            self.log(f"❌ Failed to initialize email system: {e}")
            messagebox.showerror("Error", f"Failed to initialize email system: {e}")
    
    def log(self, message):
        """Add a message to the log display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear the log display."""
        self.log_text.delete(1.0, tk.END)
        self.log("🗑️ Log cleared")
    
    def update_progress(self, value, text):
        """Update the progress bar and label."""
        self.progress_bar['value'] = value
        self.progress_label.config(text=text)
        self.root.update_idletasks()
    
    def update_stats(self):
        """Update the statistics display."""
        if self.email_sender:
            stats = self.email_sender.get_email_statistics()
            stats_text = f"📊 Statistics: {stats['sent_emails']} sent, {stats['pending_approvals']} pending, {stats['total_emails']} total"
            self.stats_label.config(text=stats_text)
    
    def show_email_popup(self, email_data, step):
        """Show a popup window with email details."""
        popup = tk.Toplevel(self.root)
        popup.title(f"📧 Email {step} - {email_data['property_name']}")
        popup.geometry("600x500")
        popup.configure(bg='#f0f0f0')
        
        # Make popup modal
        popup.transient(self.root)
        popup.grab_set()
        
        # Header
        header_frame = tk.Frame(popup, bg='#3498db', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame,
            text=f"📧 Email {step} - {email_data['property_name']}",
            font=('Arial', 14, 'bold'),
            bg='#3498db',
            fg='white'
        )
        header_label.pack(expand=True)
        
        # Content frame
        content_frame = tk.Frame(popup, bg='#f0f0f0')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Email details
        details_frame = tk.LabelFrame(
            content_frame,
            text="Email Details",
            font=('Arial', 10, 'bold'),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        details_frame.pack(fill='x', pady=(0, 10))
        
        details_text = f"""To: {email_data['email_address']}
Subject: {email_data['subject']}
Total Extra: €{email_data['total_extra']:.2f}
Status: {email_data['status']}
Generated: {email_data['created_at']}"""
        
        details_label = tk.Label(
            details_frame,
            text=details_text,
            font=('Consolas', 9),
            bg='#f0f0f0',
            fg='#2c3e50',
            justify='left'
        )
        details_label.pack(padx=10, pady=10)
        
        # Email body preview
        body_frame = tk.LabelFrame(
            content_frame,
            text="Email Body Preview",
            font=('Arial', 10, 'bold'),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        body_frame.pack(fill='both', expand=True)
        
        body_text = scrolledtext.ScrolledText(
            body_frame,
            height=12,
            font=('Consolas', 9),
            bg='#ecf0f1',
            fg='#2c3e50',
            wrap=tk.WORD
        )
        body_text.pack(fill='both', expand=True, padx=10, pady=10)
        body_text.insert(tk.END, email_data['body'])
        body_text.config(state='disabled')
        
        # Close button
        close_button = tk.Button(
            content_frame,
            text="Close",
            command=popup.destroy,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        close_button.pack(pady=10)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
    
    def start_demo(self):
        """Start the email system demo in a separate thread."""
        self.start_button.config(state='disabled')
        self.clear_log()
        
        # Start demo in separate thread to avoid blocking UI
        demo_thread = threading.Thread(target=self.run_demo)
        demo_thread.daemon = True
        demo_thread.start()
    
    def run_demo(self):
        """Run the email system demo."""
        try:
            self.log("🚀 Starting Email System Demo...")
            self.update_progress(0, "Initializing demo...")
            
            # Sample property data
            properties = [
                {
                    'name': 'Aribau 1º 1ª',
                    'elec_cost': 45.50,
                    'water_cost': 25.30,
                    'allowance': 50.0,
                    'total_extra': 20.80,
                    'payment_link': 'https://payment.example.com/aribau',
                    'electricity_invoice_url': '_debug/invoices/elec_test_001_20250903.pdf',
                    'water_invoice_url': '_debug/invoices/water_test_001_20250903.pdf'
                },
                {
                    'name': 'Test Property 2',
                    'elec_cost': 60.00,
                    'water_cost': 30.00,
                    'allowance': 70.0,
                    'total_extra': 20.00,
                    'payment_link': 'https://payment.example.com/test2',
                    'electricity_invoice_url': '',
                    'water_invoice_url': ''
                },
                {
                    'name': 'No Overage Property',
                    'elec_cost': 30.00,
                    'water_cost': 15.00,
                    'allowance': 50.0,
                    'total_extra': -5.00,
                    'payment_link': 'https://payment.example.com/no-overage'
                }
            ]
            
            self.log(f"📋 Processing {len(properties)} properties...")
            self.update_progress(10, "Processing properties...")
            
            # Generate emails
            self.generated_emails = []
            for i, property_data in enumerate(properties):
                self.log(f"\n🏠 Processing Property {i+1}: {property_data['name']}")
                self.log(f"   - Electricity: €{property_data['elec_cost']:.2f}")
                self.log(f"   - Water: €{property_data['water_cost']:.2f}")
                self.log(f"   - Allowance: €{property_data['allowance']:.2f}")
                self.log(f"   - Total Extra: €{property_data['total_extra']:.2f}")
                
                progress = 10 + (i * 20)
                self.update_progress(progress, f"Processing {property_data['name']}...")
                
                email_data = self.email_generator.generate_email_for_property(property_data)
                if email_data:
                    self.generated_emails.append(email_data)
                    self.log(f"   ✅ Email generated (ID: {email_data['id'][:8]}...)")
                    
                    # Show email popup
                    self.root.after(0, lambda ed=email_data, step=f"{i+1}": self.show_email_popup(ed, step))
                    time.sleep(2)  # Pause to show popup
                else:
                    self.log(f"   ⏭️  No email generated (no overage or error)")
                
                time.sleep(1)  # Pause between properties
            
            self.log(f"\n✅ Generated {len(self.generated_emails)} emails")
            self.update_progress(70, "Testing email sending...")
            
            # Test email sending
            if self.generated_emails:
                self.log("\n📤 Testing Email Sending Workflow:")
                
                # Test approval workflow
                self.log("\n1. Testing approval workflow...")
                email_data = self.generated_emails[0]
                
                send_result = self.email_sender.send_email(email_data, require_approval=True)
                if send_result['success']:
                    self.log(f"   ✅ Email queued for approval")
                    self.log(f"   Status: {send_result['status']}")
                    
                    pending = self.email_sender.get_pending_approvals()
                    self.log(f"   Pending approvals: {len(pending)}")
                    
                    self.log("\n   Approving email...")
                    time.sleep(1)
                    
                    approval_result = self.email_sender.approve_email(email_data['id'])
                    if approval_result['success']:
                        self.log(f"   ✅ Email approved and sent!")
                        self.log(f"   Status: {approval_result['status']}")
                        self.log(f"   Sent at: {approval_result.get('sent_at', 'N/A')}")
                    else:
                        self.log(f"   ❌ Failed to approve: {approval_result.get('error')}")
                
                # Test direct sending
                if len(self.generated_emails) > 1:
                    self.log("\n2. Testing direct sending...")
                    email_data2 = self.generated_emails[1]
                    
                    send_result2 = self.email_sender.send_email(email_data2, require_approval=False)
                    if send_result2['success']:
                        self.log(f"   ✅ Email sent directly!")
                        self.log(f"   Status: {send_result2['status']}")
                    else:
                        self.log(f"   ❌ Failed to send: {send_result2.get('error')}")
            
            # Final statistics
            self.update_progress(100, "Demo completed!")
            self.log("\n📊 Final Statistics:")
            stats = self.email_sender.get_email_statistics()
            self.log(f"   Pending approvals: {stats['pending_approvals']}")
            self.log(f"   Sent emails: {stats['sent_emails']}")
            self.log(f"   Total emails: {stats['total_emails']}")
            self.log(f"   Offline mode: {stats['offline_mode']}")
            
            self.log("\n🎉 EMAIL SYSTEM DEMO COMPLETED SUCCESSFULLY!")
            
            # Update stats display
            self.root.after(0, self.update_stats)
            
            # Show completion message
            self.root.after(0, lambda: messagebox.showinfo(
                "Demo Complete", 
                "Email system demo completed successfully!\n\nCheck the log for details."
            ))
            
        except Exception as e:
            self.log(f"\n❌ DEMO FAILED: {e}")
            self.root.after(0, lambda: messagebox.showerror("Demo Error", f"Demo failed: {e}"))
        finally:
            self.root.after(0, lambda: self.start_button.config(state='normal'))

def main():
    """Run the GUI demo."""
    root = tk.Tk()
    app = EmailSystemGUI(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
