# Estatísticas, histogramas, contraste e composições de imagens
#no GEE

## 3.1 Preparação dos dados
# Neste lab vamos usar os dados  WPM do CBERS 4.0. Vamos trabalhar apenas com os
# DN, por falta de informaçõs para se obter a reflectância. Apesar disso,
# correção atmosférica simples com DOS será feita.
nome_base <- '../dados/cbers_4a_wpm/CBERS_4A_WPM_20240529_202_143_L4_BAND'
#lista_bandas <- c(3, 2, 1, 4)
red <- terra::rast(paste0(nome_base, '3.tif'))
green <- terra::rast(paste0(nome_base, '2.tif'))
blue <- terra::rast(paste0(nome_base, '1.tif'))
nir <- terra::rast(paste0(nome_base, '4.tif'))
# Gera raster com as bandas
imagem <- terra::rast(list(red, green, blue, nir))
terra::datatype(imagem)
terra::summary(imagem)
rm(red,green,blue, nir)

gc()

# Limites para recorte da área de interesse.
limites_subprefeituras <- sf::st_read('../dados/geoportal_subprefeitura_v2.gpkg')
limites_subprefeituras <- sf::st_transform(limites_subprefeituras, 32723)

# Encontra a melhor área
## Redução da resolução.
fator_resolucao <- 10
#red_binario <- terra::not.na(red)
dimensoes <- dim(imagem[[1]])
#const_matrix <- matrix(TRUE, nrow=dimensoes[1], ncol=dimensoes[2])
const_imagem <- terra::rast(terra::ext(imagem[[1]]), crs=terra::crs(imagem[[1]]), 
                            resolution=terra::res(imagem[[1]]))
dim(const_imagem)
const_imagem[] <- 1
#terra::plot(const_imagem)
red_binario <- terra::mask(const_imagem, imagem[[1]])
terra::plot(red_binario)
# O parâmetro em y é um fator multiplicador nas direções x e y, repectivamente.
red_reduzido <- terra::resample(red_binario, y=fator_resolucao, method='near', threads=TRUE)
terra::plot(red_reduzido)
tempo_inicio <- Sys.time()

# Calcula as áreas da imagem disponíveis em cada subprefeitura.
areas_cobertas <- lapply(limites_subprefeituras$ge_poligono, 
                                      function (area_poligono) {
                                        area_poligono_vect <- terra::vect(area_poligono)
                                        terra::crs(area_poligono_vect) <- 'epsg:32723'
                                        resultado_selecao <- terra::crop(red_reduzido, area_poligono_vect)
                                        resultado_selecao <- terra::mask(resultado_selecao, area_poligono_vect, touches = FALSE)
                                        #resultado_selecao < terra::trim(resultado_selecao)
                                        area <- terra::expanse(resultado_selecao)$area
                                        rm(resultado_selecao)
                                        gc()
                                        return(area)
                                      })

tempo_fim <- Sys.time()
print(tempo_fim-tempo_inicio)
areas_cobertas <- unlist(areas_cobertas)
# Calcula a proporção da área coberta.
areas_cobertas/sf::st_area(limites_subprefeituras)
limites_subprefeituras$nm_subprefeitura

# Observe como funciona o parametro tourches usado em mask:
# touches = TRUE é o padrão. If TRUE, all cells touched by lines or polygons
#will be masked, not just those on the line render path, or whose center point 
#is within the polygon
teste_false <- terra::mask(red_reduzido, terra::vect(limites_subprefeituras$ge_poligono[3]), touches = FALSE)
teste_false
teste_false <- terra::trim(teste_false)
names(teste_false) <- 'Touches_false'

teste_true <- terra::mask(red_reduzido, terra::vect(limites_subprefeituras$ge_poligono[3]), touches = TRUE)
teste_true
teste_true <- terra::trim(teste_true)
names(teste_true) <- 'Touches_true'

centroides_raster <- terra::as.points(teste_true, values = FALSE, na.rm = TRUE)
centroides_raster <- sf::st_as_sf(centroides_raster)

mapview::mapview(limites_subprefeituras$ge_poligono[3]) + 
mapview::mapview(teste_false, na.color='transparent', col.regions='red') + 
  mapview::mapview(teste_true, na.color='transparent', col.regions='blue') + 
  mapview::mapview(centroides_raster, na.color='transparent', col.regions='red') 
# Cast para trar do tipo units.
limites_subprefeituras[as.numeric(areas_cobertas/sf::st_area(limites_subprefeituras)) >= 1,]$nm_subprefeitura

# Você pode escolher uma área de interesse pelo nome, mas caso queria achar uma 
# área que tenha uma boa parte da imagem, o código seguinte acha a proporção de cada
# subprefeitura que contém imagem.
#area_interesse <- limites_subprefeituras[limites_subprefeituras$nm_subprefeitura=="FREGUESIA-BRASILANDIA",]
area_interesse <- limites_subprefeituras[3,]
area_interesse

area_interesse_vect <- terra::vect(area_interesse)
imagem_area_interesse <- terra::crop(imagem, area_interesse)
imagem_area_interesse <- terra::mask(imagem_area_interesse, area_interesse)
imagem_area_interesse <- terra::trim(imagem_area_interesse)
terra::plot(imagem_area_interesse)
# Correção atmosferica
correcao_atmosferica <- function (banda_img) {
  #banda_img <- terra::rast(paste0(nome_base, n_banda,'.tif'))
  #banda_img <- terra::mask(banda_img, roi)
  #banda_img <- terra::trim(banda_img)
  
  L1 <- terra::global(banda_img, fun=quantile, probs=0.01, na.rm=TRUE)
  print(L1)
  banda_img_corrigida <- banda_img - L1[1,1]
  banda_img_corrigida[banda_img_corrigida <=0] <- 0
  return(banda_img_corrigida)
}

imgs_corrigidas <- lapply(imagem_area_interesse, correcao_atmosferica)


composicao_final <- terra::rast(imgs_corrigidas)

rm(imgs_corrigidas)
gc()
names(composicao_final)
#terra::writeRaster(imagem_area_interesse, '~/Downloads/dn.tif', overwrite=TRUE)
#terra::writeRaster(composicao_final, '~/Downloads/sr_rad_correct.tif', overwrite=TRUE)
terra::hist(imagem_area_interesse)
terra::hist(composicao_final)
imagem_area_interesse <- composicao_final

# 3.2 Exibindo valores de um pixel no mapa no GEE
# coordenadas vs linha/coluna vs Célula 
linha <- sample(nrow(imagem_area_interesse), 1)
coluna <- sample(ncol(imagem_area_interesse), 1)
imagem_area_interesse[linha, coluna]
posicao <- 1 + (linha - 1) * (ncol(imagem_area_interesse)) + (coluna - 1)
# Terr::values pega todos os valores.
terra::values(imagem_area_interesse)[posicao,]
# Extrai da posicao dada no segundo parâmetro. A depender do valor desse segundo
# parãmetro, um tipo de assinatura de método aciona o método especifico. Na linha
# seguinte vamos tirar o valor com o número da célula dentro do raster.
terra::extract(imagem_area_interesse, posicao) 
# Em uma coordenadas específica, passando um ponto como referência. xy como TRUE
# retornajunto dos valores as coordenadas.
terra::extract(imagem_area_interesse, terra::centroids(area_interesse_vect), xy=TRUE)
resolucao <- terra::res(imagem_area_interesse)
vetor_coordenadas <- c(terra::xmin(imagem_area_interesse) + (resolucao[1]/2 + resolucao[1] * (coluna-1)),
                       terra::ymax(imagem_area_interesse) - (resolucao[1]/2 + resolucao[2] * (linha-1)))
coordenadas <- matrix(vetor_coordenadas, 
                      ncol=2,
                      byrow = FALSE)
coordenadas
terra::extract(imagem_area_interesse, 
               coordenadas, 
               cells=TRUE)
posicao

# Exercício: Você consegue encontrar o valor do pixel da centróide do polígono
# utilizando as posições de linhas e colunas ou o número da célula a partir das suas coordenadas?


# 3.3 Estatísticas dos dados de uma imagem no GEE
terra::summary(imagem_area_interesse)
tamanho_amostra <- terra::ncell(imagem_area_interesse ) * 0.01
amostra_imagem <- terra::spatSample(imagem, tamanho_amostra, as.raster = TRUE)
terra::global(amostra_imagem, fun='min', na.rm=TRUE)
terra::global(amostra_imagem, fun='max', na.rm=TRUE)
terra::global(amostra_imagem, fun='sd', na.rm=TRUE)

# 3.4 Normalizado os valores da imagem
min_bandas <- terra::global(imagem_area_interesse, 'min', na.rm=TRUE)
max_bandas <- terra::global(imagem_area_interesse, 'max', na.rm=TRUE)
# Formula: (x-x_min)/(x_max-x_min)
imagem_normalizada <- terra::scale(imagem_area_interesse, 
                                   center=min_bandas$min, 
                                   scale=max_bandas$max-min_bandas$min)
terra::summary(imagem_normalizada)
terra::global(imagem_normalizada, fun='min', na.rm=TRUE)
terra::global(imagem_normalizada, fun='max', na.rm=TRUE)
terra::global(imagem_normalizada, fun='sd', na.rm=TRUE)

# 3.5 Gerando Histogramas no R
terra::hist(imagem_normalizada)
terra::hist(imagem_area_interesse)
# Se você conhece a biblioteca ggplot, use-a para visualizar um histograma
# mais elaborado.

# 3.6 Exibindo e ajustando o contraste de uma imagem no GEE
# ajuste linear para exibição
# Pode dar erro por ter valores fora do domínio.
# Neste caso, pelo tipo de dado, os valores podem estar além de 255. Precisamos ajustar
# para o intervalo correto para usar a função plotRGB. Note que o parâmetro scale pode ser ajustado
# para o máximo valor possível nas bandas, mas um erro ocorre se os valores dos pixels não forem ajustados
# adequadamente para um valores inferiores a 255.
# Ajuste para 0-1. Cuidado com a função scale quando a imagem possuir grandes dimensões.

# Monocromatico
paleta_cores <- terra::map.pal('reds', 100)

# Realce min-max
terra::summary(imagem_area_interesse[[1]])
# Monocromatico

# Realce min-max
min_saida <- 0
max_saida <- 1

# Banda vermelha ajustada linearmente usando o mínimo e máximo absoluto da imagem.
# Preencha com os valores encontrados anteriormente.
min_bandas
max_bandas
nivel_min <- 0
nivel_max <- 967
imagem_ajustada_min_max <- ((imagem_area_interesse[[1]] - nivel_min)/(nivel_max - nivel_min))*(max_saida - min_saida) + min_saida
imagem_ajustada_min_max[imagem_ajustada_min_max < min_saida] <- min_saida
imagem_ajustada_min_max[imagem_ajustada_min_max > max_saida] <- max_saida

# Banda vermelha ajustada em min-max escolhendo valores minimo e maximo visualmente no histograma
# para evitar outliers.
# Preencha com valores encontrados visualmente pelo histograma. Escolha
# um corte onde os valores estão concentrados.
nivel_min_hist <- 0
nivel_max_hist <- 200

imagem_ajustada_hist = ((imagem_area_interesse[[1]] - nivel_min_hist)/(nivel_max_hist - nivel_min_hist))*(max_saida - min_saida) + min_saida
imagem_ajustada_hist[imagem_ajustada_hist < min_saida] <- min_saida
imagem_ajustada_hist[imagem_ajustada_hist > max_saida] <- max_saida
# Seta o painel.
par(mfrow = c(2, 2))
# Sem nenhum ajuste.
terra::plot(imagem_area_interesse[[1]], 
            col=paleta_cores, type='continuous', 
            smooth=TRUE,
            main='Sem ajuste')

# Min-Max
terra::plot(imagem_ajustada_min_max[[1]], col=paleta_cores, 
            type='continuous', 
            smooth=TRUE,
            main='Min-Max')
# Min-Max pelo histograma.
terra::plot(imagem_ajustada_hist[[1]], 
            col=paleta_cores, 
            type='continuous', 
            smooth=TRUE,
            main='Min-Max pelo histograma')
# Imagem normalizada.
terra::plot(imagem_normalizada[[1]], col=paleta_cores, 
            type='continuous', 
            smooth=TRUE,
            main='Valores normalizados 0-1')
# Reset do plot.
par(mfrow = c(1, 1))

# 3.7 Composição colorida com ajuste de contraste das bandas
tryCatch(terra::plotRGB(imagem_area_interesse, r=1, g=2, b=3, scale=1), 
         error = function(e) e,  
         finally = print("Finalizado"))
imagem_lin_stretch <- terra::stretch(imagem_normalizada, minq=0.1, maxq=0.99)
imagem_lin_stretch
imagem_lin_hist <- terra::stretch(imagem_normalizada, histeq=TRUE, scale=3)
imagem_lin_hist
# Reset do plot.
par(mfrow = c(1, 3))
terra::plotRGB(imagem_normalizada, r=1, g=2, b=3, scale=1)
terra::plotRGB(imagem_lin_stretch, r=1, g=2, b=3)
terra::plotRGB(imagem_lin_hist, r=1, g=2, b=3)
mapview::viewRGB(as(imagem_normalizada, 'Raster'), r=1, g=2, b=3, na.color = 'transparent')
# Reset do plot.
par(mfrow = c(1, 1))


# Falsa cor - Infravermelho Colorido
terra::plotRGB(imagem_lin_stretch, r=4, g=1, b=2)
# Falsa cor - Vegetação
terra::plotRGB(imagem_lin_stretch, r=1, g=4, b=2)


#terra::writeRaster(imagem_normalizada, '~/Downloads/img_normalizada.tif', overwrite=TRUE)
