#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 10:54:28 2026

@author: leonardo
"""

# Preparação dos dados no GEE
import numpy as np
import rasterio

from matplotlib import pyplot


caminho_base = '/home/leonardo/Documents/usp/PTR3312/labs_r/lab_08/'
caminho_arquivo = caminho_base + 'dados/sr_rad_correct.tif'

src_raster = rasterio.open(caminho_arquivo)
dados_raster = src_raster.read(masked=True)
dados_raster.shape
dados_raster = dados_raster.transpose(1, 2, 0)

extensao = [src_raster.bounds[0], src_raster.bounds[2], src_raster.bounds[1], src_raster.bounds[3]]
# Aritmética raster e manipulação de dados pixel a pixel. Vamos tirar os pixels
# mais saturados do visível para eliminar possíveis nuvens de forma primitiva.
selecao = np.logical_and.reduce(dados_raster[:, :, 0:3].data > 100, axis = 2)
# Adicione a última banda com um corte para  < 50.

imagem_sem_nuvens = dados_raster.copy()
mascara = np.logical_or(imagem_sem_nuvens[:, :, 0].mask, selecao)

imagem_sem_nuvens.mask = np.repeat(mascara[:, :, np.newaxis], 4, 2)

imagem_sem_nuvens
pyplot.imshow(imagem_sem_nuvens[:,:,0], vmin=0, vmax=500, 
              interpolation='kaiser', interpolation_stage='rgba',
              extent=extensao,  cmap='viridis')
# Visualiza as bandas separadamente
# Sem nenhum ajuste.
import math
f, ax = pyplot.subplots(2, 2, figsize=(12, 12), alpha=0)
#ax.set_aspect('equal')
mapa_red = ax[0,0].imshow(imagem_sem_nuvens[:,:,0], 
               vmin=0, vmax=math.ceil(imagem_sem_nuvens[:,:,0].max() / 100) * 100,
               interpolation='bilinear', interpolation_stage='rgba',
              extent=extensao,  cmap='viridis')
ax[0,0].set_title('Red')
pyplot.colorbar(mapa_red, ax=ax[0, 0])

mapa_green = ax[0,1].imshow(imagem_sem_nuvens[:,:,1], 
               vmin=0, vmax=math.ceil(imagem_sem_nuvens[:,:,1].max() / 100) * 100,
               interpolation='bilinear', interpolation_stage='rgba',
              extent=extensao,  cmap='viridis')
ax[0,1].set_title('Green')
pyplot.colorbar(mapa_green, ax=ax[0, 1])
mapa_blue = ax[1,0].imshow(imagem_sem_nuvens[:,:,2], 
               vmin=0, vmax=math.ceil(imagem_sem_nuvens[:,:,2].max() / 100) * 100,
               interpolation='bilinear', interpolation_stage='rgba',
              extent=extensao,  cmap='viridis')
ax[1,0].set_title('Blue')
pyplot.colorbar(mapa_blue, ax=ax[1, 0])

mapa_nir = ax[1,1].imshow(imagem_sem_nuvens[:,:,3], 
               vmin=0, vmax=math.ceil(imagem_sem_nuvens[: ,: , 3].max() / 100) * 100,
               interpolation='bilinear', interpolation_stage='rgba',
              extent=extensao,  cmap='viridis')
ax[1,1].set_title('NIR')
pyplot.colorbar(mapa_nir, ax=ax[1, 1])
pyplot.show()

# Visualiza uma composição colorida.
# Ajusta para 0-1 considerando os percentis para 0.02 e 0.98.
def ajuste_linear(imagem, min_entrada, max_entrada, min_saida, max_saida):
    imagem_ajustada = ((imagem - min_entrada)/(max_entrada - min_entrada))*(max_saida - min_saida) + min_saida
    return(np.clip(imagem_ajustada, min_saida, max_saida))

# Ajuste por percentis.
#ind_validos = [~imagem_sem_nuvens.mask[:, :, id_banda].flatten() for id_banda in range(3)]
ind_validos = [~dados_raster[:, :, id_banda].mask.flatten() for id_banda in range(3)]

quantidade_ind_validos = [sum(ind_validos_banda) for ind_validos_banda in ind_validos]

ind_validos = ind_validos[quantidade_ind_validos.index(min(quantidade_ind_validos))]
percentis = [np.quantile(imagem_sem_nuvens.data[: ,: , id_banda].flatten()[ind_validos], [0.02, 0.98])
              for id_banda in range(3)]
percentis = np.array(percentis)
min_bandas = percentis[:, 0]
max_bandas = percentis[:, 1] 

min_saida = 0
max_saida = 1

# Ajuste.
composicao_mapa = [ajuste_linear(imagem_sem_nuvens[:, :, 0:3].data[:, : , id_banda],
                                             min_bandas[id_banda], max_bandas[id_banda], 
                                             min_saida, max_saida)
                               for id_banda in [0, 1, 2]]


banda_alpha = np.array([(~imagem_sem_nuvens.mask[:,:,0]).astype(float)]).transpose(1, 2, 0)
composicao_mapa = np.array(composicao_mapa).transpose(1, 2, 0)
composicao_mapa = np.append(composicao_mapa, banda_alpha, axis=2)
pyplot.imshow(composicao_mapa, interpolation='bilinear', 
              interpolation_stage='rgba', extent=extensao)


# Calculando o NDVI
ndvi = (dados_raster[: , :, 3]- dados_raster[: , :, 0])/(dados_raster[: , :, 0] + dados_raster[: , :, 3])

dados_raster = np.ma.append(dados_raster, ndvi[:, :, np.newaxis], axis=2)
#dados_raster.fill_value = np.nan
# Copia os metadados (profile) do primeiro arquivo.
profile_tiff = src_raster.profile
    
profile_tiff.update(
    nodata=np.nan, # Float
    dtype='float32', # Tipos de dados armazenados nas bandas conforme o numpy.
    count=dados_raster.shape[2], # Quantidade de bandas (profundidade do array).
    #compress='lzw'# Caso deseje comprimir o aruquivo.
)

# Agora vamos juntar todas as bandas em um único tiff.
arquivo_raster_completo = caminho_base + 'dados/sr_rad_correct_ndvi_python.tif'
# open() cria uma conexão com o arquivo destino.
with rasterio.open(arquivo_raster_completo, 'w', **profile_tiff) as tiff_destino:
    # Aqui deve se conhecer os tipos e distribuição dos valores dos dados armazenados.
    # Para tipo inteiro, use algum valor específico, para float você pode usar np.nan.
    # O valor específico deve estar fora do range dos dados. Para os dados aqui
    # utilizados, sabemos que o valor 0 é o utilizado. Um padrão utilizado é inserir o menor
    # valor possível (em alguns casos negativo) para ser o no data.
    # Note que o valor já está nos metadados (profile), mas a linha abaixo demonstra como
    # forçar o valor de nodata.
    tiff_destino.nodata = np.nan
    tiff_destino.write(dados_raster.transpose(2, 0, 1))
    tiff_destino.set_band_description(1, 'red')
    tiff_destino.set_band_description(2, 'green')
    tiff_destino.set_band_description(3, 'blue')
    tiff_destino.set_band_description(4, 'nir')
    tiff_destino.set_band_description(5, 'ndvi')

# Visualiza a banda ndvi.
mapa_ndvi = pyplot.imshow(ndvi, cmap='gray', interpolation='bilinear', 
                          interpolation_stage='rgba', extent=extensao)
pyplot.colorbar(mapa_ndvi)
pyplot.show()

# Executando o algoritmo do k-means no Python

# Calcula a distancia para cada centroide e atribui como cluster a menor.

# Kmeans terra
from sklearn.cluster import KMeans

total_clusters = 5
dados_raster.shape
print([dados_raster[:, :, id_banda].min() for id_banda in range(5)])
print([dados_raster[:, :, id_banda].max() for id_banda in range(5)])
print([dados_raster[:, :, id_banda].mean() for id_banda in range(5)])
print([dados_raster[:, :, id_banda].std() for id_banda in range(5)])

dados_kmeans = [dados_raster[: , :, id_banda].flatten() for id_banda in range(5)]
dados_kmeans = np.ma.array(dados_kmeans)
dados_kmeans.shape

dados_kmeans = [dados_kmeans[id_banda].data[ind_validos] for id_banda in range(5)]
dados_kmeans = np.array(dados_kmeans).transpose(1,0)
dados_kmeans.shape
# Padroniza os dados para média 0 e 1 desvio padrão.
dados_kmeans = [(dados_kmeans[:, id_banda] - dados_kmeans[:, id_banda].mean())/dados_kmeans[:, id_banda].std() 
                for id_banda in range(5)]
dados_kmeans = np.array(dados_kmeans).transpose(1, 0)

print([dados_kmeans[:, id_banda].mean() for id_banda in range(5)])
print([dados_kmeans[:, id_banda].std() for id_banda in range(5)])
# Veja a documentação para detalhes da implementação.
resultado_kmeans = KMeans(n_clusters=total_clusters, random_state=None, n_init="auto").fit(dados_kmeans)

print(resultado_kmeans.labels_)
print(resultado_kmeans.cluster_centers_)

id_cluster, total = np.unique(resultado_kmeans.labels_, return_counts=True)
print(np.array([id_cluster, total]).transpose(1,0))
pyplot.bar(id_cluster, total)
resultado_kmeans.labels_

imagem_clusters = np.array([0] * (composicao_mapa.shape[0] * composicao_mapa.shape[1]))

for id_cluster in range(5):
    ind_clusters = np.where(ind_validos)[0][resultado_kmeans.labels_ == id_cluster]
    imagem_clusters[ind_clusters.tolist()] = id_cluster

imagem_clusters = imagem_clusters.reshape(imagem_sem_nuvens[:,:,0].shape[0],
                                          imagem_sem_nuvens[:,:,0].shape[1], 1)
imagem_clusters = np.ma.masked_array(imagem_clusters, dados_raster[:,:,0].mask)
pyplot.imshow(imagem_clusters, extent=extensao)

import colorsys
def calcula_nivel_cinza_medio(id_cluster):
    # Cria lista com zeros.
    nivel_cinza_medio = []
    for id_banda in range(3):
        ind_cluster = resultado_kmeans.labels_ == id_cluster
        valor_pixels = composicao_mapa[: ,: , id_banda].flatten()
        valor_medio = valor_pixels[ind_validos][ind_cluster].mean()
        
        # composicao_mapa está entre 0 e 1, que é o range para as funções
        # em colorsys.
        nivel_cinza_medio.append(valor_medio)
    
    cluster_cor_media_hsv = colorsys.rgb_to_hsv(r = nivel_cinza_medio[0],
                                  g = nivel_cinza_medio[1], 
                                  b = nivel_cinza_medio[2])
    cluster_cor_media_hsv = list(cluster_cor_media_hsv)

    cluster_cor_media_hsv[1] = 0.9
    cluster_cor_media_hsv[2] = 0.5    
    cor_cluster = colorsys.hsv_to_rgb(h = cluster_cor_media_hsv[0], 
                                      s = cluster_cor_media_hsv[1], 
                                      v = cluster_cor_media_hsv[2])        
    #cor_cluster = [ int(255*cor_cluster[i]) for i in range(3) ]

    return(tuple(cor_cluster))

import matplotlib.colors
cores_rgb_cluster = [calcula_nivel_cinza_medio(id_cluster) for id_cluster in range(5)]
mapa_cores_clusters = matplotlib.colors.ListedColormap(cores_rgb_cluster)
mapa_clusters = pyplot.imshow(imagem_clusters, cmap=mapa_cores_clusters,
                              interpolation='nearest', interpolation_stage='rgba',
                              extent=extensao)
pyplot.colorbar(mapa_clusters)
pyplot.show()

# Seleção de número de clusters ótimo com a regra do cotovelo.
# Exercicio.