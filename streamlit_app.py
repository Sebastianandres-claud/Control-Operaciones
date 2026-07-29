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
    # Filtramos solo los archivos Excel
    return [
        f["name"] for f in response.json() if f["name"].endswith(".xlsx") or f["name"].endswith(".xls")
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
  # Crear un menú desplegable (selectbox) en la barra lateral o principal
  archivo_seleccionado = st.selectbox(
      "Selecciona el archivo que deseas analizar:", archivos_disponibles
  )

  # Cargar y mostrar el archivo elegido
  if archivo_seleccionado:
    df = cargar_archivo_individual(archivo_seleccionado)
    st.success(f"Mostrando datos de: {archivo_seleccionado}")
    st.dataframe(df)

    # Aquí puedes aplicar la limpieza específica para ESTE formato si lo deseas
    st.metric(label="Total de registros", value=len(df))
else:
  st.warning("No se encontraron archivos en la carpeta data.")
