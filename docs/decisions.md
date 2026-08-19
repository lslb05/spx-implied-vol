# Decisões

Registre somente decisões que alterem custo de mudança futuro.

## Modelo

### AAAA-MM-DD — Título

- **Contexto:** qual restrição ou problema exigiu decisão.
- **Decisão:** o caminho escolhido.
- **Alternativas:** opções relevantes descartadas.
- **Consequências:** ganhos, custos e gatilho para revisar.

### 2026-08-18 — Manter `CLAUDE.md` e `AGENTS.md` no repositório público

- **Contexto:** os dois arquivos declaram que o repositório é construído com
  apoio de agentes. A alternativa era ignorá-los no git para que o repositório
  público não revelasse o fluxo de trabalho.
- **Decisão:** manter os dois versionados e públicos.
- **Alternativas:** ignorar `AGENTS.md` no `.gitignore`; mantê-lo apenas local.
  Ambas quebram a delegação ao Codex, que lê esse arquivo do repositório — o
  custo é funcional e imediato, o ganho é cosmético.
- **Consequências:** o repositório declara o método em vez de escondê-lo, o que
  também é verificável por quem lê. Rever se algum destino exigir o contrário.

### 2026-08-19 — SPY como proxy do SPX, e Black-Scholes europeu sobre opção americana

- **Contexto:** o índice SPX não expõe chain de opções via `yfinance`; os
  únicos jeitos gratuitos de ter dado de opção de índice em quantidade são
  proxies via ETF (SPY) ou dado pago (CBOE DataShop). SPY é opção americana;
  o modelo de precificação mais simples de implementar sem dependência nova é
  Black-Scholes-Merton, que assume europeia.
- **Decisão:** usar a chain da SPY e aceitar o viés americano-vs-europeu,
  medindo-o em teste (`tests/test_skew.py`) contra a IV que a própria fonte
  publica, em vez de escondê-lo ou tentar corrigi-lo com um modelo binomial
  neste primeiro corte.
- **Alternativas:** modelo binomial (Cox-Ross-Rubinstein) para precificar
  exercício antecipado corretamente — mais fiel, mas mais código e mais
  parâmetro pra validar num corte que já tem risco técnico suficiente
  (inversão numérica). CBOE DataShop para XSP europeu — pago, fora da regra
  de fonte pública do portfólio.
- **Consequências:** o viés fica pequeno e documentado para o horizonte
  testado (~30 dias, diferença média abaixo de 0,015 vol point). Se um corte
  futuro precisar de opção curta (poucos dias) ou LEAP longo, o viés cresce e
  a decisão deve ser revisitada — não assuma que continua pequeno fora da
  faixa testada.

### 2026-08-19 — Newton-Raphson com bisseção como salva-vidas, sem `scipy`

- **Contexto:** inverter Black-Scholes para achar a IV não tem forma fechada.
  Newton-Raphson puro é rápido mas diverge quando a vega é quase zero (strike
  bem fora do dinheiro) — comum numa chain real, como a fixture de teste
  mostrou nos primeiros contratos experimentados.
- **Decisão:** Newton-Raphson como caminho rápido; se ele sair da faixa
  `[0.0001, 5.0]` ou a vega ficar pequena demais, cai pra bisseção na mesma
  faixa, que sempre converge se o preço estiver na banda alcançável por
  alguma vol positiva. Fora dessa banda, devolve `None` em vez de inventar
  número.
- **Alternativas:** `scipy.optimize.brentq` — mais testado, mas traz `scipy`
  inteiro (dependência pesada) só por uma função de root-finding que dá pra
  implementar em ~15 linhas com a garantia que este projeto precisa.
- **Consequências:** sem dependência nova além do que já era necessário;
  custo é manter esse solver testado (`tests/test_black_scholes.py` cobre
  round-trip preço→IV para vols de 5% a 80%, chamada e put).
