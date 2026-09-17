import qrcode
from fpdf import FPDF
import os

# Disha Locations (Rooms Only)
locations = [
    ("d_main_entrance", "MAIN ENTRANCE"),
    ("d_reception", "RECEPTION / INQUIRY"),
    ("d_general_opd", "GENERAL OPD"),
    ("d_pathology", "PATHOLOGY LAB"),
    ("d_blood_bank", "BLOOD BANK"),
    ("d_icu", "ICU"),
    ("d_male_ward", "GENERAL MALE WARD"),
    ("d_labour", "LABOUR ROOM")
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
    pdf.multi_cell(0, 20, loc_name, align='C')
    
    # Generate QR Code (Using localhost for hackathon demo, or vercel if deployed)
    qr_data = f"http://localhost:5173/?start={loc_id}"
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
    pdf.cell(0, 15, "SCAN THIS QR CODE", align='C')
    
    pdf.set_y(265)
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "TO NAVIGATE THE HOSPITAL", align='C')

output_path = "Disha_QR_Posters.pdf"
pdf.output(output_path)
print(f"Generated {output_path}")
