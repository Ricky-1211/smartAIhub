"""
Fraud Detection Service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os
import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import ALLOWED_ORIGINS
from shared.utils import create_response, log_error

app = FastAPI(title="Fraud Detection Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "fraud_detection_model.pkl")

model = None


class Transaction(BaseModel):
    amount: float
    user_id: str
    merchant_id: str
    transaction_type: str  # purchase, withdrawal, transfer
    location: Optional[str] = None
    timestamp: Optional[str] = None
    previous_transactions_count: int = 0
    account_age_days: int = 0


class FraudPrediction(BaseModel):
    is_fraud: bool
    fraud_score: float
    risk_level: str
    reasons: list


def extract_features(transaction: Transaction) -> np.ndarray:
    """Extract features from transaction"""
    # Normalize amount (log scale)
    amount_log = np.log1p(transaction.amount)
    
    # Transaction type encoding
    type_map = {"purchase": 0, "withdrawal": 1, "transfer": 2}
    transaction_type_encoded = type_map.get(transaction.transaction_type.lower(), 0)
    
    # Features: [amount_log, transaction_type, previous_count, account_age]
    features = np.array([[
        amount_log,
        transaction_type_encoded,
        transaction.previous_transactions_count,
        transaction.account_age_days
    ]])
    
    return features


def initialize_model():
    """Initialize fraud detection model"""
    global model
    
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            return
        except Exception as e:
            log_error("fraud-service", e, {"action": "load_model"})
    
    # Train Isolation Forest with sample data
    np.random.seed(42)
    n_samples = 1000
    
    # Generate normal transactions
    normal_data = np.array([
        np.random.uniform(0, 8, n_samples),  # log(amount)
        np.random.randint(0, 3, n_samples),  # transaction_type
        np.random.randint(0, 100, n_samples),  # previous_count
        np.random.randint(30, 3650, n_samples),  # account_age
    ]).T
    
    # Train model
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(normal_data)
    
    # Save model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)


def predict_fraud(transaction: Transaction) -> dict:
    """Predict if transaction is fraudulent"""
    features = extract_features(transaction)
    
    # Predict
    prediction = model.predict(features)[0]
    score = model.score_samples(features)[0]
    
    # Normalize score to 0-1 range (lower = more anomalous)
    fraud_score = 1 / (1 + np.exp(score))  # Sigmoid transformation
    
    is_fraud = prediction == -1 or fraud_score > 0.7
    
    # Determine risk level
    if fraud_score > 0.8:
        risk_level = "high"
    elif fraud_score > 0.5:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Generate reasons
    reasons = []
    if transaction.amount > 10000:
        reasons.append("Unusually large transaction amount")
    if transaction.previous_transactions_count < 5:
        reasons.append("New user with limited transaction history")
    if transaction.account_age_days < 30:
        reasons.append("Recently created account")
    if fraud_score > 0.7:
        reasons.append("Anomalous transaction pattern detected")
    
    return {
        "is_fraud": is_fraud,
        "fraud_score": round(float(fraud_score), 4),
        "risk_level": risk_level,
        "reasons": reasons
    }


@app.on_event("startup")
async def startup():
    initialize_model()


@app.get("/health")
async def health_check():
    return create_response(True, "Fraud detection service is healthy")


@app.post("/detect")
async def detect_fraud(transaction: Transaction):
    """Detect fraud in transaction"""
    try:
        result = predict_fraud(transaction)
        return create_response(True, "Fraud detection completed", result)
    except Exception as e:
        log_error("fraud-service", e)
        raise HTTPException(status_code=500, detail="Fraud detection failed")


@app.post("/batch-detect")
async def batch_detect_fraud(transactions: list[Transaction]):
    """Batch fraud detection"""
    results = []
    for transaction in transactions:
        try:
            result = predict_fraud(transaction)
            results.append({
                "transaction": transaction.dict(),
                "prediction": result
            })
        except Exception as e:
            results.append({
                "transaction": transaction.dict(),
                "error": str(e)
            })
    
    return create_response(True, "Batch detection completed", results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)

