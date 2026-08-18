import streamlit as st
import numpy as np
import sqlite3
import pandas as pd
from PIL import Image, ImageOps
from datetime import datetime

# Importer el motor de inferencia ligero (ai-edge-litert)
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

# Función para cargar etiquetas/clases
@st.cache_data
def cargar_etiquetas():
    try:
        with open("labels.txt", "r", encoding="utf-8") as f:
            labels = [line.strip() for line in f.readlines()]
        return labels
    except Exception as e:
        return []

# Función para preprocesar la imagen sin Keras
def preparar_imagen(image):
    # Redimensionar la imagen a 224x224 (estándar Teachable Machine / TFLite)
    size = (224, 224)
    image_resized = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    
    # Convertir a array de NumPy
    image_array = np.asarray(image_resized, dtype=np.float32)
    
    # Normalizar la imagen: (-1 a 1)
    normalized_image_array = (image_array / 127.5) - 1.0
    
    # Añadir dimensión de lote (1, 224, 224, 3)
    data = np.expand_dims(normalized_image_array, axis=0)
    return data

# Función para realizar el análisis/predicción
def analizar_imagen(image):
    if not TFLITE_DISPONIBLE:
        raise Exception("No se encontró ningún motor de TFLite instalado.")
    
    # Cargar intérprete
    try:
        interpreter = Interpreter(model_path="model_unquant.tflite")
    except NameError:
        interpreter = tflite.Interpreter(model_path="model_unquant.tflite")
        
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Preparar imagen y ejecutar inferencia
    data = preparar_imagen(image)
    interpreter.set_tensor(input_details[0]['index'], data)
    interpreter.invoke()
    
    prediction = interpreter.get_tensor(output_details[0]['index'])[0]
    
    # Cargar etiquetas
    labels = cargar_etiquetas()
    index_max = np.argmax(prediction)
    confianza = float(prediction[index_max])
    
    etiqueta = labels[index_max] if labels else f"Clase {index_max}"
    
    # Limpiar número o índice inicial si las etiquetas vienen como "0 Nombre"
    if " " in etiqueta:
        etiqueta = etiqueta.split(" ", 1)[1]
        
    return etiqueta, confianza

# --- INTERFAZ STREAMLIT ---

st.sidebar.title("🌱 AGRO IA")
st.sidebar.caption("Detección Inteligente de Plagas")

opcion = st.sidebar.radio(
    "Navegación",
    ["🏠 Inicio", "📷 Detectar Plaga", "📜 Registro Histórico", "💡 Catálogo y Tratamientos", "👤 Mi Perfil"]
)

if "Detectar Plaga" in opcion:
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
                        
                        # Guardar opcionalmente en la base de datos SQLite
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
                            pass # Si la tabla historial aún no existe, no interrumpe la pantalla
                            
                    except Exception as e:
                        st.error(f"Error al analizar la imagen: {e}")
        else:
            st.info("Sube o captura una imagen para ver el diagnóstico.")

elif "Inicio" in opcion:
    st.title("Bienvenido a Agro IA 🌱")
    st.write("Selecciona **Detectar Plaga** en el menú lateral para iniciar un escaneo.")