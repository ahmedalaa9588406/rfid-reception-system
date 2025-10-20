"""
Test script to verify Arabic text rendering in PDF
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# Register Arabic font
FONT_PATH = Path(__file__).parent / "rfid_reception" / "assets" / "fonts" / "NotoSansArabic-VariableFont_wdth,wght.ttf"
pdfmetrics.registerFont(TTFont("NotoArabic", str(FONT_PATH)))

# Test text
arabic_text = "تقرير يومي"
print(f"Original text: {arabic_text}")

# Without reshaping (WRONG)
wrong_display = get_display(arabic_text)
print(f"Without reshaping: {wrong_display}")

# With reshaping (CORRECT)
reshaped_text = reshape(arabic_text)
correct_display = get_display(reshaped_text)
print(f"With reshaping: {correct_display}")

# Create PDF
pdf_path = "test_arabic_output.pdf"
c = canvas.Canvas(pdf_path, pagesize=A4)
width, height = A4

c.setFont("NotoArabic", 24)

# Test both versions
c.drawRightString(width - 50, height - 100, wrong_display)
c.drawString(50, height - 100, "(Without reshaping - WRONG)")

c.drawRightString(width - 50, height - 150, correct_display)
c.drawString(50, height - 150, "(With reshaping - CORRECT)")

c.save()
print(f"\nPDF created: {pdf_path}")
print("Check the PDF to see the difference!")
