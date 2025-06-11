# app/routes/rating_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import rating_service
from app.auth.decorators import login_required

bp = Blueprint('ratings', __name__, url_prefix='/ratings')

@bp.route('', methods=['POST'])
@login_required
def create():
    data = request.get_json()
    required = ['orderId', 'score', 'comment']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Faltan campos: 'orderId', 'score', 'comment'"}), 400
    if not 1 <= int(data['score']) <= 5:
        return jsonify({"error": "El 'score' debe ser un número entre 1 y 5."}), 400
    try:
        new_rating = rating_service.create_rating(data, g.user['id'])
        return jsonify(new_rating), 201
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 400

@bp.route('', methods=['GET'])
def get_all():
    user_id = request.args.get('userId')
    ratings = rating_service.list_ratings(user_id=user_id)
    return jsonify(ratings), 200

@bp.route('/<rating_id>', methods=['GET'])
def get_one(rating_id):
    rating = rating_service.get_rating_by_id(rating_id)
    if not rating: return jsonify({"error": "Calificación no encontrada"}), 404
    return jsonify(rating), 200

@bp.route('/<rating_id>', methods=['PUT'])
@login_required
def update(rating_id):
    data = request.get_json()
    try:
        updated_rating = rating_service.update_rating(rating_id, data, g.user['id'])
        return jsonify(updated_rating), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403

@bp.route('/<rating_id>', methods=['DELETE'])
@login_required
def delete(rating_id):
    try:
        result = rating_service.soft_delete_rating(rating_id, g.user['id'], g.user['role'])
        return jsonify(result), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403