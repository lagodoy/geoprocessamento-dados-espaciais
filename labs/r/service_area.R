# Isócronas/áreas de serviço
# 3.1 Software e dados necessários para a prática de laboratório
limites_subprefeituras <- sf::st_read('../dados/geoportal_subprefeitura_v2.gpkg')
sf::st_crs(limites_subprefeituras)$input
subprefeitura_selecionada <- limites_subprefeituras[limites_subprefeituras$nm_subprefeitura=='BUTANTA',]

estacoes_metro <- sf::st_read('../dados/geoportal_estacao_metro_v2.geojson')
sf::st_crs(estacoes_metro)$input

id_estacoes_subprefeitura <- sf::st_within(estacoes_metro, subprefeitura_selecionada)
id_estacoes_subprefeitura
estacoes_metro <- estacoes_metro[lengths(id_estacoes_subprefeitura) > 0, ]
head(estacoes_metro)

logradouros <- sf::st_read('../dados/LOG2020_CEM_RMSP/LOG2020_CEM_RMSP.shp')
sf::st_crs(logradouros)$input
logradouros <- sf::st_transform(logradouros, 31983)
sf::st_crs(logradouros)$input

logradouros_subprefeitura <- sf::st_intersection(logradouros, subprefeitura_selecionada)
head(logradouros_subprefeitura)

rm(logradouros)
gc()

mapview::mapview(logradouros_subprefeitura$geometry, map.types='OpenStreetMap.Mapnik') + 
  mapview::mapview(estacoes_metro, 
                   col.regions='yellow',
                   zcol='nm_linha_metro_trem', 
                   popup='nm_estacao_metro_trem')

# 3.2 Áreas de serviço
# Apenas sf
library(magrittr)

calcula_area_servico <- function(ponto_inicio) {
  ponto_inicio <- sf::st_sfc(ponto_inicio, crs=31983)
  service_area_buffer <- sf::st_buffer(ponto_inicio, 500)
  logradouros_entorno_estacao <- sf::st_intersection(logradouros_subprefeitura, service_area_buffer)
  # Resoluição dos "lixels" (equivalente em linha dos pixels)
  logradouros_entorno_estacao_segmentos <- sf::st_segmentize(logradouros_entorno_estacao, 0.5)
  
  
  linhas_log <- lapply(logradouros_entorno_estacao_segmentos$geometry, function (linha_interesse) {
            coords <- sf::st_cast(sf::st_sfc(linha_interesse), 'POINT')
            coords <- sf::st_coordinates(coords)
            linhas <- coords %>% as.data.frame() %>% 
              dplyr::mutate(linha=paste0('LINESTRING(',X, ' ', Y, ',', dplyr::lead(X), ' ', dplyr::lead(Y), ')'), .keep='none') %>% 
              head(-1) %>% 
              dplyr::mutate(geometry=sf::st_as_sfc(linha), keep='.none') %>% sf::st_as_sf()
            return(linhas[,'geometry'])
  })
  linhas_log <- data.table::rbindlist(linhas_log)
  class(linhas_log)
  linhas_log <- sf::st_as_sf(linhas_log)
  sf::st_crs(linhas_log) <- 31983
  logradouros_entorno_estacao_segmentos <- linhas_log

  rede_entorno <- sfnetworks::as_sfnetwork(logradouros_entorno_estacao_segmentos, directed = FALSE)
  rede_entorno <- rede_entorno %>% sfnetworks::activate("edges") %>% dplyr::mutate(weight=sfnetworks::edge_length())
  
  id_no_mais_proximo_rede <- sf::st_nearest_feature(ponto_inicio, rede_entorno)
  
  rede_entorno = rede_entorno %>%
    sfnetworks::activate("edges") %>%
    dplyr::mutate(speed = units::set_units(5*1000/(3600), "m/s")) %>%
    dplyr::mutate(time = weight / speed) 
  
  rede_entorno
  rede_entorno = sfnetworks::activate(rede_entorno, "nodes")
  dados_area_servico <- rede_entorno %>%
    dplyr::filter(tidygraph::node_distance_from(id_no_mais_proximo_rede, 
                                                weights = weight, 
                                                algorithm = 'automatic') <= 500) 
  
  # area_servico_logradouros <- dados_area_servico %>% 
  #                               sfnetworks::activate('edges') %>% 
  #                               sf::st_geometry()
  
  
  area_servico_convex_hull <- dados_area_servico %>% 
                                sf::st_geometry() %>%
                                sf::st_combine() %>%
                                sf::st_convex_hull()
  
  area_servico_logradouros <- sf::st_intersection (logradouros_entorno_estacao, 
                                                area_servico_convex_hull)
  return(list(sf::st_as_sf(area_servico_convex_hull), sf::st_as_sf(area_servico_logradouros)))
}  

areas_servico <- lapply (estacoes_metro$geometry,FUN = calcula_area_servico)
areas_servico_convex_hull <- lapply(areas_servico, function(area_servico) {sf::st_as_sf(area_servico[[1]])})
areas_servico_convex_hull <- data.table::rbindlist(areas_servico_convex_hull)
areas_servico_rede <- lapply(areas_servico, function(area_servico) {area_servico[[2]]})

areas_servico_rede <- data.table::rbindlist(areas_servico_rede)
areas_servico_rede <- sf::st_as_sf(areas_servico_rede)



areas_servico_convex_hull <- sf::st_as_sf(areas_servico_convex_hull)

mapview::mapview(subprefeitura_selecionada$ge_poligono,
                 lwd=2,  col.regions='transparent',
                 map.types='OpenStreetMap.Mapnik') + 
  mapview::mapview(estacoes_metro, 
                   col.regions='yellow',
                   label = 'nm_estacao_metro_trem',
                   #zcol='nm_estacao_metro_trem', 
                   layer.name='Linha Amarela',
                   popup='nm_estacao_metro_trem') +
  mapview::mapview(areas_servico_rede, label = 'NOME_CAPS', 
                   color='purple', lwd=2, layer.name='Rede Caminhada') +
  mapview::mapview(areas_servico_convex_hull, zcol=NULL, #label=NULL, 
                   alpha=0.5, lwd=2, layer.name='Service Area')


sf::st_write(areas_servico_convex_hull, 
             '~/Downloads/convex_hull.gpkg',
              delete_layer=TRUE)
sf::st_write(areas_servico_rede, 
             '~/Downloads/logradouros_area_servico.gpkg', 
             delete_layer=TRUE)


# 3.3 WMS
#install.packages('tidyverse', 'sf', 'httr', 'ows4R')
# WFS/WMS -> sf no R
# Referência: https://tutorials.inbo.be/tutorials/spatial_wfs_services/
library(magrittr)
url_base_wms <- 'https://wms.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wms?'
url_wms <- httr::parse_url(url_base_wms)

url_client_wms <- ows4R::WFSClient$new(url_base_wms, serviceVersion = "1.3.0")
# See layer names
layers_disponiveis <- lapply(url_client_wms$getFeatureTypes(), function (x) {return(x$getName())})
  
layers_disponiveis <- unlist(layers_disponiveis) %>% as.data.frame()
layers_disponiveis
limites_bbox <- sf::st_bbox(sf::st_transform( subprefeitura_selecionada, 4326))
# https://docs.geoserver.org/main/en/user/services/wms/reference.html#getmap
url_wms$query <- list(service = 'wms',
                  version = '1.3.0', 
                  request = 'GetMap',
                  layers = 'geoportal:densidade_demografica',
                  styles = '',
                  srsName = 'EPSG:4326',
                  bbox = paste0(limites_bbox, collapse = ','),
                  width='4000',
                  height='4000',
                  format='image/png')
layer_url <- httr::build_url(url_wms)
layer_url

layer_png_pagina <- httr::GET(layer_url, httr::write_memory())
layer_png_arquivo <- png::readPNG(layer_png_pagina$content)
limites_plot <- sf::st_bbox(subprefeitura_selecionada)
# Use o dev.off() em caso de erro de margens.
dev.off()
#par("mar")
#par(mar=rep(2, 4))
plot(c(limites_plot[1], limites_plot[3]), c(limites_plot[2], limites_plot[4]), type='n')
rasterImage(layer_png_arquivo, limites_plot[1], limites_plot[2], limites_plot[3], limites_plot[4] )
terra::lines(terra::vect(areas_servico_rede),  col="purple", lwd=2)
terra::polys(terra::vect(areas_servico_convex_hull),  col="blue", lwd=2, alpha=0.5)
terra::points(terra::vect(estacoes_metro),  col="yellow", cex=1.5)
dev.print(pdf, '~/Downloads/mapa.pdf')
dev.print(jpeg, '~/Downloads/mapa.jpg', width=1500)
dev.print(png, '~/Downloads/mapa.png', width=4000)

#dev.off()
rm(url_client_wms)
gc()

#  WFS
url_base_wfs <- 'https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs?'
url_client_wfs <- ows4R::WFSClient$new(url_base_wfs, serviceVersion = "2.0.0")

# Vamos preparar uma url codificada para usar posteriormente.
url_wfs <- httr::parse_url(url_base_wfs)


# See layer names
layers_disponiveis <- lapply(url_client_wfs$getFeatureTypes(), function (x) {return(x$getName())})

layers_disponiveis <- unlist(layers_disponiveis) %>% as.data.frame()
layers_disponiveis


limites_bbox <- sf::st_bbox( sf::st_buffer(subprefeitura_selecionada, 50))
# https://docs.geoserver.org/main/en/user/services/wfs/reference.html#getmap
url_wfs$query <- list(service = 'wfs',
                      version = '2.0.0', 
                      request = 'GetFeature',
                      typeName = 'geoportal:densidade_demografica',
                      bbox = paste0(limites_bbox, collapse = ','),
                      srsName = 'EPSG:31983'
                      )
layer_url <- httr::build_url(url_wfs)
layer_url

layer_sf <- sf::read_sf(layer_url)
names(layer_sf)
class(layer_sf)
sf::st_crs(layer_sf)$input
sf::st_crs(layer_sf) <- 31983

string_geom <- sf::st_as_text(layer_sf$ge_poligono)
string_geom <- substr(string_geom, start = 15,nchar(string_geom)-1)
geometria <- sf::st_as_sfc(string_geom, crs = 31983)

geometria <- sf::st_cast(geometria, 'MULTILINESTRING')

geometria <- sf::st_cast(geometria, 'MULTIPOLYGON')

dados <- layer_sf %>% sf::st_drop_geometry()
dados$geometry <- geometria
dados <- sf::st_as_sf(dados)
setores_subprefeitura <- sf::st_within(sf::st_centroid(dados), 
                                       sf::st_buffer(subprefeitura_selecionada$ge_poligono, dist = 50))
dados <- dados[lengths(setores_subprefeitura) > 0, ]

mapview::mapview(sf::st_buffer(subprefeitura_selecionada$ge_poligono, dist = 0),
                 lwd=2,  col.regions='transparent',
                 map.types='OpenStreetMap.Mapnik') +
  mapview::mapview(dados, zcol='qt_habitante_hectare') +
  mapview::mapview(estacoes_metro, 
                   col.regions='yellow',
                   label = 'nm_estacao_metro_trem',
                   #zcol='nm_estacao_metro_trem', 
                   layer.name='Linha Amarela',
                   popup='nm_estacao_metro_trem') +
  mapview::mapview(areas_servico_rede, label = 'NOME_CAPS', 
                   color='gray', lwd=2, layer.name='Rede Caminhada') +
  mapview::mapview(areas_servico_convex_hull$x, zcol=NULL, #label=NULL, 
                    col.regions='transparent', lwd=2, layer.name='Service Area')

# 3.4 Metadados do WFS
# Aqui, descreve-se os parãmetros disponiveis para efetuar operações no WFS do servidor.
# GetCapabilities: Generates a metadata document describing a WFS service provided by server as well as valid WFS operations and parameters

# Metadados do sistema e das bases disponibilizadas.
url_wfs$query <- list(service = 'wfs',
                      version = '2.0.0', 
                      request = 'GetCapabilities'
)

metadata_url <- httr::build_url(url_wfs)
metadata_url

metadata_pg <- httr::GET(metadata_url)
metadata_pg$status_code
metadata_xml <- httr::content(metadata_pg)
class(metadata_xml)

# Verifica se há namespaces.
metadata_xml %>% xml2::xml_ns()
# Remove os namespaces
metadata_xml <- metadata_xml %>% xml2::xml_ns_strip()

# Verifica os componentes da resposta, conforme descrito no manual.
xml2::xml_name(metadata_xml)
xml2::xml_name(xml2::xml_children(metadata_xml))
componentes <- xml2::xml_children(metadata_xml)
xml2::xml_name(componentes)
dados_features_disponiveis <- xml2::xml_children(componentes[4])
xml2::xml_name(dados_features_disponiveis[1])
xml2::xml_name(xml2::xml_children(dados_features_disponiveis[1]))

nomes_layers_acesso <- xml2::xml_text(xml2::xml_find_all(componentes, "//FeatureType/Name"))
dados_layer <- xml2::xml_text(xml2::xml_find_all(componentes, "//FeatureType/Title"))
descricao_layer <- xml2::xml_text(xml2::xml_find_all(componentes, "//FeatureType/Abstract"))

descricao_features_disponiveis <- data.frame(dados_layer, nomes_layers_acesso, descricao_layer)

head(descricao_features_disponiveis)

# Metadados de uma feature específica.
url_wfs$query <- list(service = 'wfs',
                      version = '2.0.0', 
                      request = 'DescribeFeatureType',
                      typeName = 'geoportal:densidade_demografica'
)
metadata_feature_url <- httr::build_url(url_wfs)
metadata_feature_pg <- httr::GET(metadata_feature_url, httr::write_memory())
metadata_feature_xsd <- xml2::read_html(metadata_feature_pg$content)

# Checando os tipos de dados na tabela de atributos.
atributos <- xml2::xml_attr(xml2::xml_find_all(metadata_feature_xsd, "//*/sequence//element"), 'name')
tipos_atributos <- xml2::xml_attr(xml2::xml_find_all(metadata_feature_xsd, "//*/sequence//element"), 'type')

tabela_metadados <- data.frame(atributos, tipos_atributos)
head(tabela_metadados)
