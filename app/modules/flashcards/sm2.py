from datetime import datetime, timedelta, timezone
from typing import Tuple


def calcular_sm2(qualidade: int, repeticoes: int, fator_facilidade: float, intervalo_atual: int) -> Tuple[int, float, int, datetime]:
    """
    Implementação canônica do algoritmo SuperMemo-2 (SM-2):
    
    Parâmetros:
    - qualidade: Avaliação do usuário de 0 a 5
        * 1 ou 2: Errei (recomeça)
        * 3: Difícil / Lembrou com esforço
        * 4: Bom / Resposta correta com pouca hesitação
        * 5: Fácil / Memorização perfeita instantânea
    - repeticoes: Número de vezes consecutivas lembradas com sucesso
    - fator_facilidade: Multiplicador de facilidade (E-Factor, mín 1.3)
    - intervalo_atual: Intervalo anterior em dias

    Retorna:
    - (novas_repeticoes, novo_fator_facilidade, novo_intervalo_dias, data_proxima_revisao)
    """
    # 1. Ajuste do fator de facilidade (EF)
    # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    novo_ef = fator_facilidade + (0.1 - (5 - qualidade) * (0.08 + (5 - qualidade) * 0.02))
    if novo_ef < 1.3:
        novo_ef = 1.3

    # 2. Se errou (qualidade < 3), o ciclo é reiniciado
    if qualidade < 3:
        novas_reps = 0
        novo_intervalo = 1
    else:
        # Se acertou
        if repeticoes == 0:
            novo_intervalo = 1
        elif repeticoes == 1:
            novo_intervalo = 6
        else:
            novo_intervalo = int(round(intervalo_atual * novo_ef))
        novas_reps = repeticoes + 1

    proxima_data = datetime.now(timezone.utc) + timedelta(days=novo_intervalo)
    return novas_reps, round(novo_ef, 2), novo_intervalo, proxima_data
