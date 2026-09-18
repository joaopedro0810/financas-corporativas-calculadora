# Calculadora Financeira

Calculadora financeira (juros simples, compostos, Sistema Price e equivalência de taxas) — MBA Gestão Empresarial FGV

Feita para a disciplina de Finanças Corporativas (MBA Gestão Empresarial -
FGV). Cobre:

- **Juros Simples** — Montante, Capital inicial ou Prazo (com taxa e prazo em
  escalas diferentes, convertidos automaticamente).
- **Juros Compostos** — Montante, Capital inicial ou Prazo (conversão de
  escala via expoente, nunca multiplicando/dividindo a taxa efetiva
  diretamente).
- **Sistema Price** — Prestação, Valor Presente, Prazo ou Taxa; parcelas
  Postecipadas (END) ou Antecipadas (BEGIN); carência com capitalização de
  juros ou pagamento de juros à parte; taxa em periodicidade diferente da
  parcela; tabela de amortização completa.
- **Equivalência de Taxas** — conversão entre periodicidades (diária, mensal,
  bimestral, trimestral, quadrimestral, semestral, anual), convenção
  comercial 30/360.

## Versão web (`index.html`)

Página única em HTML/CSS/JS puro (sem dependências, sem build), responsiva
para uso no celular. Publicada via GitHub Pages:

**https://joaopedro0810.github.io/financas-corporativas-calculadora/**

## Versão desktop (`calculadora_financeira.py`)

Aplicativo Tkinter equivalente (mesmas fórmulas, testadas em conjunto com a
versão web). Requer apenas Python 3 com Tkinter (padrão na maioria das
instalações):

```
python calculadora_financeira.py
```

## Convenções

- Taxas em regime composto usam a convenção comercial 30/360 para conversão
  entre periodicidades (Diária=1, Mensal=30, Bimestral=60, Trimestral=90,
  Quadrimestral=120, Semestral=180, Anual=360 dias).
- Autor: João Pedro Castro de Souza.
