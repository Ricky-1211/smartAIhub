"""
Spam Detection Service - Email/SMS/Comment spam detection
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sys
import os
import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import ALLOWED_ORIGINS
from shared.utils import create_response, log_error

app = FastAPI(title="Spam Detection Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model storage
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "spam_model.pkl")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")

# Initialize model and vectorizer
vectorizer = None
model = None


class SpamRequest(BaseModel):
    text: str
    type: str = "email"  # email, sms, comment


class SpamResponse(BaseModel):
    is_spam: bool
    confidence: float
    text: str
    type: str


def preprocess_text(text: str) -> str:
    """Preprocess text for spam detection"""
    # Convert to lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    # Remove special characters except spaces
    text = re.sub(r'[^a-z\s]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text


def load_model():
    """Load or initialize spam detection model"""
    global vectorizer, model
    
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            with open(VECTORIZER_PATH, 'rb') as f:
                vectorizer = pickle.load(f)
            return
        except Exception as e:
            log_error("spam-service", e, {"action": "load_model"})
    
    # Initialize new model with sample data
    sample_texts = [
        "Free money now! Click here!",
        "Congratulations! You won $1000!",
        "Hello, how are you?",
        "Meeting at 3pm tomorrow",
        "Buy now! Limited offer!",
        "Thanks for your email",
    ]
    sample_labels = [1, 1, 0, 0, 1, 0]  # 1 = spam, 0 = not spam
    
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X = vectorizer.fit_transform([preprocess_text(t) for t in sample_texts])
    model = MultinomialNB()
    model.fit(X, sample_labels)
    
    # Save model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(VECTORIZER_PATH, 'wb') as f:
        pickle.dump(vectorizer, f)


@app.on_event("startup")
async def startup():
    load_model()


@app.get("/health")
async def health_check():
    return create_response(True, "Spam detection service is healthy")


@app.post("/predict")
async def predict_spam(request: SpamRequest):
    """Predict if text is spam"""
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        # Preprocess text
        processed_text = preprocess_text(request.text)
        
        if not processed_text:
            result = {
                "is_spam": False,
                "confidence": 0.0,
                "text": request.text,
                "type": request.type
            }
            return create_response(True, "Spam prediction completed", result)
        
        # Vectorize
        X = vectorizer.transform([processed_text])
        
        # Predict
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        confidence = float(max(probabilities))
        
        is_spam = bool(prediction == 1)
        
        result = {
            "is_spam": is_spam,
            "confidence": confidence,
            "text": request.text,
            "type": request.type
        }
        
        return create_response(True, "Spam prediction completed", result)
    except Exception as e:
        log_error("spam-service", e, {"text": request.text[:100]})
        raise HTTPException(status_code=500, detail="Prediction failed")


@app.post("/batch-predict")
async def batch_predict(texts: List[str]):
    """Batch spam prediction"""
    results = []
    for text in texts:
        try:
            result = await predict_spam(SpamRequest(text=text))
            results.append(result.dict())
        except Exception as e:
            results.append({
                "text": text,
                "error": str(e)
            })
    return create_response(True, "Batch prediction completed", results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

