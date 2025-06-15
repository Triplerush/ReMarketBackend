# app/routes/report_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import report_service
from app.auth.decorators import login_required

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('', methods=['GET'])
def get_all():
    """Obtiene una lista de todos los reportes. Puede filtrarse por producto (público)."""
    product_id = request.args.get('productId')
    try:
        reports = report_service.list_reports(product_id=product_id)
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<report_id>', methods=['GET'])
def get_one(report_id):
    """Obtiene un reporte específico por su ID (público)."""
    report = report_service.get_report_by_id(report_id)
    if not report:
        return jsonify({"error": "Reporte no encontrado"}), 404
    return jsonify(report), 200

@bp.route('', methods=['POST'])
@login_required
def create():
    """Crea un nuevo reporte."""
    if not g.user.get('approved'):
        return jsonify({"error": "Tu cuenta debe ser aprobada por un administrador para poder reportar."}), 403
    
    data = request.get_json()
    required = ['productId', 'reason']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Faltan campos requeridos: 'productId' y 'reason'"}), 400
    
    try:
        reporter_id = g.user['id']
        new_report = report_service.create_report(data, reporter_id)
        return jsonify(new_report), 201
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<report_id>', methods=['PUT'])
@login_required
def update(report_id):
    """Actualiza un reporte. Permisos validados en el servicio."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Cuerpo de la petición vacío"}), 400
        
    try:
        user_id = g.user['id']
        user_role = g.user['role']
        updated_report = report_service.update_report(report_id, data, user_id, user_role)
        return jsonify(updated_report), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@bp.route('/<report_id>', methods=['DELETE'])
@login_required
def delete(report_id):
    """Elimina un reporte. Permisos validados en el servicio."""
    try:
        user_id = g.user['id']
        user_role = g.user['role']
        result = report_service.delete_report(report_id, user_id, user_role)
        return jsonify(result), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500