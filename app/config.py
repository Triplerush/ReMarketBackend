# app/config.py
import os

class Config:
    FIREBASE_CREDENTIALS_PATH = os.getenv(
        'GOOGLE_APPLICATION_CREDENTIALS', 
        'firebase-adminsdk-credentials.json'
    )
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')