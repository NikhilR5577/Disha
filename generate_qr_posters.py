import qrcode
from fpdf import FPDF
import os

# 20 High-Value Locations
locations = [
    ("r0", "MAIN ENTRANCE"),
    ("r60", "ENTRANCE NO. 2"),
    ("r7", "HELP DESK"),
    ("r6", "EMERGENCY ROOM"),
    ("r41", "PHARMACY"),
    ("r47", "BLOOD BANK"),
    ("r46", "PATHOLOGY"),
    ("r19", "ORTHOPEDIC OPD"),
    ("r17", "SURGICAL OPD"),
    ("r9", "MEDICINE OPD"),
    ("r23", "X-RAY ROOM"),
    ("r25", "SONOGRAPHY ROOM"),
    ("r37", "WARD NO. 1"),
    ("r38", "WARD NO. 2"),
    ("r33", "WARD NO. 3"),
    ("r34", "WARD NO. 4"),
    ("r49", "MATERNITY WARD"),
    ("r42", "ICU"),
    ("r43", "CT SCAN"),
    ("r29", "MEDICAL BOARD")
]

class PosterPDF(FPDF):
    pass

pdf = PosterPDF(orientation='P', unit='mm', format='A4')
pdf.set_auto_page_break(auto=False)

for loc_id, loc_name in locations:
    pdf.add_page()
    
    # Border
    pdf.set_line_width(2)
    pdf.rect(10, 10, 190, 277)
    
    # Top Text (Location Name)
    pdf.set_font("helvetica", "B", 45)
    
    # Adjust font size if text is very long
    if len(loc_name) > 15 and "\n" not in loc_name:
        pdf.set_font("helvetica", "B", 35)
        
    pdf.set_y(35)
    pdf.multi_cell(0, 20, loc_name, align='C', new_x="LMARGIN", new_y="NEXT")
    
    # Generate QR Code
    qr_data = f"https://navcare.vercel.app/?start={loc_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=20,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_path = f"temp_qr_{loc_id}.png"
    img.save(img_path)
    
    # Draw QR Code centered
    qr_size = 140
    qr_x = (210 - qr_size) / 2
    
    # Adjust Y based on text height
    qr_y = 100
    if "\n" in loc_name:
        qr_y = 120
        
    pdf.image(img_path, x=qr_x, y=qr_y, w=qr_size, h=qr_size)
    
    # Clean up temp image
    os.remove(img_path)
    
    # Bottom Text (Instructions)
    pdf.set_y(250)
    pdf.set_font("helvetica", "B", 25)
    pdf.set_text_color(220, 53, 69) # Red color for attention
    pdf.cell(0, 15, "SCAN THIS QR CODE", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_y(265)
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "TO NAVIGATE THE HOSPITAL", align='C', new_x="LMARGIN", new_y="NEXT")

output_path = "NavCare_QR_Posters.pdf"
pdf.output(output_path)
print(f"Generated {output_path}")
