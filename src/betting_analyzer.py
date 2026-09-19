"""
Analisador de apostas (esportes + crash) para 7K Bet e 7Games.
Espera um CSV com colunas mínimas:
  data, hora, plataforma, tipo, valor_apostado, valor_retorno, resultado
"""

import pandas as pd
import numpy as np
from datetime import datetime


def load_bets(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["data"])
    if "hora" in df.columns:
        # tenta combinar data + hora
        try:
            df["datetime"] = pd.to_datetime(
                df["data"].astype(str) + " " + df["hora"].astype(str),
                errors="coerce"
            )
        except Exception:
            df["datetime"] = df["data"]
    else:
        df["datetime"] = df["data"]

    df["hora_do_dia"] = df["datetime"].dt.hour
    df["dia_semana"] = df["datetime"].dt.day_name()
    df["lucro"] = df["valor_retorno"] - df["valor_apostado"]
    df["roi"] = np.where(
        df["valor_apostado"] > 0,
        (df["lucro"] / df["valor_apostado"]) * 100,
        0
    )
    df["ganhou"] = df["lucro"] > 0
    return df


def summary_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("hora_do_dia").agg(
        total_apostas=("valor_apostado", "count"),
        total_apostado=("valor_apostado", "sum"),
        total_retorno=("valor_retorno", "sum"),
        lucro=("lucro", "sum"),
        taxa_acerto=("ganhou", "mean"),
        roi_medio=("roi", "mean"),
    ).reset_index()
    g["taxa_acerto"] = (g["taxa_acerto"] * 100).round(1)
    g["roi_medio"] = g["roi_medio"].round(1)
    return g.sort_values("hora_do_dia")


def summary_by_weekday(df: pd.DataFrame) -> pd.DataFrame:
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    g = df.groupby("dia_semana").agg(
        total_apostas=("valor_apostado", "count"),
        total_apostado=("valor_apostado", "sum"),
        lucro=("lucro", "sum"),
        taxa_acerto=("ganhou", "mean"),
        roi_medio=("roi", "mean"),
    ).reindex(order).dropna().reset_index()
    g["taxa_acerto"] = (g["taxa_acerto"] * 100).round(1)
    g["roi_medio"] = g["roi_medio"].round(1)
    return g


def summary_by_platform(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("plataforma").agg(
        total_apostas=("valor_apostado", "count"),
        total_apostado=("valor_apostado", "sum"),
        lucro=("lucro", "sum"),
        taxa_acerto=("ganhou", "mean"),
        roi_medio=("roi", "mean"),
    ).reset_index()
    g["taxa_acerto"] = (g["taxa_acerto"] * 100).round(1)
    g["roi_medio"] = g["roi_medio"].round(1)
    return g


def summary_by_type(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("tipo").agg(
        total_apostas=("valor_apostado", "count"),
        total_apostado=("valor_apostado", "sum"),
        lucro=("lucro", "sum"),
        taxa_acerto=("ganhou", "mean"),
        roi_medio=("roi", "mean"),
    ).reset_index()
    g["taxa_acerto"] = (g["taxa_acerto"] * 100).round(1)
    g["roi_medio"] = g["roi_medio"].round(1)
    return g


def consecutive_results(df: pd.DataFrame) -> dict:
    """Analisa sequências de vitórias/derrotas."""
    df = df.sort_values("datetime")
    results = df["ganhou"].astype(int).tolist()
    max_win_streak = 0
    max_loss_streak = 0
    current = 0
    last = None
    for r in results:
        if r == last:
            current += 1
        else:
            current = 1
            last = r
        if r == 1:
            max_win_streak = max(max_win_streak, current)
        else:
            max_loss_streak = max(max_loss_streak, current)
    return {
        "maior_sequencia_vitorias": max_win_streak,
        "maior_sequencia_derrotas": max_loss_streak,
        "total_apostas": len(results),
        "taxa_acerto_geral": round(sum(results) / len(results) * 100, 1) if results else 0,
    }


def overall_stats(df: pd.DataFrame) -> dict:
    return {
        "total_apostas": len(df),
        "total_apostado": round(df["valor_apostado"].sum(), 2),
        "total_retorno": round(df["valor_retorno"].sum(), 2),
        "lucro_liquido": round(df["lucro"].sum(), 2),
        "roi_geral": round((df["lucro"].sum() / df["valor_apostado"].sum()) * 100, 1)
        if df["valor_apostado"].sum() > 0
        else 0,
        "taxa_acerto": round(df["ganhou"].mean() * 100, 1),
    }


def best_times_to_bet(df: pd.DataFrame, min_apostas: int = 2) -> pd.DataFrame:
    """
    Identifica os melhores horários com base em ROI e taxa de acerto.
    Só considera horários com pelo menos min_apostas.
    """
    hour_df = summary_by_hour(df)
    hour_df = hour_df[hour_df["total_apostas"] >= min_apostas].copy()
    if hour_df.empty:
        return hour_df
    # Score simples: ROI + (taxa_acerto / 2)
    hour_df["score"] = hour_df["roi_medio"] + (hour_df["taxa_acerto"] / 2)
    hour_df = hour_df.sort_values("score", ascending=False).reset_index(drop=True)
    hour_df["recomendacao"] = hour_df["score"].apply(
        lambda x: "🔥 Excelente" if x > 30 else ("✅ Bom" if x > 10 else ("⚠️ Neutro" if x > 0 else "❌ Evitar"))
    )
    return hour_df


def suggest_stake(
    df: pd.DataFrame,
    bankroll: float = 500.0,
    risk_level: str = "moderado"
) -> dict:
    """
    Sugere valor de aposta com base no histórico e no bankroll.
    risk_level: conservador | moderado | agressivo
    """
    if df.empty or df["valor_apostado"].sum() == 0:
        return {"erro": "Dados insuficientes"}

    stats = overall_stats(df)
    taxa = stats["taxa_acerto"] / 100
    roi = stats["roi_geral"] / 100

    # Percentuais de bankroll por perfil
    pct_map = {
        "conservador": 0.01,   # 1%
        "moderado": 0.025,     # 2.5%
        "agressivo": 0.05,     # 5%
    }
    pct = pct_map.get(risk_level, 0.025)

    # Ajuste pelo desempenho histórico
    if roi > 0.15 and taxa > 0.5:
        pct *= 1.3  # histórico bom → pode arriscar um pouco mais
    elif roi < 0 or taxa < 0.4:
        pct *= 0.6  # histórico ruim → reduz

    stake_sugerido = round(bankroll * pct, 2)
    stake_min = round(bankroll * 0.005, 2)  # mínimo 0.5%
    stake_max = round(bankroll * 0.05, 2)   # máximo 5%

    # Valor médio histórico do usuário
    media_historica = round(df["valor_apostado"].mean(), 2)

    return {
        "bankroll": bankroll,
        "perfil": risk_level,
        "stake_sugerido": stake_sugerido,
        "stake_minimo_recomendado": max(stake_min, 5.0),
        "stake_maximo_recomendado": stake_max,
        "media_historica_usuario": media_historica,
        "observacao": (
            f"Com base no seu ROI histórico de {stats['roi_geral']}% "
            f"e taxa de acerto de {stats['taxa_acerto']}%. "
            "Nunca aposte mais do que pode perder."
        ),
    }


def stake_by_hour(df: pd.DataFrame, bankroll: float = 500.0) -> pd.DataFrame:
    """Sugere stake diferente por horário conforme desempenho."""
    hour_df = best_times_to_bet(df)
    if hour_df.empty:
        return hour_df

    def calc_stake(row):
        base = bankroll * 0.02
        if row["score"] > 30:
            return round(base * 1.5, 2)
        elif row["score"] > 10:
            return round(base * 1.1, 2)
        elif row["score"] > 0:
            return round(base * 0.8, 2)
        else:
            return round(base * 0.4, 2)

    hour_df["stake_sugerido"] = hour_df.apply(calc_stake, axis=1)
    return hour_df[["hora_do_dia", "roi_medio", "taxa_acerto", "score", "recomendacao", "stake_sugerido"]]
