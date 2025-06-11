# app/utils.py
from datetime import datetime
# --- LÍNEA CORREGIDA ---
from google.cloud.firestore_v1 import GeoPoint 

def clean_firestore_doc(doc_data):
    """
    Limpia un diccionario de datos de Firestore, convirtiendo tipos especiales
    (datetime, GeoPoint) a formatos serializables en JSON.
    """
    if not doc_data:
        return doc_data

    for key, value in doc_data.items():
        if isinstance(value, datetime):
            doc_data[key] = value.isoformat()
        elif isinstance(value, GeoPoint):
            doc_data[key] = { "latitude": value.latitude, "longitude": value.longitude }
    
    return doc_data