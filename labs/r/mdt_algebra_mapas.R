# 1. Introdução

# 2. Preparação dos dados
# Para os shapefiles, siga as dicas dos roteiros anteriores.

# 2.1 Leitura dos dados
# Subprefeitura 
dados_subprefeituras <- sf::read_sf('../dados/SIRGAS_SHP_subprefeitura/SIRGAS_SHP_subprefeitura.shp')
sf::st_crs(dados_subprefeituras)$input
sf::st_crs(dados_subprefeituras) <- 31983


selecao_subprefeitura <- dados_subprefeituras$sp_nome=='FREGUESIA-BRASILANDIA'
limites_subprefeitura <- dados_subprefeituras[selecao_subprefeitura, ]$geometry


# MDT - SRTM:
# Retângulo para a busca a partir de um bounding box de um buffer da subprefeitura.
sf::st_bbox(sf::st_transform(sf::st_buffer(limites_subprefeitura, 300), 4326))
# Fonte: https://portal.opentopography.org/raster?opentopoID=OTSRTM.042013.4326.1

# Aqui, são quatro arquivos que precisam ser juntados em um único layer. Dois para o distrito de Brasilândia e
# dois para o distrito da Freguesia do Ó.
# Colocar exemplo com arquivos individuais antes da leitura em lote.
curvas_nivel_linha <- sf::read_sf(file.path('../dados',
                                'SIRGAS_SHP_curvaintermediaria_11_BRASILANDIA',
                                'SIRGAS_SHP_curvaintermediaria_linha_11_BRASILANDIA',
                                'SIRGAS_SHP_curvaintermediaria_linha_11_BRASILANDIA.shp'))
curvas_nivel_seg <- sf::read_sf(file.path('../dados',
                                          'SIRGAS_SHP_curvaintermediaria_11_BRASILANDIA',
                                          'SIRGAS_SHP_curvaintermediaria_segm_11_BRASILANDIA',
                                          'SIRGAS_SHP_curvaintermediaria_segm_11_BRASILANDIA.shp'))
# Aqui devemos verificar as colunas e identificar aquelas que serão mantidas posteriormente.
names(curvas_nivel_linha)
names(curvas_nivel_seg)
sf::st_crs(curvas_nivel_linha)$input
rm(curvas_nivel_linha, curvas_nivel_seg)
gc()
# Implementando a leitura em lote dos arquivos.
diretorio_dados <- '../dados/'
prefixo_arquivos_curvas <- 'SIRGAS_SHP_curvaintermediaria.*shp$'
caminho_arquivos_curvas <- list.files(diretorio_dados, pattern = prefixo_arquivos_curvas, recursive = TRUE, full.names = TRUE)
caminho_arquivos_curvas


# Função para ler arquivo com dados das curvas de nível.
le_arquivo_curvas <- function (arquivo) {
                                          curvas_nivel <- sf::read_sf(arquivo)
                                          # Seleciona as colunas de interesse.
                                          curvas_nivel <- curvas_nivel[, c('ISOVALOR', 'geometry')]
                                          sf::st_crs(curvas_nivel) <- 31983
                                          return(curvas_nivel)
                                        }
# Cria uma lista com os dataframes com dados de cada arquivo.
curvas_nivel <- lapply(caminho_arquivos_curvas, le_arquivo_curvas)
length(curvas_nivel)
# Junta os dados na lista em um único dataframe
curvas_nivel <- do.call(rbind, curvas_nivel)

# Cuidado com o plot pois pode ser pesado para renderizar.
plot(curvas_nivel[sample(nrow(curvas_nivel), nrow(curvas_nivel)*0.1 ), ])
# Com o mapview
curvas_nivel_agrupada <-dplyr::group_by(curvas_nivel, ISOVALOR)
curvas_nivel_agrupada <- dplyr::summarise(curvas_nivel_agrupada, geometry=sf::st_combine(geometry) )
mapa <- mapview::mapview(curvas_nivel_agrupada)
mapa

# Arquivo coom os dados de elevação (MDT) cobrindo a região.
mdt <- terra::rast('../dados/rasters_SRTMGL1/output_SRTMGL1.tif')
mdt
mdt[22,22]
terra::crs(mdt, describe=TRUE)
mdt <- terra::project(mdt, "epsg:31983")
terra::plot(mdt)
# Seleciona os dados de MDT apenas na região de interesse. Note o buffer na área para 
# que a seleção ultrapasse os limites, necessário para os cálculos posteriores de slope.
# Quando vetor, pega o bbox
mdt <- terra::crop(mdt, sf::st_buffer(limites_subprefeitura, 300), touches=FALSE)
terra::plot(mdt)
# Mascara tudo de uma vez.
mdt <- terra::mask(mdt, mask=terra::vect(sf::st_buffer(limites_subprefeitura, 300)), touches = FALSE)
terra::plot(mdt)

# Favelas na região
dados_favelas <- sf::read_sf('../dados/SIRGAS_SHP_favela/SIRGAS_SHP_favela.shp')

sf::st_crs(dados_favelas)$input
sf::st_crs(dados_favelas) <- 31983
favelas_subprefeitura <- sf::st_intersection(dados_favelas, limites_subprefeitura)


# 3.x Gerar curvas de nível a partir do MDT
# Primeiro vamos observar como seriam curvas de nível a partir dos dads de MDT
# fornecidos.
# Para visualização rápida use o contour do terra.
terra::contour(mdt, add=TRUE, nlevels = 100)
mapview::mapview(terra::as.contour(mdt, nlevels = 100), map=mapa@map)

rm(mapa)
gc()

# 3.2 Gerar Modelo Digital do Terreno a partir de curvas de nível

# Rede TIN.
vertices_curvas <- apply(curvas_nivel, MARGIN = 1, FUN= function (linha) {
                                            vertices <- data.frame(sf::st_coordinates(linha$geometry)[,1:2])
                                            isovalor <- data.frame(z=rep(linha$ISOVALOR, nrow(vertices)))
                                            return(cbind(vertices, isovalor))
                                            })
vertices_curvas <- data.table::rbindlist(vertices_curvas)
vertices_curvas <- sf::st_multipoint(as.matrix(vertices_curvas))
tin_network <- sf::st_triangulate(vertices_curvas)
class(tin_network)

tin_network <- sf::st_collection_extract(tin_network, type = c("POLYGON"))
class(tin_network)
tin_network <- sf::st_as_sf(tin_network)


class(tin_network)
sf::st_crs(tin_network) <- 31983
sf::st_as_text(tin_network[1,]$x)

# Salva tin como linhas.
tin_network_linhas <- sf::st_cast(tin_network, "LINESTRING")

class(tin_network_linhas)
sf::st_as_text(tin_network_linhas[1,]$x)
sf::write_sf(tin_network_linhas, '~/Downloads/teste_tin.gpkg')
rm(tin_network_linhas)
gc()
# Cria um raster vazio.
grid_area <- sf::st_make_grid(limites_subprefeitura, cellsize = c(10, 10), what = "centers")
grid_area <- sf::st_as_sf(grid_area)
ind_grid_area <- sf::st_intersects(grid_area, limites_subprefeitura)
ind_grid_area <- lengths(ind_grid_area)
grid_area <- grid_area[ind_grid_area > 0, ]
tin_network_xy <- sf::st_zm(tin_network)


triangulo <- sf::st_contains(tin_network_xy, sf::st_set_precision(grid_area,1))
rm(tin_network_xy)
gc()
id_pontos_grid <- which(lengths(triangulo) > 0)
pontos_grid <- lapply(id_pontos_grid, function(x) {return(data.frame(id_triangulo=x, ponto=grid_area[triangulo[[x]],1]))})

pontos_grid <- data.table::rbindlist(pontos_grid)


coord <- sf::st_coordinates(pontos_grid$x)
coord <- cbind(coord, pontos_grid$id_triangulo)
colnames(coord)[3] <- 'id_triangulo'

resultado <- lapply (1:nrow(pontos_grid), function(i) {
  id_triangulo <- coord[i,3]
  pontos <- sf::st_coordinates(tin_network[id_triangulo,]$x)[1:3,1:3]#triangulo[id_triangulo,]$x)[1:3,1:3]
  pontos
  a <- (pontos[2,]-pontos[1,])
  b <- (pontos[3,]-pontos[1,])
  c <- c(a[2]*b[3]-a[3]*b[2], a[3]*b[1]-a[1]*b[3], a[1]*b[2]-a[2]*b[1])
  
  x <- coord [i,1]
  y <- coord[i, 2]
  z <- (-c[1]*(x-pontos[1,1]) - c[2]*(y-pontos[1,2]))/c[3]+pontos[1,3]
  return(z)
})

resultado <- unlist(resultado)
pontos_grid <- cbind(pontos_grid, resultado)
raster_output <- cbind(coord[,1:2], resultado)
colnames(raster_output) <- c('X', 'Y', 'Z')
raster_output
raster_output <- terra::rast(raster_output, type="xyz", crs="epsg:31983")

raster::plot(raster_output)
terra::writeRaster(raster_output, '~/Downloads/raster_tin_10m.tif', overwrite=TRUE)

sf::write_sf(tin_network, '~/Downloads/tin_network.gpkg')
rm(tin_network)
gc()

# 3.3 Gerar Modelo de Declividade a partir de MDT
terra::writeRaster(mdt, '~/Downloads/mdt.tif', overwrite=TRUE)
mdt_selecionado <- raster_output
declividade <- terra::terrain(mdt_selecionado, v='slope')
#terra::plot(terra::terrain(mdt_selecionado))
declividade <- terra::mask(declividade, terra::vect(sf::st_buffer(limites_subprefeitura,30)), touches=FALSE)
terra::writeRaster(declividade, '~/Downloads/declividade_10m.tif', overwrite=TRUE)
mapa <- mapview::mapview(declividade, na.color="transparent", col.regions= RColorBrewer::brewer.pal(9, "Blues")) + 
  mapview::mapview(mdt, na.color="transparent") + 
  mapview::mapview(limites_subprefeitura, alpha.regions=0.0, lwd=2)


# 3.4 Estatística zonal (análise zonal da declividade)
estatisticas_zonais_media <- terra::zonal(declividade, terra::vect(favelas_subprefeitura), fun="mean", na.rm = TRUE, touches = FALSE)
names(estatisticas_zonais_media) <- 'media'
estatisticas_zonais_max <- terra::zonal(declividade, terra::vect(favelas_subprefeitura), fun="max", na.rm = TRUE, touches = FALSE)
names(estatisticas_zonais_max) <- 'max'
estatisticas_zonais <- cbind(estatisticas_zonais_media, estatisticas_zonais_max)
estatisticas_zonais <- cbind(favelas_subprefeitura, estatisticas_zonais)
mapa + mapview::mapview(estatisticas_zonais, na.color="transparent", col.regions= RColorBrewer::brewer.pal(9, "Blues"), zcol='media') + 
  mapview::mapview(estatisticas_zonais, na.color="transparent", col.regions= RColorBrewer::brewer.pal(9, "Reds"), zcol='max') +
  mapview::mapview(limites_subprefeitura, alpha.regions=0.0, lwd=2)


rm(list=ls())
gc()
