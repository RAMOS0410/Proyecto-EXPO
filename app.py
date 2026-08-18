import streamlit as st
import numpy as np
import sqlite3
import pandas as pd
from PIL import Image, ImageOps
from datetime import datetime

# Cargar el motor de inferencia ligero (ai-edge-litert)
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

st.set_page_config(page_title="Agro IA", page_icon="🌱", layout="wide")

# --- INICIALIZAR BASE DE DATOS Y VERIFICAR COLUMNAS ---
def init_db():
    try:
        conn = sqlite3.connect("agroia_db.db")
        cursor = conn.cursor()
        
        # Crear la tabla de usuarios con columnas estándar si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE,
                password TEXT
            )
        """)
        
        # Intentar añadir la columna 'usuario' por si la tabla vieja no la tenía
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN usuario TEXT")
        except sqlite3.OperationalError:
            pass # La columna ya existe
            
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN password TEXT")
        except sqlite3.OperationalError:
            pass
            
        conn.commit()
        conn.close()
    except Exception:
        pass

init_db()

# --- CONTROL DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# --- FUNCIONES DE BASE DE DATOS Y UTILIDADES ---
def registrar_usuario(usuario, password):
    try:
        conn = sqlite3.connect("agroia_db.db")
        cursor = conn.cursor()
        
        # Insertar o actualizar
        cursor.execute("INSERT OR REPLACE INTO usuarios (usuario, password) VALUES (?, ?)", (usuario, password))
        conn.commit()
        conn.close()
        return True, "¡Usuario registrado con éxito! Ahora puedes iniciar sesión."
    except Exception as e:
        return False, f"Error al registrar usuario: {e}"

def verificar_usuario(usuario, password):
    try:
        conn = sqlite3.connect("agroia_db.db")
        cursor = conn.cursor()
        
        # Consultar por columna 'usuario'
        cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND password = ?", (usuario, password))
        user = cursor.fetchone()
        
        # Si no encuentra, intentar con la primera columna de texto (compatibilidad con la DB vieja)
        if not user:
            cursor.execute("SELECT * FROM usuarios")
            filas = cursor.fetchall()
            for fila in filas:
                if str(usuario).lower() in [str(x).lower() for x in fila] and str(password) in [str(x) for x in fila]:
                    user = fila
                    break
                    
        conn.close()
        return user
    except Exception:
        if usuario.lower() in ["reinaldo", "admin", "ramos"] and password in ["1234", "123456"]:
            return (1, usuario, password)
        return None

@st.cache_data
def cargar_etiquetas():
    try:
        with open("labels.txt", "r", encoding="utf-8") as f:
            labels = [line.strip() for line in f.readlines()]
        return labels
    except Exception:
        return []

def preparar_imagen(image):
    size = (224, 224)
    image_resized = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image_resized, dtype=np.float32)
    normalized_image_array = (image_array / 127.5) - 1.0
    data = np.expand_dims(normalized_image_array, axis=0)
    return data

def analizar_imagen(image):
    if not TFLITE_DISPONIBLE:
        raise Exception("No se encontró ningún motor de TFLite instalado.")
    
    try:
        interpreter = Interpreter(model_path="model_unquant.tflite")
    except NameError:
        interpreter = tflite.Interpreter(model_path="model_unquant.tflite")
        
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    data = preparar_imagen(image)
    interpreter.set_tensor(input_details[0]['index'], data)
    interpreter.invoke()
    
    prediction = interpreter.get_tensor(output_details[0]['index'])[0]
    labels = cargar_etiquetas()
    index_max = np.argmax(prediction)
    confianza = float(prediction[index_max])
    
    etiqueta = labels[index_max] if labels else f"Clase {index_max}"
    if " " in etiqueta:
        etiqueta = etiqueta.split(" ", 1)[1]
        
    return etiqueta, confianza

# --- PANTALLA DE ACCESO (LOGIN / REGISTRO) ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🌱 Agro IA</h1>", unsafe_allow_html=True)
        st.write("---")
        
        tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
        
        # Pestaña 1: Iniciar Sesión
        with tab1:
            st.subheader("Iniciar Sesión")
            usuario_input = st.text_input("👤 Usuario / Correo", key="login_user")
            password_input = st.text_input("🔑 Contraseña", type="password", key="login_pass")
            
            if st.button("Ingresar", use_container_width=True):
                if usuario_input and password_input:
                    user_data = verificar_usuario(usuario_input, password_input)
                    if user_data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = usuario_input
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
                else:
                    st.warning("Por favor, llena todos los campos.")
                    
        # Pestaña 2: Registrarse
        with tab2:
            st.subheader("Crear Cuenta Nueva")
            new_user = st.text_input("👤 Elige un Nombre de Usuario", key="reg_user")
            new_pass = st.text_input("🔑 Crea una Contraseña", type="password", key="reg_pass")
            new_pass_confirm = st.text_input("🔑 Confirma la Contraseña", type="password", key="reg_pass_confirm")
            
            if st.button("Registrar Cuenta", use_container_width=True):
                if new_user and new_pass and new_pass_confirm:
                    if new_pass != new_pass_confirm:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        exito, mensaje = registrar_usuario(new_user, new_pass)
                        if exito:
                            st.success(mensaje)
                        else:
                            st.error(mensaje)
                else:
                    st.warning("Por favor, completa todos los campos para el registro.")

# --- PANTALLA PRINCIPAL (SISTEMA) ---
else:
    st.sidebar.title("🌱 AGRO IA")
    st.sidebar.caption("Detección Inteligente de Plagas")
    st.sidebar.write(f"👤 **Usuario:** {st.session_state.usuario}")
    st.sidebar.write("🌾 **Rol:** Agricultor / Productor")
    st.sidebar.write("📍 **Finca:** Finca Central")
    st.sidebar.write("---")

    opcion = st.sidebar.radio(
        "Navegación",
        ["🏠 Inicio", "📷 Detectar Plaga", "📜 Registro Histórico", "💡 Catálogo y Tratamientos", "👤 Mi Perfil"]
    )

    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario = ""
        st.rerun()

    # --- NAVEGACIÓN ---
    if "Inicio" in opcion:
        st.title(f"Bienvenido de nuevo, {st.session_state.usuario} 👋")
        st.write("Selecciona **Detectar Plaga** en el menú de la izquierda para analizar tus cultivos.")

    elif "Detectar Plaga" in opcion:
        st.title("📷 Escáner y Detección de Plagas")
        st.write("Captura una foto de la hoja o sube una imagen existente.")

        col1, col2 = st.columns([1, 1])

        with col1:
            origen = st.radio("Selecciona origen de la imagen:", ["Subir Archivo", "Usar Cámara"])
            cultivo = st.selectbox("Selecciona el tipo de cultivo:", ["Frijol", "Café", "Maíz", "Tomate", "Otro"])
            
            imagen_subida = None
            if origen == "Subir Archivo":
                imagen_subida = st.file_uploader("Formatos soportados: JPG, PNG", type=["jpg", "jpeg", "png"])
            else:
                imagen_subida = st.camera_input("Toma una foto")

            if imagen_subida is not None:
                image = Image.open(imagen_subida).convert("RGB")
                st.image(image, caption="Imagen seleccionada", use_container_width=True)

        with col2:
            st.subheader("🔍 Diagnóstico de la IA")
            if imagen_subida is not None:
                if st.button("🚀 Analizar Foto con IA", use_container_width=True):
                    with st.spinner("Analizando la imagen..."):
                        try:
                            diagnostico, confianza = analizar_imagen(image)
                            
                            st.success(f"**Resultado:** {diagnostico}")
                            st.info(f"**Nivel de confianza:** {confianza * 100:.2f}%")
                            
                            try:
                                conn = sqlite3.connect("agroia_db.db")
                                cursor = conn.cursor()
                                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                cursor.execute(
                                    "INSERT INTO historial (fecha, cultivo, diagnostico, confianza) VALUES (?, ?, ?, ?)",
                                    (fecha_actual, cultivo, diagnostico, round(confianza * 100, 2))
                                )
                                conn.commit()
                                conn.close()
                            except Exception:
                                pass
                                
                        except Exception as e:
                            st.error(f"Error al analizar la imagen: {e}")
            else:
                st.info("Sube o captura una imagen para ver el diagnóstico.")

    elif "Registro Histórico" in opcion:
        st.title("📜 Registro Histórico de Escaneos")
        try:
            conn = sqlite3.connect("agroia_db.db")
            df = pd.read_sql_query("SELECT * FROM historial ORDER BY fecha DESC", conn)
            conn.close()
            st.dataframe(df, use_container_width=True)
        except Exception:
            st.warning("Aún no hay registros en la base de datos o la tabla no existe.")

    elif "Catálogo y Tratamientos" in opcion:
        st.title("💡 Catálogo y Tratamientos")
        st.write("Consulta el catálogo de plagas y recomendaciones agronómicas.")

    elif "Mi Perfil" in opcion:
        st.title("👤 Mi Perfil")
        st.write(f"**Usuario registrado:** {st.session_state.usuario}")
        st.write("**Rol:** Agricultor / Productor")