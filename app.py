import hashlib
import os
import base64
import sqlite3
import secrets
import pandas as pd
from PIL import Image
from openai import OpenAI
import streamlit as st

# --- CARGAR FAVICON ---
try:
    favicon_img = Image.open("logo.png")
except Exception:
    favicon_img = "🌿"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="AGRO IA", 
    page_icon=favicon_img, 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    :root {
        --bg-main: #f8fafc;
        --card-bg: #ffffff;
        --card-border: #e2e8f0;
        --text-title: #0f172a;
        --text-body: #334155;
        --sidebar-bg: #1e293b;
        --sidebar-text: #f8fafc;
        --primary-btn: #15803d;
        --primary-btn-hover: #166534;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-title: #f8fafc;
            --text-body: #cbd5e1;
            --sidebar-bg: #0f172a;
            --sidebar-text: #f8fafc;
            --primary-btn: #16a34a;
            --primary-btn-hover: #15803d;
        }
    }

    .stApp { background-color: var(--bg-main) !important; }

    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] * { color: var(--sidebar-text) !important; }

    h1, h2, h3, h4 {
        color: var(--text-title) !important;
        font-weight: 700 !important;
    }

    p, span, label { color: var(--text-body); }

    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background-color: var(--card-bg) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        border: 1px solid var(--card-border) !important;
        margin-bottom: 12px !important;
    }

    div.stButton > button {
        background-color: var(--primary-btn) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
    }

    div.stButton > button:hover {
        background-color: var(--primary-btn-hover) !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- CLIENTE OPENAI ---
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
        CREATE TABLE IF NOT EXISTS sesiones (
            token TEXT PRIMARY KEY,
            usuario TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def encode_image_to_base64(image_pil):
    import io
    buffered = io.BytesIO()
    image_pil.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# --- PERSISTENCIA VÍA TOKEN EN URL Y SQLITE ---
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

# --- PANTALLA DE LOGIN ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("AGRO IA")
        st.caption("Plataforma de Diagnóstico y Monitoreo Agrícola")
        
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        with tab1:
            user_input = st.text_input("Usuario o Correo", key="l_user")
            pass_input = st.text_input("Contraseña", type="password", key="l_pass")
            if st.button("Ingresar", use_container_width=True):
                user, token, msj = autenticar_usuario(user_input, pass_input)
                if user:
                    st.session_state.autenticado = True
                    st.session_state.usuario = user[1]
                    st.session_state.nombre_completo = user[4] or user[1]
                    st.session_state.token = token
                    
                    st.query_params["session_token"] = token
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
    st.sidebar.title("AGRO IA")
    st.sidebar.caption(f"Usuario: {st.session_state.usuario}")
    st.sidebar.write("---")
    
    opcion = st.sidebar.radio(
        "Navegación",
        ["Inicio e Historial", "Detectar Plaga", "Asistente Virtual", "Mi Cuenta"]
    )

    # --- 1. INICIO E HISTORIAL ---
    if opcion == "Inicio e Historial":
        st.title(f"Bienvenido, {st.session_state.nombre_completo}")
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
        st.caption("Consulta dudas y dale seguimiento a tus conversaciones anteriores.")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT id, titulo FROM conversaciones WHERE usuario = ? ORDER BY id DESC", (st.session_state.usuario,))
        chats_existentes = cursor.fetchall()

        opciones_chat = ["+ Nueva Conversación"] + [f"Chat #{c[0]}: {c[1]}" for c in chats_existentes]
        chat_seleccionado = st.sidebar.selectbox("Historial de Conversaciones", opciones_chat)

        if chat_seleccionado == "+ Nueva Conversación":
            if "current_chat_id" in st.session_state:
                del st.session_state.current_chat_id
            st.session_state.messages = []
        else:
            chat_id = int(chat_seleccionado.split(":")[0].replace("Chat #", ""))
            if st.session_state.get("current_chat_id") != chat_id:
                st.session_state.current_chat_id = chat_id
                cursor.execute("SELECT rol, contenido FROM mensajes WHERE conversacion_id = ? ORDER BY id ASC", (chat_id,))
                mensajes_db = cursor.fetchall()
                st.session_state.messages = [{"role": m[0], "content": m[1]} for m in mensajes_db]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Escribe tu pregunta o seguimiento aquí..."):
            if "current_chat_id" not in st.session_state:
                titulo_chat = prompt[:30] + "..." if len(prompt) > 30 else prompt
                cursor.execute("INSERT INTO conversaciones (usuario, titulo) VALUES (?, ?)", (st.session_state.usuario, titulo_chat))
                conn.commit()
                st.session_state.current_chat_id = cursor.lastrowid

            st.session_state.messages.append({"role": "user", "content": prompt})
            cursor.execute("INSERT INTO mensajes (conversacion_id, rol, contenido) VALUES (?, ?, ?)", 
                           (st.session_state.current_chat_id, "user", prompt))
            conn.commit()

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
                        cursor.execute("INSERT INTO mensajes (conversacion_id, rol, contenido) VALUES (?, ?, ?)", 
                                       (st.session_state.current_chat_id, "assistant", text))
                        conn.commit()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("No hay API Key configurada.")
        
        conn.close()

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
                if "token" in st.session_state:
                    cerrar_sesion_db(st.session_state.token)
                
                st.session_state.autenticado = False
                st.session_state.usuario = ""
                st.session_state.nombre_completo = ""
                st.session_state.messages = []
                if "current_chat_id" in st.session_state:
                    del st.session_state.current_chat_id
                
                st.query_params.clear()
                st.rerun()