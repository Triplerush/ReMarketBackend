# app/routes/report_routes.py
from flask import Blueprint, request, jsonify, g
from app.services import report_service
from app.auth.decorators import login_required, admin_required

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('', methods=['POST'])
@login_required
def create():
    data = request.get_json()
    if not data or not all(k in data for k in ['pubId', 'reason']):
        return jsonify({"error": "Faltan campos: 'pubId' y 'reason'"}), 400
    try:
        new_report = report_service.create_report(data, g.user['id'])
        return jsonify(new_report), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@bp.route('', methods=['GET'])
@admin_required
def get_all():
    status = request.args.get('status')
    reports = report_service.list_reports(status=status)
    return jsonify(reports), 200

@bp.route('/<report_id>', methods=['GET'])
@admin_required
def get_one(report_id):
    report = report_service.get_report_by_id(report_id)
    if not report: return jsonify({"error": "Reporte no encontrado"}), 404
    return jsonify(report), 200

@bp.route('/<report_id>', methods=['PUT'])
@admin_required
def update(report_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Falta el campo 'status'"}), 400
    try:
        updated_report = report_service.update_report_status(report_id, data['status'])
        return jsonify(updated_report), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<report_id>', methods=['DELETE'])
@admin_required
def delete(report_id):
    try:
        result = report_service.soft_delete_report(report_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404