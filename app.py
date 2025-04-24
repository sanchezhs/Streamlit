
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os


st.title("Progreso de Entrenamiento")

CSV_PATH = "data/progreso_entrenamiento.csv"

@st.cache_data
def load_data():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    return pd.DataFrame(columns=["Ejercicio", "Semana", "Peso medio", "Reps totales", "Series"])

def calcular_metricas(df):
    if df.empty:
        return df
    df = df.copy()
    df["Volumen"] = df["Peso"] * df["Reps"]

    # Agrupaciones por ejercicio y semana
    resumen = df.groupby(["Ejercicio", "Semana"]).agg({
        "Peso": "mean",
        "Reps": "sum",
        "Volumen": "sum",
        "Serie": "count"
    }).reset_index()
    resumen = resumen.rename(columns={
        "Peso": "Peso medio",
        "Reps": "Reps totales",
        "Volumen": "Volumen total",
        "Serie": "Series"
    })
    resumen["Volumen por serie"] = round(resumen["Volumen total"] / resumen["Series"], 2)

    primeras_series = df.sort_values("Serie").drop_duplicates(["Ejercicio", "Semana"], keep="first")
    primeras_series["1RM estimado"] = round(primeras_series["Peso"] * (1 + primeras_series["Reps"] / 30), 2)

    resumen = resumen.merge(primeras_series[["Ejercicio", "Semana", "1RM estimado"]], on=["Ejercicio", "Semana"], how="left")
    resumen["Intensidad (%)"] = round(resumen["Peso medio"] / resumen["1RM estimado"] * 100, 2)
    carga_maxima = df.groupby(["Ejercicio", "Semana"])["Peso"].max().reset_index()
    carga_maxima = carga_maxima.rename(columns={"Peso": "Carga máxima"})
    resumen = resumen.merge(carga_maxima, on=["Ejercicio", "Semana"], how="left")
    resumen = resumen.sort_values(by=["Ejercicio", "Semana"])
    resumen["Δ Volumen"] = resumen.groupby("Ejercicio")["Volumen total"].diff()
    return resumen

def mostrar_grafico_linea(df, columna, titulo, ylabel, color=None, referencia_cero=False):
    fig, ax = plt.subplots()
    ax.plot(df["Semana"], df[columna], marker="o", color=color)
    ax.set_title(titulo)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Semana")
    ax.grid(True)
    if referencia_cero:
        ax.axhline(0, color="gray", linestyle="--")
    st.pyplot(fig)

def mostrar_grafico_barra(df, columna, titulo, ylabel):
    fig, ax = plt.subplots()
    ax.bar(df["Semana"], df[columna], color="skyblue")
    ax.set_title(titulo)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Semana")
    st.pyplot(fig)

df = calcular_metricas(load_data())

if "registro_actual" not in st.session_state:
    st.session_state["registro_actual"] = []

st.header("Registrar entrenamiento")
with st.form("form_series"):
    ejercicio_activo = st.text_input("Ejercicio")
    semana_opcion = st.selectbox("Semana del mes", ["1ª Semana", "2ª Semana", "3ª Semana", "4ª Semana"])
    mes_opcion = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    semana_actual = f"{semana_opcion} {mes_opcion}"
    peso = st.number_input("Peso (kg)", min_value=0.0, step=0.5)
    reps = st.number_input("Repeticiones", min_value=1, step=1)
    añadir_serie = st.form_submit_button("Añadir serie")

    if añadir_serie and ejercicio_activo:
        st.session_state["registro_actual"].append({
            "Ejercicio": ejercicio_activo,
            "Semana": semana_actual,
            "Peso": peso,
            "Reps": reps
        })

if st.session_state["registro_actual"]:
    st.subheader("Series actuales")
    registro_df = pd.DataFrame(st.session_state["registro_actual"])
    st.dataframe(registro_df)

    for i, row in registro_df.iterrows():
        col1, col2 = st.columns([8, 1])
        with col1:
            st.write(f"Serie {i+1}: {row['Peso']} kg x {row['Reps']} reps")
        with col2:
            if st.button("❌", key=f"eliminar_{i}"):
                st.session_state["registro_actual"].pop(i)
                st.rerun()

    if st.button("Guardar entrenamiento completo"):
        nuevas_series = pd.DataFrame(st.session_state["registro_actual"])
        columnas_requeridas = ["Ejercicio", "Semana", "Peso", "Reps"]
        if "Serie" not in nuevas_series.columns:
            nuevas_series.insert(2, "Serie", range(1, len(nuevas_series) + 1))
        nuevas_series = nuevas_series[["Ejercicio", "Semana", "Serie", "Peso", "Reps"]]
        nuevas_series.to_csv(CSV_PATH, mode='a', header=not os.path.exists(CSV_PATH), index=False)
        st.session_state["registro_actual"] = []
        st.success("Entrenamiento guardado correctamente.")

# Filtro
semanas_disponibles = ["Todo"] + sorted(df["Semana"].dropna().unique())
semana_seleccionada = st.selectbox("Selecciona una semana:", semanas_disponibles)

df_semana = df.copy() if semana_seleccionada == "Todo" else df[df["Semana"] == semana_seleccionada]

ejercicios_disponibles = df_semana["Ejercicio"].dropna().unique()
ejercicio = st.selectbox("Selecciona un ejercicio:", sorted(ejercicios_disponibles))

df_filtrado = df_semana[df_semana["Ejercicio"] == ejercicio]

# Mostrar datos y gráficas
st.subheader(f"{ejercicio} ({semana_seleccionada})")

# Resumen de métricas
col1, col2, col3 = st.columns(3)
col1.metric("Peso medio", f"{df_filtrado['Peso medio'].mean():.1f} kg")
col2.metric("Reps totales", int(df_filtrado["Reps totales"].sum()))
col3.metric("Volumen total", f"{df_filtrado['Volumen total'].sum():.1f}")

st.dataframe(df_filtrado)

if not df_filtrado.empty:
    mostrar_grafico_linea(df[df["Ejercicio"] == ejercicio], "Peso medio", "Progreso del Peso Medio por Semana", "Peso (kg)")
    mostrar_grafico_linea(df[df["Ejercicio"] == ejercicio], "Volumen total", "Volumen Total por Semana", "Volumen", color="green")
    mostrar_grafico_barra(df[df["Ejercicio"] == ejercicio], "Reps totales", "Repeticiones Totales por Semana", "Reps")
    mostrar_grafico_linea(df[df["Ejercicio"] == ejercicio], "Intensidad (%)", "Intensidad Estimada (%) por Semana", "% 1RM estimado", color="orange")
    mostrar_grafico_linea(df[df["Ejercicio"] == ejercicio], "Δ Volumen", "Cambio de Volumen por Semana", "Δ Volumen", color="purple", referencia_cero=True)
else:
    st.info("No hay datos disponibles para este ejercicio.")
