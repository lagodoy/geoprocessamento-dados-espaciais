# -*- coding: utf-8 -*-
"""
Editor Spyder

Este é um arquivo de script temporário.
"""

# Sensoriamento Remoto:
# Introdução ao processamento digital de imagens

# Delimitando os limites da área de interesse
import geopandas as gp
from matplotlib import pyplot
import contextily as cx
caminho_base = '/home/leonardo/Documents/usp/PTR3312/labs_r/lab_06/'
limites_subprefeituras = gp.read_file(caminho_base + 'dados/geoportal_subprefeitura_v2.gpkg')
limites_subprefeituras.crs
limites_subprefeituras = limites_subprefeituras.to_crs(crs='EPSG:32723')

# Buscando uma coleção de imagens
# MUX 
# https://data.inpe.br/geonetwork/srv/api/records/7594a5c2-82f9-4d31-8065-28185bd94d3c
# - B05 (Azul) : 0,45 - 0,52 µm
# - B06 (Verde): 0,52 - 0,59 µm
# - B07 (Vermelho): 0,63 - 0,69 µm
# - B08 (Infravermelho próximo): 0,77 - 0,89 µm

# Trabalhando com imagens de satélite

# Carregando as bandas separadamente e empilhando para criar um arquivo completo com todas.
import rasterio
import numpy as np
import rasterio.plot
nome_base_arq_mux = caminho_base + 'dados/cbers_4a_mux/CBERS_4A_MUX_20240624_203_142_L4_BAND'

red_mux = nome_base_arq_mux +  '7.tif'
green_mux = nome_base_arq_mux + '6.tif'
blue_mux = nome_base_arq_mux + '5.tif'
nir_mux = nome_base_arq_mux + '8.tif'

arquivos_entrada = [red_mux, green_mux, blue_mux, nir_mux]

lista_bandas = []
for caminho_arquivo in arquivos_entrada:
    with rasterio.open(caminho_arquivo) as tiff_entrada:
        # Lê mascarando valores fora da área.
        lista_bandas.append(tiff_entrada.read(1, masked=True))

arrays_bandas_mux = np.ma.stack(lista_bandas, axis=0)
del lista_bandas

# Copia os metadados (profile) do primeiro arquivo.
with rasterio.open(arquivos_entrada[0]) as src:
    profile_mux = src.profile
    
profile_mux

profile_mux.update(
    nodata=int(0), # Inteiro
    dtype=arrays_bandas_mux.dtype, # Tipos de dados armazenados nas bandas conforme o numpy.
    count=arrays_bandas_mux.shape[0], # Quantidade de bandas (profundidade do array).
    #compress='lzw'# Caso deseje comprimir o aruquivo.
)

# Agora vamos juntar todas as bandas em um único tiff.
arquivo_raster_completo = caminho_base + 'dados/lab_python.tiff'
# open() cria uma conexão com o arquivo destino.
with rasterio.open(arquivo_raster_completo, 'w', **profile_mux) as tiff_destino:
    # Aqui deve se conhecer os tipos e distribuição dos valores dos dados armazenados.
    # Para tipo inteiro, use algum valor específico, para float você pode usar np.nan.
    # O valor específico deve estar fora do range dos dados. Para os dados aqui
    # utilizados, sabemos que o valor 0 é o utilizado. Um padrão utilizado é inserir o menor
    # valor possível (em alguns casos negativo) para ser o no data.
    # Note que o valor já está nos metadados (profile_mux), mas a linha abaixo demonstra como
    # forçar o valor de nodata.
    tiff_destino.nodata = int(0)
    tiff_destino.write(arrays_bandas_mux)
    tiff_destino.set_band_description(1, 'red')
    tiff_destino.set_band_description(2, 'green')
    tiff_destino.set_band_description(3, 'blue')
    tiff_destino.set_band_description(4, 'nir')

# Agora podemos ler o arquivo criado fazendo uma conexão.
imagem_mux = rasterio.open(arquivo_raster_completo)
    
# Extraindo informações básicas das imagens.
# Extensão da imagem, quantidade de linhas e crs.
dimensoes_mux = imagem_mux.shape
dimensoes_mux

imagem_mux.read([1,2,3,4], masked=True)
extensao = imagem_mux.bounds
extensao
type(extensao)
imagem_mux.transform
imagem_mux.read_crs()


# Visualizando uma imagem com terra em RGB.
rasterio.plot.show(imagem_mux, adjust=False) # por padrão pega as tres primeiras bandas

# # Visualizando com RGB com stretch.
# Preparando a imagem para ser plotada. A função imshow do pyplot para plotar uma 
# imagem RGB precisa de uma quarta banda, conhecida com alpha da imagem, que 
# representa a transparência de cada pixel. Vamos converter uma máscara (valores booleanos)
# das três bandas da fonte de dados para valores d e acordo com o tipo
# nas bandas RGB e inserir nessa quarta banda. Note a negação para inverter 
# True e False, pois o primeivo deve ir para 1.0 e o segundo para 0.0. 
# Além disso, multiplicamos por 255 pois é o que o pyplot esperaria para bandas
# com int (para float o valores devem ser entre 0.0 e 1.0). Imagine que a função
# interpresta que há um stretch na banda alpha automaticamente, caso inteiro.
# A função transpose reorganiza os eixos de acordo com o indicado pela função
# imshow.
extensao_tiff = rasterio.plot.plotting_extent(imagem_mux)
imagem_mux_plot = imagem_mux.read([1,2,3], masked=True).transpose(1, 2, 0)
# Banda que será usada como máscara.
banda_alpha = np.array([(~imagem_mux_plot.mask[:,:,0]).astype(int)*255]).transpose(1, 2, 0)

# Vamos fazer um leve ajuste para melhor visualizar a imagem.
# Para funcionar um ajuste linear por banda, precisamos ajustar cada banda individualmente.
# Limitação dos masked arrays no numpy!
banda = np.ma.masked_array(imagem_mux_plot.data[:,:,0], mask=imagem_mux_plot.mask[:,:,0])
min_banda = banda.min()
max_banda = banda.max()
imagem_mux_plot[:,:,0] = ((imagem_mux_plot[:,:,0] - min_banda) / (max_banda - min_banda)) * 255
imagem_mux_plot[:,:,0] = np.clip(imagem_mux_plot[:,:,0], 0, 255).astype(np.uint8)


banda = np.ma.masked_array(imagem_mux_plot.data[:,:,1], mask=imagem_mux_plot.mask[:,:,0])
min_banda = banda.min()
max_banda = banda.max()
imagem_mux_plot[:,:,1] = ((imagem_mux_plot[:,:,1] - min_banda) / (max_banda - min_banda)) * 255
imagem_mux_plot[:,:,1] = np.clip(imagem_mux_plot[:,:,1], 0, 255).astype(np.uint8)

banda = np.ma.masked_array(imagem_mux_plot.data[:,:,2], mask=imagem_mux_plot.mask[:,:,0])
min_banda = banda.min()
max_banda = banda.max()
imagem_mux_plot[:,:,2] = ((imagem_mux_plot[:,:,2] - min_banda) / (max_banda - min_banda)) * 255
imagem_mux_plot[:,:,2] = np.clip(imagem_mux_plot[:,:,2], 0, 255).astype(np.uint8)


imagem_mux_plot = imagem_mux_plot.data
# Observe as dimensões e os eixos.
banda_alpha.shape
imagem_mux_plot.shape
imagem_mux_plot = np.append(imagem_mux_plot, banda_alpha, axis=2)

pyplot.imshow(imagem_mux_plot, extent=extensao_tiff)

# Localização da área de estudo
# Para saber qual a área de estudos, após ter baixado os dados adequadamente. 
# Carregue uma imagem, pegue a sua extensão como poligono (bounding bod, bbox, da imagem)
# e calcule a centróide desse bbox.
import geopandas as gp
from shapely.geometry import Polygon
extensao
min_x = extensao[0]
max_x = extensao[2]
min_y = extensao[1]
max_y = extensao[3]

coordenadas_extensao = [(min_x, max_y), (max_x, max_y), (max_x, min_y), (min_x, min_y), (min_x, max_y)]
extensao_poly = gp.GeoDataFrame(geometry=[Polygon(coordenadas_extensao)], crs="epsg:32723")
# extensao mapa completa, caso corte alguma parte.
extensao_mapa = extensao_poly.copy(deep=True)
extensao_mapa['geometry'] = extensao_poly.geometry.buffer(10000)
# Note q nao ha sitema de referencias e Voce precisa atribuir um crs.
# Visualizacao simples
extensao_poly.plot()

centroide_poly = gp.GeoDataFrame(geometry=[extensao_poly.union_all().centroid], crs="epsg:32723")

# Agora podemos visualizar os dados que coletamos até agora.
# A partir do mapa gerado, você pode escolher o nome da subprefeitura de interesse
# clicando dentro do bbox da imagem em uma área de subprefeitura onde os pixels 
# tenham valores e aparentem ter uma melhor qualidade de informações.
# Obs: a função resample usada para reduzir a imagem será explicada posteriormente
# Obs2:  Caso a imagem não cubra uma porção interia de uma subprefeitura (ou tenha
# muitas nuvens na região), volte alguns passos e carregue uma outra imagem para testar.

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Imagem MUX')
extensao_poly.plot(ax=ax, facecolor='none', edgecolor='red', alpha=1, zorder=4)
extensao_mapa.plot(ax=ax, facecolor='none', edgecolor='none', alpha=1)
centroide_poly.plot(ax=ax, facecolor='blue', edgecolor='blue', alpha=1, zorder=3)
limites_subprefeituras.plot(ax=ax, facecolor='none', edgecolor='blue', alpha=1, zorder=2)
# Cuidado com o zoom. A área é gigante.
cx.add_basemap(ax=ax, crs=limites_subprefeituras.crs,alpha=1, zorder=0, zoom=8,
               source=cx.providers.OpenStreetMap.Mapnik)

pyplot.imshow(imagem_mux_plot, 
              extent=extensao_tiff, zorder=1)
pyplot.show()


# Recortando uma parte de uma imagem
# SE até aqui está tudo ok, agora podemos selecionar uma área para trabalharmos melhor.
# A partir do layer de subprefeituras, filtre apenas a escolhida no item anterior.
limites_subprefeituras['nm_subprefeitura']
area_interesse = limites_subprefeituras[limites_subprefeituras['nm_subprefeitura']=="FREGUESIA-BRASILANDIA"]
min_x, min_y, max_x, max_y = area_interesse['geometry'].total_bounds
resolucao_x = imagem_mux.res[0] # A mesma do raster.
resolucao_y = imagem_mux.res[1]

n_linhas =  round((max_y - min_y)/resolucao_y)
n_colunas = round((max_x - min_x)/resolucao_x)
#transformacao = rasterio.Affine(resolucao_x, 0, min_x, 0, -resolucao_y, max_y) 
mascara_subprefeitura = [limites['geometry'] for limites in area_interesse.iterfeatures()]

#import rasterio.features
# raster_mascara = rasterio.features.rasterize(
#                     mascara_subprefeitura,
#                     out_shape=(n_linhas, n_colunas), # Shape é o mesmo pq é o mesmo bbox.
#                     transform=transformacao,
#                     fill=0,              # Value for pixels *outside* the polygons
#                     default_value=1,
#                     dtype=np.uint8,
#                     all_touched=False) # Transformação é a mesma pq é o mesmo bbox.

import rasterio.mask
recorte_area = rasterio.mask.mask(imagem_mux, area_interesse['geometry'], 
                                  all_touched=True,
                                  crop=True, filled=False, indexes=[1, 2, 3])

# Visualizando com RGB
#rasterio.plot.show(imagem_mux, adjust=True, alpha=0) # max-min (0-1)
# muda os eixos para uso em imshow.
recorte_area_plot = recorte_area[0].transpose(1,2,0).copy()
# Para plotar, vamos usar a máscara como alpha (banda 4 na ordem).
# im show infere a ordem automaticamente
banda_alpha = np.array([(~recorte_area_plot.mask[:,:,0]).astype(int)*255]).transpose(1, 2, 0)

# Vamos fazer um leve ajuste para melhor visualizar a imagem.
# Para funcionar um ajuste linear por banda, precisamos ajustar cada banda individualmente.
# Limitação dos masked arrays no numpy!
banda = np.ma.masked_array(recorte_area_plot.data[:,:,0], mask=recorte_area_plot.mask[:,:,0])
min_banda = banda.min()
max_banda = banda.max()
recorte_area_plot[:,:,0] = ((recorte_area_plot[:,:,0] - min_banda) / (max_banda - min_banda)) * 255
recorte_area_plot[:,:,0] = np.clip(recorte_area_plot[:,:,0], 0, 255).astype(np.uint8)


banda = np.ma.masked_array(recorte_area_plot.data[:,:,1], mask=recorte_area_plot.mask[:,:,0])
min_banda = banda.min()
max_banda = banda.max()
recorte_area_plot[:,:,1] = ((recorte_area_plot[:,:,1] - min_banda) / (max_banda - min_banda)) * 255
recorte_area_plot[:,:,1] = np.clip(recorte_area_plot[:,:,1], 0, 255).astype(np.uint8)

banda = np.ma.masked_array(recorte_area_plot.data[:,:,2], mask=recorte_area_plot.mask[:,:,0])
min_banda = banda.min()
max_banda = banda.max()
recorte_area_plot[:,:,2] = ((recorte_area_plot[:,:,2] - min_banda) / (max_banda - min_banda)) * 255
recorte_area_plot[:,:,2] = np.clip(recorte_area_plot[:,:,2], 0, 255).astype(np.uint8)

recorte_area_plot = recorte_area_plot.data
# Observe as dimensões e os eixos.
banda_alpha.shape
recorte_area_plot.shape
recorte_area_plot = np.append(recorte_area_plot, banda_alpha, axis=2)

pyplot.imshow(recorte_area_plot[:, :, :],
              extent=[min_x, max_x, min_y, max_y], zorder=1)

# Visualização com os limites da subprefeitura e mapa base. depdendendo do tamanho da área, é possível plotar o raster
# no mapview.
coordenadas_extensao = [(min_x, max_y), (max_x, max_y), (max_x, min_y), (min_x, min_y), (min_x, max_y)]
extensao_mapa = gp.GeoDataFrame(geometry=[Polygon(coordenadas_extensao)], crs="epsg:32723")


f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Imagem MUX')
extensao_mapa.plot(ax=ax, facecolor='none', edgecolor='none', alpha=1)
area_interesse.plot(ax=ax, facecolor='none', edgecolor='blue', alpha=1, zorder=2)
# Cuidado com o zoom. A área é gigante.
cx.add_basemap(ax=ax, crs=limites_subprefeituras.crs,alpha=1, zorder=0, zoom=12,
               source=cx.providers.OpenStreetMap.Mapnik)

pyplot.imshow(recorte_area_plot, 
              extent=[min_x, max_x, min_y, max_y], zorder=1)
pyplot.show()

# Calculando o valor médio dos pixels de uma banda
# Primeiro na imagem clipada.
recorte_area[0][0,:,:].mean()
recorte_area[0][1,:,:].mean()
recorte_area[0][2,:,:].mean()


# Para o tiff todo, ou quando as áreas tiverem muitos pixels, recomendo utilizar uma amostra
import random
# Índices válidos.
ind_validos = np.where(imagem_mux.read(1, masked=True).mask.flatten() == False)[0]
ind_sample_mux = ind_validos[random.sample(range(0, len(ind_validos) - 1), k=10000)]
amostra_banda_mux = [imagem_mux.read(1).flatten()[ind_sample_mux],
                     imagem_mux.read(2).flatten()[ind_sample_mux],
                     imagem_mux.read(3).flatten()[ind_sample_mux],
                     imagem_mux.read(4).flatten()[ind_sample_mux]]
[banda.mean() for banda in amostra_banda_mux]

# Você pode fazer uma amostra apenas dentro do recorte para comparar.

# VOce pode fazer tudo isso individualmente para cada banda. Exercício.


# Resolução espacial
imagem_mux.res


# Tipos armazenados nas bandas e resolução radiométrica
imagem_mux.dtypes

# Resolução espectral
# A faixa espectral (“Wavelength”) de cada banda, encontrada na documentação do satélite.

# Resolução temporal
# Tambem pode ser encontrada na documentaçao do satelite.

# Trabalhando com metadados via código
# Metadados
# Em memória.
imagem_mux.meta
imagem_mux.profile
imagem_mux.tags()

# No arquivo xml fornecido.
from lxml import etree
metadados_xml_red_mux_arvore = etree.parse(nome_base_arq_mux + '7.xml')
metadados_xml_red_mux = metadados_xml_red_mux_arvore.getroot()

print(etree.tostring(metadados_xml_red_mux, pretty_print=True).decode())
lista_namespaces_xml = metadados_xml_red_mux.nsmap
type(lista_namespaces_xml)
lista_namespaces_xml = list(lista_namespaces_xml.values())
lista_namespaces_xml
tag_raiz = metadados_xml_red_mux.tag
tag_raiz = tag_raiz.replace("{" + lista_namespaces_xml[0] + "}", "")
for elemento in metadados_xml_red_mux.iter():
    path_completo = metadados_xml_red_mux_arvore.getelementpath(elemento)
    path_completo = path_completo.replace(lista_namespaces_xml[0], "")
    path_completo = path_completo.replace(lista_namespaces_xml[1], "")
    path_completo = path_completo.replace("{", "")
    path_completo = path_completo.replace("}", "")
    print('/' + tag_raiz + '/' + path_completo)
    

# Bandas, projeção cartográfica e resolução espacial
# Bandas.
namespace_string = "{" + lista_namespaces_xml[0] +"}"
for elemento in metadados_xml_red_mux.findall(".//" + namespace_string + "availableBands/"):
    print(elemento.text)
# projeção cartográfica
# CRS. OBS: Essa inforamção na verdade fica embutida dentro do cabeça~jho do arquivo Tif.
# O XML auxiliar é normalmente utilizado para algumas informações extras que não são suportadas pelo formato GEOTIFF.
# No caso dos dados do CBERS temos uma breve descrição do CRS, mas não completa.
# O que estaria faltando?
for elemento in metadados_xml_red_mux.findall(".//" + namespace_string + "image/" + namespace_string + "datumName"):
    print(elemento.text)

for elemento in metadados_xml_red_mux.findall(".//" + namespace_string + "image/" + namespace_string + "projectionName"):
    print(elemento.text)

# Resolucao
metadados_xml_red_mux.find(".//" + namespace_string + "image/" + namespace_string + "verticalPixelSize").text
metadados_xml_red_mux.find(".//" + namespace_string + "image/" + namespace_string + "horizontalPixelSize").text    
 
# datas das imagens
import pandas as pd
dict_tabela_metadados = {'momento':[], 'hora':[]}
for elemento in metadados_xml_red_mux.findall(".//" + namespace_string + "image/" + namespace_string + "timeStamp/*"):
    dict_tabela_metadados['momento'].append(elemento.tag.replace("{" + lista_namespaces_xml[0] + "}", ""))
    dict_tabela_metadados['hora'].append(elemento.text)

tabela_metadados = pd.DataFrame.from_dict(dict_tabela_metadados)

print(tabela_metadados)

# Exemplos de cálculos
import numpy.ma as ma
# Se possível leia uma segunda imagem para testar.
red_mux = imagem_mux.read(1, masked=True)
# Range dos dados.
red_mux.ptp()
# Versão para dados masked.
ma.ptp(red_mux)
# Range calculado manualmente.
red_mux.max() - red_mux.min() 

# Intervalo interquartil.
ind_validos = np.where(red_mux.mask.flatten() == False)[0]
tamanho_amostra = int(0.1*len(ind_validos))
ind_amostra = ind_validos[random.sample(range(0, len(ind_validos) - 1), k=tamanho_amostra)]
amostra_banda_red = red_mux.data.flatten()[ind_sample_mux]# {ind_validos]}
quantis = np.quantile(amostra_banda_red, [0.25, 0.75])
quantis
quantis[1] - quantis[0]

# Salva um raster.
resolucao_x = imagem_mux.res[0] # A mesma do raster.
resolucao_y = imagem_mux.res[1]
min_x = imagem_mux.bounds[0]
max_y = imagem_mux.bounds[3]
transformacao = rasterio.Affine(resolucao_x, 0, min_x, 0, -resolucao_y, max_y)
# Coloca os eixos na posição correta para o metodo write.
imagem_mux_saida = imagem_mux_plot.transpose(2,0,1) 
caminho_raster_saida = '/home/leonardo/Downloads/teste_imagem_python.tiff'
with rasterio.open(
    caminho_raster_saida,
    'w',
    driver='GTiff',
    height=imagem_mux_saida.shape[1],
    width=imagem_mux_saida.shape[2],
    count=imagem_mux_saida.shape[0], # Number of bands
    dtype='uint8', #imagem_mux_saida.dtype,
    crs='EPSG:31983', # Example CRS
    transform=transformacao,
) as dst:
    dst.nodata = 0#np.nan # nan é para float.
    dst.write(imagem_mux_saida)
    
teste = rasterio.open(caminho_raster_saida)
teste.read().shape







# Indo além:
# Você pode definir funções para calcular automaticamente os ajustes das imagens.
# Abaixo está demonstrado como fazer isso para um simples ajuste min-max.
# Ajuste linear min-max entre 0-255
def ajuste_linear(imagem, min_entrada, max_entrada, min_saida, max_saida):
    return(((imagem - min_entrada)/(max_entrada - min_entrada))*(max_saida - min_saida) + min_saida)

def ajuste_linear_min_max(imagem, min_saida, max_saida):
    min_entrada = imagem.min()
    max_entrada = imagem.max()
    return(ajuste_linear(imagem, min_entrada, max_entrada, min_saida, max_saida))
a = imagem_mux.read([1,2,3], masked=True)
ajuste_linear_min_max
teste = np.apply_along_axis(ajuste_linear_min_max,0, a, min_saida=0, max_saida=255)
teste = [ajuste_linear_min_max(row, 0, 1) for row in a]
rasterio.plot.show(np.array(teste), alpha=mascara_plot)


# Proximo lab
# Falsa cor - Infravermelho Colorido
falsa_cor_infra = imagem_mux.read(indexes=(4,1,2)).transpose(1,2,0)
pyplot.imshow(falsa_cor_infra, extent=extensao_tiff)

# Falsa cor - Vegetação
falsa_cor_vegetacao = imagem_mux.read(indexes=(1,4,2)).transpose(1,2,0)
pyplot.imshow(falsa_cor_vegetacao, extent=extensao_tiff)