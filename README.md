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
- **Fluxo de Caixa (VPL / TIR / TIR-M / Payback / ILL)** — fluxo de caixa
  livre (períodos e valores editáveis), Valor Presente Líquido, Taxa Interna
  de Retorno (busca numérica), TIR-M/MIRR (taxas de captação e aplicação
  distintas), Payback simples e descontado, Índice de Lucratividade Líquida.
- **Perpetuidade** — com ou sem crescimento constante (modelo de Gordon),
  incluindo o VPL do projeto como um todo (perpetuidade menos o investimento
  inicial).
- **Custo de Capital** — CAPM (custo do capital próprio), custo de capital de
  terceiros líquido de IR, e CMPC/WACC.
- **Capital de Giro (NCG)** — PME, PMR, PMP, Ciclo Operacional, Ciclo
  Financeiro e NCG = Desembolso Anual × (Ciclo Financeiro / 360).
- **Ponto de Equilíbrio** — Operacional, Contábil (com depreciação) e
  Econômico (com custo de capital anualizado via Sistema Price).
- **Equivalência de Taxas** — conversão entre periodicidades (diária, mensal,
  bimestral, trimestral, quadrimestral, semestral, anual), convenção
  comercial 30/360.

Todas as fórmulas foram conferidas contra a planilha oficial da disciplina
(`Todas Planilhas para Finanças.xlsx`) e os exemplos numéricos dela.

## Como usar (`index.html`)

Página única em HTML/CSS/JS puro (sem dependências, sem build), responsiva
para uso no celular. Publicada via GitHub Pages:

**https://joaopedro0810.github.io/financas-corporativas-calculadora/**

Também pode ser aberta localmente, direto do arquivo `index.html`, em
qualquer navegador.

## Convenções

- Taxas em regime composto usam a convenção comercial 30/360 para conversão
  entre periodicidades (Diária=1, Mensal=30, Bimestral=60, Trimestral=90,
  Quadrimestral=120, Semestral=180, Anual=360 dias).
- Autor: João Pedro Castro de Souza.
