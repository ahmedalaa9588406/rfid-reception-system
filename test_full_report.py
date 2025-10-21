"""
Test full Arabic PDF report generation using the same logic as reports.py
اختبار كامل لتوليد تقرير PDF بالعربية
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# Register Arabic font
FONT_PATH = Path(__file__).parent / "rfid_reception" / "assets" / "fonts" / "NotoSansArabic-VariableFont_wdth,wght.ttf"
try:
    pdfmetrics.registerFont(TTFont("NotoArabic", str(FONT_PATH)))
    print("✓ Arabic font registered successfully")
except Exception as e:
    print(f"✗ Failed to register font: {e}")
    exit(1)

def process_arabic_text(text):
    """Process Arabic text with reshaping and BiDi"""
    try:
        # Step 1: Reshape to connect letters
        reshaped = reshape(text)
        # Step 2: Apply BiDi for RTL
        return get_display(reshaped)
    except Exception as e:
        print(f"Error processing: {text} - {e}")
        return text

# Create PDF
output_path = "test_full_arabic_report.pdf"
doc = SimpleDocTemplate(output_path, pagesize=A4, 
                        rightMargin=0.5*inch, leftMargin=0.5*inch,
                        topMargin=inch, bottomMargin=inch)

elements = []
styles = getSampleStyleSheet()

# Arabic style
arabic_style = ParagraphStyle(
    'Arabic',
    parent=styles['Normal'],
    fontName='NotoArabic',
    fontSize=16,
    alignment=TA_RIGHT,
    leading=24
)

title_style = ParagraphStyle(
    'ArabicTitle',
    parent=styles['Heading1'],
    fontName='NotoArabic',
    fontSize=28,
    alignment=TA_CENTER,
    textColor=HexColor("#2E86AB"),
    spaceAfter=20
)

# Test texts
test_texts = [
    "تقرير يومي",
    "المعاملات اليومية", 
    "نظام إدارة البطاقات",
    "إجمالي المعاملات",
    "الشحنات والقراءات"
]

print("\n" + "="*60)
print("Testing Arabic text processing:")
print("="*60)

for text in test_texts:
    processed = process_arabic_text(text)
    print(f"Original: {text}")
    print(f"Processed: {processed}")
    print("-" * 40)
    
    # Add to PDF
    elements.append(Paragraph(processed, arabic_style))
    elements.append(Spacer(1, 0.2*inch))

# Add title
elements.insert(0, Spacer(1, 0.3*inch))
elements.insert(1, Paragraph(process_arabic_text("تقرير يومي - اختبار"), title_style))
elements.insert(2, Spacer(1, 0.3*inch))

# Add table with Arabic headers
table_data = [
    [process_arabic_text("القيمة"), process_arabic_text("المقياس")],
    [process_arabic_text("٥٠"), process_arabic_text("إجمالي المعاملات")],
    [process_arabic_text("٣٥"), process_arabic_text("الشحنات")],
    [process_arabic_text("١٥"), process_arabic_text("القراءات")],
]

table = Table(table_data, colWidths=[2*inch, 3*inch])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HexColor("#2E86AB")),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ('FONTNAME', (0, 0), (-1, -1), 'NotoArabic'),
    ('FONTSIZE', (0, 0), (-1, 0), 14),
    ('FONTSIZE', (0, 1), (-1, -1), 12),
    ('BACKGROUND', (0, 1), (-1, -1), HexColor("#F5F5F5")),
    ('GRID', (0, 0), (-1, -1), 1, HexColor("#DDDDDD")),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor("#F5F5F5")]),
]))

elements.append(table)

# Build PDF
try:
    doc.build(elements)
    print("\n" + "="*60)
    print(f"✓ PDF created successfully: {output_path}")
    print("="*60)
    print("\nافتح الملف وتحقق من أن:")
    print("1. الحروف العربية متصلة بشكل صحيح ✓")
    print("2. النص يظهر من اليمين لليسار ✓")
    print("3. الجدول يعرض البيانات بشكل صحيح ✓")
except Exception as e:
    print(f"✗ Error creating PDF: {e}")
    import traceback
    traceback.print_exc()
