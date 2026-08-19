# vol-implicita-spx

Superfície de vol implícita e skew da SPY (proxy líquido do SPX), calculada
por inversão numérica de Black-Scholes — sem depender de nenhuma biblioteca
de precificação pronta.

## O problema

Toda corretora e todo terminal já mostra a vol implícita de uma opção. O que
não aparece é a conta: inverter Black-Scholes para achar a vol que reproduz
o preço de mercado exige um solver numérico (o preço não é invertível em
forma fechada), e fazer essa conta certo — com a taxa livre de risco e o
dividendo certos — é o que este repositório prova.

## Resultado

```console
$ uv run python -m vol_implicita_spx curva --vencimento 2026-09-18
strike,tipo,iv,iv_referencia,delta,vega
759.0,call,0.141798,0.159402,0.662783,80.404433
760.0,call,0.143328,0.160058,0.649517,81.584290
761.0,call,0.138608,0.155145,0.641586,82.239416
762.0,call,0.139309,0.155450,0.628633,83.229724
763.0,call,0.136693,0.152322,0.618046,83.966252
764.0,call,0.134564,0.149758,0.606649,84.686693
...
```

`iv_referencia` é o que a própria Yahoo/CBOE publicam na chain — um gabarito
gratuito para validar a conta sem precisar de fixture fabricada à mão. A
transcrição acima foi calculada a partir da fixture congelada em
`tests/fixtures/spy_chain_20260918.json` (chain real da SPY, capturada em
2026-08-19), com taxa livre de risco fixa de 5% só para o exemplo — a coleta
ao vivo usa a chain do momento da chamada e a taxa `DGS3MO` do Postgres.

## Problema e escopo

- **Usuário:** eu, e quem revisa o portfólio avaliando para pesquisa
  quantitativa.
- **Decisão:** dá pra ler skew e superfície de vol da SPY sem depender de
  terminal pago, e verificar a própria conta contra a IV que a fonte publica.
- **Entrada:** `yfinance`, chain de opções da SPY. Taxa livre de risco: FRED
  `DGS3MO`, lida do Postgres do
  [`dados-mercado-publico`](../dados-mercado-publico) via
  `DADOS_MERCADO_PUBLICO_POSTGRES_DSN` — a mesma variável que aquele projeto
  usa, então um `.env` configura os dois.
- **Fora de escopo:** sinal de trading, backtest histórico (`yfinance` só
  expõe a chain do dia — sem histórico, não dá pra reconstruir superfícies
  passadas ainda), superfície paramétrica (SVI/SABR), grego de segunda ordem.

## Arquitetura

```
yfinance (SPY)                    Postgres (dados-mercado-publico)
    │  chain, spot, dividendos         │  DGS3MO via series_vintage
    ▼                                  ▼
fontes/spy.py                    taxa_livre_risco.py
    │                                  │
    └──────────────┬───────────────────┘
                    ▼
              skew.py            para cada contrato: inverte
                    │             black_scholes.vol_implicita
                    ▼
                 cli.py           curva de skew em CSV
```

`black_scholes.py` não depende de nada além da biblioteca padrão —
`math.erf` já dá a CDF normal sem trazer `scipy`/`numpy` só para isso.

Duas decisões que valem explicação:

**Newton-Raphson com bisseção como salva-vidas.** Newton converge rápido perto
do preço, mas diverge quando a vega é quase zero (strike bem fora do dinheiro)
ou quando o passo joga a vol pra fora de uma faixa razoável. Nesse caso o
solver cai pra bisseção em `[0.0001, 5.0]`, que é lenta mas sempre converge se
o preço estiver dentro da banda alcançável por alguma vol positiva. Fora dessa
banda (preço de mercado abaixo do intrínseco, cotação sem negócio real), a
função devolve `None` em vez de inventar um número.

**SPY é opção americana; a conta aqui é europeia.** Black-Scholes-Merton
assume exercício só no vencimento. SPY permite exercício antecipado, e paga
dividendo — o que torna o call americano ligeiramente mais valioso que o
europeu equivalente perto de uma data-ex. Contra a fixture real usada nos
testes (vencimento de ~30 dias), a IV calculada aqui fica em média a menos de
0,015 vol point da IV que a Yahoo publica, com máximo abaixo de 0,03 — o viés
existe, é pequeno neste horizonte, e fica medido pelo teste em vez de
escondido.

## Executar localmente

Requisitos: Python 3.12, `uv`, Docker (para o Postgres efêmero dos testes),
e o [`dados-mercado-publico`](../dados-mercado-publico) rodando com a série
`DGS3MO` ingerida:

```bash
# no dados-mercado-publico:
docker compose up -d
uv run python -m dados_mercado_publico ingerir --fonte fred --serie DGS3MO
```

```bash
uv sync
cp .env.example .env
uv run python -m vol_implicita_spx curva --vencimento 2026-09-18
```

Sem a série `DGS3MO` ingerida no projeto vizinho, o comando orienta e sai com
código 2 em vez de inventar uma taxa.

## Qualidade

```bash
uv run python scripts/check.py
```

O check executa formatação, lint, tipos e testes com cobertura. É o mesmo
comando que o CI roda, em Windows, Linux e macOS.

Para aplicar formatação e correções automáticas de lint:

```bash
uv run python scripts/format.py
```

## Estrutura

```text
src/vol_implicita_spx/
    black_scholes.py   precificação e inversão numérica — sem dependência de rede
    fontes/spy.py       adaptador yfinance, testável com um ticker falso
    taxa_livre_risco.py leitura da interface pública do dados-mercado-publico
    skew.py             combina os três numa curva por vencimento
    cli.py               coordenação
tests/fixtures/          chain real da SPY congelada, usada como gabarito
```

## Limitações

- Sem histórico de chain: `yfinance` só dá o dia corrente, então não dá pra
  reconstruir uma superfície passada nem fazer backtest ainda. Point-in-time
  real exigiria capturar snapshots diários — próximo corte, se fizer sentido.
- Dividendo é um yield contínuo aproximado (soma dos pagamentos dos últimos
  365 dias / spot), não o calendário real de datas-ex.
- Sem superfície paramétrica (SVI/SABR): a curva é ponto a ponto, não
  suavizada nem extrapolada entre strikes.

## Licença

MIT. Dados de terceiros mantêm suas próprias licenças e termos de uso.
