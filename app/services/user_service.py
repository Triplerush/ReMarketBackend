# app/services/user_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore, auth

def create_user(data, uid):
    """
    (CREATE) Crea un documento de usuario en Firestore que coincide exactamente
    con el esquema de la colección 'users' proporcionado.
    """
    user_doc_ref = db.collection('users').document(uid)

    if user_doc_ref.get().exists:
        raise ValueError("El documento de usuario para este UID ya existe.")

    user_data = {
        'firstName': data['firstName'],
        'lastName': data['lastName'],
        'dniNumber': data['dniNumber'],
        'email': data['email'],
        'dniFrontUrl': data.get('dniFrontUrl', ''),
        'dniBackUrl': data.get('dniBackUrl', ''),
        'approved': False,
        'role': 'user',
        'active': True,
        'createdAt': firestore.SERVER_TIMESTAMP,
        'updatedAt': firestore.SERVER_TIMESTAMP
    }
    
    user_doc_ref.set(user_data)
    
    created_doc = user_doc_ref.get()
    new_user_data = created_doc.to_dict()
    new_user_data['id'] = created_doc.id
    
    return clean_firestore_doc(new_user_data)

def get_user_by_id(user_id):
    """(READ-ID) Obtiene un usuario activo por su ID."""
    doc_ref = db.collection('users').document(user_id)
    doc = doc_ref.get()
    
    if not doc.exists or doc.to_dict().get('active') is False:
        return None
    
    user_data = doc.to_dict()
    user_data['id'] = doc.id
    return clean_firestore_doc(user_data)

def get_all_users():
    """(READ-LIST) Obtiene una lista de todos los usuarios activos."""
    users_ref = db.collection('users').where(filter=firestore.FieldFilter('active', '==', True))
    users = []
    for doc in users_ref.stream():
        user_data = doc.to_dict()
        user_data['id'] = doc.id
        users.append(clean_firestore_doc(user_data))
    return users

def update_user(user_id, data, current_user_id, current_user_role):
    """(UPDATE) Actualiza los datos de un usuario con validación de permisos."""
    user_ref = db.collection('users').document(user_id)
    if not user_ref.get().exists:
        raise ValueError("Usuario no encontrado.")

    # Lógica de Permisos Clave
    if user_id != current_user_id and current_user_role != 'admin':
        raise PermissionError("No tienes permiso para actualizar este usuario.")
    
    allowed_fields = ['firstName', 'lastName', 'dniFrontUrl', 'dniBackUrl']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if current_user_role == 'admin':
        admin_fields = ['approved', 'role', 'active']
        admin_update_data = {k: v for k, v in data.items() if k in admin_fields}
        update_data.update(admin_update_data)

    if not update_data:
        raise ValueError("No se proporcionaron campos válidos para actualizar.")

    update_data['updatedAt'] = firestore.SERVER_TIMESTAMP
    
    user_ref.update(update_data)
    return get_user_by_id(user_id)

def soft_delete_user(user_id, current_user_id, current_user_role):
    """(DELETE) Desactiva un usuario con validación de permisos."""
    # Lógica de Permisos Clave
    if user_id != current_user_id and current_user_role != 'admin':
        raise PermissionError("No tienes permiso para eliminar este usuario.")
        
    user_ref = db.collection('users').document(user_id)
    if not user_ref.get().exists:
        raise ValueError("Usuario no encontrado.")

    user_ref.update({'active': False, 'updatedAt': firestore.SERVER_TIMESTAMP})

    try:
        auth.update_user(user_id, disabled=True)
    except Exception as e:
        print(f"Advertencia: No se pudo desactivar el usuario {user_id} en Firebase Auth: {e}")

    return {"id": user_id, "message": "Usuario desactivado exitosamente."}
