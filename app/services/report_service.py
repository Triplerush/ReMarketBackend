# app/services/report_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

def create_report(data, reporter_id):
    """Crea un nuevo reporte para una publicación."""
    pub_doc = db.collection('publicaciones').document(data['pubId']).get()
    if not pub_doc.exists:
        raise ValueError("La publicación que intentas reportar no existe.")
    report_data = {
        'pubId': data['pubId'], 'reporterId': reporter_id,
        'reason': data['reason'], 'status': 'pendiente',
        'createdAt': firestore.SERVER_TIMESTAMP, 'active': True
    }
    update_time, report_ref = db.collection('reportes').add(report_data)
    created_doc = report_ref.get()
    new_report_data = created_doc.to_dict()
    new_report_data['id'] = created_doc.id
    return clean_firestore_doc(new_report_data)

def list_reports(status=None):
    """Lista todos los reportes, opcionalmente filtrados por status."""
    query = db.collection('reportes').where(filter=firestore.FieldFilter('active', '==', True))
    if status:
        query = query.where(filter=firestore.FieldFilter('status', '==', status))
    
    reports = []
    for doc in query.stream():
        report_data = doc.to_dict()
        report_data['id'] = doc.id
        reports.append(clean_firestore_doc(report_data))
    return reports

def get_report_by_id(report_id):
    """Obtiene un reporte por su ID."""
    doc = db.collection('reportes').document(report_id).get()
    if not doc.exists or doc.to_dict().get('active') is False:
        return None
    report_data = doc.to_dict()
    report_data['id'] = doc.id
    return clean_firestore_doc(report_data)

def update_report_status(report_id, new_status):
    """Actualiza el estado de un reporte (admin only)."""
    report_ref = db.collection('reportes').document(report_id)
    if not report_ref.get().exists:
        raise ValueError("Reporte no encontrado.")
    
    valid_statuses = ['en-revision', 'resuelto', 'desestimado']
    if new_status not in valid_statuses:
        raise ValueError("Estado no válido.")

    report_ref.update({'status': new_status})
    return get_report_by_id(report_id)

def soft_delete_report(report_id):
    """Desactiva un reporte (admin only)."""
    report_ref = db.collection('reportes').document(report_id)
    if not report_ref.get().exists:
        raise ValueError("Reporte no encontrado.")
    report_ref.update({'active': False})
    return {"id": report_id, "message": "Reporte eliminado."}