# app/auth/decorators.py
from functools import wraps
from flask import request, jsonify, g
from firebase_admin import auth
from app.services import user_service

def login_required(f):
    """
    Decorador que verifica un ID Token de Firebase real desde la cabecera 'Authorization'.
    Si el token es válido, obtiene el UID del usuario, carga su perfil desde Firestore 
    y lo adjunta al objeto global 'g' de Flask.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Cabecera 'Authorization: Bearer <token>' faltante o mal formada."}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            # Verificar el ID Token con el Admin SDK
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            
            # Obtenemos el perfil del usuario desde Firestore para obtener su rol y otros datos
            user_profile = user_service.get_user_by_id(uid)

            if not user_profile:
                # Este caso ocurre si un usuario existe en Firebase Auth pero no en nuestra DB Firestore
                return jsonify({"error": "Perfil de usuario no encontrado en la base de datos."}), 404
            
            # 'g' es un objeto global de Flask para el contexto de una petición.
            # Guardamos los datos del usuario aquí para usarlos en las rutas.
            g.user = user_profile

        except auth.ExpiredIdTokenError:
            return jsonify({"error": "El token ha expirado. Por favor, inicie sesión de nuevo."}), 401
        except auth.InvalidIdTokenError:
            return jsonify({"error": "Token de ID inválido."}), 401
        except Exception as e:
            return jsonify({"error": f"Error de autenticación: {e}"}), 401
            
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """Decorador genérico que verifica si el usuario tiene un rol específico."""
    def decorator(f):
        @wraps(f)
        @login_required # Primero nos aseguramos que el usuario está logueado
        def decorated_function(*args, **kwargs):
            # g.user ahora es un diccionario con el perfil completo
            if g.user.get('role') != role_name:
                return jsonify({"error": f"Acceso denegado. Se requiere el rol de '{role_name}'."}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Creamos decoradores específicos para facilitar su uso
seller_required = role_required('seller')
admin_required = role_required('admin')