# app/routes/transaction_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import transaction_service
from app.auth.decorators import login_required, admin_required

bp = Blueprint('transactions', __name__, url_prefix='/transactions')

@bp.route('', methods=['GET'])
@login_required
def get_transactions():
    """
    Lista transacciones.
    - Si es admin, lista todas.
    - Si es usuario, lista solo aquellas en las que participa.
    """
    try:
        if g.user['role'] == 'admin':
            transactions = transaction_service.list_all_transactions()
        else:
            transactions = transaction_service.list_user_transactions(g.user['id'])
        return jsonify(transactions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/<transaction_id>', methods=['GET'])
@login_required
def get_one(transaction_id):
    """Obtiene una transacción específica si el usuario es parte de ella o admin."""
    try:
        transaction = transaction_service.get_transaction_by_id(transaction_id, g.user['id'], g.user['role'])
        if not transaction:
            return jsonify({"error": "Transacción no encontrada"}), 404
        return jsonify(transaction), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('', methods=['POST'])
@login_required
def create():
    """Crea una nueva transacción (reserva un producto)."""
    if not g.user.get('approved'):
        return jsonify({"error": "Tu cuenta debe ser aprobada para realizar esta acción."}), 403

    data = request.get_json()
    if not data or 'productId' not in data:
        return jsonify({"error": "Falta el campo requerido: 'productId'"}), 400
    
    try:
        buyer_id = g.user['id']
        new_transaction = transaction_service.create_transaction(data, buyer_id)
        return jsonify(new_transaction), 201
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 409 # 409 Conflict o 403 Forbidden
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# NOTA: No se implementan rutas PUT o DELETE para usuarios regulares,
# ya que has especificado que no pueden modificar ni borrar transacciones.
# Se podrían añadir rutas adicionales protegidas con @admin_required si fuera necesario.