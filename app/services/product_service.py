# app/services/product_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

def create_product(data, seller_id):
    """(CREATE) Crea un nuevo documento de producto en la colección 'products'."""
    
    # Construimos el diccionario del producto respetando el esquema
    product_data = {
        'sellerId': seller_id,
        'brand': data['brand'],
        'model': data['model'],
        'storage': data['storage'],
        'price': float(data['price']),
        'imei': data['imei'],
        'description': data['description'],
        
        # Campos opcionales o con valores por defecto
        'imageUrls': data.get('imageUrls', []),
        'boxImageUrl': data.get('boxImageUrl', ''),
        'invoiceUrl': data.get('invoiceUrl', ''),
        
        # Estado inicial 'pending' para que un admin lo apruebe, como en tu propuesta
        'status': 'pending',
        'active': True,
        
        # Timestamps
        'createdAt': firestore.SERVER_TIMESTAMP,
        'updatedAt': firestore.SERVER_TIMESTAMP
    }
    
    update_time, product_ref = db.collection('products').add(product_data)
    created_doc = product_ref.get()
    
    new_product_data = created_doc.to_dict()
    new_product_data['id'] = created_doc.id
    return clean_firestore_doc(new_product_data)

def list_all_products():
    """(READ-LIST) Obtiene una lista de todos los productos activos y aprobados."""
    query = db.collection('products') \
              .where(filter=firestore.FieldFilter('active', '==', True)) \
              .where(filter=firestore.FieldFilter('status', '==', 'approved'))
              
    products = []
    for doc in query.stream():
        product_data = doc.to_dict()
        product_data['id'] = doc.id
        products.append(clean_firestore_doc(product_data))
    return products

def list_user_products(user_id: str):
    """
    (READ-LIST) Devuelve productos donde el usuario es comprador
    y el estado está en 'reserved' o 'sold'.
    """
    query = db.collection('products') \
              .where(filter=firestore.FieldFilter('buyerId', '==', user_id)) \
              .where(filter=firestore.FieldFilter('status', 'in', ['reserved', 'sold']))

    products = []
    for doc in query.stream():
        data = doc.to_dict()
        data['id'] = doc.id
        products.append(clean_firestore_doc(data))
    return products

def list_products_by_seller(seller_id):
    """(READ-LIST) Obtiene los productos activos de un vendedor específico."""
    query = db.collection('products') \
              .where(filter=firestore.FieldFilter('sellerId', '==', seller_id)) \
              .where(filter=firestore.FieldFilter('active', '==', True)) \
              .where(filter=firestore.FieldFilter('status', '==', 'approved'))
    products = []
    for doc in query.stream():
        data = doc.to_dict()
        data['id'] = doc.id
        products.append(clean_firestore_doc(data))
    return products 

def get_product_by_id(product_id):
    """(READ-ID) Obtiene un producto por su ID."""
    doc = db.collection('products').document(product_id).get()
    
    if not doc.exists or doc.to_dict().get('active') is False:
        return None
        
    product_data = doc.to_dict()
    product_data['id'] = doc.id
    return clean_firestore_doc(product_data)

def update_product(product_id, data, user_id, user_role):
    """(UPDATE) Actualiza los datos de un producto con validación de permisos."""
    product_ref = db.collection('products').document(product_id)
    doc = product_ref.get()
    
    if not doc.exists:
        raise ValueError("Producto no encontrado.")
    
    product_data = doc.to_dict()
    
    # Lógica de Permisos: Solo el dueño del producto o un admin pueden editar.
    if product_data['sellerId'] != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para editar este producto.")
        
    # Definimos qué campos se pueden actualizar
    allowed_fields = ['brand', 'model', 'storage', 'price', 'description', 'imageUrls', 'boxImageUrl', 'invoiceUrl']
    # Un admin podría adicionalmente cambiar el 'status' (ej. 'approved', 'rejected')
    if user_role == 'admin':
        allowed_fields.append('status')
        
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        raise ValueError("No se proporcionaron campos válidos para actualizar.")

    update_data['updatedAt'] = firestore.SERVER_TIMESTAMP
    product_ref.update(update_data)
    
    return get_product_by_id(product_id)

def delete_product(product_id, user_id, user_role):
    """(DELETE) Desactiva un producto (soft delete) con validación de permisos."""
    product_ref = db.collection('products').document(product_id)
    doc = product_ref.get()
    
    if not doc.exists:
        raise ValueError("Producto no encontrado.")
        
    product_data = doc.to_dict()
    
    # Lógica de Permisos: Solo el dueño del producto o un admin pueden eliminar.
    if product_data['sellerId'] != user_id and user_role != 'admin':
        raise PermissionError("No tienes permiso para eliminar este producto.")
        
    product_ref.update({'active': False, 'updatedAt': firestore.SERVER_TIMESTAMP})
    
    return {"id": product_id, "message": "Producto eliminado exitosamente."}

def purchase_product(product_id: str, seller_id: str, is_admin: bool = False):
    """
    Marca la compra del producto tanto en la colección de transacciones
    como en el documento del producto.
    Solo puede hacerlo:
      - el vendedor (sellerId)
      - o un admin (is_admin=True)
    Cambia status→'sold' en ambos lugares.
    """
    # 1) Obtener el producto
    prod_ref = db.collection('products').document(product_id)
    prod_snap = prod_ref.get()
    if not prod_snap.exists:
        raise ValueError("Producto no encontrado")

    prod = prod_snap.to_dict()
    # 2) Autorizar
    if not is_admin and prod.get('sellerId') != seller_id:
        raise PermissionError("Solo el vendedor o un admin pueden completar la venta")

    # 3) Actualizar el producto
    prod_ref.update({
        'status': 'sold',
        'soldAt': firestore.SERVER_TIMESTAMP
    })

    # 4) Actualizar la transacción
    #    Asumimos que la transacción tiene ID = product_id en la colección 'transactions'
    tx_ref = db.collection('transactions').document(product_id)
    tx_snap = tx_ref.get()
    if tx_snap.exists:
        tx_ref.update({
            'status': 'completed',
            'completedAt': firestore.SERVER_TIMESTAMP
        })
    else:
        # Si no hay transacción previa, la creamos
        tx_ref.set({
            'productId': product_id,
            'buyerId': prod.get('buyerId'),
            'sellerId': prod.get('sellerId'),
            'status': 'completed',
            'createdAt': firestore.SERVER_TIMESTAMP,
            'completedAt': firestore.SERVER_TIMESTAMP
        })

    # 5) Devolver el producto actualizado
    updated = prod_ref.get().to_dict()
    updated['id'] = prod_ref.id
    return clean_firestore_doc(updated)