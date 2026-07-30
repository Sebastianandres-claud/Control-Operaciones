import io
import pandas as pd
import requests
import streamlit as st

st.title("Control Operaciones")


# Función para listar los archivos de la carpeta en GitHub
@st.cache_data
def obtener_lista_archivos():
  api_url = "https://api.github.com/repos/Sebastianandres-claud/Control-Operaciones/contents/data"
  response = requests.get(api_url)
  if response.status_code == 200:
    return [
        f["name"]
        for f in response.json()
        if f["name"].endswith(".xlsx") or f["name"].endswith(".xls")
    ]
  return []


# Función para cargar un archivo específico en base a su nombre
@st.cache_data
def cargar_archivo_individual(nombre_archivo):
  url = f"https://raw.githubusercontent.com/Sebastianandres-claud/Control-Operaciones/main/data/{nombre_archivo}"
  response = requests.get(url)
  if response.status_code == 200:
    return pd.read_excel(io.BytesIO(response.content))
  return None

@st.cache_data
def cargar_y_limpiar_vessel(nombre_archivo):
    df_v = cargar_archivo_individual(nombre_archivo)
    if df_v is not None:
        # 1. Ajuste de cabecera y filas
        if len(df_v) > 4:
            df_v = df_v.iloc[4:].reset_index(drop=True)
            df_v.columns = df_v.iloc[0]
            df_v = df_v.iloc[1:].reset_index(drop=True)
            
        # Limpiar nombres de columnas (quitar espacios extra)
        df_v.columns = [str(col).strip() for col in df_v.columns]
        
        # Buscar la columna Phase de forma flexible
        col_phase = next((col for col in df_v.columns if col.lower() == "phase"), None)
        if col_phase:
            df_v = df_v[df_v[col_phase].astype(str).str.strip().str.lower() == "working"]
        else:
            st.warning(" No se encontró la columna 'Phase' en Vessel.")
            
        # Buscar la columna de la nave de forma flexible (incluyendo "Vessel Name")
        col_vessel = next((col for col in df_v.columns if col.lower() in ["vessel", "nave", "vessel name"]), None)
        if col_vessel:
            df_v = df_v[df_v[col_vessel].astype(str).str.strip().str.upper() != "GENERICA"]
            # Renombramos la columna encontrada a "Vessel" para que coincida perfectamente con el cruce
            if col_vessel != "Vessel":
                df_v = df_v.rename(columns={col_vessel: "Vessel"})
        else:
            st.warning(" No se encontró la columna de naves en el archivo Vessel.")
            
        df_v = df_v.dropna(how="all")
        return df_v
    return None

# Funciones para búsqueda automática
def buscar_vessel():
  return next(
      (f for f in archivos_disponibles if f.lower().startswith("vessel")), None
  )


def buscar_alarma():
  return next(
      (f for f in archivos_disponibles if f.lower().startswith("alarma")), None
  )


# Obtener la lista de archivos disponibles en la nube
archivos_disponibles = obtener_lista_archivos()

if archivos_disponibles:
  archivo_seleccionado = st.selectbox(
      "Selecciona el archivo que deseas analizar:", archivos_disponibles
  )

  if archivo_seleccionado:
    df = cargar_archivo_individual(archivo_seleccionado)

    # ==========================================
    # ZONA DE LIMPIEZA Y DATACLEANING
    # ==========================================

    if archivo_seleccionado.startswith("26-"):
      df = df.dropna(how="all")

    if archivo_seleccionado.startswith("Alarma"):
      df.columns = df.iloc[2]
      df = df.iloc[3:].reset_index(drop=True)

    # ==========================================
    # CORREGIR COLUMNAS DUPLICADAS
    # ==========================================
    df.columns = [str(col) for col in df.columns]
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
      cols[cols == dup] = [
          f"{dup}_{i}" if i != 0 else dup
          for i in range(sum(cols == dup))
      ]
    df.columns = cols


# ==========================================
# CRUCE Y FILTRADO AUTOMÁTICO (ALARMA + VESSEL)
# ==========================================
nombre_vessel = buscar_vessel()
nombre_alarma = buscar_alarma()

if nombre_vessel and nombre_alarma:
  if archivo_seleccionado == nombre_alarma:

    if "Estado Ctr" in df.columns:
      estado_limpio = df["Estado Ctr"].astype(str).str.strip()
      df_alarma_filtrado = df[estado_limpio == "Desconectado"].copy()
    else:
      df_alarma_filtrado = pd.DataFrame()
      st.warning(" No se encontró la columna 'Estado Ctr' en el archivo de Alarma.")

    if not df_alarma_filtrado.empty:
      # Llamamos a nuestra nueva función dedicada a limpiar Vessel
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
              suffixes=("_alarma", "_vessel"),
          )
          df = df_resultado
          st.success(f" Visualización creada: Alarma (Desconectado) cruzado con {nombre_vessel}")
        else:
          st.warning(f" No se encontró la columna '{columna_alarma}' en Alarma o '{columna_vessel}' en Vessel.")
      else:
        st.warning(" El archivo Vessel quedó vacío después de aplicar los filtros (Phase/GENERICA).")
    else:
      st.info("ℹ No hay registros con Estado 'Desconectado' para realizar el cruce.")

    # ==========================================
    # ZONA DE CÁLCULOS Y MÉTRICAS
    # ==========================================
    st.subheader(f"Análisis de: {archivo_seleccionado}")

    col1, col2 = st.columns(2)
    with col1:
      st.metric(label="Total de registros", value=len(df))

    with col2:
      pass

    # Mostrar la tabla final limpia y cruzada
    st.dataframe(df)

else:
  st.warning("No se encontraron archivos en la carpeta data.")