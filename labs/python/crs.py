#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 15 11:47:34 2025

@author: leonardo
"""
import geopandas as gp
# A biblioteca mapview é utilizada para visualização de dados espaciais em mapas iterativos. 
# Aqui, é utilizado a função mapinfo para criar um mapa sem nenhum dado adicionado e utilizando como base o OpenStreetMap.
# pip install folium
# pip install folium
#import folium
from matplotlib import pyplot
import contextily as cx
#m = folium.Map(location=(45.5236, -122.6750), tiles="OpenStreetMap")

# Ache atraves de um servico de mapas online as coordenadas maximas e minimas desejadas.
xmin, ymin = -46.74, -23.64
xmax, ymax = -46.70, -23.57
# Cria um espaço para alocar o plot.
f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
ax.set_aspect('equal') 
# Adicionando mapa base do OSM.
cx.add_basemap(ax=ax, crs='epsg:4326',alpha=1, zorder=0, zoom=13)
pyplot.show()

# Para carregar dados vetoriais, pode ser utilizada a função read_sf do pacote sf. 
# Nesse caso, a função recebe simplesmente o caminho para o arquivo .shp como parâmetro.
# O resultado é colocado na variável dados_corticos.
# Em seguida, novamente é utilizada a função mapview, desta vez ela recebe como parâmetro
# a variável com os dados baixados do geosampa. Observe o erro que ocorre por falta do
# arquivo .prj indicando qual deve ser o CRS da base de dados.
# A seguir, cheque como está o CRS dos dados com a função st_crs do pacote sf. Essa
# função gera uma lista que pode ser de difícil visualização.
caminho_base = '~/Documents/usp/PTR3312/labs_r/lab_01/'
dados_corticos = gp.read_file(caminho_base + 'dados/SAD69-96_SHP_cortico/SAD69-96_SHP_cortico.shp')

#Detalhes do objeto CRS.
dados_corticos.crs
print(dados_corticos.crs)
dados_corticos.plot(ax=ax,facecolor='blue',edgecolor='blue', alpha=1 )
cx.add_basemap(ax=ax, crs=dados_corticos.crs,alpha=1, zorder=0, zoom=10)
#mapview::mapview(dados_corticos, map.types="OpenStreetMap")

# É possível visualizar o atributo com
# o EPSG usando chamando diretamente nas geometrias associadas ao dataframe espacial.
dados_corticos.geometry.crs
print(dados_corticos.geometry.crs)

# Como  não há CRS associado, precisamos ajustá-lo, mas primeiro vamos checar os
# detalhes do EPSG 5533 (SAD69(96) - 23S) com o mesmo comando utilizado para o dataframe espacial.
# Note como o método consegue lidar com parâmetros de tipo diferente.
# SAD69(96) / UTM zone 23S: https://epsg.io/5533
from pyproj import CRS

# Create a CRS object for WGS 84 (latitude/longitude)
crs_sad69 = CRS.from_epsg(5533)
crs_sad69
print(crs_sad69)

# Ajusta o CRS.
dados_corticos=dados_corticos.set_crs(epsg=5533)
dados_corticos.crs
print(dados_corticos.crs)

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal') 
dados_corticos.plot(ax=ax,facecolor='blue',edgecolor='blue', alpha=1 )
cx.add_basemap(ax=ax, crs=dados_corticos.crs,alpha=1, zorder=0, zoom=12)

#mapview::mapview(dados_corticos, map.types="OpenStreetMap")

# SIRGAS 2000 / UTM zone 23S: https://epsg.io/31983
dados_corticos_sirgas = dados_corticos.to_crs(31983)
f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal') 
dados_corticos_sirgas.plot(ax=ax,facecolor='none',edgecolor='green', alpha=1 )
cx.add_basemap(ax=ax, crs=dados_corticos_sirgas.crs,alpha=1, zorder=0, zoom=12)


#mapview::mapview(dados_corticos_sirgas, map.types="OpenStreetMap")
# Verifique que eles estão perfeitamente sobrepostos.
f, ax = pyplot.subplots(1,2, figsize=(12, 12), alpha=0)
ax[0].set_aspect('equal') 
ax[1].set_aspect('equal') 
dados_corticos.plot(ax=ax[0],facecolor='blue',edgecolor='blue', alpha=1 )
dados_corticos_sirgas.plot(ax=ax[1],facecolor='blue',edgecolor='green', alpha=1 )
cx.add_basemap(ax=ax[0], crs=dados_corticos.crs, alpha=1, zorder=0, zoom=12)
cx.add_basemap(ax=ax[1], crs=dados_corticos_sirgas.crs, alpha=1, zorder=0, zoom=12)
#mapview::mapview(dados_corticos_sirgas, map.types="OpenStreetMap") + mapview::mapview(dados_corticos)

# Salvando os dados com CRS definitivamente.
# Ssalva o arquivo corrigido. Note que é criado agora um prj.
arquivo_corrigido = caminho_base + 'dados/SAD69-96_SHP_cortico/SAD69-96_SHP_cortico.shp'
dados_corticos.to_file(arquivo_corrigido)

arquivo_reprojetado = caminho_base + 'dados/SIRGAS2000_SHP_cortico/SIRGAS2000_SHP_cortico.shp'
import os
os.makedirs(caminho_base + 'dados/SIRGAS2000_SHP_cortico/' , exist_ok=True)
dados_corticos_sirgas.to_file(arquivo_reprojetado)


# Releia o arquivo e cheque que o CRS está ajustado corretamente.
dados_corticos_sirgas = gp.read_file(arquivo_reprojetado)
print(dados_corticos_sirgas.crs)
