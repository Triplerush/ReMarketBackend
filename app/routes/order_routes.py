# app/routes/order_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import order_service
from app.auth.decorators import login_required

bp = Blueprint('orders', __name__, url_prefix='/orders')

@bp.route('', methods=['POST'])
@login_required
def create():
    """Crea una nueva orden de compra."""
    data = request.get_json()
    required = ['pubId', 'paymentMethod']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Faltan campos: 'pubId' y 'paymentMethod'"}), 400
    try:
        new_order = order_service.create_order(data, g.user['id'])
        return jsonify(new_order), 201
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 400

@bp.route('', methods=['GET'])
@login_required
def get_all():
    """Lista todas las órdenes en las que el usuario es comprador o vendedor."""
    orders = order_service.list_user_orders(g.user['id'])
    return jsonify(orders), 200

@bp.route('/<order_id>', methods=['GET'])
@login_required
def get_one(order_id):
    """Obtiene una orden específica si el usuario es parte de ella."""
    try:
        order = order_service.get_order_by_id(order_id, g.user['id'])
        if not order: return jsonify({"error": "Orden no encontrada"}), 404
        return jsonify(order), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

@bp.route('/<order_id>', methods=['PUT'])
@login_required
def update(order_id):
    """Actualiza el estado de una orden (ej. a 'completada'). Solo el vendedor."""
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Falta el campo 'status'"}), 400
    try:
        updated_order = order_service.update_order_status(order_id, data['status'], g.user['id'])
        return jsonify(updated_order), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403

@bp.route('/<order_id>', methods=['DELETE'])
@login_required
def delete(order_id):
    """Elimina (desactiva) una orden. El comprador o vendedor pueden hacerlo."""
    try:
        result = order_service.soft_delete_order(order_id, g.user['id'])
        return jsonify(result), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403