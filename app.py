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

# --- ESTILOS CSS PERSONALIZADOS (PALETA AGRO IA) ---
st.markdown("""
    <style>
    /* Importar fuente */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fondo principal de la aplicación */
    .stApp {
        background-color: #f4f6f3;
    }

    /* Sidebar Lateral Verde Oscuro (#344E41) */
    [data-testid="stSidebar"] {
        background-color: #344E41 !important;
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] * {
        color: #f0f4f1 !important;
    }

    /* Opciones del menú de radio en el sidebar */
    [data-testid="stSidebar"] .stRadio label {
        padding: 8px 12px;
        border-radius: 8px;
        transition: background 0.2s ease;
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: #3a5a40;
    }

    /* Estilo de Botones Generales */
    div.stButton > button {
        background-color: #3A5A40 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        transition: all 0.3s ease !important;
    }

    div.stButton > button:hover {
        background-color: #588157 !important;
        color: #ffffff !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.12);
    }

    /* Botón Secundario / Salir */
    div.stButton > button[kind="secondary"] {
        background-color: #e63946 !important;
    }

    /* Tarjetas/Contenedores en fondo blanco */
    [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8e0;
        margin-bottom: 15px;
    }

    /* Estilo para los inputs de texto y selectores */
    .stTextInput > div > div > input, .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 1px solid #dad7cd !important;
        background-color: #fdfdfd !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #3A5A40 !important;
        box-shadow: 0 0 0 1px #3A5A40 !important;
    }

    /* Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #e9ece8;
        border-radius: 8px;
        color: #344e41;
        font-weight: 600;
        padding: 0 20px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #3A5A40 !important;
        color: #ffffff !important;
    }

    /* Títulos e Encabezados */
    h1, h2, h3 {
        color: #344E41 !important;
        font-weight: 700 !important;
    }

    /* Mensajes de Estado */
    .stAlert {
        border-radius: 10px;
    }

    /* Carga de Archivo (Uploader) */
    [data-testid="stFileUploader"] {
        background-color: #fafbfa;
        border: 2px dashed #a3b18a;
        border-radius: 12px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE GEMINI IA ---
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

# --- CARGAR IA / INFERENCIA LIGERA TFLITE ---
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

# --- INICIALIZACIÓN DE LA BASE DE DATOS ---
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

# Estado de la sesión
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
        st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>AGRO IA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #588157; font-weight: 600; margin-bottom: 25px;'>Inteligencia Artificial para el cuidado de tus cultivos</p>", unsafe_allow_html=True)
        
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
                        st.success("¡Bienvenido!")
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
    st.sidebar.markdown("# AGRO IA")
    st.sidebar.caption("Inteligencia Artificial para tus cultivos")
    st.sidebar.write("---")
    
    opcion = st.sidebar.radio(
        "Navegación",
        ["Inicio", "Detectar Plaga", "Asistente Virtual", "Registro Histórico", "Catálogo y Tratamientos", "Mi Perfil"]
    )
    
    st.sidebar.write("---")
    st.sidebar.markdown(f"**Usuario:** {st.session_state.nombre_completo}")
    st.sidebar.markdown("**Rol:** Agricultor / Productor")
    st.sidebar.markdown("**Ubicación:** Finca Central")
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
            raise Exception("No hay un motor TFLite configurado.")
            
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

    # --- VISTAS ---
    if "Inicio" in opcion:
        st.title(f"¡Hola, {st.session_state.nombre_completo}!")
        st.write("Este es el estado de tus cultivos y las herramientas disponibles para hoy.")
        
        # Tarjetas resumen tipo Dashboard
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric(label="Estado General", value="Saludable", delta="Todo en orden")
        with col_b:
            st.metric(label="Cultivos Monitoreados", value="3", delta="Maíz, Frijol, Café")
        with col_c:
            st.metric(label="Alertas Activas", value="0", delta="-1 esta semana")

        st.write("---")
        st.subheader("Acciones Rápidas")
        st.write("Selecciona **Detectar Plaga** en el menú lateral para iniciar un escaneo o consulta con nuestro **Asistente Virtual**.")

    elif "Detectar Plaga" in opcion:
        st.title("Diagnóstico por Imagen")
        st.write("Toma una foto o sube una imagen para identificar la especie y diagnosticar posibles plagas.")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("1. Captura de Imagen")
            origen = st.radio("Selecciona origen de la imagen:", ["Subir Archivo", "Usar Cámara"])
            cultivo = st.selectbox("Selecciona el tipo de cultivo:", ["Café", "Frijol", "Maíz", "Tomate", "Otro"])
            
            imagen_file = None
            if origen == "Subir Archivo":
                imagen_file = st.file_uploader("Formatos soportados: JPG, PNG", type=["jpg", "png", "jpeg"])
            else:
                imagen_file = st.camera_input("Toma una foto")

            if imagen_file is not None:
                img = Image.open(imagen_file).convert("RGB")
                st.image(img, caption="Vista previa de la hoja", use_container_width=True)

        with col2:
            st.subheader("2. Resultado del Análisis")
            if imagen_file is not None:
                if st.button("Analizar Hoja con IA", use_container_width=True):
                    with st.spinner("Analizando la imagen..."):
                        try:
                            diagnostico, confianza = procesar_e_inferir(img)
                            
                            st.markdown(f"### Cultivo: **{cultivo}**")
                            st.markdown(f"**Diagnóstico Detectado:** `{diagnostico}`")
                            
                            confianza_pct = round(confianza * 100, 2)
                            st.progress(confianza, text=f"Confianza del modelo: {confianza_pct}%")
                            
                            if "sana" in diagnostico.lower() or "healthy" in diagnostico.lower():
                                st.success("La planta muestra signos de estar saludable.")
                            else:
                                st.warning("Se han detectado patologías o anomalías en la muestra.")
                            
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
                            st.error(f"Error al analizar la imagen: {e}")
            else:
                st.info("Sube o captura una foto en el panel izquierdo para desplegar los resultados aquí.")

    elif "Asistente Virtual" in opcion:
        st.title("Asistente Agrónomo Virtual")
        st.write("Consulta dudas sobre dosificación, fertilizantes, medidas preventivas o tratamientos de campo.")

        if not client:
            st.warning("La API Key de Gemini no está configurada en los Secrets de Streamlit. Por favor configúrala para habilitar el chat.")
        else:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Escribe tu duda agrícola aquí (ej. ¿Cómo controlar la roya del café?):"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Consultando información agronómica..."):
                        modelos_a_probar = ['gemini-3.6-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']
                        respuesta_exitosa = False

                        for nombre_modelo in modelos_a_probar:
                            try:
                                response = client.models.generate_content(
                                    model=nombre_modelo,
                                    contents=prompt,
                                    config=types.GenerateContentConfig(
                                        system_instruction="""
                                        Eres AGRO IA, un experto agrónomo virtual especializado en agricultura, fertilización y plagas.
                                        Responde de manera clara, educada, concisa y práctica para agricultores.
                                        Si te hacen preguntas no relacionadas con la agricultura o ganadería, amablemente orienta al usuario hacia temas del campo.
                                        """
                                    )
                                )
                                st.markdown(response.text)
                                st.session_state.messages.append({"role": "assistant", "content": response.text})
                                respuesta_exitosa = True
                                break
                            except Exception:
                                continue

                        if not respuesta_exitosa:
                            st.error("Error al conectar con los modelos de Gemini. Verifica la validez de tu API Key.")

    elif "Registro Histórico" in opcion:
        st.title("Historial de Diagnósticos")
        try:
            conn = sqlite3.connect(DB_NAME)
            df = pd.read_sql_query("SELECT cultivo AS Cultivo, diagnostico AS Diagnostico, confianza AS Confianza_Pct, fecha AS Fecha FROM historial WHERE usuario = ? ORDER BY fecha DESC", conn, params=(st.session_state.usuario,))
            conn.close()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Aún no tienes registros guardados en tu historial.")
        except Exception:
            st.info("No hay registros en la base de datos.")

    elif "Catálogo y Tratamientos" in opcion:
        st.title("Catálogo de Tratamientos")
        st.write("Guía rápida de recomendaciones agronómicas y buenas prácticas de cultivo.")
        
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            st.markdown("### Fungicidas Orgánicos")
            st.markdown("* **Oxicloruro de Cobre:** Ideal para el control de roya y antracnosis.")
            st.markdown("* **Jabón Potásico:** Recomendado para eliminación de pulgones y araña roja.")
        with col_cat2:
            st.markdown("### Buenas Prácticas")
            st.markdown("* Mapeo periódico y rotación de cultivos.")
            st.markdown("* Podas sanitarias para mantener la ventilación entre follajes.")

    elif "Mi Perfil" in opcion:
        st.title("Mi Perfil de Usuario")
        st.markdown(f"**Nombre Completo:** {st.session_state.nombre_completo}")
        st.markdown(f"**Usuario:** {st.session_state.usuario}")
        st.markdown("**Rol Asignado:** Agricultor / Productor")
        st.markdown("**Estado de Cuenta:** Activa")