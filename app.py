"""
Analisador de Bets (7K Bet / 7Games) + Loterias (Mega Sena / Lotofácil)
Interface Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os

# Corrige o caminho para funcionar no Streamlit Cloud
ROOT_DIR = Path(__file__).parent
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(ROOT_DIR))

try:
    from betting_analyzer import (
        load_bets,
        summary_by_hour,
        summary_by_weekday,
        summary_by_platform,
        summary_by_type,
        consecutive_results,
        overall_stats,
        best_times_to_bet,
        suggest_stake,
        stake_by_hour,
    )
    from lottery_analyzer import (
        load_mega_sena,
        load_lotofacil,
        frequency_analysis,
        delay_analysis,
        even_odd_stats,
        sum_stats,
        generate_games,
    )
except ModuleNotFoundError:
    # Tentativa alternativa caso a estrutura de pastas seja diferente
    from src.betting_analyzer import (
        load_bets,
        summary_by_hour,
        summary_by_weekday,
        summary_by_platform,
        summary_by_type,
        consecutive_results,
        overall_stats,
        best_times_to_bet,
        suggest_stake,
        stake_by_hour,
    )
    from src.lottery_analyzer import (
        load_mega_sena,
        load_lotofacil,
        frequency_analysis,
        delay_analysis,
        even_odd_stats,
        sum_stats,
        generate_games,
    )

st.set_page_config(
    page_title="Analisador Bets + Loterias",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Analisador de Bets + Loterias")
st.caption("7K Bet • 7Games • Mega Sena • Lotofácil")

st.warning(
    "⚠️ **Aviso importante**: Apostas e loterias envolvem risco. "
    "Análises estatísticas **não garantem** lucro nem acerto. "
    "Use apenas como ferramenta de estudo. Jogue com responsabilidade."
)

tab1, tab2, tab3 = st.tabs(["🎯 Apostas (7K / 7Games)", "🎱 Mega Sena", "🍀 Lotofácil"])

# ============================================================
# ABA 1 - APOSTAS
# ============================================================
with tab1:
    st.header("Análise de Apostas")
    st.markdown("Faça upload do seu CSV de apostas ou use o exemplo.")

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_bets = st.file_uploader(
            "CSV de apostas (colunas: data, hora, plataforma, tipo, valor_apostado, valor_retorno, resultado)",
            type=["csv"],
            key="bets_upload",
        )
    with col2:
        use_example = st.checkbox("Usar dados de exemplo", value=True, key="bets_example")

    if uploaded_bets is not None:
        df_bets = load_bets(uploaded_bets)
    elif use_example:
        exemplo_path = ROOT_DIR / "data" / "exemplo_apostas.csv"
        df_bets = load_bets(str(exemplo_path))
    else:
        df_bets = None

    if df_bets is not None:
        st.subheader("Resumo Geral")
        stats = overall_stats(df_bets)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Apostas", stats["total_apostas"])
        c2.metric("Total Apostado", f"R$ {stats['total_apostado']:.2f}")
        c3.metric("Lucro Líquido", f"R$ {stats['lucro_liquido']:.2f}")
        c4.metric("ROI Geral", f"{stats['roi_geral']}%")
        c5.metric("Taxa de Acerto", f"{stats['taxa_acerto']}%")

        seq = consecutive_results(df_bets)
        st.info(
            f"Maior sequência de vitórias: **{seq['maior_sequencia_vitorias']}** | "
            f"Maior sequência de derrotas: **{seq['maior_sequencia_derrotas']}**"
        )

        # ---------- MELHOR HORA PARA APOSTAR ----------
        st.subheader("⏰ Melhor Horário para Apostar")
        best_hours = best_times_to_bet(df_bets)
        if not best_hours.empty:
            top3 = best_hours.head(3)
            st.success(
                f"**Top 3 horários recomendados:** "
                + " | ".join([f"{int(r['hora_do_dia']):02d}h ({r['recomendacao']})" for _, r in top3.iterrows()])
            )
            fig_best = px.bar(
                best_hours,
                x="hora_do_dia",
                y="score",
                color="recomendacao",
                title="Score de Desempenho por Hora (quanto maior, melhor)",
                labels={"hora_do_dia": "Hora", "score": "Score"},
            )
            st.plotly_chart(fig_best, use_container_width=True)
            st.dataframe(best_hours, use_container_width=True)
        else:
            st.warning("Dados insuficientes para recomendar horários.")

        # ---------- SUGESTÃO DE VALOR DE APOSTA ----------
        st.subheader("💰 Melhor Valor para Apostar (conforme estatísticas)")
        col_bank, col_risk = st.columns(2)
        with col_bank:
            bankroll = st.number_input("Seu bankroll atual (R$)", min_value=50.0, value=500.0, step=50.0)
        with col_risk:
            risk = st.selectbox("Perfil de risco", ["conservador", "moderado", "agressivo"])

        stake_info = suggest_stake(df_bets, bankroll=bankroll, risk_level=risk)
        if "erro" not in stake_info:
            c1, c2, c3 = st.columns(3)
            c1.metric("Stake Sugerido", f"R$ {stake_info['stake_sugerido']:.2f}")
            c2.metric("Mínimo recomendado", f"R$ {stake_info['stake_minimo_recomendado']:.2f}")
            c3.metric("Máximo recomendado", f"R$ {stake_info['stake_maximo_recomendado']:.2f}")
            st.caption(stake_info["observacao"])
            st.caption(f"Sua média histórica de aposta: R$ {stake_info['media_historica_usuario']:.2f}")

            st.markdown("**Stake sugerido por horário** (ajustado pelo desempenho de cada hora):")
            stake_hour = stake_by_hour(df_bets, bankroll=bankroll)
            if not stake_hour.empty:
                st.dataframe(stake_hour, use_container_width=True)

        st.subheader("Por Horário do Dia (detalhado)")
        hour_df = summary_by_hour(df_bets)
        fig_hour = px.bar(
            hour_df,
            x="hora_do_dia",
            y="roi_medio",
            color="taxa_acerto",
            labels={"hora_do_dia": "Hora", "roi_medio": "ROI Médio (%)", "taxa_acerto": "Taxa Acerto (%)"},
            title="ROI Médio por Hora do Dia",
        )
        st.plotly_chart(fig_hour, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Por Dia da Semana")
            week_df = summary_by_weekday(df_bets)
            fig_week = px.bar(week_df, x="dia_semana", y="roi_medio", title="ROI por Dia da Semana")
            st.plotly_chart(fig_week, use_container_width=True)
        with col_b:
            st.subheader("Por Plataforma")
            plat_df = summary_by_platform(df_bets)
            fig_plat = px.pie(plat_df, names="plataforma", values="total_apostado", title="Volume por Plataforma")
            st.plotly_chart(fig_plat, use_container_width=True)

        st.subheader("Por Tipo (Esporte x Crash)")
        type_df = summary_by_type(df_bets)
        st.dataframe(type_df, use_container_width=True)

        with st.expander("Ver todos os dados"):
            st.dataframe(df_bets, use_container_width=True)
    else:
        st.info("Faça upload de um CSV ou marque 'Usar dados de exemplo'.")

# ============================================================
# ABA 2 - MEGA SENA
# ============================================================
with tab2:
    st.header("Mega Sena — Análise Estatística")
    st.markdown("6 números de 1 a 60")

    uploaded_mega = st.file_uploader("CSV Mega Sena (concurso, data, n1..n6)", type=["csv"], key="mega_upload")
    use_mega_example = st.checkbox("Usar dados de exemplo Mega Sena", value=True, key="mega_example")

    if uploaded_mega is not None:
        df_mega = load_mega_sena(uploaded_mega)
    elif use_mega_example:
        exemplo_path = ROOT_DIR / "data" / "exemplo_megasena.csv"
        df_mega = load_mega_sena(str(exemplo_path))
    else:
        df_mega = None

    if df_mega is not None:
        st.success(f"Carregados **{len(df_mega)}** concursos")

        freq = frequency_analysis(df_mega, 60)
        delay = delay_analysis(df_mega, 60)

        st.subheader("📈 Probabilidades dos Números (baseado no histórico)")
        st.caption(
            "Probabilidade empírica = quantas vezes o número saiu ÷ total de sorteios. "
            "A probabilidade teórica de qualquer número sair em um sorteio da Mega é ~10%."
        )
        st.dataframe(
            freq[["numero", "frequencia", "probabilidade_%", "prob_teorica_%", "desvio_vs_teorica"]].head(20),
            use_container_width=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Números Mais Sorteados (Quentes)")
            fig_hot = px.bar(
                freq.head(15),
                x="numero",
                y="probabilidade_%",
                title="Top 15 - Probabilidade Empírica (%)",
                labels={"probabilidade_%": "Probabilidade (%)"},
            )
            st.plotly_chart(fig_hot, use_container_width=True)
        with col2:
            st.subheader("Números Mais Atrasados")
            st.dataframe(delay.head(10), use_container_width=True)
            fig_delay = px.bar(delay.head(15), x="numero", y="atraso", title="Top 15 Atrasados")
            st.plotly_chart(fig_delay, use_container_width=True)

        st.subheader("Estatísticas de Soma e Par/Ímpar")
        s = sum_stats(df_mega)
        e = even_odd_stats(df_mega)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Soma Média", s["media"])
        c2.metric("Soma Mediana", s["mediana"])
        c3.metric("Média de Pares", e["media_pares"])
        c4.metric("Desvio da Soma", s["desvio"])

        st.subheader("Sugestões de Jogos (apenas estatística)")
        strategy = st.selectbox(
            "Estratégia",
            ["misto", "quentes", "frios", "atrasados"],
            key="mega_strategy",
        )
        num_games = st.slider("Quantidade de jogos", 1, 10, 5, key="mega_games")
        if st.button("Gerar sugestões Mega Sena", key="btn_mega"):
            games = generate_games(freq, delay, 6, num_games, strategy)
            for i, g in enumerate(games, 1):
                st.write(f"**Jogo {i}:** {' - '.join(f'{n:02d}' for n in g)}")
            st.caption("Lembrete: isso não aumenta sua chance real. É só análise histórica.")
    else:
        st.info("Faça upload ou use o exemplo.")

# ============================================================
# ABA 3 - LOTOFÁCIL
# ============================================================
with tab3:
    st.header("Lotofácil — Análise Estatística")
    st.markdown("15 números de 1 a 25")

    uploaded_loto = st.file_uploader("CSV Lotofácil (concurso, data, n1..n15)", type=["csv"], key="loto_upload")
    use_loto_example = st.checkbox("Usar dados de exemplo Lotofácil", value=True, key="loto_example")

    if uploaded_loto is not None:
        df_loto = load_lotofacil(uploaded_loto)
    elif use_loto_example:
        exemplo_path = ROOT_DIR / "data" / "exemplo_lotofacil.csv"
        df_loto = load_lotofacil(str(exemplo_path))
    else:
        df_loto = None

    if df_loto is not None:
        st.success(f"Carregados **{len(df_loto)}** concursos")

        freq = frequency_analysis(df_loto, 25)
        delay = delay_analysis(df_loto, 25)

        st.subheader("📈 Probabilidades dos Números (baseado no histórico)")
        st.caption(
            "Probabilidade empírica = quantas vezes o número saiu ÷ total de sorteios. "
            "Na Lotofácil a probabilidade teórica de qualquer número sair é 60%."
        )
        st.dataframe(
            freq[["numero", "frequencia", "probabilidade_%", "prob_teorica_%", "desvio_vs_teorica"]].head(25),
            use_container_width=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Números Mais Sorteados (Quentes)")
            fig_hot = px.bar(
                freq.head(15),
                x="numero",
                y="probabilidade_%",
                title="Top 15 - Probabilidade Empírica (%)",
                labels={"probabilidade_%": "Probabilidade (%)"},
            )
            st.plotly_chart(fig_hot, use_container_width=True)
        with col2:
            st.subheader("Números Mais Atrasados")
            st.dataframe(delay.head(10), use_container_width=True)
            fig_delay = px.bar(delay.head(15), x="numero", y="atraso", title="Top 15 Atrasados")
            st.plotly_chart(fig_delay, use_container_width=True)

        st.subheader("Estatísticas de Soma e Par/Ímpar")
        s = sum_stats(df_loto)
        e = even_odd_stats(df_loto)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Soma Média", s["media"])
        c2.metric("Soma Mediana", s["mediana"])
        c3.metric("Média de Pares", e["media_pares"])
        c4.metric("Desvio da Soma", s["desvio"])

        st.subheader("Sugestões de Jogos (apenas estatística)")
        strategy = st.selectbox(
            "Estratégia",
            ["misto", "quentes", "frios", "atrasados"],
            key="loto_strategy",
        )
        num_games = st.slider("Quantidade de jogos", 1, 10, 5, key="loto_games")
        if st.button("Gerar sugestões Lotofácil", key="btn_loto"):
            games = generate_games(freq, delay, 15, num_games, strategy)
            for i, g in enumerate(games, 1):
                st.write(f"**Jogo {i}:** {' - '.join(f'{n:02d}' for n in g)}")
            st.caption("Lembrete: isso não aumenta sua chance real. É só análise histórica.")
    else:
        st.info("Faça upload ou use o exemplo.")

st.markdown("---")
st.markdown(
    "Feito para estudo • 7K Bet • 7Games • Mega Sena • Lotofácil  \n"
    "Jogue com responsabilidade. 18+"
)
