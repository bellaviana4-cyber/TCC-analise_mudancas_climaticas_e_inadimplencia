# Guia de reprodução

O projeto pode ser consultado em três níveis: leitura dos notebooks com saídas salvas, execução dos cadernos sobre as tabelas publicadas e reestimação a partir dos dados.

## 1. Preparar o ambiente

Use **Python 3.10.20**, versão registrada na execução dos modelos. Na raiz de uma cópia local do repositório:

```bash
python -m venv .venv
```

Ative o ambiente conforme o sistema:

```powershell
# Windows / PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Instale as versões registradas:

```bash
python -m pip install -r requirements-reestimacao-exclusoes.lock.txt
```

Os demais arquivos de dependências preservam ambientes de etapas anteriores. Para a execução da versão final, utilize o arquivo acima. A leitura pelo GitHub dispensa instalação. Para abrir os cadernos localmente, utilize um editor com suporte a Jupyter; a interface e o kernel escolhidos podem exigir instalação adicional.

## 2. Consultar as tabelas e executar os notebooks

O [painel agregado](../data/processed/df_tcc_2013_2024.csv) e as [tabelas da versão final](../outputs/tables/modalidades_excluidas_20261104/README.md) estão publicados. Os cinco notebooks organizam essas saídas, sem reestimar automaticamente todos os modelos. Execute-os na ordem do [índice dos notebooks](../notebooks/README.md).

Os nomes `Pré` e `Total` presentes em algumas tabelas correspondem, respectivamente, aos recortes pré-pandemia e completo.

## 3. Reconstruir o painel

Obtenha os arquivos nas [fontes institucionais](../data/README.md) e organize:

- 144 CSVs mensais do SCR em `data/raw/bacen/`, com nomes `scrdata_YYYYMM.csv`.
- O consolidado `BD_Atlas_1991_2024_v1.0_2025.04.14_Consolidado.csv` em `data/raw/atlas_desastres/`.

A preparação do Atlas exige **um único CSV** nessa pasta. O processamento inicial também aceita os caminhos definidos por `TCC_RAW_BACEN` e `TCC_RAW_ATLAS`. Algumas auditorias DLM acessam o caminho local explicitamente; para a reprodução integral, mantenha disponível a estrutura local indicada abaixo.

Execute na raiz:

```bash
python src/01_consolidar_scr.py
python src/02_preparar_atlas.py
python src/03_integrar_bases.py
python src/auditar_base_com_exclusoes.py
```

A auditoria confere cobertura, fórmula da taxa e agregações do primeiro e do último mês, além de registrar os hashes das fontes e do painel. Compare o painel reconstruído ao [manifesto publicado](../outputs/tables/modalidades_excluidas_20261104/manifesto.json): fontes ou serializações diferentes podem alterar seu hash.

**Somente após a preparação e a auditoria**, disponibilize uma cópia idêntica do consolidado em `data/raw/atlas_desastres/atlas.csv`. Esse nome é usado pela classificação COBRADE no DLM. Se precisar repetir `02_preparar_atlas.py`, mantenha apenas o consolidado original na pasta durante essa etapa, pois duas cópias interrompem sua execução.

## 4. Executar as análises

### Descritiva, estacionariedade e Granger

```bash
python src/analise_descritiva_base_corrigida.py
python src/reestimar_com_exclusoes.py granger
python src/reestimar_com_exclusoes.py estacionariedade
python src/verificar_granger_com_exclusoes.py
```

### DLM e sensibilidades

```bash
python src/reestimar_com_exclusoes.py dlm0
python src/reestimar_com_exclusoes.py dlm0_inferencia
python src/reestimar_com_exclusoes.py dlm_aic_bic
python src/reestimar_com_exclusoes.py dlm_top2
python src/reestimar_com_exclusoes.py dlm3
```

### SARIMA/SARIMAX

```bash
python src/executar_reestimacao_sarimax.py
python src/reestimar_com_exclusoes.py comparar_sarimax
python src/verificar_sarimax_com_exclusoes.py
```

O executor percorre as duas grades, as unidades e os recortes, primeiro nos modelos individuais e depois nos gerais. A estimação é computacionalmente mais demorada que a leitura das tabelas. A opção `--workers` controla o número de tarefas simultâneas e tem valor padrão seis.

### Resumo numérico

```bash
python src/gerar_sintese_base_corrigida.py
```

O comando atualiza [resumo_execucao.md](resumo_execucao.md) a partir das tabelas. O README e os guias de leitura são mantidos como documentação editorial e não são sobrescritos.

## 5. Integridade e retomada

Os modelos são vinculados ao hash do painel. Os checkpoints SARIMAX registram também Python, versões das bibliotecas e hashes dos códigos de estimação. Mudanças nesses componentes impedem sua reutilização automática.

Para uma execução em outro ambiente ou com outras fontes, preserve os resultados publicados e os manifestos. Trabalhe em uma cópia separada do projeto, movendo para um local de arquivo os diretórios `sarimax0` e `sarimax3` existentes antes de iniciar resultados novos. Não misture checkpoints de proveniências distintas nem desative a verificação para forçar uma retomada.

O [índice de saídas](../outputs/README.md) distingue as pastas da versão final das etapas históricas. A organização e a documentação podem ser revisadas sem alterar os bytes dos dados, das tabelas e das figuras auditadas.
