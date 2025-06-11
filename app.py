import os
import uuid # Para generar IDs únicos
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone # Para timestamps

# --- Configuración Inicial de Flask y Firebase ---
app = Flask(__name__)

# Cargar credenciales de Firebase Admin SDK
# Asegúrate de que el archivo 'firebase-adminsdk-credentials.json' esté en el mismo directorio
# o que la variable de entorno GOOGLE_APPLICATION_CREDENTIALS esté configurada.
try:
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-adminsdk-credentials.json')
    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            f"Archivo de credenciales '{cred_path}' no encontrado. "
            "Descárgalo de Firebase Console (Project settings > Service accounts) "
            "y colócalo en la raíz del proyecto o configura la variable de entorno."
        )
    cred = credentials.Certificate(cred_path)

    # Inicializar la app de Firebase Admin.
    # Si NO vas a usar Firebase Storage por ahora, puedes omitir 'storageBucket'.
    # Si SÍ lo vas a usar más adelante, asegúrate de que tu proyecto esté en el plan Blaze
    # y reemplaza 'tu-proyecto-id.appspot.com' con el nombre de tu bucket.
    firebase_storage_bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET') # Opcional por ahora

    if firebase_storage_bucket_name:
        firebase_admin.initialize_app(cred, {
            'storageBucket': firebase_storage_bucket_name
        })
        print(f"Firebase Admin SDK inicializado con Storage Bucket: {firebase_storage_bucket_name}")
    else:
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK inicializado (solo Firestore y otros servicios, sin Storage Bucket predeterminado).")

    db = firestore.client() # Cliente de Firestore
except Exception as e:
    print(f"Error CRÍTICO inicializando Firebase Admin SDK: {e}")
    # En un escenario real, podrías querer que la app no inicie si Firebase no está disponible.
    # exit(1)

# --- Modelos de Datos (Representación Lógica para Firestore) ---

# Colección: 'users'
# Documento:
#   uid (String, ID del documento, puede ser el UID de Firebase Auth más adelante)
#   nombres (String)
#   apellidos (String)
#   dni (String)
#   email (String)
#   password_hash (String) -> Si no usas Firebase Auth, necesitarías hashear y guardar. Por ahora omitido.
#   selfie_url (String) -> URL de la selfie en Firebase Storage
#   dni_anverso_url (String) -> URL del anverso del DNI
#   dni_reverso_url (String) -> URL del reverso del DNI
#   approved (Boolean, default: false)
#   role (String, e.g., "user", "admin", default: "user")
#   registered_at (Timestamp)
#   approved_at (Timestamp, opcional)
#   reputation_score (Number, opcional)

# Colección: 'publications'
# Documento:
#   pid (String, ID del documento)
#   seller_id (String, UID del vendedor, referencia a la colección 'users')
#   seller_name (String, para mostrar rápidamente)
#   marca (String)
#   modelo (String)
#   capacidad (String, e.g., "128GB")
#   precio (Number)
#   imei (String)
#   descripcion_estado (String)
#   image_urls (Array of Strings) -> URLs de las imágenes del producto
#   boleta_url (String) -> URL de la boleta/factura
#   caja_url (String) -> URL de la imagen de la caja
#   imei_externally_validated (Boolean, default: false) -> Resultado de la validación externa del IMEI
#   status (String, e.g., "en_revision", "disponible", "reservado", "vendido")
#   created_at (Timestamp)
#   updated_at (Timestamp)
#   approved_by_admin (Boolean, default: false) -> Si las publicaciones necesitan aprobación
#   admin_approved_at (Timestamp, opcional)

# --- Endpoints para Usuarios ---

@app.route('/users/register', methods=['POST'])
def register_user():
    """
    Registra un nuevo usuario. Los datos se guardan en Firestore con 'approved: false'.
    El administrador deberá aprobarlo posteriormente.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body no puede estar vacío."}), 400

        required_fields = ['nombres', 'apellidos', 'dni', 'email'] # 'password' se manejaría con Firebase Auth
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Campo requerido faltante o vacío: {field}"}), 400

        # Validar si el email o DNI ya existen (opcional, pero recomendado)
        users_ref = db.collection('users')
        query_email = users_ref.where(filter=firestore.FieldFilter('email', '==', data['email'])).limit(1).stream()
        if len(list(query_email)) > 0:
            return jsonify({"error": "El correo electrónico ya está registrado."}), 409 # Conflict

        query_dni = users_ref.where(filter=firestore.FieldFilter('dni', '==', data['dni'])).limit(1).stream()
        if len(list(query_dni)) > 0:
            return jsonify({"error": "El DNI ya está registrado."}), 409

        user_id = str(uuid.uuid4()) # Generar un ID único para el usuario
        user_data = {
            'uid': user_id,
            'nombres': data['nombres'],
            'apellidos': data['apellidos'],
            'dni': data['dni'],
            'email': data['email'],
            'selfie_url': data.get('selfie_url', ''), # URL de la selfie (se subirá a Storage en otro paso)
            'dni_anverso_url': data.get('dni_anverso_url', ''),
            'dni_reverso_url': data.get('dni_reverso_url', ''),
            'approved': False,
            'role': 'user', # Rol por defecto
            'registered_at': firestore.SERVER_TIMESTAMP # O datetime.now(timezone.utc)
        }

        db.collection('users').document(user_id).set(user_data)
        # No devolvemos la selfie_url ni urls de DNI en la respuesta por privacidad, solo el ID y mensaje.
        return jsonify({
            "message": "Usuario registrado exitosamente. Pendiente de aprobación por un administrador.",
            "userId": user_id,
            "email": data['email']
        }), 201

    except Exception as e:
        print(f"Error en register_user: {e}")
        return jsonify({"error": "Ocurrió un error interno al registrar el usuario."}), 500

@app.route('/admin/users/<user_id>/approve', methods=['PUT'])
def approve_user(user_id):
    """
    Endpoint para que un administrador apruebe un usuario.
    NOTA: Este endpoint debería estar protegido para que solo administradores puedan acceder.
    """
    try:
        # Aquí iría la lógica para verificar si el solicitante es un administrador
        # (e.g., validando un token de admin, verificando el rol del usuario que hace la request)
        # Por simplicidad, se omite esta validación en este ejemplo.

        user_ref = db.collection('users').document(user_id)
        doc = user_ref.get()

        if not doc.exists:
            return jsonify({"error": "Usuario no encontrado."}), 404

        if doc.to_dict().get('approved'):
            return jsonify({"message": "El usuario ya estaba aprobado."}), 200

        user_ref.update({
            'approved': True,
            'approved_at': firestore.SERVER_TIMESTAMP
        })
        return jsonify({"message": f"Usuario {user_id} aprobado exitosamente."}), 200

    except Exception as e:
        print(f"Error en approve_user: {e}")
        return jsonify({"error": "Ocurrió un error interno al aprobar el usuario."}), 500

@app.route('/users', methods=['GET'])
def get_users():
    """
    Obtiene una lista de usuarios.
    Permite filtrar por usuarios aprobados usando el query param 'approved=true'.
    """
    try:
        users_ref = db.collection('users')
        show_approved_only = request.args.get('approved', 'false').lower() == 'true'
        role_filter = request.args.get('role') # ej. /users?role=admin

        query = users_ref

        if show_approved_only:
            query = query.where(filter=firestore.FieldFilter('approved', '==', True))
        
        if role_filter:
            query = query.where(filter=firestore.FieldFilter('role', '==', role_filter))

        users_list = []
        for doc in query.stream():
            user_data = doc.to_dict()
            # Opcional: convertir Timestamps a string si es necesario para el cliente
            if 'registered_at' in user_data and hasattr(user_data['registered_at'], 'isoformat'):
                user_data['registered_at'] = user_data['registered_at'].isoformat()
            if 'approved_at' in user_data and user_data.get('approved_at') and hasattr(user_data['approved_at'], 'isoformat'):
                 user_data['approved_at'] = user_data['approved_at'].isoformat()
            users_list.append(user_data)

        return jsonify(users_list), 200
    except Exception as e:
        print(f"Error en get_users: {e}")
        return jsonify({"error": "Ocurrió un error interno al obtener los usuarios."}), 500

@app.route('/users/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Obtiene un usuario específico por su ID."""
    try:
        user_ref = db.collection('users').document(user_id)
        doc = user_ref.get()

        if not doc.exists:
            return jsonify({"error": "Usuario no encontrado."}), 404
        
        user_data = doc.to_dict()
        if 'registered_at' in user_data and hasattr(user_data['registered_at'], 'isoformat'):
            user_data['registered_at'] = user_data['registered_at'].isoformat()
        if 'approved_at' in user_data and user_data.get('approved_at') and hasattr(user_data['approved_at'], 'isoformat'):
             user_data['approved_at'] = user_data['approved_at'].isoformat()

        return jsonify(user_data), 200
    except Exception as e:
        print(f"Error en get_user_by_id: {e}")
        return jsonify({"error": "Ocurrió un error interno al obtener el usuario."}), 500


# --- Endpoints para Publicaciones de Celulares ---

@app.route('/publications', methods=['POST'])
def create_publication():
    """
    Crea una nueva publicación de celular.
    Requiere 'seller_id' del usuario que publica.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body no puede estar vacío."}), 400

        required_fields = ['seller_id', 'marca', 'modelo', 'precio', 'imei', 'descripcion_estado']
        for field in required_fields:
            if field not in data or not data[field]: # Verifica también que no sea vacío
                return jsonify({"error": f"Campo requerido faltante o vacío: {field}"}), 400

        # Verificar que el seller_id (vendedor) exista y esté aprobado
        seller_ref = db.collection('users').document(data['seller_id'])
        seller_doc = seller_ref.get()
        if not seller_doc.exists:
            return jsonify({"error": "El usuario vendedor no existe."}), 404
        
        seller_data = seller_doc.to_dict()
        if not seller_data.get('approved'):
            return jsonify({"error": "El usuario vendedor no está aprobado para publicar."}), 403 # Forbidden

        # Aquí iría la validación del IMEI con una API externa (como mencionaste en tu plan)
        # Por ahora, asumimos que se validará en el cliente o se marcará un campo.
        # imei_validation_result = validate_imei_externally(data['imei']) # Función hipotética

        publication_id = str(uuid.uuid4())
        publication_data = {
            'pid': publication_id,
            'seller_id': data['seller_id'],
            'seller_name': f"{seller_data.get('nombres','')} {seller_data.get('apellidos','')} ".strip(), # Nombre del vendedor
            'marca': data['marca'],
            'modelo': data['modelo'],
            'capacidad': data.get('capacidad', ''), # Opcional
            'precio': float(data['precio']), # Asegurar que sea número
            'imei': data['imei'],
            'descripcion_estado': data['descripcion_estado'],
            'image_urls': data.get('image_urls', []), # Lista de URLs de imágenes
            'boleta_url': data.get('boleta_url', ''), # URL de la boleta/factura
            'caja_url': data.get('caja_url', ''), # URL de la imagen de la caja
            'imei_externally_validated': data.get('imei_externally_validated', False), # Resultado de validación IMEI
            'status': 'en_revision', # Estado inicial, podría requerir aprobación de admin
            'approved_by_admin': False, # Las publicaciones también podrían necesitar aprobación
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
        }

        db.collection('publications').document(publication_id).set(publication_data)
        return jsonify({
            "message": "Publicación creada exitosamente, pendiente de revisión.",
            "publicationId": publication_id
        }), 201

    except ValueError:
        return jsonify({"error": "El precio debe ser un número válido."}), 400
    except Exception as e:
        print(f"Error en create_publication: {e}")
        return jsonify({"error": "Ocurrió un error interno al crear la publicación."}), 500

@app.route('/admin/publications/<publication_id>/approve', methods=['PUT'])
def approve_publication(publication_id):
    """
    Endpoint para que un administrador apruebe una publicación.
    NOTA: Este endpoint debería estar protegido.
    """
    try:
        pub_ref = db.collection('publications').document(publication_id)
        doc = pub_ref.get()

        if not doc.exists:
            return jsonify({"error": "Publicación no encontrada."}), 404
        
        current_status = doc.to_dict().get('status')
        if current_status == 'disponible':
             return jsonify({"message": "La publicación ya estaba aprobada y disponible."}), 200

        pub_ref.update({
            'approved_by_admin': True,
            'status': 'disponible', # Cambiar estado a disponible
            'admin_approved_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return jsonify({"message": f"Publicación {publication_id} aprobada y marcada como disponible."}), 200
    except Exception as e:
        print(f"Error en approve_publication: {e}")
        return jsonify({"error": "Ocurrió un error interno al aprobar la publicación."}), 500


@app.route('/publications', methods=['GET'])
def get_publications():
    """
    Obtiene una lista de todas las publicaciones.
    Filtra por defecto para mostrar solo las aprobadas y disponibles ('status' == 'disponible').
    Se pueden añadir más filtros como query params (e.g., ?marca=Samsung&precio_max=1000)
    """
    try:
        publications_ref = db.collection('publications')
        
        # Filtros básicos (puedes expandirlos mucho más)
        query = publications_ref.where(filter=firestore.FieldFilter('status', '==', 'disponible')) \
                                .where(filter=firestore.FieldFilter('approved_by_admin', '==', True))

        marca_filter = request.args.get('marca')
        if marca_filter:
            query = query.where(filter=firestore.FieldFilter('marca', '==', marca_filter))
        
        # Para filtros de rango de precio, Firestore requiere índices compuestos o múltiples queries
        # precio_min = request.args.get('precio_min', type=float)
        # precio_max = request.args.get('precio_max', type=float)
        # if precio_min is not None:
        #     query = query.where(filter=firestore.FieldFilter('precio', '>=', precio_min))
        # if precio_max is not None:
        #     query = query.where(filter=firestore.FieldFilter('precio', '<=', precio_max))
        
        query = query.order_by('created_at', direction=firestore.Query.DESCENDING) # Mostrar más recientes primero

        publications_list = []
        for doc in query.stream():
            pub_data = doc.to_dict()
            # Convertir Timestamps a string
            if 'created_at' in pub_data and hasattr(pub_data['created_at'], 'isoformat'):
                pub_data['created_at'] = pub_data['created_at'].isoformat()
            if 'updated_at' in pub_data and hasattr(pub_data['updated_at'], 'isoformat'):
                pub_data['updated_at'] = pub_data['updated_at'].isoformat()
            publications_list.append(pub_data)

        return jsonify(publications_list), 200
    except Exception as e:
        print(f"Error en get_publications: {e}")
        return jsonify({"error": "Ocurrió un error interno al obtener las publicaciones."}), 500

@app.route('/publications/<publication_id>', methods=['GET'])
def get_publication_by_id(publication_id):
    """Obtiene una publicación específica por su ID."""
    try:
        pub_ref = db.collection('publications').document(publication_id)
        doc = pub_ref.get()

        if not doc.exists:
            return jsonify({"error": "Publicación no encontrada."}), 404
        
        publication_data = doc.to_dict()
        # Solo mostrar si está aprobada y disponible, o si el que consulta es el vendedor o admin
        # Esta lógica de permisos puede ser más compleja.
        if not publication_data.get('approved_by_admin') or publication_data.get('status') != 'disponible':
            # Aquí podrías verificar si el solicitante es el dueño o un admin para permitir la vista.
            # Por ahora, se restringe a solo disponibles/aprobadas para el público general.
            # return jsonify({"error": "Publicación no disponible o pendiente de aprobación."}), 403
            pass # Permitimos verla por ahora, pero en producción se debe controlar el acceso

        if 'created_at' in publication_data and hasattr(publication_data['created_at'], 'isoformat'):
            publication_data['created_at'] = publication_data['created_at'].isoformat()
        if 'updated_at' in publication_data and hasattr(publication_data['updated_at'], 'isoformat'):
            publication_data['updated_at'] = publication_data['updated_at'].isoformat()

        return jsonify(publication_data), 200
    except Exception as e:
        print(f"Error en get_publication_by_id: {e}")
        return jsonify({"error": "Ocurrió un error interno al obtener la publicación."}), 500

# --- Endpoints de ejemplo para Edición y Eliminación (Esqueleto) ---
@app.route('/publications/<publication_id>', methods=['PUT'])
def update_publication(publication_id):
    """
    Actualiza una publicación existente.
    NOTA: Se debe verificar que el usuario que actualiza sea el dueño o un admin.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body no puede estar vacío."}), 400

        pub_ref = db.collection('publications').document(publication_id)
        doc = pub_ref.get()
        if not doc.exists:
            return jsonify({"error": "Publicación no encontrada."}), 404

        # Aquí iría la lógica de permisos: ¿es el dueño o un admin?
        # current_seller_id = doc.to_dict().get('seller_id')
        # requesting_user_id = ... # obtener de token de autenticación
        # if current_seller_id != requesting_user_id and not is_admin(requesting_user_id):
        #     return jsonify({"error": "No tienes permiso para editar esta publicación."}), 403

        # Campos que se pueden actualizar (ejemplo)
        update_data = {}
        allowed_to_update = ['marca', 'modelo', 'capacidad', 'precio', 'descripcion_estado', 'image_urls', 'boleta_url', 'caja_url', 'status']
        for key in allowed_to_update:
            if key in data:
                update_data[key] = data[key]
        
        if 'precio' in update_data:
            try:
                update_data['precio'] = float(update_data['precio'])
            except ValueError:
                 return jsonify({"error": "El precio debe ser un número válido."}), 400


        if not update_data:
            return jsonify({"error": "No se proporcionaron campos válidos para actualizar."}), 400

        update_data['updated_at'] = firestore.SERVER_TIMESTAMP
        # Si se edita, podría volver a "en_revision" si se cambian datos sensibles
        # update_data['status'] = 'en_revision'
        # update_data['approved_by_admin'] = False 

        pub_ref.update(update_data)
        return jsonify({"message": f"Publicación {publication_id} actualizada exitosamente."}), 200

    except Exception as e:
        print(f"Error en update_publication: {e}")
        return jsonify({"error": "Ocurrió un error interno al actualizar la publicación."}), 500

@app.route('/publications/<publication_id>', methods=['DELETE'])
def delete_publication(publication_id):
    """
    Elimina una publicación.
    NOTA: Se debe verificar que el usuario que elimina sea el dueño o un admin.
    También se deberían eliminar los archivos asociados de Firebase Storage.
    """
    try:
        pub_ref = db.collection('publications').document(publication_id)
        doc = pub_ref.get()
        if not doc.exists:
            return jsonify({"error": "Publicación no encontrada."}), 404

        # Lógica de permisos (similar a update)

        # Lógica para eliminar archivos de Storage (importante para el futuro)
        # image_urls_to_delete = doc.to_dict().get('image_urls', [])
        # boleta_url_to_delete = doc.to_dict().get('boleta_url')
        # ... (llamar a funciones para borrar de Storage) ...

        pub_ref.delete()
        return jsonify({"message": f"Publicación {publication_id} eliminada exitosamente."}), 200
    except Exception as e:
        print(f"Error en delete_publication: {e}")
        return jsonify({"error": "Ocurrió un error interno al eliminar la publicación."}), 500


# --- Punto de entrada principal ---
if __name__ == '__main__':
    # El puerto 8080 es común para servicios en la nube como Cloud Run.
    # Para desarrollo local, debug=True es útil. ¡NO USAR EN PRODUCCIÓN!
    # En producción, usa un servidor WSGI como Gunicorn: gunicorn --bind 0.0.0.0:8080 app:app
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
