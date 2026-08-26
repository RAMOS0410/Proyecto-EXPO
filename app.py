import hashlib
import os
import io
import uuid
import base64
import sqlite3
import pandas as pd
from PIL import Image, ImageDraw
from openai import OpenAI
import streamlit as st








def cargar_logo():
    for nombre in ["logo.jpeg"]:
        if os.path.exists(nombre):
            try:
                return Image.open(nombre)
            except Exception:
                pass
    # Ícono de respaldo generado localmente: un monograma simple, sin emojis.
    icono = Image.new("RGB", (192, 192), color="#1f3d2b")
    dibujo = ImageDraw.Draw(icono)
    dibujo.ellipse((16, 16, 176, 176), fill="#2f5b3e")
    dibujo.text((96, 96), "A", fill="#f6faf5", anchor="mm")
    return icono

favicon_img = cargar_logo()

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="AGRO IA",
    page_icon=favicon_img,
    layout="wide",
    initial_sidebar_state="expanded"
)


PWA_INJECTION = """
<script>
(function() {
    if (document.getElementById('agroia-manifest')) return;

    const manifest = {
        name: "AGRO IA",
        short_name: "AGRO IA",
        description: "Plataforma de Diagnóstico y Monitoreo Agrícola",
        start_url: window.location.href,
        display: "standalone",
        background_color: "#f6faf5",
        theme_color: "#1f3d2b",
        icons: [{
            src: "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjMyIiBmaWxsPSIjMWYzZDJiIi8+PHRleHQgeD0iOTYiIHk9IjEyNCIgZm9udC1zaXplPSI5NiIgZmlsbD0iI2ZmZmZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIj5BPC90ZXh0Pjwvc3ZnPg==",
            sizes: "192x192",
            type: "image/svg+xml"
        }]
    };

    const manifestBlob = new Blob([JSON.stringify(manifest)], {type: 'application/json'});
    const manifestUrl = URL.createObjectURL(manifestBlob);

    const link = document.createElement('link');
    link.id = 'agroia-manifest';
    link.rel = 'manifest';
    link.href = manifestUrl;
    document.head.appendChild(link);

    const themeMeta = document.createElement('meta');
    themeMeta.name = 'theme-color';
    themeMeta.content = '#1f3d2b';
    document.head.appendChild(themeMeta);

    if ('serviceWorker' in navigator) {
        const swCode = "self.addEventListener('install', e => self.skipWaiting()); self.addEventListener('activate', e => self.clients.claim()); self.addEventListener('fetch', e => {});";
        const swBlob = new Blob([swCode], {type: 'application/javascript'});
        const swUrl = URL.createObjectURL(swBlob);
        navigator.serviceWorker.register(swUrl).catch(function(err) {
            console.log('No se pudo registrar el service worker:', err);
        });
    }
})();
</script>
"""
st.markdown(PWA_INJECTION, unsafe_allow_html=True)


if "tema" not in st.session_state:
    st.session_state.tema = "Claro"

TEMA_CALIDO_CSS = """
    :root {
        --bg-main: #faf3e8 !important;
        --card-bg: #fffaf2 !important;
        --card-border: #e3cba6 !important;
        --card-accent: #b5793a !important;
        --text-title: #4a3220 !important;
        --text-body: #6b4f37 !important;
        --sidebar-bg: linear-gradient(180deg, #5c4326 0%, #46331d 100%) !important;
        --sidebar-text: #fdf6ec !important;
        --primary-btn: #a9702e !important;
        --primary-btn-hover: #8a5a22 !important;
        --accent: #6f9c5a !important;
        --accent-2: #d98c3a !important;
    }
"""

BASE_CSS = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, h4 {
        font-family: 'Sora', 'Inter', sans-serif !important;
        letter-spacing: -0.01em;
    }

    :root {
        --bg-main: #f6faf5;
        --card-bg: #ffffff;
        --card-border: #dbe8d9;
        --card-accent: #4c8c5c;
        --text-title: #1f3d2b;
        --text-body: #3f4b45;
        --sidebar-bg: linear-gradient(180deg, #1f3d2b 0%, #142a1d 100%);
        --sidebar-text: #f6faf5;
        --primary-btn: #4c8c5c;
        --primary-btn-hover: #3a6e47;
        --accent: #4c8c5c;
        --accent-2: #c9a06c;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #10201a;
            --card-bg: #16281f;
            --card-border: #2b4438;
            --card-accent: #4fae68;
            --text-title: #eaf5ec;
            --text-body: #c9d8cd;
            --sidebar-bg: linear-gradient(180deg, #0c1912 0%, #081108 100%);
            --sidebar-text: #eaf5ec;
            --primary-btn: #4fae68;
            --primary-btn-hover: #3d8a52;
            --accent: #4fae68;
            --accent-2: #c9a06c;
        }
    }

    .stApp {
        background-color: var(--bg-main) !important;
        transition: background-color 0.4s ease;
    }

    [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] * { color: var(--sidebar-text) !important; }

    h1, h2, h3, h4 { color: var(--text-title) !important; font-weight: 700 !important; }
    p, span, label { color: var(--text-body); }

    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background-color: var(--card-bg) !important;
        border-radius: 14px !important;
        padding: 20px !important;
        border: 1px solid var(--card-border) !important;
        border-left: 4px solid var(--card-accent) !important;
        margin-bottom: 12px !important;
        animation: fadeIn 0.5s ease;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"]:hover {
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }

    div.stButton > button {
        background-color: var(--primary-btn) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: transform 0.15s ease, background-color 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: var(--primary-btn-hover) !important;
        color: #ffffff !important;
        transform: translateY(-2px);
    }

    .agro-titulo-bienvenida {
        text-align: center;
        animation: fadeIn 0.8s ease;
    }
    .agro-subtitulo {
        text-align: center;
        animation: fadeIn 1.1s ease;
        color: var(--text-body);
    }

    [data-testid="stTabs"] button[data-baseweb="tab"] {
        font-weight: 600;
        color: var(--text-body);
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom-color: var(--accent) !important;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    </style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)
if st.session_state.tema == "Cálido":
    st.markdown(f"<style>{TEMA_CALIDO_CSS}</style>", unsafe_allow_html=True)

# --- SELECTOR DE TEMA (visible también antes de iniciar sesión) ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.session_state.tema = st.selectbox(
        "Tema", ["Claro", "Cálido"],
        index=["Claro", "Cálido"].index(st.session_state.tema),
        help="El modo oscuro se activa automáticamente según la configuración de tu dispositivo."
    )

# --- CLIENTE OPENAI (sin cambios de estructura) ---
raw_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
api_key = str(raw_key).strip().strip('"').strip("'")
client = OpenAI(api_key=api_key) if api_key else None

# --- BASE DE DATOS LOCAL ---
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
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            cultivo TEXT,
            diagnostico TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Tabla de sesiones -> esto es lo que arregla el cierre de sesión
    # accidental cada vez que se toma una foto o se hace una acción.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesiones (
            token TEXT PRIMARY KEY,
            usuario TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        conn.close()
        if user and user[3] == hash_password(password):
            return user, "OK"
        return None, "Usuario o contraseña incorrectos."
    except Exception as e:
        return None, f"Error: {e}"



def crear_sesion(usuario):
    token = str(uuid.uuid4())
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sesiones (token, usuario) VALUES (?, ?)", (token, usuario))
    conn.commit()
    conn.close()
    return token

def validar_sesion(token):
    if not token:
        return None
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT usuario FROM sesiones WHERE token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def cerrar_sesion_db(token):
    if token:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sesiones WHERE token = ?", (token,))
        conn.commit()
        conn.close()

def obtener_nombre_completo(usuario):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_completo FROM usuarios WHERE usuario = ?", (usuario,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else usuario

def encode_image_to_base64(image_pil):
    buffered = io.BytesIO()
    image_pil.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# --- ESTADO DE SESIÓN ---
for clave, valor in {
    "autenticado": False, "usuario": "", "nombre_completo": "",
    "messages": [], "token": None
}.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor


if not st.session_state.autenticado:
    token_url = st.query_params.get("token")
    if token_url:
        usuario_valido = validar_sesion(token_url)
        if usuario_valido:
            st.session_state.autenticado = True
            st.session_state.usuario = usuario_valido
            st.session_state.nombre_completo = obtener_nombre_completo(usuario_valido)
            st.session_state.token = token_url

# --- PANTALLA DE LOGIN ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h1 class="agro-titulo-bienvenida">AGRO IA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="agro-subtitulo">Plataforma de Diagnóstico y Monitoreo Agrícola</p>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        with tab1:
            user_input = st.text_input("Usuario o Correo", key="l_user")
            pass_input = st.text_input("Contraseña", type="password", key="l_pass")
            if st.button("Ingresar", use_container_width=True):
                user, msj = autenticar_usuario(user_input, pass_input)
                if user:
                    token = crear_sesion(user[1])
                    st.session_state.autenticado = True
                    st.session_state.usuario = user[1]
                    st.session_state.nombre_completo = user[4] or user[1]
                    st.session_state.token = token
                    st.query_params["token"] = token
                    st.rerun()
                else:
                    st.error(msj)
        with tab2:
            n_name = st.text_input("Nombre Completo", key="r_name")
            n_user = st.text_input("Usuario", key="r_user")
            n_mail = st.text_input("Correo", key="r_mail")
            n_pass = st.text_input("Contraseña", type="password", key="r_pass")
            if st.button("Crear Cuenta", use_container_width=True):
                ok, msj = registrar_usuario(n_user, n_mail, n_pass, n_name)
                if ok:
                    st.success(msj)
                else:
                    st.error(msj)

# --- PANEL PRINCIPAL ---
else:
    st.sidebar.markdown('<h2>AGRO IA</h2>', unsafe_allow_html=True)
    st.sidebar.caption(f"Usuario: {st.session_state.usuario}")
    st.sidebar.write("---")

    opcion = st.sidebar.radio(
        "Navegación",
        ["Inicio e Historial", "Detectar Plaga", "Asistente Virtual", "Mi Cuenta"]
    )

    # --- 1. INICIO E HISTORIAL ---
    if opcion == "Inicio e Historial":
        st.markdown(f'<h1 class="agro-titulo-bienvenida">Bienvenido, {st.session_state.nombre_completo}</h1>', unsafe_allow_html=True)
        st.caption("Consulta el registro y la evolución de los diagnósticos de tus cultivos.")

        st.subheader("Historial de Diagnósticos")
        try:
            conn = sqlite3.connect(DB_NAME)
            df = pd.read_sql_query(
                "SELECT fecha AS Fecha, cultivo AS Cultivo, diagnostico AS Resumen FROM historial WHERE usuario = ? ORDER BY fecha DESC",
                conn,
                params=(st.session_state.usuario,)
            )
            conn.close()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Aún no has realizado diagnósticos. Ve a la sección 'Detectar Plaga' para escanear una muestra.")
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")

    # --- 2. DETECTAR PLAGA ---
    elif opcion == "Detectar Plaga":
        st.title("Diagnóstico de Cultivo")
        st.caption("Sube una imagen o toma una foto para analizar el estado de salud de tu muestra.")

        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Entrada de Muestra")
            origen = st.radio("Método de captura:", ["Subir Archivo", "Cámara Directa"])

            imagen_file = None
            if origen == "Subir Archivo":
                imagen_file = st.file_uploader("Formatos: JPG, PNG", type=["jpg", "png", "jpeg"])
            else:
                imagen_file = st.camera_input("Capturar foto")

            if imagen_file:
                img = Image.open(imagen_file).convert("RGB")
                st.image(img, caption="Muestra cargada", use_container_width=True)

        with col2:
            st.subheader("Informe del Diagnóstico")
            if imagen_file:
                if st.button("Ejecutar Análisis", use_container_width=True):
                    with st.spinner("Procesando imagen..."):
                        if client:
                            try:
                                base64_image = encode_image_to_base64(img)
                                prompt_analisis = """
                                Analiza esta imagen agrícola. Explica todo con lenguaje muy sencillo, directo y fácil de entender.

                                Responde en estas 4 secciones claras:
                                1. Planta y Problema Detectado (Especie y daño visto en palabras sencillas).
                                2. Nivel de Gravedad (Bajo, Medio o Alto).
                                3. Soluciones Recomendadas (Remedios caseros orgánicos y opción comercial de tienda).
                                4. Prevención (Consejos simples para evitar que vuelva a suceder).
                                """
                                response = client.chat.completions.create(
                                    model="gpt-5.6-luna",
                                    messages=[{
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": prompt_analisis},
                                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                        ]
                                    }],
                                    reasoning_effort="none",
                                    max_completion_tokens=1200
                                )
                                resultado = response.choices[0].message.content
                                st.markdown(resultado)

                                conn = sqlite3.connect(DB_NAME)
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO historial (usuario, cultivo, diagnostico) VALUES (?, ?, ?)",
                                               (st.session_state.usuario, "Auto-detectado", resultado[:100] + "..."))
                                conn.commit()
                                conn.close()
                            except Exception as e:
                                st.error(f"Error al analizar: {e}")
                        else:
                            st.error("No hay API Key configurada.")
            else:
                st.info("Carga una foto en el panel izquierdo para ver los resultados aquí.")

    # --- 3. ASISTENTE VIRTUAL ---
    elif opcion == "Asistente Virtual":
        st.title("Asistente Agrónomo")
        st.caption("Consulta dudas sobre tratamiento de suelos, dosis o manejo de plagas.")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Escribe tu pregunta agrícola aquí..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                if client:
                    try:
                        history = [{"role": "system", "content": "Eres un experto agrónomo que responde en español sencillo, directo y profesional."}] + st.session_state.messages
                        res = client.chat.completions.create(
                            model="gpt-5.6-luna",
                            messages=history,
                            reasoning_effort="none",
                            max_completion_tokens=1000
                        )
                        text = res.choices[0].message.content
                        st.markdown(text)
                        st.session_state.messages.append({"role": "assistant", "content": text})
                    except Exception as e:
                        st.error(f"Error: {e}")

    # --- 4. MI CUENTA ---
    elif opcion == "Mi Cuenta":
        st.title("Gestión de Cuenta")
        st.caption("Información del perfil de usuario y opciones de sesión.")

        st.write(f"**Nombre:** {st.session_state.nombre_completo}")
        st.write(f"**Usuario:** {st.session_state.usuario}")
        st.write("---")

        col_logout, _ = st.columns([1, 2])
        with col_logout:
            if st.button("Cerrar Sesión", use_container_width=True):
                cerrar_sesion_db(st.session_state.get("token"))
                st.session_state.autenticado = False
                st.session_state.usuario = ""
                st.session_state.nombre_completo = ""
                st.session_state.messages = []
                st.session_state.token = None
                st.query_params.clear()
                st.rerun()