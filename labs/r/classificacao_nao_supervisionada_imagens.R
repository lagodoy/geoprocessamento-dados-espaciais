# Preparação dos dados.
dados_raster <- terra::rast('../dados/sr_rad_correct.tif')
dados_raster

# Aritmética raster e manipulação de dados pixel a pixel.
selecao <- dados_raster[[1]] > 100 &
  dados_raster[[2]] > 100 &
  dados_raster[[3]] > 100# &
 # dados_raster[[4]] < 50
imagem_sem_nuvens <- dados_raster
imagem_sem_nuvens[selecao] <- NA

# Visualiza as bandas separadamente
terra::plot(imagem_sem_nuvens)
# Visualiza uma composição colorida.
terra::plotRGB(imagem_sem_nuvens, stretch='hist')
#imagem_reduzida <- terra::resample(imagem_sem_nuvens, c(15,15))
#imagem_sem_nuvens <- terra::clamp(imagem_mux, upper=100, value=FALSE)
# Calculando o NDVI
ndvi <- (dados_raster[[4]] - dados_raster[[1]])/(dados_raster[[1]] + dados_raster[[4]])
names(ndvi) <- 'ndvi'

terra::add(dados_raster) <- ndvi
terra::writeRaster(dados_raster, '../dados/sr_rad_correct_ndvi.tif', datatype='FLT4S', overwrite=TRUE)
paleta <- terra::map.pal("grey", 255)

# Visualiza a banda ndvi.
terra::plot(ndvi, type='continuous', col=paleta)
mapview::mapview(terra::resample(ndvi, y=c(1.5, 1.5)),
                 col.regions=paleta, 
                 na.color='transparent',
                 alpha=1)

# Executando o algoritmo do k-means.


# Calcula a distancia para cada centroide e atribui como cluster a menor.

# Kmeans terra
total_clusters <- 5
dados_raster_normalizados <- terra::scale(dados_raster, center=TRUE, scale=TRUE)
terra::global(dados_raster_normalizados, "mean", na.rm=TRUE)
terra::global(dados_raster_normalizados, "sd", na.rm=TRUE)
resultado_kmeans <- terra::k_means(dados_raster_normalizados, centers=total_clusters, maxcell=10^5)
terra::barplot(resultado_kmeans)

cores_clusters <- lapply(1:total_clusters, 
                         function (n_cluster) {
                            dados_raster_lin <- terra::stretch(dados_raster, minq=0.02, maxq=0.98)
                            dados_cluster <- dados_raster_lin[resultado_kmeans==n_cluster]
                            dados_cluster <- dados_cluster[, 1:3]

                            cluster_cor_media <- colMeans(dados_cluster)
                            cluster_cor_media[1] <- round(cluster_cor_media[1])
                            cluster_cor_media[2] <- round(cluster_cor_media[2])
                            cluster_cor_media[3] <- round(cluster_cor_media[3])
                            print(max(dados_cluster/255))
                            cluster_cor_media_hsv = rgb2hsv (cluster_cor_media[1], cluster_cor_media[2], cluster_cor_media[3])
                            cluster_cor_media_hsv[2] = 1
                            cluster_cor_media_hsv[3] = 0.6
                            string_cor_media = hsv(h=cluster_cor_media_hsv[1], 
                                                   s=cluster_cor_media_hsv[2],
                                                   v=cluster_cor_media_hsv[3])
                            return(string_cor_media)
                          })


cores_clusters <- unlist(cores_clusters)# Para cores aleatórias use: terra::map.pal('ramp', 5).
terra::plot(resultado_kmeans, type='classes', col=cores_clusters)
#terra::plot(resultado_kmeans_manual_final, type='classes', col=cores_clusters)
kmeans_mapview <- terra::resample(resultado_kmeans,  y=c(1.5, 1.5), method='near')
kmeans_mapview <- terra::as.factor(kmeans_mapview) 
kmeans_mapview
terra::levels(kmeans_mapview)

mapview::mapview(kmeans_mapview,
                 col.regions=cores_clusters, 
                 na.color='transparent',
                 method='ngb',
                 alpha=1) 

# Alternativa para execução do k-means manualmente

# Kmeans manual
amostra_kmeans <- terra::spatSample(dados_raster, size=10^5, na.rm=TRUE)
resultado_kmeans_manual <- stats::kmeans(amostra_kmeans, centers = 5)

resultado_kmeans_manual$centers

atribui_cluster <- function(pixel) {
  if(is.na(pixel[1]) == TRUE) return(NA)
  matriz_distancias <- as.matrix(stats::dist(rbind(resultado_kmeans_manual$centers, pixel)))
  num_cluster <- which.min(matriz_distancias[nrow(matriz_distancias),1:(ncol(matriz_distancias)-1)])
  #print(num_cluster)
  return(as.numeric(num_cluster))
}
resultado_kmeans_manual_final <- terra::app(dados_raster, fun=atribui_cluster)
kmeans_mapview_manual <- terra::resample(resultado_kmeans_manual_final,  y=c(1.5, 1.5), method='near')
kmeans_mapview_manual <- terra::as.factor(kmeans_mapview_manual)

mapview::mapview(kmeans_mapview,
                 col.regions=cores_clusters, 
                 na.color='transparent',
                 method='ngb',
                 alpha=1,
                 layer.name='Kmeans - Terra') +
  mapview::mapview(kmeans_mapview_manual,
                   col.regions=cores_clusters, 
                   na.color='transparent',
                   method='ngb',
                   alpha=1,
                   layer.name='Kmeans - Manual')

# Seleção de número de clusters ótimo com a regra do cotovelo.
# Exercicio.