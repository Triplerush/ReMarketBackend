# app/auth/decorators.py
from functools import wraps
from flask import request, jsonify, g

def login_required(f):
    """Decorador que verifica una cabecera de autenticación simulada y adjunta el usuario a 'g'."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Cabecera 'Authorization: Bearer <token>' faltante o mal formada."}), 401
        
        token = auth_header.split('Bearer ')[1]
        
        try:
            # Simulación: El token es "user_id:role"
            user_id, role = token.split(':')
            if not user_id or not role:
                raise ValueError()
            # 'g' es un objeto global de Flask para el contexto de una petición.
            # Guardamos los datos del usuario aquí para usarlos en las rutas.
            g.user = {'id': user_id, 'role': role}
        except (ValueError, IndexError):
            return jsonify({"error": "Token simulado inválido. Use el formato 'user-id:role'."}), 401
            
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """Decorador genérico que verifica si el usuario tiene un rol específico."""
    def decorator(f):
        @wraps(f)
        @login_required # Primero nos aseguramos que el usuario está logueado
        def decorated_function(*args, **kwargs):
            if g.user.get('role') != role_name:
                return jsonify({"error": f"Acceso denegado. Se requiere el rol de '{role_name}'."}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Creamos decoradores específicos para facilitar su uso
seller_required = role_required('seller')
admin_required = role_required('admin')