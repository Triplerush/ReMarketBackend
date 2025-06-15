# app/services/transaction_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

@firestore.transactional
def create_transaction_atomic(transaction, data, buyer_id):
    """
    Función transaccional que crea la transacción y actualiza el producto de forma atómica.
    """
    product_id = data['productId']
    product_ref = db.collection('products').document(product_id)
    product_doc = product_ref.get(transaction=transaction)

    if not product_doc.exists:
        raise ValueError("El producto no existe.")
    
    product_data = product_doc.to_dict()

    # Validaciones adicionales dentro de la transacción para máxima seguridad
    if product_data.get('sellerId') == buyer_id:
        raise PermissionError("No puedes comprar tu propio producto.")
    
    if product_data.get('status') != 'approved':
        raise ValueError("Este producto no está disponible para la venta.")
    
    # Construir datos de la transacción
    transaction_data = {
        'productId': product_id,
        'buyerId': buyer_id,
        'sellerId': product_data['sellerId'],
        'status': 'reserved', # Toda nueva transacción empieza como 'reserved'
        'active': True,
        'timestamp': firestore.SERVER_TIMESTAMP
    }

    # Actualizar el estado del producto
    transaction.update(product_ref, {'status': 'reserved'})
    
    # Crear la nueva transacción
    new_transaction_ref = db.collection('transactions').document()
    transaction.set(new_transaction_ref, transaction_data)
    
    return new_transaction_ref.id


def create_transaction(data, buyer_id):
    """(CREATE) Orquesta la creación de una transacción."""
    transaction = db.transaction()
    new_transaction_id = create_transaction_atomic(transaction, data, buyer_id)
    
    # Devolvemos el documento completo para la respuesta
    new_doc = db.collection('transactions').document(new_transaction_id).get()
    return clean_firestore_doc(new_doc.to_dict())


def list_all_transactions():
    """(READ-LIST) ADMIN ONLY: Lista todas las transacciones."""
    query = db.collection('transactions').order_by('timestamp', direction=firestore.Query.DESCENDING)
    transactions = []
    for doc in query.stream():
        transaction_data = doc.to_dict()
        transaction_data['id'] = doc.id
        transactions.append(clean_firestore_doc(transaction_data))
    return transactions


def list_user_transactions(user_id):
    """(READ-LIST) Lista las transacciones donde un usuario es comprador o vendedor."""
    buyer_query = db.collection('transactions').where(filter=firestore.FieldFilter('buyerId', '==', user_id)).stream()
    seller_query = db.collection('transactions').where(filter=firestore.FieldFilter('sellerId', '==', user_id)).stream()
    
    transactions = {}
    for doc in buyer_query:
        transactions[doc.id] = clean_firestore_doc(doc.to_dict())

    for doc in seller_query:
        # Añadir solo si no existe para evitar duplicados
        if doc.id not in transactions:
            transactions[doc.id] = clean_firestore_doc(doc.to_dict())
            
    return list(transactions.values())


def get_transaction_by_id(transaction_id, user_id, user_role):
    """(READ-ID) Obtiene una transacción si el usuario es parte de ella o es admin."""
    doc = db.collection('transactions').document(transaction_id).get()
    
    if not doc.exists:
        return None
        
    transaction_data = doc.to_dict()
    
    # Lógica de Permisos
    is_participant = user_id in [transaction_data.get('buyerId'), transaction_data.get('sellerId')]
    if user_role != 'admin' and not is_participant:
        raise PermissionError("No tienes permiso para ver esta transacción.")
        
    transaction_data['id'] = doc.id
    return clean_firestore_doc(transaction_data)