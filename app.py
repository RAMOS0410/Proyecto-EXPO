import streamlit as st
import sqlite3
import hashlib
import os
import pandas as pd
import numpy as np
from PIL import Image, ImageOps
from google import genai
from google.genai import types

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

# Configuración inicial de la página
st.set_page_config(page_title="AGRO IA - Detección de Plagas", page_icon="🌱", layout="wide")

# Directorio para almacenar notas de voz
AUDIO_FOLDER = "audios_chat"
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #1e3a2b !important;
    }
    [data-testid="stSidebar"] * {
        color: #e0f2e9 !important;
    }
    div.stButton > button:first-child {
        background-color: #e63946;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #d62839;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            audio_path TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE BASE DE DATOS PARA CHAT ---
def guardar_mensaje_bd(usuario, role, content, audio_path=None):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chats (usuario, role, content, audio_path) VALUES (?, ?, ?, ?)",
            (usuario, role, content, audio_path)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error al guardar mensaje en BD: {e}")

def obtener_historial_chat_bd(usuario):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content, audio_path FROM chats WHERE usuario = ? ORDER BY fecha ASC",
            (usuario,)
        )
        filas = cursor.fetchall()
        conn.close()
        historial = []
        for role, content, audio_path in filas:
            historial.append({
                "role": role,
                "content": content,
                "audio_path": audio_path
            })
        return historial
    except Exception:
        return []

def borrar_historial_chat_bd(usuario):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chats WHERE usuario = ?", (usuario,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error al borrar el historial: {e}")
        return False

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

# --- PANTALLA DE AUTENTICACIÓN ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🌱 AGRO IA</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: #a3b18a;'>Sistema Inteligente de Detección de Plagas</h4>", unsafe_allow_html=True)
        st.write("---")
        
        tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
        
        with tab1:
            st.subheader("Ingreso al Sistema")
            user_input = st.text_input("Usuario o Correo Electrónico", key="login_u")
            pass_input = st.text_input("Contraseña", type="password", key="login_p")
            
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
            st.subheader("Crear una nueva cuenta")
            new_nombre = st.text_input("Nombre Completo", key="reg_n")
            new_user = st.text_input("Nombre de Usuario", key="reg_u")
            new_email = st.text_input("Correo Electrónico", key="reg_e")
            new_pass = st.text_input("Contraseña", type="password", key="reg_p")
            new_pass2 = st.text_input("Confirmar Contraseña", type="password", key="reg_p2")
            
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
    st.sidebar.caption("Detección Inteligente de Plagas")
    st.sidebar.write("---")
    
    opcion = st.sidebar.radio(
        "Navegación",
        ["🏠 Inicio", "📷 Detectar Plaga", "💬 Asistente Virtual", "📜 Registro Histórico", "💡 Catálogo y Tratamientos", "👤 Mi Perfil"]
    )
    
    st.sidebar.write("---")
    st.sidebar.markdown(f"👤 **Usuario:** {st.session_state.nombre_completo}")
    st.sidebar.markdown("Rol: Agricultor / Productor")
    st.sidebar.markdown("📍 Finca Central")
    st.sidebar.write("")
    
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario = ""
        st.session_state.nombre_completo = ""
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
        st.title(f"Bienvenido a Agro IA, {st.session_state.nombre_completo} 🌱")
        st.write("Selecciona **Detectar Plaga** en el menú lateral para iniciar un escaneo o **Asistente Virtual** para hacer consultas.")

    elif "Detectar Plaga" in opcion:
        st.title("📷 Escáner y Detección de Plagas")
        st.write("Captura una foto de la hoja o sube una imagen existente.")

        col1, col2 = st.columns([1, 1])

        with col1:
            origen = st.radio("Selecciona origen de la imagen:", ["Subir Archivo", "Usar Cámara"])
            cultivo = st.selectbox("Selecciona el tipo de cultivo:", ["Café", "Frijol", "Maíz", "Tomate", "Otro"])
            
            imagen_file = None
            if origen == "Subir Archivo":
                imagen_file = st.file_uploader("Formatos soportados: JPG, PNG", type=["jpg", "png", "jpeg"])
            else:
                imagen_file = st.camera_input("Toma una foto")

            if imagen_file is not None:
                img = Image.open(imagen_file).convert("RGB")
                st.image(img, caption="Imagen seleccionada", use_container_width=True)

        with col2:
            st.subheader("🔍 Diagnóstico de la IA")
            if imagen_file is not None:
                if st.button("📌 Analizar Foto con IA", use_container_width=True):
                    with st.spinner("Procesando imagen con la IA..."):
                        try:
                            diagnostico, confianza = procesar_e_inferir(img)
                            st.success(f"**Diagnóstico:** {diagnostico}")
                            st.info(f"**Confianza:** {confianza * 100:.2f}%")
                            
                            try:
                                conn = sqlite3.connect(DB_NAME)
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO historial (usuario, cultivo, diagnostico, confianza) VALUES (?, ?, ?, ?)",
                                               (st.session_state.usuario, cultivo, diagnostico, round(confianza * 100, 2)))
                                conn.commit()
                                conn.close()
                            except Exception:
                                pass
                        except Exception as e:
                            st.error(f"Error al analizar la imagen: {e}")
            else:
                st.info("Sube o toma una fotografía para ver los resultados.")

    # --- VISTA: ASISTENTE VIRTUAL ---
    elif "Asistente Virtual" in opcion:
        col_head, col_btn = st.columns([3, 1])
        with col_head:
            st.title("💬 Asistente Agrónomo Virtual")
        with col_btn:
            st.write("") # Espaciador para alinear el botón
            if st.button("🗑️ Borrar Chat", use_container_width=True):
                if borrar_historial_chat_bd(st.session_state.usuario):
                    st.success("Historial borrado.")
                    st.rerun()

        st.write("Hazle preguntas sobre tratamientos, dosis de fertilizantes, cuidados de tu cultivo o adjunta notas de voz.")

        if not client:
            st.warning("⚠️ La API Key de Gemini no está configurada en los Secrets de Streamlit. Por favor configúrala para habilitar el chat.")
        else:
            mensajes_bd = obtener_historial_chat_bd(st.session_state.usuario)

            for msg in mensajes_bd:
                with st.chat_message(msg["role"]):
                    if msg["content"]:
                        st.markdown(msg["content"])
                    if msg["audio_path"] and os.path.exists(msg["audio_path"]):
                        st.audio(msg["audio_path"])

            audio_file = st.file_uploader("🎤 Adjuntar nota de voz (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"], key="audio_uploader")
            prompt = st.chat_input("Escribe tu duda agrícola aquí...")

            if prompt or audio_file:
                audio_saved_path = None
                texto_a_enviar = prompt if prompt else "El usuario envió un mensaje de voz."

                if audio_file:
                    audio_saved_path = os.path.join(AUDIO_FOLDER, f"{st.session_state.usuario}_{audio_file.name}")
                    with open(audio_saved_path, "wb") as f:
                        f.write(audio_file.getbuffer())

                with st.chat_message("user"):
                    if prompt:
                        st.markdown(prompt)
                    if audio_saved_path:
                        st.audio(audio_saved_path)

                guardar_mensaje_bd(
                    usuario=st.session_state.usuario,
                    role="user",
                    content=prompt if prompt else "[Nota de voz adjunta]",
                    audio_path=audio_saved_path
                )

                with st.chat_message("assistant"):
                    with st.spinner("Pensando respuesta agrícola..."):
                        modelos_a_probar = ['gemini-2.0-flash', 'gemini-1.5-flash']
                        respuesta_exitosa = False

                        for nombre_modelo in modelos_a_probar:
                            try:
                                response = client.models.generate_content(
                                    model=nombre_modelo,
                                    contents=texto_a_enviar,
                                    config=types.GenerateContentConfig(
                                        system_instruction="""
                                        Eres AGRO IA, un experto agrónomo virtual especializado en agricultura, fertilización y plagas.
                                        Responde de manera clara, educada, concisa y práctica para agricultores.
                                        Si te hacen preguntas no relacionadas con la agricultura o ganadería, amablemente orienta al usuario hacia temas del campo.
                                        """
                                    )
                                )
                                st.markdown(response.text)
                                
                                guardar_mensaje_bd(
                                    usuario=st.session_state.usuario,
                                    role="assistant",
                                    content=response.text
                                )
                                respuesta_exitosa = True
                                break
                            except Exception:
                                continue

                        if not respuesta_exitosa:
                            st.error("Error al conectar con los modelos de Gemini. Verifica la validez de tu API Key.")

    elif "Registro Histórico" in opcion:
        st.title("📜 Registro Histórico")
        try:
            conn = sqlite3.connect(DB_NAME)
            df = pd.read_sql_query("SELECT cultivo, diagnostico, confianza, fecha FROM historial WHERE usuario = ? ORDER BY fecha DESC", conn, params=(st.session_state.usuario,))
            conn.close()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Aún no tienes escaneos registrados.")
        except Exception:
            st.info("No hay registros en el historial.")

    elif "Catálogo y Tratamientos" in opcion:
        st.title("💡 Catálogo y Tratamientos")
        st.write("Consulta recomendaciones sobre el cuidado de cultivos y tratamiento de plagas.")

    elif "Mi Perfil" in opcion:
        st.title("👤 Mi Perfil")
        st.write(f"**Nombre:** {st.session_state.nombre_completo}")
        st.write(f"**Usuario:** {st.session_state.usuario}")
        st.write("**Rol:** Agricultor / Productor")