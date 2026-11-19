# Introdução.
# 3.1 Carregamento e preparação dos dados necessários para a prática de laboratório
limites_municipios <- sf::st_read('../dados/OD-2017/Mapas-OD2017/Shape-OD2017/Municipios_2017_region.shp')
sf::st_crs(limites_municipios)$input
limites_municipios <- sf::st_transform(limites_municipios, 31983)
zonas_od <- sf::st_read('../dados/OD-2017/Mapas-OD2017/Shape-OD2017/Zonas_2017_region.shp')
sf::st_crs(zonas_od)$input
zonas_od <- sf::st_transform(zonas_od, 31983)

plot(limites_municipios$geometry)
head(limites_municipios)
sort(limites_municipios$NomeMunici)
limites_municipios_selecionado <- limites_municipios[limites_municipios$NomeMunici=="São Paulo", ]
plot(limites_municipios_selecionado$geometry)

# 3.2. Recortando Zonas de Pesquisa do Município de São Paulo
zonas_od_selecao <- sf::st_intersection(zonas_od, limites_municipios_selecionado)

# 3.3 GRASS “v.clean”
ind_geometrias_erro <- !sf::st_is_valid(zonas_od)
zonas_od$erro <- ind_geometrias_erro
plot(zonas_od[,c('erro', 'geometry')])
zonas_od$motivo_erro <- sf::st_is_valid(zonas_od, reason=TRUE)
zonas_od_corrigidas <- sf::st_make_valid(zonas_od)
ind_geometrias_erro <- !sf::st_is_valid(zonas_od_corrigidas)
zonas_od_corrigidas[ind_geometrias_erro,]

# Um truque que funciona muitas vezes para polígonos é utilizar um buffer de raio 0.
zonas_od_corrigidas_buff <- sf::st_intersection(sf::st_buffer(zonas_od, 0), limites_municipios_selecionado)
ind_geometrias_erro <- !sf::st_is_valid(zonas_od_corrigidas_buff)
zonas_od_corrigidas_buff[ind_geometrias_erro,]

# Faça o clip novamente
zonas_od_selecao <- sf::st_intersection(zonas_od_corrigidas, limites_municipios_selecionado)
plot(zonas_od_selecao$geometry)
# Cheque a tabela de atributos e observe que o intersection carrega algumas zonas indevidas, fora do
# município de São Paulo. Você consegue explicar?


# Com a tabela de atributos, cheque a quantidade de zonas em SP.
sum(zonas_od_corrigidas$NomeMunici=='São Paulo')

# Podemos usar outro approach, checando os polígonos que estão totalmente dentro do município. 
lista_zonas_od_selecionadas <- sf::st_within(zonas_od_corrigidas, limites_municipios_selecionado)
zonas_od_selecao <- zonas_od_corrigidas[lengths(lista_zonas_od_selecionadas) > 0, ]
plot(zonas_od_selecao$geometry)
nrow(zonas_od_selecao)

# Observe que ainda há falhas no processo. Para ajustar, podemos rerduzir ligeiramente
# os polígonos das zonas od, para que fiquem exatamente dentro dos limites do
# município. A função st_buffer pode ser utilizada para isso.
lista_zonas_od_selecionadas <- sf::st_within(sf::st_buffer(zonas_od_corrigidas, -50), limites_municipios_selecionado)
zonas_od_selecao <- zonas_od_corrigidas[lengths(lista_zonas_od_selecionadas) > 0, ]
plot(zonas_od_selecao$geometry)
nrow(zonas_od_selecao)

# Outra opção é utilizar a função st_intersects, com o buffer negativo nas zonas od.
lista_zonas_od_selecionadas <- sf::st_intersects( sf::st_buffer(zonas_od_corrigidas, -50), limites_municipios_selecionado)
zonas_od_selecao <- zonas_od_corrigidas[lengths(lista_zonas_od_selecionadas) > 0, ]
plot(zonas_od_selecao$geometry)
nrow(zonas_od_selecao)

# 3.4 Inserção de dado externo e fazendo cálculo
nomes_colunas <- c('zona', 'nome', 'domicilios', 'familias', 'populacao', 
                   'matriculas_ecolares', 'empregos',	'automoveis_particulares',
                   'viagens_produzidas', 'viagens_atraidas', 'area_ha')

dados_gerais_od <- readxl::read_xlsx('../dados/OD-2017/Tabelas-OD2017/Tab01_OD2017.xlsx', 
                                     col_names=nomes_colunas, skip = 9, 
                                     n_max=nrow(zonas_od_corrigidas))

# Empregos por pessoa. Movimento pendular.
dados_gerais_od$emp_pessoa <- ifelse(dados_gerais_od$populacao != 0, 
                                     dados_gerais_od$empregos/dados_gerais_od$populacao,
                                     0)

# 3.5 Join
names(zonas_od_selecao)
names(dados_gerais_od)
zonas_od_selecao <- merge(zonas_od_selecao, dados_gerais_od, by.x = 'NumeroZona', by.y='zona')
# Outra opção é utilizar um pacote de manipulação de dados, como dplyr.
# zonas_od_selecao <- dplyr::left_join(zonas_od_selecao, dados_gerais_od, by= c('NumeroZona' = 'zona'))

# 3.5 Mapas coropléticos
# Com o mapview
summary(zonas_od_selecao$emp_pessoa)
zonas_od_selecao$classe_emp_pessoa <- ifelse(zonas_od_selecao$emp_pessoa > 1,
                                             '[1,00, 40,00[',
                                             '[0,00, 1,00[')
mapview::mapview(zonas_od_selecao, zcol='classe_emp_pessoa', col.regions=c('red', 'blue'), label=c('emp_pessoa') )
plot(zonas_od_selecao["classe_emp_pessoa"], axes=TRUE, pal = c('red', 'blue'))
plot(zonas_od_selecao["emp_pessoa"], axes=TRUE, pal = c('red', 'blue'), breaks = c(0,1,40))
zonas_od_selecao$classe_emp_pessoa <- cut(zonas_od_selecao$emp_pessoa, breaks=c(0,1,40), right = FALSE)

plot(zonas_od_selecao["classe_emp_pessoa"], axes=TRUE, pal = c('red', 'blue'))
