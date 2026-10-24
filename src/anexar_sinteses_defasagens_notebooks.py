"""Acrescenta sínteses das extensões aos notebooks principais, sem mudar células anteriores."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cell(kind: str, ident: str, content: str):
    result = {"cell_type": kind, "id": ident, "metadata": {},
              "source": content.strip("\n").splitlines(keepends=True)}
    if kind == "code":
        result["execution_count"] = None
        result["outputs"] = []
    return result


def add_to(path: Path, marker: str, md: str, code: str):
    book = json.loads(path.read_text(encoding="utf-8"))
    if any(marker in "".join(c.get("source", [])) for c in book["cells"]):
        print(f"já incorporado: {path.name}")
        return
    book["cells"].append(cell("markdown", marker + "a", md))
    book["cells"].append(cell("code", marker + "b", code))
    path.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"acrescentado: {path.name}")


DLM_MD = """
## 10. Complemento: os dois menores AICs

A auditoria posterior à unificação dos notebooks examinou a primeira e a
segunda escolha de K em cada período e tipologia. **Todos os 29 casos
estimáveis têm ΔAIC inferior a 2**, mas essa proximidade é parcialmente
esperada por construção: os modelos com K e K+1 são aninhados e usam a mesma
amostra, de modo que `AIC(K+1) − AIC(K) ≤ 2` se o candidato K+1 estiver
disponível. Isso **não** equivale à significância da nova defasagem.

A inferência foi recalculada sob os dois K com DK por regra, DK6 e DK12,
Bonferroni para a busca de K e Holm entre tipologias. Sob **DK por regra, nenhuma
rejeição sobrevive aos ajustes em ambas as escolhas**. Veja a
`docs/nota_defasagens_20261024.md` para a metodologia completa. A célula abaixo
exibe as tabelas auditadas produzidas pelos scripts complementares de `src/`.
"""

DLM_CODE = """
from pathlib import Path
import pandas as pd
from IPython.display import display, Markdown

_raiz = Path.cwd().resolve()
if _raiz.name == 'notebooks': _raiz = _raiz.parent
_dir = _raiz / 'outputs/tables/revisao_defasagens_20261024'
_duas = pd.read_csv(_dir / 'dlm_dois_menores_aic.csv', encoding='utf-8-sig')
_dk = pd.read_csv(_dir / 'resumo_inferencia_top2.csv', encoding='utf-8-sig')
display(Markdown('**Defasagens escolhidas pelos dois menores AICs**'))
display(_duas[['periodo','tipologia','K_menor_AIC','K_segundo_AIC','delta_AIC']].round(3))
display(Markdown('**Hipóteses rejeitadas após os ajustes — comparação entre K**'))
display(_dk.pivot(index='posicao_AIC', columns='banda_DK', values='com_ajustes'))
"""

SARIMAX_MD = """
## 9. Complemento: defasagens das exposições climáticas no SARIMAX

Além dos ajustes contemporâneos descritos acima, uma extensão de sensibilidade
comparou, na mesma amostra de treinamento, três blocos por tipologia elegível:
`[0]`, `[0,1]` e `[0,1,3]`. As 16 tipologias são consideradas antes de um filtro
por suporte, posto e condicionamento dos regressores no treino. As exposições
elegíveis entram simultaneamente em **um SARIMAX por UF/período**, com a mesma
ordem temporal do melhor SARIMA por BIC.

Foram 54 aplicações, das quais 53 estimáveis. **Todas as 53 selecionaram
o bloco `[0]` pelo BIC; nenhuma superou o SARIMA pelo BIC**, embora 16 tenham
reduzido o RMSE de teste. O único caso sem exógenas estimáveis foi DF no pré.
O resultado não exclui efeitos em outros horizontes nem corresponde a previsão
ex ante do desastre quando a exposição contemporânea está presente.

O recálculo integral deste complemento está em
`src/sarimax_com_defasagens.py`. O detalhamento metodológico e os diagnósticos
estão em `docs/nota_defasagens_20261024.md`.
"""

SARIMAX_CODE = """
from pathlib import Path
import pandas as pd
from IPython.display import display, Markdown

_raiz = Path.cwd().resolve()
if _raiz.name == 'notebooks': _raiz = _raiz.parent
_dir = _raiz / 'outputs/tables/sarimax_defasagens_20261024'
_sar = pd.read_csv(_dir / 'comparacao.csv', encoding='utf-8-sig')
_validos = _sar.loc[_sar.status.eq('estimado')].copy()
display(Markdown('**Estruturas de defasagens escolhidas pelo BIC**'))
display(_validos.groupby(['periodo','lag_escolhido']).size().rename('aplicacoes').reset_index())
display(Markdown('**SARIMA × SARIMAX defasado — por UF**'))
display(_sar[['periodo','unidade','status','n_tipologias_elegiveis','lag_escolhido',
              'delta_BIC','melhora_rmse_pct']].round(2))
"""


def main():
    add_to(ROOT / "notebooks/02_dlm_painel_aic_bic.ipynb", "c0d24a1", DLM_MD, DLM_CODE)
    add_to(ROOT / "notebooks/03_sarima_sarimax_estadual_nacional.ipynb", "c0d24a2", SARIMAX_MD, SARIMAX_CODE)


if __name__ == "__main__":
    main()
