# app/services/report_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

def create_report(data, reporter_id):
    """(CREATE) Crea un nuevo reporte para un producto, con validaciones."""
    product_id = data['productId']

    # Validación 1: El producto debe existir.
    product_ref = db.collection('products').document(product_id)
    product_doc = product_ref.get()
    if not product_doc.exists:
        raise ValueError("El producto que intentas reportar no existe.")
    
    # Validación 2: El usuario no puede reportar su propio producto.
    product_data = product_doc.to_dict()
    if product_data.get('sellerId') == reporter_id:
        raise PermissionError("No puedes reportar tus propios productos.")

    # Validación 3: Un usuario solo puede reportar un producto una vez.
    report_query = db.collection('reports') \
                     .where(filter=firestore.FieldFilter('productId', '==', product_id)) \
                     .where(filter=firestore.FieldFilter('reporterId', '==', reporter_id)) \
                     .limit(1).stream()
    
    if len(list(report_query)) > 0:
        raise ValueError("Ya has enviado un reporte para este producto.")

    # Construimos el diccionario del reporte
    report_data = {
        'productId': product_id,
        'reporterId': reporter_id,
        'reason': data['reason'],
        'active': True,
        'createdAt': firestore.SERVER_TIMESTAMP
    }
    
    update_time, report_ref = db.collection('reports').add(report_data)
    created_doc = report_ref.get()
    
    new_report_data = created_doc.to_dict()
    new_report_data['id'] = created_doc.id
    return clean_firestore_doc(new_report_data)

def list_reports(product_id=None):
    """(READ-LIST) Lista todos los reportes activos. Opcionalmente filtra por producto."""
    query = db.collection('reports').where(filter=firestore.FieldFilter('active', '==', True))

    # Si se provee un product_id, se añade el filtro a la consulta.
    if product_id:
        query = query.where(filter=firestore.FieldFilter('productId', '==', product_id))
        
    reports = []
    for doc in query.stream():
        report_data = doc.to_dict()
        report_data['id'] = doc.id
        reports.append(clean_firestore_doc(report_data))
    return reports

def get_report_by_id(report_id):
    """(READ-ID) Obtiene un reporte por su ID."""
    doc = db.collection('reports').document(report_id).get()
    
    if not doc.exists or doc.to_dict().get('active') is False:
        return None
        
    report_data = doc.to_dict()
    report_data['id'] = doc.id
    return clean_firestore_doc(report_data)

def update_report(report_id, data, user_id, user_role):
    """(UPDATE) Actualiza el motivo de un reporte. Solo el autor o un admin."""
    report_ref = db.collection('reports').document(report_id)
    doc = report_ref.get()
    
    if not doc.exists:
        raise ValueError("Reporte no encontrado.")
    
    report_data = doc.to_dict()
    
    if report_data['reporterId'] != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para editar este reporte.")
        
    if 'reason' not in data:
        raise ValueError("Falta el campo 'reason' para actualizar.")

    report_ref.update({'reason': data['reason']})
    return get_report_by_id(report_id)

def delete_report(report_id, user_id, user_role):
    """(DELETE) Desactiva un reporte. Solo el autor o un admin."""
    report_ref = db.collection('reports').document(report_id)
    doc = report_ref.get()
    
    if not doc.exists:
        raise ValueError("Reporte no encontrado.")
        
    report_data = doc.to_dict()
    
    if report_data['reporterId'] != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para eliminar este reporte.")
        
    report_ref.update({'active': False})
    return {"id": report_id, "message": "Reporte eliminado exitosamente."}