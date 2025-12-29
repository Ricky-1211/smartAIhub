"""
WhatsApp Chat Analysis Service
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
import re
from datetime import datetime
from collections import Counter, defaultdict
import json
from io import BytesIO
import base64

# Image processing imports
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
    # Initialize EasyOCR reader (English)
    try:
        easyocr_reader = easyocr.Reader(['en'], gpu=False)
    except:
        easyocr_reader = None
        EASYOCR_AVAILABLE = False
except ImportError:
    EASYOCR_AVAILABLE = False
    easyocr_reader = None

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import ALLOWED_ORIGINS
from shared.utils import create_response, log_error

app = FastAPI(title="WhatsApp Analysis Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to import sentiment analysis libraries (optional)
try:
    from textblob import TextBlob
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False


class AnalysisRequest(BaseModel):
    chat_text: str
    images: Optional[List[str]] = None  # Base64 encoded images


class AnalysisResponse(BaseModel):
    total_messages: int
    total_participants: int
    most_active_user: str
    sentiment_analysis: Dict
    word_frequency: Dict[str, int]
    emoji_analysis: Dict[str, int]
    timeline_analysis: List[Dict]
    participants: List[str]


def parse_whatsapp_chat(chat_text: str) -> List[Dict]:
    """Parse WhatsApp chat export"""
    messages = []
    # WhatsApp format: [DD/MM/YYYY, HH:MM:SS AM/PM] Sender: Message
    pattern = r'\[(\d{1,2}/\d{1,2}/\d{4}),\s*(\d{1,2}:\d{2}:\d{2}\s*[AP]M)\]\s*([^:]+):\s*(.+)'
    
    for line in chat_text.split('\n'):
        match = re.match(pattern, line)
        if match:
            date_str, time_str, sender, message = match.groups()
            try:
                # Parse date and time
                dt_str = f"{date_str} {time_str}"
                dt = datetime.strptime(dt_str, "%d/%m/%Y %I:%M:%S %p")
                
                messages.append({
                    "timestamp": dt.isoformat(),
                    "sender": sender.strip(),
                    "message": message.strip(),
                    "date": date_str,
                    "time": time_str
                })
            except:
                continue
    
    return messages


def analyze_sentiment(text: str) -> Dict:
    """Analyze sentiment of text"""
    if not SENTIMENT_AVAILABLE:
        return {"polarity": 0.0, "subjectivity": 0.0, "label": "neutral"}
    
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        return {
            "polarity": float(polarity),
            "subjectivity": float(subjectivity),
            "label": label
        }
    except:
        return {"polarity": 0.0, "subjectivity": 0.0, "label": "neutral"}


def extract_emojis(text: str) -> List[str]:
    """Extract emojis from text"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.findall(text)


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image using OCR"""
    extracted_text = ""
    
    if not PIL_AVAILABLE:
        return extracted_text
    
    try:
        # Open image
        image = Image.open(BytesIO(image_bytes))
        
        # Try EasyOCR first (more accurate)
        if EASYOCR_AVAILABLE and easyocr_reader:
            try:
                results = easyocr_reader.readtext(image_bytes)
                extracted_text = " ".join([result[1] for result in results])
                if extracted_text:
                    return extracted_text
            except Exception as e:
                log_error("whatsapp-service", e, {"action": "easyocr"})
        
        # Fallback to Tesseract
        if TESSERACT_AVAILABLE:
            try:
                extracted_text = pytesseract.image_to_string(image)
            except Exception as e:
                log_error("whatsapp-service", e, {"action": "tesseract"})
        
    except Exception as e:
        log_error("whatsapp-service", e, {"action": "image_processing"})
    
    return extracted_text.strip()


def process_images(images: Optional[List[str]]) -> str:
    """Process base64 encoded images and extract text"""
    if not images:
        return ""
    
    all_extracted_text = []
    
    for img_base64 in images:
        try:
            # Decode base64 image
            if img_base64.startswith('data:image'):
                # Remove data URL prefix
                img_base64 = img_base64.split(',')[1]
            
            image_bytes = base64.b64decode(img_base64)
            extracted_text = extract_text_from_image(image_bytes)
            
            if extracted_text:
                all_extracted_text.append(extracted_text)
        except Exception as e:
            log_error("whatsapp-service", e, {"action": "decode_image"})
            continue
    
    return "\n".join(all_extracted_text)


@app.get("/health")
async def health_check():
    return create_response(True, "WhatsApp analysis service is healthy")


@app.post("/analyze")
async def analyze_chat(request: AnalysisRequest):
    """Analyze WhatsApp chat"""
    try:
        # Process images if provided
        image_text = ""
        if request.images:
            image_text = process_images(request.images)
            if image_text:
                # Append extracted text to chat text
                request.chat_text += "\n\n[Extracted from images]\n" + image_text
        
        messages = parse_whatsapp_chat(request.chat_text)
        
        if not messages:
            raise HTTPException(
                status_code=400,
                detail="Could not parse chat. Please ensure it's in WhatsApp export format."
            )
        
        # Basic stats
        total_messages = len(messages)
        participants = list(set([msg["sender"] for msg in messages]))
        total_participants = len(participants)
        
        # Most active user
        sender_counts = Counter([msg["sender"] for msg in messages])
        most_active_user = sender_counts.most_common(1)[0][0] if sender_counts else ""
        
        # Word frequency
        all_words = []
        for msg in messages:
            words = re.findall(r'\b\w+\b', msg["message"].lower())
            all_words.extend(words)
        word_frequency = dict(Counter(all_words).most_common(20))
        
        # Emoji analysis
        emoji_counts = Counter()
        for msg in messages:
            emojis = extract_emojis(msg["message"])
            emoji_counts.update(emojis)
        emoji_analysis = dict(emoji_counts.most_common(10))
        
        # Sentiment analysis
        all_text = " ".join([msg["message"] for msg in messages])
        sentiment = analyze_sentiment(all_text)
        
        # Timeline analysis (messages per day)
        timeline = defaultdict(int)
        for msg in messages:
            timeline[msg["date"]] += 1
        timeline_analysis = [
            {"date": date, "count": count}
            for date, count in sorted(timeline.items())
        ]
        
        result = {
            "total_messages": total_messages,
            "total_participants": total_participants,
            "most_active_user": most_active_user,
            "sentiment_analysis": sentiment,
            "word_frequency": word_frequency,
            "emoji_analysis": emoji_analysis,
            "timeline_analysis": timeline_analysis,
            "participants": participants
        }
        
        return create_response(True, "Chat analysis completed", result)
    except HTTPException:
        raise
    except Exception as e:
        log_error("whatsapp-service", e)
        raise HTTPException(status_code=500, detail="Analysis failed")


@app.post("/analyze-file")
async def analyze_chat_file(file: UploadFile = File(...)):
    """Analyze WhatsApp chat from uploaded file"""
    try:
        content = await file.read()
        
        # Check if it's an image
        if file.content_type and file.content_type.startswith('image/'):
            # Extract text from image
            extracted_text = extract_text_from_image(content)
            if not extracted_text:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from image. Please ensure the image contains readable text."
                )
            request = AnalysisRequest(chat_text=extracted_text)
        else:
            # Regular text file
            chat_text = content.decode('utf-8', errors='ignore')
            request = AnalysisRequest(chat_text=chat_text)
        
        return await analyze_chat(request)
    except HTTPException:
        raise
    except Exception as e:
        log_error("whatsapp-service", e)
        raise HTTPException(status_code=500, detail="File analysis failed")


@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """Extract text from uploaded image"""
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        content = await file.read()
        extracted_text = extract_text_from_image(content)
        
        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from image. Please ensure the image contains readable text."
            )
        
        return create_response(
            True,
            "Text extracted from image",
            {"extracted_text": extracted_text}
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error("whatsapp-service", e)
        raise HTTPException(status_code=500, detail="Image analysis failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

