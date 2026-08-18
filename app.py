import streamlit as st
import sqlite3
import hashlib
import os
import pandas as pd
import numpy as np
from PIL import Image, ImageOps

# --- CARGAR IA / INFERENCIA LIGERA ---
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

DB_NAME = "agroia_db.db"

# --- INICIALIZACIÓN Y REPARACIÓN AUTOMÁTICA DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verificar si la columna 'usuario' existe en la tabla actual
    try:
        cursor.execute("SELECT usuario FROM usuarios LIMIT 1")
    except sqlite3.OperationalError:
        # Si da error, significa que la tabla vieja no tiene la columna 'usuario'
        # Reconstruimos la tabla con el formato correcto
        cursor.execute("DROP TABLE IF EXISTS usuarios")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
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

def registrar_usuario(usuario, password, nombre):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario, password, nombre_completo) VALUES (?, ?, ?)",
                       (usuario, hash_password(password), nombre))
        conn.commit()
        conn.close()
        return True, "¡Usuario registrado exitosamente! Ya puedes iniciar sesión."
    except sqlite3.IntegrityError:
        return False, "El nombre de usuario ya existe."
    except Exception as e:
        return False, f"Error: {e}"

def autenticar_usuario(usuario, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND password = ?", 
                       (usuario, hash_password(password)))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception:
        return None

# Estado de la sesión
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "nombre_completo" not in st.session_state:
    st.session_state.nombre_completo = ""

# --- PANTALLA DE AUTENTICACIÓN (LOGIN Y REGISTRO) ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🌱 AGRO IA</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: gray;'>Sistema Inteligente de Detección de Plagas</h4>", unsafe_allow_html=True)
        st.write("---")
        
        tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
        
        with tab1:
            st.subheader("Ingreso al Sistema")
            user_input = st.text_input("Usuario / Correo", key="login_u")
            pass_input = st.text_input("Contraseña", type="password", key="login_p")
            
            if st.button("Iniciar Sesión", use_container_width=True, type="primary"):
                if user_input and pass_input:
                    user = autenticar_usuario(user_input, pass_input)
                    if user:
                        st.session_state.autenticado = True
                        st.session_state.usuario = user[1]
                        st.session_state.nombre_completo = user[3] if len(user) > 3 and user[3] else user[1]
                        st.success("¡Bienvenido!")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
                else:
                    st.warning("Por favor completa todos los campos.")
                    
        with tab2:
            st.subheader("Crear una nueva cuenta")
            new_nombre = st.text_input("Nombre Completo", key="reg_n")
            new_user = st.text_input("Nombre de Usuario", key="reg_u")
            new_pass = st.text_input("Contraseña", type="password", key="reg_p")
            new_pass2 = st.text_input("Confirmar Contraseña", type="password", key="reg_p2")
            
            if st.button("Registrar Cuenta", use_container_width=True):
                if new_user and new_pass and new_nombre:
                    if new_pass != new_pass2:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        exito, msj = registrar_usuario(new_user, new_pass, new_nombre)
                        if exito:
                            st.success(msj)
                        else:
                            st.error(msj)
                else:
                    st.warning("Por favor completa todos los campos.")

# --- INTERFAZ PRINCIPAL CON MENÚ LATERAL ---
else:
    st.sidebar.title("🌱 AGRO IA")
    st.sidebar.caption("Detección Inteligente de Plagas")
    st.sidebar.write("---")
    
    opcion = st.sidebar.radio(
        "Navegación",
        ["🏠 Inicio", "📷 Detectar Plaga", "📜 Registro Histórico", "💡 Catálogo y Tratamientos", "👤 Mi Perfil"]
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

    # --- LÓGICA DE PROCESAMIENTO IA ---
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
        
        # Preprocesar imagen
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

    # --- VISTAS DEL SISTEMA ---
    if "Inicio" in opcion:
        st.title(f"Bienvenido a Agro IA, {st.session_state.nombre_completo} 🌱")
        st.write("Selecciona **Detectar Plaga** en el menú lateral para iniciar un escaneo.")

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
                if st.button("🚀 Analizar Foto con IA", use_container_width=True, type="primary"):
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

    elif "Registro Histórico" in opcion:
        st.title("📜 Registro Histórico")
        st.write("Historial de escaneos guardados:")
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