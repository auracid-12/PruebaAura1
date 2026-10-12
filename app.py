import streamlit as st
import serial
import pandas as pd
import time

# Configuración de la página
st.set_page_config(page_title="Monitor Arduino", layout="wide")
st.title("Visualizador de Sensores Arduino")

# Variables de estado para controlar la lectura
if "leyendo" not in st.session_state:
    st.session_state.leyendo = False

# --- BARRA LATERAL: CONFIGURACIÓN ---
st.sidebar.header("Configuración de Conexión")
puerto = st.sidebar.text_input("Puerto Serial", value="COM3", help="Ejemplo: COM3 en Windows o /dev/ttyUSB0 en Linux/Mac")
baudrate = st.sidebar.selectbox("Baud Rate", [9600, 115200, 38400, 57600])

st.sidebar.header("Visualización")
# Opciones de sensores (asumiendo que el Arduino envía 3 valores separados por coma)
opciones_sensores = {"Sensor 1 (Columna 0)": 0, "Sensor 2 (Columna 1)": 1, "Sensor 3 (Columna 2)": 2}
sensor_seleccionado = st.sidebar.selectbox("Selecciona el sensor a graficar", list(opciones_sensores.keys()))
indice_sensor = opciones_sensores[sensor_seleccionado]

# Botones de control
col1, col2 = st.sidebar.columns(2)
if col1.button("Iniciar", type="primary"):
    st.session_state.leyendo = True
if col2.button("Detener"):
    st.session_state.leyendo = False

# --- ÁREA PRINCIPAL: LECTURA Y GRÁFICO ---
espacio_grafico = st.empty()
espacio_datos = st.empty()

if st.session_state.leyendo:
    try:
        # Abrir conexión serial
        ser = serial.Serial(puerto, baudrate, timeout=1)
        st.sidebar.success(f"Conectado a {puerto}")
        
        datos_historicos = []
        
        # Bucle de lectura
        while st.session_state.leyendo:
            if ser.in_waiting > 0:
                linea = ser.readline().decode('utf-8').strip()
                
                # Intentar procesar la línea como valores separados por coma
                try:
                    valores = [float(v) for v in linea.split(',')]
                    
                    if len(valores) > indice_sensor:
                        valor_actual = valores[indice_sensor]
                        datos_historicos.append(valor_actual)
                        
                        # Limitar el historial para que la gráfica no consuma toda la memoria
                        if len(datos_historicos) > 100:
                            datos_historicos.pop(0)
                        
                        # Actualizar la interfaz
                        df = pd.DataFrame(datos_historicos, columns=[sensor_seleccionado])
                        espacio_grafico.line_chart(df)
                        espacio_datos.metric(label=f"Lectura actual: {sensor_seleccionado}", value=f"{valor_actual:.2f}")
                        
                except ValueError:
                    # Ignorar líneas que no sean números (como encabezados o ruido serial)
                    pass
            
            # Pequeña pausa para no saturar el procesador
            time.sleep(0.05)
            
    except serial.SerialException as e:
        st.error(f"Error de conexión: No se pudo abrir el puerto {puerto}. Verifica que esté libre y conectado.")
        st.session_state.leyendo = False
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            st.sidebar.warning("Conexión cerrada.")
else:
    st.info("Configura el puerto y presiona 'Iniciar' para recibir datos.")
