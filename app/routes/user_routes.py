# app/routes/user_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import user_service
from app.auth.decorators import login_required, admin_required

bp = Blueprint('users', __name__, url_prefix='/users')

# La ruta de registro ha sido movida a auth_routes.py

@bp.route('', methods=['GET'])
@admin_required
def list_users():
    """Lista todos los usuarios (solo para administradores)."""
    users = user_service.get_all_users()
    return jsonify(users), 200

@bp.route('/me', methods=['GET'])
@login_required
def get_me():
    """Ruta de conveniencia para que un usuario obtenga su propio perfil."""
    # g.user es cargado por el decorador @login_required
    return jsonify(g.user), 200

@bp.route('/<user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """Obtiene un perfil de usuario por su ID."""
    user = user_service.get_user_by_id(user_id)
    if not user: 
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200

@bp.route('/<user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Actualiza un perfil de usuario."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Cuerpo de la petición vacío"}), 400
    try:
        updated_user = user_service.update_user(user_id, data, g.user['id'], g.user['role'])
        return jsonify(updated_user), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403

@bp.route('/<user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Desactiva un usuario (soft delete)."""
    try:
        result = user_service.soft_delete_user(user_id, g.user['id'], g.user['role'])
        return jsonify(result), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403