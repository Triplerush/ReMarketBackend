# app/services/order_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

def create_order(data, buyer_id):
    pub_ref = db.collection('publicaciones').document(data['pubId'])
    pub_doc = pub_ref.get()
    if not pub_doc.exists or pub_doc.to_dict().get('active') is False:
        raise ValueError("La publicación no existe o no está activa.")
    pub_data = pub_doc.to_dict()
    if pub_data['status'] != 'disponible':
        raise PermissionError("Esta publicación no está disponible para la venta.")
    order_data = {
        'pubId': data['pubId'], 'buyerId': buyer_id, 'sellerId': pub_data['sellerId'],
        'price': pub_data['price'], 'status': 'reservada', 'paymentMethod': data['paymentMethod'],
        'createdAt': firestore.SERVER_TIMESTAMP, 'updatedAt': firestore.SERVER_TIMESTAMP, 'active': True
    }
    transaction = db.transaction()
    @firestore.transactional
    def update_in_transaction(trans, pub_ref, order_data):
        trans.update(pub_ref, {'status': 'vendida', 'updatedAt': firestore.SERVER_TIMESTAMP})
        order_ref = db.collection('orders').document()
        trans.set(order_ref, order_data)
        return order_ref
    order_ref = update_in_transaction(transaction, pub_ref, order_data)
    return get_order_by_id(order_ref.id, buyer_id)

def get_order_by_id(order_id, user_id):
    doc = db.collection('orders').document(order_id).get()
    if not doc.exists: return None
    order_data = doc.to_dict()
    if user_id not in [order_data['buyerId'], order_data['sellerId']]:
        raise PermissionError("No tienes permiso para ver esta orden.")
    order_data['id'] = doc.id
    return clean_firestore_doc(order_data)

def list_user_orders(user_id):
    buyer_orders_query = db.collection('orders').where(filter=firestore.FieldFilter('buyerId', '==', user_id)).stream()
    seller_orders_query = db.collection('orders').where(filter=firestore.FieldFilter('sellerId', '==', user_id)).stream()
    orders = []
    for doc in buyer_orders_query:
        order_data = doc.to_dict()
        order_data['id'] = doc.id
        orders.append(clean_firestore_doc(order_data))
    for doc in seller_orders_query:
        order_data = doc.to_dict()
        order_data['id'] = doc.id
        if not any(o['id'] == doc.id for o in orders):
            orders.append(clean_firestore_doc(order_data))
    return orders

def update_order_status(order_id, new_status, user_id):
    order_ref = db.collection('orders').document(order_id)
    doc = order_ref.get()
    if not doc.exists: raise ValueError("Orden no encontrada.")
    order_data = doc.to_dict()
    if user_id != order_data['sellerId']:
        raise PermissionError("Solo el vendedor puede actualizar el estado de la orden.")
    valid_statuses = ['completada', 'cancelada']
    if new_status not in valid_statuses:
        raise ValueError("Estado no válido.")
    
    update_data = {'status': new_status, 'updatedAt': firestore.SERVER_TIMESTAMP}
    order_ref.update(update_data)

    if new_status == 'cancelada':
        pub_ref = db.collection('publicaciones').document(order_data['pubId'])
        pub_ref.update({'status': 'disponible', 'updatedAt': firestore.SERVER_TIMESTAMP})

    return get_order_by_id(order_id, user_id)

# Añade esta función al final de app/services/order_service.py

def soft_delete_order(order_id, user_id):
    """Desactiva una orden (soft delete), solo por el comprador o vendedor."""
    order_ref = db.collection('orders').document(order_id)
    doc = order_ref.get()
    if not doc.exists: raise ValueError("Orden no encontrada.")
    
    order_data = doc.to_dict()
    if user_id not in [order_data['buyerId'], order_data['sellerId']]:
        raise PermissionError("No tienes permiso para eliminar esta orden.")
    
    # Se podría añadir lógica para revertir el estado de la publicación si se cancela
    # if order_data['status'] == 'reservada':
    #     pub_ref = db.collection('publicaciones').document(order_data['pubId'])
    #     pub_ref.update({'status': 'disponible'})

    order_ref.update({'active': False, 'updatedAt': firestore.SERVER_TIMESTAMP})
    return {"id": order_id, "message": "Orden eliminada."}