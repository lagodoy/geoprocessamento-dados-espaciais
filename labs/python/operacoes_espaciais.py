#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 10:16:17 2025

@author: leonardo
"""

# 1. Introdução
# Labarotório para introduzir o uso de operações espaciais no python, focando 
# especialmente no geopandas.

# 2. Preparação dos dados
# Normalmente a informação de encoding fica no arquivo com extensão .cpg do conjunto
# do shapefile lido, caso não exista, a atribuição será um charset padrão. Abra os dataframes para checar
# se as strings estão com caracteres estranhos. No caso dos dados do CEM testados (até o momento) não há
# o arquivo cpg e pode haver esse problema. Caso ele ocorra, use o parâmetro options = "ENCODING=latin1",
# confome última linha do bloco de códigos abaixo.
# 2.1 Leitura dos dados
import geopandas as gp
from matplotlib import pyplot
import contextily as cx
caminho_base = '~/Documents/usp/PTR3312/labs_r/lab_02/'
dados_favelas = gp.read_file(caminho_base + 'dados/SIRGAS_SHP_favela/SIRGAS_SHP_favela.shp')
dados_subprefeituras = gp.read_file(caminho_base + 'dados/SIRGAS_SHP_subprefeitura/SIRGAS_SHP_subprefeitura.shp')
dados_saude = gp.read_file(caminho_base + 'dados/SAU2022_RMSP_CEM/SAU2022_RMSP_CEM.shp')


# 2.2 Checagem dos CRS's e atribuiççao ou transformaççao quando necessaŕio.
print(dados_favelas.crs)
print(dados_subprefeituras.crs)
print(dados_saude.crs)
dados_favelas = dados_favelas.set_crs(epsg=31983)
dados_subprefeituras = dados_subprefeituras.set_crs(epsg=31983)

dados_saude = dados_saude.to_crs(31983)

print(dados_favelas.crs)
print(dados_subprefeituras.crs)
print(dados_saude.crs)
# 3. Seleção por atributo e Operações espaciais
# 3.1 Seleção por atributo
dados_favelas
dados_subprefeituras['sp_nome']
selecao_subprefeitura = dados_subprefeituras['sp_nome']=='BUTANTA'
limites_subprefeitura = dados_subprefeituras[selecao_subprefeitura]

# 3.2 Clipping
favelas_subprefeitura = gp.clip(dados_favelas, limites_subprefeitura)
f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Subprefeitura - Favelas')
limites_subprefeitura.plot(ax=ax,facecolor='none',edgecolor='blue', alpha=1 )
favelas_subprefeitura.plot(ax=ax,facecolor='red',edgecolor='red', alpha=1 )
cx.add_basemap(ax=ax, crs=limites_subprefeitura.crs,alpha=1, zorder=0, zoom=15,
               source=cx.providers.OpenStreetMap.Mapnik)

# 3.3 Como exercício, faça o mesmo para a base de dados de saúde, selecionando
# somente os equipamentos públicos de alta complexidade.
saude_alta_complexidade = dados_saude[(dados_saude['SEGMENTO'].isin(['SAUGM', 'SAUGE']))
                                       & (dados_saude['TIPO'] =='HOSP') |(dados_saude['TIPO'] == 'PATEN')]

saude_subprefeitura = gp.sjoin(saude_alta_complexidade, limites_subprefeitura, how="inner", predicate ='within')
f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Subprefeitura - Favelas \n Equipamentos de Saúde Públicos de Alta Complexidade')
limites_subprefeitura.plot(ax=ax,facecolor='none',edgecolor='blue', alpha=1 )
favelas_subprefeitura.plot(ax=ax,facecolor='red',edgecolor='red', alpha=1 )
saude_subprefeitura.plot(ax=ax,facecolor='black',edgecolor='black', alpha=1 )
cx.add_basemap(ax=ax, crs=limites_subprefeitura.crs,alpha=1, zorder=0, zoom=12,
               source=cx.providers.OpenStreetMap.Mapnik)


# 3.4 Buffering
saude_subprefeitura_buffer = saude_subprefeitura.copy(deep=True)
saude_subprefeitura_buffer['geometry'] = saude_subprefeitura.geometry.buffer(2000)
f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Subprefeitura - Favelas\nEquipamentos de Saúde Públicos de Alta Complexidade\nAlcance do equipamento - 2km')
limites_subprefeitura.plot(ax=ax,facecolor='none',edgecolor='blue', alpha=1 )
favelas_subprefeitura.plot(ax=ax,facecolor='red',edgecolor='red', alpha=1 )
saude_subprefeitura.plot(ax=ax,facecolor='black',edgecolor='black', alpha=1 )
saude_subprefeitura_buffer.plot(ax=ax,facecolor='none',edgecolor='black', alpha=1 )
cx.add_basemap(ax=ax, crs=limites_subprefeitura.crs,alpha=1, zorder=0, zoom=12,
               source=cx.providers.OpenStreetMap.Mapnik)

# 3.5 Intersecção
favelas_cobertura = gp.clip(favelas_subprefeitura, saude_subprefeitura_buffer)

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Subprefeitura - Favelas\n' +\
             'Equipamentos de Saúde Públicos de Alta Complexidade\n' +\
             'Alcance do equipamento - 2km\n' +\
             'Favelas dentro em área de alcance de equipamento')
limites_subprefeitura.plot(ax=ax,facecolor='none',edgecolor='blue', alpha=1 )
favelas_subprefeitura.plot(ax=ax,facecolor='red',edgecolor='red', alpha=1 )
saude_subprefeitura.plot(ax=ax,facecolor='black',edgecolor='black', alpha=1 )
saude_subprefeitura_buffer.plot(ax=ax,facecolor='none',edgecolor='black', alpha=1 )
favelas_cobertura.plot(ax=ax,facecolor='green',edgecolor='green', alpha=1 )
cx.add_basemap(ax=ax, crs=limites_subprefeitura.crs,alpha=1, zorder=0, zoom=12,
               source=cx.providers.OpenStreetMap.Mapnik)



# 3.6 Difference
favelas_fora_raio = gp.overlay(favelas_subprefeitura, saude_subprefeitura_buffer.dissolve(), how='difference')

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Subprefeitura - Favelas\n' +\
             'Equipamentos de Saúde Públicos de Alta Complexidade\n' +\
             'Alcance do equipamento - 2km\n' +\
             'Favelas dentro em área de alcance de equipamento e\n' +\
             'Favelas fora de área de alcance de equipamento')
limites_subprefeitura.plot(ax=ax,facecolor='none',edgecolor='blue', alpha=1 )
favelas_subprefeitura.plot(ax=ax,facecolor='none',edgecolor='red', alpha=1 )
saude_subprefeitura.plot(ax=ax,facecolor='black',edgecolor='black', alpha=1 )
saude_subprefeitura_buffer.plot(ax=ax,facecolor='none',edgecolor='black', alpha=1 )
favelas_cobertura.plot(ax=ax,facecolor='green',edgecolor='none', alpha=1 )
favelas_fora_raio.plot(ax=ax,facecolor='purple',edgecolor='none', alpha=1 )
cx.add_basemap(ax=ax, crs=limites_subprefeitura.crs,alpha=1, zorder=0, zoom=12,
               source=cx.providers.OpenStreetMap.Mapnik)

