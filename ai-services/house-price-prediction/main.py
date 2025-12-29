"""
House Price Prediction Service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import ALLOWED_ORIGINS
from shared.utils import create_response, log_error

app = FastAPI(title="House Price Prediction Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "house_price_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "house_price_scaler.pkl")

model = None
rent_model = None
scaler = None
rent_scaler = None
city_encoder = None
state_encoder = None
area_encoder = None

# Sample location data with price multipliers (in production, use real data)
LOCATION_MULTIPLIERS = {
    "mumbai": {"city_mult": 1.5, "state": "Maharashtra", "rent_ratio": 0.004},
    "delhi": {"city_mult": 1.4, "state": "Delhi", "rent_ratio": 0.0035},
    "bangalore": {"city_mult": 1.3, "state": "Karnataka", "rent_ratio": 0.003},
    "hyderabad": {"city_mult": 1.2, "state": "Telangana", "rent_ratio": 0.0028},
    "chennai": {"city_mult": 1.25, "state": "Tamil Nadu", "rent_ratio": 0.0025},
    "pune": {"city_mult": 1.15, "state": "Maharashtra", "rent_ratio": 0.0022},
    "kolkata": {"city_mult": 1.1, "state": "West Bengal", "rent_ratio": 0.002},
    "ahmedabad": {"city_mult": 1.05, "state": "Gujarat", "rent_ratio": 0.0018},
}

# Sample area suggestions (in production, use database)
AREA_SUGGESTIONS = {
    "mumbai": [
        {"name": "Bandra", "price_mult": 1.6, "rent_ratio": 0.005},
        {"name": "Andheri", "price_mult": 1.3, "rent_ratio": 0.004},
        {"name": "Powai", "price_mult": 1.4, "rent_ratio": 0.0035},
        {"name": "Thane", "price_mult": 1.0, "rent_ratio": 0.0025},
    ],
    "delhi": [
        {"name": "Gurgaon", "price_mult": 1.5, "rent_ratio": 0.004},
        {"name": "Noida", "price_mult": 1.3, "rent_ratio": 0.0035},
        {"name": "Dwarka", "price_mult": 1.2, "rent_ratio": 0.003},
        {"name": "Rohini", "price_mult": 1.1, "rent_ratio": 0.0025},
    ],
    "bangalore": [
        {"name": "Koramangala", "price_mult": 1.4, "rent_ratio": 0.0035},
        {"name": "Whitefield", "price_mult": 1.3, "rent_ratio": 0.003},
        {"name": "Indiranagar", "price_mult": 1.5, "rent_ratio": 0.004},
        {"name": "Electronic City", "price_mult": 1.1, "rent_ratio": 0.0025},
    ],
}


class HouseFeatures(BaseModel):
    area: float  # in square feet
    bedrooms: int
    bathrooms: float
    city: Optional[str] = None
    state: Optional[str] = None
    area_name: Optional[str] = None  # Neighborhood/area name
    location_score: float = 5.0  # 1-10 scale
    age: int = 0  # years
    floor: int = 1


class PricePrediction(BaseModel):
    predicted_price: float
    predicted_rent: Optional[float] = None
    features: dict
    confidence_interval: dict
    location_info: Optional[dict] = None
    suggested_areas: Optional[List[dict]] = None


def get_location_multiplier(city: Optional[str], state: Optional[str]) -> float:
    """Get price multiplier based on location"""
    if city:
        city_lower = city.lower().strip()
        if city_lower in LOCATION_MULTIPLIERS:
            return LOCATION_MULTIPLIERS[city_lower]["city_mult"]
    
    if state:
        state_lower = state.lower().strip()
        # Check if any city in state matches
        for city_name, data in LOCATION_MULTIPLIERS.items():
            if data.get("state", "").lower() == state_lower:
                return data["city_mult"] * 0.9  # Slightly lower for state-level
    
    return 1.0  # Default multiplier


def get_rent_ratio(city: Optional[str], area_name: Optional[str]) -> float:
    """Get rent to price ratio based on location"""
    if city and area_name:
        city_lower = city.lower().strip()
        area_lower = area_name.lower().strip()
        
        if city_lower in AREA_SUGGESTIONS:
            for area in AREA_SUGGESTIONS[city_lower]:
                if area["name"].lower() == area_lower:
                    return area["rent_ratio"]
    
    if city:
        city_lower = city.lower().strip()
        if city_lower in LOCATION_MULTIPLIERS:
            return LOCATION_MULTIPLIERS[city_lower]["rent_ratio"]
    
    return 0.002  # Default rent ratio (0.2% of price per month)


def get_suggested_areas(city: Optional[str], price_range: tuple) -> List[dict]:
    """Get suggested areas based on city and price range"""
    if not city:
        return []
    
    city_lower = city.lower().strip()
    if city_lower not in AREA_SUGGESTIONS:
        return []
    
    suggestions = []
    for area in AREA_SUGGESTIONS[city_lower]:
        # Calculate estimated price for this area
        base_price = (price_range[0] + price_range[1]) / 2
        estimated_price = base_price * area["price_mult"]
        estimated_rent = estimated_price * area["rent_ratio"]
        
        suggestions.append({
            "name": area["name"],
            "estimated_price": round(estimated_price, 2),
            "estimated_rent": round(estimated_rent, 2),
            "price_multiplier": area["price_mult"]
        })
    
    # Sort by estimated price
    suggestions.sort(key=lambda x: x["estimated_price"])
    return suggestions


def initialize_model():
    """Initialize or load house price prediction model"""
    global model, rent_model, scaler, rent_scaler
    
    RENT_MODEL_PATH = os.path.join(MODEL_DIR, "house_rent_model.pkl")
    RENT_SCALER_PATH = os.path.join(MODEL_DIR, "house_rent_scaler.pkl")
    
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            with open(SCALER_PATH, 'rb') as f:
                scaler = pickle.load(f)
            if os.path.exists(RENT_MODEL_PATH) and os.path.exists(RENT_SCALER_PATH):
                with open(RENT_MODEL_PATH, 'rb') as f:
                    rent_model = pickle.load(f)
                with open(RENT_SCALER_PATH, 'rb') as f:
                    rent_scaler = pickle.load(f)
            return
        except Exception as e:
            log_error("house-service", e, {"action": "load_model"})
    
    # Train a simple model with sample data
    # In production, use real dataset
    np.random.seed(42)
    n_samples = 200
    
    # Generate sample data
    X = np.array([
        np.random.uniform(500, 5000, n_samples),  # area
        np.random.randint(1, 6, n_samples),  # bedrooms
        np.random.uniform(1, 5, n_samples),  # bathrooms
        np.random.uniform(1, 10, n_samples),  # location_score
        np.random.randint(0, 50, n_samples),  # age
        np.random.randint(1, 20, n_samples),  # floor
    ]).T
    
    # Generate prices (simple formula for demo)
    y = (X[:, 0] * 100 +  # area
         X[:, 1] * 50000 +  # bedrooms
         X[:, 2] * 30000 +  # bathrooms
         X[:, 3] * 20000 +  # location
         -X[:, 4] * 1000 +  # age (negative)
         X[:, 5] * 5000 +  # floor
         np.random.normal(0, 50000, n_samples))  # noise
    
    # Generate rent (typically 0.2-0.5% of price per month)
    rent_ratio = np.random.uniform(0.002, 0.005, n_samples)
    y_rent = y * rent_ratio
    
    # Train price model
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = LinearRegression()
    model.fit(X_scaled, y)
    
    # Train rent model
    rent_scaler = StandardScaler()
    X_rent_scaled = rent_scaler.fit_transform(X)
    rent_model = LinearRegression()
    rent_model.fit(X_rent_scaled, y_rent)
    
    # Save models
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    with open(RENT_MODEL_PATH, 'wb') as f:
        pickle.dump(rent_model, f)
    with open(RENT_SCALER_PATH, 'wb') as f:
        pickle.dump(rent_scaler, f)


@app.on_event("startup")
async def startup():
    initialize_model()


@app.get("/health")
async def health_check():
    return create_response(True, "House price prediction service is healthy")


@app.post("/predict")
async def predict_price(features: HouseFeatures):
    """Predict house price and rent"""
    try:
        # Prepare features
        X = np.array([[
            features.area,
            features.bedrooms,
            features.bathrooms,
            features.location_score,
            features.age,
            features.floor
        ]])
        
        # Scale features
        X_scaled = scaler.transform(X)
        
        # Predict base price
        predicted_price = model.predict(X_scaled)[0]
        
        # Apply location multiplier
        location_mult = get_location_multiplier(features.city, features.state)
        predicted_price = predicted_price * location_mult
        
        # Predict rent
        predicted_rent = None
        if rent_model:
            X_rent_scaled = rent_scaler.transform(X)
            predicted_rent = rent_model.predict(X_rent_scaled)[0] * location_mult
        else:
            # Fallback: use rent ratio
            rent_ratio = get_rent_ratio(features.city, features.area_name)
            predicted_rent = predicted_price * rent_ratio
        
        # Calculate confidence interval (simplified)
        std_error = 50000 * location_mult  # Standard error estimate
        lower_bound = max(0, predicted_price - 1.96 * std_error)
        upper_bound = predicted_price + 1.96 * std_error
        
        # Get location info
        location_info = None
        if features.city or features.state:
            location_info = {
                "city": features.city,
                "state": features.state,
                "area": features.area_name,
                "location_multiplier": location_mult,
                "rent_ratio": get_rent_ratio(features.city, features.area_name)
            }
        
        # Get suggested areas
        suggested_areas = None
        if features.city:
            price_range = (lower_bound, upper_bound)
            suggested_areas = get_suggested_areas(features.city, price_range)
        
        result = {
            "predicted_price": round(float(predicted_price), 2),
            "predicted_rent": round(float(predicted_rent), 2) if predicted_rent else None,
            "features": features.dict(),
            "confidence_interval": {
                "lower": round(lower_bound, 2),
                "upper": round(upper_bound, 2)
            },
            "location_info": location_info,
            "suggested_areas": suggested_areas
        }
        
        return create_response(True, "Price prediction completed", result)
    except Exception as e:
        log_error("house-service", e)
        raise HTTPException(status_code=500, detail="Prediction failed")


@app.get("/predict")
async def predict_price_get(
    area: float,
    bedrooms: int,
    bathrooms: float,
    city: Optional[str] = None,
    state: Optional[str] = None,
    area_name: Optional[str] = None,
    location_score: float = 5.0,
    age: int = 0,
    floor: int = 1
):
    """Predict house price (GET endpoint)"""
    features = HouseFeatures(
        area=area,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        city=city,
        state=state,
        area_name=area_name,
        location_score=location_score,
        age=age,
        floor=floor
    )
    return await predict_price(features)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)

