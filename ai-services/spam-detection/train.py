"""
Train spam detection model
"""
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import os

# Sample training data (in production, use real dataset)
def create_sample_data():
    """Create sample training data"""
    spam_texts = [
        "Free money now! Click here!",
        "Congratulations! You won $1000!",
        "Buy now! Limited offer!",
        "Click here for free prizes!",
        "You've been selected! Claim your reward!",
        "Act now! Special discount!",
        "Win $5000 today!",
        "Free gift card! Click now!",
    ]
    
    ham_texts = [
        "Hello, how are you?",
        "Meeting at 3pm tomorrow",
        "Thanks for your email",
        "Can we schedule a call?",
        "I'll send the report by Friday",
        "Let me know your thoughts",
        "Looking forward to working with you",
        "Have a great day!",
    ]
    
    texts = spam_texts + ham_texts
    labels = [1] * len(spam_texts) + [0] * len(ham_texts)
    
    return texts, labels


def train_model():
    """Train spam detection model"""
    print("Loading data...")
    texts, labels = create_sample_data()
    
    print("Preprocessing...")
    from main import preprocess_text
    processed_texts = [preprocess_text(text) for text in texts]
    
    print("Vectorizing...")
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X = vectorizer.fit_transform(processed_texts)
    y = labels
    
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training model...")
    model = MultinomialNB()
    model.fit(X_train, y_train)
    
    print("Evaluating...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.2f}")
    print(classification_report(y_test, y_pred))
    
    print("Saving model...")
    os.makedirs("models", exist_ok=True)
    with open("models/spam_model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open("models/vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    
    print("Model saved successfully!")


if __name__ == "__main__":
    train_model()

