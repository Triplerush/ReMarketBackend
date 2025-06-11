# app/services/publication_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

def create_publication(data, seller_id):
    publication_data = {
        'sellerId': seller_id, 'brand': data['brand'], 'model': data['model'],
        'capacity': data['capacity'], 'price': float(data['price']), 'imei': data['imei'],
        'description': data['description'], 'images(s)': data.get('images(s)', []),
        'category': data.get('category', 'smartphone'), 'urlVideo': data.get('urlVideo', ''),
        'box/cargador': data.get('box/cargador', 'No especificado'), 'invoice/uri': data.get('invoice/uri', ''),
        'status': 'disponible', 'createdAt': firestore.SERVER_TIMESTAMP,
        'updatedAt': firestore.SERVER_TIMESTAMP, 'active': True
    }
    update_time, pub_ref = db.collection('publicaciones').add(publication_data)
    created_doc = pub_ref.get()
    new_pub_data = created_doc.to_dict()
    new_pub_data['id'] = created_doc.id
    return clean_firestore_doc(new_pub_data)

def get_all_active_publications():
    query = db.collection('publicaciones')\
              .where(filter=firestore.FieldFilter('active', '==', True))\
              .where(filter=firestore.FieldFilter('status', '==', 'disponible'))
    publications = []
    for doc in query.stream():
        pub_data = doc.to_dict()
        pub_data['id'] = doc.id
        publications.append(clean_firestore_doc(pub_data))
    return publications

def get_publication_by_id(pub_id):
    doc = db.collection('publicaciones').document(pub_id).get()
    if not doc.exists or doc.to_dict().get('active') is False:
        return None
    pub_data = doc.to_dict()
    pub_data['id'] = doc.id
    return clean_firestore_doc(pub_data)

def update_publication(pub_id, data, user_id):
    pub_ref = db.collection('publicaciones').document(pub_id)
    doc = pub_ref.get()
    if not doc.exists: raise ValueError("Publicación no encontrada.")
    
    pub_data = doc.to_dict()
    if pub_data['sellerId'] != user_id:
        raise PermissionError("No tienes permiso para editar esta publicación.")
    
    allowed_fields = ['brand', 'model', 'capacity', 'price', 'description', 'images(s)', 'urlVideo', 'box/cargador']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    if not update_data:
        raise ValueError("No se proporcionaron campos válidos para actualizar.")
    update_data['updatedAt'] = firestore.SERVER_TIMESTAMP
    pub_ref.update(update_data)
    return get_publication_by_id(pub_id)

def soft_delete_publication(pub_id, user_id, user_role):
    pub_ref = db.collection('publicaciones').document(pub_id)
    doc = pub_ref.get()
    if not doc.exists: raise ValueError("Publicación no encontrada.")
    pub_data = doc.to_dict()
    if pub_data['sellerId'] != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para eliminar esta publicación.")
    pub_ref.update({'active': False, 'updatedAt': firestore.SERVER_TIMESTAMP})
    return {"id": pub_id, "message": "Publicación eliminada."}