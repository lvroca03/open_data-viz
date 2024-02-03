import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import nltk
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS


st.set_page_config(page_title="Tweets guerra", page_icon="✖", layout="wide")

tab1, tab2,tab3,tab4,tab5 = st.tabs(["Datos","Resumen tweets","Análisis territorial", "Análisis temporal","Análisis de sentimientos"])

with tab1:
    st.title("Tweets 'GUERRA ISRAEL GAZA'")
    st.write("En un esfuerzo por comprender la dinámica de la conversación en torno a la Guerra Israel-Gaza, se llevó a cabo un proceso de web scraping focalizado en la recopilación de 2000 tweets considerados 'top'. La información extraída pretende ofrecer una visión representativa de las opiniones y tendencias predominantes en la plataforma Twitter respecto a este conflicto.")
    st.write("La extracción de datos se realizó el 28 de enero de 2024 utilizando twscrape. Se estableció como parámetro de búsqueda “guerra israel gaza” para capturar los tweets pertinentes. La selección de los 'top tweets' se basó en criterios que podrían incluir el número de retweets, likes o relevancia, con el propósito de destacar aquellos mensajes que generaron mayor impacto en la comunidad virtual.")
    st.write("Es crucial destacar que se respetaron los términos de servicio de Twitter y las políticas de privacidad durante el proceso de web scraping. El uso responsable de los datos fue una prioridad.")

with tab2:
    data_tw = pd.read_csv("tweets_guerra_limpio.csv")
    def etiqueta(title, value):
        st.markdown(f"<div style='text-align:center;'><p style='font-size:48px; margin: 0; color:#1DA1F2;'>{value}</p><p style='margin: 0;'>{title}</p></div>", unsafe_allow_html=True)

    col_etiquetas = st.columns(4)

    with col_etiquetas[0]:
        etiqueta("TWEETS", data_tw["tweet"].count())
    with col_etiquetas[1]:
        etiqueta("UBICACIONES", len(data_tw["ubicacion"].unique()))
    with col_etiquetas[2]:
        etiqueta("MIN. FECHA", pd.to_datetime(data_tw["fecha"]).min().strftime("%d/%m/%Y") )
    with col_etiquetas[3]:
        etiqueta("MAX. FECHA", pd.to_datetime(data_tw["fecha"]).max().strftime("%d/%m/%Y") )
    
    col_filtos = st.columns(2)
    lista_paises = sorted(data_tw["ubicacion"].unique())
    lista_paises.remove("España")
    lista_paises.insert(0,"España")
    ubi = col_filtos[0].selectbox("Ubicacion",lista_paises )
    fecha = col_filtos[1].multiselect("Fecha",sorted(data_tw["fecha"].unique(),reverse= True), default = [data_tw[data_tw["ubicacion"] == "España"]["fecha"].value_counts().idxmax()])
    data_tw_filtrado = data_tw[(data_tw["ubicacion"]== ubi) & (data_tw["fecha"].isin(fecha))]
    
    st.write(f"Se han seleccionado {len(data_tw_filtrado)} tweets.")
    if not data_tw_filtrado.empty:
        st.dataframe(data_tw_filtrado[["usuario","tweet"]], hide_index = True,use_container_width=True)
    if data_tw_filtrado.empty:
        st.error("No hay tweets para la ubicación y fecha seleccionadas")

with tab3:
    info_tem_cols = st.columns(2)
    with info_tem_cols[0]:
        etiqueta("TWEETS SIN UBICACIÓN", data_tw[data_tw["ubicacion"] == "sin ubicación"]["tweet"].count())
    with info_tem_cols[1]:
        etiqueta("TWEETS CON UBICACIÓN", data_tw[data_tw["ubicacion"] != "sin ubicación"]["tweet"].count())
    data_tw_ubicacion= data_tw['ubicacion'].value_counts().reset_index().merge(data_tw[["ubicacion","codigo_pais"]], on="ubicacion").drop_duplicates()
    paises_codigos = pd.read_csv("paises.csv")
    paises_codigos= paises_codigos.rename(columns={'iso2': 'codigo_pais'})
    data_tw_ubicacion= data_tw_ubicacion.merge(paises_codigos[["codigo_pais","iso3"]], on="codigo_pais")
    data_tw_ubicacion= data_tw_ubicacion.rename(columns={'count': 'tweets'})
    maps_col = st.columns([1,2])
    with maps_col[0]:
        bubble_map = px.scatter_geo(data_tw_ubicacion, locations="iso3",size="tweets",
                            hover_name="ubicacion",hover_data={"iso3": False},
                            color='iso3',projection="robinson",
                            color_discrete_sequence= px.colors.sequential.Plasma_r,
                            labels={"iso3": "País"})
        bubble_map.update_geos(resolution=50,showland=True, landcolor="LightGreen",
        showocean=True, oceancolor="LightBlue")
        bubble_map.update_layout(template="none",margin=dict(l=0, r=20, t=0,b=0))
        bubble_map.update_traces(showlegend=False)
        st.plotly_chart(bubble_map, use_container_width=True)
    with maps_col[1]:
        calor_map= px.choropleth(data_tw_ubicacion, locations="iso3",color="tweets",
                            hover_name="ubicacion",hover_data={"iso3": False},
                            projection="robinson",
                            color_continuous_scale="Inferno",
                            labels={"tweets": "Tweets"})
        calor_map.update_geos(resolution=50,showocean=True, oceancolor="LightBlue")
        calor_map.update_layout(margin=dict(l=20, r=0, t=10,b=0))
        calor_map.update_coloraxes(colorbar=dict(thickness=20, len=0.5, xanchor='left', yanchor='middle'))
        st.plotly_chart(calor_map, use_container_width=True)
    
    data_tw_ubicacion["Porcentaje"]= round(data_tw_ubicacion["tweets"]/sum(data_tw_ubicacion["tweets"])*100).astype(str) + "%"
    data_tw_ubicacion_sorted = data_tw_ubicacion.sort_values(by="tweets", ascending=False)

    ubicacion_barplot = go.Figure(data=[go.Bar(x=data_tw_ubicacion_sorted["ubicacion"], 
                                y=data_tw_ubicacion_sorted["tweets"],
                                hovertext=data_tw_ubicacion_sorted["Porcentaje"])])

    ubicacion_barplot.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                    marker_line_width=1.5, opacity=0.6)
    ubicacion_barplot.update_layout(margin=dict(l=30, r=20, t=20), height=200, width=200,yaxis_title="Tweets")
    st.plotly_chart(ubicacion_barplot, use_container_width=True)

with tab4:
    ubicaciones = st.selectbox("Ubicaciones",["Todas las ubicaciones"]+sorted(list(data_tw["ubicacion"].unique())))
    if ubicaciones != "Todas las ubicaciones":
        data_tw2 = data_tw[data_tw["ubicacion"] == ubicaciones]
    else: 
        data_tw2 = data_tw
    
    temp_cols = st.columns(4)

    with temp_cols[0]:
        data_tw_temp= data_tw2['fecha'].value_counts().reset_index().sort_values(by='fecha')
        data_tw_temp= data_tw_temp.rename(columns={'count': 'Tweets'})
        fecha_lineplot = px.line(data_tw_temp[data_tw_temp['fecha'] > '2024-01-21'], x='fecha', y='Tweets')
        fecha_lineplot.update_xaxes(rangeslider_visible=True, tickformat='%d %b')
        fecha_lineplot.update_layout(margin=dict(l=0, r=0, t=0,b=0), height=220, width=220)
        st.plotly_chart(fecha_lineplot, use_container_width=True)
    
    with temp_cols[1]:
        abreviaturas_dias = {'lunes': 'Lun.', 'martes': 'Mar.', 'miércoles': 'Mié.', 
                             'jueves': 'Jue.', 'viernes': 'Vie.', 'sábado': 'Sáb.', 'domingo': 'Dom.'}

        data_tw2['dia_semana_abrev'] = data_tw2['dia_semana'].map(abreviaturas_dias)
        dia_semana_barplot = go.Figure(data=[go.Bar(x=data_tw2['dia_semana_abrev'].value_counts().index,
                                        y=data_tw2['dia_semana_abrev'].value_counts().values,
                                        hovertext=round(data_tw2['dia_semana_abrev'].value_counts().reset_index()["count"]/sum(data_tw2['dia_semana_abrev'].value_counts().reset_index()["count"])*100).astype(str) + "%")])

        orden_dias_semana = ['Lun.', 'Mar.', 'Mié.', 'Jue.', 'Vie.', 'Sáb.', 'Dom.']
        dia_semana_barplot.update_layout(xaxis=dict(categoryorder='array', categoryarray=orden_dias_semana))
        dia_semana_barplot.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                                    marker_line_width=1.5, opacity=0.6)
        dia_semana_barplot.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=220, width=220,yaxis_title="Tweets")
        st.plotly_chart(dia_semana_barplot, use_container_width=True)
    
    with temp_cols[2]:
        data_tw2["hora"]= pd.to_datetime(data_tw2["hora"] , format="%Y-%m-%d %H:%M:%S")
        hora_lineplot = px.line(data_tw2['hora'].dt.hour.value_counts().reset_index().sort_values(by='hora'), x='hora', y='count')
        hora_lineplot.update_layout(yaxis_title="Tweets")
        hora_lineplot.update_traces(hovertemplate='Hora: %{x}<br>Tweets: %{y}')
        hora_lineplot.update_xaxes(rangeslider_visible=True)
        hora_lineplot.update_layout(margin=dict(l=0, r=0, t=0,b=0), height=220, width=220)
        st.plotly_chart(hora_lineplot, use_container_width=True)
    
    with temp_cols[3]:
        periodo_barplot = go.Figure(data=[go.Bar(x=data_tw2['periodo'].value_counts().index,
                                y=data_tw2['periodo'].value_counts().values,
                                hovertext = round(data_tw2['periodo'].value_counts().reset_index()["count"]/sum(data_tw2['periodo'].value_counts().reset_index()["count"])*100).astype(str) + "%")])
        orden_periodo = ['Mañana','Tarde','Noche']
        periodo_barplot.update_layout(xaxis=dict(categoryorder='array', categoryarray=orden_periodo))
        periodo_barplot.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                    marker_line_width=1.5, opacity=0.6)
        periodo_barplot.update_layout(margin=dict(l=0, r=0, t=0,b=0), height=220, width=220,yaxis_title="Tweets")
        st.plotly_chart(periodo_barplot, use_container_width=True)

    st.header("Tweets por país a través del tiempo")
    data_tw_ubicacion_fecha=data_tw.groupby(['fecha', 'codigo_pais']).size().reset_index(name='tweets')
    data_tw_coordenadas= data_tw_ubicacion_fecha.merge(data_tw[["codigo_pais","Latitud","Longitud","ubicacion"]], on= "codigo_pais",how="right").drop_duplicates()
    animate_map = px.density_mapbox(data_tw_coordenadas.sort_values(by='fecha'), lat='Latitud', lon='Longitud', z='tweets', radius=20, 
                zoom=1,mapbox_style="open-street-map",animation_frame="fecha", color_continuous_scale="Inferno",center=dict(lat=0, lon=0),
                hover_data={"fecha": False,"Latitud":False,"Longitud":False, "ubicacion": True})
    animate_map.update_layout(updatemenus=[dict(type='buttons', showactive=False, buttons=[dict(label='Play',
                                        method='animate', args=[None, dict(frame=dict(duration=1300, redraw=True), fromcurrent=True)]),
                                        dict(label='Pause', method='animate', args=[[None], dict(frame=dict(duration=0, redraw=True), mode='immediate', transition=dict(duration=0))])])])
    animate_map.update_layout(margin=dict(l=0, r=0, t=0,b=0))
    st.plotly_chart(animate_map, use_container_width=True)

with tab5:
    ubicaciones2 = st.selectbox("Ubicación",["Todas las ubicaciones"]+sorted(list(data_tw["ubicacion"].unique())))
    if ubicaciones2 != "Todas las ubicaciones":
        data_tw3 = data_tw[data_tw["ubicacion"] == ubicaciones2]
    else: 
        data_tw3= data_tw
    sentimientos_cols = st.columns(2)
    with sentimientos_cols[0]:
        sentimientos_barplot = go.Figure(data=[go.Bar(x=data_tw3["sentimiento"].value_counts().index,
                                        y=data_tw3["sentimiento"].value_counts().values)])
        sentimientos_barplot.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                                    marker_line_width=1.5, opacity=0.6)
        sentimientos_barplot.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=220, width=220,yaxis_title="Tweets")
        st.plotly_chart(sentimientos_barplot, use_container_width=True)

    with sentimientos_cols[1]:
        sentimientos_donut = px.pie(data_tw3, names='sentimiento', hole=0.3, color='sentimiento',
                                    color_discrete_sequence= ['#1f77b4', '#aec7e8', '#d3d3d3', '#636363'])

        sentimientos_donut.update_traces(opacity=0.8, marker_line=dict(color='rgb(8,48,107)', width=1.5))
        sentimientos_donut.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=220, width=220)
        st.plotly_chart(sentimientos_donut, use_container_width=True)



    stopwords = nltk.corpus.stopwords.words('spanish')
    newStopWords = ['t', "tras", 'co', 'https', 'que', 'el', 'del', 'es', 'la', "m s", 'de', 'un', 'son', 'tambien',
                    'porque', 'cuando', 'lo', 'su', 'pueden', 'hacer', 'le', 'esto', 'nadie', 'yo', 'mas', 'hasta', 'por',
                    'da', 'mi', 'ni', 'estan', 'todo', 'el ', 'con', 'por', 'para', 'la ', 'eso', 'nos', 'dio', 'ello',
                    'es ', 'un ', 'tu', 'donde', 'solo', 'nosotros', 'mas ', 'hace', 'toda', 'toda ', 'si', 'si ', 'lo ',
                    'lo', 'que ', 'la', 'tener', 'tener', 'la', 'que', 'de', 'una', 'todo', 'son', 'esta', 'cual', 'desde',
                    'desde', 'nada', 'esa', 'eso', 'de ', 'te', 'alguna', ' lo', 'cuando', ' donde', 'como']
    stopwords.extend(newStopWords)
    text = ' '.join(data_tw3["tweet"])
    wordcloud = WordCloud(stopwords=stopwords, background_color="white",colormap = "inferno",margin=0).generate(text)
    plt.imshow(wordcloud)
    plt.axis("off")
    st.pyplot(plt.gcf())