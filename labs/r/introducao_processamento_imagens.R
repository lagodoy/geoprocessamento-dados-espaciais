# Sensoriamento Remoto:
# Introdução ao processamento digital de imagens,
# resoluções, metadados e busca por imagens no GEE


# 3.6.2 Criando uma feature no GEE 15
limites_subprefeituras <- sf::st_read('../dados/geoportal_subprefeitura_v2.gpkg')
limites_subprefeituras <- sf::st_transform(limites_subprefeituras, 32723)

#3.6.3 Buscando uma coleção de imagens
# MUX 
# https://data.inpe.br/geonetwork/srv/api/records/7594a5c2-82f9-4d31-8065-28185bd94d3c
# - B05 (Azul) : 0,45 - 0,52 µm
# - B06 (Verde): 0,52 - 0,59 µm
# - B07 (Vermelho): 0,63 - 0,69 µm
# - B08 (Infravermelho próximo): 0,77 - 0,89 µm

#3.7 Trabalhando com imagens de satélite no GEE 18

# Carregando uma imagem em memória com o terra.
nome_base_arq_mux <- '../dados/cbers_4a_mux/CBERS_4A_MUX_20240624_203_142_L4_BAND'
red_mux <- terra::rast(paste0(nome_base_arq_mux, '7.tif'))
green_mux <- terra::rast(paste0(nome_base_arq_mux, '6.tif'))
blue_mux <- terra::rast(paste0(nome_base_arq_mux, '5.tif'))
nir_mux <- terra::rast(paste0(nome_base_arq_mux, '8.tif'))


imagem_mux <- terra::rast(list(red_mux, green_mux, blue_mux, nir_mux))

names(imagem_mux)
names(imagem_mux) <- c('red', 'green', 'blue', 'nir')
names(imagem_mux)

# Extraindo informações básicas das imagens.
# Extensão da imagem, quantidade de linhas e crs.
dimensoes_mux <- dim(blue_mux)
dimensoes_mux

imagem_mux
extensao <- terra::ext(imagem_mux)
extensao
class(extensao)
terra::crs(imagem_mux,proj=TRUE, describe=FALSE)
terra::crs(imagem_mux,proj=FALSE, describe=TRUE)

#3.7.1 Visualizando uma imagem com terra em RGB.
terra::plotRGB(imagem_mux, r=1, g=2, b=3)
# Visualizando com RGB com stretch.
# character. Option to stretch the values to increase contrast: "lin" (linear) or "hist" (histogram).
# The linear stretch uses stretch with arguments minq=0.02 and maxq=0.98
terra::plotRGB(imagem_mux, r=1, g=2, b=3, stretch="hist")
terra::plotRGB(imagem_mux, r=1, g=2, b=3, stretch="lin")

# 3.6.1 Localização da área de estudo 14
# Para saber qual a área de estudos, após ter baixado os dados adequadamente.
# Carregue uma imagem, pegue a sua extensão como poligono (bounding bod, bbox, da imagem)
# e calcule a centróide desse bbox.
extensao_poly <- terra::vect(extensao)
# Note q nao ha sitema de referencias e Voce precisa atribuir um crs.
terra::crs(extensao_poly) <- "epsg:32723"
# Visualizacao simples
terra::plot(extensao_poly)

# Obs: Note q é possivel coverter para o padrão do pacote sf.
sf::st_as_sf(extensao_poly)

# Agora podemos visualizar os dados que coletamos até agora.
# A partir do mapa gerado, você pode escolher o nome da subprefeitura de interesse
# clicando dentro do bbox da imagem em uma área de subprefeitura onde os pixels 
# tenham valores e aparentem ter uma melhor qualidade de informações.
# Obs: a função resample usada para reduzir a imagem será explicada posteriormente
# Obs2:  Caso a imagem não cubra uma porção interia de uma subprefeitura (ou tenha
# muitas nuvens na região), volte alguns passos e carregue uma outra imagem para testar.

imagem_reduzida <- terra::resample(imagem_mux, c(15,15))
paleta_cinzas <- grDevices::hcl.colors(250, palette = "Grays")
mapview::mapview(extensao_poly, 
                 map.types = "OpenStreetMap", 
                 layer.name = "BBOX",
                 color='red',
                 lwd=2,
                 col.regions='red',
                 alpha.regions=0) +
  mapview::viewRGB(as(imagem_reduzida, 'Raster'), 1,2,3, quantiles=c(0.1,0.9),
                   #col.regions = paleta_cinzas,
                   na.color='transparent',
                   layer.name = 'Banda')+
  mapview::mapview(terra::centroids(extensao_poly), 
                   cex=5, layer.name = "Centróide") +  
  mapview::mapview(limites_subprefeituras, layer.name = "Subprefeituras",color='blue', lwd=2, alpha.regions=0)

# 3.7.2 Recortando uma parte de uma imagem
# SE até aqui está tudo ok, agora podemos selecionar uma área para trabalharmos melhor.
# A partir do layer de subprefeituras, filtre apenas a escolhida no item anterior.
limites_subprefeituras$nm_subprefeitura
area_interesse <- limites_subprefeituras[limites_subprefeituras$nm_subprefeitura=="FREGUESIA-BRASILANDIA",]

area_interesse_vect <- terra::vect(area_interesse)
recorte_bbox <- terra::crop(imagem_mux, area_interesse_vect)
terra::plotRGB(recorte_bbox)
recorte_area <- terra::mask(imagem_mux, area_interesse_vect)
# Trim reduz o extent para o novo bbox?
recorte_area <- terra::trim(recorte_area)
terra::plotRGB(recorte_area)

# Para visualizar usando o mapview, fazemos:
# Note que agora, depdendendo do tamanho da área, é possível plotar o raster
# no mapview.
mapview::viewRGB(as(recorte_area, 'Raster'), 1,2,3, quantiles=c(0.1,0.9),
                   #col.regions = paleta_cinzas,
                   na.color='transparent',
                   layer.name = 'Subprefeitura',
                   map.types = "OpenStreetMap")+
  mapview::mapview(area_interesse, zcol = 'nm_subprefeitura',
                   color='blue', lwd=2,alpha.regions=0)


#3.7.3 Calculando o valor médio dos pixels de uma banda
# Primeiro na imagem clipada.
terra::global(recorte_area, fun="mean", na.rm=TRUE)

# Para o tiff todo, ou quando as áreas tiverem muitos pixels, recomendo utilizar uma amostra
ind_sample_mux <- sample(dimensoes_mux[1]*dimensoes_mux[2], 10000)
amostra_banda_mux <- imagem_mux[ind_sample_mux]
summary(amostra_banda_mux)
mean(amostra_banda_mux$CBERS_4A_MUX_20241201_202_143_L2_BAND5, na.rm = TRUE)
mean(amostra_banda_mux, na.rm=TRUE)

# Você pode fazer uma amostra apenas dentro do recorte para comparar.

# VOce pode fazer tudo isso individualmente para cada banda. Exercício.

# 3.9 Resolução espacial
terra::res(imagem_mux)

#3.18.4 Tipos armazenados nas bandas e resolução radiométrica
terra::datatype(imagem_mux)
?terra::datatype

# 3.10 Resolução espectral
# A faixa espectral (“Wavelength”) de cada banda, encontrada na documentação do satélite.

# 3.11 Resolução temporal
# Tambem pode ser encontrada na documentaçao do satelite.

# 3.13 Trabalhando com metadados via código
# Metadados
# Em memória.
metadados_mux_nir_list <- terra::meta(nir_mux)
metadados_mux_nir <- terra::metags(nir_mux)

metadados_mux_lista <- terra::meta(imagem_mux)
metadados_mux <- lapply(seq_along(metadados_mux_lista), 
                        function(i) {
                          return(data.frame(nome_banda=names(imagem_mux)[i], metadados_mux_lista[[i]]))
                        })
metadados_mux[[1]]
metadados_mux <- do.call(rbind, metadados_mux)


# No arquivo xml fornecido.
library(magrittr)
metadados_xml_red_mux <- xml2::read_xml(paste0(nome_base_arq_mux, '7.xml'))
metadados_xml_red_mux
# Verifica se há namespaces.
metadados_xml_red_mux %>% xml2::xml_ns()
# Remove os namespaces
metadados_xml_red_mux <- metadados_xml_red_mux %>% xml2::xml_ns_strip()
# Pega todos os nomes de atributos.
# transforma numa lista (node) com todos os nós do documento.
xml_dados_completos <- metadados_xml_red_mux %>% xml2::xml_find_all("//*")
xml_dados_completos
# Extrai os caminhos completos dos nós.
caminhos_nos <- xml2::xml_path(xml_dados_completos) %>% data.frame()
names(caminhos_nos) <- c('caminho_completo')
head(caminhos_nos)

# 3.13.3 Bandas, projeção cartográfica e resolução espacial
# Bandas.
metadados_xml_red_mux %>% xml2::xml_find_all("//availableBands/*") %>% xml2::xml_text()

# projeção cartográfica
# CRS. OBS: Essa inforamção na verdade fica embutida dentro do cabeça~jho do arquivo Tif.
# O XML auxiliar é normalmente utilizado para algumas informações extras que não são suportadas pelo formato GEOTIFF.
# No caso dos dados do CBERS temos uma breve descrição do CRS, mas não completa.
# O que estaria faltando?
metadados_xml_red_mux %>% xml2::xml_find_all("//image/datumName") %>% xml2::xml_text()
metadados_xml_red_mux %>% xml2::xml_find_all("//image/projectionName") %>% xml2::xml_text()

# Resolucao
metadados_xml_red_mux %>% xml2::xml_find_all("//image/verticalPixelSize") %>% xml2::xml_text()
metadados_xml_red_mux %>% xml2::xml_find_all("//image/horizontalPixelSize") %>% xml2::xml_text()

# datas das imagens
metadados_xml_red_mux %>% xml2::xml_find_all("//image/timeStamp/*") #%>% xml2::xml_text()


# 3.18.3 Exemplos de cálculos no GEE
# LEia uma segunda imagem
terra::global(red_mux, 'range', na.rm=TRUE)
terra::global(red_mux, 'max', na.rm=TRUE) - terra::global(red_mux, 'min', na.rm=TRUE)

# Intervalo interquartil.
n_amostra <- 0.1 * terra::ncell(red_mux)
quantis <- terra::global(red_mux, fun=quantile, na.rm=TRUE, maxcell=n_amostra)
quantis
quantis$X75. - quantis$X25.

# Salva um raster.
terra::writeRaster(imagem_mux, '~/Downloads/teste_imagem.tiff', overwrite=TRUE)



