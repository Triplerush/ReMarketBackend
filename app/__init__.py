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

    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK inicializado exitosamente.")
        except Exception as e:
            print(f"Error CRÍTICO inicializando Firebase Admin SDK: {e}")
    
    db = firestore.client()

    with app.app_context():
        # Importamos las rutas actualizadas
        from .routes import auth_routes, chat_routes, user_routes, product_routes, rating_routes, report_routes, transaction_routes, saved_routes
        
        app.register_blueprint(auth_routes.bp)
        app.register_blueprint(chat_routes.bp)
        app.register_blueprint(user_routes.bp)
        app.register_blueprint(product_routes.bp)
        app.register_blueprint(rating_routes.bp)
        app.register_blueprint(report_routes.bp)
        app.register_blueprint(transaction_routes.bp)
        app.register_blueprint(saved_routes.bp)

        
        print("Todos los Blueprints han sido registrados.")

    return app