"""
Modern, professional PDF reports generator for transactions.
Produces visually impressive, well-structured reports with charts and statistics.
Enhanced with modern design, RTL Arabic support, and professional styling.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from io import BytesIO
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont 
from tkinter import Toplevel, messagebox
from tkinter import ttk
from tkinter import filedialog

# --- FONT CONFIGURATION ---
# IMPORTANT: This path must be correct for the script environment.
ARABIC_FONT_FILE = "NotoSansArabic-VariableFont_wdth,wght.ttf"
# Updated path: relative to project root (rfid_reception/) instead of dialogs/
ARABIC_FONT_PATH = Path(__file__).parent.parent.parent / "assets" / "fonts" / ARABIC_FONT_FILE
ARABIC_FONT_NAME = "NotoArabic"

logger = logging.getLogger(__name__)

# Try to register the Arabic font; fall back gracefully if it fails
try:
    # Use Path().as_posix() to ensure cross-platform compatibility for TTFont
    pdfmetrics.registerFont(TTFont(ARABIC_FONT_NAME, ARABIC_FONT_PATH.as_posix()))
    pdfmetrics.registerFont(TTFont(f"{ARABIC_FONT_NAME}-Bold", ARABIC_FONT_PATH.as_posix()))
    
    ARABIC_REPORTLAB_FONT = ARABIC_FONT_NAME 
    logger.info(f"ReportLab Arabic font '{ARABIC_FONT_NAME}' registered.")
except Exception as e:
    ARABIC_REPORTLAB_FONT = "Helvetica" 
    logger.warning(f"Failed to register NotoSansArabic font. PDF generation will use default: {e}")

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, 
        Image, KeepTogether, Frame, PageTemplate, Flowable
    )
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logging.warning("reportlab not installed. PDF generation will be unavailable.")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logging.warning("matplotlib not installed. Charts will be unavailable.")

try:
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False
    logging.warning("python-bidi not installed. Arabic RTL support will be limited.")

try:
    from arabic_reshaper import reshape
    HAS_ARABIC_RESHAPER = True
except ImportError:
    HAS_ARABIC_RESHAPER = False
    logging.warning("arabic-reshaper not installed. Arabic text will not be properly connected.")


class ArabicTextHelper:
    """Helper class for Arabic text handling and RTL support."""
    
    ARABIC_NUMERALS = '٠١٢٣٤٥٦٧٨٩'
    WESTERN_NUMERALS = '0123456789'
    
    # Arabic translations
    TRANSLATIONS = {
        "Daily Report": "تقرير يومي", "Weekly Report": "تقرير أسبوعي", "Monthly Report": "تقرير شهري", "Custom Report": "تقرير مخصص", "Selected Cards Report": "تقرير البطاقات المختارة",
        "Period": "الفترة الزمنية", "Key Metrics": "المقاييس الرئيسية", "Transactions": "المعاملات", "Analytics": "التحليلات", "Card Information": "معلومات البطاقة", "Transaction History": "سجل المعاملات",
        "ID": "الرقم", "Card UID": "معرف البطاقة", "Type": "النوع", "Amount (EGP)": "المبلغ (جنيه)", "Balance (EGP)": "الرصيد (جنيه)", "Balance After (EGP)": "الرصيد بعد (جنيه)", "Employee": "الموظف", 
        "Timestamp": "التاريخ والوقت", "Created": "تاريخ الإنشاء", "Last Top-up": "آخر شحن", "Notes": "ملاحظات", "Transaction Count": "عدد المعاملات", "Metric": "المقياس", "Value": "القيمة", 
        "Total Transactions": "إجمالي المعاملات", "Total Cards": "إجمالي البطاقات", "Aggregate Balance": "إجمالي الرصيد", "Top-ups": "الشحنات", "Reads": "القراءات", "Total Amount": "الإجمالي", 
        "Average Transaction": "متوسط المعاملة", "TOP-UP": "شحن", "READ": "قراءة", "TOPUP": "شحن", "Generated on": "تم إنشاؤه في", "Page": "الصفحة", "TOTAL": "الإجمالي", "N/A": "غير متاح", 
        "No transactions available for this card.": "لا توجد معاملات متاحة لهذه البطاقة.", "Generated Date": "تاريخ الإنشاء", "Transaction Types Distribution": "توزيع أنواع المعاملات", 
        "Daily Top-up Amounts": "مبالغ الشحن اليومية", "Date": "التاريخ"
    }
    
    @classmethod
    def translate(cls, text: str, use_arabic: bool = True) -> str:
        if not use_arabic: return text
        return cls.TRANSLATIONS.get(text, text)
    
    @classmethod
    def to_arabic_numerals(cls, number: int) -> str:
        """Convert Western numerals to Arabic numerals."""
        western = str(number)
        arabic = ""
        for char in western:
            if char.isdigit():
                arabic += cls.ARABIC_NUMERALS[int(char)]
            else:
                arabic += char
        return arabic
    
    @classmethod
    def format_date_arabic(cls, dt: Optional[datetime]) -> str:
        if not dt: 
            return cls.translate("N/A")
        
        try:
            # Arabic month names
            arabic_months = [
                "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
            ]
            
            # Get date components and convert to Arabic numerals
            day = cls.to_arabic_numerals(dt.day)
            month_name = arabic_months[dt.month - 1]
            year = cls.to_arabic_numerals(dt.year)
            
            # Format time in 24-hour format with Arabic numerals
            hour = cls.to_arabic_numerals(dt.hour)
            minute = cls.to_arabic_numerals(dt.minute).zfill(2)
            
            # Format: ٢١ أكتوبر ٢٠٢٥ - ١٤:٣٠
            return f"{day} {month_name} {year} - {hour}:{minute}"
            
        except Exception as e:
            logger.warning(f"Error formatting date in Arabic: {e}")
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    @classmethod
    def format_date_arabic_dmy(cls, dt: Optional[datetime], include_time: bool = True) -> str:
        """Format date as 'time - day month year' in Arabic (UI table)."""
        if not dt:
            return cls.translate("N/A")
        try:
            # Arabic month names
            arabic_months = [
                "يناير","فبراير","مارس","أبريل","مايو","يونيو",
                "يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"
            ]
            # ensure datetime instance
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            # numerals
            day = cls.to_arabic_numerals(dt.day)
            month = arabic_months[dt.month-1]
            year = cls.to_arabic_numerals(dt.year)
            if include_time:
                hour = cls.to_arabic_numerals(dt.hour)
                minute = cls.to_arabic_numerals(dt.minute).zfill(2)
                return f"{hour}:{minute} - {day} {month} {year}"
            return f"{day} {month} {year}"
        except Exception:
            return cls.translate("N/A")
    
    @classmethod
    def format_currency_arabic(cls, amount: float) -> str:
        try:
            formatted = f"{amount:,.2f}"; arabic = ""
            for char in formatted:
                if char.isdigit(): arabic += cls.ARABIC_NUMERALS[int(char)]
                else: arabic += char
            return arabic
        except Exception as e:
            logger.warning(f"Error formatting currency: {e}")
            return f"{amount:,.2f}"
            
    @classmethod
    def process_arabic_text(cls, text: str) -> str:
        """Apply Arabic reshaping and BiDi algorithm for correct RTL rendering."""
        try:
            # Step 1: reshape to connect Arabic letters (presentation forms)
            reshaped = reshape(text) if 'HAS_ARABIC_RESHAPER' in globals() and HAS_ARABIC_RESHAPER else text
            # Step 2: apply BiDi to reorder for RTL display
            return get_display(reshaped) if HAS_BIDI else reshaped
        except Exception as e:
            logger.warning(f"Arabic text processing failed for text: {text[:50]}... Error: {e}")
            return text


class ModernPDFHeaderFooter(PageTemplate):
    """Modern PDF header and footer with branding."""
    
    def __init__(self, company_name: str = "Card Management System", 
                 use_arabic: bool = False, *args, **kwargs):
        frame = Frame(
            0.8 * inch, 0.8 * inch, 
            A4[0] - 1.6 * inch, A4[1] - 1.6 * inch, 
            id='normal'
        )
        super().__init__(frames=[frame], *args, **kwargs)
        self.company_name = company_name
        self.use_arabic = use_arabic
        self.primary_color = HexColor("#2E86AB")
        self.secondary_color = HexColor("#A23B72")
        self.accent_color = HexColor("#06A77D")
        self.arabic_font = ARABIC_REPORTLAB_FONT
    
    def before_page(self, canvas_obj, doc):
        """Draw modern header."""
        canvas_obj.saveState()
        width, height = letter if not hasattr(doc, '_pagesize') else doc._pagesize
        
        # Decorative line
        canvas_obj.setStrokeColor(self.primary_color); canvas_obj.setLineWidth(3)
        canvas_obj.line(0.5 * inch, height - 0.6 * inch, width - 0.5 * inch, height - 0.6 * inch)
        
        # Company name
        font_name = self.arabic_font if self.use_arabic else "Helvetica-Bold"
        canvas_obj.setFont(font_name, 11); canvas_obj.setFillColor(self.primary_color)
        company_text = ArabicTextHelper.process_arabic_text(self.company_name) if self.use_arabic else self.company_name
        
        if self.use_arabic:
             canvas_obj.drawRightString(width - 0.5 * inch, height - 0.35 * inch, company_text)
        else:
             canvas_obj.drawString(0.5 * inch, height - 0.35 * inch, company_text)
        
        # Generation date and time
        canvas_obj.setFont(self.arabic_font if self.use_arabic else "Helvetica", 8)
        canvas_obj.setFillColor(HexColor("#666666"))
        date_raw = datetime.now()
        date_text = ArabicTextHelper.format_date_arabic(date_raw) if self.use_arabic else date_raw.strftime("%Y-%m-%d %H:%M:%S")
        date_text_proc = ArabicTextHelper.process_arabic_text(date_text)
        
        if self.use_arabic:
            canvas_obj.drawString(0.5 * inch, height - 0.35 * inch, date_text_proc)
        else:
            canvas_obj.drawRightString(width - 0.5 * inch, height - 0.35 * inch, date_text_proc)
        
        canvas_obj.restoreState()
    
    def after_page(self, canvas_obj, doc):
        """Draw modern footer."""
        canvas_obj.saveState()
        width, height = letter if not hasattr(doc, '_pagesize') else doc._pagesize
        
        # Footer line
        canvas_obj.setStrokeColor(HexColor("#E0E0E0")); canvas_obj.setLineWidth(0.5)
        canvas_obj.line(0.5 * inch, 0.6 * inch, width - 0.5 * inch, 0.6 * inch)
        
        # Page number
        canvas_obj.setFont(self.arabic_font if self.use_arabic else "Helvetica", 8)
        canvas_obj.setFillColor(HexColor("#999999"))
        page_label = ArabicTextHelper.translate("Page", self.use_arabic)
        page_num_str = ArabicTextHelper.to_arabic_numerals(doc.page) if self.use_arabic else str(doc.page)
        page_text = f"{page_label} {page_num_str}"
        page_text_proc = ArabicTextHelper.process_arabic_text(page_text)
        
        canvas_obj.drawRightString(width - 0.5 * inch, 0.35 * inch, page_text_proc)
        
        canvas_obj.restoreState()


class ModernChartGenerator:
    """Generate modern, professional charts for PDF reports."""
    
    COLORS = {
        'topup': '#06A77D', 'read': '#2E86AB', 'accent': '#A23B72', 'warning': '#F18F01',
        'danger': '#C1121F', 'light': '#F5F5F5', 'dark': '#2C3E50'
    }
    
    @staticmethod
    def generate_transaction_pie_chart(transactions: List[Dict], 
                                       width: int = 4, height: int = 4,
                                       use_arabic: bool = False) -> Optional[BytesIO]:
        """Generate modern pie chart of transaction types."""
        if not HAS_MATPLOTLIB: return None
        topup_count = sum(1 for t in transactions if t['type'] == 'topup')
        read_count = sum(1 for t in transactions if t['type'] == 'read')
        if topup_count == 0 and read_count == 0: return None
        
        fig, ax = plt.subplots(figsize=(width, height), facecolor='white')
        sizes = [topup_count, read_count]
        label_topup = ArabicTextHelper.process_arabic_text(f'{ArabicTextHelper.translate("TOP-UP", use_arabic)}\n({ArabicTextHelper.to_arabic_numerals(topup_count) if use_arabic else topup_count})')
        label_read = ArabicTextHelper.process_arabic_text(f'{ArabicTextHelper.translate("READ", use_arabic)}\n({ArabicTextHelper.to_arabic_numerals(read_count) if use_arabic else read_count})')
        labels = [label_topup, label_read]
        
        colors_pie = [ModernChartGenerator.COLORS['topup'], ModernChartGenerator.COLORS['read']]
        text_props = {'fontsize': 11, 'weight': 'bold', 'family': 'sans-serif'}
        
        ax.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90,
            textprops=text_props, explode=(0.05, 0.05), shadow=True)
        
        title_raw = ArabicTextHelper.translate("Transaction Types Distribution", use_arabic)
        title_proc = ArabicTextHelper.process_arabic_text(title_raw) if use_arabic else title_raw
        ax.set_title(title_proc, fontsize=13, weight='bold', pad=20, color=ModernChartGenerator.COLORS['dark'])
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        img_buffer.seek(0); plt.close(fig)
        return img_buffer
    
    @staticmethod
    def generate_daily_amount_chart(transactions: List[Dict], 
                                    width: int = 7, height: int = 4,
                                    use_arabic: bool = False) -> Optional[BytesIO]:
        """Generate modern bar chart of daily amounts."""
        if not HAS_MATPLOTLIB: return None
        daily_data = {};
        for t in transactions:
            date = t['timestamp'].date()
            if date not in daily_data: daily_data[date] = 0
            if t['type'] == 'topup': daily_data[date] += t['amount']
        if not daily_data: return None
        
        dates = sorted(daily_data.keys()); amounts = [daily_data[d] for d in dates]
        fig, ax = plt.subplots(figsize=(width, height), facecolor='white')
        
        bars = ax.bar(range(len(dates)), amounts, color=ModernChartGenerator.COLORS['topup'], 
                     edgecolor=ModernChartGenerator.COLORS['dark'], linewidth=1.5, alpha=0.85)
        
        xlabel_proc = ArabicTextHelper.process_arabic_text(ArabicTextHelper.translate("Date", use_arabic))
        ylabel_proc = ArabicTextHelper.process_arabic_text(ArabicTextHelper.translate("Amount (EGP)", use_arabic))
        title_proc = ArabicTextHelper.process_arabic_text(ArabicTextHelper.translate("Daily Top-up Amounts", use_arabic))
        
        font_config = {'fontname': 'sans-serif'}
        
        ax.set_xlabel(xlabel_proc, fontsize=11, weight='bold', color=ModernChartGenerator.COLORS['dark'], **font_config)
        ax.set_ylabel(ylabel_proc, fontsize=11, weight='bold', color=ModernChartGenerator.COLORS['dark'], **font_config)
        ax.set_title(title_proc, fontsize=13, weight='bold', pad=20, color=ModernReportsGenerator.DARK_TEXT, **font_config)
        ax.set_xticks(range(len(dates))); ax.set_xticklabels([d.strftime('%m-%d') for d in dates], rotation=45, fontsize=9)
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        img_buffer.seek(0); plt.close(fig)
        return img_buffer


class ModernReportsGenerator:
    """Generate modern, professional PDF reports with Arabic support."""
    
    PRIMARY_COLOR = HexColor("#2E86AB"); SECONDARY_COLOR = HexColor("#A23B72"); SUCCESS_COLOR = HexColor("#06A77D")
    WARNING_COLOR = HexColor("#F18F01"); DANGER_COLOR = HexColor("#C1121F"); LIGHT_BG = HexColor("#F5F5F5")
    LIGHT_GRAY = HexColor("#EEEEEE"); DARK_TEXT = HexColor("#2C3E50"); MEDIUM_TEXT = HexColor("#555555")
    
    def __init__(self, db_service, output_dir: str = 'reports', 
                 company_name: str = "Card Management System",
                 use_arabic: bool = False):
        """Initialize reports generator."""
        if use_arabic and not HAS_BIDI:
            raise ImportError("Arabic support requires 'python-bidi' library.")
        if use_arabic and ARABIC_REPORTLAB_FONT == "Helvetica":
            logger.warning("Arabic font registration failed. PDF rendering may be incorrect.")
        
        self.db_service = db_service
        self.output_dir = Path(output_dir); self.output_dir.mkdir(exist_ok=True)
        self.company_name = company_name; self.use_arabic = use_arabic
        self.chart_generator = ModernChartGenerator(); self.arabic_font = ARABIC_REPORTLAB_FONT 
        
    def _translate(self, text: str) -> str:
        """Translate text if Arabic is enabled."""
        return ArabicTextHelper.translate(text, self.use_arabic)
        
    def _bidi_process(self, text: str) -> str:
        """Process Arabic text for RTL display if Arabic is enabled."""
        if self.use_arabic:
            return ArabicTextHelper.process_arabic_text(text)
        return text

    def _calculate_statistics(self, transactions: List[Dict]) -> Dict:
        """Calculate report statistics."""
        topup_transactions = [t for t in transactions if t['type'] == 'topup']
        total_topup_amount = sum(t['amount'] for t in topup_transactions)
        total_read_amount = sum(t['amount'] for t in [t for t in transactions if t['type'] == 'read'])
        
        return {
            'total_transactions': len(transactions),
            'topup_count': len(topup_transactions),
            'read_count': len([t for t in transactions if t['type'] == 'read']),
            'total_topup_amount': total_topup_amount,
            'total_read_amount': total_read_amount,
            'total_amount': total_topup_amount + total_read_amount,
            'avg_transaction': (total_topup_amount + total_read_amount) / len(transactions) if transactions else 0
        }
    
    def _create_modern_cover_page(self, report_title: str, period: str, stats: Dict) -> List:
        """Create modern cover page elements."""
        elements = []; styles = getSampleStyleSheet()
        
        font_name = self.arabic_font; font_name_bold = f"{font_name}-Bold"
        text_align = TA_RIGHT if self.use_arabic else TA_CENTER
        
        title_style = ParagraphStyle('ModernTitle', parent=styles['Heading1'], fontSize=42, textColor=self.PRIMARY_COLOR, alignment=text_align, fontName=font_name_bold, leading=50)
        subtitle_style = ParagraphStyle('ModernSubtitle', parent=styles['Normal'], fontSize=18, textColor=self.DARK_TEXT, alignment=text_align, fontName=font_name_bold)
        meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=10, textColor=self.MEDIUM_TEXT, alignment=text_align, fontName=font_name)
        
        elements.append(Spacer(1, 1.2 * inch))
        elements.append(Paragraph(self._bidi_process(self.company_name), subtitle_style)); elements.append(Spacer(1, 0.2 * inch))
        
        elements.append(Paragraph(self._bidi_process(self._translate(report_title)), title_style)); elements.append(Spacer(1, 0.15 * inch))
        
        period_label = self._bidi_process(self._translate('Period'))
        elements.append(Paragraph(f"<font color='{self.MEDIUM_TEXT.hexval()}' fontName='{font_name_bold}'>{period_label}:</font> <font fontName='{font_name}'>{self._bidi_process(period)}</font>", meta_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        elements.append(Paragraph(self._bidi_process(self._translate("Key Metrics")), subtitle_style)); elements.append(Spacer(1, 0.15 * inch))
        
        total_amount_str = f"EGP {ArabicTextHelper.format_currency_arabic(stats['total_amount'])}" if self.use_arabic else f"EGP {stats['total_amount']:.2f}"
        avg_transaction_str = f"EGP {ArabicTextHelper.format_currency_arabic(stats['avg_transaction'])}" if self.use_arabic else f"EGP {stats['avg_transaction']:.2f}"
                               
        # Reversed: Value column first, then Metric column
        stats_data = [
            [self._bidi_process(self._translate('Value')), self._bidi_process(self._translate('Metric'))],
            [self._bidi_process(ArabicTextHelper.to_arabic_numerals(stats['total_transactions']) if self.use_arabic else str(stats['total_transactions'])), self._bidi_process(self._translate('Total Transactions'))],
            [self._bidi_process(f"{ArabicTextHelper.to_arabic_numerals(stats['topup_count']) if self.use_arabic else stats['topup_count']} (EGP {stats['total_topup_amount']:.2f})"), self._bidi_process(self._translate('Top-ups'))],
            [self._bidi_process(f"{ArabicTextHelper.to_arabic_numerals(stats['read_count']) if self.use_arabic else stats['read_count']} (EGP {stats['total_read_amount']:.2f})"), self._bidi_process(self._translate('Reads'))],
            [self._bidi_process(total_amount_str), self._bidi_process(self._translate('Total Amount'))],
            [self._bidi_process(avg_transaction_str), self._bidi_process(self._translate('Average Transaction'))]
        ]
        
        if self.use_arabic:
            stats_data = [row[::-1] for row in stats_data]; col_align_left = 'RIGHT'; col_align_right = 'LEFT'
        else:
            col_align_left = 'LEFT'; col_align_right = 'RIGHT'
        
        stats_table = Table(stats_data, colWidths=[2.5 * inch, 3 * inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), font_name_bold), ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), self.LIGHT_BG), ('TEXTCOLOR', (0, 1), (-1, -1), self.DARK_TEXT),
            ('ALIGN', (0, 1), (0, -1), col_align_left), ('ALIGN', (1, 1), (1, -1), col_align_right),
            ('FONTNAME', (0, 1), (-1, -1), font_name), ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_GRAY]),
            ('GRID', (0, 0), (-1, -1), 1, HexColor("#DDDDDD")),
        ]))
        
        elements.append(stats_table); elements.append(Spacer(1, 0.4 * inch))
        
        gen_date = ArabicTextHelper.format_date_arabic(datetime.now()) if self.use_arabic else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        gen_text = self._bidi_process(f"{self._translate('Generated on')} {gen_date}")
        elements.append(Paragraph(f"<font color='#999999' size=8 fontName='{font_name}'>{gen_text}</font>", meta_style))
        
        return elements
    
    def _create_modern_transactions_table(self, transactions: List[Dict]) -> Table:
        """Create modern formatted transactions table."""
        
        font_name = self.arabic_font; font_name_bold = f"{font_name}-Bold"
        
        table_data_raw = [
            [self._translate('ID'), self._translate('Card UID'), self._translate('Type'), self._translate('Amount (EGP)'),
             self._translate('Balance After (EGP)'), self._translate('Employee'), self._translate('Timestamp'), self._translate('Notes')]
        ]
        
        for i, t in enumerate(transactions):
            tx_type = self._translate('TOP-UP') if t['type'] == 'topup' else self._translate('READ')
            amount = ArabicTextHelper.format_currency_arabic(t['amount']) if self.use_arabic else f"{t['amount']:.2f}"
            balance = ArabicTextHelper.format_currency_arabic(t['balance_after']) if self.use_arabic else f"{t['balance_after']:.2f}"
            
            row = [
                self._bidi_process(str(t.get('id', ''))),
                self._bidi_process(t['card_uid'][:12] + '...' if len(t['card_uid']) > 12 else t['card_uid']),
                self._bidi_process(tx_type),
                self._bidi_process(amount),
                self._bidi_process(balance),
                self._bidi_process(t.get('employee', 'N/A')[:15]),
                self._bidi_process(ArabicTextHelper.format_date_arabic(t['timestamp']) if self.use_arabic else t['timestamp'].strftime('%Y-%m-%d %H:%M')),
                self._bidi_process((t.get('notes', 'N/A') or self._translate('N/A'))[:20])
            ]
            table_data_raw.append(row)
        
        # Add total row
        total_amount = sum(t['amount'] for t in transactions if t['type'] == 'topup')
        total_formatted = ArabicTextHelper.format_currency_arabic(total_amount) if self.use_arabic else f"{total_amount:.2f}"
        total_row = ['', '', f"<b>{self._bidi_process(self._translate('TOTAL'))}</b>", f"<b>{self._bidi_process(total_formatted)}</b>", '', '', '', '']
        table_data_raw.append(total_row)
        
        # Reverse columns for RTL display of table data
        if self.use_arabic:
            table_data = [row[::-1] for row in table_data_raw]
            header_align = 'RIGHT'; content_align_left = 'RIGHT'; content_align_right = 'LEFT'
            total_text_col = 5; total_value_col = 4
        else:
            table_data = table_data_raw
            header_align = 'CENTER'; content_align_left = 'LEFT'; content_align_right = 'RIGHT'
            total_text_col = 2; total_value_col = 3
        
        col_widths = [0.5*inch, 1.2*inch, 0.8*inch, 1*inch, 1*inch, 1*inch, 1.2*inch, 1.3*inch]
        table = Table(table_data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), header_align), ('FONTNAME', (0, 0), (-1, 0), font_name_bold), ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 1), (-1, -2), content_align_left), ('ALIGN', (3, 1), (4, -2), content_align_right),
            ('FONTSIZE', (0, 1), (-1, -2), 8), ('FONTNAME', (0, 1), (-1, -2), font_name),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, self.LIGHT_BG]),
            ('BACKGROUND', (0, -1), (-1, -1), self.SUCCESS_COLOR), ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), font_name_bold),
            ('ALIGN', (total_text_col, -1), (total_text_col, -1), 'RIGHT'), ('ALIGN', (total_value_col, -1), (total_value_col, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#E0E0E0")),
        ]))
        
        return table
    
    def _get_report_filename(self, report_type: str, extension: str = 'pdf', 
                            identifier: str = '') -> Path:
        """Generate report filename with timestamp."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_report_{identifier}_{timestamp}.{extension}"
        return self.output_dir / filename
    
    def _generate_pdf(self, filename: str, elements: List, 
                     landscape_mode: bool = False) -> str:
        """Generate modern PDF document."""
        if not HAS_REPORTLAB:
            raise ImportError("reportlab is required for PDF generation.")
        
        filepath = self.output_dir / filename
        
        try:
            pagesize = landscape(A4) if landscape_mode else A4
            doc = SimpleDocTemplate(
                str(filepath), pagesize=pagesize, rightMargin=0.5 * inch, leftMargin=0.5 * inch, 
                topMargin=0.9 * inch, bottomMargin=0.9 * inch
            )
            
            header_footer = ModernPDFHeaderFooter(
                self.company_name, use_arabic=self.use_arabic, id='standard_template'
            )
            doc.addPageTemplates([header_footer])
            
            doc.build(elements)
            logger.info(f"PDF report generated: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise

    # --- PUBLIC REPORT GENERATION METHODS (PDF ONLY) ---

    def generate_report(self, report_type: str, transactions: List[Dict], period: str, 
                        identifier: str = '', landscape_mode: bool = False) -> str:
        """A consolidated PDF generator for all standard report types."""
        stats = self._calculate_statistics(transactions)
        
        elements = self._create_modern_cover_page(report_type, period, stats)
        elements.append(PageBreak())
        
        # Transactions section
        tx_title_style = ParagraphStyle('TxTitle', parent=getSampleStyleSheet()['Heading2'], fontSize=16, textColor=self.PRIMARY_COLOR, spaceAfter=12, fontName=f"{self.arabic_font}-Bold")
        elements.append(Paragraph(self._bidi_process(self._translate("Transactions")), tx_title_style))
        elements.append(Spacer(1, 0.15 * inch))
        elements.append(self._create_modern_transactions_table(transactions))
        
        # Charts section
        if HAS_MATPLOTLIB and transactions:
            elements.append(PageBreak())
            analytics_style = ParagraphStyle('AnalyticsTitle', parent=getSampleStyleSheet()['Heading2'], fontSize=16, textColor=self.PRIMARY_COLOR, spaceAfter=12, fontName=f"{self.arabic_font}-Bold")
            elements.append(Paragraph(self._bidi_process(self._translate("Analytics")), analytics_style))
            elements.append(Spacer(1, 0.15 * inch))
            
            # Pie Chart
            pie_chart = ModernChartGenerator.generate_transaction_pie_chart(transactions, use_arabic=self.use_arabic)
            if pie_chart:
                img = Image(pie_chart, width=4*inch, height=4*inch); elements.append(img); elements.append(Spacer(1, 0.2 * inch))
            
            # Bar Chart
            bar_chart = ModernChartGenerator.generate_daily_amount_chart(transactions, width=7, height=4, use_arabic=self.use_arabic)
            if bar_chart:
                img = Image(bar_chart, width=7*inch, height=4*inch); elements.append(img)

        pdf_path = self._get_report_filename(report_type.lower().replace(' ', '_'), 'pdf', identifier)
        return self._generate_pdf(pdf_path.name, elements, landscape_mode=landscape_mode)


    def generate_daily_report(self, date: Optional[datetime] = None) -> str:
        """Generate modern daily report."""
        date = date or datetime.now().date()
        if isinstance(date, str): date = datetime.strptime(date, '%Y-%m-%d').date()
        
        start_date = datetime.combine(date, datetime.min.time())
        end_date = datetime.combine(date, datetime.max.time())
        
        # Assuming db_service is implemented and returns List[Dict]
        transactions = self.db_service.get_transactions(start_date=start_date, end_date=end_date) if hasattr(self.db_service, 'get_transactions') else []
        period = date.strftime('%Y-%m-%d')
        identifier = date.strftime('%Y%m%d')
        
        return self.generate_report('Daily Report', transactions, period, identifier)

    def generate_weekly_report(self, week_start: Optional[datetime] = None) -> str:
        """Generate modern weekly report."""
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        elif isinstance(week_start, str):
            week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
        
        week_end = week_start + timedelta(days=6)
        start_date = datetime.combine(week_start, datetime.min.time())
        end_date = datetime.combine(week_end, datetime.max.time())
        
        transactions = self.db_service.get_transactions(start_date=start_date, end_date=end_date) if hasattr(self.db_service, 'get_transactions') else []
        period = f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
        identifier = week_start.strftime('%Y%m%d')
        
        return self.generate_report('Weekly Report', transactions, period, identifier, landscape_mode=True)

    def generate_monthly_report(self, month: Optional[int] = None, year: Optional[int] = None) -> str:
        """Generate modern monthly report."""
        now = datetime.now()
        month = month or now.month; year = year or now.year
        
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month % 12 + 1, 1) - timedelta(seconds=1) if month < 12 else datetime(year + 1, 1, 1) - timedelta(seconds=1)
        
        transactions = self.db_service.get_transactions(start_date=start_date, end_date=end_date) if hasattr(self.db_service, 'get_transactions') else []
        period = start_date.strftime('%B %Y')
        identifier = f"{year}{month:02d}"
        
        return self.generate_report('Monthly Report', transactions, period, identifier, landscape_mode=True)

    def generate_custom_report(self, start_date: datetime, end_date: datetime, card_uid: Optional[str] = None) -> str:
        """Generate modern custom date range report."""
        if isinstance(start_date, str): start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str): end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        transactions = self.db_service.get_transactions(start_date=start_date, end_date=end_date, card_uid=card_uid) if hasattr(self.db_service, 'get_transactions') else []
        
        period_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        if card_uid: period_str += f" ({self._translate('Card UID')}: {card_uid[:16]}...)"
        
        identifier = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        if card_uid: identifier += f"_{card_uid[:8]}"
        
        return self.generate_report('Custom Report', transactions, period_str, identifier, landscape_mode=True)

    # Note: generate_beautiful_arabic_report is already PDF-only and remains functional.

    def generate_beautiful_arabic_report(self, cards: List[Dict], output_path: Optional[str] = None) -> str:
        """Generate a visually appealing PDF report in Arabic with beautiful styling."""
        if not HAS_REPORTLAB: raise ImportError("reportlab is required for PDF generation")
        
        original_setting = self.use_arabic; self.use_arabic = True
        filepath = Path(output_path) if output_path else self._get_report_filename('arabic', 'pdf')
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Mock transactions and stats for demonstration
        transactions_map = {card['card_uid']: [] for card in cards if 'card_uid' in card}
        total_cards = len(cards); total_balance = sum(card.get('balance', 0) for card in cards)
        avg_balance = total_balance / total_cards if total_cards > 0 else 0
        total_transactions = sum(len(txs) for txs in transactions_map.values())
        
        styles = getSampleStyleSheet()
        font_name = self.arabic_font; font_name_bold = f'{self.arabic_font}-Bold'
        
        title_style = ParagraphStyle('ArabicTitle', parent=styles['Title'], fontName=font_name_bold, fontSize=28, leading=34, alignment=TA_RIGHT, textColor=self.PRIMARY_COLOR, spaceAfter=20)
        subtitle_style = ParagraphStyle('ArabicSubtitle', parent=styles['Heading2'], fontName=font_name_bold, fontSize=18, leading=22, alignment=TA_RIGHT, textColor=self.SECONDARY_COLOR, spaceAfter=12)
        heading_style = ParagraphStyle('ArabicHeading', parent=styles['Heading3'], fontName=font_name_bold, fontSize=14, leading=18, alignment=TA_RIGHT, textColor=self.PRIMARY_COLOR, spaceAfter=8)
        body_rtl_style = ParagraphStyle('ArabicBody', parent=styles['Normal'], fontName=font_name, fontSize=10, leading=14, alignment=TA_RIGHT, spaceAfter=8, wordWrap='RTL')
        
        elements = []
        elements.append(Spacer(1, 1 * inch))
        elements.append(Paragraph(self._bidi_process("تقرير بطاقات نظام الاستقبال"), title_style))
        elements.append(Paragraph(self._bidi_process("نظام إدارة البطاقات الذكية"), subtitle_style))
        elements.append(Spacer(1, 0.5 * inch))
        
        # Format current date in Arabic
        current_date = datetime.now()
        date_str = ArabicTextHelper.format_date_arabic(current_date)
        elements.append(Paragraph(f"<para align='right'>{self._bidi_process('تم إنشاؤه في:')} {date_str}</para>", body_rtl_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Add statistics section
        elements.append(Paragraph(self._bidi_process("الإحصائيات الرئيسية"), heading_style))
        
        # Create statistics data with proper RTL formatting
        stats_data = [
            [self._bidi_process("القيمة"), self._bidi_process("المؤشر")],
            [self._bidi_process(ArabicTextHelper.to_arabic_numerals(total_cards)), self._bidi_process("إجمالي البطاقات")],
            [self._bidi_process(f"{ArabicTextHelper.format_currency_arabic(total_balance)} جنيه"), self._bidi_process("إجمالي الرصيد")],
            [self._bidi_process(f"{ArabicTextHelper.format_currency_arabic(avg_balance)} جنيه"), self._bidi_process("متوسط الرصيد")],
            [self._bidi_process(ArabicTextHelper.to_arabic_numerals(total_transactions)), self._bidi_process("إجمالي المعاملات")],
        ]
        
        # Create and style the statistics table
        stats_table = Table(stats_data, colWidths=[2.5*inch, 3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), self.PRIMARY_COLOR), 
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('FONTNAME', (0, 0), (1, -1), font_name), 
            ('FONTNAME', (0, 0), (1, 0), font_name_bold),  # Bold header
            ('ALIGN', (0, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (1, -1), 0.5, colors.grey), 
            ('ROWBACKGROUNDS', (0, 1), (1, -1), [self.LIGHT_BG, colors.white]),
        ]))
        
        elements.append(stats_table)
        elements.append(PageBreak())
        
        # Add cards list section
        elements.append(Paragraph(self._bidi_process("قائمة البطاقات"), heading_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Prepare table data with RTL processing
        cards_data = []
        
        # Add header row with RTL processing
        header_row = [
            self._bidi_process("الرصيد (جنيه)"),
            self._bidi_process("آخر شحن"),
            self._bidi_process("تاريخ الإنشاء"),
            self._bidi_process("معرّف البطاقة")
        ]
        cards_data.append(header_row)
        
        # Add data rows with proper RTL processing
        for card in sorted(cards, key=lambda x: x.get('balance', 0), reverse=True):
            card_uid = card.get('card_uid', 'N/A')
            
            # Format dates with RTL processing
            created = card.get('created_at')
            created_str = self._bidi_process(ArabicTextHelper.format_date_arabic(created)) if created else self._bidi_process('غير متاح')
            
            last_topup = card.get('last_topped_at')
            last_topup_str = self._bidi_process(ArabicTextHelper.format_date_arabic(last_topup)) if last_topup else self._bidi_process('غير متاح')
            
            balance = self._bidi_process(ArabicTextHelper.format_currency_arabic(card.get('balance', 0)))
            
            # Add row with proper RTL order (reversed from English order)
            cards_data.append([
                balance,
                last_topup_str,
                created_str,
                self._bidi_process(card_uid)
            ])
        
        # Calculate column widths based on content
        col_widths = [
            1.2 * inch,  # Balance
            2.0 * inch,  # Last top-up
            2.0 * inch,  # Created at
            1.5 * inch   # Card UID
        ]
        
        # Create and style the cards table
        cards_table = Table(cards_data, colWidths=col_widths, repeatRows=1)
        cards_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), font_name_bold),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('ALIGN', (0, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            
            # Grid and alternating row colors
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
            
            # Cell padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(cards_table)
        
        # Create the PDF document with proper RTL settings
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=0.8 * inch,
            leftMargin=0.8 * inch,
            topMargin=0.8 * inch,
            bottomMargin=0.8 * inch,
            initialFontName=font_name,
            initialFontSize=10,
            title=self._bidi_process("تقرير البطاقات"),
            author=self._bidi_process("نظام إدارة البطاقات"),
            subject=self._bidi_process("تقرير شامل عن البطاقات"),
            creator=self._bidi_process("نظام إدارة البطاقات الذكية"),
            encoding='utf-8'
        )
        
        # Add RTL page template
        header_footer = ModernPDFHeaderFooter(
            self._bidi_process("نظام إدارة البطاقات"),
            use_arabic=True,
            id='arabic_template'
        )
        doc.addPageTemplates([header_footer])
        
        # Build the PDF document
        doc.build(elements)
        
        # Restore original language setting
        self.use_arabic = original_setting
        logger.info(f"Beautiful Arabic report generated: {filepath}")
        return str(filepath)


class ReportsGenerator(ModernReportsGenerator):
    """Backward-compatible alias for legacy imports."""
    pass

# Remove PyQt imports and use Tkinter instead
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime

class ViewAllCardsDialog(tk.Toplevel):
    """Modern UI for viewing all cards with enhanced visual appeal."""
    
    # Modern color palette
    PRIMARY_COLOR = "#2E86AB"
    SECONDARY_COLOR = "#A23B72"
    SUCCESS_COLOR = "#06A77D"
    WARNING_COLOR = "#F18F01"
    LIGHT_BG = "#F5F5F5"
    CARD_BG = "#FFFFFF"
    TEXT_PRIMARY = "#2C3E50"
    TEXT_SECONDARY = "#555555"
    BORDER_COLOR = "#E0E0E0"
    
    def __init__(self, parent, db_service):
        super().__init__(parent)
        self.db_service = db_service
        self.title("Card Management System - View All Cards")
        self.geometry("1000x700")
        self.resizable(True, True)
        self.minsize(800, 500)
        
        # Configure window style
        self.configure(bg=self.LIGHT_BG)
        
        # Fetch cards data
        try:
            self.cards = self.db_service.get_all_cards()
        except AttributeError:
            self.cards = []
            logging.warning("db_service.get_all_cards() not found; using empty list")
        
        self.filtered_cards = self.cards.copy()
        self.setup_styles()
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_styles(self):
        """Configure modern ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for the theme
        style.configure('Treeview', 
                       background=self.CARD_BG,
                       foreground=self.TEXT_PRIMARY,
                       fieldbackground=self.CARD_BG,
                       borderwidth=0,
                       font=('Segoe UI', 10))
        style.map('Treeview', 
                 background=[('selected', self.PRIMARY_COLOR)],
                 foreground=[('selected', 'white')])
        
        style.configure('Treeview.Heading',
                       background=self.PRIMARY_COLOR,
                       foreground='white',
                       borderwidth=1,
                       font=('Segoe UI', 11, 'bold'))
        style.map('Treeview.Heading',
                 background=[('active', self.SECONDARY_COLOR)])
        
        # Modern buttons
        style.configure('Modern.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10,
                       relief='flat',
                       borderwidth=0)
        
        style.configure('Primary.TButton',
                       background=self.PRIMARY_COLOR,
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)
        style.map('Primary.TButton',
                 background=[('active', self.SECONDARY_COLOR)])
        
        style.configure('Success.TButton',
                       background=self.SUCCESS_COLOR,
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)
        style.map('Success.TButton',
                 background=[('active', '#059969')])
    
    def setup_ui(self):
        """Build the modern UI."""
        # Header section
        self._create_header()
        
        # Statistics panel
        self._create_stats_panel()
        
        # Search and filter section
        self._create_search_section()
        
        # Table section with separator
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', padx=15, pady=10)
        
        self._create_table_section()
        
        # Footer with action buttons
        self._create_footer()
    
    def _create_header(self):
        """Create attractive header section."""
        header_frame = tk.Frame(self, bg=self.PRIMARY_COLOR, height=80)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)
        
        # Title with icon representation
        title_frame = tk.Frame(header_frame, bg=self.PRIMARY_COLOR)
        title_frame.pack(fill='both', expand=True, padx=20, pady=15)
        
        title_label = tk.Label(title_frame, 
                              text="🎫 Card Management System",
                              font=('Segoe UI', 18, 'bold'),
                              fg='white',
                              bg=self.PRIMARY_COLOR)
        title_label.pack(side='left')
        
        subtitle_label = tk.Label(title_frame,
                                 text=f"Viewing {len(self.cards)} card(s)",
                                 font=('Segoe UI', 11),
                                 fg='#E8F4F8',
                                 bg=self.PRIMARY_COLOR)
        subtitle_label.pack(side='left', padx=(20, 0))
    
    def _create_stats_panel(self):
        """Create statistics panel showing key metrics."""
        stats_frame = tk.Frame(self, bg=self.LIGHT_BG)
        stats_frame.pack(fill='x', padx=15, pady=15)
        
        # Calculate statistics
        total_balance = sum(card.get('balance', 0) for card in self.cards)
        avg_balance = total_balance / len(self.cards) if self.cards else 0
        total_cards = len(self.cards)
        
        stats_data = [
            ("📊 Total Cards", str(total_cards), self.PRIMARY_COLOR),
            ("💰 Total Balance", f"EGP {total_balance:,.2f}", self.SUCCESS_COLOR),
            ("📈 Average Balance", f"EGP {avg_balance:,.2f}", self.SECONDARY_COLOR),
        ]
        
        for i, (label, value, color) in enumerate(stats_data):
            self._create_stat_card(stats_frame, label, value, color, i)
    
    def _create_stat_card(self, parent, label, value, color, index):
        """Create individual stat card."""
        card = tk.Frame(parent, bg=self.CARD_BG, relief='flat', bd=1)
        card.configure(highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        card.pack(side='left', expand=True, fill='both', padx=(0, 10) if index < 2 else 0)
        
        label_widget = tk.Label(card,
                               text=label,
                               font=('Segoe UI', 10),
                               fg=self.TEXT_SECONDARY,
                               bg=self.CARD_BG)
        label_widget.pack(padx=15, pady=8, anchor='w')
        
        value_widget = tk.Label(card,
                               text=value,
                               font=('Segoe UI', 14, 'bold'),
                               fg=color,
                               bg=self.CARD_BG)
        value_widget.pack(padx=15, pady=(0, 8), anchor='w')
    
    def _create_search_section(self):
        """Create search and filter controls."""
        search_frame = tk.Frame(self, bg=self.LIGHT_BG)
        search_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        search_label = tk.Label(search_frame,
                               text="🔍 Search Cards",
                               font=('Segoe UI', 10, 'bold'),
                               fg=self.TEXT_PRIMARY,
                               bg=self.LIGHT_BG)
        search_label.pack(side='left', padx=(0, 10))
        
        search_entry = tk.Entry(search_frame,
                               font=('Segoe UI', 10),
                               width=30,
                               relief='flat',
                               bd=1)
        search_entry.configure(highlightbackground=self.BORDER_COLOR, 
                              highlightthickness=1,
                              bg=self.CARD_BG)
        search_entry.pack(side='left', padx=(0, 10), ipady=5)
        search_entry.bind('<KeyRelease>', lambda e: self._filter_cards(search_entry.get()))
        
        # Clear button
        clear_btn = tk.Label(search_frame,
                            text="✕",
                            font=('Segoe UI', 12),
                            fg=self.WARNING_COLOR,
                            bg=self.LIGHT_BG,
                            cursor='hand2')
        clear_btn.pack(side='left', padx=5)
        clear_btn.bind('<Button-1>', lambda e: (search_entry.delete(0, 'end'), 
                                                 self._filter_cards('')))
    
    def _filter_cards(self, search_text):
        """Filter cards based on search text."""
        self.filtered_cards = [
            card for card in self.cards
            if search_text.lower() in card.get('card_uid', '').lower()
        ]
        self._populate_table()
    
    def _create_table_section(self):
        """Create the cards table with modern styling."""
        table_frame = tk.Frame(self, bg=self.LIGHT_BG)
        table_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Scrollbar styling
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        columns = ("UID", "Balance", "Employee", "Status")  # Removed "Created At" and "Last Top-Up"
        self.tree = ttk.Treeview(table_frame, 
                                columns=columns,
                                show='headings',
                                height=15,
                                yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns
        col_widths = [140, 110, 130, 80]  # Adjusted for 4 columns
        col_anchors = ['w', 'center', 'w', 'center']  # Adjusted for 4 columns
        
        for i, (col, width, anchor) in enumerate(zip(columns, col_widths, col_anchors)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)
        
        # Add alternating row colors
        self.tree.tag_configure('oddrow', background=self.CARD_BG)
        self.tree.tag_configure('evenrow', background='#F9F9F9')
        self.tree.tag_configure('positive', foreground=self.SUCCESS_COLOR)
        
        self.tree.pack(fill='both', expand=True)
        self._populate_table()
    
    def _populate_table(self):
        """Populate the table with card data."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Populate with filtered cards
        for i, card in enumerate(self.filtered_cards):
            uid = card.get('card_uid', 'N/A')
            balance = card.get('balance', 0)
            employee = card.get('employee_name', 'N/A')
            
            # Determine status
            status = "✓ Active" if balance > 0 else "⚠ Empty"
            
            values = (
                uid[:12] + '...' if len(uid) > 12 else uid,
                f"EGP {balance:.2f}",
                employee if employee != 'N/A' else 'N/A',
                status
            )  # Removed created_str and last_topup_str
            
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree.insert('', 'end', values=values, tags=(tag, 'positive' if balance > 0 else ''))
    
    def _create_footer(self):
        """Create footer with action buttons."""
        footer_frame = tk.Frame(self, bg=self.LIGHT_BG)
        footer_frame.pack(fill='x', padx=15, pady=15)
        
        # Left side info
        info_label = tk.Label(footer_frame,
                             text=f"Showing {len(self.filtered_cards)} of {len(self.cards)} cards",
                             font=('Segoe UI', 9),
                             fg=self.TEXT_SECONDARY,
                             bg=self.LIGHT_BG)
        info_label.pack(side='left')
        
        # Spacer
        spacer = tk.Frame(footer_frame, bg=self.LIGHT_BG)
        spacer.pack(side='left', expand=True)
        
        # Action buttons
        button_frame = tk.Frame(footer_frame, bg=self.LIGHT_BG)
        button_frame.pack(side='right')
        
        export_btn = tk.Button(button_frame,
                              text="📄 Export Arabic PDF",
                              font=('Segoe UI', 10, 'bold'),
                              bg=self.SUCCESS_COLOR,
                              fg='white',
                              relief='flat',
                              cursor='hand2',
                              padx=15,
                              pady=8,
                              command=self.export_arabic_pdf)
        export_btn.pack(side='left', padx=(0, 10))
        
        close_btn = tk.Button(button_frame,
                             text="✕ Close",
                             font=('Segoe UI', 10, 'bold'),
                             bg='#E8E8E8',
                             fg=self.TEXT_PRIMARY,
                             relief='flat',
                             cursor='hand2',
                             padx=15,
                             pady=8,
                             command=self.on_close)
        close_btn.pack(side='left')
    
    def export_arabic_pdf(self):
        """Export all cards to an Arabic PDF report."""
        if not self.cards:
            messagebox.showwarning("No Cards", 
                                 "No cards available to export.",
                                 parent=self)
            return
        
        default_filename = f"arabic_cards_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Save Arabic PDF Report"
        )
        
        if not output_path:
            return
        
        try:
            generator = ModernReportsGenerator(self.db_service, use_arabic=True)
            final_path = generator.generate_beautiful_arabic_report(self.cards, 
                                                                   output_path=output_path)
            messagebox.showinfo("Export Successful",
                              f"Arabic PDF report saved to:\n{final_path}",
                              parent=self)
        except ImportError as e:
            messagebox.showerror("Missing Dependencies",
                               f"Required libraries are missing:\n{e}",
                               parent=self)
        except Exception as e:
            messagebox.showerror("Export Failed",
                               f"An error occurred:\n{e}",
                               parent=self)
    
    def on_close(self):
        self.destroy()