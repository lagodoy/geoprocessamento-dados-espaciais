# 1. Introdução

# 2. Preparação dos dados
# Normalmente a informação de encoding fica no arquivo com extensão .cpg do conjunto
# do shapefile lido, caso não exista, a atribuição será um charset padrão. Abra os dataframes para checar
# se as strings estão com caracteres estranhos. No caso dos dados do CEM testados (até o momento) não há
# o arquivo cpg e pode haver esse problema. Caso ele ocorra, use o parâmetro options = "ENCODING=latin1",
# confome última linha do bloco de códigos abaixo.
# 2.1 Leitura dos dados
dados_favelas <- sf::read_sf('../dados/SIRGAS_SHP_favela/SIRGAS_SHP_favela.shp')
dados_subprefeituras <- sf::read_sf('../dados/SIRGAS_SHP_subprefeitura/SIRGAS_SHP_subprefeitura.shp')
dados_saude <- sf::read_sf('../dados/SAU2022_RMSP_CEM/SAU2022_RMSP_CEM.shp')#, options = "ENCODING=latin1")
#dados_saude <- sf::read_sf('../dados/SAU2022_RMSP_CEM/SAU2022_RMSP_CEM.shp', options = "ENCODING=latin1")

# 2.2 Checagem dos CRS's e atribuiççao ou transformaççao quando necessaŕio.
sf::st_crs(dados_favelas)$input
sf::st_crs(dados_subprefeituras)$input
sf::st_crs(dados_saude)$input

sf::st_crs(dados_favelas) <- 31983
sf::st_crs(dados_subprefeituras) <- 31983

dados_saude <-  sf::st_transform(dados_saude, crs = 31983)

# 3. Seleção por atributo e Operações espaciais
# 3.1 Seleção por atributo
dados_favelas
dados_subprefeituras$sp_nome
selecao_subprefeitura <- dados_subprefeituras$sp_nome=='BUTANTA'
limites_subprefeitura <- dados_subprefeituras[selecao_subprefeitura, ]$geometry

# 3.2 Clipping
favelas_subprefeitura <- sf::st_intersection(dados_favelas, limites_subprefeitura)

mapa <- mapview::mapview(sf::st_boundary(limites_subprefeitura), 
                         layer.name='Subprefeitura', map.types='OpenStreetMap')
mapa
mapa <- mapa + mapview::mapview(favelas_subprefeitura, layer.name='Favelas')
mapa

# 3.3 Como exercício, faça o mesmo para a base de dados de saúde, selecionando
# somente os equipamentos públicos de alta complexidade.
saude_alta_complexidade <- dados_saude[(dados_saude$SEGMENTO %in% c('SAUGM', 'SAUGE'))
                                       & (dados_saude$TIPO =='HOSP' | dados_saude$TIPO == 'PATEN'), ]
saude_subprefeitura <- sf::st_intersection(saude_alta_complexidade, limites_subprefeitura)

mapa <- mapa + mapview::mapview(saude_subprefeitura, layer.name='Equipamentos de Saúde Públicos de Alta Complexidade')
mapa

# 3.4 Buffering
saude_subprefeitura_buffer<- sf::st_buffer(saude_subprefeitura, 2000)
mapa <-  mapa +  mapview::mapview(sf::st_boundary(saude_subprefeitura_buffer), 
                                  layer.name='Alcance do equipamento - 2km')
mapa

# 3.5 Intersecção
favelas_cobertura <- sf::st_intersection(favelas_subprefeitura, saude_subprefeitura_buffer)
mapa <-  mapa + mapview::mapview(favelas_cobertura, label='Dentro',
                                 layer.name='Favelas dentro em área de alcance de equipamento')
mapa

# 3.6 Difference
favelas_fora_raio <- sf::st_difference(favelas_subprefeitura, 
                                       sf::st_union(saude_subprefeitura_buffer))

mapa <-  mapa + mapview::mapview(favelas_fora_raio, color='red', col.regions='pink', 
                                 label='Fora', layer.name='Favelas fora de área de alcance de equipamento')
mapa
