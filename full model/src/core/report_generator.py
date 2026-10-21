from fpdf import FPDF
import datetime
import json
import os
import sys

# Add project root for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.core.indian_railways import IndianWagonParser

# ============================================
# COLOR SCHEME (Industry Standard)
# ============================================
COLORS = {
    'primary': (30, 58, 95),        # Navy Blue #1e3a5f
    'secondary': (44, 82, 130),     # Dark Blue #2c5282
    'accent': (201, 162, 39),       # Gold #c9a227
    'success': (56, 161, 105),      # Green #38a169
    'warning': (214, 158, 46),      # Amber #d69e2e
    'danger': (229, 62, 62),        # Red #e53e3e
    'bg_light': (247, 250, 252),    # Light Gray #f7fafc
    'bg_dark': (26, 32, 44),        # Dark Gray #1a202c
    'white': (255, 255, 255),
    'text': (45, 55, 72),           # Dark text
    'text_light': (113, 128, 150),  # Light text
    'border': (226, 232, 240),      # Border gray
}


class IndustryPDFReport(FPDF):
    """Industry-level PDF Report Generator for Railway Wagon Inspection"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        
    def header(self):
        # Skip header on cover page (page 1)
        if self.page_no() == 1:
            return
            
        # Header bar
        self.set_fill_color(*COLORS['primary'])
        self.rect(0, 0, 210, 15, 'F')
        
        # Logo (if exists)
        logo_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', 'frontend', 'public',
            'PhotoshopExtension_Image (1).png'
        )
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, x=8, y=2, h=10)
            except:
                pass
        
        # Title
        self.set_xy(0, 3)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['white'])
        self.cell(0, 8, 'CARGOVISION AI INSPECTION REPORT', 0, 0, 'C')
        
        self.ln(18)
        
    def footer(self):
        # Skip footer on cover page
        if self.page_no() == 1:
            return
            
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(*COLORS['text_light'])
        
        # Left: Confidential
        self.cell(60, 10, 'CONFIDENTIAL - Internal Use Only', 0, 0, 'L')
        
        # Center: Page number
        self.cell(70, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')
        
        # Right: Generated time
        self.cell(60, 10, f'Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'R')


def draw_metric_box(pdf, x, y, width, height, title, value, color, subtitle=""):
    """Draw a styled metric box with color accent"""
    # Background
    pdf.set_fill_color(*COLORS['white'])
    pdf.set_draw_color(*COLORS['border'])
    pdf.rect(x, y, width, height, 'DF')
    
    # Color accent bar on top
    pdf.set_fill_color(*color)
    pdf.rect(x, y, width, 4, 'F')
    
    # Title
    pdf.set_xy(x, y + 8)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(*COLORS['text_light'])
    pdf.cell(width, 5, title, 0, 0, 'C')
    
    # Value
    pdf.set_xy(x, y + 16)
    pdf.set_font('Arial', 'B', 20)
    pdf.set_text_color(*COLORS['text'])
    pdf.cell(width, 10, str(value), 0, 0, 'C')
    
    # Subtitle
    if subtitle:
        pdf.set_xy(x, y + 28)
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(*COLORS['text_light'])
        pdf.cell(width, 5, subtitle, 0, 0, 'C')


def draw_status_indicator(pdf, x, y, status, text):
    """Draw a colored status badge"""
    if status == 'success':
        color = COLORS['success']
    elif status == 'warning':
        color = COLORS['warning']
    else:
        color = COLORS['danger']
    
    pdf.set_fill_color(*color)
    pdf.set_text_color(*COLORS['white'])
    pdf.set_font('Arial', 'B', 9)
    
    # Badge background
    text_width = pdf.get_string_width(text) + 8
    pdf.rect(x, y, text_width, 6, 'F')
    pdf.set_xy(x, y)
    pdf.cell(text_width, 6, text, 0, 0, 'C')
    
    # Reset colors
    pdf.set_text_color(*COLORS['text'])


def generate_report(inspection, wagons):
    """Generate industry-level PDF report"""
    pdf = IndustryPDFReport()
    pdf.alias_nb_pages()
    
    # ========================================
    # PAGE 1: COVER PAGE
    # ========================================
    pdf.add_page()
    
    # Blue header band
    pdf.set_fill_color(*COLORS['primary'])
    pdf.rect(0, 0, 210, 80, 'F')
    
    # Logo
    logo_path = os.path.join(
        os.path.dirname(__file__),
        '..', '..', '..', 'frontend', 'public',
        'PhotoshopExtension_Image (1).png'
    )
    if os.path.exists(logo_path):
        try:
            pdf.image(logo_path, x=85, y=15, h=25)
        except:
            pass
    
    # Main Title
    pdf.set_xy(0, 45)
    pdf.set_font('Arial', 'B', 28)
    pdf.set_text_color(*COLORS['white'])
    pdf.cell(0, 12, 'INSPECTION REPORT', 0, 1, 'C')
    
    pdf.set_font('Arial', '', 14)
    pdf.set_text_color(*COLORS['accent'])
    pdf.cell(0, 8, 'Automated Railway Wagon Analysis', 0, 1, 'C')
    
    # Calculate metrics
    total_wagons = len(wagons)
    ocr_success = len([w for w in wagons if w.get('ocr_text') and w['ocr_text'] != "OCR Failed"])
    ocr_rate = round((ocr_success / total_wagons * 100)) if total_wagons > 0 else 0
    defects = len([w for w in wagons if w.get('defects') and w['defects'] not in ["None", "[]", ""]])
    anomalies = len([w for w in wagons if w.get('anomaly_type') and w['anomaly_type'] != ""])
    night_count = len([w for w in wagons if w.get('is_night')])
    
    # Metric boxes
    box_y = 95
    box_width = 42
    box_height = 38
    start_x = 15
    gap = 5
    
    draw_metric_box(pdf, start_x, box_y, box_width, box_height, 
                    "WAGONS INSPECTED", total_wagons, COLORS['primary'])
    
    draw_metric_box(pdf, start_x + box_width + gap, box_y, box_width, box_height,
                    "OCR SUCCESS", f"{ocr_rate}%", COLORS['success'] if ocr_rate >= 80 else COLORS['warning'])
    
    draw_metric_box(pdf, start_x + 2*(box_width + gap), box_y, box_width, box_height,
                    "DEFECTS FOUND", defects, COLORS['danger'] if defects > 0 else COLORS['success'])
    
    draw_metric_box(pdf, start_x + 3*(box_width + gap), box_y, box_width, box_height,
                    "ANOMALIES", anomalies, COLORS['warning'] if anomalies > 0 else COLORS['success'])
    
    # Inspection Details Section
    pdf.set_xy(15, 145)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(*COLORS['primary'])
    pdf.cell(0, 8, 'INSPECTION DETAILS', 0, 1)
    
    pdf.set_draw_color(*COLORS['border'])
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    # Details table
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(*COLORS['text'])
    
    details = [
        ('Inspection ID', f"#{inspection['id']}"),
        ('Video Source', inspection.get('video_name', 'N/A')),
        ('Inspection Date', inspection.get('timestamp', 'N/A')),
        ('Status', inspection.get('status', 'COMPLETED')),
        ('Train Speed', f"{inspection.get('train_speed', 0):.1f} km/h" if inspection.get('train_speed') else "N/A"),
        ('Night Inspections', f"{night_count} wagons ({round(night_count/total_wagons*100) if total_wagons else 0}%)"),
    ]
    
    col1_x = 20
    col2_x = 110
    
    for i, (label, value) in enumerate(details):
        if i % 2 == 0:
            pdf.set_xy(col1_x, pdf.get_y())
        else:
            pdf.set_xy(col2_x, pdf.get_y() - 7)
            
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(*COLORS['text_light'])
        pdf.cell(35, 7, label + ":", 0, 0)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(*COLORS['text'])
        pdf.cell(50, 7, str(value)[:30], 0, 1)
    
    # System Health Section
    pdf.set_xy(15, 210)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(*COLORS['primary'])
    pdf.cell(0, 8, 'SYSTEM HEALTH', 0, 1)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    fps = inspection.get('fps', 0) or 0
    resolution = inspection.get('resolution', 'N/A') or 'N/A'
    brightness = inspection.get('avg_brightness', 0) or 0
    
    # System metrics in boxes
    sys_box_y = pdf.get_y()
    sys_box_width = 55
    sys_box_height = 25
    
    # FPS Box
    pdf.set_fill_color(*COLORS['bg_light'])
    pdf.rect(20, sys_box_y, sys_box_width, sys_box_height, 'DF')
    pdf.set_xy(20, sys_box_y + 3)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(*COLORS['text_light'])
    pdf.cell(sys_box_width, 5, 'Camera FPS', 0, 0, 'C')
    pdf.set_xy(20, sys_box_y + 10)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*COLORS['text'])
    pdf.cell(sys_box_width, 8, f"{fps:.1f}", 0, 0, 'C')
    
    # Resolution Box
    pdf.set_fill_color(*COLORS['bg_light'])
    pdf.rect(80, sys_box_y, sys_box_width, sys_box_height, 'DF')
    pdf.set_xy(80, sys_box_y + 3)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(*COLORS['text_light'])
    pdf.cell(sys_box_width, 5, 'Resolution', 0, 0, 'C')
    pdf.set_xy(80, sys_box_y + 10)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*COLORS['text'])
    pdf.cell(sys_box_width, 8, str(resolution)[:15], 0, 0, 'C')
    
    # Brightness Box
    pdf.set_fill_color(*COLORS['bg_light'])
    pdf.rect(140, sys_box_y, sys_box_width, sys_box_height, 'DF')
    pdf.set_xy(140, sys_box_y + 3)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(*COLORS['text_light'])
    pdf.cell(sys_box_width, 5, 'Avg Brightness', 0, 0, 'C')
    pdf.set_xy(140, sys_box_y + 10)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*COLORS['text'])
    pdf.cell(sys_box_width, 8, f"{brightness:.0f}/255", 0, 0, 'C')
    
    
    # ========================================
    # PAGE 2: WAGON DETAILS TABLE
    # ========================================
    pdf.add_page()
    
    # Section title
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*COLORS['primary'])
    pdf.cell(0, 10, 'WAGON INSPECTION DETAILS', 0, 1)
    pdf.set_draw_color(*COLORS['primary'])
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Table Header
    pdf.set_fill_color(*COLORS['primary'])
    pdf.set_text_color(*COLORS['white'])
    pdf.set_font('Arial', 'B', 9)
    
    col_widths = [10, 28, 45, 15, 32, 25, 15]  # Total: 170mm (fits in 190mm page width)
    headers = ['#', 'OCR', 'Decoded Info', 'Conf', 'Railway/Type', 'Time', 'Status']
    
    x_start = 10
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
    pdf.ln()
    
    # Table Rows
    pdf.set_font('Arial', '', 8)
    
    # Check if there are wagons to display
    if not wagons or len(wagons) == 0:
        pdf.set_font('Arial', 'I', 11)
        pdf.set_text_color(*COLORS['text_light'])
        pdf.ln(20)
        pdf.cell(0, 10, 'No wagon data available for this inspection.', 0, 1, 'C')
        pdf.ln(10)
    else:
        for idx, wagon in enumerate(wagons):
            # Alternating row colors
            if idx % 2 == 0:
                pdf.set_fill_color(*COLORS['white'])
            else:
                pdf.set_fill_color(*COLORS['bg_light'])
            
            ocr_text = wagon.get('ocr_text') or "N/A"
            conf = wagon.get('ocr_confidence', 0) or 0
            conf_pct = f"{conf*100:.0f}%"
            ts = wagon.get('timestamp', '').split(' ')[1] if ' ' in wagon.get('timestamp', '') else wagon.get('timestamp', '')[:8]
            
            # Decode OCR
            decoded_text = "OCR Failed"
            railway_type = "N/A"
            if ocr_text and ocr_text not in ["OCR Failed", "N/A"]:
                parsed = IndianWagonParser.parse(ocr_text)
                if parsed:
                    decoded_text = parsed['formatted']
                    railway_type = f"{parsed['railway']} / {parsed['type']}"
                else:
                    decoded_text = "Invalid Format"
                    railway_type = "N/A"
            
            # Status based on confidence and defects
            has_defect = wagon.get('defects') and wagon['defects'] not in ["None", "[]", ""]
            has_anomaly = wagon.get('anomaly_type') and wagon['anomaly_type'] != ""
            
            if has_defect or has_anomaly:
                status = "ALERT"
                status_color = COLORS['danger']
            elif conf >= 0.85:
                status = "PASS"
                status_color = COLORS['success']
            elif conf >= 0.7:
                status = "WARN"
                status_color = COLORS['warning']
            else:
                status = "FAIL"
                status_color = COLORS['danger']
            
            # Row background based on status
            if has_defect or has_anomaly:
                pdf.set_fill_color(255, 235, 235)  # Light red
            
            pdf.set_text_color(*COLORS['text'])
            
            # Draw cells with appropriate text truncation for column widths
            pdf.cell(col_widths[0], 7, str(wagon.get('wagon_index', idx+1)), 1, 0, 'C', True)
            pdf.cell(col_widths[1], 7, str(ocr_text)[:12], 1, 0, 'L', True)  # Reduced from 15
            pdf.cell(col_widths[2], 7, decoded_text[:20], 1, 0, 'L', True)  # Reduced from 25
            
            # Confidence with color
            pdf.set_text_color(*status_color)
            pdf.set_font('Arial', 'B', 8)
            pdf.cell(col_widths[3], 7, conf_pct, 1, 0, 'C', True)
            
            pdf.set_text_color(*COLORS['text'])
            pdf.set_font('Arial', '', 8)
            pdf.cell(col_widths[4], 7, railway_type[:15], 1, 0, 'L', True)  # Reduced from 18
            pdf.cell(col_widths[5], 7, ts, 1, 0, 'C', True)
            
            # Status badge
            pdf.set_fill_color(*status_color)
            pdf.set_text_color(*COLORS['white'])
            pdf.set_font('Arial', 'B', 7)
            pdf.cell(col_widths[6], 7, status, 1, 1, 'C', True)
            
            # Reset fill color for next row
            pdf.set_text_color(*COLORS['text'])
            
            # Check for page break
            if pdf.get_y() > 265:
                pdf.add_page()
                # Redraw header
                pdf.set_fill_color(*COLORS['primary'])
                pdf.set_text_color(*COLORS['white'])
                pdf.set_font('Arial', 'B', 9)
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
                pdf.ln()
                pdf.set_font('Arial', '', 8)
    # End of wagon table (close the else block if wagons exist)
    
    # ========================================
    # VISUAL INSPECTION PAGES
    # ========================================
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*COLORS['primary'])
    pdf.cell(0, 10, 'VISUAL INSPECTION GALLERY', 0, 1)
    pdf.set_draw_color(*COLORS['primary'])
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    wagons_per_page = 2
    wagon_count = 0
    
    for wagon in wagons:
        # Check if we need a new page (2 wagons per page)
        if wagon_count > 0 and wagon_count % wagons_per_page == 0:
            pdf.add_page()
            pdf.ln(5)
        
        wagon_count += 1
        
        card_y = pdf.get_y()
        card_height = 120
        
        # Card background
        pdf.set_fill_color(*COLORS['bg_light'])
        pdf.set_draw_color(*COLORS['border'])
        pdf.rect(10, card_y, 190, card_height, 'DF')
        
        # Header bar with wagon number
        has_issue = (wagon.get('anomaly_type') and wagon['anomaly_type'] != "") or \
                    (wagon.get('defects') and wagon['defects'] not in ["None", "[]", ""])
        
        if has_issue:
            pdf.set_fill_color(*COLORS['danger'])
        else:
            pdf.set_fill_color(*COLORS['primary'])
        
        pdf.rect(10, card_y, 190, 12, 'F')
        
        # Wagon title
        pdf.set_xy(15, card_y + 2)
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(*COLORS['white'])
        wagon_title = f"Wagon #{wagon.get('wagon_index', '?')} - OCR: {wagon.get('ocr_text', 'N/A')}"
        pdf.cell(120, 8, wagon_title[:50], 0, 0, 'L')
        
        # Status badge
        if has_issue:
            badge_text = "REQUIRES ATTENTION"
        else:
            badge_text = "PASSED"
        pdf.set_xy(150, card_y + 3)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(45, 6, badge_text, 0, 0, 'R')
        
        # Images row
        img_y = card_y + 18
        img_width = 42
        img_height = 50
        img_gap = 5
        img_start_x = 15
        
        images = [
            ("Original Frame", wagon.get('original_image_path')),
            ("Enhanced", wagon.get('deblurred_image_path')),
            ("Number Crop", wagon.get('cropped_number_path')),
            ("Anomaly Check", wagon.get('anomaly_image_path')),
        ]
        
        current_x = img_start_x
        
        for label, path in images:
            # Label
            pdf.set_xy(current_x, img_y)
            pdf.set_font('Arial', '', 7)
            pdf.set_text_color(*COLORS['text_light'])
            pdf.cell(img_width, 4, label, 0, 0, 'C')
            
            # Image or placeholder
            if path and os.path.exists(path):
                is_anomaly = "Anomaly" in label and wagon.get('anomaly_type')
                
                if is_anomaly:
                    pdf.set_draw_color(*COLORS['danger'])
                    pdf.set_line_width(0.8)
                    pdf.rect(current_x - 1, img_y + 5, img_width + 2, img_height + 2)
                    pdf.set_line_width(0.2)
                
                try:
                    pdf.image(path, x=current_x, y=img_y + 6, w=img_width, h=img_height)
                except:
                    pdf.set_draw_color(*COLORS['border'])
                    pdf.rect(current_x, img_y + 6, img_width, img_height)
                    pdf.set_xy(current_x, img_y + 30)
                    pdf.set_font('Arial', '', 8)
                    pdf.cell(img_width, 5, "[Error]", 0, 0, 'C')
            else:
                pdf.set_draw_color(*COLORS['border'])
                pdf.rect(current_x, img_y + 6, img_width, img_height)
                pdf.set_xy(current_x, img_y + 30)
                pdf.set_font('Arial', '', 8)
                pdf.set_text_color(*COLORS['text_light'])
                placeholder = "No Anomaly" if "Anomaly" in label else "No Image"
                pdf.cell(img_width, 5, placeholder, 0, 0, 'C')
            
            current_x += img_width + img_gap
        
        # Details row
        details_y = img_y + img_height + 12
        pdf.set_xy(15, details_y)
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(*COLORS['text'])
        
        
        conf = wagon.get('ocr_confidence', 0) or 0
        defect_text = wagon.get('defects', 'None')
        anomaly = wagon.get('anomaly_type', '')
        is_night = "Yes" if wagon.get('is_night') else "No"
        
        pdf.cell(45, 5, f"Confidence: {conf*100:.1f}%", 0, 0, 'L')
        pdf.cell(50, 5, f"Defects: {str(defect_text)[:20]}", 0, 0, 'L')
        pdf.cell(45, 5, f"Anomaly: {anomaly or 'None'}", 0, 0, 'L')
        pdf.cell(40, 5, f"Night: {is_night}", 0, 0, 'L')
        
        # Move to next wagon position
        pdf.set_y(card_y + card_height + 8)
    
    # ========================================
    # FINAL PAGE: SUMMARY & RECOMMENDATIONS
    # ========================================
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*COLORS['primary'])
    pdf.cell(0, 10, 'SUMMARY & RECOMMENDATIONS', 0, 1)
    pdf.set_draw_color(*COLORS['primary'])
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    # Summary statistics
    avg_conf = sum(w.get('ocr_confidence', 0) or 0 for w in wagons) / len(wagons) if wagons else 0
    
    summary_data = [
        ("Total Wagons Analyzed", total_wagons),
        ("Successful OCR Readings", f"{ocr_success} ({ocr_rate}%)"),
        ("Wagons with Defects", defects),
        ("Anomalies Detected", anomalies),
        ("Night-time Inspections", night_count),
        ("Average OCR Confidence", f"{avg_conf*100:.1f}%"),
    ]
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(*COLORS['text'])
    
    for label, value in summary_data:
        pdf.set_fill_color(*COLORS['bg_light'])
        pdf.cell(90, 8, f"  {label}:", 1, 0, 'L', True)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(90, 8, f"  {value}", 1, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
    
    pdf.ln(10)
    
    # Recommendations section
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(*COLORS['primary'])
    pdf.cell(0, 8, 'Recommendations', 0, 1)
    pdf.ln(3)
    
    recommendations = []
    
    if ocr_rate < 80:
        recommendations.append("- OCR success rate below 80%. Consider improving image quality or lighting conditions.")
    else:
        recommendations.append("- OCR performance is satisfactory. Continue with current camera settings.")
    
    if defects > 0:
        recommendations.append(f"- {defects} wagon(s) flagged with defects require manual inspection.")
    
    if anomalies > 0:
        recommendations.append(f"- {anomalies} visual anomaly(ies) detected. Review affected wagons.")
    
    if night_count > total_wagons * 0.5:
        recommendations.append("- High proportion of night inspections. Ensure adequate lighting.")
    
    if avg_conf < 0.7:
        recommendations.append("- Average confidence is low. Consider deblurring or enhancement improvements.")
    
    if not recommendations:
        recommendations.append("- All inspections completed successfully. No immediate actions required.")
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(*COLORS['text'])
    
    for rec in recommendations:
        # Check if we need a new page
        if pdf.get_y() > 250:
            pdf.add_page()
        # Set left margin and use 170mm width
        pdf.set_x(15)
        pdf.multi_cell(170, 6, rec)
        pdf.ln(2)  # Small gap between recommendations
    
    # Sign-off section
    pdf.ln(15)
    pdf.set_draw_color(*COLORS['border'])
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(*COLORS['text_light'])
    pdf.cell(0, 5, 'This report was automatically generated by the CargoVision AI Automated Inspection System.', 0, 1, 'C')
    pdf.cell(0, 5, 'For questions or concerns, please contact the system administrator.', 0, 1, 'C')
    
    return pdf
