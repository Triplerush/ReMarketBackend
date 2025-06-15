# app/routes/saved_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import saved_service
from app.auth.decorators import login_required

bp = Blueprint('saved', __name__, url_prefix='/saved')

@bp.route('', methods=['GET'])
@login_required
def get_saved():
    """Lista los elementos guardados. Admin ve todo, usuario ve solo lo suyo."""
    try:
        if g.user['role'] == 'admin':
            saved_items = saved_service.list_all_saved_items()
        else:
            saved_items = saved_service.list_user_saved_items(g.user['id'])
        return jsonify(saved_items), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<saved_id>', methods=['GET'])
@login_required
def get_one(saved_id):
    """Obtiene un elemento guardado específico."""
    try:
        item = saved_service.get_saved_item_by_id(saved_id, g.user['id'], g.user['role'])
        if not item:
            return jsonify({"error": "Elemento no encontrado"}), 404
        return jsonify(item), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('', methods=['POST'])
@login_required
def create():
    """Guarda un producto en la lista de favoritos."""
    data = request.get_json()
    if not data or 'productId' not in data:
        return jsonify({"error": "Falta el campo requerido: 'productId'"}), 400
    
    try:
        user_id = g.user['id']
        new_item = saved_service.create_saved_item(data, user_id)
        return jsonify(new_item), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409 # Conflict
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# NOTA: La modificación se maneja con la lógica de DELETE (soft delete) y CREATE (reactivación).
# Por lo tanto, no se necesita una ruta PUT dedicada.

@bp.route('/<saved_id>', methods=['DELETE'])
@login_required
def delete(saved_id):
    """Elimina (desactiva) un producto de la lista de guardados."""
    try:
        user_id = g.user['id']
        user_role = g.user['role']
        result = saved_service.delete_saved_item(saved_id, user_id, user_role)
        return jsonify(result), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500