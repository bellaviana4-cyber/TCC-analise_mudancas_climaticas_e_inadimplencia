# Revisão metodológica DLM — resultados



46 de 48 cenários estimados. Horizonte 0–12; cobertura municipal relativa; seleção J3/J4 por BIC. Resultados históricos preservados em dlm/. Protocolo prévio no commit 1641dfd. Nenhum Granger reestimado e nenhum SARIMAX executado.



## A. Problemas anteriores

K curto selecionado em DLM irrestrito não mede duração. Suporte esparso, 27 clusters nominais com contribuição desigual, ausência de placebos e comparação de recortes sobrepostos limitavam a interpretação. Os testes antigos exigiam o resultado de Onda de Frio; novos testes não exigem significância.



## B. Ajustes implementados

Auditoria UF-mês exata; ocorrências municipais auditáveis; cobertura; classificação por COBRADE; suporte e N_eff; splines; C(h); bandas condicionais; placebos; interação; inferência CR2/WCR/DK; multiverse finita; ponderação fixa; nacional complementar.



## C. Especificação principal

ΔI em pp; C_prop em escala 0–1; K12; spline natural J3/4; UF FE e mês-ano FE; não ponderado; CR1S, CR2+Satterthwaite/HTZ, WCR11 e DK12; BH global48 separado por endpoint/inferência. Não há seleção por p.



## D. Exposição

40339 registros; 40238 chaves municipais únicas; 101 repetições da chave; nenhuma duplicata exata. Cobertura significa municípios com registros, não população/área ou intensidade. Mudança +10 pp de cobertura multiplica coeficiente por 0,1. A/B/C são sensibilidades, com estimandos/unidades distintos. 13310 em Chuvas Intensas exige ressalva nome/código; 14140 não permite isolar onda de calor de baixa umidade.



## E. Defasagens por tipo

K12 compara janelas sem impor curvas iguais. Horizontes ex ante K6 para súbitos e robustez K6 para persistentes. A métrica h90 de massa absoluta é descritiva, não último lag significativo nem duração causal. Perfis sem suporte e estabilidade ficam inconclusivos.



## F. Resultados gerais

{"cluster": {"acumulado": 3, "conjunto": 15}, "boot": {"acumulado": 0, "conjunto": 0}, "dk": {"acumulado": 2, "conjunto": 12}, "cr2": {"acumulado": 0, "conjunto": 0}}



Rejeições BH global48 por inferência (acumulado/conjunto). Concordância nos quatro métodos é necessária, mas insuficiente para robustez substantiva.

Acumulados simultaneamente ajustados em todos os quatro: 0.



## G. Grupos e agregados analíticos

| periodo   | exposicao                         |   acumulado_cluster_estimate |   q_global_acumulado_cluster_p |   q_global_acumulado_boot_p |
|:----------|:----------------------------------|-----------------------------:|-------------------------------:|----------------------------:|
| Total     | Total de desastres                |                    0.0582895 |                       0.722454 |                    0.906442 |
| Total     | Grupo | Climatológico             |                    0.0846342 |                       0.844017 |                    0.906442 |
| Total     | Grupo | Hidrológico               |                   -0.0274861 |                       0.931778 |                    0.961873 |
| Total     | Grupo | Meteorológico             |                    0.0958008 |                       0.844017 |                    0.906442 |
| Total     | Grupo | Outros                    |                    0.0651063 |                       0.667914 |                    0.906442 |
| Total     | Clima/hidrometeorologia           |                    0.0610041 |                       0.802029 |                    0.906442 |
| Total     | Natural não diretamente climático |                    0.0455306 |                       0.760209 |                    0.906442 |
| Total     | Tecnológico/antrópico             |                   -0.0630849 |                       0.931778 |                    0.972726 |
| Pré       | Total de desastres                |                   -0.0738098 |                       0.722454 |                    0.906442 |
| Pré       | Grupo | Climatológico             |                   -0.235715  |                       0.389658 |                    0.906442 |
| Pré       | Grupo | Hidrológico               |                    0.101882  |                       0.861155 |                    0.906442 |
| Pré       | Grupo | Meteorológico             |                    0.103315  |                       0.722454 |                    0.906442 |
| Pré       | Grupo | Outros                    |                   -0.186329  |                       0.844017 |                    0.906442 |
| Pré       | Clima/hidrometeorologia           |                   -0.0862026 |                       0.722454 |                    0.906442 |
| Pré       | Natural não diretamente climático |                   -0.204057  |                       0.844017 |                    0.906442 |
| Pré       | Tecnológico/antrópico             |                    0.993817  |                       0.844017 |                    0.906442 |



## H. Tipologias

| periodo   | exposicao                                   |   acumulado_cluster_estimate |   q_global_acumulado_cluster_p |   q_global_acumulado_boot_p |   q_global_joint_boot_p |
|:----------|:--------------------------------------------|-----------------------------:|-------------------------------:|----------------------------:|------------------------:|
| Total     | Tipologia | Alagamentos                     |                  -0.118033   |                    0.877904    |                    0.906442 |                0.739657 |
| Total     | Tipologia | Chuvas Intensas                 |                  -0.228572   |                    0.667914    |                    0.906442 |                0.761856 |
| Total     | Tipologia | Doenças infecciosas             |                  -0.00405723 |                    1           |                    1        |                0.887481 |
| Total     | Tipologia | Enxurradas                      |                   0.529013   |                    0.667914    |                    0.906442 |                0.826924 |
| Total     | Tipologia | Erosão                          |                   0.074426   |                    0.667914    |                    0.906442 |                1        |
| Total     | Tipologia | Estiagem e Seca                 |                   0.0733559  |                    0.861155    |                    0.906442 |                1        |
| Total     | Tipologia | Granizo                         |                  -0.510787   |                    0.844017    |                    0.906442 |                0.3516   |
| Total     | Tipologia | Incêndio Florestal              |                   0.00558559 |                    1           |                    1        |                0.887481 |
| Total     | Tipologia | Inundações                      |                   0.368403   |                    0.722454    |                    0.906442 |                1        |
| Total     | Tipologia | Movimento de Massa              |                  -1.88774    |                    0.667914    |                    0.906442 |                0.3008   |
| Total     | Tipologia | Onda de Calor e Baixa Umidade   |                   3.44963    |                    7.6206e-08  |                    0.906442 |                0.739657 |
| Total     | Tipologia | Onda de Frio                    |                  -1.66771    |                    6.18376e-07 |                    0.906442 |                0.739657 |
| Total     | Tipologia | Outros                          |                   0.0278552  |                    0.97098     |                    0.999491 |                0.925538 |
| Total     | Tipologia | Rompimento/Colapso de barragens |                  16.6721     |                    0.0452599   |                    0.906442 |                0.545067 |
| Total     | Tipologia | Tornado                         |                   5.80248    |                    0.667914    |                    0.906442 |                0.887481 |
| Total     | Tipologia | Vendavais e Ciclones            |                   0.0869187  |                    0.861598    |                    0.906442 |                0.545067 |
| Pré       | Tipologia | Alagamentos                     |                  -1.66291    |                    0.823953    |                    0.906442 |                0.94884  |
| Pré       | Tipologia | Chuvas Intensas                 |                  -0.301363   |                    0.667914    |                    0.906442 |                1        |
| Pré       | Tipologia | Doenças infecciosas             |                  -0.136481   |                    0.861598    |                    0.906442 |                0.8859   |
| Pré       | Tipologia | Enxurradas                      |                   0.189717   |                    0.861155    |                    0.906442 |                0.875148 |
| Pré       | Tipologia | Erosão                          |                  -2.07095    |                    0.667914    |                    0.906442 |                0.60672  |
| Pré       | Tipologia | Estiagem e Seca                 |                  -0.25052    |                    0.545238    |                    0.906442 |                0.739657 |
| Pré       | Tipologia | Granizo                         |                   0.475354   |                    0.931778    |                    0.961873 |                0.766629 |
| Pré       | Tipologia | Incêndio Florestal              |                  -0.594424   |                    0.667914    |                    0.906442 |                0.766629 |
| Pré       | Tipologia | Inundações                      |                   0.97728    |                    0.667914    |                    0.906442 |                0.887481 |
| Pré       | Tipologia | Movimento de Massa              |                  -0.480768   |                    0.871176    |                    0.906442 |                0.739657 |
| Pré       | Tipologia | Onda de Frio                    |                  -0.431967   |                    0.844017    |                    0.906442 |                0.739657 |
| Pré       | Tipologia | Outros                          |                   0.166999   |                    0.97098     |                    0.972726 |                1        |
| Pré       | Tipologia | Tornado                         |                   5.05841    |                    0.722454    |                    0.960738 |                0.761856 |
| Pré       | Tipologia | Vendavais e Ciclones            |                   0.0611479  |                    0.844017    |                    0.906442 |                0.739657 |



## I. Onda de Frio

Total: C12=-1.66771 pp/unidade; cluster p=2.57657e-08; WCR p=0.2734; DK p=1.28583e-05; CR2 p=0.228893, df=1.099; N_eff cobertura=1.509; top1=80.6%; top2=91.3%.

Pré: C12=-0.431967 pp/unidade; cluster p=0.528295; WCR p=0.6535; DK p=0.633749; CR2 p=0.774389, df=1.128; N_eff cobertura=1.509; top1=79.8%; top2=95.8%.



**Classificação do sinal positivo pré anterior: não robusto.** A versão principal revisada não o reproduz; suporte fortemente concentrado. Não comparar magnitudes brutas C_prop e log1p(A). Rastreio A/K3 mostra o impacto isolado de ampliar inferência na medida histórica. As retiradas de UFs incluem cenários que perdem suporte mínimo e não devem ser promovidos a especificações principais.



| periodo   | retirada   | status                          |   n_eff |   acumulado_cluster_estimate |   acumulado_cluster_low |   acumulado_cluster_high |   acumulado_cluster_p |
|:----------|:-----------|:--------------------------------|--------:|-----------------------------:|------------------------:|-------------------------:|----------------------:|
| Total     | AC         | exposição altamente concentrada | 1.50868 |                  -1.70289    |               -2.1533   |                -1.25249  |           3.8317e-08  |
| Total     | AL         | exposição altamente concentrada | 1.50868 |                  -1.60355    |               -2.03312  |                -1.17398  |           4.81467e-08 |
| Total     | AM         | exposição altamente concentrada | 1.50868 |                  -1.64116    |               -2.08439  |                -1.19792  |           5.56358e-08 |
| Total     | AP         | exposição altamente concentrada | 1.50868 |                  -1.6568     |               -2.11342  |                -1.20019  |           7.95543e-08 |
| Total     | BA         | exposição altamente concentrada | 1.50868 |                  -1.64033    |               -2.08789  |                -1.19276  |           6.6683e-08  |
| Total     | CE         | exposição altamente concentrada | 1.50868 |                  -1.62042    |               -2.05924  |                -1.18161  |           5.83599e-08 |
| Total     | DF         | exposição altamente concentrada | 1.50868 |                  -1.66825    |               -2.12218  |                -1.21433  |           6.34885e-08 |
| Total     | ES         | exposição altamente concentrada | 1.45791 |                  -1.70494    |               -2.15505  |                -1.25483  |           3.70659e-08 |
| Total     | GO         | exposição altamente concentrada | 1.50868 |                  -1.72043    |               -2.16342  |                -1.27743  |           2.35807e-08 |
| Total     | MA         | exposição altamente concentrada | 1.49939 |                  -1.66308    |               -2.11763  |                -1.20853  |           6.87262e-08 |
| Total     | MG         | exposição altamente concentrada | 1.43289 |                  -1.6815     |               -2.11203  |                -1.25096  |           2.12704e-08 |
| Total     | MS         | exposição altamente concentrada | 2.89456 |                  -7.04554    |              -14.5173   |                 0.426209 |           0.0634783   |
| Total     | MT         | exposição altamente concentrada | 1.48033 |                  -1.71733    |               -2.13351  |                -1.30115  |           7.67148e-09 |
| Total     | PA         | exposição altamente concentrada | 1.50868 |                  -1.65958    |               -2.11517  |                -1.20399  |           7.42574e-08 |
| Total     | PB         | exposição altamente concentrada | 1.50868 |                  -1.62386    |               -2.06719  |                -1.18052  |           6.73857e-08 |
| Total     | PE         | exposição altamente concentrada | 1.50868 |                  -1.59359    |               -2.01288  |                -1.17431  |           3.4864e-08  |
| Total     | PI         | exposição altamente concentrada | 1.50868 |                  -1.6186     |               -2.05951  |                -1.17769  |           6.47649e-08 |
| Total     | PR         | exposição altamente concentrada | 1.49858 |                  -1.70305    |               -2.14391  |                -1.2622   |           2.597e-08   |
| Total     | RJ         | exposição altamente concentrada | 1.44448 |                  -1.64668    |               -2.11621  |                -1.17715  |           1.43644e-07 |
| Total     | RN         | exposição altamente concentrada | 1.50868 |                  -1.63702    |               -2.0831   |                -1.19094  |           6.5163e-08  |
| Total     | RO         | exposição altamente concentrada | 1.50868 |                  -1.71305    |               -2.16144  |                -1.26467  |           3.17511e-08 |
| Total     | RR         | exposição altamente concentrada | 1.50868 |                  -1.64295    |               -2.09697  |                -1.18892  |           8.34181e-08 |
| Total     | RS         | exposição altamente concentrada | 1.49653 |                  -1.70867    |               -2.15292  |                -1.26442  |           2.8121e-08  |
| Total     | SC         | exposição altamente concentrada | 1.2247  |                  -1.64991    |               -2.04233  |                -1.25749  |           5.38393e-09 |
| Total     | SE         | exposição altamente concentrada | 1.50868 |                  -1.641      |               -2.09107  |                -1.19093  |           7.30412e-08 |
| Total     | SP         | exposição altamente concentrada | 1.50242 |                  -1.68953    |               -2.13814  |                -1.24092  |           4.10877e-08 |
| Total     | TO         | exposição altamente concentrada | 1.50868 |                  -1.72861    |               -2.17079  |                -1.28643  |           2.09047e-08 |
| Total     | MS + SC    | exposição altamente concentrada | 4.80437 |                 -12.948      |              -42.1005   |                16.2045   |           0.368433    |
| Pré       | AC         | exposição altamente concentrada | 1.50875 |                  -0.483106   |               -1.90338  |                 0.93717  |           0.490052    |
| Pré       | AL         | exposição altamente concentrada | 1.50875 |                  -0.287219   |               -1.68973  |                 1.11529  |           0.676796    |
| Pré       | AM         | exposição altamente concentrada | 1.50875 |                  -0.557873   |               -2.01647  |                 0.900725 |           0.438268    |
| Pré       | AP         | exposição altamente concentrada | 1.50875 |                  -0.45526    |               -1.86782  |                 0.957303 |           0.512909    |
| Pré       | BA         | exposição altamente concentrada | 1.50875 |                  -0.476156   |               -1.92289  |                 0.970574 |           0.504095    |
| Pré       | CE         | exposição altamente concentrada | 1.50875 |                  -0.462745   |               -1.91804  |                 0.992545 |           0.518525    |
| Pré       | DF         | exposição altamente concentrada | 1.50875 |                  -0.427598   |               -1.86016  |                 1.00497  |           0.544282    |
| Pré       | ES         | exposição altamente concentrada | 1.42473 |                  -0.648794   |               -2.01551  |                 0.71792  |           0.337597    |
| Pré       | GO         | exposição altamente concentrada | 1.50875 |                  -0.466368   |               -1.90588  |                 0.973139 |           0.510728    |
| Pré       | MA         | exposição altamente concentrada | 1.50875 |                  -0.40898    |               -1.83295  |                 1.01499  |           0.559482    |
| Pré       | MG         | exposição altamente concentrada | 1.49293 |                  -0.504413   |               -1.94453  |                 0.935701 |           0.477374    |
| Pré       | MS         | exposição altamente concentrada | 1.54173 |                  10.3198     |               -2.9378   |                23.5773   |           0.121461    |
| Pré       | MT         | exposição altamente concentrada | 1.50875 |                  -0.548585   |               -2.01148  |                 0.91431  |           0.447162    |
| Pré       | PA         | exposição altamente concentrada | 1.50875 |                  -0.528218   |               -1.93158  |                 0.875145 |           0.445493    |
| Pré       | PB         | exposição altamente concentrada | 1.50875 |                  -0.370326   |               -1.77035  |                 1.0297   |           0.590734    |
| Pré       | PE         | exposição altamente concentrada | 1.50875 |                  -0.361779   |               -1.82206  |                 1.0985   |           0.614358    |
| Pré       | PI         | exposição altamente concentrada | 1.50875 |                  -0.254453   |               -1.62669  |                 1.11778  |           0.705763    |
| Pré       | PR         | exposição altamente concentrada | 1.50875 |                  -0.41146    |               -1.85324  |                 1.03032  |           0.561967    |
| Pré       | RJ         | exposição altamente concentrada | 1.50875 |                  -0.545715   |               -2.01165  |                 0.920215 |           0.450443    |
| Pré       | RN         | exposição altamente concentrada | 1.50875 |                  -0.44098    |               -1.9003   |                 1.01834  |           0.539344    |
| Pré       | RO         | exposição altamente concentrada | 1.50875 |                  -0.441704   |               -1.8362   |                 0.952796 |           0.520127    |
| Pré       | RR         | exposição altamente concentrada | 1.50875 |                   0.00409261 |               -0.968041 |                 0.976226 |           0.993151    |
| Pré       | RS         | exposição altamente concentrada | 1.49516 |                  -0.412596   |               -1.88355  |                 1.05836  |           0.56864     |
| Pré       | SC         | exposição altamente concentrada | 1.10692 |                  -0.589873   |               -2.10725  |                 0.927505 |           0.430886    |
| Pré       | SE         | exposição altamente concentrada | 1.50875 |                  -0.388279   |               -1.80737  |                 1.03081  |           0.578105    |
| Pré       | SP         | exposição altamente concentrada | 1.49827 |                  -0.430559   |               -1.88416  |                 1.02304  |           0.54734     |
| Pré       | TO         | exposição altamente concentrada | 1.50875 |                  -0.56484    |               -1.97433  |                 0.844655 |           0.416986    |
| Pré       | MS + SC    | não estimável                   | 1.98919 |                  -6.39077    |              -85.9852   |                73.2037   |           0.86977     |



## J. Placebos

Rejeições BH leads: cluster=15; WCR=0; CR2=0. Placebos não comprovam exogeneidade quando não rejeitam.



## K. Pré versus pós

| exposicao                                   |   pre_cluster_estimate |   pos_cluster_estimate |   diferenca_cluster_estimate |   q_global_joint_boot_p |
|:--------------------------------------------|-----------------------:|-----------------------:|-----------------------------:|------------------------:|
| Total de desastres                          |            0.0218897   |              0.0699492 |                   0.0480595  |                0.941217 |
| Grupo | Climatológico                       |           -0.000492208 |              0.122114  |                   0.122607   |                0.92736  |
| Grupo | Hidrológico                         |           -0.0238047   |             -0.0302903 |                  -0.00648555 |                0.92736  |
| Grupo | Meteorológico                       |            0.159783    |              0.0038167 |                  -0.155966   |                0.92736  |
| Grupo | Outros                              |           -0.166201    |              0.0848835 |                   0.251085   |                0.92736  |
| Tipologia | Alagamentos                     |           -1.41694     |              0.0303773 |                   1.44732    |                0.941217 |
| Tipologia | Chuvas Intensas                 |           -0.389345    |             -0.201869  |                   0.187476   |                0.941217 |
| Tipologia | Doenças infecciosas             |           -0.112975    |              9.13089   |                   9.24386    |                0.92736  |
| Tipologia | Enxurradas                      |            0.545483    |              0.320207  |                  -0.225276   |                0.92736  |
| Tipologia | Erosão                          |           -2.23721     |              0.095028  |                   2.33223    |                0.6576   |
| Tipologia | Estiagem e Seca                 |            0.0329989   |              0.10663   |                   0.0736313  |                0.92736  |
| Tipologia | Granizo                         |            0.750631    |             -0.62873   |                  -1.37936    |                0.92736  |
| Tipologia | Incêndio Florestal              |           -0.45142     |              0.0282354 |                   0.479655   |                0.92736  |
| Tipologia | Inundações                      |            0.325492    |              0.3816    |                   0.0561078  |                0.92736  |
| Tipologia | Movimento de Massa              |           -0.942933    |             -2.83416   |                  -1.89123    |                0.92736  |
| Tipologia | Onda de Calor e Baixa Umidade   |           -1.31204     |              3.5364    |                   4.84844    |                0.92736  |
| Tipologia | Onda de Frio                    |           -2.53031     |             -1.6604    |                   0.869914   |                0.92736  |
| Tipologia | Outros                          |            0.401659    |              0.0187675 |                  -0.382892   |                0.9642   |
| Tipologia | Rompimento/Colapso de barragens |           21.7072      |            -18.7547    |                 -40.4619     |                0.92736  |
| Tipologia | Tornado                         |            5.08615     |              7.43041   |                   2.34426    |                0.92736  |
| Tipologia | Vendavais e Ciclones            |            0.10577     |              0.0110391 |                  -0.0947311  |                0.92736  |
| Clima/hidrometeorologia                     |            0.0144219   |              0.0714972 |                   0.0570753  |                0.92736  |
| Natural não diretamente climático           |           -0.14552     |              0.06134   |                   0.20686    |                0.92736  |
| Tecnológico/antrópico                       |            1.25037     |             -0.0994469 |                  -1.34982    |                0.92736  |

Pós é fev/2020 em diante. A hipótese conjunta de γ e a diferença acumulada são perguntas diferentes. Janela da pandemia exclui respostas, não necessariamente todas exposições defasadas.



## L. Poucos clusters

CR2 usa df Satterthwaite do contraste, não G−1 nem N_eff. Concentração pode produzir df efetivo muito baixo e grande discordância. Wild bootstrap não corrige automaticamente poucos estados informativos. Bandas baseadas em cluster são aproximações condicionais e não certificam categorias concentradas.



## M. Robustez

Todas as sensibilidades estão em multiverse.csv; inferência não foi selecionada pelo menor p. CD é diagnóstico aproximado: FE temporais induzem restrições transversais; não usar p CD como certificação. Autocorrelação permanece limitação em alguns cenários.



## N. Painel versus nacional

Há 4 efeitos acumulados diretos e 10 perfis conjuntos após BH/HAC nesta análise complementar. Os 4 acumulados são Inundações, Onda de Calor/Baixa Umidade e Onda de Frio no total, e o agregado Natural não diretamente climático no pré. Seus diagnósticos Ljung–Box12 não rejeitam; isso não prova adequação, elimina confundimento ou certifica estabilidade. Não apagar essas associações por não coincidirem com o painel.

| periodo   | exposicao                                   |   p_proprio |   acumulado_direto |   q_global_p_acumulado |   q_global_p_conjunto |   ljungbox12_p |
|:----------|:--------------------------------------------|------------:|-------------------:|-----------------------:|----------------------:|---------------:|
| Total     | Total de desastres                          |           1 |          0.0704387 |             0.995853   |           0.860245    |      0.600464  |
| Total     | Grupo | Climatológico                       |           1 |         -0.588927  |             0.884653   |           0.860245    |      0.64666   |
| Total     | Grupo | Hidrológico                         |           1 |          0.586225  |             0.884653   |           0.607785    |      0.533854  |
| Total     | Grupo | Meteorológico                       |           1 |         -6.86076   |             0.376924   |           0.118016    |      0.722888  |
| Total     | Grupo | Outros                              |           1 |         -5.96263   |             0.897162   |           0.607785    |      0.498622  |
| Total     | Tipologia | Alagamentos                     |           1 |         19.6904    |             0.220118   |           0.11348     |      0.50243   |
| Total     | Tipologia | Chuvas Intensas                 |           1 |          0.260794  |             0.958211   |           0.332676    |      0.5025    |
| Total     | Tipologia | Doenças infecciosas             |           1 |         -7.67425   |             0.767078   |           0.860245    |      0.532316  |
| Total     | Tipologia | Enxurradas                      |           1 |         -3.35787   |             0.884653   |           0.860496    |      0.558237  |
| Total     | Tipologia | Erosão                          |           1 |         14.7486    |             0.884653   |           0.67145     |      0.493923  |
| Total     | Tipologia | Estiagem e Seca                 |           1 |         -0.424553  |             0.958211   |           0.539613    |      0.690898  |
| Total     | Tipologia | Granizo                         |           1 |         16.2609    |             0.528674   |           0.860245    |      0.507556  |
| Total     | Tipologia | Incêndio Florestal              |           1 |          2.33729   |             0.528674   |           0.114586    |      0.549733  |
| Total     | Tipologia | Inundações                      |           1 |         11.4503    |             0.0021032  |           0.000987641 |      0.544422  |
| Total     | Tipologia | Movimento de Massa              |           1 |         25.0894    |             0.253218   |           0.193076    |      0.63936   |
| Total     | Tipologia | Onda de Calor e Baixa Umidade   |           1 |       -432.965     |             0.0021032  |           0.00294209  |      0.907237  |
| Total     | Tipologia | Onda de Frio                    |           1 |         35.0925    |             0.00175195 |           0.0019715   |      0.543695  |
| Total     | Tipologia | Outros                          |           1 |          6.19504   |             0.950886   |           0.48741     |      0.512801  |
| Total     | Tipologia | Rompimento/Colapso de barragens |           1 |       -117.509     |             0.767078   |           0.607785    |      0.647196  |
| Total     | Tipologia | Tornado                         |           1 |        -64.6118    |             0.884653   |           0.860496    |      0.635201  |
| Total     | Tipologia | Vendavais e Ciclones            |           1 |        -14.5904    |             0.0597736  |           0.0021108   |      0.852734  |
| Total     | Clima/hidrometeorologia                     |           1 |          0.0634784 |             0.995853   |           0.860245    |      0.599554  |
| Total     | Natural não diretamente climático           |           1 |          7.44093   |             0.884653   |           0.952757    |      0.554453  |
| Total     | Tecnológico/antrópico                       |           1 |         -0.1941    |             1          |           0.237078    |      0.524895  |
| Pré       | Total de desastres                          |           0 |         -5.01098   |             0.0559904  |           0.11348     |      0.31004   |
| Pré       | Grupo | Climatológico                       |           0 |         -3.82638   |             0.466369   |           0.0112501   |      0.541722  |
| Pré       | Grupo | Hidrológico                         |           0 |         -8.53358   |             0.188908   |           0.257613    |      0.239898  |
| Pré       | Grupo | Meteorológico                       |           0 |         -6.2702    |             0.884653   |           0.860496    |      0.0734575 |
| Pré       | Grupo | Outros                              |           0 |        -55.6693    |             0.173987   |           0.273869    |      0.138621  |
| Pré       | Tipologia | Alagamentos                     |           0 |        -56.3696    |             0.220118   |           0.22009     |      0.159537  |
| Pré       | Tipologia | Chuvas Intensas                 |           0 |        -17.7181    |             0.188908   |           0.298006    |      0.323406  |
| Pré       | Tipologia | Doenças infecciosas             |           0 |        -21.3946    |             0.312512   |           0.607785    |      0.261093  |
| Pré       | Tipologia | Enxurradas                      |           0 |        -21.9468    |             0.1278     |           0.1598      |      0.0795128 |
| Pré       | Tipologia | Erosão                          |           0 |        -97.2247    |             0.188908   |           0.11348     |      0.146765  |
| Pré       | Tipologia | Estiagem e Seca                 |           0 |         -4.58969   |             0.339545   |           0.00780703  |      0.501944  |
| Pré       | Tipologia | Granizo                         |           0 |         32.6652    |             0.253218   |           0.314285    |      0.204623  |
| Pré       | Tipologia | Incêndio Florestal              |           0 |         15.6405    |             0.767078   |           0.000987641 |      0.580426  |
| Pré       | Tipologia | Inundações                      |           0 |        -14.0029    |             0.767078   |           0.607785    |      0.0895968 |
| Pré       | Tipologia | Movimento de Massa              |           0 |        -76.2124    |             0.173987   |           0.104934    |      0.164344  |
| Pré       | Tipologia | Onda de Frio                    |           0 |        -82.1774    |             0.583277   |           0.860245    |      0.215453  |
| Pré       | Tipologia | Outros                          |           0 |         52.5643    |             0.220118   |           0.0103743   |      0.170056  |
| Pré       | Tipologia | Tornado                         |           0 |         95.604     |             0.897162   |           0.860496    |      0.0919717 |
| Pré       | Tipologia | Vendavais e Ciclones            |           0 |        -21.7281    |             0.167426   |           0.299676    |      0.106195  |
| Pré       | Clima/hidrometeorologia                     |           0 |         -5.13376   |             0.0597736  |           0.114586    |      0.335289  |
| Pré       | Natural não diretamente climático           |           0 |        -47.6437    |             0.0021032  |           0.0021108   |      0.184712  |
| Pré       | Tecnológico/antrópico                       |           0 |         50.2762    |             0.1278     |           0.0089001   |      0.167157  |

O painel remove variação nacional comum; o nacional mantém essa variação e é vulnerável a confundimento agregado. Soma direta do componente exposição não é multiplicador total em modelo com lags próprios; recursão dinâmica é descritiva, sem bandas conjuntas nesta extensão.



## O. Granger

A etapa15 encontrou Granizo total exploratório sensível a HAC/especificação. Granger usa séries nacionais diferentemente transformadas e testa informação precedente. DLM estima associação relativa UF-mês. Não exigir concordância entre métodos.



## P. Implicações para SARIMAX

Não executado. Usar futura validação temporal fora da amostra, controles e regressoras selecionados por mecanismo/disponibilidade e não pelo menor p nesta revisão. Evitar selecionar Onda de Frio por resultado histórico.



## Q. Atualização do TCC

1. Dados: atualizar cobertura 2013–2024, contagem e taxonomia nome/código.

2. Metodologia DLM: ΔI, exposição territorial, estimando TWFE e ponderado, spline K12, contrastes/covariâncias e bandas.

3. Inferência: CR2/Satterthwaite/HTZ, WCR11, DK, famílias BH48/24 e limitações de suporte.

4. Períodos: recortes sobrepostos descritivos; interação formal e definição de Pós.

5. Resultados: substituir afirmação de Onda de Frio robusta; reportar divergências e leave-outs.

6. Discussão: não atribuir contagens ou associações à mudança climática antropogênica; exposição registrada não mede causalidade climática.

7. Nacional: razão de somas, dinâmica própria, soma direta versus resposta recursiva; limitações de amostra/diagnósticos.

8. Conclusão: ausência de perfil robusto não demonstra ausência de impactos; manter resultados não estimáveis/inconclusivos.



## Estacionariedade em painel

| periodo   | serie              | deterministico   |   lags |     CIPS |         p |   N |   T |
|:----------|:-------------------|:-----------------|-------:|---------:|----------:|----:|----:|
| Total     | taxa_inadimplencia | drift            |      1 | -2.25405 | 0.0281247 |  27 | 144 |
| Total     | taxa_inadimplencia | drift            |      2 | -2.29169 | 0.0177227 |  27 | 144 |
| Total     | taxa_inadimplencia | trend            |      1 | -1.88218 | 0.1       |  27 | 144 |
| Total     | taxa_inadimplencia | trend            |      2 | -1.78322 | 0.1       |  27 | 144 |
| Total     | delta              | drift            |      1 | -6.1722  | 0.01      |  27 | 143 |
| Total     | delta              | drift            |      2 | -5.64521 | 0.01      |  27 | 143 |
| Pré       | taxa_inadimplencia | drift            |      1 | -2.14855 | 0.0632568 |  27 |  85 |
| Pré       | taxa_inadimplencia | drift            |      2 | -2.04847 | 0.1       |  27 |  85 |
| Pré       | taxa_inadimplencia | trend            |      1 | -2.35422 | 0.1       |  27 |  85 |
| Pré       | taxa_inadimplencia | trend            |      2 | -2.27508 | 0.1       |  27 |  85 |
| Pré       | delta              | drift            |      1 | -5.70053 | 0.01      |  27 |  84 |
| Pré       | delta              | drift            |      2 | -4.98747 | 0.01      |  27 |  84 |



## Limitações adicionais

Exposição retrospectiva não garante informação disponível em tempo real; cadastro municipal não mede área/população; modelagem linear homogênea por UF, splines podem suavizar reversões abruptas; seleção de J e amostras pequenas aumentam incerteza. ICs e bandas não incorporam incerteza de mensuração da exposição. Rejeição conjunta pode ocorrer com soma próxima de zero.