import streamlit as st
import pandas as pd
import os

# Configuración de la página
st.set_page_config(page_title="Control de Operaciones", layout="wide")

# Directorio en GitHub donde están los archivos
GITHUB_DATA_DIR = "data"

@st.cache_data
def listar_archivos_github():
    """Simula o lista los archivos disponibles en la carpeta data del repositorio."""
    # Si usas una ruta local para pruebas o la carpeta data en el repo:
    if os.path.exists(GITHUB_DATA_DIR):
        return [f for f in os.listdir(GITHUB_DATA_DIR) if f.endswith(('.xlsx', '.xls', '.csv'))]
    return []

@st.cache_data
def cargar_archivo_individual(nombre_archivo):
    """Carga un archivo individual desde la carpeta de datos."""
    ruta = os.path.join(GITHUB_DATA_DIR, nombre_archivo)
    try:
        if nombre_archivo.endswith('.csv'):
            return pd.read_csv(ruta)
        else:
            return pd.read_excel(ruta)
    except Exception as e:
        st.error(f"Error al cargar {nombre_archivo}: {e}")
        return None

def buscar_alarma():
    archivos = listar_archivos_github()
    for f in archivos:
        if "alarma" in f.lower():
            return f
    return None

def buscar_vessel():
    archivos = listar_archivos_github()
    for f in archivos:
        if "vessel" in f.lower():
            return f
    return None

# ==========================================
# FUNCIÓN BLINDADA PARA VESSEL
# ==========================================
@st.cache_data(show_spinner=False)
def cargar_y_limpiar_vessel(nombre_archivo):
    df_v = cargar_archivo_individual(nombre_archivo)
    if df_v is not None:
        # 1. Ajuste de cabecera y filas (ajusta si tu archivo Vessel requiere otro índice)
        if len(df_v) > 4:
            df_v = df_v.iloc[4:].reset_index(drop=True)
            df_v.columns = df_v.iloc[0]
            df_v = df_v.iloc[1:].reset_index(drop=True)
            
        # Limpiar espacios en los nombres de las columnas
        df_v.columns = [str(col).strip() for col in df_v.columns]
        
        # Buscar la columna Phase de forma flexible
        col_phase = next((col for col in df_v.columns if col.lower() == "phase"), None)
        if col_phase:
            df_v = df_v[df_v[col_phase].astype(str).str.strip().str.lower() == "working"]
        else:
            st.warning(" No se encontró la columna 'Phase' en Vessel.")
            
        # Buscar la columna de la nave de forma flexible (incluye Vessel, Nave o Vessel Name)
        col_vessel = next((col for col in df_v.columns if col.lower() in ["vessel", "nave", "vessel name"]), None)
        if col_vessel:
            df_v = df_v[df_v[col_vessel].astype(str).str.strip().str.upper() != "GENERICA"]
            if col_vessel != "Vessel":
                df_v = df_v.rename(columns={col_vessel: "Vessel"})
        else:
            st.warning(" No se encontró la columna de naves en el archivo Vessel.")
            
        df_v = df_v.dropna(how="all")
        return df_v
    return None

# ==========================================
# INTERFAZ PRINCIPAL STREAMLIT
# ==========================================
st.title("Control de Operaciones - Automatización")

archivos_disponibles = listar_archivos_github()

if not archivos_disponibles:
    st.warning(f"No se encontraron archivos en la carpeta '{GITHUB_DATA_DIR}'.")
else:
    # Selector de archivos
    archivo_seleccionado = st.selectbox("Seleccione el archivo a visualizar:", archivos_disponibles)
    
    if archivo_seleccionado:
        df = cargar_archivo_individual(archivo_seleccionado)
        
        if df is not None:
            # ==========================================
            # LIMPIEZA DE ALARMA (Si es el archivo correspondiente)
            # ==========================================
            nombre_alarma = buscar_alarma()
            nombre_vessel = buscar_vessel()
            
            if nombre_alarma and archivo_seleccionado == nombre_alarma:
                if len(df) > 2:
                    df.columns = df.iloc[2]
                    df = df.iloc[3:].reset_index(drop=True)
                
                # Limpiar nombres de columnas de alarma
                df.columns = [str(col).strip() for col in df.columns]
                
                # Filtrar "Desconectado" en Estado Ctr
                if "Estado Ctr" in df.columns:
                    estado_limpio = df["Estado Ctr"].astype(str).str.strip()
                    df_alarma_filtrado = df[estado_limpio == "Desconectado"].copy()
                else:
                    df_alarma_filtrado = pd.DataFrame()
                    st.warning(" No se encontró la columna 'Estado Ctr' en el archivo de Alarma.")
                
                # Cruce automático con Vessel si hay datos filtrados
                if not df_alarma_filtrado.empty and nombre_vessel:
                    df_vessel = cargar_y_limpiar_vessel(nombre_vessel)
                    
                    if df_vessel is not None and not df_vessel.empty:
                        columna_alarma = "Nave"
                        columna_vessel = "Vessel"
                        
                        if columna_alarma in df_alarma_filtrado.columns and columna_vessel in df_vessel.columns:
                            df_resultado = pd.merge(
                                df_alarma_filtrado,
                                df_vessel,
                                left_on=columna_alarma,
                                right_on=columna_vessel,
                                how="left",
                                suffixes=('_alarma', '_vessel')
                            )
                            df = df_resultado
                            st.success(f" Visualización creada: Alarma (Desconectado) cruzado con {nombre_vessel}")
                        else:
                            st.warning(f" No se encontró la columna '{columna_alarma}' en Alarma o '{columna_vessel}' en Vessel.")
                    else:
                        st.warning(" El archivo Vessel quedó vacío después de los filtros.")
                else:
                    st.info("ℹ No hay registros con Estado 'Desconectado' para realizar el cruce.")
                    df = df_alarma_filtrado

            # Mostrar la tabla final resultante en la app
            st.dataframe(df)