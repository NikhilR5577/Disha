import os
import qrcode
import sys

# The base URL of your deployed Vercel app
BASE_URL = "https://navcare.vercel.app" # <--- Change this to your real Vercel URL once deployed

# Key locations where you want to physically stick a QR code
# Format: (Location ID, Display Name for the image file)
LOCATIONS = [
    ("entrance_1", "Main_Entrance"),
    ("reception", "Reception_Desk"),
    ("opd_1", "General_OPD"),
    ("emergency", "Emergency_Ward"),
    ("blood_bank", "Blood_Bank"),
    ("xray", "X_Ray_Room"),
    ("lift_1", "Ground_Floor_Lift"),
    ("icu", "ICU_Entrance"),
    ("pharmacy", "Pharmacy")
]

# Create output directory
output_dir = os.path.join(os.path.dirname(__file__), "..", "QR_Codes")
os.makedirs(output_dir, exist_ok=True)

print(f"Generating QR Codes in: {output_dir}")

for loc_id, name in LOCATIONS:
    # Generate the URL that forces the app to start at this location
    url = f"{BASE_URL}/?start={loc_id}"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save image
    file_path = os.path.join(output_dir, f"{name}_QR.png")
    img.save(file_path)
    print(f"âœ… Generated: {name}_QR.png ({url})")

print("\nDone! You can now print these images and stick them on the hospital walls.")
