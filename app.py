import streamlit as st
import sqlite3
import hashlib
import os
import pandas as pd
import numpy as np
from PIL import Image, ImageOps
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="AGRO IA - Detección de Plagas", 
    page_icon="🌱", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    :root {
        --bg-main: #f4f6f3;
        --card-bg: #ffffff;
        --card-border: #e2e8e0;
        --text-title: #344E41;
        --text-body: #2d3748;
        --text-muted: #6c757d;
        --sidebar-bg: #344E41;
        --sidebar-text: #f0f4f1;
        --primary-btn: #3A5A40;
        --primary-btn-hover: #588157;
        --input-bg: #ffffff;
        --input-text: #2d3748;
        --input-border: #dad7cd;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #121815;
            --card-bg: #1e2621;
            --card-border: #2d3831;
            --text-title: #e2ece9;
            --text-body: #d1d5db;
            --text-muted: #9ca3af;
            --sidebar-bg: #1a2820;
            --sidebar-text: #f0f4f1;
            --primary-btn: #3A5A40;
            --primary-btn-hover: #588157;
            --input-bg: #27332c;
            --input-text: #f3f4f6;
            --input-border: #3b4d42;
        }
    }

    .stApp {
        background-color: var(--bg-main) !important;
    }

    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] * {
        color: var(--sidebar-text) !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        padding: 10px 14px;
        border-radius: 10px;
        transition: background 0.2s ease;
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: #3a5a40 !important;
    }

    h1, h2, h3, h4 {
        color: var(--text-title) !important;
        font-weight: 700 !important;
    }

    p, span, label {
        color: var(--text-body);
    }

    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background-color: var(--card-bg) !important;
        border-radius: 16px !important;
        padding: 22px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid var(--card-border) !important;
        margin-bottom: 15px !important;
    }

    div.stButton > button {
        background-color: var(--primary-btn) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.65rem 1.4rem !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.3s ease !important;
    }

    div.stButton > button:hover {
        background-color: var(--primary-btn-hover) !important;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .stTextInput input, .stSelectbox > div > div {
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        border-radius: 10px !important;
        border: 1px solid var(--input-border) !important;
    }

    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 700;
        text-align: center;
    }
    .badge-high { background-color: #fee2e2; color: #991b1b; }
    .badge-medium { background-color: #fef3c7; color: #92400e; }
    .badge-low { background-color: #e0e7ff; color: #3730a3; }
    .badge-good { background-color: #d1fae5; color: #065f46; }

    .metric-card {
        background-color: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 18px;
        text-align: center;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 1.8rem;
        color: #3A5A40 !important;
    }
    .metric-card p {
        margin: 4px 0 0 0;
        font-size: 0.9rem;
        color: var(--text-muted);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        background-color: var(--card-bg);
        border-radius: 10px;
        color: var(--text-body);
        font-weight: 600;
        padding: 0 18px;
        border: 1px solid var(--card-border);
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--primary-btn) !important;
        color: #ffffff !important;
        border-color: var(--primary-btn) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- OBTENCIÓN DE API KEY ---
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

# --- INFERENCIA TFLITE ---
TFLITE_DISPONIBLE = False
try:
    from ai_edge_litert.interpreter import Interpreter
    TFLITE_DISPONIBLE = True
except ImportError:
    try:
        import tflite_runtime.interpreter as tflite
        TFLITE_DISPONIBLE = True
    except ImportError:
        try:
            import tensorflow.lite as tflite
            TFLITE_DISPONIBLE = True
        except ImportError:
            TFLITE_DISPONIBLE = False

DB_NAME = "agroia_v3.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre_completo TEXT,
            rol TEXT DEFAULT 'Agricultor / Productor'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            cultivo TEXT,
            diagnostico TEXT,
            confianza REAL,
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
        return True, "¡Usuario registrado exitosamente! Ya puedes iniciar sesión."
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "correo" in err_msg:
            return False, "El correo electrónico ya está registrado."
        return False, "El nombre de usuario ya existe."
    except Exception as e:
        return False, f"Error: {e}"

def autenticar_usuario(identificador, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        identificador_clean = identificador.strip().lower()
        pass_hash = hash_password(password)
        
        cursor.execute("""
            SELECT id, usuario, correo, password, nombre_completo, rol FROM usuarios 
            WHERE usuario = ? OR correo = ?
        """, (identificador_clean, identificador_clean))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return None, "El usuario o correo no existe."
        if user[3] == pass_hash:
            return user, "OK"
        else:
            return None, "Contraseña incorrecta."
            
    except Exception as e:
        return None, f"Error en BD: {e}"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "nombre_completo" not in st.session_state:
    st.session_state.nombre_completo = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- PANTALLA DE AUTENTICACIÓN ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>🌱 AGRO IA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: 500; margin-bottom: 25px;'>Inteligencia Artificial para el cuidado de tus cultivos</p>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab1:
            st.write("")
            user_input = st.text_input("Usuario o Correo Electrónico", key="login_u")
            pass_input = st.text_input("Contraseña", type="password", key="login_p")
            st.write("")
            
            if st.button("Iniciar Sesión", use_container_width=True):
                if user_input and pass_input:
                    user, msj = autenticar_usuario(user_input, pass_input)
                    if user:
                        st.session_state.autenticado = True
                        st.session_state.usuario = user[1]
                        st.session_state.nombre_completo = user[4] if len(user) > 4 and user[4] else user[1]
                        st.success("¡Bienvenido de nuevo!")
                        st.rerun()
                    else:
                        st.error(msj)
                else:
                    st.warning("Por favor completa todos los campos.")
                    
        with tab2:
            st.write("")
            new_nombre = st.text_input("Nombre Completo", key="reg_n")
            new_user = st.text_input("Nombre de Usuario", key="reg_u")
            new_email = st.text_input("Correo Electrónico", key="reg_e")
            new_pass = st.text_input("Contraseña", type="password", key="reg_p")
            new_pass2 = st.text_input("Confirmar Contraseña", type="password", key="reg_p2")
            st.write("")
            
            if st.button("Registrar Cuenta", use_container_width=True):
                if new_user and new_email and new_pass and new_nombre:
                    if "@" not in new_email or "." not in new_email:
                        st.error("Por favor ingresa un correo electrónico válido.")
                    elif new_pass != new_pass2:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        exito, msj = registrar_usuario(new_user, new_email, new_pass, new_nombre)
                        if exito:
                            st.success(msj)
                        else:
                            st.error(msj)
                else:
                    st.warning("Por favor completa todos los campos.")

# --- INTERFAZ PRINCIPAL ---
else:
    st.sidebar.markdown("# 🌱 AGRO IA")
    st.sidebar.caption("Monitoreo Inteligente de Cultivos")
    st.sidebar.write("---")
    
    opcion = st.sidebar.radio(
        "Navegación",
        ["Inicio", "Detectar Plaga", "Asistente Virtual", "Historial", "Catálogo y Tratamientos", "Mi Perfil"]
    )
    
    st.sidebar.write("---")
    st.sidebar.markdown(f"**Usuario:** {st.session_state.nombre_completo}")
    st.sidebar.markdown("**Rol:** Agricultor")
    st.sidebar.write("")
    
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario = ""
        st.session_state.nombre_completo = ""
        st.session_state.messages = []
        st.rerun()

    @st.cache_data
    def cargar_labels():
        try:
            with open("labels.txt", "r", encoding="utf-8") as f:
                return [line.strip() for line in f.readlines()]
        except Exception:
            return []

    def procesar_e_inferir(image):
        if not TFLITE_DISPONIBLE:
            raise Exception("No hay un motor TFLite configurado en el servidor.")
            
        try:
            interpreter = Interpreter(model_path="model_unquant.tflite")
        except NameError:
            interpreter = tflite.Interpreter(model_path="model_unquant.tflite")
            
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        size = (224, 224)
        image_resized = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
        image_array = np.asarray(image_resized, dtype=np.float32)
        normalized_image_array = (image_array / 127.5) - 1.0
        data = np.expand_dims(normalized_image_array, axis=0)
        
        interpreter.set_tensor(input_details[0]['index'], data)
        interpreter.invoke()
        
        predictions = interpreter.get_tensor(output_details[0]['index'])[0]
        max_idx = np.argmax(predictions)
        confianza = float(predictions[max_idx])
        
        labels = cargar_labels()
        if labels and max_idx < len(labels):
            diagnostico = labels[max_idx]
            if " " in diagnostico:
                diagnostico = diagnostico.split(" ", 1)[1]
        else:
            diagnostico = f"Clase {max_idx}"
            
        return diagnostico, confianza

    # --- VISTA: INICIO ---
    if "Inicio" in opcion:
        st.title(f"¡Hola, {st.session_state.nombre_completo}! 👋")
        st.write("Este es el estado de tus cultivos hoy.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div class="metric-card">
                <span class="badge badge-good">Óptimo</span>
                <h3>Todo va bien</h3>
                <p>3 cultivos monitoreados</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="metric-card">
                <span class="badge badge-low">Normal</span>
                <h3>0 Alertas</h3>
                <p>Sin plagas activas</p>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
            <div class="metric-card">
                <span class="badge badge-good">28°C</span>
                <h3>Clima Estable</h3>
                <p>Humedad del suelo: 72%</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("---")
        st.subheader("🌾 Cultivos Registrados")
        
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown("**🌽 Maíz**")
            st.markdown("Salud: <span class='badge badge-good'>Buena</span>", unsafe_allow_html=True)
        with col_c2:
            st.markdown("**🫘 Frijol**")
            st.markdown("Salud: <span class='badge badge-medium'>Regular</span>", unsafe_allow_html=True)
        with col_c3:
            st.markdown("**☕ Café**")
            st.markdown("Salud: <span class='badge badge-good'>Buena</span>", unsafe_allow_html=True)

    # --- VISTA: DETECTAR PLAGA ---
    elif "Detectar Plaga" in opcion:
        st.title("Nuevo Diagnóstico")
        st.write("Toma una foto o sube una imagen de tu cultivo para identificar posibles plagas.")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📷 Captura de Imagen")
            origen = st.radio("Origen de la imagen:", ["Subir Imagen", "Tomar Foto"])
            cultivo = st.selectbox("Selecciona el cultivo:", ["Café", "Frijol", "Maíz", "Tomate", "Otro"])
            
            imagen_file = None
            if origen == "Subir Imagen":
                imagen_file = st.file_uploader("Formatos permitidos: JPG, PNG", type=["jpg", "png", "jpeg"])
            else:
                imagen_file = st.camera_input("Capturar foto del cultivo")

            if imagen_file is not None:
                img = Image.open(imagen_file).convert("RGB")
                st.image(img, caption="Vista previa de la muestra", use_container_width=True)

        with col2:
            st.subheader("📋 Resultado del Análisis")
            if imagen_file is not None:
                if st.button("Analizar Hoja con IA", use_container_width=True):
                    with st.spinner("Procesando imagen..."):
                        try:
                            diagnostico, confianza = procesar_e_inferir(img)
                            confianza_pct = round(confianza * 100, 2)
                            
                            es_sana = "sana" in diagnostico.lower() or "healthy" in diagnostico.lower()
                            badge_html = "<span class='badge badge-good'>Saludable</span>" if es_sana else "<span class='badge badge-high'>Riesgo: Alto</span>"
                            
                            st.markdown(f"### {diagnostico} {badge_html}", unsafe_allow_html=True)
                            st.markdown(f"**Cultivo:** {cultivo}")
                            st.progress(confianza, text=f"Confianza del modelo: {confianza_pct}%")
                            
                            if es_sana:
                                st.success("La planta muestra signos de estar saludable.")
                            else:
                                st.warning("Recomendación: Aplicar tratamiento enfocado y mantener buena ventilación entre plantas.")
                            
                            try:
                                conn = sqlite3.connect(DB_NAME)
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO historial (usuario, cultivo, diagnostico, confianza) VALUES (?, ?, ?, ?)",
                                               (st.session_state.usuario, cultivo, diagnostico, confianza_pct))
                                conn.commit()
                                conn.close()
                            except Exception:
                                pass
                        except Exception as e:
                            st.error(f"Error durante el análisis: {e}")
            else:
                st.info("Sube o toma una foto en el panel izquierdo para obtener el diagnóstico.")

    # --- VISTA: ASISTENTE VIRTUAL ---
    elif "Asistente Virtual" in opcion:
        st.title("Asistente Agrónomo Virtual")
        st.write("Resuelve tus dudas sobre dosis, fertilizantes o control orgánico de plagas.")

        if not api_key:
            st.error("⚠️ No se detectó ninguna API Key. Agrégala en tu archivo `.streamlit/secrets.toml` o en la sección Secrets de Streamlit Cloud.")
        else:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Escribe tu consulta agrícola aquí..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Consultando información agronómica..."):
                        try:
                            ai_client = genai.Client(api_key=api_key)
                            response = ai_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=prompt,
                                config=types.GenerateContentConfig(
                                    system_instruction="Eres AGRO IA, un agrónomo virtual experto. Da respuestas concisas, prácticas y amables."
                                )
                            )
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            st.error(f"Error al comunicar con la API: {str(e)}")

    # --- VISTA: HISTORIAL ---
    elif "Historial" in opcion:
        st.title("Historial de Diagnósticos")
        try:
            conn = sqlite3.connect(DB_NAME)
            df = pd.read_sql_query("SELECT cultivo AS Cultivo, diagnostico AS Diagnostico, confianza AS Confianza_Pct, fecha AS Fecha FROM historial WHERE usuario = ? ORDER BY fecha DESC", conn, params=(st.session_state.usuario,))
            conn.close()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Aún no tienes análisis guardados.")
        except Exception:
            st.info("No hay registros en la base de datos.")

    # --- VISTA: CATÁLOGO Y TRATAMIENTOS ---
    elif "Catálogo y Tratamientos" in opcion:
        st.title("Tratamientos y Prevención")
        
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            st.markdown("### 🧪 Fungicidas Orgánicos")
            st.markdown("* **Oxicloruro de Cobre:** Control de roya y antracnosis.")
            st.markdown("* **Jabón Potásico:** Control de pulgón y araña roja.")
            st.markdown("* **Caldo Bordelés:** Excelente preventivo contra hongos.")
        with col_cat2:
            st.markdown("### 🛡️ Buenas Prácticas")
            st.markdown("* **Rotación:** Cambiar cultivos por temporada.")
            st.markdown("* **Podas sanitarias:** Retirar hojas enfermas a tiempo.")
            st.markdown("* **Ventilación:** Mantener suficiente distancia entre plantas.")

    # --- VISTA: MI PERFIL ---
    elif "Mi Perfil" in opcion:
        st.title("Mi Perfil")
        
        st.markdown(f"**Nombre:** {st.session_state.nombre_completo}")
        st.markdown(f"**Usuario:** {st.session_state.usuario}")
        st.markdown("**Rol:** Agricultor / Productor")
        st.markdown("**Estado:** <span class='badge badge-good'>Activo</span>", unsafe_allow_html=True)