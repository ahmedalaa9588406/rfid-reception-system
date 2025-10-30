"""Receipt printer service for RFID Reception System.

This service provides receipt printing functionality that works with all printers.
Supports both direct printing (Windows) and PDF generation (cross-platform).
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ReceiptPrinter:
    """Service for printing receipts to physical printers or PDF."""
    
    def __init__(self, company_name="RFID Reception System", company_info=None):
        """
        Initialize the receipt printer.
        
        Args:
            company_name: Name of the company/organization
            company_info: Additional company information (address, phone, etc.)
        """
        self.company_name = company_name
        self.company_info = company_info or {}
        self.printer_available = self._check_printer_availability()
    
    def _check_printer_availability(self) -> bool:
        """Check if direct printing is available."""
        try:
            import win32print
            # Get default printer
            default_printer = win32print.GetDefaultPrinter()
            logger.info(f"Default printer available: {default_printer}")
            return True
        except ImportError:
            logger.warning("win32print not available - using PDF fallback")
            return False
        except Exception as e:
            logger.warning(f"Printer check failed: {e}")
            return False
    
    def print_receipt(self, 
                     card_uid: str,
                     amount: float,
                     balance_after: float,
                     transaction_id: int,
                     employee: str,
                     timestamp: datetime = None,
                     auto_print: bool = True) -> tuple[bool, str]:
        """
        Print a receipt for a transaction.
        
        Args:
            card_uid: Card UID
            amount: Transaction amount
            balance_after: Balance after transaction
            transaction_id: Transaction ID from database
            employee: Employee who processed the transaction
            timestamp: Transaction timestamp (defaults to now)
            auto_print: If True, sends to printer automatically; if False, saves as PDF
        
        Returns:
            Tuple of (success, message/path)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        receipt_data = {
            'card_uid': card_uid,
            'amount': amount,
            'balance_after': balance_after,
            'transaction_id': transaction_id,
            'employee': employee,
            'timestamp': timestamp
        }
        
        # Try direct printing first if available and auto_print is True
        if auto_print and self.printer_available:
            return self._print_to_printer(receipt_data)
        else:
            # Fallback to PDF
            return self._print_to_pdf(receipt_data)
    
    def _print_to_printer(self, receipt_data: Dict[str, Any]) -> tuple[bool, str]:
        """Print receipt directly to default printer (Windows)."""
        try:
            import win32print
            import win32ui
            from PIL import Image, ImageDraw, ImageFont
            
            # Create receipt image
            receipt_image = self._create_receipt_image(receipt_data)
            
            # Get default printer
            printer_name = win32print.GetDefaultPrinter()
            
            # Print the image
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            hDC.StartDoc("RFID Receipt")
            hDC.StartPage()
            
            # Get printer dimensions
            printer_width = hDC.GetDeviceCaps(110)  # HORZRES
            printer_height = hDC.GetDeviceCaps(111)  # VERTRES
            
            # Calculate scaling
            img_width, img_height = receipt_image.size
            scale = min(printer_width / img_width, printer_height / img_height) * 0.8
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Save to temp file and print
            temp_path = os.path.join(tempfile.gettempdir(), "receipt_temp.bmp")
            receipt_image.save(temp_path, "BMP")
            
            # Draw the image
            bmp = Image.open(temp_path)
            dib = win32ui.CreateBitmap()
            dib.CreateCompatibleBitmap(hDC, new_width, new_height)
            
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
            
            logger.info(f"Receipt printed to {printer_name}")
            return True, f"Printed to {printer_name}"
            
        except Exception as e:
            logger.error(f"Direct printing failed: {e}")
            # Fallback to PDF
            return self._print_to_pdf(receipt_data)
    
    def _print_to_pdf(self, receipt_data: Dict[str, Any]) -> tuple[bool, str]:
        """Generate receipt as PDF (cross-platform)."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch, mm
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors
            
            # Generate filename
            timestamp_str = receipt_data['timestamp'].strftime("%Y%m%d_%H%M%S")
            filename = f"receipt_{receipt_data['transaction_id']}_{timestamp_str}.pdf"
            
            # Create receipts directory if it doesn't exist
            receipts_dir = os.path.join(os.getcwd(), "receipts")
            os.makedirs(receipts_dir, exist_ok=True)
            
            filepath = os.path.join(receipts_dir, filename)
            
            # Create PDF (thermal receipt size: 80mm wide)
            c = canvas.Canvas(filepath, pagesize=(80*mm, 200*mm))
            
            # Draw receipt
            self._draw_receipt_pdf(c, receipt_data)
            
            c.save()
            
            logger.info(f"Receipt saved to {filepath}")
            return True, filepath
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return False, str(e)
    
    def _create_receipt_image(self, receipt_data: Dict[str, Any]):
        """Create receipt as PIL Image for direct printing."""
        from PIL import Image, ImageDraw, ImageFont
        
        # Receipt dimensions (thermal printer: 80mm = ~300 pixels)
        width = 300
        height = 500
        
        # Create image
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a better font, fallback to default
        try:
            title_font = ImageFont.truetype("arial.ttf", 18)
            normal_font = ImageFont.truetype("arial.ttf", 12)
            small_font = ImageFont.truetype("arial.ttf", 10)
        except:
            title_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        y = 10
        
        # Company name
        draw.text((width//2, y), self.company_name, fill='black', 
                 font=title_font, anchor="mt")
        y += 30
        
        # Separator line
        draw.line([(10, y), (width-10, y)], fill='black', width=2)
        y += 20
        
        # Receipt title
        draw.text((width//2, y), "TRANSACTION RECEIPT", fill='black',
                 font=normal_font, anchor="mt")
        y += 30
        
        # Transaction details
        details = [
            f"Transaction ID: #{receipt_data['transaction_id']}",
            f"Date: {receipt_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Card UID: {receipt_data['card_uid']}",
            f"Amount: {receipt_data['amount']:.2f} EGP",
            f"Balance After: {receipt_data['balance_after']:.2f} EGP",
            "",
            f"Employee: {receipt_data['employee']}",
        ]
        
        for line in details:
            draw.text((15, y), line, fill='black', font=normal_font)
            y += 20
        
        y += 10
        draw.line([(10, y), (width-10, y)], fill='black', width=1)
        y += 15
        
        # Footer
        draw.text((width//2, y), "Thank you!", fill='black',
                 font=normal_font, anchor="mt")
        y += 25
        draw.text((width//2, y), "Keep this receipt for your records", 
                 fill='black', font=small_font, anchor="mt")
        
        return img
    
    def _draw_receipt_pdf(self, c, receipt_data: Dict[str, Any]):
        """Draw receipt content on PDF canvas."""
        from reportlab.lib.units import mm
        
        width = 80 * mm
        x_center = width / 2
        x_left = 5 * mm
        y = 190 * mm  # Start from top
        
        # Company name (centered, bold)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(x_center, y, self.company_name)
        y -= 6 * mm
        
        # Company info (if available)
        c.setFont("Helvetica", 8)
        if self.company_info.get('address'):
            c.drawCentredString(x_center, y, self.company_info['address'])
            y -= 4 * mm
        if self.company_info.get('phone'):
            c.drawCentredString(x_center, y, f"Tel: {self.company_info['phone']}")
            y -= 4 * mm
        
        # Separator line
        y -= 3 * mm
        c.line(x_left, y, width - x_left, y)
        y -= 6 * mm
        
        # Receipt title
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x_center, y, "TRANSACTION RECEIPT")
        y -= 8 * mm
        
        # Transaction details
        c.setFont("Helvetica", 10)
        
        details = [
            ("Transaction ID:", f"#{receipt_data['transaction_id']}"),
            ("Date:", receipt_data['timestamp'].strftime('%Y-%m-%d')),
            ("Time:", receipt_data['timestamp'].strftime('%H:%M:%S')),
            ("", ""),
            ("Card UID:", receipt_data['card_uid'][:16]),
            ("", receipt_data['card_uid'][16:] if len(receipt_data['card_uid']) > 16 else ""),
        ]
        
        for label, value in details:
            if label:
                c.drawString(x_left, y, label)
                c.drawRightString(width - x_left, y, value)
            y -= 5 * mm
        
        # Amount (highlighted)
        y -= 2 * mm
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x_left, y - 3*mm, width - 2*x_left, 8*mm, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x_left + 2*mm, y, "Top-Up Amount:")
        c.drawRightString(width - x_left - 2*mm, y, f"{receipt_data['amount']:.2f} EGP")
        y -= 6 * mm
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x_left + 2*mm, y, "New Balance:")
        c.drawRightString(width - x_left - 2*mm, y, f"{receipt_data['balance_after']:.2f} EGP")
        y -= 8 * mm
        
        # Separator
        c.setFillColorRGB(0, 0, 0)
        c.line(x_left, y, width - x_left, y)
        y -= 6 * mm
        
        # Employee
        c.setFont("Helvetica", 9)
        c.drawString(x_left, y, f"Served by: {receipt_data['employee']}")
        y -= 8 * mm
        
        # Footer
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x_center, y, "Thank You!")
        y -= 5 * mm
        
        c.setFont("Helvetica", 8)
        c.drawCentredString(x_center, y, "Please keep this receipt for your records")
        y -= 4 * mm
        c.drawCentredString(x_center, y, "For support, contact reception")
        
        # IMPORTANT: Show the page to finalize the content
        c.showPage()
    
    def print_card_summary(self, card_data: Dict[str, Any], 
                          transactions: list = None) -> tuple[bool, str]:
        """
        Print a summary receipt for a card with transaction history.
        
        Args:
            card_data: Dictionary with card information
            transactions: List of recent transactions (optional)
        
        Returns:
            Tuple of (success, message/path)
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import mm
            from reportlab.pdfgen import canvas
            
            # Generate filename
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"card_summary_{card_data['card_uid']}_{timestamp_str}.pdf"
            
            receipts_dir = os.path.join(os.getcwd(), "receipts")
            os.makedirs(receipts_dir, exist_ok=True)
            
            filepath = os.path.join(receipts_dir, filename)
            
            # Create PDF (A4 size for detailed summary)
            c = canvas.Canvas(filepath, pagesize=letter)
            
            self._draw_card_summary_pdf(c, card_data, transactions)
            
            c.save()
            
            logger.info(f"Card summary saved to {filepath}")
            return True, filepath
            
        except Exception as e:
            logger.error(f"Card summary generation failed: {e}")
            return False, str(e)
    
    def _draw_card_summary_pdf(self, c, card_data: Dict[str, Any], 
                               transactions: list = None):
        """Draw card summary on PDF canvas."""
        from reportlab.lib.units import inch
        from reportlab.lib.pagesizes import letter
        
        width, height = letter
        margin = 0.75 * inch
        y = height - margin
        
        # Header
        c.setFont("Helvetica-Bold", 18)
        c.drawString(margin, y, self.company_name)
        y -= 0.3 * inch
        
        c.setFont("Helvetica", 12)
        c.drawString(margin, y, f"Card Summary Report")
        y -= 0.2 * inch
        c.drawString(margin, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        y -= 0.4 * inch
        
        # Card information
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y, "Card Information")
        y -= 0.25 * inch
        
        c.setFont("Helvetica", 11)
        info_lines = [
            f"Card UID: {card_data.get('card_uid', 'N/A')}",
            f"Current Balance: {card_data.get('balance', 0):.2f} EGP",
            f"Created: {card_data.get('created_at', 'N/A')}",
            f"Last Top-up: {card_data.get('last_topped_at', 'N/A')}",
        ]
        
        for line in info_lines:
            c.drawString(margin + 0.2 * inch, y, line)
            y -= 0.2 * inch
        
        # Transaction history
        if transactions:
            y -= 0.3 * inch
            c.setFont("Helvetica-Bold", 14)
            c.drawString(margin, y, "Recent Transactions")
            y -= 0.25 * inch
            
            c.setFont("Helvetica", 10)
            for txn in transactions[:10]:  # Show last 10
                txn_line = (f"{txn.get('timestamp', '')} | "
                           f"{txn.get('type', '').upper()}: "
                           f"{txn.get('amount', 0):.2f} EGP | "
                           f"Balance: {txn.get('balance_after', 0):.2f} EGP")
                c.drawString(margin + 0.2 * inch, y, txn_line)
                y -= 0.18 * inch
                
                # Check if we need a new page
                if y < margin:
                    c.showPage()
                    y = height - margin
                    c.setFont("Helvetica", 10)
        
        # IMPORTANT: Show the page to finalize the content
        c.showPage()
