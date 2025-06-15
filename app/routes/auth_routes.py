# app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from app.services import auth_service

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['POST'])
def register():
    """
    Endpoint para registrar un nuevo usuario.
    Recibe los datos del perfil y las credenciales.
    """
    data = request.get_json()
    required = ['firstName', 'lastName', 'dniNumber', 'email', 'password']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Faltan campos requeridos: 'firstName', 'lastName', 'dniNumber', 'email', 'password'"}), 400

    try:
        new_user = auth_service.register_user(data)
        # Por seguridad, no devolvemos la contraseña. El servicio de usuario ya no la maneja.
        return jsonify({"message": "Usuario registrado exitosamente", "user": new_user}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409 # 409 Conflict
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- EXPLICACIÓN DEL ENDPOINT DE LOGIN ---
# El backend NO debe recibir la contraseña del usuario para el login.
# El flujo correcto es:
# 1. El CLIENTE (app móvil/web) usa el SDK de Firebase para hacer signInWithEmailAndPassword.
# 2. Firebase le devuelve al CLIENTE un ID Token si las credenciales son correctas.
# 3. El CLIENTE envía ese ID Token a las rutas protegidas del backend.
#
# Este endpoint '/login' es conceptual. Podría usarse para que el cliente,
# después de iniciar sesión en Firebase, obtenga el perfil completo de la base de datos
# si lo necesitara.

@bp.route('/login', methods=['POST'])
def login():
    """
    Este endpoint NO es para un login tradicional con email/password.
    Es para que el cliente, una vez logueado en Firebase y con un ID Token,
    pueda verificarlo e iniciar una "sesión" en el backend (aunque es sin estado).
    La verificación real ocurre en el decorador @login_required en otras rutas.
    """
    return jsonify({
        "message": "El login se maneja en el cliente con el SDK de Firebase. Usa el ID Token obtenido para acceder a las rutas protegidas."
    }), 200