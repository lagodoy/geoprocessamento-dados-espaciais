#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 14 13:32:48 2026

@author: leonardo
"""

# Preparação dos dados
# Para os shapefiles, siga as dicas dos roteiros anteriores.

# Leitura dos dados
# Subprefeitura
import geopandas as gp
from matplotlib import pyplot
import contextily as cx
caminho_base = '/home/leonardo/Documents/usp/PTR3312/labs_r/lab_03/'
dados_subprefeituras = gp.read_file(caminho_base + 'dados/SIRGAS_SHP_subprefeitura/SIRGAS_SHP_subprefeitura.shp')
print(dados_subprefeituras.crs)
dados_subprefeituras = dados_subprefeituras.set_crs(epsg=31983)
print(dados_subprefeituras.crs)

selecao_subprefeitura = dados_subprefeituras['sp_nome']=='FREGUESIA-BRASILANDIA'
limites_subprefeitura = dados_subprefeituras[selecao_subprefeitura]


# MDT - SRTM:
# Retângulo para a busca a partir de um bounding box de um buffer da subprefeitura.
limites_subprefeitura.buffer(300).to_crs(4326).envelope

# Fonte: https://portal.opentopography.org/raster?opentopoID=OTSRTM.042013.4326.1

# Aqui, são quatro arquivos que precisam ser juntados em um único layer. Dois para o distrito de Brasilândia e
# dois para o distrito da Freguesia do Ó.
# Checando arquivos antes de consolidar.
curvas_nivel_linha = gp.read_file(caminho_base + 'dados/SIRGAS_SHP_curvaintermediaria_11_BRASILANDIA/' +\
                                                    'SIRGAS_SHP_curvaintermediaria_linha_11_BRASILANDIA/' +\
                                                    'SIRGAS_SHP_curvaintermediaria_linha_11_BRASILANDIA.shp')
curvas_nivel_seg = gp.read_file(caminho_base + 'dados/SIRGAS_SHP_curvaintermediaria_11_BRASILANDIA/' +\
                                                    'SIRGAS_SHP_curvaintermediaria_segm_11_BRASILANDIA/' +\
                                                    'SIRGAS_SHP_curvaintermediaria_segm_11_BRASILANDIA.shp')

# Aqui devemos verificar as colunas e identificar aquelas que serão mantidas posteriormente.
print(curvas_nivel_linha.columns.tolist())
print(curvas_nivel_seg.columns.tolist())

print(curvas_nivel_linha.crs)

del curvas_nivel_linha, curvas_nivel_seg

# Implementando a leitura em lote dos arquivos.
diretorio_dados = caminho_base + 'dados/'
prefixo_arquivos_curvas = 'SIRGAS_SHP_curvaintermediaria_*/'
import glob
diretorios_curvas = glob.glob(diretorio_dados + prefixo_arquivos_curvas, recursive=True)
import pandas as pd
lista_shapefile_curvas_nivel = []
for diretorio in diretorios_curvas:
   lista_caminhos_shapefiles_curvas = glob.glob(diretorio + '**/*.shp', recursive=True)
   for nome_shapefile_curvas in lista_caminhos_shapefiles_curvas:
       shapefile_curvas_nivel = gp.read_file(nome_shapefile_curvas)
       shapefile_curvas_nivel = shapefile_curvas_nivel[['ISOVALOR', 'geometry']]
       lista_shapefile_curvas_nivel.append(shapefile_curvas_nivel)

# Junta os dados na lista em um único dataframe
curvas_nivel = pd.concat(lista_shapefile_curvas_nivel)

curvas_nivel = curvas_nivel.set_crs(epsg=31983)

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Curvas de nivel')
# Uso o sample() para pegar apenas uma amostra de 10% das curvas.
curvas_nivel.sample(frac=0.1).plot(ax=ax, column='ISOVALOR', cmap='viridis', alpha=1 , legend=True)
cx.add_basemap(ax=ax, crs=limites_subprefeitura.crs,alpha=1, zorder=0, zoom=15,
               source=cx.providers.OpenStreetMap.Mapnik)

len(curvas_nivel['ISOVALOR'])
len(pd.unique(curvas_nivel['ISOVALOR']))

# Arquivo coom os dados de elevação (MDT) cobrindo a região.
import rasterio
caminho_arquivo_mdt = caminho_base + 'dados/rasters_SRTMGL1/output_SRTMGL1.tif'

# Abre o arquivo de entrada e checa conteúdo, exibindo o valor de um pixel e o crs.
with rasterio.open(caminho_arquivo_mdt) as mdt:
    print(mdt)
    print(mdt.read(1, window=((21, 22), (21, 22)))[0,0])
    print(mdt.crs)
  
   
# Abre o arquivo de entrada e executa o clip. Note que a transformaçãp do crs 
# também é feita.
#from rasterio.mask import mask
import rioxarray as rxr

mdt = rxr.open_rasterio(caminho_arquivo_mdt, masked=True).squeeze()
mdt_sirgas = mdt.rio.reproject(curvas_nivel.crs)#CRS.from_string('EPSG:4326'))
# Caso queira inserir um valor para nodata.
#nodata_valor = -9999.0
#mdt_sirgas = mdt_sirgas.rio.set_nodata(nodata_valor)
# Seleciona os dados de MDT apenas na região de interesse. Note o buffer na área para 
# que a seleção ultrapasse os limites, necessário para os cálculos posteriores de slope.
limites = limites_subprefeitura.buffer(300)
# Mascara tudo de uma vez.
mdt_subprefeitura = mdt_sirgas.rio.clip(limites)

mdt_subprefeitura.plot()


# Favelas na região
dados_favelas = gp.read_file(caminho_base + 'dados/SIRGAS_SHP_favela/SIRGAS_SHP_favela.shp')
print(dados_favelas.crs)
dados_favelas = dados_favelas.set_crs(31983)

favelas_subprefeitura = gp.clip(dados_favelas, limites_subprefeitura)

# Visualizando as curvas de nível a partir do MDT
# No python, também é possível gerar uma visualização rápida de curvas de nível 
# a partir de um arquivo de MDT.
import numpy as np
x = mdt_subprefeitura.rio.bounds()[0]
y = mdt_subprefeitura.rio.bounds()[1]
x_res, y_res = mdt_subprefeitura.rio.resolution()

height = mdt_subprefeitura.shape[0]
width = mdt_subprefeitura.shape[1]
cols, rows = np.meshgrid(np.arange(x + x_res/2, width * x_res + x, 1 * x_res), 
                         np.arange(y + (height) * abs(y_res) - abs(y_res)/2, y, y_res))

f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Curvas de nivel')
ax.contour(cols, rows, mdt_subprefeitura.data.tolist() , levels=100, legend=True)
cx.add_basemap(ax=ax, crs=limites_subprefeitura.crs,alpha=1, zorder=0, zoom=15,
               source=cx.providers.OpenStreetMap.Mapnik)

pyplot.contour(cols, rows, mdt_subprefeitura.data.tolist() , levels=100, legend=True)


from skimage import measure
from shapely import LineString
elevacoes = np.unique(mdt_subprefeitura)
elevacoes = elevacoes[~np.isnan(elevacoes)]
lista_coordenadas_curvas = []
for elevacao in elevacoes:
    lista_coordenadas_curvas_elevacao_corrigida = []
    lista_coordenadas_curvas_elevacao = measure.find_contours(np.array(mdt_subprefeitura.data.tolist()), elevacao)
    for coordenadas_curva_elevacao in lista_coordenadas_curvas_elevacao:
        #Broadcasting is generally the most straightforward and efficient method in NumPy. NumPy automatically expands the smaller array to match the shape of the larger array during element-wise operations. 
        coordenadas_curva_elevacao = np.array(coordenadas_curva_elevacao)*np.array([y_res, x_res]) + [y, x]
        coordenadas_curva_elevacao = coordenadas_curva_elevacao = coordenadas_curva_elevacao[:, ::-1]
        #print(coordenadas_curva_elevacao)
        lista_coordenadas_curvas_elevacao_corrigida.append(LineString(coordenadas_curva_elevacao))
    #df_curvas = pd.concat(lista_coordenadas_curvas_elevacao_corrigida, axis=0)    
    #lista_coordenadas_curvas.append(gp.GeoSeries(lista_coordenadas_curvas_elevacao_corrigida, name='geometry', crs="EPSG:31983"))
    df_curva_elevacao = gp.GeoDataFrame(geometry=gp.GeoSeries(lista_coordenadas_curvas_elevacao_corrigida, crs="EPSG:31983"))
    df_curva_elevacao['elevacao'] = elevacao
    lista_coordenadas_curvas.append(df_curva_elevacao)
    
df_curvas = pd.concat(lista_coordenadas_curvas, axis=0)
df_curvas.sample(frac=0.1).plot(column='elevacao', cmap='viridis', alpha=1 , legend=True)

# Gerar Modelo Digital do Terreno a partir de curvas de nível
# Primeiro vamos observar como seriam curvas de nível a partir dos dads de MDT
# fornecidos.

# TIN interpolation
from scipy.spatial import Delaunay
import numpy as np
import time
lista_coordenadas_vertices = []
for index, linha in curvas_nivel.iterrows():
    vertices = gp.GeoSeries(linha['geometry']).get_coordinates()
    isovalor = linha['ISOVALOR']
    vertices['z'] = isovalor
    lista_coordenadas_vertices.append(vertices)

vertices_curvas = pd.concat(lista_coordenadas_vertices, axis=0)
#vertices_curvas_amostra = vertices_curvas.sample(frac=0.2).to_numpy()
vertices_curvas_array = vertices_curvas.to_numpy()
start = time.time()
resultado_triangulacao = Delaunay(vertices_curvas_array[:,:2])
end = time.time()
print(end - start)

resultado_triangulacao.simplices
resultado_triangulacao.points
resultado_triangulacao.points[resultado_triangulacao.simplices]
# Junta xyz em uma matriz e cria um 
tin_network_matriz = vertices_curvas_array[resultado_triangulacao.simplices]
tin_network_matriz
from shapely.geometry import LineString
start = time.time()
lista_triangulos = []
i = 0
for triangulo in tin_network_matriz:
    #print(triangulo)
    geometria_triangulo = LineString(triangulo)# gp.GeoDataFrame(geometry=gp.GeoSeries(LineString(triangulo), crs="EPSG:31983"))
    lista_triangulos.append(geometria_triangulo)
    if (i % 100000 == 0):
        print(i)
    i = i + 1
end = time.time()
print(end - start)

df_triangulos = pd.DataFrame({'geometry': lista_triangulos})

tin_network = gp.GeoDataFrame(df_triangulos, geometry='geometry')
tin_network.set_crs(epsg=31983, inplace=True)

print(tin_network)
type(tin_network)
tin_network.to_file('~/Downloads/teste_tin_python.gpkg', driver='GPKG', layer='tin')

#  MDT a partir do TIN
min_x, min_y, max_x, max_y = limites_subprefeitura.total_bounds
resolucao = 10
coordenadas_x = [i for i in np.arange(min_x + resolucao/2, max_x, resolucao)]
coordenadas_y = [i for i in np.arange(min_y+ resolucao/2, max_y, resolucao)]

coordenadas_grid = np.meshgrid(coordenadas_x, coordenadas_y)

grid_area_points = gp.points_from_xy(x=coordenadas_grid[0].flatten(), y=coordenadas_grid[1].flatten())
grid_area = gp.GeoDataFrame(geometry=grid_area_points)
grid_area.set_crs(epsg=31983, inplace=True)

tin_network_xy = tin_network.copy(deep=True)
tin_network_xy['geometry'] = tin_network_xy.force_2d()
# Torna os triâgunlos que estão em linhas em poligonos.
from shapely.geometry import Polygon
tin_network_xy['geometry'] = tin_network_xy['geometry'].apply(lambda triangulo: Polygon(triangulo))

triangulo = gp.sjoin(tin_network_xy, grid_area, how='right', predicate='contains', lsuffix='id_triangulo', rsuffix='ponto')

df_triangulo = pd.DataFrame({'id_triangulo': triangulo['index_id_triangulo']})#.index})

geometry = grid_area.geometry[triangulo.index].reset_index()
pontos_grid = gp.GeoDataFrame(df_triangulo, crs="EPSG:31983",
                           geometry=geometry.geometry)
coords_xy = pontos_grid.geometry.get_coordinates()
coord = pd.DataFrame({'x': coords_xy['x'], 
                      'y': coords_xy['y'],
                     'id_triangulo': pontos_grid['id_triangulo']})
# Vamos utilizar a função get_coordinates do pacote shapely.
from shapely import get_coordinates
def calcula_z(i):
    # Mostra a quantidade de células calculadas, caso seja múltiplo de 100.
    if i % 1000 == 0:
        print(i)
    #i é o id do ponto (ou linha na tabela).
    
    id_triangulo = coord.at[i,'id_triangulo']
    # Esses pontos são as coordenadas dos triangulos.
    if pd.isna(id_triangulo):
        return(float("nan"))
    # Extrai as coordenadas do triângulo, incluindo o valor em z.
    pontos = get_coordinates(tin_network.geometry[id_triangulo], include_z=True)
    # Calcula o valor interpolado.
    a = (pontos[1,:]-pontos[0,:])
    b = (pontos[2,:]-pontos[0,:])
    c = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    # Coordenadas do ponto que queremos calcular o z.
    x = coord.at[i, 'x']
    y = coord.at[i, 'y']
    z = (-c[0]*(x-pontos[0,0]) - c[1]*(y-pontos[0,1]))/c[2]+pontos[0,2]
    return(z)

start = time.time()
resultado = pontos_grid.index.to_series().apply(lambda ponto: calcula_z(ponto))
end = time.time()
print(end - start)
# Adiciona uma coluna com os resultados da interpolação no TIN.
coord['z'] = resultado
# Remove coluna que não será usada.
coord = coord.drop(columns=['id_triangulo']) 
# Visualiza uma amostra dos valores em z.
coord.sample(frac=0.1).plot.scatter(x='x',y='y', c='z')
# Ordena as coordendas no array.
coord = coord.sort_values(by=['y', 'x'], ascending=[False, True])
# Coordenadas z no formato matricial apropriado.
n_linhas = coordenadas_grid[0].shape[0]
n_colunas = coordenadas_grid[0].shape[1]
dados_raster = coord['z'].values.reshape(n_linhas, n_colunas)

# Considero a extremidade do pixel como referência para a transformoção a partir da origem, por isso 
# tiramos 5 metros.
transformacao = rasterio.Affine(10,0, min(coordenadas_x) - 5, 0, -10, max(coordenadas_y) - 5) 
src = rasterio.features.shapes(dados_raster, transform=transformacao)
shapes = [(g,v) for g, v in src]

mascara_subprefeitura = [limites['geometry'] for limites in limites_subprefeitura.iterfeatures()]

raster_mascara = rasterio.features.rasterize(
                    mascara_subprefeitura,
                    out_shape=(n_linhas, n_colunas), # Shape é o mesmo pq é o mesmo bbox.
                    transform=transformacao,
                    fill=0,              # Value for pixels *outside* the polygons
                    default_value=1,
                    dtype=np.uint8,
                    all_touched=False) # Transformação é a mesma pq é o mesmo bbox.

raster_saida_subprefeitura = np.ma.masked_where(raster_mascara == 0, dados_raster)

# Salva o raster criado.
caminho_raster_saida = '/home/leonardo/Downloads/raster_tin_10m_python.tif'
with rasterio.open(
    caminho_raster_saida,
    'w',
    driver='GTiff',
    height=raster_saida_subprefeitura.shape[0],
    width=raster_saida_subprefeitura.shape[1],
    count=1, # Number of bands
    dtype=raster_saida_subprefeitura.dtype,
    crs='EPSG:31983', # Example CRS
    transform=transformacao,
) as dst:
    dst.nodata = np.nan
    dst.write(raster_saida_subprefeitura, 1)


# Gerar Modelo de Declividade a partir de MDT
from osgeo import gdal
caminho_slope_saida = '/home/leonardo/Downloads/slope_python.tif'
caminho_arquivo_mdt_sirgas = '/home/leonardo/Downloads/mdt_sirgas_subprefeitura.tif'
x_origem = mdt_subprefeitura.rio.bounds()[0]
y_origem = mdt_subprefeitura.rio.bounds()[3]

transformacao = rasterio.transform.Affine.translation(x_origem - x_res/2, y_origem - y_res/2) * rasterio.transform.Affine.scale(x_res, y_res)
with rasterio.open(
    caminho_arquivo_mdt_sirgas,
    'w',
    driver='GTiff',
    height=mdt_subprefeitura.shape[0],
    width=mdt_subprefeitura.shape[1],
    count=1, # Number of bands
    dtype=mdt_subprefeitura.dtype,
    crs='EPSG:31983', # Example CRS
    transform=transformacao,
) as dst:
    dst.nodata = np.nan
    dst.write(mdt_subprefeitura, 1)

gdal.DEMProcessing(caminho_slope_saida, caminho_arquivo_mdt_sirgas,  processing='slope')

src_declividade = rasterio.open(caminho_slope_saida, nodata = np.float32(-9999))

declividade = src_declividade.read(1)
declividade = np.ma.masked_where(declividade == -9999, declividade)


print(type(declividade))
print(declividade.dtype)
print(declividade.shape)

extensao_mapa = rasterio.plot.plotting_extent(src_declividade)
f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Declividade')
# Adicionando mapa base do OSM.
# A linha a seguir é uma gambiarra para o plot não se perder.
limites_subprefeitura.plot(ax=ax, facecolor='none', edgecolor='none', alpha=1)
cx.add_basemap(ax=ax, crs=src_declividade.crs, alpha=1, zorder=0)
pyplot.imshow(declividade, extent=extensao_mapa, alpha=0.7, zorder=1)
pyplot.show()


# Estatística zonal (análise zonal da declividade)

def calcula_estatistica_area (area):
    # area Chega aqui como Series. Sim, o python faz isso.
    # shapes precisa ser iterável, por isso os colchetes para formar uma lista.
    pixels_area = rasterio.mask.mask(src_declividade, shapes=[area.geometry])
    # Remove nodata antes da estatistica ser calculada.
    pixels_area_validos = np.ma.masked_values(pixels_area[0], -9999.0)
    # Transforma em dataframe, para calcular um sumário com um único comando.
    # Essa é uma limitação do python. flatten deixa a matrix em formato 1-d.
    pixels_area_validos = pd.DataFrame(pixels_area_validos.flatten())
    estatisticas = pixels_area_validos.describe()
    #print(pd.concat([area.to_frame().transpose(), estatisticas.transpose()], axis=1, ignore_index=True))
    df = pd.concat([area.to_frame().transpose().reset_index(drop=True), 
                    estatisticas.transpose().reset_index(drop=True)], 
                   axis=1, ignore_index=True)
    colunas = area.to_frame().transpose().columns.to_list() + estatisticas.transpose().columns.to_list()
    #print(colunas)
    df.columns = colunas
    print(df)
    return(df)
                      
estatisticas_zonais = favelas_subprefeitura.apply(lambda area: calcula_estatistica_area(area), axis=1)

type(estatisticas_zonais)
gp_estatisticas_zonais = pd.concat(estatisticas_zonais.to_list())

gp_estatisticas_zonais[gp_estatisticas_zonais['fv_nome'] == 'Alegria'].transpose()


gp_estatisticas_zonais = gp.GeoDataFrame(estatisticas_zonais, geometry=estatisticas_zonais.geometry)
gp_estatisticas_zonais.plot(color='mean')
gp_estatisticas_zonais.crs = 'EPSG:31983'
f, ax = pyplot.subplots(1,1, figsize=(12, 12), alpha=0)
ax.set_aspect('equal')
ax.set_title('Média')
gp_estatisticas_zonais.plot(ax=ax, column='mean', cmap='viridis', alpha=1 , legend=True)
cx.add_basemap(ax=ax, crs=gp_estatisticas_zonais.crs,alpha=1, zorder=0, zoom=15,
               source=cx.providers.OpenStreetMap.Mapnik)

