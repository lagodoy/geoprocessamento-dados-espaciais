#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 15 11:37:51 2026

@author: leonardo
"""

# Isócronas/áreas de serviço
# Software e dados necessários para a prática de laboratório
import geopandas as gp
from matplotlib import pyplot
import contextily as cx

caminho_base = '/home/leonardo/Documents/usp/PTR3312/labs_r/lab_05/'
limites_subprefeituras = gp.read_file(caminho_base + 'dados/geoportal_subprefeitura_v2.gpkg')
limites_subprefeituras.crs
subprefeitura_selecionada = limites_subprefeituras.loc[limites_subprefeituras['nm_subprefeitura']=='BUTANTA',]
estacoes_metro = gp.read_file(caminho_base + 'dados/geoportal_estacao_metro_v2.geojson')
estacoes_metro.crs

estacoes_metro = gp.sjoin(estacoes_metro, subprefeitura_selecionada, how='inner', predicate='within')
estacoes_metro.columns
estacoes_metro['nm_estacao_metro_trem']
logradouros  = gp.read_file(caminho_base + 'dados/LOG2020_CEM_RMSP/LOG2020_CEM_RMSP.shp')
logradouros.crs
logradouros = logradouros.to_crs('EPSG:31983')
logradouros.crs

logradouros_subprefeitura = gp.clip(logradouros, subprefeitura_selecionada)
logradouros_subprefeitura.columns
logradouros_subprefeitura['NAME'].head()

del logradouros

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Curvas de nivel')
logradouros_subprefeitura.plot(ax=ax,facecolor='none',edgecolor='blue', alpha=1, zorder=1)
estacoes_metro.plot(ax=ax,facecolor='red',edgecolor='red', alpha=1 , zorder=2)
cx.add_basemap(ax=ax, crs=logradouros_subprefeitura.crs, alpha=1, zorder=0, zoom=15,
               source=cx.providers.OpenStreetMap.Mapnik)

# Áreas de serviço
# Apenas sf

import momepy
import networkx
import numpy as np
def calcula_area_servico (ponto_inicio):
    print(ponto_inicio['geometry'])
    ponto_inicio = gp.GeoSeries(ponto_inicio['geometry'],  crs='EPSG:31983')

    service_area_buffer = ponto_inicio.buffer(500)
    logradouros_entorno_estacao = gp.clip(logradouros_subprefeitura, service_area_buffer)
    # Resoluição dos "lixels" (equivalente em linha dos pixels)
    logradouros_entorno_estacao_segmentos = logradouros_entorno_estacao.explode()
    logradouros_entorno_estacao_segmentos['geometry'] = logradouros_entorno_estacao_segmentos.segmentize(0.5)
    logradouros_entorno_estacao_segmentos['peso'] = logradouros_entorno_estacao_segmentos['geometry'].length
    logradouros_entorno_estacao_segmentos 
    graph = momepy.gdf_to_nx(logradouros_entorno_estacao_segmentos, approach="primal",
                           length='peso', integer_labels=False)
    
    nos_rede = np.asarray(list(graph.nodes))
    coordenadas_ponto_estacao = np.array([[ponto_inicio[0].x, ponto_inicio[0].y]])
    coordenadas_ponto_estacao = np.repeat(coordenadas_ponto_estacao, len(nos_rede), axis=0)
    distancia = ((nos_rede[:,0] - ponto_inicio[0].x)**2 + (nos_rede[:,1] - ponto_inicio[0].y)**2)**0.5
    id_menor_distancia = distancia.argmin()
    a = networkx.floyd_warshall_numpy(graph, weight='peso')
    nos_selecionados_distancia = nos_rede[a[id_menor_distancia,:] <= 500]
    geometrias_nos_area_servico = gp.points_from_xy(nos_selecionados_distancia[:,0], nos_selecionados_distancia[:,1], crs='EPSG:31983')
    pontos_area_servico = gp.GeoDataFrame(geometry=geometrias_nos_area_servico)
    area_servico_convex_hull = pontos_area_servico['geometry'].union_all().convex_hull
    
    
    print('Funcionou')
    return(area_servico_convex_hull)

areas_servico_convex_hull = estacoes_metro.apply(calcula_area_servico, axis=1)#, result_type='broadcast')
areas_servico_convex_hull = gp.GeoDataFrame(geometry=areas_servico_convex_hull, crs='EPSG:31983')

area_servico_logradouros = gp.clip(logradouros_subprefeitura, areas_servico_convex_hull)
area_servico_logradouros_linhas = area_servico_logradouros
area_servico_logradouros_linhas = area_servico_logradouros_linhas.loc[area_servico_logradouros['geometry'].geom_type != 'Point',:]

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Subprefeitura - Favelas')
areas_servico_convex_hull.plot(ax=ax, facecolor='blue',edgecolor='blue', alpha=0.5 )
area_servico_logradouros_linhas.plot(ax=ax, facecolor='purple',edgecolor='purple', alpha=1 )
estacoes_metro.plot(ax=ax,facecolor='yellow',edgecolor='yellow', alpha=1 , zorder=2)
subprefeitura_selecionada.plot(ax=ax, facecolor='none',edgecolor='black', alpha=1 , zorder=2)
cx.add_basemap(ax=ax, crs=areas_servico_convex_hull.crs,alpha=1, zorder=0, zoom=15,
               source=cx.providers.OpenStreetMap.Mapnik)


areas_servico_convex_hull.to_file('/home/leonardo/Downloads/convex_hull_python.gpkg')
area_servico_logradouros_linhas.to_file('/home/leonardo/Downloads/logradouros_area_servico_python.gpkg')


# WMS
from owslib.wms import WebMapService
import pandas as pd
url_base_wms = 'https://wms.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wms?'

cliente_wms = WebMapService(url_base_wms, version = "1.3.0")
# Lista as camadas disponíveis.
layers_disponiveis = pd.DataFrame(list(cliente_wms.contents.keys()), columns=['nome_layer'])
print(layers_disponiveis)  

layers_disponiveis
limites_bbox = tuple(subprefeitura_selecionada.to_crs('EPSG:4326').total_bounds)
# https://docs.geoserver.org/main/en/user/services/wms/reference.html#getmap
# Obter uma imagem (ex: OpenStreetMap)
layer_png_arquivo = cliente_wms.getmap(layers=['geoportal:densidade_demografica'], # Camada
                                         srs='EPSG:4326', # Sistema de coordenadas
                                         bbox=limites_bbox, # Bounding Box (lon_min, lat_min, lon_max, lat_max)
                                         size=(4000, 4000), # Tamanho da imagem
                                         format='image/png')

# Salvar a imagem
with open('/home/leonardo/Downloads/mapa_python.png', 'wb') as f:
    f.write(layer_png_arquivo.read())
from matplotlib import pyplot


from matplotlib.offsetbox import OffsetImage#, AnnotationBbox
layer_png_arquivo = pyplot.imread('/home/leonardo/Downloads/mapa_python.png')
limites_imagem = subprefeitura_selecionada.total_bounds.tolist()
extensao_imagem_base = [int(limites_imagem[0]), int(limites_imagem[2]), int(limites_imagem[1]), int(limites_imagem[3])]
f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Subprefeitura - Favelas')
ax.imshow(layer_png_arquivo, extent=extensao_imagem_base)
im = OffsetImage(layer_png_arquivo)
areas_servico_convex_hull.plot(ax=ax, facecolor='blue',edgecolor='blue', alpha=0.5 )
area_servico_logradouros_linhas.plot(ax=ax, facecolor='purple',edgecolor='purple', alpha=1 )
estacoes_metro.plot(ax=ax,facecolor='yellow',edgecolor='yellow', alpha=1 , zorder=2)
subprefeitura_selecionada.plot(ax=ax, facecolor='none',edgecolor='black', alpha=1 , zorder=2)


#  WFS
from owslib.wfs import WebFeatureService
url_base_wfs = 'https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs?'
cliente_wfs = WebFeatureService(url_base_wfs, version = "2.0.0")
import geojson
# Lista as camadas disponíveis.
layers_disponiveis = pd.DataFrame(list(cliente_wfs.contents.keys()), columns=['nome_layer'])
print(layers_disponiveis)

layers_disponiveis


limites_bbox = tuple(subprefeitura_selecionada.geometry.buffer(50).total_bounds)
layer_geopandas = cliente_wfs.getfeature(typename=['geoportal:densidade_demografica'], # Camada
                                         bbox=limites_bbox, # Bounding Box (lon_min, lat_min, lon_max, lat_max)
                                         outputFormat='json')
dados = layer_geopandas.read()
json_string = dados.decode('utf-8')
gp_dados = gp.GeoDataFrame.from_features(geojson.loads(json_string), crs="EPSG:31983")
gp_dados.plot()
gp_dados_centroide = gp_dados.copy(deep=True)
gp_dados_centroide['geometry'] = gp_dados['geometry'].centroid
subprefeitura_selecionada_buff = subprefeitura_selecionada.copy(deep=True)
subprefeitura_selecionada_buff['geometry'] = subprefeitura_selecionada['geometry'].buffer(50)
setores_subprefeitura = gp.sjoin(gp_dados_centroide, subprefeitura_selecionada_buff, how='inner', predicate='within' )
# Use o index para identificar
setores_subprefeitura_poligonos = gp_dados.merge(setores_subprefeitura.drop(columns='geometry'),  how='inner', left_index=True, right_index=True)
setores_subprefeitura_poligonos.plot()

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Subprefeitura - Favelas')
areas_servico_convex_hull.plot(ax=ax, facecolor='blue',edgecolor='blue', alpha=0.5 , zorder=3)
area_servico_logradouros_linhas.plot(ax=ax, facecolor='purple',edgecolor='purple', alpha=1, zorder=4)
estacoes_metro.plot(ax=ax,facecolor='yellow',edgecolor='yellow', alpha=1 , zorder=5)
subprefeitura_selecionada.plot(ax=ax, facecolor='none',edgecolor='black', alpha=1 , zorder=1)
setores_subprefeitura_poligonos.plot(ax=ax, column='qt_habitante_hectare_x', alpha=0.8 , zorder=2)
cx.add_basemap(ax=ax, crs=areas_servico_convex_hull.crs,alpha=1, zorder=0, zoom=15,
               source=cx.providers.OpenStreetMap.Mapnik)

# Metadados do WFS
# Aqui, descreve-se os parãmetros disponiveis para efetuar operações no WFS do servidor.
# GetCapabilities: Generates a metadata document describing a WFS service provided by server as well as valid WFS operations and parameters

# Metadados do sistema e das bases disponibilizadas.
nomes_layers_acesso = cliente_wfs.contents
dict_metadado = {'nomes_layers_acesso': [],
                 'dados_layer': [],
                 'descricao_layer': []}
for layer_disponivel in nomes_layers_acesso.items():
    dict_metadado['nomes_layers_acesso'].append(layer_disponivel[0])
    dict_metadado['dados_layer'].append(layer_disponivel[1].title)
    dict_metadado['descricao_layer'].append(layer_disponivel[1].abstract)
descricao_features_disponiveis = pd.DataFrame.from_dict(dict_metadado)

descricao_features_disponiveis.head()

# Metadados de uma feature específica.
# Por bug da biblioteca e por ser uma versão "estática" de um arquivo que pode ser
# baixada, vamos usar outra abordagem, criarndo uma url.
url_metadados_feature = url_base_wfs + '?service=wfs&' +\
                                    'version=2.0.0&' +\
                                    'request=DescribeFeatureType&' +\
                                    'typeName=geoportal:densidade_demografica'

import urllib.request
from lxml import etree
with urllib.request.urlopen(url_metadados_feature) as f:
    metadata_feature_xsd = etree.fromstring(f.read())#.decode('utf-8'))

# Checando os tipos de dados na tabela de atributos.
dict_tabela_metadados = {'atributos':[], 'tipos_atributos':[]}
for elemento in metadata_feature_xsd.findall(".//{*}*/{*}sequence//{*}element"):
    dict_tabela_metadados['atributos'].append(elemento.get("name"))
    dict_tabela_metadados['tipos_atributos'].append(elemento.get("type"))
tabela_metadados = pd.DataFrame.from_dict(dict_tabela_metadados)

tabela_metadados.head()
