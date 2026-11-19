# A biblioteca mapview é utilizada para visualização de dados espaciais em mapas iterativos. 
# Aqui, é utilizado a função mapinfo para criar um mapa sem nenhum dado adicionado e utilizando como base o OpenStreetMap.
mapview::mapview(map.types="OpenStreetMap")

# Para carregar dados vetoriais, pode ser utilizada a função read_sf do pacote sf. 
# Nesse caso, a função recebe simplesmente o caminho para o arquivo .shp como parâmetro.
# O resultado é colocado na variável dados_corticos.
# Em seguida, novamente é utilizada a função mapview, desta vez ela recebe como parâmetro
# a variável com os dados baixados do geosampa. Observe o erro que ocorre por falta do
# arquivo .prj indicando qual deve ser o CRS da base de dados.
# A seguir, cheque como está o CRS dos dados com a função st_crs do pacote sf. Essa
# função gera uma lista que pode ser de difícil visualização. 
dados_corticos <- sf::read_sf('../dados/SAD69-96_SHP_cortico/SAD69-96_SHP_cortico.shp')
mapview::mapview(dados_corticos, map.types="OpenStreetMap")
sf::st_crs(dados_corticos)

# É possível visualizar o atributo com
# o EPSG usando chamando diretamente o elemento input da lista, usando o operador $.
# Note que na última linha dessa sequência demonstra que a função st_crs pode ser
# aplicada diretamente nas geometrias associadas ao dataframe espacial.
sf::st_crs(dados_corticos)$input
sf::st_crs(dados_corticos$geometry)$input

# Como  não há CRS associado, precisamos ajustá-lo, mas primeiro vamos checar os
# detalhes do EPSG 5533 (SAD69(96) - 23S) com o mesmo comando utilizado para o dataframe espacial.
# Note como o método consegue lidar com parâmetros de tipo diferente.
# SAD69(96) / UTM zone 23S: https://epsg.io/5533
crs <- sf::st_crs(5533)
crs$input
crs$proj4string

# Ajusta o CRS.
sf::st_crs(dados_corticos) <- 5533
sf::st_crs(dados_corticos)
sf::st_crs(dados_corticos)$input
sf::st_crs(dados_corticos)$proj4string
sf::st_crs(dados_corticos$geometry)$input
mapview::mapview(dados_corticos, map.types="OpenStreetMap")

# SIRGAS 2000 / UTM zone 23S: https://epsg.io/31983
dados_corticos_sirgas <- sf::st_transform(dados_corticos, 31983)

mapview::mapview(dados_corticos_sirgas, map.types="OpenStreetMap")

# Verifique que eles estão perfeitamente sobrepostos.
mapview::mapview(dados_corticos_sirgas, map.types="OpenStreetMap") + mapview::mapview(dados_corticos)

# Salvando os dados com CRS definitivamente.
sf::write_sf(dados_corticos, '../dados/SAD69-96_SHP_cortico/SAD69-96_SHP_cortico.shp', delete_layer = FALSE)
sf::write_sf(dados_corticos, '../dados/SAD69-96_SHP_cortico/SAD69-96_SHP_cortico.shp', delete_layer = TRUE)
dir.create('../dados/SIRGAS2000_SHP_cortico/')
sf::write_sf(dados_corticos_sirgas, '../dados/SIRGAS2000_SHP_cortico/SIRGAS2000_SHP_cortico.shp', delete_layer = TRUE)

# Releia o arquivo e cheque que o CRS está ajustado corretamente.
dados_corticos_sirgas <- sf::read_sf('../dados/SIRGAS2000_SHP_cortico/SIRGAS2000_SHP_cortico.shp')
sf::st_crs(dados_corticos_sirgas)$input
