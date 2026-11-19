#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 14 13:32:48 2026

@author: leonardo
"""

# Introdução.
# 1 Carredamento e preparação dos dados necessários para a prática de laboratório
import geopandas as gp
caminho_base = '/home/leonardo/Documents/usp/PTR3312/labs_r/lab_04/'
limites_municipios = gp.read_file(caminho_base + 'dados/OD-2017/Mapas-OD2017/Shape-OD2017/Municipios_2017_region.shp')
print(limites_municipios.crs)
limites_municipios = limites_municipios.to_crs('EPSG:31983')

zonas_od = gp.read_file(caminho_base + 'dados/OD-2017/Mapas-OD2017/Shape-OD2017/Zonas_2017_region.shp')
print(zonas_od.crs)
zonas_od = zonas_od.to_crs('EPSG:31983')

limites_municipios.plot()
limites_municipios.head()
limites_municipios['NomeMunici'].sort_values()
limites_municipios_selecionado = limites_municipios.copy(deep=True)
limites_municipios_selecionado = limites_municipios_selecionado[limites_municipios_selecionado['NomeMunici']=="São Paulo"]
limites_municipios_selecionado.plot()

# 2. Recortando Zonas de Pesquisa do Município de São Paulo
# Observe o erro.
zonas_od_selecao = gp.clip(zonas_od, limites_municipios_selecionado)

# 3 GRASS “v.clean”
geometrias_erro = ~zonas_od['geometry'].is_valid
zonas_od['erro'] = geometrias_erro
zonas_od.plot(column='erro', legend=True)
zonas_od['motivo_erro'] = zonas_od['geometry'].is_valid_reason()
zonas_od[geometrias_erro]
zonas_od_corrigidas = zonas_od.copy(deep=True)
zonas_od_corrigidas['geometry'] = zonas_od_corrigidas['geometry'].make_valid()

geometrias_erro = ~zonas_od_corrigidas['geometry'].is_valid
zonas_od_corrigidas[geometrias_erro]
# Verifique e faça a correção nos municipios, caso necessário.
limites_municipios_selecionado['geometry'].is_valid
limites_municipios_selecionado['geometry'] = limites_municipios_selecionado['geometry'].make_valid()
limites_municipios_selecionado['geometry'].is_valid
# Um truque que funciona muitas vezes para polígonos é utilizar um buffer de raio 0.
zonas_od_corrigidas_buff = zonas_od.copy(deep=True)
zonas_od_corrigidas_buff['geometry'] = zonas_od_corrigidas_buff['geometry'].buffer(0)
zonas_od_selecao_buff = gp.clip(zonas_od_corrigidas_buff, limites_municipios_selecionado)
geometrias_erro = ~zonas_od_corrigidas_buff['geometry'].is_valid
zonas_od_corrigidas_buff[geometrias_erro]

# Faça o clip novamente
zonas_od_selecao = gp.clip(zonas_od_corrigidas, limites_municipios_selecionado )
zonas_od_selecao.plot()
# Cheque a tabela de atributos e observe queo intersection carrega algumas zonas indevidas, fora do
# município de São Paulo. Você consegue explicar?
zonas_od_selecao['NomeMunici'].unique()


# Com a tabela de atributos, cheque a quantidade de zonas em SP.
sum(zonas_od_corrigidas['NomeMunici']=='São Paulo')

# Podemos usar outro approach, checando os polígonos que estão totalmente dentro do município. 
zonas_od_selecao = gp.sjoin(zonas_od_corrigidas, limites_municipios_selecionado, how='inner', predicate='within')
zonas_od_selecao.plot()
len(zonas_od_selecao)


# Observe que ainda há falhas no processo. Para ajustar, podemos rerduzir ligeiramente
# os polígonos das zonas od, para que fiquem exatamente dentro dos limites do
# município. A função st_buffer pode ser utilizada para isso.
zonas_od_buff_clip = zonas_od_corrigidas.copy(deep=True)
zonas_od_buff_clip['geometry'] = zonas_od_buff_clip['geometry'].buffer(-50)
zonas_od_selecao = gp.sjoin(zonas_od_buff_clip, limites_municipios_selecionado, how='inner', predicate='within')
zonas_od_selecao.plot()
len(zonas_od_selecao)

# Outra opção é utilizar a função st_intersects, com o buffer negativo nas zonas od.
zonas_od_selecao = gp.clip(zonas_od_buff_clip, limites_municipios_selecionado)
zonas_od_selecao.plot()
len(zonas_od_selecao)


# 4 Inserção de dado externo e fazendo cálculo
import pandas as pd
nomes_colunas = ['zona', 'nome', 'domicilios', 'familias', 'populacao', 
                   'matriculas_ecolares', 'empregos',	'automoveis_particulares',
                   'viagens_produzidas', 'viagens_atraidas', 'area_ha']
dados_gerais_od = pd.read_excel(caminho_base + 'dados/OD-2017/Tabelas-OD2017/Tab01_OD2017.xlsx',
                               names = nomes_colunas, 
                               skiprows = 8,
                               nrows = len(zonas_od_corrigidas))


# Empregos por pessoa. Movimento pendular.
dados_gerais_od['emp_pessoa'] = dados_gerais_od['empregos']/dados_gerais_od['populacao']
# Zera os valores onde não há população.
dados_gerais_od.loc[dados_gerais_od['populacao'] == 0,'emp_pessoa'] = 0


# 5 Join
zonas_od_selecao.columns
dados_gerais_od.columns
zonas_od_selecao= zonas_od_selecao.merge(dados_gerais_od, left_on='NumeroZona', right_on='zona', how='inner')
zonas_od_selecao.columns

# 6 Mapas coropléticos
# Com o mapview
zonas_od_selecao['emp_pessoa'].describe()

from matplotlib.colors import ListedColormap
cores = ListedColormap(['red', 'blue'])

zonas_od_selecao['classe_emp_pessoa'] = pd.cut(zonas_od_selecao['emp_pessoa'], [0,1, 40], right=False)
zonas_od_selecao.plot(column='classe_emp_pessoa', legend=True, categorical=True, cmap=cores)


