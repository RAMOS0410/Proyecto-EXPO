import hashlib
import os
import io
import base64
import sqlite3
import secrets
import pandas as pd
from PIL import Image
from openai import OpenAI
import streamlit as st
import streamlit.components.v1 as components

# --- FIREBASE ---
import firebase_admin
from firebase_admin import credentials, firestore, storage

# --- CONFIGURACIÓN E ICONO ---
try:
    favicon_img = Image.open("logo.png")
except Exception:
    favicon_img = "🌿"

st.set_page_config(
    page_title="AGRO IA",
    page_icon=favicon_img,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS CON BOTONES Y TARJETAS DESTACADAS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg-main: #F4F9F4;
        --card-bg: #FFFFFF;
        --card-border: #D8F3DC;
        --text-title: #081C15;
        --text-body: #1B4332;
        --sidebar-bg: #1B4332;
        --sidebar-bg-2: #2D6A4F;
        --primary-btn: #2D6A4F;
        --primary-btn-hover: #40916C;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text-body) !important;
        font-family: 'Inter', sans-serif !important;
    }

    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    [data-testid="stMarkdownContainer"] h1, 
    [data-testid="stMarkdownContainer"] h2, 
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--text-title) !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
    }

    .stApp p, .stApp span, .stApp label, .stApp li, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {
        color: #1B4332 !important;
    }

    [data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        margin-bottom: 10px !important;
    }

    [data-testid="stChatMessage"] p, 
    [data-testid="stChatMessage"] li, 
    [data-testid="stChatMessage"] span, 
    [data-testid="stChatMessage"] div {
        color: #081C15 !important;
    }

    input[type="text"], input[type="password"] {
        background-color: #FFFFFF !important;
        color: #081C15 !important;
        border: 1.5px solid var(--card-border) !important;
        border-radius: 10px !important;
    }

    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] div[data-baseweb="base-input"],
    [data-testid="stChatInput"] div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border-color: #2D6A4F !important;
        border-radius: 16px !important;
    }

    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] input {
        color: #081C15 !important;
        -webkit-text-fill-color: #081C15 !important;
        background-color: transparent !important;
        font-weight: 500 !important;
    }

    [data-testid="stChatInput"] textarea::placeholder,
    [data-testid="stChatInput"] input::placeholder {
        color: #555555 !important;
        -webkit-text-fill-color: #555555 !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-2) 100%) !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-captioncontainer="true"] {
        color: #D8F3DC !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(216, 243, 220, 0.3) !important;
    }

    /* BOTONES GRANDES DE NAVEGACIÓN EN SIDEBAR */
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: #FFFFFF !important;
        border: 1.5px solid #D8F3DC !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #1B4332 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background-color: #D8F3DC !important;
        border-color: #40916C !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.12) !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #081C15 !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label [data-baseweb="radio"] > div:first-child {
        display: none !important;
    }

    /* BOTONES DE ACCIÓN PRINCIPALES */
    div.stButton > button,
    div.stButton > button * {
        background-color: var(--primary-btn) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 14px !important;
        border: none !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        padding: 1rem 2.2rem !important;
        font-size: 17px !important;
        letter-spacing: 0.2px !important;
        min-height: 52px !important;
        box-shadow: 0 4px 14px rgba(45, 106, 79, 0.25) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease !important;
    }

    div.stButton > button:hover,
    div.stButton > button:hover * {
        background-color: var(--primary-btn-hover) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        transform: translateY(-3px) scale(1.01) !important;
        box-shadow: 0 8px 20px rgba(45, 106, 79, 0.35) !important;
    }

    [data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 1.5px dashed #40916C !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }

    [data-testid="stFileUploader"] * {
        color: #1B4332 !important;
    }

    div[data-testid="stNotification"] {
        background-color: #E8F5E9 !important;
        color: #1B4332 !important;
        border: 1px solid #B7E4C7 !important;
        border-radius: 12px !important;
    }

    div[data-testid="stNotification"] * {
        color: #1B4332 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES PWA Y LOCALSTORAGE ---
def inject_pwa():
    components.html("""
    <script>
    if (!document.querySelector('link[rel="manifest"]')) {
        const linkManifest = document.createElement('link');
        linkManifest.rel = 'manifest';
        linkManifest.href = 'app/static/manifest.json';
        document.head.appendChild(linkManifest);
    }
    if (!document.querySelector('meta[name="theme-color"]')) {
        const metaTheme = document.createElement('meta');
        metaTheme.name = 'theme-color';
        metaTheme.content = '#2D6A4F';
        document.head.appendChild(metaTheme);
    }
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('app/static/sw.js').catch(() => {});
    }
    </script>
    """, height=0, width=0)

def set_local_storage_token(token):
    components.html(f"""
    <script>
    try {{
        localStorage.setItem('agroia_token', '{token}');
    }} catch (e) {{}}
    </script>
    """, height=0, width=0)

def clear_local_storage_token():
    components.html("""
    <script>
    try {
        localStorage.removeItem('agroia_token');
    } catch (e) {}
    </script>
    """, height=0, width=0)

def try_restore_from_local_storage():
    components.html("""
    <script>
    try {
        const token = localStorage.getItem('agroia_token');
        if (token) {
            const topWindow = window.top;
            const url = new URL(topWindow.location.href);
            if (url.searchParams.get('session_token') !== token) {
                url.searchParams.set('session_token', token);
                topWindow.location.replace(url.toString());
            }
        }
    } catch (e) {}
    </script>
    """, height=0, width=0)

# --- CONEXIÓN OPENAI ---
raw_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
api_key = str(raw_key).strip().strip('"').strip("'")
client = OpenAI(api_key=api_key) if api_key else None

@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        firebase_config = dict(st.secrets["firebase"])
        storage_bucket = firebase_config.pop("storage_bucket", None)
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})
    return firestore.client(), storage.bucket()

try:
    db_firestore, firebase_bucket = init_firebase()
    firebase_ok = True
except Exception as e:
    db_firestore, firebase_bucket = None, None
    firebase_ok = False
    firebase_error = str(e)

# --- BASE DE DATOS SQLITE ---
DB_NAME = "agroia_v4.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre_completo TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesiones (
            token TEXT PRIMARY KEY,
            usuario TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            titulo TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversacion_id INTEGER,
            rol TEXT,
            contenido TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversacion_id) REFERENCES conversaciones (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def registrar_usuario(usuario, correo, password, nombre):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario, correo, password, nombre_completo) VALUES (?, ?, ?, ?)",
                       (usuario.strip().lower(), correo.strip().lower(), hash_password(password), nombre))
        conn.commit()
        conn.close()
        return True, "Registro exitoso. Inicia sesión."
    except sqlite3.IntegrityError:
        return False, "El usuario o correo ya existe."
    except Exception as e:
        return False, f"Error: {e}"

def autenticar_usuario(identificador, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, usuario, correo, password, nombre_completo FROM usuarios WHERE usuario = ? OR correo = ?",
                       (identificador.strip().lower(), identificador.strip().lower()))
        user = cursor.fetchone()

        if user and user[3] == hash_password(password):
            token = secrets.token_hex(16)
            cursor.execute("INSERT INTO sesiones (token, usuario) VALUES (?, ?)", (token, user[1]))
            conn.commit()
            conn.close()
            return user, token, "OK"
        conn.close()
        return None, None, "Usuario o contraseña incorrectos."
    except Exception as e:
        return None, None, f"Error: {e}"

def obtener_usuario_por_token(token):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.usuario, u.nombre_completo
            FROM sesiones s
            JOIN usuarios u ON s.usuario = u.usuario
            WHERE s.token = ?
        """, (token,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception:
        return None

def cerrar_sesion_db(token):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sesiones WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def preparar_imagen(image_pil, max_dim=1024):
    imagen = image_pil.convert("RGB")
    imagen.thumbnail((max_dim, max_dim), Image.LANCZOS)
    return imagen

def encode_image_to_base64(image_pil):
    buffered = io.BytesIO()
    image_pil.save(buffered, format="JPEG", quality=85, optimize=True)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def subir_imagen_firebase(image_pil, usuario):
    buffer = io.BytesIO()
    image_pil.save(buffer, format="JPEG", quality=85, optimize=True)
    buffer.seek(0)

    nombre_unico = f"cultivos/{usuario}_{secrets.token_hex(8)}.jpg"
    blob = firebase_bucket.blob(nombre_unico)
    blob.upload_from_file(buffer, content_type="image/jpeg")
    blob.make_public()
    return blob.public_url

def crear_diagnostico_firestore(usuario, cultivo, diagnostico, imagen_url):
    doc_ref = db_firestore.collection("historial_cultivos").document()
    doc_ref.set({
        "usuario": usuario,
        "cultivo": cultivo,
        "diagnostico": diagnostico,
        "imagen_url": imagen_url,
        "chat": [],
        "fecha": firestore.SERVER_TIMESTAMP
    })
    return doc_ref.id

def agregar_mensaje_chat_firestore(doc_id, role, content):
    db_firestore.collection("historial_cultivos").document(doc_id).update({
        "chat": firestore.ArrayUnion([{"role": role, "content": content}])
    })

def obtener_historial_firestore(usuario):
    docs = (
        db_firestore.collection("historial_cultivos")
        .where("usuario", "==", usuario)
        .order_by("fecha", direction=firestore.Query.DESCENDING)
        .stream()
    )
    resultados = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        resultados.append(data)
    return resultados

inject_pwa()

params = st.query_params

if "autenticado" not in st.session_state:
    if "session_token" in params:
        user_info = obtener_usuario_por_token(params["session_token"])
        if user_info:
            st.session_state.autenticado = True
            st.session_state.usuario = user_info[0]
            st.session_state.nombre_completo = user_info[1] or user_info[0]
            st.session_state.token = params["session_token"]
        else:
            st.session_state.autenticado = False
    else:
        st.session_state.autenticado = False

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- ACCESO ---
if not st.session_state.autenticado:
    try_restore_from_local_storage()

    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        st.markdown('<div style="font-size: 56px; text-align: center; margin-bottom: 6px;">🌿</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; font-size: 34px; font-weight: 800; color: #081C15;">AGRO IA</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #1B4332; font-size: 15px; margin-bottom: 24px;">Inteligencia Artificial para el cuidado de tus cultivos</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        with tab1:
            user_input = st.text_input("Usuario o Correo", key="l_user")
            pass_input = st.text_input("Contraseña", type="password", key="l_pass")
            if st.button("Iniciar sesión", use_container_width=True, key="btn_login"):
                user, token, msj = autenticar_usuario(user_input, pass_input)
                if user:
                    st.session_state.autenticado = True
                    st.session_state.usuario = user[1]
                    st.session_state.nombre_completo = user[4] or user[1]
                    st.session_state.token = token

                    st.query_params["session_token"] = token
                    set_local_storage_token(token)
                    st.rerun()
                else:
                    st.error(msj)
        with tab2:
            n_name = st.text_input("Nombre Completo", key="r_name")
            n_user = st.text_input("Usuario", key="r_user")
            n_mail = st.text_input("Correo", key="r_mail")
            n_pass = st.text_input("Contraseña", type="password", key="r_pass")
            if st.button("Crear Cuenta", use_container_width=True, key="btn_register"):
                ok, msj = registrar_usuario(n_user, n_mail, n_pass, n_name)
                if ok:
                    st.success(msj)
                else:
                    st.error(msj)

# --- PANEL PRINCIPAL ---
else:
    st.sidebar.title("AGRO IA 🌿")
    st.sidebar.caption(f"Usuario activo: {st.session_state.usuario}")
    st.sidebar.write("---")

    opcion_mostrada = st.sidebar.radio(
        "Navegación",
        ["🏠  Inicio e Historial", "🐛  Detectar Plaga", "🤖  Asistente Virtual", "👤  Mi Cuenta"],
        label_visibility="collapsed"
    )
    opcion = opcion_mostrada.split("  ", 1)[1]

    if opcion == "Inicio e Historial":
        st.title(f"¡Bienvenido, {st.session_state.nombre_completo}! 🌿")
        st.caption("Resumen y registro de los diagnósticos aplicados a tus cultivos.")
        st.subheader("Historial de Diagnósticos")

        if not firebase_ok:
            st.error(f"No se pudo conectar con Firebase: {firebase_error}")
        else:
            try:
                historial = obtener_historial_firestore(st.session_state.usuario)

                if historial:
                    for registro in historial:
                        fecha = registro.get("fecha")
                        fecha_str = fecha.strftime("%d/%m/%Y %H:%M") if fecha else "Fecha no disponible"
                        cultivo = registro.get("cultivo", "Diagnóstico")

                        with st.expander(f"🌿 {cultivo} — {fecha_str}"):
                            col_img, col_texto = st.columns([1, 1.5])
                            with col_img:
                                imagen_url = registro.get("imagen_url")
                                if imagen_url:
                                    st.image(imagen_url, use_container_width=True, caption="Muestra analizada")
                                else:
                                    st.info("Sin imagen disponible para este registro.")
                            with col_texto:
                                st.markdown(registro.get("diagnostico", "Sin detalle disponible."))

                            chat_guardado = registro.get("chat", [])
                            if chat_guardado:
                                st.write("---")
                                st.markdown("**💬 Conversación de seguimiento:**")
                                for msg in chat_guardado:
                                    rol_label = "🧑 Tú" if msg.get("role") == "user" else "🤖 Asistente"
                                    st.markdown(f"**{rol_label}:** {msg.get('content', '')}")
                else:
                    st.info("Aún no has realizado diagnósticos. Selecciona 'Detectar Plaga' en el menú lateral para evaluar una muestra.")
            except Exception as e:
                st.error(f"Error al cargar historial desde Firestore: {e}")

    elif opcion == "Detectar Plaga":
        st.title("Nuevo Diagnóstico Agrícola")
        st.caption("Sube una foto clara de la hoja o cultivo.")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Captura de Muestra")
            origen = st.radio("Origen de la imagen:", ["Subir Archivo", "Cámara Directa"])

            imagen_file = None
            if origen == "Subir Archivo":
                imagen_file = st.file_uploader("Formatos permitidos: JPG, PNG", type=["jpg", "png", "jpeg"])
            else:
                imagen_file = st.camera_input("Tomar foto")

            img = None
            if imagen_file:
                img = preparar_imagen(Image.open(imagen_file))
                st.image(img, caption="Muestra seleccionada", use_container_width=True)
            else:
                if "ultimo_analisis" in st.session_state:
                    del st.session_state["ultimo_analisis"]
                if "chat_plaga_historial" in st.session_state:
                    del st.session_state["chat_plaga_historial"]
                if "diag_doc_id" in st.session_state:
                    del st.session_state["diag_doc_id"]

        with col2:
            st.subheader("Resultado del Análisis")
            if imagen_file and img is not None:
                if st.button("Ejecutar Análisis", use_container_width=True):
                    with st.spinner("Procesando muestra foliar..."):
                        if client:
                            try:
                                base64_image = encode_image_to_base64(img)

                                prompt_analisis = """
                                Asistente de identificación botánica y agronomía.
                                Examina la muestra foliar presente en la fotografía y genera un reporte técnico en español.

                                Formato requerido:
                                🌱 **Especie Vegetal:** (Nombre común y científico)
                                🔍 **Observaciones Foliares:** (Síntomas visuales, manchas, coloración o presencia de insectos)
                                📊 **Estado de la Muestra:** (Normal, Leve, Moderado o Severo)
                                💡 **Manejo Agronómico Recomendado:** (Tratamientos orgánicos o cuidados del cultivo)
                                🛡️ **Medidas Preventivas:** (Riego, nutrición y ventilación)
                                """

                                response = client.chat.completions.create(
                                    model="gpt-4o-mini",
                                    messages=[
                                        {
                                            "role": "system",
                                            "content": "Eres un software de visión artificial para la catalogación e identificación de plantas agrícolas y jardinería."
                                        },
                                        {
                                            "role": "user",
                                            "content": [
                                                {"type": "text", "text": prompt_analisis},
                                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "auto"}}
                                            ]
                                        }
                                    ],
                                    max_tokens=1000
                                )

                                resultado = response.choices[0].message.content
                                st.session_state.ultimo_analisis = resultado
                                st.session_state.chat_plaga_historial = []

                                if firebase_ok:
                                    try:
                                        imagen_url = subir_imagen_firebase(img, st.session_state.usuario)
                                        doc_id = crear_diagnostico_firestore(
                                            usuario=st.session_state.usuario,
                                            cultivo="Análisis Foliar",
                                            diagnostico=resultado,
                                            imagen_url=imagen_url
                                        )
                                        st.session_state.diag_doc_id = doc_id
                                    except Exception as e:
                                        st.session_state.diag_doc_id = None
                                        st.warning(f"El diagnóstico se generó, pero no se pudo guardar en Firebase: {e}")
                                else:
                                    st.session_state.diag_doc_id = None
                                    st.warning("Firebase no está configurado; el diagnóstico no se guardó en el historial.")

                            except Exception as e:
                                st.error(f"Error durante el procesamiento: {e}")
                        else:
                            st.error("No se ha configurado la clave API de OpenAI.")

                if "ultimo_analisis" in st.session_state:
                    st.markdown(st.session_state.ultimo_analisis)
            else:
                st.info("Carga o toma una fotografía a la izquierda para desplegar aquí el reporte.")

        # SOLO MUESTRA EL CHAT DE SEGUIMIENTO SI HAY UN ANÁLISIS GENERADO
        if "ultimo_analisis" in st.session_state:
            st.write("---")
            st.subheader("💬 Chat de seguimiento sobre esta muestra")

            if "chat_plaga_historial" not in st.session_state:
                st.session_state.chat_plaga_historial = []

            for msg in st.session_state.chat_plaga_historial:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if prompt_seguimiento := st.chat_input("Pregunta cualquier duda sobre este diagnóstico..."):
                st.session_state.chat_plaga_historial.append({"role": "user", "content": prompt_seguimiento})

                with st.chat_message("user"):
                    st.markdown(prompt_seguimiento)

                if firebase_ok and st.session_state.get("diag_doc_id"):
                    try:
                        agregar_mensaje_chat_firestore(st.session_state.diag_doc_id, "user", prompt_seguimiento)
                    except Exception:
                        pass

                with st.chat_message("assistant"):
                    if client:
                        try:
                            mensajes_contexto = [
                                {
                                    "role": "system",
                                    "content": f"Eres un asistente agrónomo experto. Responde las dudas del usuario basándote en este análisis foliar previo:\n{st.session_state.ultimo_analisis}"
                                }
                            ] + st.session_state.chat_plaga_historial

                            res = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=mensajes_contexto,
                                max_tokens=800
                            )
                            respuesta_bot = res.choices[0].message.content
                            st.markdown(respuesta_bot)
                            st.session_state.chat_plaga_historial.append({"role": "assistant", "content": respuesta_bot})

                            if firebase_ok and st.session_state.get("diag_doc_id"):
                                try:
                                    agregar_mensaje_chat_firestore(st.session_state.diag_doc_id, "assistant", respuesta_bot)
                                except Exception:
                                    pass

                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al responder: {e}")
                    else:
                        st.error("No hay clave API de OpenAI configurada.")

    elif opcion == "Asistente Virtual":
        st.title("Asistente Agrónomo")
        st.caption("Resuelve tus dudas generales sobre siembras, fertilizantes, rotación de cultivos y plagas.")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT id, titulo FROM conversaciones WHERE usuario = ? ORDER BY id DESC", (st.session_state.usuario,))
        chats_existentes = cursor.fetchall()

        opciones_map = {"+ Nueva Conversación": None}
        for c in chats_existentes:
            opciones_map[f"Chat #{c[0]}: {c[1]}"] = c[0]

        lista_opciones = list(opciones_map.keys())

        index_seleccionado = 0
        if "current_chat_id" in st.session_state:
            for idx, key in enumerate(lista_opciones):
                if opciones_map[key] == st.session_state.current_chat_id:
                    index_seleccionado = idx
                    break

        chat_seleccionado = st.sidebar.selectbox("Historial de Consultas Generales", lista_opciones, index=index_seleccionado)

    elif opcion == "Mi Cuenta":
        st.title("👤 Mi Cuenta")
        st.write(f"**Usuario:** {st.session_state.usuario}")
        st.write(f"**Nombre Completo:** {st.session_state.nombre_completo}")

        if st.button("Cerrar Sesión", use_container_width=True):
            cerrar_sesion_db(st.session_state.get("token"))
            clear_local_storage_token()
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()