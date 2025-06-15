# app/services/saved_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

def create_saved_item(data, user_id):
    """(CREATE) Guarda un producto para un usuario."""
    product_id = data['productId']
    
    # Validación 1: El producto debe existir.
    product_ref = db.collection('products').document(product_id)
    if not product_ref.get().exists:
        raise ValueError("El producto que intentas guardar no existe.")
        
    # Validación 2: Prevenir duplicados.
    # Buscamos si ya existe una entrada, sin importar si está activa o no.
    saved_query = db.collection('saved') \
                    .where(filter=firestore.FieldFilter('userId', '==', user_id)) \
                    .where(filter=firestore.FieldFilter('productId', '==', product_id)) \
                    .limit(1).stream()
    
    existing_saved = list(saved_query)
    
    if existing_saved:
        existing_doc_ref = existing_saved[0].reference
        existing_data = existing_saved[0].to_dict()
        # Si ya está guardado y activo, no hacemos nada.
        if existing_data.get('active'):
            raise ValueError("Este producto ya está en tu lista de guardados.")
        # Si existía pero fue eliminado (active: false), lo reactivamos.
        else:
            existing_doc_ref.update({'active': True, 'createdAt': firestore.SERVER_TIMESTAMP})
            updated_doc = existing_doc_ref.get()
            return clean_firestore_doc(updated_doc.to_dict())

    # Si no existe, creamos una nueva entrada.
    saved_data = {
        'userId': user_id,
        'productId': product_id,
        'active': True,
        'createdAt': firestore.SERVER_TIMESTAMP
    }
    
    update_time, saved_ref = db.collection('saved').add(saved_data)
    created_doc = saved_ref.get()
    
    new_saved_data = created_doc.to_dict()
    new_saved_data['id'] = created_doc.id
    return clean_firestore_doc(new_saved_data)

def list_all_saved_items():
    """(READ-LIST) ADMIN ONLY: Lista todos los elementos guardados."""
    query = db.collection('saved').order_by('createdAt', direction=firestore.Query.DESCENDING)
    saved_items = []
    for doc in query.stream():
        item_data = doc.to_dict()
        item_data['id'] = doc.id
        saved_items.append(clean_firestore_doc(item_data))
    return saved_items

def list_user_saved_items(user_id):
    """(READ-LIST) Lista los elementos guardados activos para un usuario específico."""
    query = db.collection('saved') \
              .where(filter=firestore.FieldFilter('userId', '==', user_id)) \
              .where(filter=firestore.FieldFilter('active', '==', True))
              
    saved_items = []
    for doc in query.stream():
        item_data = doc.to_dict()
        item_data['id'] = doc.id
        saved_items.append(clean_firestore_doc(item_data))
    return saved_items

def get_saved_item_by_id(saved_id, user_id, user_role):
    """(READ-ID) Obtiene un elemento guardado si el usuario es el dueño o es admin."""
    doc = db.collection('saved').document(saved_id).get()
    
    if not doc.exists:
        return None
        
    item_data = doc.to_dict()
    
    if item_data.get('userId') != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para ver este elemento.")
        
    item_data['id'] = doc.id
    return clean_firestore_doc(item_data)

def delete_saved_item(saved_id, user_id, user_role):
    """(DELETE) Desactiva un elemento guardado (soft delete)."""
    saved_ref = db.collection('saved').document(saved_id)
    doc = saved_ref.get()
    
    if not doc.exists:
        raise ValueError("El elemento guardado no fue encontrado.")
        
    item_data = doc.to_dict()
    
    if item_data.get('userId') != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para eliminar este elemento.")
        
    saved_ref.update({'active': False})
    return {"id": saved_id, "message": "Elemento eliminado de tu lista de guardados."}