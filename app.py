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

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    /* Reset global y tipografía */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4, .login-title {
        font-family: 'Poppins', sans-serif !important;
    }

    /* FORZAR VISTA CLARA GLOBAL (Anula el tema oscuro del navegador) */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #f4f7f4 !important;
        color: #1f2d24 !important;
    }

    /* SIDEBAR VERDE BOSQUE ROBUSTO */
    [data-testid="stSidebar"] {
        background-color: #1a4332 !important;
        padding-top: 1.5rem;
    }

    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { 
        color: #ffffff !important; 
    }

    [data-testid="stSidebar"] .stCaption {
        color: #a3c1b2 !important;
    }

    /* BOTONES DE NAVEGACIÓN EN EL SIDEBAR (Visibilidad del texto garantizada) */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 8px !important;
        display: flex !important;
        flex-direction: column !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.18) !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background-color: #2d6a4f !important;
        border: 1px solid #4ade80 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
    }

    /* Asegurar visibilidad completa del texto en la navegación */
    [data-testid="stSidebar"] div[role="radiogroup"] label * {
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    /* CONTENIDO PRINCIPAL: TÍTULOS Y TEXTO */
    .main h1, .main h2, .main h3, .main h4 {
        color: #1a4332 !important;
        font-weight: 700 !important;
    }

    .main p, .main span, .main label {
        color: #2d3748 !important;
    }

    /* TARJETAS BLANCAS Y LIMPIAS */
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        padding: 24px !important;
        border: 1px solid #e2e8e3 !important;
        margin-bottom: 16px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }

    /* ALERTAS DE INFORMACIÓN (MODIFICADAS A BLANCO/VERDE) */
    div[data-testid="stNotification"] {
        background-color: #ffffff !important;
        color: #1a4332 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }

    /* BOTONES PRINCIPALES */
    div.stButton > button {
        background-color: #2d6a4f !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 15px !important;
        box-shadow: 0 4px 10px rgba(45, 106, 79, 0.2);
    }

    div.stButton > button:hover {
        background-color: #1e4b38 !important;
    }

    /* LOGIN CARD */
    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 75vh;
    }

    .login-card {
        background: #ffffff !important;
        border: 1px solid #e2e8e3 !important;
        border-radius: 16px;
        padding: 36px;
        width: 100%;
        max-width: 420px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
    }

    .login-icon { font-size: 48px; text-align: center; margin-bottom: 4px; }
    .login-title { text-align: center; font-size: 28px; font-weight: 800; color: #1a4332 !important; }
    .login-caption { text-align: center; color: #64748b !important; font-size: 13px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

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
        metaTheme.content = '#1a4332';
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

raw_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
api_key = str(raw_key).strip().strip('"').strip("'")
client = OpenAI(api_key=api_key) if api_key else None

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

def preparar_imagen(image_pil, max_dim=1024, calidad=85):
    imagen = image_pil.convert("RGB")
    imagen.thumbnail((max_dim, max_dim), Image.LANCZOS)
    return imagen

def encode_image_to_base64(image_pil):
    buffered = io.BytesIO()
    image_pil.save(buffered, format="JPEG", quality=85, optimize=True)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

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

if not st.session_state.autenticado:
    try_restore_from_local_storage()

    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="login-icon">🌿</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-title">AGRO IA</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-caption">Plataforma de Diagnóstico y Monitoreo Agrícola</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        with tab1:
            user_input = st.text_input("Usuario o Correo", key="l_user")
            pass_input = st.text_input("Contraseña", type="password", key="l_pass")
            if st.button("Ingresar", use_container_width=True, key="btn_login"):
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
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.sidebar.title("AGRO IA")
    st.sidebar.caption(f"Usuario: {st.session_state.usuario}")
    st.sidebar.write("---")

    opcion_mostrada = st.sidebar.radio(
        "Navegación",
        ["🏠 Inicio e Historial", "🐛 Detectar Plaga", "🤖 Asistente Virtual", "👤 Mi Cuenta"],
        label_visibility="collapsed"
    )
    
    opcion = opcion_mostrada.split(" ", 1)[1] if " " in opcion_mostrada else opcion_mostrada

    if "Inicio" in opcion:
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

    elif "Detectar" in opcion:
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

            img = None
            if imagen_file:
                img = preparar_imagen(Image.open(imagen_file))
                st.image(img, caption="Muestra cargada", use_container_width=True)

        with col2:
            st.subheader("Informe del Diagnóstico")
            if imagen_file and img is not None:
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
                                    model="gpt-4o",
                                    messages=[{
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": prompt_analisis},
                                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                        ]
                                    }],
                                    max_tokens=1200
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

    elif "Asistente" in opcion:
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
                            model="gpt-4o",
                            messages=history,
                            max_tokens=1000
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

    elif "Cuenta" in opcion:
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

                clear_local_storage_token()

                st.session_state.autenticado = False
                st.session_state.usuario = ""
                st.session_state.nombre_completo = ""
                st.session_state.messages = []
                if "current_chat_id" in st.session_state:
                    del st.session_state.current_chat_id

                st.query_params.clear()
                st.rerun()