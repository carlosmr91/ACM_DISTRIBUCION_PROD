# -*- coding: utf-8 -*-
""""
Created on Thu Oct 31 17:35:14 2024

@author: juan.melendez
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from pyproj import Proj, Transformer

# CONFIGURACIÓN DE LA PÁGINA STREAMLIT
def configure_page():
    st.set_page_config(page_title="ZONAS ACM", layout="wide")
    st.markdown("<h1 style='text-align: center; color: black;'>DISTRIBUCIÓN DE LA PRODUCCIÓN DE LOS YACIMIENTOS EN ACM</h1>", 
                unsafe_allow_html=True)
    st.sidebar.markdown("<h2 style='color: gray;'>⚙️ CONTROLADORES</h2>", 
                        unsafe_allow_html=True)
    st.sidebar.markdown("<p style='text-align: center;'>---------------------------------</p>", 
                        unsafe_allow_html=True)

# CARGA DE ARCHIVO
def load_data():
    df_or = st.sidebar.file_uploader("📂", type=["csv", "CSV", "TXT", "txt"])
    if df_or:
        return pd.read_csv(df_or, sep=",")
    st.error("ARCHIVO NO CARGADO ❗❗")
    st.stop()

def process_data(df_loaded):

    if df_loaded is None:
        raise ValueError("df_loaded no cargó correctamente.")

    # Convertir la columna de fecha a formato datetime
    df_loaded['FECHA'] = pd.to_datetime(df_loaded['FECHA'], format='%d/%m/%Y %H:%M')    

    df_acumulada_tabla_max = df_loaded.groupby(["POZO", "POZO ID", "ZONA"])[['NP Mbbl','WP Mbbl','GP MMcf']].max().reset_index()
    df_acumulada_tabla_sum = df_acumulada_tabla_max.groupby(["POZO", "ZONA"])[['NP Mbbl','WP Mbbl','GP MMcf']].sum().reset_index()
    
    df_meses_max = df_loaded.groupby(["POZO", "POZO ID", "ZONA"])[['MESES ACTIVO']].max().reset_index()
    df_meses_sum = df_meses_max.groupby(["POZO", "ZONA"])[['MESES ACTIVO']].max().reset_index()
    
    merged_df = pd.merge(df_acumulada_tabla_sum, df_meses_sum, on=["POZO", "ZONA"], how="inner")
    


    #DATAFRAME CON DATOS ACUMULADA TOTAL
    # Filtrar los valores máximos de los disparos por pozo
    df_acumulada_max = df_loaded.groupby(["POZO", "POZO ID", "ZONA","WGS84_UTMX_OBJETIVO", "WGS84_UTMY_OBJETIVO"])[['MESES ACTIVO','NP Mbbl','WP Mbbl','GP MMcf']].max().reset_index()
    # Totalizar los la producion acumulada por pozo
    df_acumulada_totalizada = df_acumulada_max.groupby(["POZO", "ZONA","WGS84_UTMX_OBJETIVO", "WGS84_UTMY_OBJETIVO",'MESES ACTIVO'])[['NP Mbbl','WP Mbbl','GP MMcf']].sum().reset_index()
    
    
    #DATAFRAME CON DATOS A 6 MESES
    df_corte = df_loaded[df_loaded['MESES ACTIVO'] == 12]
    
    # Filtrar los valores máximos de los disparos por pozo
    df_acumulada_normalizada = df_corte.groupby(["POZO", "POZO ID", "ZONA","WGS84_UTMX_OBJETIVO", "WGS84_UTMY_OBJETIVO"])[['MESES ACTIVO','NP Mbbl','WP Mbbl','GP MMcf']].max().reset_index()
    # Totalizar los la producion acumulada por pozo
    df_acumulada_corte = df_acumulada_normalizada.groupby(["POZO", "ZONA","WGS84_UTMX_OBJETIVO", "WGS84_UTMY_OBJETIVO",'MESES ACTIVO'])[['NP Mbbl','WP Mbbl','GP MMcf']].sum().reset_index()
       
    
    
    #Identifica la fecha de corte OFM (maxima) y crea un filtro de los pozos que tienen produccion a esa fecha
    fecha_corte_OFM = df_loaded['FECHA'].max()
    df_fecha_corte_OFM = df_loaded[df_loaded['FECHA'] == fecha_corte_OFM]
        
    #Crear dataframe de la producción diaria por disparo a la fecha maxima del OFM
    df_prod_diaria_xdisparo = df_fecha_corte_OFM.groupby(["POZO", "POZO ID", "ZONA","WGS84_UTMX_OBJETIVO", "WGS84_UTMY_OBJETIVO",'FECHA'])[['ACEITE DIARIO BPD', 'AGUA DIARIA BPD', 
                                                            'GAS DIARIO MMcfd']].max().reset_index()
    # Totalizar los la producion diaria por pozo
    df_diaria_totalizada = df_prod_diaria_xdisparo.groupby(["POZO", "ZONA","WGS84_UTMX_OBJETIVO", "WGS84_UTMY_OBJETIVO",'FECHA'])[['ACEITE DIARIO BPD', 'AGUA DIARIA BPD', 
                                                            'GAS DIARIO MMcfd']].sum().reset_index()
        
    #df_integral = pd.merge(df_acumulada_totalizada, df_diaria_totalizada, on=["POZO", "ZONA"], how="inner")
    
    #df_lista_coor = df_loaded[["POZO", "WGS84_UTMX_OBJETIVO", "WGS84_UTMY_OBJETIVO", "ZONA"]].drop_duplicates()
    
    df_data = df_acumulada_totalizada
    df_data_corte = df_acumulada_corte
    df_diaria_actual = df_diaria_totalizada
    df_pozos = df_loaded[["POZO", "WGS84_UTMX_OBJETIVO", "WGS84_UTMY_OBJETIVO", "ZONA"]].drop_duplicates()
    merged_data = merged_df
    
    # Definir el transformador para convertir de UTM a Lat/Long
    transformer = Transformer.from_crs(
        "epsg:32614",  # UTM Zone 14N WGS84 (ajustar según tu zona UTM)
        "epsg:4326",   # WGS84
        always_xy=True
    )
       
    # Función para convertir UTM a Lat/Long
    def utm_to_latlon(utm_easting, utm_northing):
        lon, lat = transformer.transform(utm_easting, utm_northing)
        return lat, lon
    
    # Aplicar la conversión de UTM a Lat/Long para los pozos
    df_pozos[['Latitude', 'Longitude']] = df_pozos.apply(
        lambda row: utm_to_latlon(row['WGS84_UTMX_OBJETIVO'], row['WGS84_UTMY_OBJETIVO']), 
        axis=1, result_type='expand'
    )
        
    # Aplicar la conversión de UTM a Lat/Long para los pozos
    df_data[['Latitude', 'Longitude']] = df_data.apply(
        lambda row: utm_to_latlon(row['WGS84_UTMX_OBJETIVO'], row['WGS84_UTMY_OBJETIVO']), 
        axis=1, result_type='expand'
    )
    
    # Aplicar la conversión de UTM a Lat/Long para los pozos
    df_data_corte[['Latitude', 'Longitude']] = df_data_corte.apply(
        lambda row: utm_to_latlon(row['WGS84_UTMX_OBJETIVO'], row['WGS84_UTMY_OBJETIVO']), 
        axis=1, result_type='expand'
    )
    
    # Aplicar la conversión de UTM a Lat/Long para los pozos
    df_diaria_actual[['Latitude', 'Longitude']] = df_diaria_actual.apply(
        lambda row: utm_to_latlon(row['WGS84_UTMX_OBJETIVO'], row['WGS84_UTMY_OBJETIVO']), 
        axis=1, result_type='expand'
    )
    
    # Definir y convertir las coordenadas UTM para el polígono
    polygon_utm_coords = [
        (629254, 2294990),
        (629205, 2305136),
        (643050, 2305249),
        (643137, 2295102),
        (629254, 2294990)
        
    ]
    polygon_latlon = [utm_to_latlon(easting, northing) for easting, northing in polygon_utm_coords]
    
    # Separar las coordenadas en latitudes y longitudes
    polygon_lats, polygon_lons = zip(*polygon_latlon)
    zoom = 1    
  
    return df_pozos, df_data,df_data_corte,df_diaria_actual, merged_data, polygon_lats, polygon_lons, zoom

def plot_density_map(df,df_p, variable, polygon_lats, polygon_lons,color_continuous_scale,zoom):
    # Ajusta el factor de escala según el nivel de detalle que necesites
    radius = max(2, 35 - zoom * 1)  # Ejemplo de fórmula que disminuye el radio a medida que el zoom aumenta
    
    # Definir el rango de colores basado en los valores de la variable seleccionada
    min_val = 0
    max_val = df[variable].max()
    range_color = [min_val, max_val]
    
    # Crear el mapa de densidad
    fig = px.density_mapbox(df, lat='Latitude', lon='Longitude', z=variable, radius=radius,
                            center=dict(lat=df['Latitude'].mean(), lon=df['Longitude'].mean()), 
                            zoom=zoom,  # Ajustar el nivel de zoom según sea necesario
                            mapbox_style="carto-positron",
                            color_continuous_scale=color_continuous_scale,
                            opacity=0.9,
                            range_color=range_color,
                            title=f"Mapa de Densidad de {variable}")

    # Agregar los marcadores de todos los pozos
    well_coort = go.Scattermapbox(
        lat=df_p['Latitude'],
        lon=df_p['Longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10,
            color='black',
            opacity=1
        ),
        text=df_p['POZO'],  # Texto emergente
        hoverinfo='text',
        name='Pozos'  # Nombre de la leyenda
    )    

    # Agregar los marcadores de los pozos filtrados
    well_coorf = go.Scattermapbox(
        lat=df['Latitude'],
        lon=df['Longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=9,
            color='red',
            opacity=1
        ),
        text=df['POZO'],  # Texto emergente
        hoverinfo='text',
        name='Seleccionados' # Nombre de la leyenda
    )
    
    # Agregar el polígono
    polygon_trace = go.Scattermapbox(
        fill="none",
        lat=polygon_lats,
        lon=polygon_lons,
        mode="lines",
        line=dict(width=2, color="black"),
        hoverinfo='none',
        opacity=1,
        name='ACM'  # Nombre de la leyenda
    )
    
    # Combinar el mapa de densidad con los marcadores y el polígono
    fig.add_trace(well_coort)
    fig.add_trace(well_coorf)
    fig.add_trace(polygon_trace)
    
    # Actualizar el diseño del gráfico
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=20.795, lon=-97.691),
            zoom=11.4,
        ),
        margin={"r":1,"t":1,"l":1,"b":1},
        height=550,
        width=650,
        title_text=f"Mapa de Densidad de {variable}"
    )
    
    return fig

def main():
    # Configura la página y carga los datos
    configure_page()
    df_loaded = load_data()
    
    with st.spinner("Procesando datos..."):
        df_pozos, df_data,df_data_corte,df_diaria_actual, merged_data, polygon_lats, polygon_lons, zoom = process_data(df_loaded)
        
        # Crea las pestañas de la interfaz
        tabs = st.tabs(["ACUMULADA TOTAL", "ACUMULADA NORMALIZADA", "PRODUCCIÓN ACTUAL"])
        
        # Filtros desde la barra lateral
        ms_zona = st.sidebar.multiselect("SELECCIONA EL/LAS ZONA(S)", df_pozos["ZONA"].unique(), default=[])
                
        df_data_seleccion = df_data[df_data["ZONA"].isin(ms_zona)]
        df_data_selection_norm = df_data_corte[df_data_corte["ZONA"].isin(ms_zona)]
        df_data_selection_diaria = df_diaria_actual[df_diaria_actual["ZONA"].isin(ms_zona)]
        df_tablas_resumen = merged_data[merged_data["ZONA"].isin(ms_zona)]
        
        
        # Pestaña "PRODUCCIÓN ACUMULADA"
        with tabs[0]:         
            # Crear histogramas para cada variable
            fig_histogram_Np = px.histogram(df_data_seleccion, x='NP Mbbl', nbins=40, title="Histograma de AceiteAcumulado")
            fig_histogram_Wp = px.histogram(df_data_seleccion, x='WP Mbbl', nbins=40, title="Histograma de AguaAcumulada")
            fig_histogram_Gp = px.histogram(df_data_seleccion, x='GP MMcf', nbins=40, title="Histograma de GasAcumulado")
            
            # Configuración de color y estilo de los gráficos
            histogram_style = dict(
                plot_bgcolor="white",
                font=dict(family='Arial', size=12, color='black'),
                xaxis_title_font=dict(size=12, color='black', family='Arial'),
                yaxis_title_font=dict(size=12, color='black', family='Arial'),
                height=200,
                width=190,
                margin=dict(l=20, r=170, t=40, b=20)  # Ajustar márgenes para mejor visualización
            )
            
            # Configuración de cada histograma con título centrado y colores específicos
            fig_histogram_Np.update_layout(
                **histogram_style,
                title=dict(text="Histograma de Aceite Acumulado", x=0.2, font=dict(size=16, color='black', family='Arial')),
                yaxis_title="Total del Pozos"
            )
            fig_histogram_Np.update_traces(marker_color='green', marker_line_color='black', marker_line_width=0.5)
            
            fig_histogram_Wp.update_layout(
                **histogram_style,
                title=dict(text="Histograma de Agua Acumulada", x=0.2, font=dict(size=16, color='black', family='Arial')),
                yaxis_title="Total del Pozos"
            )
            fig_histogram_Wp.update_traces(marker_color='blue', marker_line_color='black', marker_line_width=0.5)
            
            fig_histogram_Gp.update_layout(
                **histogram_style,
                title=dict(text="Histograma de Gas Acumulado", x=0.2, font=dict(size=16, color='black', family='Arial')),
                yaxis_title="Total del Pozos"
            )
            fig_histogram_Gp.update_traces(marker_color='orange', marker_line_color='black', marker_line_width=0.5)
            

            # Mostrar en cuatro columnas
            col1, col2, col3 = st.columns(3)
            with col1:
            # Mostrar el mapa (ya sea filtrado o no)
                col1.markdown("""<h3 style='text-align:center; font-family:Arial;
                              font-size:18px; color:#333333;'>ACEITE ACUMULADO TOTAL (Mbbl)</h3>""",
                    unsafe_allow_html=True
                )
                figNp = plot_density_map(df_data_seleccion, df_pozos, "NP Mbbl", polygon_lats, polygon_lons, 'turbo', zoom)
                st.plotly_chart(figNp, use_container_width=True, key="figNp_key")
                st.plotly_chart(fig_histogram_Np, use_container_width=True, key="fig_histogram_Np_key")
                selected_columnsNP = ["POZO", "ZONA", 'MESES ACTIVO', 'NP Mbbl']
                st.write(df_tablas_resumen[selected_columnsNP])
                            
            with col2:
            # Mostrar el mapa (ya sea filtrado o no)
                col2.markdown("""<h3 style='text-align:center; font-family:Arial;
                              font-size:18px; color:#333333;'>AGUA ACUMULADA TOTAL (Mbbl)</h3>""",
                    unsafe_allow_html=True
                )
                figWp = plot_density_map(df_data_seleccion, df_pozos, "WP Mbbl", polygon_lats, polygon_lons, 'turbo', zoom)
                st.plotly_chart(figWp, use_container_width=True, key="figWp_key")
                st.plotly_chart(fig_histogram_Wp, use_container_width=True, key="fig_histogram_Wp_key")
                selected_columnsWP = ["POZO", "ZONA", 'MESES ACTIVO', 'WP Mbbl']
                st.write(df_tablas_resumen[selected_columnsWP])
                
            with col3:
            # Mostrar el mapa (ya sea filtrado o no)
                col3.markdown("""<h3 style='text-align:center; font-family:Arial;
                              font-size:18px; color:#333333;'>GAS ACUMULADO TOTAL (MMcf)</h3>""",
                    unsafe_allow_html=True
                )
                figGp = plot_density_map(df_data_seleccion, df_pozos, "GP MMcf", polygon_lats, polygon_lons, 'turbo', zoom)
                st.plotly_chart(figGp, use_container_width=True, key="figGp_key") 
                st.plotly_chart(fig_histogram_Gp, use_container_width=True, key="fig_histogram_Gp_key")
                selected_columnsGP = ["POZO", "ZONA", 'MESES ACTIVO', 'GP MMcf']
                st.write(df_tablas_resumen[selected_columnsGP])
                
            # Pestaña "PRODUCCIÓN ACUMULADA NORMALIZADA"
            with tabs[1]:         
                # Crear histogramas para cada variable
                fig_histogram_Np_corte = px.histogram(df_data_selection_norm, x='NP Mbbl', nbins=40, title="Histograma de Aceite Acumulado")
                fig_histogram_Wp_corte = px.histogram(df_data_selection_norm, x='WP Mbbl', nbins=40, title="Histograma de Agua Acumulada")
                fig_histogram_Gp_corte = px.histogram(df_data_selection_norm, x='GP MMcf', nbins=40, title="Histograma de Gas Acumulado")
                
                # Configuración de color y estilo de los gráficos
                histogram_style = dict(
                    plot_bgcolor="white",
                    font=dict(family='Arial', size=12, color='black'),
                    xaxis_title_font=dict(size=12, color='black', family='Arial'),
                    yaxis_title_font=dict(size=12, color='black', family='Arial'),
                    height=200,
                    width=190,
                    margin=dict(l=20, r=170, t=40, b=20)  # Ajustar márgenes para mejor visualización
                )
                
                # Configuración de cada histograma con título centrado y colores específicos
                fig_histogram_Np_corte.update_layout(
                    **histogram_style,
                    title=dict(text="Histograma de Aceite Acumulado Normalizado", x=0.2, font=dict(size=16, color='black', family='Arial')),
                    yaxis_title="Total del Pozos"
                )
                fig_histogram_Np_corte.update_traces(marker_color='green', marker_line_color='black', marker_line_width=0.5)
                
                fig_histogram_Wp_corte.update_layout(
                    **histogram_style,
                    title=dict(text="Histograma de Agua Acumulada Normalizada", x=0.2, font=dict(size=16, color='black', family='Arial')),
                    yaxis_title="Total del Pozos"
                )
                fig_histogram_Wp_corte.update_traces(marker_color='blue', marker_line_color='black', marker_line_width=0.5)
                
                fig_histogram_Gp_corte.update_layout(
                    **histogram_style,
                    title=dict(text="Histograma de Gas Acumulado Normalizado", x=0.2, font=dict(size=16, color='black', family='Arial')),
                    yaxis_title="Total del Pozos"
                )
                fig_histogram_Gp_corte.update_traces(marker_color='orange', marker_line_color='black', marker_line_width=0.5)
                
    
            # Mostrar en cuatro columnas
                col1, col2, col3 = st.columns(3)
                with col1:
                # Mostrar el mapa (ya sea filtrado o no)
                    col1.markdown("""<h3 style='text-align:center; font-family:Arial;
                                  font-size:18px; color:#333333;'>ACEITE ACUMULADO NORMALIZADO A 12 MESES (Mbbl)</h3>""",
                        unsafe_allow_html=True
                    )
                    figNpc = plot_density_map(df_data_selection_norm, df_pozos, "NP Mbbl", polygon_lats, polygon_lons, 'turbo', zoom)
                    st.plotly_chart(figNpc, use_container_width=True, key="figNpc_key")
                    st.plotly_chart(fig_histogram_Np_corte, use_container_width=True, key="fig_histogram_Np_corte_key")
                    selected_columnsNP = ["POZO", "ZONA", 'MESES ACTIVO', 'NP Mbbl']
                    st.write(df_data_selection_norm[selected_columnsNP])
                                
                with col2:
                # Mostrar el mapa (ya sea filtrado o no)
                    col2.markdown("""<h3 style='text-align:center; font-family:Arial;
                                  font-size:18px; color:#333333;'>AGUA ACUMULADA NORMALIZADA A 12 MESES (Mbbl)</h3>""",
                        unsafe_allow_html=True
                    )
                    figWpc = plot_density_map(df_data_selection_norm, df_pozos, "WP Mbbl", polygon_lats, polygon_lons, 'turbo', zoom)
                    st.plotly_chart(figWpc, use_container_width=True, key="figWpc_key")
                    st.plotly_chart(fig_histogram_Wp_corte, use_container_width=True, key="fig_histogram_Wp_corte_key")
                    selected_columnsWP = ["POZO", "ZONA", 'MESES ACTIVO', 'WP Mbbl']
                    st.write(df_data_selection_norm[selected_columnsWP])
                    
                with col3:
                # Mostrar el mapa (ya sea filtrado o no)
                    col3.markdown("""<h3 style='text-align:center; font-family:Arial;
                                  font-size:18px; color:#333333;'>GAS ACUMULADO NORMALIZADO A 12 MESES  (MMcf)</h3>""",
                        unsafe_allow_html=True
                    )
                    figGpc = plot_density_map(df_data_selection_norm, df_pozos, "GP MMcf", polygon_lats, polygon_lons, 'turbo', zoom)
                    st.plotly_chart(figGpc, use_container_width=True, key="figGpc_key") 
                    st.plotly_chart(fig_histogram_Gp_corte, use_container_width=True, key="fig_histogram_Gp_corte_key")
                    selected_columnsGP = ["POZO", "ZONA", 'MESES ACTIVO', 'GP MMcf']
                    st.write(df_data_selection_norm[selected_columnsGP])
                    

                # Pestaña "PRODUCCIÓN DIARIA ACTUAL"
                with tabs[2]:         
                    # Crear histogramas para cada variable
                    fig_histogram_Qo = px.histogram(df_data_selection_diaria, x='ACEITE DIARIO BPD', nbins=40, title="Histograma de Aceite Diario")
                    fig_histogram_Qw = px.histogram(df_data_selection_diaria, x='AGUA DIARIA BPD', nbins=40, title="Histograma de Agua Diaria")
                    fig_histogram_Qg = px.histogram(df_data_selection_diaria, x='GAS DIARIO MMcfd', nbins=40, title="Histograma de Gas Diario")
                    
                    # Configuración de color y estilo de los gráficos
                    histogram_style = dict(
                        plot_bgcolor="white",
                        font=dict(family='Arial', size=12, color='black'),
                        xaxis_title_font=dict(size=12, color='black', family='Arial'),
                        yaxis_title_font=dict(size=12, color='black', family='Arial'),
                        height=200,
                        width=190,
                        margin=dict(l=20, r=170, t=40, b=20)  # Ajustar márgenes para mejor visualización
                    )
                    
                    # Configuración de cada histograma con título centrado y colores específicos
                    fig_histogram_Qo.update_layout(
                        **histogram_style,
                        title=dict(text="Histograma de Aceite Diario", x=0.2, font=dict(size=16, color='black', family='Arial')),
                        yaxis_title="Total del Pozos"
                    )
                    fig_histogram_Qo.update_traces(marker_color='green', marker_line_color='black', marker_line_width=0.5)
                    
                    fig_histogram_Qw.update_layout(
                        **histogram_style,
                        title=dict(text="Histograma de Agua Diaria", x=0.2, font=dict(size=16, color='black', family='Arial')),
                        yaxis_title="Total del Pozos"
                    )
                    fig_histogram_Qw.update_traces(marker_color='blue', marker_line_color='black', marker_line_width=0.5)
                    
                    fig_histogram_Qg.update_layout(
                        **histogram_style,
                        title=dict(text="Histograma de Gas Diario", x=0.2, font=dict(size=16, color='black', family='Arial')),
                        yaxis_title="Total del Pozos"
                    )
                    fig_histogram_Qg.update_traces(marker_color='orange', marker_line_color='black', marker_line_width=0.5)
                    
        
                # Mostrar en cuatro columnas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                    # Mostrar el mapa (ya sea filtrado o no)
                        col1.markdown("""<h3 style='text-align:center; font-family:Arial;
                                      font-size:18px; color:#333333;'>ACEITE DIARIO (BPD)</h3>""",
                            unsafe_allow_html=True
                        )
                        figQo_diario = plot_density_map(df_data_selection_diaria, df_pozos, "ACEITE DIARIO BPD", polygon_lats, polygon_lons, 'turbo', zoom)
                        st.plotly_chart(figQo_diario, use_container_width=True, key="figQo_diario_key")
                        st.plotly_chart(fig_histogram_Qo, use_container_width=True, key="fig_histogram_Qo_key")
                        selected_columnsQo = ["POZO", "ZONA", 'FECHA', 'ACEITE DIARIO BPD']
                        st.write(df_data_selection_diaria[selected_columnsQo])
                                    
                    with col2:
                    # Mostrar el mapa (ya sea filtrado o no)
                        col2.markdown("""<h3 style='text-align:center; font-family:Arial;
                                      font-size:18px; color:#333333;'>AGUA DIARIA (BPD)</h3>""",
                            unsafe_allow_html=True
                        )
                        figQw_diario = plot_density_map(df_data_selection_diaria, df_pozos, "AGUA DIARIA BPD", polygon_lats, polygon_lons, 'turbo', zoom)
                        st.plotly_chart(figQw_diario, use_container_width=True, key="figQw_diario_key")
                        st.plotly_chart(fig_histogram_Qw, use_container_width=True, key="fig_histogram_Qw_key")
                        selected_columnsQw = ["POZO", "ZONA", 'FECHA', 'AGUA DIARIA BPD']
                        st.write(df_data_selection_diaria[selected_columnsQw])
                        
                    with col3:
                    # Mostrar el mapa (ya sea filtrado o no)
                        col3.markdown("""<h3 style='text-align:center; font-family:Arial;
                                      font-size:18px; color:#333333;'>GAS DIARIO  (MMcfd)</h3>""",
                            unsafe_allow_html=True
                        )
                        figQg_diario = plot_density_map(df_data_selection_diaria, df_pozos, "GAS DIARIO MMcfd", polygon_lats, polygon_lons, 'turbo', zoom)
                        st.plotly_chart(figQg_diario, use_container_width=True, key="figQg_diario_key") 
                        st.plotly_chart(fig_histogram_Qg, use_container_width=True, key="fig_histogram_Qg_key")
                        selected_columnsQg = ["POZO", "ZONA", "FECHA", "GAS DIARIO MMcfd"]
                        df_data_selection_diaria["RGA Mcfb"] = (df_data_selection_diaria["GAS DIARIO MMcfd"] * 1000) / df_data_selection_diaria["ACEITE DIARIO BPD"]
                        selected_columnsQg.append("RGA Mcfb")
                        st.write(df_data_selection_diaria[selected_columnsQg])
                        
                        
    
if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    