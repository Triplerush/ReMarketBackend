# app/services/auth_service.py
from firebase_admin import auth
from . import user_service # Importamos el servicio de usuario para crear el perfil

def register_user(data):
    """
    Orquesta el registro de un nuevo usuario.
    1. Crea el usuario en Firebase Authentication.
    2. Si tiene éxito, crea el perfil del usuario en la base de datos Firestore.
    """
    email = data['email']
    password = data['password']

    # Paso 1: Crear el usuario en Firebase Authentication
    try:
        user_record = auth.create_user(
            email=email,
            password=password,
            disabled=False
        )
        uid = user_record.uid
    except auth.EmailAlreadyExistsError:
        # Este error es manejado por el controlador para devolver un 409 Conflict
        raise ValueError("El correo electrónico ya está en uso.")
    except Exception as e:
        raise Exception(f"Error creando usuario en Firebase Auth: {e}")

    # Paso 2: Crear el documento del usuario en Firestore
    # Pasamos el resto de los datos y el nuevo UID al servicio de usuarios.
    try:
        user_profile = user_service.create_user(data, uid)
        return user_profile
    except Exception as e:
        # Si falla la creación en Firestore, debemos borrar el usuario de Auth para evitar inconsistencias.
        auth.delete_user(uid)
        raise Exception(f"Error creando perfil en Firestore: {e}")

# NOTA SOBRE EL LOGIN:
# El login con email/password se realiza en el cliente (app móvil/web) usando el SDK de Firebase.
# El cliente recibe un ID Token. El backend no maneja contraseñas directamente.
# La función del backend es verificar ese token para dar acceso a rutas protegidas.
# El decorador @login_required ya hace esta verificación.