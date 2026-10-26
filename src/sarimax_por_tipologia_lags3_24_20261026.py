"""Sensibilidade SARIMAX: apenas exógenas climáticas dos meses 3 a K.

Reutiliza a implementação auditada do SARIMAX 0..24, com a única
modificação dos lags climáticos elegíveis. Os resultados ficam em pasta
separada e a execução antiga permanece intacta.

Exemplos:
  python src/sarimax_por_tipologia_lags3_24_20261026.py --fase gerais
  python src/sarimax_por_tipologia_lags3_24_20261026.py --fase consolidar
"""
from __future__ import annotations

import os

os.environ["TCC_SARIMAX_LAG_INICIAL"] = "3"

from sarimax_por_tipologia_k0_24_20261026 import main  # noqa: E402


if __name__ == "__main__":
    main()
