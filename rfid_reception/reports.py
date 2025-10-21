"""
Modern, professional PDF reports generator for transactions.
Produces visually impressive, well-structured reports with charts and statistics.
Enhanced with modern design, RTL Arabic support, and professional styling.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from threading import Thread
from io import BytesIO
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont 

# --- FONT CONFIGURATION ---
# IMPORTANT: This path must be correct for the script environment.
ARABIC_FONT_FILE = "NotoSansArabic-VariableFont_wdth,wght.ttf"
ARABIC_FONT_PATH = Path(__file__).parent / "assets" / "fonts" / ARABIC_FONT_FILE
ARABIC_FONT_NAME = "NotoArabic"

logger = logging.getLogger(__name__)

# Try to register the Arabic font; fall back gracefully if it fails
try:
    # Use Path().as_posix() to ensure cross-platform compatibility for TTFont
    pdfmetrics.registerFont(TTFont(ARABIC_FONT_NAME, ARABIC_FONT_PATH.as_posix()))
    # Note: Using same font file for Bold variant since NotoSansArabic is a Variable Font
    # ReportLab will use the same font for bold, which is acceptable for Arabic text
    try:
        pdfmetrics.registerFont(TTFont(f"{ARABIC_FONT_NAME}-Bold", ARABIC_FONT_PATH.as_posix()))
    except:
        pass  # Bold variant registration is optional
    
    ARABIC_REPORTLAB_FONT = ARABIC_FONT_NAME 
    logger.info(f"ReportLab Arabic font '{ARABIC_FONT_NAME}' registered successfully.")
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
    ARABIC_MONTHS = [
        'يناير', 'فبراير', 'مارس', 'ابريل', 'مايو', 'يونيو',
        'يوليو', 'اغسطس', 'سبتمبر', 'اكتوبر', 'نوفمبر', 'ديسمبر'
    ]
    
    # Arabic translations (omitted for brevity)
    TRANSLATIONS = {
        "Daily Report": "تقرير يومي", "Weekly Report": "تقرير أسبوعي", "Monthly Report": "تقرير شهري", "Yearly Report": "تقرير سنوي", "Custom Report": "تقرير مخصص", "Selected Cards Report": "تقرير البطاقات المختارة",
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
        """Translate text to Arabic if available."""
        if not use_arabic:
            return text
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
        """Format datetime in Arabic format with Arabic numerals."""
        if not dt:
            return cls.translate("N/A")
        
        try:
            year = cls.to_arabic_numerals(dt.year)
            month = cls.to_arabic_numerals(dt.month)
            day = cls.to_arabic_numerals(dt.day)
            hour = cls.to_arabic_numerals(dt.hour)
            minute = cls.to_arabic_numerals(dt.minute)
            second = cls.to_arabic_numerals(dt.second)
            
            return f"{year}-{month}-{day} {hour}:{minute}:{second}"
        except Exception as e:
            logger.warning(f"Error formatting date in Arabic: {e}")
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    @classmethod
    def format_date_arabic_dmy(cls, dt: Optional[datetime], include_time: bool = True) -> str:
        """Format date as 'day month_name year' in Arabic, with Arabic numerals.
        Example: '٢١ اكتوبر ٢٠٢٥' or with time '٢١ اكتوبر ٢٠٢٥ ١٤:٣٠'."""
        if not dt:
            return cls.translate("N/A")
        try:
            day = cls.to_arabic_numerals(dt.day)
            month_name = cls.ARABIC_MONTHS[dt.month - 1]
            year = cls.to_arabic_numerals(dt.year)
            if include_time:
                hour = cls.to_arabic_numerals(dt.hour)
                minute = cls.to_arabic_numerals(dt.minute)
                return f"{day} {month_name} {year} {hour}:{minute}"
            return f"{day} {month_name} {year}"
        except Exception as e:
            logger.warning(f"Error formatting DMY Arabic date: {e}")
            return dt.strftime('%d %B %Y')
    
    @classmethod
    def format_currency_arabic(cls, amount: float) -> str:
        """Format currency amount with Arabic numerals."""
        try:
            formatted = f"{amount:,.2f}"
            arabic = ""
            for char in formatted:
                if char.isdigit():
                    arabic += cls.ARABIC_NUMERALS[int(char)]
                else:
                    arabic += char
            return arabic
        except Exception as e:
            logger.warning(f"Error formatting currency: {e}")
            return f"{amount:,.2f}"
            
    @classmethod
    def process_arabic_text(cls, text: str) -> str:
        """Apply Arabic reshaping and BiDi algorithm for correct RTL rendering."""
        try:
            # Step 1: Reshape Arabic text to connect letters properly
            if HAS_ARABIC_RESHAPER:
                reshaped_text = reshape(text)
            else:
                reshaped_text = text
            
            # Step 2: Apply BiDi algorithm for RTL text flow
            if HAS_BIDI:
                return get_display(reshaped_text)
            else:
                return reshaped_text
        except Exception as e:
            logger.warning(f"Arabic text processing failed for text: {text[:50]}... Error: {e}")
            return text


class ModernPDFHeaderFooter(PageTemplate):
    """Modern PDF header and footer with branding."""
    
    def __init__(self, company_name: str = "Card Management System", 
                 use_arabic: bool = False, pagesize=None, *args, **kwargs):
        """Initialize header/footer template."""
        pg = pagesize if pagesize else A4
        frame = Frame(
            0.5 * inch, 0.5 * inch, 
            pg[0] - 1.0 * inch, pg[1] - 1.0 * inch, 
            id='normal'
        )
        super().__init__(frames=[frame], pagesize=pg, *args, **kwargs)
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
        
        # Modern decorative line
        canvas_obj.setStrokeColor(self.primary_color)
        canvas_obj.setLineWidth(3)
        canvas_obj.line(0.5 * inch, height - 0.6 * inch, width - 0.5 * inch, height - 0.6 * inch)
        
        # Company name
        font_name = self.arabic_font if self.use_arabic else "Helvetica-Bold"
        
        # Handle font gracefully if Arabic font is not available
        try:
            canvas_obj.setFont(font_name, 11)
        except KeyError:
            logger.warning(f"Font '{font_name}' not available, falling back to Helvetica-Bold")
            canvas_obj.setFont("Helvetica-Bold", 11)
            
        canvas_obj.setFillColor(self.primary_color)
        
        # Process company name for BiDi
        if self.use_arabic:
            # For Arabic text, we need to process it with BiDi BEFORE drawing
            company_text = ArabicTextHelper.process_arabic_text(self.company_name)
            # Draw on the right side for RTL
            canvas_obj.drawRightString(width - 0.5 * inch, height - 0.35 * inch, company_text)
        else:
            canvas_obj.drawString(0.5 * inch, height - 0.35 * inch, self.company_name)
        
        # Generation date and time
        try:
            canvas_obj.setFont(self.arabic_font if self.use_arabic else "Helvetica", 8)
        except KeyError:
            canvas_obj.setFont("Helvetica", 8)
            
        canvas_obj.setFillColor(HexColor("#666666"))
        
        date_raw = datetime.now()
        
        if self.use_arabic:
            # Format date in Arabic DMY numerals and process with BiDi
            date_text = ArabicTextHelper.format_date_arabic_dmy(date_raw, include_time=True)
            date_text_proc = ArabicTextHelper.process_arabic_text(date_text)
            # Draw date on the left for Arabic layout
            canvas_obj.drawString(0.5 * inch, height - 0.35 * inch, date_text_proc)
        else:
            date_text = date_raw.strftime("%Y-%m-%d %H:%M:%S")
            canvas_obj.drawRightString(width - 0.5 * inch, height - 0.35 * inch, date_text)
        
        canvas_obj.restoreState()
    
    def after_page(self, canvas_obj, doc):
        """Draw modern footer."""
        canvas_obj.saveState()
        
        width, height = letter if not hasattr(doc, '_pagesize') else doc._pagesize
        
        # Footer line
        canvas_obj.setStrokeColor(HexColor("#E0E0E0"))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(0.5 * inch, 0.6 * inch, width - 0.5 * inch, 0.6 * inch)
        
        # Page number
        try:
            canvas_obj.setFont(self.arabic_font if self.use_arabic else "Helvetica", 8)
        except KeyError:
            canvas_obj.setFont("Helvetica", 8)
            
        canvas_obj.setFillColor(HexColor("#999999"))
        
        if self.use_arabic:
            page_label = ArabicTextHelper.translate("Page", True)
            page_num_str = ArabicTextHelper.to_arabic_numerals(doc.page)
            # Construct the page text: "الصفحة ١" (Page 1)
            page_text = f"{page_label} {page_num_str}"
            # Apply BiDi processing to the entire string
            page_text_proc = ArabicTextHelper.process_arabic_text(page_text)
        else:
            page_text_proc = f"Page {doc.page}"
        
        # Right-align the page number for both languages
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
        
        # Apply BiDi processing to chart labels
        label_topup = ArabicTextHelper.process_arabic_text(f'{ArabicTextHelper.translate("TOP-UP", use_arabic)}\n({ArabicTextHelper.to_arabic_numerals(topup_count) if use_arabic else topup_count})')
        label_read = ArabicTextHelper.process_arabic_text(f'{ArabicTextHelper.translate("READ", use_arabic)}\n({ArabicTextHelper.to_arabic_numerals(read_count) if use_arabic else read_count})')
        labels = [label_topup, label_read]
        
        colors_pie = [ModernChartGenerator.COLORS['topup'], ModernChartGenerator.COLORS['read']]
        text_props = {'fontsize': 11, 'weight': 'bold', 'family': 'sans-serif'}
        
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90,
            textprops=text_props, explode=(0.05, 0.05), shadow=True
        )
        
        for autotext in autotexts:
            autotext.set_color('white'); autotext.set_fontsize(11); autotext.set_weight('bold')
        
        title_raw = ArabicTextHelper.translate("Transaction Types Distribution", use_arabic)
        title_proc = ArabicTextHelper.process_arabic_text(title_raw) if use_arabic else title_raw
        ax.set_title(title_proc, fontsize=13, weight='bold', pad=20, color=ModernChartGenerator.COLORS['dark'])
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        plt.close(fig)
        
        return img_buffer
    
    @staticmethod
    def generate_daily_amount_chart(transactions: List[Dict], 
                                    width: int = 7, height: int = 4,
                                    use_arabic: bool = False) -> Optional[BytesIO]:
        """Generate modern bar chart of daily amounts."""
        if not HAS_MATPLOTLIB: return None
        
        daily_data = {}
        for t in transactions:
            date = t['timestamp'].date()
            if date not in daily_data: daily_data[date] = 0
            if t['type'] == 'topup': daily_data[date] += t['amount']
        
        if not daily_data: return None
        
        dates = sorted(daily_data.keys())
        amounts = [daily_data[d] for d in dates]
        
        fig, ax = plt.subplots(figsize=(width, height), facecolor='white')
        bars = ax.bar(range(len(dates)), amounts, color=ModernChartGenerator.COLORS['topup'], 
                     edgecolor=ModernChartGenerator.COLORS['dark'], linewidth=1.5, alpha=0.85)
        
        for i, (bar, amount) in enumerate(zip(bars, amounts)):
            height_val = bar.get_height()
            label = ArabicTextHelper.to_arabic_numerals(int(amount)) if use_arabic else f"{int(amount)}"
            ax.text(bar.get_x() + bar.get_width()/2., height_val, label, ha='center', va='bottom', fontsize=9, weight='bold')
        
        xlabel_proc = ArabicTextHelper.process_arabic_text(ArabicTextHelper.translate("Date", use_arabic))
        ylabel_proc = ArabicTextHelper.process_arabic_text(ArabicTextHelper.translate("Amount (EGP)", use_arabic))
        title_proc = ArabicTextHelper.process_arabic_text(ArabicTextHelper.translate("Daily Top-up Amounts", use_arabic))
        
        font_config = {'fontname': 'sans-serif'}
        
        ax.set_xlabel(xlabel_proc, fontsize=11, weight='bold', color=ModernChartGenerator.COLORS['dark'], **font_config)
        ax.set_ylabel(ylabel_proc, fontsize=11, weight='bold', color=ModernChartGenerator.COLORS['dark'], **font_config)
        ax.set_title(title_proc, fontsize=13, weight='bold', pad=20, color=ModernChartGenerator.COLORS['dark'], **font_config)
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels([d.strftime('%m-%d') for d in dates], rotation=45, fontsize=9)
        ax.grid(axis='y', alpha=0.2, linestyle='--', color=ModernChartGenerator.COLORS['light'])
        ax.set_axisbelow(True)
        
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC'); ax.spines['bottom'].set_color('#CCCCCC')
        
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        plt.close(fig)
        
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
            raise ImportError(
                "Arabic support requires 'python-bidi' library. "
                "Install it with: pip install python-bidi"
            )
        
        self.db_service = db_service
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.company_name = company_name
        self.use_arabic = use_arabic
        self.chart_generator = ModernChartGenerator()
        self.arabic_font = ARABIC_REPORTLAB_FONT 
        
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
        read_transactions = [t for t in transactions if t['type'] == 'read']
        
        total_topup_amount = sum(t['amount'] for t in topup_transactions)
        total_read_amount = sum(t['amount'] for t in read_transactions)
        
        return {
            'total_transactions': len(transactions),
            'topup_count': len(topup_transactions),
            'read_count': len(read_transactions),
            'total_topup_amount': total_topup_amount,
            'total_read_amount': total_read_amount,
            'total_amount': total_topup_amount + total_read_amount,
            'avg_transaction': (total_topup_amount + total_read_amount) / len(transactions) if transactions else 0
        }
    
    def _create_modern_cover_page(self, report_title: str, period: str, 
                                   stats: Dict) -> List:
        """Create modern cover page elements."""
        elements = []
        styles = getSampleStyleSheet()
        
        # Determine font and alignment
        font_name = self.arabic_font if self.use_arabic else 'Helvetica'
        font_name_bold = f"{font_name}-Bold" if self.use_arabic else 'Helvetica-Bold'
        text_align = TA_RIGHT if self.use_arabic else TA_CENTER
        
        # Modern custom styles
        title_style = ParagraphStyle(
            'ModernTitle', parent=styles['Heading1'], fontSize=42, textColor=self.PRIMARY_COLOR, spaceAfter=15, 
            alignment=text_align, fontName=font_name_bold, leading=50
        )
        subtitle_style = ParagraphStyle(
            'ModernSubtitle', parent=styles['Normal'], fontSize=18, textColor=self.DARK_TEXT, spaceAfter=10, 
            alignment=text_align, fontName=font_name_bold
        )
        meta_style = ParagraphStyle(
            'Meta', parent=styles['Normal'], fontSize=10, textColor=self.MEDIUM_TEXT, spaceAfter=8, 
            alignment=text_align, fontName=font_name 
        )
        
        elements.append(Spacer(1, 1.2 * inch))
        
        # Company name
        company_name_proc = self._bidi_process(self.company_name)
        elements.append(Paragraph(company_name_proc, subtitle_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Report title
        report_title_proc = self._bidi_process(self._translate(report_title))
        elements.append(Paragraph(report_title_proc, title_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Removed: Generated date first
        # gen_date = ArabicTextHelper.format_date_arabic(datetime.now()) if self.use_arabic else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # gen_text = self._bidi_process(f"{self._translate('Generated on')} {gen_date}")
        # elements.append(Paragraph(f"<font color='#999999' size=8 fontName='{font_name}'>{gen_text}</font>", meta_style))
        
        # Removed: Period after
        # period_label = self._bidi_process(self._translate('Period'))
        # elements.append(Paragraph(f"<font color='{self.MEDIUM_TEXT.hexval()}' fontName='{font_name_bold}'>{period_label}:</font> <font fontName='{font_name}'>{self._bidi_process(period)}</font>", meta_style))
        
        elements.append(Spacer(1, 0.3 * inch))
        
        # Key metrics section
        key_metrics_proc = self._bidi_process(self._translate("Key Metrics"))
        elements.append(Paragraph(key_metrics_proc, subtitle_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Statistics table data preparation
        total_amount_str = (f"EGP {ArabicTextHelper.format_currency_arabic(stats['total_amount'])}"
                            if self.use_arabic else f"EGP {stats['total_amount']:.2f}")
        avg_transaction_str = (f"EGP {ArabicTextHelper.format_currency_arabic(stats['avg_transaction'])}"
                               if self.use_arabic else f"EGP {stats['avg_transaction']:.2f}")
                               
        total_amount_proc = self._bidi_process(total_amount_str)
        avg_transaction_proc = self._bidi_process(avg_transaction_str)
        
        stats_data = [
            [self._bidi_process(self._translate('Metric')), self._bidi_process(self._translate('Value'))],
            [self._bidi_process(self._translate('Total Transactions')), 
             self._bidi_process(ArabicTextHelper.to_arabic_numerals(stats['total_transactions']) if self.use_arabic else str(stats['total_transactions']))],
            [self._bidi_process(self._translate('Top-ups')), 
             self._bidi_process(f"{ArabicTextHelper.to_arabic_numerals(stats['topup_count']) if self.use_arabic else stats['topup_count']} (EGP {stats['total_topup_amount']:.2f})")],
            [self._bidi_process(self._translate('Reads')), 
             self._bidi_process(f"{ArabicTextHelper.to_arabic_numerals(stats['read_count']) if self.use_arabic else stats['read_count']} (EGP {stats['total_read_amount']:.2f})")],
            [self._bidi_process(self._translate('Total Amount')), total_amount_proc],
            [self._bidi_process(self._translate('Average Transaction')), avg_transaction_proc]
        ]
        
        # Reverse columns for RTL display of table data
        if self.use_arabic:
            stats_data = [row[::-1] for row in stats_data]
            col_align_left = 'RIGHT'; col_align_right = 'LEFT'
        else:
            col_align_left = 'LEFT'; col_align_right = 'RIGHT'
        
        stats_table = Table(stats_data, colWidths=[3 * inch, 2.5 * inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), font_name_bold), ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), self.LIGHT_BG), ('TEXTCOLOR', (0, 1), (-1, -1), self.DARK_TEXT),
            ('ALIGN', (0, 1), (0, -1), col_align_left), ('ALIGN', (1, 1), (1, -1), col_align_right),
            ('FONTNAME', (0, 1), (-1, -1), font_name), ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_GRAY]),
            ('GRID', (0, 0), (-1, -1), 1, HexColor("#DDDDDD")),
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 0.4 * inch))
        
        # Removed: Original gen_date paragraph at the end
        # elements.append(Paragraph(f"<font color='#999999' size=8 fontName='{font_name}'>{gen_text}</font>", meta_style))
        
        return elements
    
    def _create_modern_transactions_table(self, transactions: List[Dict], landscape_mode: bool = False) -> Table:
        """Create modern formatted transactions table."""
        
        font_name = self.arabic_font if self.use_arabic else 'Helvetica'
        font_name_bold = f"{font_name}-Bold" if self.use_arabic else 'Helvetica-Bold'
        styles = getSampleStyleSheet()
        wrap_mode = 'RTL' if self.use_arabic else 'CJK'
        header_par_style = ParagraphStyle('TblHeader', parent=styles['Normal'], fontName=font_name_bold, fontSize=9, alignment=TA_RIGHT if self.use_arabic else TA_CENTER, wordWrap=wrap_mode, leading=11)
        body_par_style = ParagraphStyle('TblBody', parent=styles['Normal'], fontName=font_name, fontSize=8, alignment=TA_RIGHT if self.use_arabic else TA_LEFT, wordWrap=wrap_mode, leading=10)
        
        # Table data
        ts_header_label = self._translate('Date') if self.use_arabic else self._translate('Timestamp')
        balance_header_label = self._translate('Balance After (EGP)')
        if self.use_arabic and not landscape_mode:
            # Prevent splitting Arabic words in portrait daily report header
            balance_header_label = balance_header_label.replace(' ', '\u00A0')
        header_row = [
            self._bidi_process(self._translate('ID')),
            self._bidi_process(self._translate('Card UID')),
            self._bidi_process(self._translate('Type')),
            self._bidi_process(self._translate('Amount (EGP)')),
            self._bidi_process(balance_header_label),
            self._bidi_process(self._translate('Employee')),
            self._bidi_process(ts_header_label),
        ]
        table_data_raw = [header_row]
        
        for i, t in enumerate(transactions):
            tx_type = self._translate('TOP-UP') if t['type'] == 'topup' else self._translate('READ')
            amount = ArabicTextHelper.format_currency_arabic(t['amount']) if self.use_arabic else f"{t['amount']:.2f}"
            balance = ArabicTextHelper.format_currency_arabic(t['balance_after']) if self.use_arabic else f"{t['balance_after']:.2f}"
            
            row = [
                self._bidi_process(str(t.get('id', ''))),
                self._bidi_process(t.get('card_uid', '')),
                self._bidi_process(tx_type),
                self._bidi_process(amount),
                self._bidi_process(balance),
                self._bidi_process(t.get('employee', 'N/A')),
                self._bidi_process(ArabicTextHelper.format_date_arabic_dmy(t['timestamp'], include_time=False) if self.use_arabic else t['timestamp'].strftime('%Y-%m-%d %H:%M')),
            ]
            table_data_raw.append(row)
        
        # Add total row
        total_amount = sum(t['amount'] for t in transactions if t['type'] == 'topup')
        total_formatted = ArabicTextHelper.format_currency_arabic(total_amount) if self.use_arabic else f"{total_amount:.2f}"
        total_row = [
            '', '', self._bidi_process(self._translate('TOTAL')), self._bidi_process(total_formatted), '', '', ''
        ]
        table_data_raw.append(total_row)
        
        # Reverse columns for RTL display of table data
        if self.use_arabic:
            table_data = [row[::-1] for row in table_data_raw]
            header_align = 'RIGHT'; content_align_left = 'RIGHT'; content_align_right = 'LEFT'
            total_text_col = 4; total_value_col = 3
        else:
            table_data = table_data_raw
            header_align = 'CENTER'; content_align_left = 'LEFT'; content_align_right = 'RIGHT'
            total_text_col = 2; total_value_col = 3
        
        # Convert to Paragraphs for proper wrapping in table cells (both Arabic and English)
        table_data_par = []
        for r_idx, row in enumerate(table_data):
            style = header_par_style if r_idx == 0 else body_par_style
            table_data_par.append([Paragraph(str(cell), style) for cell in row])
        table_data = table_data_par

        # Compute dynamic column widths based on page orientation and margins
        available_width = (A4[1] if landscape_mode else A4[0]) - 1.0 * inch  # match 0.5" margins on both sides
        if landscape_mode:
            proportions = [0.06, 0.18, 0.08, 0.12, 0.12, 0.18, 0.26]
        else:
            # Daily (portrait): give extra space to Balance After to avoid header wrapping in Arabic
            proportions = [0.06, 0.16, 0.08, 0.12, 0.16, 0.16, 0.26]
        col_widths = [available_width * p for p in (proportions[::-1] if self.use_arabic else proportions)]

        table = Table(table_data, colWidths=col_widths, repeatRows=1, splitByRow=1)
        
        # Modern table styling
        num_start = 2 if self.use_arabic else 3
        num_end = 3 if self.use_arabic else 4
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), header_align), ('FONTNAME', (0, 0), (-1, 0), font_name_bold), ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 1), (-1, -2), content_align_left), ('ALIGN', (num_start, 1), (num_end, -2), content_align_right),
            ('FONTSIZE', (0, 1), (-1, -2), 8), ('FONTNAME', (0, 1), (-1, -2), font_name),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, self.LIGHT_BG]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), self.SUCCESS_COLOR), ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), font_name_bold),
            ('ALIGN', (total_text_col, -1), (total_text_col, -1), 'RIGHT'), ('ALIGN', (total_value_col, -1), (total_value_col, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#E0E0E0")), ('LINEABOVE', (0, -1), (-1, -1), 2, self.SUCCESS_COLOR),
        ]))
        
        return table
    
    def _get_report_filename(self, report_type: str, identifier: str = '') -> Path:
        """Generate report filename with timestamp."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_report_{identifier}_{timestamp}.pdf"
        return self.output_dir / filename
    
    def _generate_pdf(self, filename: str, elements: List, 
                     landscape_mode: bool = False, save_to: Optional[str] = None) -> str:
        """Generate modern PDF document."""
        if not HAS_REPORTLAB:
            raise ImportError("reportlab is required for PDF generation. Install it with: pip install reportlab")
        
        filepath = Path(save_to) if save_to else (self.output_dir / filename)
        
        try:
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            pagesize = landscape(A4) if landscape_mode else A4
            doc = SimpleDocTemplate(
                str(filepath), pagesize=pagesize, rightMargin=0.5 * inch, leftMargin=0.5 * inch, 
                topMargin=0.5 * inch, bottomMargin=0.5 * inch
            )
            
            header_footer = ModernPDFHeaderFooter(
                self.company_name, use_arabic=self.use_arabic, pagesize=pagesize, id='standard_template'
            )
            doc.addPageTemplates([header_footer])
            
            doc.build(elements)
            logger.info(f"PDF report generated: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise

    def generate_report(self, report_type: str, transactions: List[Dict], period: str,
                        identifier: str = '', landscape_mode: bool = False,
                        output_path: Optional[str] = None) -> str:
        """A consolidated PDF generator for standard report types (daily/weekly/monthly/custom)."""
        stats = self._calculate_statistics(transactions)
        elements = self._create_modern_cover_page(report_type, period, stats)
        elements.append(PageBreak())

        # Transactions section
        styles = getSampleStyleSheet()
        tx_title_style = ParagraphStyle(
            'TxTitle', parent=styles['Heading2'], fontSize=16, textColor=self.PRIMARY_COLOR,
            spaceAfter=12, fontName=f"{self.arabic_font}-Bold" if self.use_arabic else 'Helvetica-Bold',
            alignment=TA_RIGHT if self.use_arabic else TA_LEFT
        )
        elements.append(Paragraph(self._bidi_process(self._translate("Transactions")), tx_title_style))
        elements.append(Spacer(1, 0.15 * inch))
        elements.append(self._create_modern_transactions_table(transactions, landscape_mode=landscape_mode))

        # Charts section
        if HAS_MATPLOTLIB and transactions:
            elements.append(PageBreak())
            analytics_style = ParagraphStyle(
                'AnalyticsTitle', parent=styles['Heading2'], fontSize=16, textColor=self.PRIMARY_COLOR,
                spaceAfter=12, fontName=f"{self.arabic_font}-Bold" if self.use_arabic else 'Helvetica-Bold',
                alignment=TA_RIGHT if self.use_arabic else TA_LEFT
            )
            elements.append(Paragraph(self._bidi_process(self._translate("Analytics")), analytics_style))
            elements.append(Spacer(1, 0.15 * inch))

            # Pie Chart
            pie_chart = self.chart_generator.generate_transaction_pie_chart(transactions, use_arabic=self.use_arabic)
            if pie_chart:
                elements.append(Image(pie_chart, width=4*inch, height=4*inch))
                elements.append(Spacer(1, 0.2 * inch))

            # Bar Chart
            bar_chart = self.chart_generator.generate_daily_amount_chart(transactions, width=7, height=4, use_arabic=self.use_arabic)
            if bar_chart:
                elements.append(Image(bar_chart, width=7*inch, height=4*inch))

        pdf_path = self._get_report_filename(report_type.lower().replace(' ', '_'), identifier)
        return self._generate_pdf(pdf_path.name, elements, landscape_mode=landscape_mode, save_to=output_path)

    def generate_daily_report(self, date: Optional[datetime] = None, output_path: Optional[str] = None) -> str:
        """Generate modern daily PDF report."""
        date = date or datetime.now().date()
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()

        start_date = datetime.combine(date, datetime.min.time())
        end_date = datetime.combine(date, datetime.max.time())

        transactions = (self.db_service.get_transactions(start_date=start_date, end_date=end_date)
                        if hasattr(self.db_service, 'get_transactions') else [])
        period = (
            ArabicTextHelper.format_date_arabic_dmy(start_date, include_time=False)
            if self.use_arabic else date.strftime('%Y-%m-%d')
        )
        identifier = date.strftime('%Y%m%d')
        return self.generate_report('Daily Report', transactions, period, identifier, output_path=output_path)

    def generate_weekly_report(self, week_start: Optional[datetime] = None, output_path: Optional[str] = None) -> str:
        """Generate modern weekly PDF report."""
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        elif isinstance(week_start, str):
            week_start = datetime.strptime(week_start, '%Y-%m-%d').date()

        week_end = week_start + timedelta(days=6)
        start_date = datetime.combine(week_start, datetime.min.time())
        end_date = datetime.combine(week_end, datetime.max.time())

        transactions = (self.db_service.get_transactions(start_date=start_date, end_date=end_date)
                        if hasattr(self.db_service, 'get_transactions') else [])
        if self.use_arabic:
            start_dmy = ArabicTextHelper.format_date_arabic_dmy(start_date, include_time=False)
            end_dmy = ArabicTextHelper.format_date_arabic_dmy(end_date, include_time=False)
            period = f"{start_dmy} إلى {end_dmy}"
        else:
            period = f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
        identifier = week_start.strftime('%Y%m%d')
        return self.generate_report('Weekly Report', transactions, period, identifier, landscape_mode=True, output_path=output_path)

    def generate_monthly_report(self, month: Optional[int] = None, year: Optional[int] = None, output_path: Optional[str] = None) -> str:
        """Generate modern monthly PDF report."""
        now = datetime.now()
        month = month or now.month
        year = year or now.year

        start_date = datetime(year, month, 1)
        # Compute last day of month
        end_date = datetime(year, month % 12 + 1, 1) - timedelta(seconds=1) if month < 12 else datetime(year + 1, 1, 1) - timedelta(seconds=1)

        transactions = (self.db_service.get_transactions(start_date=start_date, end_date=end_date)
                        if hasattr(self.db_service, 'get_transactions') else [])
        period = (
            f"{ArabicTextHelper.ARABIC_MONTHS[month-1]} {ArabicTextHelper.to_arabic_numerals(year)}"
            if self.use_arabic else start_date.strftime('%B %Y')
        )
        identifier = f"{year}{month:02d}"
        return self.generate_report('Monthly Report', transactions, period, identifier, landscape_mode=True, output_path=output_path)

    def generate_yearly_report(self, year: Optional[int] = None, output_path: Optional[str] = None) -> str:
        """Generate modern yearly PDF report."""
        now = datetime.now()
        year = year or now.year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        transactions = (self.db_service.get_transactions(start_date=start_date, end_date=end_date)
                        if hasattr(self.db_service, 'get_transactions') else [])
        period = ArabicTextHelper.to_arabic_numerals(year) if self.use_arabic else f"{year}"
        identifier = f"{year}"
        return self.generate_report('Yearly Report', transactions, period, identifier, landscape_mode=True, output_path=output_path)

    def generate_custom_report(self, start_date: datetime, end_date: datetime, card_uid: Optional[str] = None, output_path: Optional[str] = None) -> str:
        """Generate modern custom date range report."""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        transactions = (self.db_service.get_transactions(start_date=start_date, end_date=end_date, card_uid=card_uid)
                        if hasattr(self.db_service, 'get_transactions') else [])

        if self.use_arabic:
            start_dmy = ArabicTextHelper.format_date_arabic_dmy(start_date, include_time=False)
            end_dmy = ArabicTextHelper.format_date_arabic_dmy(end_date, include_time=False)
            period_str = f"{start_dmy} إلى {end_dmy}"
        else:
            period_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        if card_uid:
            period_str += f" ({self._translate('Card UID')}: {card_uid[:16]}...)"

        identifier = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        if card_uid:
            identifier += f"_{card_uid[:8]}"

        return self.generate_report('Custom Report', transactions, period_str, identifier, landscape_mode=True, output_path=output_path)

    def generate_beautiful_arabic_report(self, cards: List[Dict], output_path: Optional[str] = None) -> str:
        """
        Generate a visually appealing PDF report in Arabic with beautiful styling.
        (Implementation is provided to show full RTL and font application).
        """
        if not HAS_REPORTLAB:
            raise ImportError("reportlab is required for PDF generation")
        
        if not HAS_BIDI:
            raise ImportError(
                "Arabic report generation requires 'python-bidi' library. "
                "Install it with: pip install python-bidi"
            )
        
        original_setting = self.use_arabic
