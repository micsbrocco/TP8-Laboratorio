import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Análisis de Ventas")

def mostrar_informacion_alumno():
    with st.container(border=True):
        st.markdown('**Legajo:** 59320')
        st.markdown('**Nombre:** Sbrocco Micaela')
        st.markdown('**Comisión:** C9')


def calcular_metricas(df):
    df['Precio_promedio'] = df['Ingreso_total'] / df['Unidades_vendidas']
    df['Margen_promedio'] = (df['Ingreso_total'] - df['Costo_total']) / df['Ingreso_total']
    
    df['Precio_promedio_anterior'] = df.groupby('Producto')['Precio_promedio'].shift(1)
    df['Margen_promedio_anterior'] = df.groupby('Producto')['Margen_promedio'].shift(1)
    df['Unidades_vendidas_anterior'] = df.groupby('Producto')['Unidades_vendidas'].shift(1)
    
    resumen = df.groupby('Producto').agg({
        'Precio_promedio': 'mean',
        'Precio_promedio_anterior': 'mean',
        'Margen_promedio': 'mean',
        'Margen_promedio_anterior': 'mean',
        'Unidades_vendidas': 'sum',
        'Unidades_vendidas_anterior': 'sum',
    }).reset_index()
    return resumen

def graficar_evolucion(df, producto, sucursal="Todas"):
    if sucursal == "Todas":
        datos_producto = df[df['Producto'] == producto].groupby(['Año', 'Mes']).agg({
            'Unidades_vendidas': 'sum'
        }).reset_index()
    else:
        datos_producto = df[df['Producto'] == producto]

    datos_producto['Fecha'] = pd.to_datetime(
        datos_producto['Año'].astype(str) + '-' + datos_producto['Mes'].astype(str) + '-01'
    )
    datos_producto = datos_producto.sort_values('Fecha')

    datos_producto['Unidades_vendidas_suavizadas'] = datos_producto['Unidades_vendidas'].rolling(window=3).mean()

    X = np.arange(len(datos_producto))
    y = datos_producto['Unidades_vendidas_suavizadas'].fillna(0).values 
    coef = np.polyfit(X, y, 1)
    tendencia = np.polyval(coef, X)

    fig, ax = plt.subplots(figsize=(26, 16))
    ax.plot(datos_producto['Fecha'], datos_producto['Unidades_vendidas_suavizadas'], label=producto, color="#2271b3", linestyle="-", linewidth=2)
    ax.plot(datos_producto['Fecha'], tendencia, label="Tendencia", linestyle="--", color="red", linewidth=1.5)

    fechas_mes = pd.date_range(datos_producto['Fecha'].min(), datos_producto['Fecha'].max(), freq='MS')
    for fecha in fechas_mes:
        ax.axvline(x=fecha, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)

    years = datos_producto['Fecha'].dt.year.unique()
    for year in years:
        fecha_inicio = pd.Timestamp(f"{year}-01-01")
        ax.axvline(x=fecha_inicio, color='black', linestyle='-', linewidth=1.0, alpha=0.8)
    ax.set_ylim(bottom=0)

    ax.set_title("Evolución de Ventas Mensual", fontsize=28)
    ax.set_xlabel("Año", fontsize=24)
    ax.set_ylabel("Unidades Vendidas", fontsize=24)

    year_positions = [pd.Timestamp(f"{year}-01-01") for year in years]
    ax.set_xticks(year_positions)
    ax.set_xticklabels([str(year) for year in years], fontsize=22)

    ax.tick_params(axis='y', labelsize=22)
    ax.grid(True, which='major', axis='y', linestyle='--', linewidth=0.5, alpha=0.7)
    ax.legend(fontsize=20)

    return fig

st.sidebar.header("Cargar archivo de datos")
archivo = st.sidebar.file_uploader("Subir archivo CSV", type=["csv"])

if archivo is not None:
    df = pd.read_csv(archivo)
    df['Mes'] = df['Mes'].astype(int)
    df['Año'] = df['Año'].astype(int)

    st.sidebar.empty()

    sucursales = ["Todas"] + list(df['Sucursal'].unique())
    sucursal = st.sidebar.selectbox("Seleccionar Sucursal", sucursales)

    if sucursal == "Todas":
        st.header("Datos de todas las sucursales")
    else:
        st.header(f"Datos de la {sucursal}")
        df = df[df['Sucursal'] == sucursal]

    resumen = calcular_metricas(df)

    for _, row in resumen.iterrows():
        with st.container(border=True):            
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown(f"## {row['Producto']}")  
                delta_precio = (row['Precio_promedio'] - row['Precio_promedio_anterior']) / row['Precio_promedio_anterior'] * 100 if row['Precio_promedio_anterior'] else 0
                delta_margen = (row['Margen_promedio'] - row['Margen_promedio_anterior']) / row['Margen_promedio_anterior'] * 100 if row['Margen_promedio_anterior'] else 0
                delta_unidades = (row['Unidades_vendidas'] - row['Unidades_vendidas_anterior']) / row['Unidades_vendidas_anterior'] * 100 if row['Unidades_vendidas_anterior'] else 0

                st.metric(
                    label="Precio Promedio",
                    value=f"${row['Precio_promedio']:.2f}",
                    delta=f"{delta_precio:.2f}%",
                )
                st.metric(
                    label="Margen Promedio",
                    value=f"{row['Margen_promedio'] * 100:.2f}%",
                    delta=f"{delta_margen:.2f}%",
                )
                st.metric(
                    label="Unidades Vendidas",
                    value=f"{int(row['Unidades_vendidas']):,}",
                    delta=f"{delta_unidades:.2f}%",
                )
            with col2:
                fig = graficar_evolucion(df, row['Producto'], sucursal)
                st.pyplot(fig)
else:
    st.header("Por favor, sube un archivo CSV desde la barra lateral.")
    mostrar_informacion_alumno()
