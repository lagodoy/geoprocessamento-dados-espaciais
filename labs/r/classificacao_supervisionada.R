# Preparação dos dados
# Carregamento dos dados
dados_raster <- terra::rast('../dados/sr_rad_correct_ndvi.tif')
dados_raster

# Classificação supervisionada
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
# Gerando as amostras automaticamente 
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

# Treinamento e classificação
# Treinamento
resultado_rf <- randomForest::randomForest(classe ~ ., amostra_treinamento[,-1])

# Matriz de confusão
resultado_rf

# Classificação da imagem
dados_raster_predito <- terra::predict(dados_raster, resultado_rf)

# Visualização da classificação
vetor_cores <- c("#346B45", "#ABD6B8", "#2347DE", '#BDBDBF', '#E3B16F')
terra::plot(dados_raster_predito, col=vetor_cores)

# Mapa com todas as classes.
mapview::mapview(dados_raster_predito, col.regions=vetor_cores, na.col='transparent', alpha=1)
# Visualiza apenas uma classe.
mapview::mapview(terra::clamp(dados_raster_predito, upper=2, lower=2, values=FALSE), 
                 col.regions=vetor_cores[2], na.col='transparent', alpha=1)

# Calculando a área de cada tipo de uso do solo.
area_classe <- terra::expanse(dados_raster_predito, byValue=TRUE, unit='km')
area_classe

# Area total.
area_total <- terra::expanse(dados_raster_predito, byValue=FALSE, unit='km')
area_total

area_classe$prop <- 100*area_classe$area/area_total$area
area_classe

# Teste e validação para classificadores.
# Divisão das amostras em subconjuntos
amostra_conjuntos <- lapply(1:5, 
       function(x){
         amostra_classe <- amostra_treinamento[amostra_treinamento$classe==x,]
         tamanho_amostra <- nrow(amostra_classe)
         amostra_classe$conjunto <- sample(c('treino', 'validacao', 'teste'), 
                                           size=tamanho_amostra, 
                                           replace=TRUE,
                                           prob=c(0.7, 0.15, 0.15))
         return(amostra_classe)
       }
)
amostra_conjuntos <- do.call(rbind, amostra_conjuntos)

library(magrittr)
# Conjunto pra treinamento.
amostra_conjunto_treinamento <- amostra_conjuntos %>% dplyr::filter(conjunto=='treino')

# Conjunto de validação
amostra_conjunto_validacao <- amostra_conjuntos %>% dplyr::filter(conjunto=='validacao')

# Conjunto para o teste final.
amostra_conjunto_teste <- amostra_conjuntos %>% dplyr::filter(conjunto=='teste')

#  Treinamento e avaliação dos modelos
# Processo de seleção de modelo.
# Treinamento RF
resultado_rf <- randomForest::randomForest(classe ~ ., 
                                           amostra_conjunto_treinamento[,c(-1,-ncol(amostra_conjunto_treinamento))])
matriz_confusao_rf = resultado_rf$confusion

# Acurácia no conjunto de treinamento.
100*sum(diag(matriz_confusao_rf))/sum(matriz_confusao_rf)

# Validação
predito_validacao_rf <- predict(resultado_rf, amostra_conjunto_validacao)
validacao_rf <- data.frame(classe=amostra_conjunto_validacao$classe, 
                       predito=predito_validacao_rf)
matriz_validacao_rf <- table(validacao_rf)
acuracia_rf <- sum(diag(matriz_validacao_rf))/sum(matriz_validacao_rf)
100 * acuracia_rf
100*prop.table(matriz_validacao_rf, margin = 1)

# Outro algoritmo para comparação.
# Treinamento
resultado_svm <- e1071::svm(classe ~ ., 
                            amostra_conjunto_treinamento[,c(-1,-ncol(amostra_conjunto_treinamento))])

matriz_confusao_svm = table(list(real=amostra_conjunto_treinamento$classe, 
                              predito=resultado_svm$fitted))

100*sum(diag(matriz_confusao_svm))/sum(matriz_confusao_svm)

#  Validação
predito_validacao_svm <- predict(resultado_svm, amostra_conjunto_validacao)
validacao_svm <- data.frame(classe=amostra_conjunto_validacao$classe, 
                       predito=predito_validacao_svm)
matriz_validacao_svm <- table(validacao_svm)
acuracia_svm <- sum(diag(matriz_validacao_svm))/sum(matriz_validacao_svm)
100*prop.table(matriz_validacao_svm)

# Compara os dois modelos e seleciona o de melhor acurácia para apresentar.
if (acuracia_rf > acuracia_svm) {
  resultado_modelo_escolhido <- resultado_rf
  message('Random Forest')
} else{
  resultado_modelo_escolhido <- resultado_svm
  message('SVM')
}

#  Teste final e classificação da imagem
#  Classificação da imagem
dados_raster_predito <- terra::predict(dados_raster, resultado_modelo_escolhido)
dados_raster_predito

# Classificação no conjunto de testes.
predito_validacao_selecionado <- predict(resultado_modelo_escolhido, amostra_conjunto_teste)

teste_selecionado <- data.frame(classe=amostra_conjunto_teste$classe, 
                        predito=predito_validacao_selecionado)

# Matriz de erro no conjuntos de testes.
matriz_teste_selecionado <- table(teste_selecionado)
matriz_teste_selecionado
100*prop.table(matriz_teste_selecionado)

# Acurácia no conjunto de testes.
acuracia_selecionado <- sum(diag(matriz_teste_selecionado))/sum(matriz_teste_selecionado)
acuracia_selecionado

#  Visualização da classificação
raster_visualizacao <- as(terra::resample(terra::stretch(dados_raster, histeq=TRUE), y=c(1.5,1.5)), 'Raster')
visualizacao <- mapview::viewRGB(raster_visualizacao, 
                 r=1, g=2, b=3,
                 na.col='transparent',
                 layer.name='imagem')
visualizacao + mapview::mapview(dados_raster_predito, 
                 col.regions=vetor_cores, 
                 na.col='transparent', 
                 alpha=1,
                 layer.name='Classificação')
  
# Exercício: Verifique se suas amostras estão desbalanceadas. Caso estejam, ajuste.

