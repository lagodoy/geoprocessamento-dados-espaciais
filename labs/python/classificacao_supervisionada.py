#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 18:15:16 2026

@author: leonardo
"""

# Preparação dos dados
# Carregamento dos dados
import numpy as np
import rasterio
from matplotlib import pyplot
caminho_base = '/home/leonardo/Documents/usp/PTR3312/labs_r/lab_09/'
caminho_arquivo = caminho_base + 'dados/sr_rad_correct_ndvi.tif'

src_raster = rasterio.open(caminho_arquivo)
dados_raster = src_raster.read(masked=True)
dados_raster.shape
dados_raster = dados_raster.transpose(1, 2, 0)

extensao = [src_raster.bounds[0], src_raster.bounds[2], src_raster.bounds[1], src_raster.bounds[3]]

# Classificação supervisionada no GEE
# Preparação das amostras
# Deve ser feito em ambiente externo, por exemplo no Qgis. Crie polígonos envolvendo regiões com
# pixels de determinadas classes, sempre os identificando com algum nome (ou número inteiro).
# Ex: 
# 1 - Vegetacao alta
# 2 - Vegetacao Rasterira
# 3 - Agua
# 4 - Construcoes
# 5 - Solo exposto

# Delimitação das áreas das amostras
# Gerando as amostras automaticamente no GEE
# Amostragem com todos os pixels nas áreas
import geopandas as gp
import rasterio.mask
areas_amostras = gp.read_file( caminho_base + 'dados/amostras.shp')
areas_amostras
areas_amostras.crs
areas_amostras['classe']
import pandas as pd
def seleciona_amostras(classe):
    pixels_amostra = rasterio.mask.mask(src_raster, areas_amostras[areas_amostras['classe'] == classe]['geometry'], 
                                      all_touched=True,
                                      crop=True, filled=False)
    print(classe)
    ind_validos = ~pixels_amostra[0].mask[0, :, :].flatten()
    valores_pixels = [pixels_amostra[0].data[id_banda, :, :].flatten()[ind_validos] 
                      for id_banda in range(5)]
    valores_pixels = np.vstack(valores_pixels)
    valores_pixels = pd.DataFrame(valores_pixels.transpose(1,0))
    coluna_classe = pd.DataFrame(len(valores_pixels) * [classe], columns = ['classe'])
    amostra_classe = pd.concat([coluna_classe, valores_pixels], axis = 1)
    
    return(amostra_classe)

amostra_treinamento =  [ seleciona_amostras(classe)
                for classe in range(1, 6) ]
# Junta todas as amostras em um dataframe.
amostra_treinamento = pd.concat(amostra_treinamento).dropna()

# Treinamento e classificação
# Treinamento
from sklearn.ensemble import RandomForestClassifier
x = amostra_treinamento.iloc[:, 1:6]
y = amostra_treinamento['classe']
modelo_rf = RandomForestClassifier(n_estimators=50, random_state=None)
modelo_rf.fit(x, y)

# Matriz de confusão e acurácia
classificacao_amostra = modelo_rf.predict(x)

# Evaluate the model (for classification)
from sklearn.metrics import confusion_matrix, accuracy_score

# Matriz de confusão.
matriz_confusao = confusion_matrix(y, classificacao_amostra)
print(matriz_confusao)

# Acurácia no conjunto de treinamento.
acuracia = accuracy_score(y, classificacao_amostra)
print(f"Acurácia: {acuracia}")

# Classificação da imagem
ind_validos = ~dados_raster[:, :, 0].mask.flatten()

valores_pixels = [dados_raster.data[:, :, id_banda].flatten()[ind_validos] 
                  for id_banda in range(5)]

valores_pixels = np.vstack(valores_pixels)

valores_pixels = pd.DataFrame(valores_pixels.transpose(1,0))

resultado_rf = modelo_rf.predict(valores_pixels)

id_cluster, total = np.unique(resultado_rf, return_counts=True)
print(np.array([id_cluster, total]).transpose(1,0))
pyplot.bar(id_cluster, total)

imagem_classificada = np.array([0] * (dados_raster.shape[0] * dados_raster.shape[1]))

for classe in range(1, 6):
    ind_classe = np.where(ind_validos)[0][resultado_rf == classe]
    imagem_classificada[ind_classe.tolist()] = classe

imagem_classificada = imagem_classificada.reshape(dados_raster[:,:,0].shape[0],
                                                  dados_raster[:,:,0].shape[1], 1)
imagem_classificada = np.ma.masked_array(imagem_classificada, dados_raster[:,:,0].mask)

# Visualização da classificação.
import matplotlib.colors
# Começa em 1.
vetor_cores = ["#346B45", "#ABD6B8", "#2347DE", '#BDBDBF', '#E3B16F']
mapa_cores_classe = matplotlib.colors.ListedColormap(vetor_cores)

mapa_classificado = pyplot.imshow(imagem_classificada, cmap=mapa_cores_classe,
                              interpolation='nearest', interpolation_stage='rgba',
                              extent=extensao)
pyplot.colorbar(mapa_classificado)
pyplot.show()

# Calculando a área de cada tipo de uso do solo.
area_pixel = src_raster.res[0] * src_raster.res[1]
area_classe = [len(resultado_rf[resultado_rf==classe]) * area_pixel 
               for classe in range(1, 6)]

# Area total.
area_total = len(resultado_rf) * area_pixel
area_total
area_classe_prop = [ 100*(area_classe[classe]/area_total) 
               for classe in range(0, 5)]
area_classe
area_classe_prop

# Teste e validação para classificadores.
# Divisão das amostras em subconjuntos
import random

def separa_amostra(classe):
    ind_classe = (amostra_treinamento['classe'] == classe)
    amostra_classe = amostra_treinamento.loc[ind_classe, :]
    tamanho_amostra = len(amostra_classe)
    conjunto = random.choices(['treino', 'validacao', 'teste'], k=tamanho_amostra,
                  weights=[0.7, 0.15, 0.15])
    conjunto = pd.DataFrame(conjunto, columns=['conjunto'])
    amostra_classe = pd.concat([amostra_classe, conjunto], axis=1)
    
    return(amostra_classe)

amostra_conjuntos = [ separa_amostra(classe) for classe in range(1,6) ]
amostra_conjuntos = amostra_conjuntos
amostra_conjuntos = pd.concat(amostra_conjuntos, axis=0).dropna()
# Confira o tamanho dos conjuntos.
# Conjunto pra treinamento.
amostra_conjunto_treinamento  = amostra_conjuntos.loc[amostra_conjuntos['conjunto']=='treino', :]

# Conjunto de validação
amostra_conjunto_validacao  = amostra_conjuntos.loc[amostra_conjuntos['conjunto']=='validacao', :]

# Conjunto para o teste final.
amostra_conjunto_teste  = amostra_conjuntos.loc[amostra_conjuntos['conjunto']=='teste', :]

# Treinamento e avaliação dos modelos
# Processo de seleção de modelo.

# Treinamento RF
x = amostra_conjunto_treinamento.iloc[:, 1:6]
y = amostra_conjunto_treinamento['classe']

modelo_rf = RandomForestClassifier(n_estimators=50, random_state=None)
modelo_rf.fit(x, y)

# Classificação no conjunto de treinamento.
classificacao_amostra_treinamento = modelo_rf.predict(x)

# Matriz de confusão.
matriz_confusao_rf = confusion_matrix(y, classificacao_amostra_treinamento)
print(matriz_confusao_rf)

# Acurácia no conjunto de treinamento.
acuracia = accuracy_score(y, classificacao_amostra_treinamento)
print(f"Acurácia: {acuracia}")

# Validação
x = amostra_conjunto_validacao.iloc[:, 1:6]
y = amostra_conjunto_validacao['classe']

# Classificação no conjunto de treinamento.
classificacao_amostra_validacao = modelo_rf.predict(x)

# Matriz de erros do conjunto de validação..
matriz_validacao_rf = confusion_matrix(y, classificacao_amostra_validacao)
print(matriz_validacao_rf)

# Acurácia no conjunto de validação para o random forest.
acuracia_rf = accuracy_score(y, classificacao_amostra_validacao)
print(f"Acurácia: {acuracia_rf}")

# Outro algoritmo.
# Treinamento
from sklearn import svm

x = amostra_conjunto_treinamento.iloc[:, 1:6]
y = amostra_conjunto_treinamento['classe']

modelo_svm = svm.SVC(kernel='rbf', C=1.0, gamma='scale')
modelo_svm.fit(x, y)

classificacao_amostra_treinamento = modelo_svm.predict(x)

# Matriz de confusão.
matriz_confusao_svm = confusion_matrix(y, classificacao_amostra_treinamento)
print(matriz_confusao_svm)

# Acurácia no conjunto de treinamento.
acuracia_svm = accuracy_score(y, classificacao_amostra_treinamento)
print(f"Acurácia: {acuracia_svm}")

# Validação
x = amostra_conjunto_validacao.iloc[:, 1:6]
y = amostra_conjunto_validacao['classe']

# Classificação no conjunto de validação.
classificacao_amostra_validacao = modelo_svm.predict(x)

# Matriz de erros do conjunto de validação..
matriz_validacao_svm = confusion_matrix(y, classificacao_amostra_validacao)
print(matriz_validacao_svm)

# Acurácia no conjunto de validação.
acuracia_svm = accuracy_score(y, classificacao_amostra_validacao)
print(f"Acurácia: {acuracia_svm}")

# Compara os dois modelos e seleciona o de melhor acurácia para apresentar.
if (acuracia_rf > acuracia_svm):
  modelo_escolhido = modelo_rf
  print('Random Forest')
else:
  modelo_escolhido = modelo_svm
  print('SVM')
  
#  Teste final e classificação da imagem.
# Classificação da imagem
valores_pixels = [dados_raster.data[:, :, id_banda].flatten()[ind_validos] 
                  for id_banda in range(5)]

valores_pixels = np.vstack(valores_pixels)

valores_pixels = pd.DataFrame(valores_pixels.transpose(1,0))

resultado_final = modelo_escolhido.predict(valores_pixels)

imagem_classificada = np.array([0] * (dados_raster.shape[0] * dados_raster.shape[1]))

for classe in range(1, 6):
    ind_classe = np.asarray(ind_validos).nonzero()[0][resultado_final == classe]
    imagem_classificada[ind_classe.tolist()] = classe

imagem_classificada = imagem_classificada.reshape(dados_raster[:,:,0].shape[0],
                                                  dados_raster[:,:,0].shape[1], 1)
imagem_classificada = np.ma.masked_array(imagem_classificada, dados_raster[:,:,0].mask)

# Classificação no conjunto de testes.
x = amostra_conjunto_teste.iloc[:, 1:6]
y = amostra_conjunto_teste['classe']

# Classificação no conjunto de testes.
classificacao_amostra_teste = modelo_escolhido.predict(x)

# Matriz de erros do conjunto de validação..
matriz_validacao_final = confusion_matrix(y, classificacao_amostra_teste)
print(matriz_validacao_final)

# Acurácia no conjunto de validação.
acuracia_final = accuracy_score(y, classificacao_amostra_teste)
print(f"Acurácia: {acuracia_final}")

# Visualização da classificação

mapa_classificado = pyplot.imshow(imagem_classificada, cmap=mapa_cores_classe,
                              interpolation='nearest', interpolation_stage='rgba',
                              extent=extensao)
pyplot.colorbar(mapa_classificado)
pyplot.show()

# Exercício: Verifique se suas amostras estão desbalanceadas. Caso estejam, ajuste.

