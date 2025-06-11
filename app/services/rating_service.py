# app/services/rating_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

def create_rating(data, rater_id):
    """Crea una nueva calificación para una orden."""
    order_doc = db.collection('orders').document(data['orderId']).get()
    if not order_doc.exists:
        raise ValueError("La orden no existe.")
    
    order_data = order_doc.to_dict()
    if order_data.get('status') != 'reservada':
        raise PermissionError("Solo se pueden calificar órdenes completadas.")

    if rater_id not in [order_data['buyerId'], order_data['sellerId']]:
        raise PermissionError("No participaste en esta transacción.")

    # Verificar que no se haya calificado ya
    ratings_ref = db.collection('ratings')
    query = ratings_ref.where(filter=firestore.FieldFilter('orderId', '==', data['orderId']))\
                       .where(filter=firestore.FieldFilter('raterId', '==', rater_id))\
                       .limit(1).stream()
    if len(list(query)) > 0:
        raise PermissionError("Ya has calificado esta transacción.")

    rating_data = {
        'orderId': data['orderId'], 'sellerId': order_data['sellerId'],
        'buyerId': order_data['buyerId'], 'raterId': rater_id,
        'score': int(data['score']), 'comment': data['comment'],
        'createdAt': firestore.SERVER_TIMESTAMP, 'active': True
    }
    update_time, rating_ref = ratings_ref.add(rating_data)
    created_doc = rating_ref.get()
    new_rating_data = created_doc.to_dict()
    new_rating_data['id'] = created_doc.id
    return clean_firestore_doc(new_rating_data)

def list_ratings(user_id=None):
    """Lista calificaciones. Si se provee user_id, filtra por el usuario calificado."""
    query = db.collection('ratings').where(filter=firestore.FieldFilter('active', '==', True))
    if user_id:
        # rateeId es el usuario que recibe la calificación
        query = query.where(filter=firestore.FieldFilter('rateeId', '==', user_id))
    
    ratings = []
    for doc in query.stream():
        rating_data = doc.to_dict()
        rating_data['id'] = doc.id
        ratings.append(clean_firestore_doc(rating_data))
    return ratings

def get_rating_by_id(rating_id):
    """Obtiene una calificación por su ID."""
    doc = db.collection('ratings').document(rating_id).get()
    if not doc.exists or doc.to_dict().get('active') is False:
        return None
    rating_data = doc.to_dict()
    rating_data['id'] = doc.id
    return clean_firestore_doc(rating_data)

def update_rating(rating_id, data, user_id):
    """Actualiza el score o comentario de una calificación."""
    rating_ref = db.collection('ratings').document(rating_id)
    doc = rating_ref.get()
    if not doc.exists: raise ValueError("Calificación no encontrada.")
    
    rating_data = doc.to_dict()
    if rating_data['raterId'] != user_id:
        raise PermissionError("Solo puedes editar tus propias calificaciones.")

    update_data = {}
    if 'score' in data: update_data['score'] = int(data['score'])
    if 'comment' in data: update_data['comment'] = data['comment']
    if not update_data: raise ValueError("No se proporcionaron campos para actualizar.")

    rating_ref.update(update_data)
    return get_rating_by_id(rating_id)

def soft_delete_rating(rating_id, user_id, user_role):
    """Desactiva una calificación (soft delete)."""
    rating_ref = db.collection('ratings').document(rating_id)
    doc = rating_ref.get()
    if not doc.exists: raise ValueError("Calificación no encontrada.")

    rating_data = doc.to_dict()
    if rating_data['raterId'] != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para eliminar esta calificación.")
    
    rating_ref.update({'active': False})
    return {"id": rating_id, "message": "Calificación eliminada."}