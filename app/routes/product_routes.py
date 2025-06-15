# app/routes/product_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import product_service
from app.auth.decorators import login_required

bp = Blueprint('products', __name__, url_prefix='/products')

@bp.route('', methods=['GET'])
def get_all():
    """Obtiene una lista de todos los productos disponibles (público)."""
    try:
        products = product_service.list_all_products()
        return jsonify(products), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<product_id>', methods=['GET'])
def get_one(product_id):
    """Obtiene un producto específico por su ID (público)."""
    product = product_service.get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(product), 200

@bp.route('', methods=['POST'])
@login_required # Requiere que el usuario esté autenticado
def create():
    """Crea un nuevo producto. El 'sellerId' se toma del usuario autenticado."""
    
    # --- LÍNEA AÑADIDA ---
    # Verificamos si el usuario tiene el estado 'approved' en True.
    if not g.user.get('approved'):
        return jsonify({"error": "Tu cuenta debe ser aprobada por un administrador para poder crear productos."}), 403 # 403 Forbidden
    
    data = request.get_json()
    required = ['brand', 'model', 'storage', 'price', 'imei', 'description']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Faltan campos requeridos"}), 400
    
    try:
        seller_id = g.user['id']
        new_product = product_service.create_product(data, seller_id)
        return jsonify(new_product), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<product_id>', methods=['PUT'])
@login_required # Requiere que el usuario esté autenticado
def update(product_id):
    """Actualiza un producto. La validación de permisos se hace en el servicio."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Cuerpo de la petición vacío"}), 400
    
    try:
        user_id = g.user['id']
        user_role = g.user['role']
        updated_product = product_service.update_product(product_id, data, user_id, user_role)
        return jsonify(updated_product), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@bp.route('/<product_id>', methods=['DELETE'])
@login_required # Requiere que el usuario esté autenticado
def delete(product_id):
    """Elimina un producto. La validación de permisos se hace en el servicio."""
    try:
        user_id = g.user['id']
        user_role = g.user['role']
        result = product_service.delete_product(product_id, user_id, user_role)
        return jsonify(result), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500