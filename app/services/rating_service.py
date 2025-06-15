# app/services/rating_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

def create_rating(data, buyer_id):
    """(CREATE) Crea una nueva calificación para un producto."""
    product_id = data['productId']
    
    # Validación 1: El producto debe existir.
    product_ref = db.collection('products').document(product_id)
    product_doc = product_ref.get()
    if not product_doc.exists:
        raise ValueError("El producto que intentas calificar no existe.")
    
    # Validación 2: Un usuario solo puede calificar un producto una vez.
    ratings_query = db.collection('ratings') \
                      .where(filter=firestore.FieldFilter('productId', '==', product_id)) \
                      .where(filter=firestore.FieldFilter('buyerId', '==', buyer_id)) \
                      .limit(1).stream()
    
    if len(list(ratings_query)) > 0:
        raise ValueError("Ya has enviado una calificación para este producto.")

    # Construimos el diccionario de la calificación
    seller_id = product_doc.to_dict().get('sellerId')
    rating_data = {
        'productId': product_id,
        'buyerId': buyer_id,
        'sellerId': seller_id,
        'score': int(data['score']),
        'comment': data.get('comment', ''),
        'active': True,
        'createdAt': firestore.SERVER_TIMESTAMP
    }
    
    update_time, rating_ref = db.collection('ratings').add(rating_data)
    created_doc = rating_ref.get()
    
    new_rating_data = created_doc.to_dict()
    new_rating_data['id'] = created_doc.id
    return clean_firestore_doc(new_rating_data)

def list_ratings(product_id=None):
    """(READ-LIST) Lista calificaciones. Opcionalmente filtra por producto."""
    query = db.collection('ratings').where(filter=firestore.FieldFilter('active', '==', True))
    
    if product_id:
        query = query.where(filter=firestore.FieldFilter('productId', '==', product_id))
        
    ratings = []
    for doc in query.stream():
        rating_data = doc.to_dict()
        rating_data['id'] = doc.id
        ratings.append(clean_firestore_doc(rating_data))
    return ratings

def get_rating_by_id(rating_id):
    """(READ-ID) Obtiene una calificación por su ID."""
    doc = db.collection('ratings').document(rating_id).get()
    
    if not doc.exists or doc.to_dict().get('active') is False:
        return None
        
    rating_data = doc.to_dict()
    rating_data['id'] = doc.id
    return clean_firestore_doc(rating_data)

def update_rating(rating_id, data, user_id, user_role):
    """(UPDATE) Actualiza una calificación. Solo el autor o un admin."""
    rating_ref = db.collection('ratings').document(rating_id)
    doc = rating_ref.get()
    
    if not doc.exists:
        raise ValueError("Calificación no encontrada.")
    
    rating_data = doc.to_dict()
    
    # Lógica de Permisos: Solo el autor de la calificación o un admin pueden editar.
    if rating_data['buyerId'] != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para editar esta calificación.")
        
    allowed_fields = ['score', 'comment']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if 'score' in update_data:
        update_data['score'] = int(update_data['score'])

    if not update_data:
        raise ValueError("No se proporcionaron campos válidos para actualizar.")

    rating_ref.update(update_data)
    return get_rating_by_id(rating_id)

def delete_rating(rating_id, user_id, user_role):
    """(DELETE) Desactiva una calificación. Solo el autor o un admin."""
    rating_ref = db.collection('ratings').document(rating_id)
    doc = rating_ref.get()
    
    if not doc.exists:
        raise ValueError("Calificación no encontrada.")
        
    rating_data = doc.to_dict()
    
    # Lógica de Permisos: Solo el autor de la calificación o un admin pueden eliminar.
    if rating_data['buyerId'] != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para eliminar esta calificación.")
        
    rating_ref.update({'active': False})
    
    return {"id": rating_id, "message": "Calificación eliminada exitosamente."}