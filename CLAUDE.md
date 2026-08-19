# Contrato do projeto — Vol Implicita Spx

Leia o `CLAUDE.md` global e use este arquivo para o que é específico deste
repositório.

## Resultado do produto

- **Problema:** superfície de vol implícita e skew não são triviais de
  calcular corretamente (opção americana, taxa livre de risco, dividendo).
  Um repositório que faz isso certo prova leitura de derivativos.
- **Usuário:** eu, e quem revisa o portfólio avaliando para pesquisa
  quantitativa.
- **Saída verificável:** IV, delta e vega por strike/vencimento, calculados
  por inversão Black-Scholes (Newton-Raphson) e validados contra o
  `impliedVolatility` que a própria Yahoo/CBOE já publica na chain — a fonte
  carrega seu próprio gabarito, sem precisar de fixture externa fabricada.
- **Fonte de dados permitida:** `yfinance`, chain de opções da SPY (proxy
  líquido do SPX; o índice em si não expõe chain via yfinance). Taxa livre de
  risco: FRED `DGS3MO` via Postgres do `dados-mercado-publico`
  (`DADOS_MERCADO_PUBLICO_POSTGRES_DSN` do projeto vizinho — lido pela
  interface pública `series_vintage`, sem importar código de lá).
- **Menor corte ponta a ponta:** CLI que recebe um vencimento, busca a chain
  na SPY, calcula IV+delta+vega por strike e devolve a curva de skew daquele
  vencimento.
- **Fora de escopo:** sinal de trading, backtest histórico (`yfinance` só dá
  a chain do dia — sem histórico, não dá pra reconstruir superfícies
  passadas ainda), superfície paramétrica (SVI/SABR), grego de segunda ordem.

Não implemente enquanto um `PREENCHER` que altere o design continuar em aberto.

## Comandos

```bash
uv sync
uv run python scripts/format.py
uv run python scripts/check.py
```

## Regras locais

- O pacote é `vol_implicita_spx` e vive em `src/vol_implicita_spx`.
- Notebook importa de `src/`; código de produção nunca importa notebook.
- Configuração vem de ambiente por `Settings`.
- Preserve dado bruto e metadados temporais quando houver ingestão.
- Atualize este arquivo quando uma decisão estrutural mudar.

## Estilo

Código público, lido por gente. A regra é contenção — a lista completa está em
`AGENTS.md`, seção "Style", e vale igual para mim e para o Codex.

- Comentário explica *por quê*, nunca *o quê*. Se parafraseia a linha abaixo,
  apague; se a linha precisa de paráfrase, renomeie a variável.
- Docstring só onde a assinatura não basta (unidade, fuso, efeito colateral,
  o que levanta). Helper privado de três linhas não leva.
- Teste afirma comportamento que pode quebrar, não constante. Cobertura é
  consequência de testar o que importa, nunca meta a inflar.
- Não capture exceção que não sabe tratar; não abstraia com um único chamador.

## Autoria dos commits

Autor e committer são um só: o dono do repositório. Nenhum `Co-Authored-By:`,
nenhum trailer de sessão, nenhuma menção a Claude, Codex ou ferramenta. Não
altere `user.name` nem `user.email`.

## Estado da sessão

- **Decidido:** primeiro corte entregue — CLI `curva --vencimento` que busca
  a chain da SPY, inverte Black-Scholes por Newton-Raphson (bisseção como
  salva-vidas) e devolve IV, delta e vega por strike. Taxa livre de risco lida
  do Postgres do `dados-mercado-publico` (série `DGS3MO`). Validado contra a
  IV que a própria Yahoo publica, usando fixture congelada de uma chain real.
- **Pendente:** ingerir `DGS3MO` no `dados-mercado-publico` de verdade (hoje
  só a taxa fixa de exemplo do README foi testada; o comando real depende da
  série existir no Postgres vizinho).
- **Próximo passo:** decidir se vale um segundo corte de snapshot diário
  (via Airflow, no padrão do `dados-mercado-publico`) para começar a acumular
  histórico de superfície — sem isso, backtest de vol continua fora de
  alcance.

