import pandas as pd
import streamlit as st

st.title("Control Operaciones")

# URL limpia sin saltos de línea ocultos
DATA_URL = "https://raw.githubusercontent.com/Sebastianandres-claud/Control-Operaciones/main/data/Alarma29-07-202611-26.xlsx"


@st.cache_data
def cargar_datos(url):
  # Leemos el archivo Excel desde la URL de GitHub
  df = pd.read_excel(url)
  return df


try:
  df = cargar_datos(DATA_URL)
  st.success("¡Datos cargados correctamente desde GitHub!")
  st.dataframe(df)
  st.metric(label="Total de registros", value=len(df))
except Exception as e:
  st.error(f"Ocurrió un error al cargar el archivo: {e}")
