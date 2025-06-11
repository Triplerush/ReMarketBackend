# app/routes/publication_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import publication_service
from app.auth.decorators import login_required, seller_required

bp = Blueprint('publications', __name__, url_prefix='/publications')

@bp.route('', methods=['POST'])
@seller_required
def create():
    """Crea una nueva publicación. Solo para vendedores."""
    data = request.get_json()
    required = ['brand', 'model', 'capacity', 'price', 'imei', 'description']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Faltan campos requeridos"}), 400
    try:
        new_pub = publication_service.create_publication(data, g.user['id'])
        return jsonify(new_pub), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('', methods=['GET'])
def get_all():
    """Obtiene una lista de todas las publicaciones activas y disponibles."""
    pubs = publication_service.get_all_active_publications()
    return jsonify(pubs), 200

@bp.route('/<pub_id>', methods=['GET'])
def get_one(pub_id):
    """Obtiene una publicación específica por su ID."""
    pub = publication_service.get_publication_by_id(pub_id)
    if not pub:
        return jsonify({"error": "Publicación no encontrada"}), 404
    return jsonify(pub), 200

@bp.route('/<pub_id>', methods=['PUT'])
@login_required
def update(pub_id):
    """Actualiza una publicación. Solo para el vendedor dueño."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Cuerpo de la petición vacío"}), 400
    try:
        updated_pub = publication_service.update_publication(pub_id, data, g.user['id'])
        return jsonify(updated_pub), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500

@bp.route('/<pub_id>', methods=['DELETE'])
@login_required
def delete(pub_id):
    """Elimina (desactiva) una publicación. Solo para el vendedor dueño o un admin."""
    try:
        result = publication_service.soft_delete_publication(pub_id, g.user['id'], g.user['role'])
        return jsonify(result), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500