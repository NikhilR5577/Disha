# Disha - AWS Hackathon 🚀

A next-generation hospital digital wayfinding platform powered by **Amazon Web Services**. Disha allows patients to scan a QR code inside a hospital, speak their destination in Hindi or English, and receive an instant indoor route on their phone—all without installing an app.

## Key Features
- **Amazon Polly Voice Engine**: Premium multilingual text-to-speech navigation guidance using AWS Polly's 'Aditi' neural voice.
- **Multilingual NLP**: Speak naturally in Hindi ("मुझे आईसीयू जाना है") and the engine intelligently maps it to the correct hospital department.
- **2-Floor Interactive Routing**: A complete graph-theory based routing engine (A*) spanning the Ground Floor and First Floor.
- **Zero-Install Experience**: Patients scan physical QR codes and use the web-based app instantly.

## Project Architecture

This is a monorepo consisting of:
- `frontend/`: React + Vite + Tailwind CSS for the user-facing web app. Features auto-floor switching and vector-based SVG routing.
- `backend/`: FastAPI + Python for the routing engine, NLP synonym processing, and AWS integrations.
- `generate_qr_posters.py`: Utility script to generate printable PDFs of QR codes for physical hospital walls.

## Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- AWS Account with an IAM User provisioned for `AmazonPollyFullAccess`

### Backend Setup
1. `cd backend`
2. `python -m venv .venv`
3. Activate virtual environment (`.\.venv\Scripts\activate`)
4. `pip install -r requirements.txt`
5. Create a `.env` file in the `backend/` directory with your AWS Credentials:
   ```env
   AWS_ACCESS_KEY_ID="your_key"
   AWS_SECRET_ACCESS_KEY="your_secret"
   AWS_REGION="ap-south-1"
   ```
6. `uvicorn app.main:app --reload`

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`

*Built for the AWS Hackathon.*
