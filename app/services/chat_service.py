# app/services/chat_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore
from . import product_service # Usaremos esto para obtener los datos del producto

def start_or_get_chat(product_id, buyer_id):
    """
    Inicia una nueva conversación o recupera una existente.
    Verifica si ya existe un chat entre este comprador y para este producto.
    Si no existe, lo crea.
    """
    # Validación 1: El producto debe existir
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise ValueError("El producto sobre el que intentas chatear no existe.")

    seller_id = product['sellerId']

    # Validación 2: El comprador no puede ser el vendedor
    if buyer_id == seller_id:
        raise PermissionError("No puedes iniciar un chat contigo mismo.")

    # Validación 3: Buscar si ya existe una conversación entre estos dos usuarios para este producto
    chat_query = db.collection('chats') \
                   .where(filter=firestore.FieldFilter('productId', '==', product_id)) \
                   .where(filter=firestore.FieldFilter('buyerId', '==', buyer_id)) \
                   .limit(1).stream()
    
    existing_chat = list(chat_query)

    if existing_chat:
        # Si el chat ya existe, simplemente devolvemos sus datos
        chat_data = existing_chat[0].to_dict()
        chat_data['id'] = existing_chat[0].id
        return clean_firestore_doc(chat_data)
    else:
        # Si no existe, creamos un nuevo documento de chat
        chat_data = {
            'productId': product_id,
            'productTitle': f"{product.get('brand', '')} {product.get('model', '')}".strip(),
            'productImageUrl': product.get('imageUrls', [''])[0] if product.get('imageUrls') else '',
            'productPrice': product.get('price', 0),
            'participantIds': [seller_id, buyer_id],
            'sellerId': seller_id,
            'buyerId': buyer_id,
            'lastMessage': 'Conversación iniciada.',
            'lastMessageTimestamp': firestore.SERVER_TIMESTAMP,
            'createdAt': firestore.SERVER_TIMESTAMP
        }
        
        update_time, chat_ref = db.collection('chats').add(chat_data)
        created_doc = chat_ref.get()
        new_chat_data = created_doc.to_dict()
        new_chat_data['id'] = created_doc.id
        return clean_firestore_doc(new_chat_data)