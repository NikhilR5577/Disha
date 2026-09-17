import boto3
import os
from dotenv import load_dotenv
from io import BytesIO
from gtts import gTTS

load_dotenv()

def get_polly_client():
    """Initializes and returns the Amazon Polly client using credentials from .env"""
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        return None
        
    return boto3.client(
        'polly',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')
    )

def synthesize_speech(text: str, is_hindi: bool = True):
    """
    Synthesize speech using Amazon Polly if available.
    Otherwise, gracefully fallback to Google TTS.
    Returns the mp3 audio stream bytes.
    """
    try:
        client = get_polly_client()
        if client:
            # 'Aditi' is standard bilingual (Hindi/Indian English)
            voice_id = 'Aditi' 
            language_code = 'hi-IN' if is_hindi else 'en-IN'
            
            response = client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode=language_code,
                Engine='standard'
            )
            
            if 'AudioStream' in response:
                print("Generated TTS using Amazon Polly")
                return response['AudioStream'].read()
                
    except Exception as e:
        print(f"AWS Polly failed, falling back. Error: {e}")
        
    # FALLBACK: If AWS fails or keys are missing, use Google TTS instantly
    print("Generating TTS using gTTS Fallback...")
    lang = 'hi' if is_hindi else 'en'
    tts = gTTS(text=text, lang=lang, slow=False)
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()
