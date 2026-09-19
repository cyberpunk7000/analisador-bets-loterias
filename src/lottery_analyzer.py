"""
Analisador estatístico de Mega Sena e Lotofácil.
Usa dados históricos (CSV ou JSON) e gera estatísticas + sugestões.
"""

import pandas as pd
import numpy as np
from collections import Counter
from typing import List, Dict, Tuple
import random


# ---------- Carregamento ----------

def load_mega_sena(filepath: str) -> pd.DataFrame:
    """
    Espera CSV com colunas: concurso, data, n1, n2, n3, n4, n5, n6
    (números já ordenados ou não)
    """
    df = pd.read_csv(filepath)
    num_cols = [c for c in df.columns if c.startswith("n") or c.lower().startswith("bola") or c.isdigit()]
    if not num_cols:
        # tenta detectar colunas numéricas após concurso/data
        num_cols = df.columns[2:8].tolist()
    df["numeros"] = df[num_cols].apply(lambda row: sorted([int(x) for x in row if pd.notna(x)]), axis=1)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    return df


def load_lotofacil(filepath: str) -> pd.DataFrame:
    """
    Espera CSV com colunas: concurso, data, n1 ... n15
    """
    df = pd.read_csv(filepath)
    num_cols = [c for c in df.columns if c.startswith("n") or c.lower().startswith("bola")]
    if not num_cols:
        num_cols = df.columns[2:17].tolist()
    df["numeros"] = df[num_cols].apply(lambda row: sorted([int(x) for x in row if pd.notna(x)]), axis=1)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    return df


# ---------- Estatísticas ----------

def frequency_analysis(df: pd.DataFrame, max_num: int) -> pd.DataFrame:
    """Conta frequência e probabilidade empírica de cada número."""
    all_nums = []
    for nums in df["numeros"]:
        all_nums.extend(nums)
    counter = Counter(all_nums)
    total_sorteios = len(df)
    # Em cada sorteio saem N números (6 na Mega, 15 na Lotofácil)
    # Probabilidade empírica = vezes que saiu / total de sorteios
    freq = pd.DataFrame({
        "numero": list(range(1, max_num + 1)),
        "frequencia": [counter.get(i, 0) for i in range(1, max_num + 1)]
    })
    freq["probabilidade_%"] = (freq["frequencia"] / total_sorteios * 100).round(2)
    freq["percentual_relativo"] = (freq["frequencia"] / freq["frequencia"].sum() * 100).round(2)
    # Probabilidade teórica (uniforme)
    if max_num == 60:  # Mega Sena - 6 de 60
        teorica = (6 / 60) * 100
    else:  # Lotofácil - 15 de 25
        teorica = (15 / 25) * 100
    freq["prob_teorica_%"] = round(teorica, 2)
    freq["desvio_vs_teorica"] = (freq["probabilidade_%"] - teorica).round(2)
    freq = freq.sort_values("frequencia", ascending=False).reset_index(drop=True)
    return freq


def delay_analysis(df: pd.DataFrame, max_num: int) -> pd.DataFrame:
    """Calcula quantos concursos cada número está atrasado."""
    last_seen = {i: -1 for i in range(1, max_num + 1)}
    for idx, row in df.iterrows():
        for n in row["numeros"]:
            last_seen[n] = idx
    total = len(df)
    delays = []
    for n in range(1, max_num + 1):
        if last_seen[n] == -1:
            delay = total
        else:
            delay = total - 1 - last_seen[n]
        delays.append({"numero": n, "atraso": delay})
    return pd.DataFrame(delays).sort_values("atraso", ascending=False).reset_index(drop=True)


def even_odd_stats(df: pd.DataFrame) -> Dict:
    even_counts = []
    for nums in df["numeros"]:
        even = sum(1 for n in nums if n % 2 == 0)
        even_counts.append(even)
    return {
        "media_pares": round(np.mean(even_counts), 2),
        "distribuicao": Counter(even_counts)
    }


def sum_stats(df: pd.DataFrame) -> Dict:
    sums = [sum(nums) for nums in df["numeros"]]
    return {
        "media": round(np.mean(sums), 1),
        "mediana": round(np.median(sums), 1),
        "min": min(sums),
        "max": max(sums),
        "desvio": round(np.std(sums), 1)
    }


# ---------- Sugestões (apenas estatísticas, sem garantia) ----------

def suggest_numbers(
    freq_df: pd.DataFrame,
    delay_df: pd.DataFrame,
    qty: int,
    strategy: str = "misto"
) -> List[int]:
    """
    Gera sugestão de números.
    Estratégias:
      - quentes: mais frequentes
      - frios: menos frequentes
      - atrasados: maior atraso
      - misto: mistura de quentes + atrasados
    """
    if strategy == "quentes":
        return sorted(freq_df.head(qty)["numero"].tolist())
    elif strategy == "frios":
        return sorted(freq_df.tail(qty)["numero"].tolist())
    elif strategy == "atrasados":
        return sorted(delay_df.head(qty)["numero"].tolist())
    else:  # misto
        quentes = freq_df.head(qty // 2 + 1)["numero"].tolist()
        atrasados = delay_df.head(qty // 2 + 1)["numero"].tolist()
        combinado = list(dict.fromkeys(quentes + atrasados))  # remove duplicados mantendo ordem
        while len(combinado) < qty:
            # completa com números aleatórios restantes
            remaining = [n for n in range(1, 61 if qty <= 6 else 26) if n not in combinado]
            combinado.append(random.choice(remaining))
        return sorted(combinado[:qty])


def generate_games(
    freq_df: pd.DataFrame,
    delay_df: pd.DataFrame,
    qty_numbers: int,
    num_games: int = 5,
    strategy: str = "misto"
) -> List[List[int]]:
    games = []
    for _ in range(num_games):
        game = suggest_numbers(freq_df, delay_df, qty_numbers, strategy)
        # pequena variação para não repetir o mesmo jogo
        if game in games:
            game = sorted(random.sample(range(1, 61 if qty_numbers == 6 else 26), qty_numbers))
        games.append(game)
    return games
