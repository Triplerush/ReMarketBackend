# app/routes/rating_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import rating_service
from app.auth.decorators import login_required

bp = Blueprint('ratings', __name__, url_prefix='/ratings')

@bp.route('', methods=['GET'])
def get_all():
    """Obtiene una lista de calificaciones. Puede filtrarse por producto (público)."""
    product_id = request.args.get('productId')
    try:
        ratings = rating_service.list_ratings(product_id=product_id)
        return jsonify(ratings), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<rating_id>', methods=['GET'])
def get_one(rating_id):
    """Obtiene una calificación específica por su ID (público)."""
    rating = rating_service.get_rating_by_id(rating_id)
    if not rating:
        return jsonify({"error": "Calificación no encontrada"}), 404
    return jsonify(rating), 200

@bp.route('', methods=['POST'])
@login_required # Requiere que el usuario esté autenticado
def create():
    """Crea una nueva calificación."""
    data = request.get_json()
    required = ['productId', 'score']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Faltan campos requeridos: 'productId' y 'score'"}), 400
    
    if not 1 <= int(data['score']) <= 5:
        return jsonify({"error": "El 'score' debe ser un número entre 1 y 5."}), 400
    
    try:
        # El 'buyerId' se toma del usuario autenticado
        buyer_id = g.user['id']
        new_rating = rating_service.create_rating(data, buyer_id)
        return jsonify(new_rating), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409 # 409 Conflict si ya existe
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<rating_id>', methods=['PUT'])
@login_required # Requiere que el usuario esté autenticado
def update(rating_id):
    """Actualiza una calificación. Permisos validados en el servicio."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Cuerpo de la petición vacío"}), 400
    
    try:
        user_id = g.user['id']
        user_role = g.user['role']
        updated_rating = rating_service.update_rating(rating_id, data, user_id, user_role)
        return jsonify(updated_rating), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@bp.route('/<rating_id>', methods=['DELETE'])
@login_required # Requiere que el usuario esté autenticado
def delete(rating_id):
    """Elimina una calificación. Permisos validados en el servicio."""
    try:
        user_id = g.user['id']
        user_role = g.user['role']
        result = rating_service.delete_rating(rating_id, user_id, user_role)
        return jsonify(result), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500