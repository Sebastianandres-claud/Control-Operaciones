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

    # Regla: Si el archivo empieza por "26-"
    if archivo_seleccionado.startswith("26-"):
      # 1. Borrar filas donde todas las columnas estén vacías (NaN)
      df = df.dropna(how="all")

      # 2. (Opcional) Borrar filas si una columna clave está vacía, por ejemplo:
      # df = df.dropna(subset=['Nombre_De_Columna'])
    if archivo_seleccionado.startswith("Alarma"):
      if len(df) > 4:
        df = df.iloc[4:].reset_index(drop=True)
        # Convertir la nueva primera fila en los encabezados oficiales
        df.columns = df.iloc[0]
        # Eliminar esa fila que ya subió a ser cabecera y reiniciar los índices
        df = df.iloc[1:].reset_index(drop=True)

    # ==========================================
    # CORREGIR COLUMNAS DUPLICADAS
    # ==========================================
    # Convierte todas las columnas a string para evitar errores de tipo
    df.columns = [str(col) for col in df.columns]

    # Detecta y renombra columnas duplicadas añadiendo un número consecutivo
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
      cols[cols == dup] = [
          f"{dup}_{i}" if i != 0 else dup
          for i in range(sum(cols == dup))
      ]
    df.columns = cols

    # ==========================================
    # ZONA DE CÁLCULOS Y MÉTRICAS
    # ==========================================
    st.subheader(f"Análisis de: {archivo_seleccionado}")

    # Muestra métricas básicas
    col1, col2 = st.columns(2)
    with col1:
      st.metric(label="Total de registros", value=len(df))

    with col2:
      # Ejemplo de cálculo numérico (puedes cambiar 'Columna_Numerica' por una real de tu Excel)
      # if 'Columna_Numerica' in df.columns:
      #     total_suma = df['Columna_Numerica'].sum()
      #     st.metric(label="Suma Total", value=total_suma)
      pass

    # Mostrar la tabla final limpia
    st.dataframe(df)

else:
  st.warning("No se encontraron archivos en la carpeta data.")
