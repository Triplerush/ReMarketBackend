# app/routes/user_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import user_service
from app.auth.decorators import login_required, admin_required

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['firstName', 'lastName', 'dni', 'tel/movil', 'dir/domicilio', 'email']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Faltan campos requeridos"}), 400
    try:
        new_user = user_service.create_user(data)
        return jsonify({"message": "Usuario creado", "user": new_user}), 201
    except ValueError as e: return jsonify({"error": str(e)}), 409

@bp.route('', methods=['GET'])
@admin_required
def list_users():
    users = user_service.get_all_users()
    return jsonify(users), 200

@bp.route('/<user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    user = user_service.get_user_by_id(user_id)
    if not user: return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200

@bp.route('/<user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    data = request.get_json()
    try:
        updated_user = user_service.update_user(user_id, data, g.user['id'], g.user['role'])
        return jsonify(updated_user), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403

@bp.route('/<user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    try:
        result = user_service.soft_delete_user(user_id, g.user['id'], g.user['role'])
        return jsonify(result), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403