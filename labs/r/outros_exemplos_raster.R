# Preparação dos dados
# Carregamento dos dados
dados_raster <- terra::rast('../dados/sr_rad_correct_ndvi.tif')
dados_raster

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

#  Delimitação das áreas das amostras

# Gerando as amostras automaticamente no GEE
# Amostragem com todos os pixels nas áreas
areas_amostras <- terra::vect('../dados/amostras.shp')
amostra_treinamento <- terra::extract(dados_raster, areas_amostras)
amostra_treinamento
classes_poligonos <- data.frame(id=1:nrow(areas_amostras), classe=areas_amostras$classe)
amostra_treinamento <- merge(amostra_treinamento, classes_poligonos, by.x='ID', by.y='id')
unique(amostra_treinamento$classe)
amostra_treinamento$classe <- factor(amostra_treinamento$classe)
names(amostra_treinamento)
names(amostra_treinamento[,-1])
amostra_treinamento <- na.omit(amostra_treinamento)

# Teste e validação para classificadores.
# 2.2 Divisão da amostra em subconjuntos
amostra_conjuntos <- lapply(1:5, 
                            function(x){
                              amostra_classe <- amostra_treinamento[amostra_treinamento$classe==x,]
                              tamanho_amostra <- nrow(amostra_classe)
                              amostra_classe$conjunto <- sample(c('treino', 'teste'), 
                                                                size=tamanho_amostra, 
                                                                replace=TRUE,
                                                                prob=c(0.7,0.3))
                              return(amostra_classe)
                            }
)

amostra_conjuntos <- do.call(rbind, amostra_conjuntos)
library(magrittr)
amostra_conjunto_treinamento <- amostra_conjuntos %>% dplyr::filter(conjunto=='treino')

# Processo de seleção de modelo.
# Conjunto de teste
amostra_conjunto_teste <- amostra_conjuntos %>% dplyr::filter(conjunto=='teste')
resultado_rf <- randomForest::randomForest(classe ~ ., amostra_conjunto_treinamento[,c(-1,-ncol(amostra_conjunto_treinamento))])

predito_teste_rf <- predict(resultado_rf, amostra_conjunto_teste)
teste_rf <- data.frame(classe=amostra_conjunto_teste$classe, 
                       predito=predito_teste_rf)
matriz_teste_rf <- table(teste_rf)
acuracia_rf <- sum(diag(matriz_teste_rf))/sum(matriz_teste_rf)

100*prop.table(matriz_teste_rf, margin = 1)

# Classificação da imagem
dados_raster_predito <- terra::predict(dados_raster, resultado_rf)
vetor_cores <- c("#346B45", "#ABD6B8", "#2347DE", '#BDBDBF', '#E3B16F')
# Visualização da classificação
mapa_final <- mapview::mapview(dados_raster_predito, col.regions=vetor_cores, na.col='transparent', alpha=1)

# Forma simples de tratar ruídos.
raster_classificado <- terra::focal(dados_raster_predito, w=3,fun='modal')

vetor_objetos <- terra::as.polygons(raster_classificado)
terra::plot(vetor_objetos, col=vetor_cores)

mapa_final <- mapa_final + mapview::mapview(vetor_objetos, col.regions=vetor_cores, na.col='transparent', alpha=1)

mapa_final +  mapview::mapview(raster_classificado, col.regions=vetor_cores, na.col='transparent', alpha=1)

# Calculando a área de cada tipo de uso do solo.
area_classe <- terra::expanse(dados_raster_predito, byValue=TRUE, unit='km')
area_classe

# Area total.
area_total <- terra::expanse(dados_raster_predito, byValue=FALSE, unit='km')
area_total

area_classe$prop <- 100*area_classe$area/area_total$area
area_classe

