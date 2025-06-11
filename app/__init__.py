# app/__init__.py
import os
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore
from .config import Config

db = None

def create_app():
    global db
    app = Flask(__name__)
    app.config.from_object(Config)

    # Evita reinicializar la app de Firebase si ya existe
    if not firebase_admin._apps:
        try:
            # Usamos la configuración de Config para mantenerlo centralizado
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK inicializado exitosamente.")
        except Exception as e:
            print(f"Error CRÍTICO inicializando Firebase Admin SDK: {e}")
    
    db = firestore.client()

    with app.app_context():
        # --- LÍNEA DE IMPORTACIÓN CORREGIDA ---
        from .routes import user_routes, publication_routes, order_routes, rating_routes, report_routes
        # NOTA: Había un 'transaction_routes' que no existía, lo he quitado por ahora.
        # Si lo creas, puedes añadirlo de nuevo.

        app.register_blueprint(user_routes.bp)
        # --- LÍNEA DE REGISTRO CORREGIDA ---
        app.register_blueprint(publication_routes.bp)
        app.register_blueprint(order_routes.bp)
        app.register_blueprint(rating_routes.bp)
        app.register_blueprint(report_routes.bp)
        
        print("Todos los Blueprints han sido registrados.")

    return app