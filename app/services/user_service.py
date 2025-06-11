# app/services/user_service.py
from app import db
from app.utils import clean_firestore_doc
from firebase_admin import firestore

def create_user(data):
    """(CREATE) Crea un nuevo usuario en la colección 'users'."""
    users_ref = db.collection('users')
    query = users_ref.where(filter=firestore.FieldFilter('email', '==', data['email'])).limit(1).stream()
    if len(list(query)) > 0:
        raise ValueError("El correo electrónico ya está en uso.")

    user_data = {
        'firstName': data['firstName'],
        'lastName': data['lastName'],
        'dni': data['dni'],
        'tel/movil': data['tel/movil'],
        'dir/domicilio': data['dir/domicilio'],
        'selfie/uri': data.get('selfie/uri', ''),
        'email': data['email'],
        'approved': False,
        'role': data.get('role', 'buyer'),
        'createdAt': firestore.SERVER_TIMESTAMP,
        'active': True
    }
    
    update_time, user_ref = users_ref.add(user_data)
    created_doc = user_ref.get()
    
    new_user_data = created_doc.to_dict()
    new_user_data['id'] = created_doc.id
    
    return clean_firestore_doc(new_user_data)

def get_all_users():
    """(READ-LIST) Obtiene una lista de todos los usuarios activos."""
    users_ref = db.collection('users').where(filter=firestore.FieldFilter('active', '==', True))
    users = []
    for doc in users_ref.stream():
        user_data = doc.to_dict()
        user_data['id'] = doc.id
        users.append(clean_firestore_doc(user_data))
    return users

def get_user_by_id(user_id):
    """(READ-ID) Obtiene un usuario activo por su ID."""
    doc = db.collection('users').document(user_id).get()
    if not doc.exists or doc.to_dict().get('active') is False:
        return None
    
    user_data = doc.to_dict()
    user_data['id'] = doc.id
    return clean_firestore_doc(user_data)

def update_user(user_id, data, current_user_id, current_user_role):
    """(UPDATE) Actualiza los datos de un usuario."""
    user_ref = db.collection('users').document(user_id)
    if not user_ref.get().exists:
        raise ValueError("Usuario no encontrado.")

    # Lógica de Permisos: Un usuario solo puede actualizarse a sí mismo, a menos que sea admin.
    if user_id != current_user_id and current_user_role != 'admin':
        raise PermissionError("No tienes permiso para actualizar este usuario.")
    
    # Campos que un usuario normal puede actualizar de su propio perfil
    allowed_fields = ['firstName', 'lastName', 'tel/movil', 'dir/domicilio', 'selfie/uri']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    # Campos que solo un administrador puede modificar
    if current_user_role == 'admin':
        admin_fields = ['approved', 'role', 'active']
        admin_update_data = {k: v for k, v in data.items() if k in admin_fields}
        update_data.update(admin_update_data)

    if not update_data:
        raise ValueError("No se proporcionaron campos válidos para actualizar.")

    user_ref.update(update_data)
    # Devuelve el documento actualizado y limpio
    return get_user_by_id(user_id)

def soft_delete_user(user_id, current_user_id, current_user_role):
    """(DELETE) Desactiva un usuario (soft delete)."""
    # Lógica de Permisos: Un usuario solo puede eliminarse a sí mismo, a menos que sea admin.
    if user_id != current_user_id and current_user_role != 'admin':
        raise PermissionError("No tienes permiso para eliminar este usuario.")
        
    user_ref = db.collection('users').document(user_id)
    if not user_ref.get().exists:
        raise ValueError("Usuario no encontrado.")

    # Se marca el usuario como inactivo en lugar de borrarlo de la base de datos
    user_ref.update({'active': False})
    return {"id": user_id, "message": "Usuario desactivado exitosamente."}