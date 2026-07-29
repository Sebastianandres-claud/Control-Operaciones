import pandas as pd
import streamlit as st

# Título de tu aplicación
st.title("Mi Dashboard en la Nube")

# Si usas GitHub para los datos (recomendado):
DATA_URL = (
    "https://raw.githubusercontent.com/Sebastianandres-claud/Control-Operaciones/main/data/Alarma 29-07-2026 11-26.xlsx"
)


# Cargar datos con caché para que la app sea rápida
@st.cache_data
def cargar_datos(url):
  # Usa pd.read_csv(url) si tu archivo es CSV, o pd.read_excel(url) si es Excel
  df = pd.read_excel(url)
  return df


# Cargar el DataFrame
df = cargar_datos(DATA_URL)

# Mostrar un resumen o la tabla interactiva
st.subheader("Vista previa de los datos")
st.dataframe(df)

# Ejemplo de métrica básica
st.metric(label="Total de registros", value=len(df))
