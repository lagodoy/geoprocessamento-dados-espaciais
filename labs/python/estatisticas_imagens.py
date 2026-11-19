#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 12:41:20 2026

@author: leonardo
"""

# Estatísticas, histogramas, contraste e composições de imagens

##  Preparação dos dados
# Neste lab vamos usar os dados  WPM do CBERS 4.0. Vamos trabalhar apenas com os
# DN, por falta de informaçõs para se obter a reflectância. Apesar disso,
# correção atmosférica simples com DOS será feita.
import rasterio
import numpy as np
import geopandas as gp
caminho_base = '/home/leonardo/Documents/usp/PTR3312/labs_r/lab_07/'
nome_base = caminho_base + 'dados/cbers_4a_wpm/CBERS_4A_WPM_20240529_202_143_L4_BAND'

red = nome_base +  '3.tif'
green = nome_base + '2.tif'
blue = nome_base + '1.tif'
nir = nome_base + '4.tif'

arquivos_entrada = [red, green, blue, nir]

lista_bandas = []
for caminho_arquivo in arquivos_entrada:
    with rasterio.open(caminho_arquivo) as tiff_entrada:
        # Lê mascarando valores fora da área.
        lista_bandas.append(tiff_entrada.read(1, masked=True))

arrays_bandas = np.ma.stack(lista_bandas, axis=0)

del lista_bandas

# Copia os metadados (profile) do primeiro arquivo.
with rasterio.open(arquivos_entrada[0]) as src:
    profile_tiff = src.profile
    
profile_tiff

profile_tiff.update(
    nodata=int(0), # Inteiro
    dtype=arrays_bandas.dtype, # Tipos de dados armazenados nas bandas conforme o numpy.
    count=arrays_bandas.shape[0], # Quantidade de bandas (profundidade do array).
    #compress='lzw'# Caso deseje comprimir o aruquivo.
)

# Agora vamos juntar todas as bandas em um único tiff.
arquivo_raster_completo = caminho_base + 'dados/lab07_python.tiff'
# open() cria uma conexão com o arquivo destino.
with rasterio.open(arquivo_raster_completo, 'w', **profile_tiff) as tiff_destino:
    # Aqui deve se conhecer os tipos e distribuição dos valores dos dados armazenados.
    # Para tipo inteiro, use algum valor específico, para float você pode usar np.nan.
    # O valor específico deve estar fora do range dos dados. Para os dados aqui
    # utilizados, sabemos que o valor 0 é o utilizado. Um padrão utilizado é inserir o menor
    # valor possível (em alguns casos negativo) para ser o no data.
    # Note que o valor já está nos metadados (profile), mas a linha abaixo demonstra como
    # forçar o valor de nodata.
    tiff_destino.nodata = int(0)
    tiff_destino.write(arrays_bandas)
    tiff_destino.set_band_description(1, 'red')
    tiff_destino.set_band_description(2, 'green')
    tiff_destino.set_band_description(3, 'blue')
    tiff_destino.set_band_description(4, 'nir')

# Agora podemos ler o arquivo criado fazendo uma conexão.
imagem = rasterio.open(arquivo_raster_completo)
    
# Extraindo informações básicas das imagens.
# Extensão da imagem, quantidade de linhas e crs.
dimensoes = imagem.shape
dimensoes

imagem.read([1,2,3,4], masked=True)


# Agora podemos ler o arquivo criado fazendo uma conexão.
imagem = rasterio.open(arquivo_raster_completo)

# Limites para recorte da área de interesse.
limites_subprefeituras = gp.read_file(caminho_base + 'dados/geoportal_subprefeitura_v2.gpkg')
limites_subprefeituras = limites_subprefeituras.to_crs(crs='EPSG:32723')

# Encontra a melhor área

## Redução da resolução.
from rasterio.enums import Resampling
fator_resolucao = 10
imagem_reduzida = imagem.read(1, out_shape=(
                1, # Quantidade de bandas.
                int(imagem.height/fator_resolucao),
                int(imagem.width/fator_resolucao)
            ), 
            resampling = Resampling.average,
            masked=True)

transformacao = imagem.transform * imagem.transform.scale(
        (imagem.width / imagem_reduzida.shape[-1]),
        (imagem.height / imagem_reduzida.shape[-2])
    )


caminho_raster_saida = '/home/leonardo/Downloads/imagem_area_python.tiff'
imagem_reduzida_saida = imagem_reduzida.reshape(1, imagem_reduzida.shape[0], imagem_reduzida.shape[1])
with rasterio.open(
    caminho_raster_saida,
    'w',
    driver='GTiff',
    height=imagem_reduzida.shape[0],
    width=imagem_reduzida.shape[1],
    count=1, # Number of bands
    dtype='int16', #imagem_mux_saida.dtype,
    crs='EPSG:32723', # Example CRS
    transform=transformacao,
) as dst:
    dst.nodata = -9999#np.nan # nan é para float.
    dst.write(imagem_reduzida_saida)

from matplotlib import pyplot
extensao = imagem.bounds
extensao
min_x = extensao[0]
max_x = extensao[2]
min_y = extensao[1]
max_y = extensao[3]
extensao_tiff = [min_x, max_x, min_y, max_y]
pyplot.imshow(imagem_reduzida, extent=extensao_tiff)

# Calcula as áreas da imagem disponíveis em cada subprefeitura.
import rasterio.mask
import pandas as pd

src_imagem_reduzida = rasterio.open(caminho_raster_saida, masked=True)

def calcula_area_coberta_tiff (area):
    # area Chega aqui como Series. Sim, o python faz isso.
    # shapes precisa ser iterável, por isso os colchetes para formar uma lista.
    resolucao = src_imagem_reduzida.res
    pixels_area = rasterio.mask.mask(src_imagem_reduzida, shapes=[area.geometry], 
                                     crop = True, all_touched=False)
    # Remove nodata antes da estatistica ser calculada.
    pixels_area_validos = np.ma.masked_values(pixels_area[0], -9999)
    
    # Transforma em dataframe, para calcular um sumário com um único comando.
    # Essa é uma limitação do python. flatten deixa a matrix em formato 1-d.
    pixels_area_validos = pixels_area_validos.flatten()
    area_total = sum(~pixels_area_validos.mask) * resolucao[0] * resolucao[1]
    proporcao_coberta = 100 * area_total/area.geometry.area
    df_area = pd.DataFrame({'subprefeitura': [area['nm_subprefeitura']], 
                  'area_subprefeitura': [area_total], 
                  'area_coberta': [proporcao_coberta]})
    #print(df_area)
    return(df_area)
# Proporção da área coberta.           
areas_cobertas_subprefeituras = limites_subprefeituras.apply(lambda area: calcula_area_coberta_tiff(area), axis=1)
areas_cobertas_subprefeituras = pd.concat(areas_cobertas_subprefeituras.to_list())
# Ordena pela cobertura.
areas_cobertas_subprefeituras = areas_cobertas_subprefeituras.sort_values(by='area_coberta', ascending=[False])
# Verifique as áreas com cerca de 100% de cobertura pela imagem e escolha uma para trabalhar.
areas_cobertas_subprefeituras[areas_cobertas_subprefeituras['area_coberta'] > 99.0]

# Cria uma uma seleção da área de interesse.
# Você pode escolher uma área de interesse pelo nome, mas caso queria achar uma 
# área que tenha uma boa parte da imagem, o código seguinte acha a proporção de cada
# subprefeitura que contém imagem.

limites_subprefeituras.columns

area_interesse = limites_subprefeituras[limites_subprefeituras['nm_subprefeitura'] == 'IPIRANGA']

#Observe como funciona o parâmetro touches em mask
# all_touched : bool (opt)
#     Include a pixel in the mask if it touches any of the shapes.
#     If False (default), include a pixel only if its center is within one of
#     the shapes, or if it is selected by Bresenham's line algorithm.
teste_false = rasterio.mask.mask(src_imagem_reduzida, shapes=area_interesse['geometry'], 
                                 filled=False, crop = True, all_touched=False)
teste_false
teste_false[0].shape
teste_false[1]
min_x = teste_false[1][2]
max_x = min_x + teste_false[1][0] * (teste_false[0].shape[2])
max_y = teste_false[1][5] #+ teste_false[1][4]
min_y = max_y + teste_false[1][4] * (teste_false[0].shape[1])
print([min_x, max_x, min_y, max_y])
extensao_false = [min_x, max_x, min_y, max_y]
area_interesse.bounds

pyplot.imshow(teste_false[0].transpose(1,2,0), extent=extensao_false)


teste_true = rasterio.mask.mask(src_imagem_reduzida, shapes=area_interesse['geometry'], 
                                 filled=False, crop = True, all_touched=True)
teste_true
teste_true[0].shape
teste_true[1]
min_x = teste_true[1][2]
max_x = min_x + teste_true[1][0] * (teste_true[0].shape[2])
max_y = teste_true[1][5] 
min_y = max_y + teste_true[1][4] * (teste_true[0].shape[1])
print([min_x, max_x, min_y, max_y])
area_interesse.bounds
extensao_true = [min_x, max_x, min_y, max_y]
pyplot.imshow(teste_true[0].transpose(1,2,0), extent=extensao_true)

#centroides_raster <- terra::as.points(teste_true, values = FALSE, na.rm = TRUE)
#centroides_raster <- sf::st_as_sf(centroides_raster)

import contextily as cx

# Usando o parâmetro all_touched como False.

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Teste all_touched=False')
# Adicionando mapa base do OSM.
# A linha a seguir é uma gambiarra para o plot não se perder.
area_interesse.plot(ax=ax, facecolor='none', edgecolor='blue', alpha=1, zorder=2)
cx.add_basemap(ax=ax, crs=area_interesse.crs, alpha=1, zorder=0)
pyplot.imshow(teste_false[0].transpose(1,2,0), extent=extensao_false, alpha=0.7, zorder=1)
pyplot.show()

# Usando o parâmetro all_touched como True.

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Teste all_touched=True')
# Adicionando mapa base do OSM.
# A linha a seguir é uma gambiarra para o plot não se perder.
area_interesse.plot(ax=ax, facecolor='none', edgecolor='blue', alpha=1, zorder=2)
cx.add_basemap(ax=ax, crs=area_interesse.crs, alpha=1, zorder=0)
pyplot.imshow(teste_true[0].transpose(1,2,0), extent=extensao_true, alpha=0.7, zorder=1)

pyplot.show()

imagem_area_interesse = rasterio.mask.mask(imagem, shapes=area_interesse['geometry'], 
                                 filled=False, crop = True, all_touched=True)

pixels_imagem = imagem_area_interesse[0].transpose(1,2,0)
transformacao = imagem_area_interesse[1]
imagem_area_interesse_plot = pixels_imagem[:, :, 0:3]
imagem_area_interesse_plot.dtype
imagem_area_interesse_plot = imagem_area_interesse_plot.astype('int16')
banda_alpha = np.array([(~imagem_area_interesse_plot.mask[:,:,0]).astype(int)*255]).transpose(1, 2, 0)
imagem_area_interesse_plot = np.append(imagem_area_interesse_plot, banda_alpha, axis=2)
pyplot.imshow(imagem_area_interesse_plot, extent=extensao_true)


# "Correção atmosférica" (na verdade um ajuste) simples com DOS. Usualmente indicado
# para comparar séries temporais de imagens.
import random
# Índices válidos.
mascara = pixels_imagem.mask
ind_validos = np.where(mascara[: ,: , 0].flatten() == False)[0]
ind_sample = ind_validos[random.sample(range(0, len(ind_validos) - 1), k=10000)]
amostra_bandas = [pixels_imagem.data[: ,: , 0].flatten()[ind_sample],
                     pixels_imagem.data[: ,: , 1].flatten()[ind_sample],
                     pixels_imagem.data[: ,: , 2].flatten()[ind_sample],
                     pixels_imagem.data[: ,: , 3].flatten()[ind_sample]]
# Usa percentil 1% de cada banda.
L1 = [np.quantile(banda, [0.01]) for banda in amostra_bandas]

id_bandas_imagem = range(0, pixels_imagem.shape[2])
# retorna lista
teste = [pixels_imagem.data[:, : , id_banda] - L1[id_banda] for id_banda in id_bandas_imagem]
import numpy.ma as ma

composicao_final = ma.masked_array(np.array(teste).transpose(1,2,0), mascara)
composicao_final = np.clip(composicao_final, a_min=0, a_max=1024)
composicao_final.dtype
composicao_final = composicao_final.astype('int16')
composicao_colorida = composicao_final[:, :, 0:3].copy()
banda_alpha = np.array([(~composicao_final.mask[:,:,0]).astype(int)*255]).transpose(1, 2, 0)
composicao_colorida = np.append(composicao_colorida, banda_alpha, axis=2)

pyplot.imshow(composicao_colorida, extent=extensao_true)
pixels_imagem = composicao_final
#imagem_area_interesse[0] = pixels_imagem
del imagem_area_interesse

# Exibindo valores de um pixel
# coordenadas vs linha/coluna vs Célula []
linha = random.sample(range(0, (pixels_imagem.shape[0] - 1)), k=1)[0]
coluna = random.sample(range(0, (pixels_imagem.shape[1] - 1)), k=1)[0]
pixels_imagem.data[linha, coluna, :]

# Em uma coordenadas específica, passando um ponto como referência. xy como TRUE
# retornajunto dos valores as coordenadas.
resolucao = imagem.res
x_min = transformacao[2]
y_max = transformacao[5]

# Vamos calcular as coordendas do centro do pixel sorteado.
coordenadas = [(x_min + (resolucao[0]/2 + resolucao[0] * (coluna)),
                       y_max - (resolucao[1]/2 + resolucao[1] * (linha)))]

for pixel in imagem.sample(coordenadas):
    print(f"Valores do pixel: {pixel}")

# Exercício: Você consegue encontrar o valor do pixel da centróide do polígono
# utilizando as posições de linhas e colunas ou o número da célula a partir das suas coordenadas?


# Estatísticas dos dados de uma imagem
# O mais simple é, após a leitura, fazer a análise utilizando o numpy.
# No laboratorio anterior fizemos algo similar.
# Para o tiff todo, ou quando as áreas tiverem muitos pixels, recomendo utilizar uma amostra
import random
# Índices dos pixels com valores não clipados.
ind_validos = np.where(pixels_imagem[:, :, 0].mask.flatten() == False)[0]
ind_sample = ind_validos[random.sample(range(0, len(ind_validos) - 1), k=int(len(ind_validos)*0.1))]
amostra_banda = [pixels_imagem[:, :, 0].flatten()[ind_sample],
                     pixels_imagem[:, :, 1].flatten()[ind_sample],
                     pixels_imagem[:, :, 2].flatten()[ind_sample],
                     pixels_imagem[:, :, 3].flatten()[ind_sample]]
[banda.mean() for banda in amostra_banda]
[banda.min() for banda in amostra_banda]
[banda.max() for banda in amostra_banda]
[banda.std() for banda in amostra_banda]
[np.median(banda) for banda in amostra_banda]
[np.quantile(banda, [0.25, 0.75]) for banda in amostra_banda]

# Normalizando os valores da imagem
# Lembre que se a imagem for muito grande, você pode usar uma amostra.
min_bandas = [pixels_imagem[:, :, id_banda].min()
              for id_banda in range(4)]
max_bandas = [pixels_imagem[:, :, id_banda].max()
              for id_banda in range(4)]
# Formula: (x-x_min)/(x_max-x_min)

imagem_normalizada = [(pixels_imagem.data[:, :, id_banda] - min_bandas[id_banda])/(max_bandas[id_banda] - min_bandas[id_banda]) 
                      for id_banda in range(4)]

imagem_normalizada = ma.masked_array(np.array(imagem_normalizada).transpose(1,2,0), mascara)
[imagem_normalizada[:, :, id_banda].min()
              for id_banda in range(4)]

[imagem_normalizada[:, :, id_banda].max()
              for id_banda in range(4)]
[imagem_normalizada[:, :, id_banda].std()
              for id_banda in range(4)]

#  Gerando Histogramas no python
# Lembre-se de usar amostras, caso a imagem seja grande.
f, ax = pyplot.subplots(2, 2, figsize=(12, 12), alpha=0)
ax[0,0].hist(imagem_normalizada[:,:,0].flatten()[ind_validos], bins=100, color='red')
ax[0,1].hist(imagem_normalizada[:,:,1].flatten()[ind_validos], bins=100, color='green')
ax[1,0].hist(imagem_normalizada[:,:,2].flatten()[ind_validos], bins=100, color='blue')
ax[1,1].hist(imagem_normalizada[:,:,3].flatten()[ind_validos], bins=100, color='purple')
pyplot.show()

f, ax = pyplot.subplots(2, 2, figsize=(12, 12), alpha=0)
ax[0,0].hist(pixels_imagem[:,:,0].flatten()[ind_validos], bins=100, color='red')
ax[0,1].hist(pixels_imagem[:,:,1].flatten()[ind_validos], bins=100, color='green')
ax[1,0].hist(pixels_imagem[:,:,2].flatten()[ind_validos], bins=100, color='blue')
ax[1,1].hist(pixels_imagem[:,:,3].flatten()[ind_validos], bins=100, color='purple')
pyplot.show()


#  Exibindo e ajustando o contraste de uma imagem
# ajuste linear para exibição
# Pode dar erro por ter valores fora do domínio.
# Neste caso, pelo tipo de dado, os valores podem estar além de 255. Precisamos ajustar
# para o intervalo correto para usar a função plotRGB. Note que o parâmetro scale pode ser ajustado
# para o máximo valor possível nas bandas, mas um erro ocorre se os valores dos pixels não forem ajustados
# adequadamente para um valores inferiores a 255.
# Ajuste para 0-1. Cuidado com a função scale quando a imagem possuir grandes dimensões.

# Monocromatico

# Realce min-max
min_saida = 0
max_saida = 1

# Banda vermelha ajustada linearmente usando o mínimo e máximo absoluto da imagem.
# Preencha com os valores encontrados anteriormente.
min_bandas
max_bandas
nivel_min = 0
nivel_max = 967
imagem_ajustada_min_max = ((pixels_imagem[:, :, 0] - nivel_min)/(nivel_max - nivel_min))*(max_saida - min_saida) + min_saida
imagem_ajustada_min_max = imagem_ajustada_min_max.clip(0,1)

# Banda vermelha ajustada em min-max escolhendo valores minimo e maximo visualmente no histograma
# para evitar outliers.
# Preencha com valores encontrados visualmente pelo histograma. Escolha
# um corte onde os valores estão concentrados.
nivel_min_hist = 0
nivel_max_hist = 200

imagem_ajustada_hist = ((pixels_imagem[:, :, 0] - nivel_min_hist)/(nivel_max_hist - nivel_min_hist))*(max_saida - min_saida) + min_saida
imagem_ajustada_hist = imagem_ajustada_hist.clip(0,1)

# Sem nenhum ajuste.
f, ax = pyplot.subplots(2, 2, figsize=(12, 12), alpha=0)
#ax.set_aspect('equal')
ax[0,0].imshow(pixels_imagem[:,:,0], 
              extent=extensao_true,  cmap='Reds')
ax[0,0].set_title('Sem ajuste')
ax[0,1].imshow(imagem_ajustada_min_max, 
              extent=extensao_true,  cmap='Reds')
ax[0,1].set_title('Min-Max')
ax[1,0].imshow(imagem_ajustada_hist, 
              extent=extensao_true,  cmap='Reds')
ax[1,0].set_title('Min-Max pelo histogram')
ax[1,1].imshow(imagem_normalizada[:,:,0], 
              extent=extensao_true,  cmap='Reds')
ax[1,1].set_title('Valores normalizados 0-1')
pyplot.show()


# Composição colorida com ajuste de contraste das bandas
def ajuste_linear(imagem, min_entrada, max_entrada, min_saida, max_saida):
    imagem_ajustada = ((imagem - min_entrada)/(max_entrada - min_entrada))*(max_saida - min_saida) + min_saida
    return(np.clip(imagem_ajustada, min_saida, max_saida))


min_saida = 0
max_saida = 1

# Ajuste por percentis.
percentis = [np.quantile(imagem_normalizada.data[: ,: , id_banda].flatten()[ind_validos], [0.01, 0.99])
              for id_banda in range(4)]
percentis = np.array(percentis)
min_entrada = percentis[:, 0]
max_entrada = percentis[:, 1] 
imagem_lin_stretch = [ajuste_linear(imagem_normalizada.data[:, : , id_banda],
                                             min_entrada[id_banda], max_entrada[id_banda], 
                                             min_saida, max_saida)
                               for id_banda in id_bandas_imagem]
# Uso float
banda_alpha = np.array([(~composicao_final.mask[:,:,0]).astype(float)]).transpose(1, 2, 0)
imagem_lin_stretch = np.array(imagem_lin_stretch).transpose(1, 2, 0)
imagem_lin_stretch = np.append(imagem_lin_stretch, banda_alpha, axis=2)
imagem_lin_stretch.min()
imagem_lin_stretch.max()
# Agora a banda 5 é nosso alpha.
imagem_lin_stretch.shape

# Vamos colocar os valores entre 0 e 1 usando como referência a média mais 2 desvios padrão.
media_bandas = [imagem_normalizada[:, :, id_banda].mean()
              for id_banda in range(4)]
dp_bandas = [imagem_normalizada[:, :, id_banda].std()
              for id_banda in range(4)]

quantidade_dps = 2

min_entrada = [media - 2*dp 
             for media, dp in zip(media_bandas, dp_bandas)]

max_entrada = [media + 2*dp 
             for media, dp in zip(media_bandas, dp_bandas)]

imagem_stretch = [ajuste_linear(imagem_normalizada.data[:, : , id_banda],
                                             min_entrada[id_banda], max_entrada[id_banda], 
                                             min_saida, max_saida)
                               for id_banda in id_bandas_imagem]
# Uso float
# uso a mesma banda alpha.
imagem_stretch = np.array(imagem_stretch).transpose(1, 2, 0)
imagem_stretch = np.append(imagem_stretch, banda_alpha, axis=2)
imagem_stretch.min()
imagem_stretch.max()
# Agora a banda 5 é nosso alpha.
imagem_stretch.shape

# Composição colorida da imagem normalizada.
imagem_normalizada_plot = np.append(imagem_normalizada[:,:,0:3], banda_alpha, axis=2)
# Plot as composições coloridas RGB.
f, ax = pyplot.subplots(1, 3, figsize=(12, 12), alpha=0)
ax[0].imshow(imagem_normalizada_plot, 
              extent=extensao_true)
ax[0].set_title('Imagem normalizada')
ax[2].imshow(imagem_stretch[:, :, np.r_[0:3,4]], 
              extent=extensao_true)
ax[2].set_title('Ajuste media +/- 2*dp')
ax[1].imshow(imagem_lin_stretch[:, :, np.r_[0:3,4]], 
              extent=extensao_true)
ax[1].set_title('Ajuste percentis')

pyplot.show()

# Falsa cor - Infravermelho Colorido
pyplot.imshow(imagem_stretch[:, :, np.r_[3, 0:2, 4]], extent=extensao_true)
pyplot.show()
# Falsa cor - Vegetação
pyplot.imshow(imagem_stretch[:, :, np.r_[0, 3, 2, 4 ]], extent=extensao_true)
pyplot.show()