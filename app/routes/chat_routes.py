# app/routes/chat_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import chat_service
from app.auth.decorators import login_required

bp = Blueprint('chats', __name__, url_prefix='/chats')

@bp.route('', methods=['POST'])
@login_required
def start_chat():
    """
    Endpoint para iniciar una nueva conversación o recuperar una existente.
    Recibe un 'productId' y utiliza el ID del usuario autenticado como 'buyerId'.
    """
    data = request.get_json()
    if not data or 'productId' not in data:
        return jsonify({"error": "Falta el campo requerido: 'productId'"}), 400

    try:
        product_id = data['productId']
        buyer_id = g.user['id']
        
        # El servicio se encarga de la lógica de crear o recuperar
        chat = chat_service.start_or_get_chat(product_id, buyer_id)
        
        # Si el chat es nuevo, se devuelve 201, si es existente, se puede debatir devolver 200, pero 201 es aceptable.
        return jsonify(chat), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 404 # Not Found, si el producto no existe
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403 # Forbidden, si intenta chatear consigo mismo
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500