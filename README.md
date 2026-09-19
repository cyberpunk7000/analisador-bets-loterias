# 📊 Analisador de Bets + Loterias

Ferramenta em Python + Streamlit para analisar:

- **Apostas** nas plataformas **7K Bet** e **7Games** (esportes + crash games)
- **Mega Sena** e **Lotofácil** com base em sorteios anteriores

---

## ⚠️ Aviso Importante

Apostas e loterias envolvem **risco real de perda de dinheiro**.

- Nenhuma análise estatística garante lucro ou acerto.
- Cada sorteio de loteria é independente dos anteriores.
- Use esta ferramenta **apenas para estudo e entretenimento**.
- Jogue com responsabilidade. 18+

---

## O que o programa faz

### 1. Análise de Apostas (7K Bet / 7Games)
- Resumo geral (ROI, taxa de acerto, lucro)
- **Melhor horário para apostar** (ranking com score e recomendação)
- **Sugestão de valor de aposta** (stake) conforme bankroll e perfil de risco
- Stake ajustado por horário
- Melhor dia da semana
- Comparativo por plataforma e por tipo (esporte x crash)
- Sequências de vitórias/derrotas

### 2. Mega Sena & Lotofácil
- **Probabilidade empírica** de cada número (+ comparação com a probabilidade teórica)
- Frequência dos números (quentes e frios)
- Números mais atrasados
- Estatísticas de soma e par/ímpar
- Geração de sugestões de jogos baseadas em estratégias estatísticas:
  - Quentes
  - Frios
  - Atrasados
  - Misto

---

## Como rodar

### 1. Clonar o repositório
```bash
git clone https://github.com/SEU_USUARIO/analisador-bets-loterias.git
cd analisador-bets-loterias
```

### 2. Criar ambiente virtual (recomendado)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / Mac
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Rodar a interface
```bash
streamlit run app.py
```

O navegador vai abrir automaticamente em `http://localhost:8501`.

---

## Formato dos CSVs

### Apostas (`exemplo_apostas.csv`)
```csv
data,hora,plataforma,tipo,valor_apostado,valor_retorno,resultado
2026-08-01,14:22,7K Bet,esporte,20.00,0.00,perdeu
2026-08-01,15:10,7K Bet,esporte,15.00,32.50,ganhou
```

Colunas obrigatórias:
- `data` (AAAA-MM-DD ou DD/MM/AAAA)
- `hora` (HH:MM)
- `plataforma` (7K Bet, 7Games, etc.)
- `tipo` (esporte ou crash)
- `valor_apostado`
- `valor_retorno`
- `resultado` (ganhou / perdeu) — opcional, o lucro é calculado automaticamente

### Mega Sena
```csv
concurso,data,n1,n2,n3,n4,n5,n6
2800,15/03/2025,4,12,23,31,45,58
```

### Lotofácil
```csv
concurso,data,n1,n2,...,n15
3700,01/08/2025,1,2,3,5,7,8,10,12,14,15,17,19,21,23,25
```

---

## Como pegar dados reais das loterias

Você pode baixar o histórico completo de várias fontes públicas:

- Site oficial da Caixa (loterias.caixa.gov.br)
- Repositórios públicos no GitHub com JSON/CSV atualizados
- Pacote Python `lotterybr` (`pip install lotterybr`)

Depois é só salvar como CSV no formato acima e fazer upload na interface.

---

## Estrutura do projeto

```
analisador-bets-loterias/
├── app.py                  # Interface Streamlit
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── exemplo_apostas.csv
│   ├── exemplo_megasena.csv
│   └── exemplo_lotofacil.csv
└── src/
    ├── betting_analyzer.py
    └── lottery_analyzer.py
```

---

## Próximos passos possíveis

- Integração automática com APIs de resultados da Caixa
- Mais estratégias de geração de jogos
- Exportar relatórios em PDF
- Análise de fechamentos (Lotofácil)

---

Feito para estudo. Jogue com responsabilidade.
