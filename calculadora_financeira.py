"""
Calculadora financeira (GUI) - Juros Simples, Juros Compostos, Montante e
Equivalencia de Taxas.

Disciplina: Financas Corporativas - MBA Gestao Empresarial (FGV)
Autor: Joao Pedro Castro de Souza

Uso: basta rodar `python calculadora_financeira.py` (usa apenas a
biblioteca padrao do Python - tkinter - sem dependencias externas).

Interface com tema escuro, navegacao lateral e calculo em tempo real
(o resultado é recalculado a cada tecla, sem precisar clicar em nada).
"""

import math
import tkinter as tk
from tkinter import ttk

# ----------------------------------------------------------------------
# Paleta / tema
# ----------------------------------------------------------------------
BG = "#0b1220"
BG_SIDEBAR = "#0a0f1c"
BG_CARD = "#111a2e"
BG_ENTRY = "#0e1626"
BORDER = "#1e2a44"
ACCENT = "#22d3ee"
ACCENT_DIM = "#0e7490"
TEXT = "#e2e8f0"
TEXT_MUTED = "#7d8aa3"
ERROR = "#f87171"
OK = "#34d399"

FONT_UI = ("Segoe UI", 10)
FONT_UI_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI Semibold", 15)
FONT_NAV = ("Segoe UI", 11)
FONT_MONO_BIG = ("Consolas", 22, "bold")
FONT_MONO = ("Consolas", 10)

# Dias por período (convenção comercial 30/360) para equivalência de taxas.
DIAS_POR_PERIODO = {
    "Diária": 1,
    "Mensal": 30,
    "Bimestral": 60,
    "Trimestral": 90,
    "Quadrimestral": 120,
    "Semestral": 180,
    "Anual": 360,
}


def parse_float(valor: str):
    """Converte texto em float aceitando vírgula decimal. Retorna None se vazio/inválido."""
    texto = valor.strip().replace("%", "").replace(",", ".")
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def fmt_moeda(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_pct(v: float, casas: int = 4) -> str:
    return f"{v:,.{casas}f}%".replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_num(v: float, casas: int = 4) -> str:
    return f"{v:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def prazo_efetivo(n: float, periodo_taxa: str, periodo_prazo: str) -> float:
    """Converte o prazo (n, na unidade `periodo_prazo`) para a unidade da taxa.

    Usa a convenção comercial 30/360 (DIAS_POR_PERIODO). A conversão é feita
    em número de dias e depois expressa de volta na unidade da taxa — nunca
    multiplicando ou dividindo a taxa efetiva diretamente.
    """
    dias_taxa = DIAS_POR_PERIODO[periodo_taxa]
    dias_prazo = DIAS_POR_PERIODO[periodo_prazo]
    return n * dias_prazo / dias_taxa


def linha_conversao(n_efetivo: float, periodo_taxa: str, periodo_prazo: str):
    """Linha extra de resultado mostrando o prazo já convertido, só quando as
    escalas de taxa e prazo são diferentes (para deixar a conversão visível)."""
    if periodo_taxa == periodo_prazo:
        return []
    return [(f"Prazo em nº de \"{periodo_taxa.lower()}\"", fmt_num(n_efetivo))]


def taxa_equivalente(i_frac: float, periodo_origem: str, periodo_destino: str) -> float:
    """Converte uma taxa (fração, ex.: 0.02) do período de origem para o de
    destino, em regime composto (convenção comercial 30/360)."""
    dias_origem = DIAS_POR_PERIODO[periodo_origem]
    dias_destino = DIAS_POR_PERIODO[periodo_destino]
    return (1 + i_frac) ** (dias_destino / dias_origem) - 1


# ----------------------------------------------------------------------
# Widgets utilitários com o visual escuro
# ----------------------------------------------------------------------
class Field(ttk.Frame):
    """Rótulo + campo de entrada, com callback ao vivo a cada tecla."""

    def __init__(self, master, label, default="", on_change=None, width=18):
        super().__init__(master, style="Card.TFrame")
        ttk.Label(self, text=label, style="Muted.TLabel").pack(anchor="w")
        self.var = tk.StringVar(value=default)
        self._entry = ttk.Entry(self, textvariable=self.var, style="Dark.TEntry",
                                 font=FONT_MONO, width=width)
        self._entry.pack(anchor="w", fill="x", pady=(4, 0))
        self._on_change = on_change
        self._silent = False
        self.var.trace_add("write", self._fire)

    def _fire(self, *_):
        if self._silent or not self._on_change:
            return
        self._on_change()

    def get(self):
        return parse_float(self.var.get())

    def set_value(self, text):
        """Atualiza o valor exibido sem disparar o recálculo (evita loop)."""
        self._silent = True
        self.var.set(text)
        self._silent = False

    def set_enabled(self, enabled: bool):
        self._entry.configure(state="normal" if enabled else "disabled")


class ComboField(ttk.Frame):
    """Rótulo + combobox (somente leitura), com callback ao vivo na seleção."""

    def __init__(self, master, label, valores, default, on_change=None, width=14):
        super().__init__(master, style="Card.TFrame")
        ttk.Label(self, text=label, style="Muted.TLabel").pack(anchor="w")
        self.var = tk.StringVar(value=default)
        combo = ttk.Combobox(
            self, textvariable=self.var, values=valores, state="readonly",
            style="Dark.TCombobox", font=FONT_MONO, width=width,
        )
        combo.pack(anchor="w", fill="x", pady=(4, 0))
        if on_change:
            combo.bind("<<ComboboxSelected>>", lambda *_: on_change())

    def get(self):
        return self.var.get()


class ResultPanel(ttk.Frame):
    """Painel tipo "display" que mostra o resultado em destaque, ao vivo."""

    def __init__(self, master, formula_text=""):
        super().__init__(master, style="Display.TFrame")
        self.formula = ttk.Label(self, text=formula_text, style="Formula.TLabel")
        self.formula.pack(anchor="w", padx=16, pady=(12, 0))

        self.rows = {}
        self.body = ttk.Frame(self, style="Display.TFrame")
        self.body.pack(fill="x", padx=16, pady=(6, 14))

        self.status = ttk.Label(self, text="", style="Status.TLabel")
        self.status.pack(anchor="w", padx=16, pady=(0, 12))

    def set_formula(self, texto):
        self.formula.configure(text=texto)

    def set_rows(self, pares):
        for widget in self.body.winfo_children():
            widget.destroy()
        for i, (rotulo, valor) in enumerate(pares):
            ttk.Label(self.body, text=rotulo, style="Muted.TLabel").grid(
                row=i, column=0, sticky="w", pady=3
            )
            ttk.Label(self.body, text=valor, style="Value.TLabel").grid(
                row=i, column=1, sticky="e", padx=(24, 0), pady=3
            )
        self.body.columnconfigure(1, weight=1)

    def set_status(self, texto, ok=True):
        self.status.configure(text=texto, foreground=OK if ok else ERROR)


class ModeToggle(tk.Frame):
    """Controle segmentado (pílula) para alternar entre modos de cálculo."""

    def __init__(self, master, opcoes, on_change=None):
        super().__init__(master, bg=BG_CARD, highlightbackground=BORDER,
                          highlightcolor=BORDER, highlightthickness=1, bd=0)
        self.on_change = on_change
        self.value = opcoes[0][0]
        self.buttons = {}
        for key, texto in opcoes:
            btn = tk.Button(
                self, text=texto, font=FONT_UI_BOLD, bd=0, relief="flat",
                padx=14, pady=8, cursor="hand2",
                command=lambda k=key: self.set_value(k),
            )
            btn.pack(side="left")
            self.buttons[key] = btn
        self.set_value(self.value, fire=False)

    def set_value(self, key, fire=True):
        self.value = key
        for k, btn in self.buttons.items():
            if k == key:
                btn.configure(bg=ACCENT, fg="#04222b")
            else:
                btn.configure(bg=BG_CARD, fg=TEXT_MUTED)
        if fire and self.on_change:
            self.on_change(key)

    def get(self):
        return self.value


# ----------------------------------------------------------------------
# Abas de cálculo
# ----------------------------------------------------------------------
class AbaJurosSimples(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style="Card.TFrame", padding=24)
        ttk.Label(self, text="Juros Simples", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="J = C · i · n     |     M = C + J     |     C = M / (1 + i·n)     |     n = (M/C − 1) / i",
            style="Muted.TLabel", wraplength=780, justify="left",
        ).pack(anchor="w", pady=(2, 4))
        ttk.Label(
            self,
            text="Taxa e prazo em escalas diferentes? O prazo é convertido automaticamente (proporção linear). "
                 "O campo do valor que está sendo calculado fica travado e se atualiza sozinho.",
            style="Muted.TLabel", wraplength=780, justify="left",
        ).pack(anchor="w", pady=(0, 14))

        self.modo = ModeToggle(
            self,
            [
                ("montante", "Calcular Montante"),
                ("capital", "Calcular Capital Inicial"),
                ("prazo", "Calcular Prazo"),
            ],
            on_change=lambda _k: self._trocar_modo(),
        )
        self.modo.pack(anchor="w", pady=(0, 16))

        linha1 = ttk.Frame(self, style="Card.TFrame")
        linha1.pack(fill="x")
        self.capital = Field(linha1, "Capital inicial (C)", "1000", self.calcular)
        self.capital.grid(row=0, column=0, padx=(0, 16))
        self.montante_in = Field(linha1, "Montante final (M)", "1240", self.calcular)
        self.montante_in.grid(row=0, column=1, padx=(0, 16))
        self.taxa = Field(linha1, "Taxa i (%)", "2", self.calcular)
        self.taxa.grid(row=0, column=2)

        linha2 = ttk.Frame(self, style="Card.TFrame")
        linha2.pack(fill="x", pady=(14, 0))
        self.periodo_taxa = ComboField(
            linha2, "Período da taxa", list(DIAS_POR_PERIODO.keys()), "Mensal", self.calcular
        )
        self.periodo_taxa.grid(row=0, column=0, padx=(0, 16))
        self.periodos = Field(linha2, "Prazo (n)", "12", self.calcular)
        self.periodos.grid(row=0, column=1, padx=(0, 16))
        self.periodo_prazo = ComboField(
            linha2, "Período do prazo", list(DIAS_POR_PERIODO.keys()), "Mensal", self.calcular
        )
        self.periodo_prazo.grid(row=0, column=2)

        self.resultado = ResultPanel(self, "J = C × i × n")
        self.resultado.pack(fill="x", pady=(24, 0))

        self._trocar_modo()

    def _trocar_modo(self):
        modo = self.modo.get()
        self.capital.set_enabled(modo != "capital")
        self.montante_in.set_enabled(modo != "montante")
        self.periodos.set_enabled(modo != "prazo")
        self.calcular()

    def calcular(self):
        modo = self.modo.get()
        periodo_taxa = self.periodo_taxa.get()
        periodo_prazo = self.periodo_prazo.get()
        i = self.taxa.get()

        if modo == "montante":
            c, n = self.capital.get(), self.periodos.get()
            self.resultado.set_formula("M = C × (1 + i × n)")
            if None in (c, i, n):
                self.montante_in.set_value("")
                self.resultado.set_rows([("Juros (J)", "—"), ("Montante (M)", "—")])
                self.resultado.set_status("Preencha todos os campos com números válidos.", ok=False)
                return
            n_efetivo = prazo_efetivo(n, periodo_taxa, periodo_prazo)
            i_frac = i / 100
            juros = c * i_frac * n_efetivo
            montante = c + juros
            self.montante_in.set_value(f"{montante:.2f}")
            rows = [("Juros (J)", fmt_moeda(juros)), ("Montante (M)", fmt_moeda(montante))]
            rows += linha_conversao(n_efetivo, periodo_taxa, periodo_prazo)

        elif modo == "capital":
            m, n = self.montante_in.get(), self.periodos.get()
            self.resultado.set_formula("C = M / (1 + i × n)")
            if None in (m, i, n):
                self.capital.set_value("")
                self.resultado.set_rows([("Capital inicial (C)", "—"), ("Juros (J)", "—")])
                self.resultado.set_status("Preencha todos os campos com números válidos.", ok=False)
                return
            n_efetivo = prazo_efetivo(n, periodo_taxa, periodo_prazo)
            i_frac = i / 100
            denom = 1 + i_frac * n_efetivo
            if denom == 0:
                self.capital.set_value("")
                self.resultado.set_rows([("Capital inicial (C)", "—"), ("Juros (J)", "—")])
                self.resultado.set_status("Combinação de taxa e prazo torna o denominador zero.", ok=False)
                return
            capital = m / denom
            juros = m - capital
            self.capital.set_value(f"{capital:.2f}")
            rows = [("Capital inicial (C)", fmt_moeda(capital)), ("Juros (J)", fmt_moeda(juros))]
            rows += linha_conversao(n_efetivo, periodo_taxa, periodo_prazo)

        else:  # prazo
            c, m = self.capital.get(), self.montante_in.get()
            self.resultado.set_formula("n = (M/C − 1) / i")
            if None in (c, m, i):
                self.periodos.set_value("")
                self.resultado.set_rows([("Prazo (n)", "—"), ("Juros (J)", "—")])
                self.resultado.set_status("Preencha todos os campos com números válidos.", ok=False)
                return
            i_frac = i / 100
            if c == 0 or i_frac == 0:
                self.periodos.set_value("")
                self.resultado.set_rows([("Prazo (n)", "—"), ("Juros (J)", "—")])
                self.resultado.set_status("Capital e taxa não podem ser zero para calcular o prazo.", ok=False)
                return
            n_efetivo = (m / c - 1) / i_frac  # em unidades do período da taxa
            n_no_prazo = prazo_efetivo(n_efetivo, periodo_prazo, periodo_taxa)
            juros = m - c
            self.periodos.set_value(f"{n_no_prazo:.4f}")
            rows = [
                (f"Prazo (n, em \"{periodo_prazo.lower()}\")", fmt_num(n_no_prazo)),
                ("Juros (J)", fmt_moeda(juros)),
            ]

        self.resultado.set_rows(rows)
        self.resultado.set_status("Calculado em tempo real ✓", ok=True)


class AbaJurosCompostos(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style="Card.TFrame", padding=24)
        ttk.Label(self, text="Juros Compostos", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="M = C · (1 + i)ⁿ     |     J = M − C     |     C = M / (1 + i)ⁿ     |     n = ln(M/C) / ln(1 + i)",
            style="Muted.TLabel", wraplength=780, justify="left",
        ).pack(anchor="w", pady=(2, 4))
        ttk.Label(
            self,
            text="Taxa e prazo em escalas diferentes? A conversão usa expoente — nunca multiplique/divida "
                 "uma taxa efetiva diretamente (3º pecado mortal). O campo calculado fica travado e se "
                 "atualiza sozinho.",
            style="Muted.TLabel", wraplength=780, justify="left",
        ).pack(anchor="w", pady=(0, 14))

        self.modo = ModeToggle(
            self,
            [
                ("montante", "Calcular Montante"),
                ("capital", "Calcular Capital Inicial"),
                ("prazo", "Calcular Prazo"),
            ],
            on_change=lambda _k: self._trocar_modo(),
        )
        self.modo.pack(anchor="w", pady=(0, 16))

        linha1 = ttk.Frame(self, style="Card.TFrame")
        linha1.pack(fill="x")
        self.capital = Field(linha1, "Capital inicial (C)", "10000", self.calcular)
        self.capital.grid(row=0, column=0, padx=(0, 16))
        self.montante_in = Field(linha1, "Montante final (M)", "11292.43", self.calcular)
        self.montante_in.grid(row=0, column=1, padx=(0, 16))
        self.taxa = Field(linha1, "Taxa i (%)", "20", self.calcular)
        self.taxa.grid(row=0, column=2)

        linha2 = ttk.Frame(self, style="Card.TFrame")
        linha2.pack(fill="x", pady=(14, 0))
        self.periodo_taxa = ComboField(
            linha2, "Período da taxa", list(DIAS_POR_PERIODO.keys()), "Anual", self.calcular
        )
        self.periodo_taxa.grid(row=0, column=0, padx=(0, 16))
        self.periodos = Field(linha2, "Prazo (n)", "8", self.calcular)
        self.periodos.grid(row=0, column=1, padx=(0, 16))
        self.periodo_prazo = ComboField(
            linha2, "Período do prazo", list(DIAS_POR_PERIODO.keys()), "Mensal", self.calcular
        )
        self.periodo_prazo.grid(row=0, column=2)

        self.resultado = ResultPanel(self, "M = C × (1 + i)ⁿ")
        self.resultado.pack(fill="x", pady=(24, 0))

        self._trocar_modo()

    def _trocar_modo(self):
        modo = self.modo.get()
        self.capital.set_enabled(modo != "capital")
        self.montante_in.set_enabled(modo != "montante")
        self.periodos.set_enabled(modo != "prazo")
        self.calcular()

    def calcular(self):
        modo = self.modo.get()
        periodo_taxa = self.periodo_taxa.get()
        periodo_prazo = self.periodo_prazo.get()
        i = self.taxa.get()

        if modo == "montante":
            c, n = self.capital.get(), self.periodos.get()
            self.resultado.set_formula("M = C × (1 + i)ⁿ")
            if None in (c, i, n):
                self.montante_in.set_value("")
                self.resultado.set_rows([("Juros (J)", "—"), ("Montante (M)", "—")])
                self.resultado.set_status("Preencha todos os campos com números válidos.", ok=False)
                return
            n_efetivo = prazo_efetivo(n, periodo_taxa, periodo_prazo)
            i_frac = i / 100
            try:
                montante = c * (1 + i_frac) ** n_efetivo
            except (OverflowError, ValueError):
                self.montante_in.set_value("")
                self.resultado.set_rows([("Juros (J)", "—"), ("Montante (M)", "—")])
                self.resultado.set_status("Não é possível calcular com esses valores.", ok=False)
                return
            juros = montante - c
            self.montante_in.set_value(f"{montante:.2f}")
            rows = [("Juros (J)", fmt_moeda(juros)), ("Montante (M)", fmt_moeda(montante))]
            rows += linha_conversao(n_efetivo, periodo_taxa, periodo_prazo)

        elif modo == "capital":
            m, n = self.montante_in.get(), self.periodos.get()
            self.resultado.set_formula("C = M / (1 + i)ⁿ")
            if None in (m, i, n):
                self.capital.set_value("")
                self.resultado.set_rows([("Capital inicial (C)", "—"), ("Juros (J)", "—")])
                self.resultado.set_status("Preencha todos os campos com números válidos.", ok=False)
                return
            n_efetivo = prazo_efetivo(n, periodo_taxa, periodo_prazo)
            i_frac = i / 100
            try:
                fator = (1 + i_frac) ** n_efetivo
                capital = m / fator
            except (OverflowError, ValueError, ZeroDivisionError):
                self.capital.set_value("")
                self.resultado.set_rows([("Capital inicial (C)", "—"), ("Juros (J)", "—")])
                self.resultado.set_status("Não é possível calcular com esses valores.", ok=False)
                return
            juros = m - capital
            self.capital.set_value(f"{capital:.2f}")
            rows = [("Capital inicial (C)", fmt_moeda(capital)), ("Juros (J)", fmt_moeda(juros))]
            rows += linha_conversao(n_efetivo, periodo_taxa, periodo_prazo)

        else:  # prazo
            c, m = self.capital.get(), self.montante_in.get()
            self.resultado.set_formula("n = ln(M/C) / ln(1 + i)")
            if None in (c, m, i):
                self.periodos.set_value("")
                self.resultado.set_rows([("Prazo (n)", "—"), ("Juros (J)", "—")])
                self.resultado.set_status("Preencha todos os campos com números válidos.", ok=False)
                return
            i_frac = i / 100
            if c <= 0 or m <= 0 or i_frac <= -1:
                self.periodos.set_value("")
                self.resultado.set_rows([("Prazo (n)", "—"), ("Juros (J)", "—")])
                self.resultado.set_status("Capital, montante e (1 + taxa) precisam ser positivos.", ok=False)
                return
            try:
                n_efetivo = math.log(m / c) / math.log(1 + i_frac)  # em unidades do período da taxa
            except (ValueError, ZeroDivisionError):
                self.periodos.set_value("")
                self.resultado.set_rows([("Prazo (n)", "—"), ("Juros (J)", "—")])
                self.resultado.set_status("Não é possível calcular o prazo com esses valores (taxa 0%?).", ok=False)
                return
            n_no_prazo = prazo_efetivo(n_efetivo, periodo_prazo, periodo_taxa)
            juros = m - c
            self.periodos.set_value(f"{n_no_prazo:.4f}")
            rows = [
                (f"Prazo (n, em \"{periodo_prazo.lower()}\")", fmt_num(n_no_prazo)),
                ("Juros (J)", fmt_moeda(juros)),
            ]

        self.resultado.set_rows(rows)
        self.resultado.set_status("Calculado em tempo real ✓", ok=True)


class AmortizationTable(ttk.Frame):
    """Tabela de amortização (Sistema Price), com scroll vertical."""

    COLUNAS = [
        ("n", "Nº", 46, "center"),
        ("prestacao", "Prestação", 110, "e"),
        ("juros", "Juros", 110, "e"),
        ("amortizacao", "Amortização", 120, "e"),
        ("saldo", "Saldo Devedor", 130, "e"),
    ]

    def __init__(self, master):
        super().__init__(master, style="Card.TFrame")
        container = ttk.Frame(self, style="Card.TFrame")
        container.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            container, columns=[c[0] for c in self.COLUNAS], show="headings",
            style="Dark.Treeview", height=8,
        )
        for chave, rotulo, largura, ancora in self.COLUNAS:
            self.tree.heading(chave, text=rotulo)
            self.tree.column(chave, width=largura, anchor=ancora)

        vsb = ttk.Scrollbar(
            container, orient="vertical", command=self.tree.yview, style="Dark.Vertical.TScrollbar"
        )
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        self.info = ttk.Label(self, text="", style="Muted.TLabel", wraplength=780, justify="left")
        self.info.pack(anchor="w", pady=(8, 0))

    def set_rows(self, linhas):
        self.tree.delete(*self.tree.get_children())
        for linha in linhas:
            self.tree.insert("", "end", values=linha)

    def clear(self, mensagem=""):
        self.tree.delete(*self.tree.get_children())
        self.info.configure(text=mensagem)

    def set_info(self, texto):
        self.info.configure(text=texto)


class AbaPrice(ttk.Frame):
    """Sistema Price (parcelas/prestações constantes).

    PV = PMT · (1 − (1+i)⁻ⁿ) / i   —   a taxa i deve estar na mesma
    periodicidade das parcelas (use a aba Equivalência de Taxas para
    converter antes, se a taxa informada estiver em outra escala).
    """

    def __init__(self, master):
        super().__init__(master, style="Card.TFrame")

        # A aba tem bastante conteúdo (campos + resultado + tabela). Para
        # nunca cortar a tabela quando a janela for menor, tudo fica dentro
        # de um canvas com rolagem vertical em vez de direto no frame.
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview,
                             style="Dark.Vertical.TScrollbar")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        body = ttk.Frame(canvas, style="Card.TFrame", padding=24)
        window_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def _ajustar_scrollregion(_e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        body.bind("<Configure>", _ajustar_scrollregion)

        def _ajustar_largura(e):
            canvas.itemconfig(window_id, width=e.width)
        canvas.bind("<Configure>", _ajustar_largura)

        def _rolar(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _rolar))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

        ttk.Label(body, text="Sistema Price", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            body,
            text="PMT = PV · i / (1 − (1+i)⁻ⁿ)     |     PV = PMT · (1 − (1+i)⁻ⁿ) / i     —     "
                 "parcelas constantes. Se a taxa estiver numa escala diferente da parcela (ex.: taxa "
                 "anual, parcelas mensais), a conversão para a taxa equivalente da parcela é automática. "
                 "Carência > 0 adia o início das parcelas — os juros do período podem capitalizar "
                 "(aumentam o saldo) ou ser pagos à parte (saldo não muda).",
            style="Muted.TLabel", wraplength=780, justify="left",
        ).pack(anchor="w", pady=(2, 14))

        self.modo = ModeToggle(
            body,
            [
                ("pmt", "Calcular Prestação"),
                ("pv", "Calcular Valor Presente"),
                ("prazo", "Calcular Prazo (n)"),
                ("taxa", "Calcular Taxa (i)"),
            ],
            on_change=lambda _k: self._trocar_modo(),
        )
        self.modo.pack(anchor="w", pady=(0, 16))

        conv_row = ttk.Frame(body, style="Card.TFrame")
        conv_row.pack(anchor="w", pady=(0, 16))
        ttk.Label(conv_row, text="Parcelas:", style="Muted.TLabel").pack(side="left", padx=(0, 10))
        self.convencao = ModeToggle(
            conv_row,
            [
                ("postecipada", "Postecipada (fim do período · END)"),
                ("antecipada", "Antecipada (início do período · BEGIN)"),
            ],
            on_change=lambda _k: self.calcular(),
        )
        self.convencao.pack(side="left")

        carencia_row = ttk.Frame(body, style="Card.TFrame")
        carencia_row.pack(anchor="w", pady=(0, 16))
        ttk.Label(carencia_row, text="Carência:", style="Muted.TLabel").pack(side="left", padx=(0, 10))
        self.tipo_carencia = ModeToggle(
            carencia_row,
            [
                ("capitaliza", "Capitaliza os juros"),
                ("paga_juros", "Paga só os juros no período"),
            ],
            on_change=lambda _k: self.calcular(),
        )
        self.tipo_carencia.pack(side="left")

        linha1 = ttk.Frame(body, style="Card.TFrame")
        linha1.pack(fill="x")
        self.pv = Field(linha1, "Valor Presente (PV)", "10000", self.calcular)
        self.pv.grid(row=0, column=0, padx=(0, 16))
        self.pmt = Field(linha1, "Prestação (PMT)", "1101.03", self.calcular)
        self.pmt.grid(row=0, column=1, padx=(0, 16))
        self.taxa = Field(linha1, "Taxa i (%)", "2", self.calcular)
        self.taxa.grid(row=0, column=2, padx=(0, 16))
        self.periodo_taxa = ComboField(
            linha1, "Período da taxa", list(DIAS_POR_PERIODO.keys()), "Mensal", self.calcular
        )
        self.periodo_taxa.grid(row=0, column=3)

        linha2 = ttk.Frame(body, style="Card.TFrame")
        linha2.pack(fill="x", pady=(14, 0))
        self.periodos = Field(linha2, "Prazo (n)", "10", self.calcular)
        self.periodos.grid(row=0, column=0, padx=(0, 16))
        self.periodo_parcela = ComboField(
            linha2, "Período das parcelas", list(DIAS_POR_PERIODO.keys()), "Mensal", self.calcular
        )
        self.periodo_parcela.grid(row=0, column=1, padx=(0, 16))
        self.carencia = Field(linha2, "Carência (nº de parcelas sem amortizar)", "0", self.calcular)
        self.carencia.grid(row=0, column=2)

        self.resultado = ResultPanel(body, "PMT = PV × i / (1 − (1+i)⁻ⁿ)")
        self.resultado.pack(fill="x", pady=(20, 0))

        ttk.Label(body, text="Tabela de amortização", style="SubSection.TLabel").pack(
            anchor="w", pady=(20, 6)
        )
        self.tabela = AmortizationTable(body)
        self.tabela.pack(fill="both", expand=True)

        self._trocar_modo()

    def _trocar_modo(self):
        modo = self.modo.get()
        self.pv.set_enabled(modo != "pv")
        self.pmt.set_enabled(modo != "pmt")
        self.taxa.set_enabled(modo != "taxa")
        self.periodos.set_enabled(modo != "prazo")
        self.calcular()

    def _atualizar_tabela(self, pv_original, pmt, i_frac, n, antecipada, carencia, tipo_carencia):
        if n is None or n <= 0 or abs(n - round(n)) > 1e-6:
            self.tabela.clear("A tabela só é exibida quando o prazo é um número inteiro de parcelas.")
            return
        n_int = int(round(n))
        c_int = int(round(carencia))
        if n_int + c_int > 600:
            self.tabela.clear("Prazo grande demais para exibir a tabela (máximo de 600 linhas).")
            return
        linhas = []
        saldo = pv_original

        for k in range(1, c_int + 1):
            if tipo_carencia == "capitaliza":
                # Sem pagamento: os juros do período incorporam ao saldo devedor.
                juros_k = saldo * i_frac
                saldo += juros_k
                linhas.append((f"C{k}", "—", fmt_moeda(juros_k), "—", fmt_moeda(saldo)))
            else:
                # "Paga só os juros": o saldo não muda durante a carência.
                juros_k = saldo * i_frac
                linhas.append((f"C{k}", fmt_moeda(juros_k), fmt_moeda(juros_k), fmt_moeda(0), fmt_moeda(saldo)))

        for k in range(1, n_int + 1):
            # Na convenção antecipada, a 1ª parcela é paga no ato (t=0),
            # antes de qualquer juro incidir sobre o saldo.
            juros_k = 0.0 if (antecipada and k == 1) else saldo * i_frac
            amort_k = pmt - juros_k
            saldo -= amort_k
            linhas.append((c_int + k, fmt_moeda(pmt), fmt_moeda(juros_k), fmt_moeda(amort_k), fmt_moeda(saldo)))

        self.tabela.set_rows(linhas)
        carencia_info = f"{c_int} período(s) de carência + " if c_int > 0 else ""
        self.tabela.set_info(
            f"{carencia_info}{n_int} parcela(s) de {fmt_moeda(pmt)}  ·  saldo devedor final: {fmt_moeda(saldo)}"
        )

    def calcular(self):
        modo = self.modo.get()
        antecipada = self.convencao.get() == "antecipada"
        tipo_car = self.tipo_carencia.get()
        sufixo = "  ×  (1+i)  [antecipada]" if antecipada else ""
        pv, pmt, i, n = self.pv.get(), self.pmt.get(), self.taxa.get(), self.periodos.get()
        carencia_val = self.carencia.get()
        periodo_taxa = self.periodo_taxa.get()
        periodo_parcela = self.periodo_parcela.get()

        def linha_taxa_equivalente(i_frac_parcela):
            if periodo_taxa == periodo_parcela:
                return []
            return [(f"Taxa equivalente ({periodo_parcela.lower()})", fmt_pct(i_frac_parcela * 100))]

        def carencia_invalida():
            return (carencia_val is None or carencia_val < 0
                    or abs(carencia_val - round(carencia_val)) > 1e-6)

        if modo == "pmt":
            self.resultado.set_formula("PMT = PV × i / (1 − (1+i)⁻ⁿ)" + sufixo)
            if None in (pv, i, n) or carencia_invalida():
                self.pmt.set_value("")
                self.tabela.clear("Preencha os campos para ver a tabela.")
                self.resultado.set_rows([("Prestação (PMT)", "—")])
                self.resultado.set_status(
                    "Preencha todos os campos (carência precisa ser um inteiro ≥ 0).", ok=False
                )
                return
            i_frac = i / 100
            if periodo_taxa != periodo_parcela:
                i_frac = taxa_equivalente(i_frac, periodo_taxa, periodo_parcela)
            if n <= 0:
                self.pmt.set_value("")
                self.resultado.set_rows([("Prestação (PMT)", "—")])
                self.resultado.set_status("O prazo deve ser maior que zero.", ok=False)
                return
            c = int(round(carencia_val))
            fator_tempo = (1 + i_frac) if antecipada else 1.0
            try:
                pv_para_formula = pv * (1 + i_frac) ** c if tipo_car == "capitaliza" else pv
            except OverflowError:
                self.pmt.set_value("")
                self.resultado.set_rows([("Prestação (PMT)", "—")])
                self.resultado.set_status("Carência grande demais para esses valores.", ok=False)
                return
            if i_frac == 0:
                pmt_calc = pv_para_formula / n
            else:
                fator = (1 - (1 + i_frac) ** (-n)) * fator_tempo
                if fator == 0:
                    self.pmt.set_value("")
                    self.resultado.set_rows([("Prestação (PMT)", "—")])
                    self.resultado.set_status("Combinação de taxa e prazo inválida.", ok=False)
                    return
                pmt_calc = pv_para_formula * i_frac / fator
            self.pmt.set_value(f"{pmt_calc:.2f}")
            juros_carencia = 0.0 if tipo_car == "capitaliza" else c * pv * i_frac
            total_pago = pmt_calc * n + juros_carencia
            rows = [
                ("Prestação (PMT)", fmt_moeda(pmt_calc)),
                ("Total pago", fmt_moeda(total_pago)),
                ("Total de juros", fmt_moeda(total_pago - pv)),
            ]
            if c > 0 and tipo_car == "paga_juros":
                rows.insert(1, ("Juros pagos na carência (cada período)", fmt_moeda(pv * i_frac)))
            rows += linha_taxa_equivalente(i_frac)
            self.resultado.set_rows(rows)
            self.resultado.set_status("Calculado em tempo real ✓", ok=True)
            self._atualizar_tabela(pv, pmt_calc, i_frac, n, antecipada, c, tipo_car)

        elif modo == "pv":
            self.resultado.set_formula("PV = PMT × (1 − (1+i)⁻ⁿ) / i" + sufixo)
            if None in (pmt, i, n) or carencia_invalida():
                self.pv.set_value("")
                self.tabela.clear("Preencha os campos para ver a tabela.")
                self.resultado.set_rows([("Valor Presente (PV)", "—")])
                self.resultado.set_status(
                    "Preencha todos os campos (carência precisa ser um inteiro ≥ 0).", ok=False
                )
                return
            i_frac = i / 100
            if periodo_taxa != periodo_parcela:
                i_frac = taxa_equivalente(i_frac, periodo_taxa, periodo_parcela)
            if n <= 0:
                self.pv.set_value("")
                self.resultado.set_rows([("Valor Presente (PV)", "—")])
                self.resultado.set_status("O prazo deve ser maior que zero.", ok=False)
                return
            c = int(round(carencia_val))
            fator_tempo = (1 + i_frac) if antecipada else 1.0
            if i_frac == 0:
                pv_no_fim_carencia = pmt * n
            else:
                pv_no_fim_carencia = pmt * (1 - (1 + i_frac) ** (-n)) / i_frac * fator_tempo
            try:
                if tipo_car == "capitaliza":
                    fator_carencia = (1 + i_frac) ** c
                    if fator_carencia == 0:
                        raise ZeroDivisionError
                    pv_calc = pv_no_fim_carencia / fator_carencia
                else:
                    pv_calc = pv_no_fim_carencia
            except (OverflowError, ZeroDivisionError):
                self.pv.set_value("")
                self.resultado.set_rows([("Valor Presente (PV)", "—")])
                self.resultado.set_status("Carência grande demais para esses valores.", ok=False)
                return
            self.pv.set_value(f"{pv_calc:.2f}")
            juros_carencia = 0.0 if tipo_car == "capitaliza" else c * pv_calc * i_frac
            total_pago = pmt * n + juros_carencia
            rows = [
                ("Valor Presente (PV)", fmt_moeda(pv_calc)),
                ("Total pago", fmt_moeda(total_pago)),
                ("Total de juros", fmt_moeda(total_pago - pv_calc)),
            ]
            if c > 0 and tipo_car == "paga_juros":
                rows.insert(1, ("Juros pagos na carência (cada período)", fmt_moeda(pv_calc * i_frac)))
            rows += linha_taxa_equivalente(i_frac)
            self.resultado.set_rows(rows)
            self.resultado.set_status("Calculado em tempo real ✓", ok=True)
            self._atualizar_tabela(pv_calc, pmt, i_frac, n, antecipada, c, tipo_car)

        elif modo == "prazo":
            self.resultado.set_formula(
                "n = −ln(1 − PV·i / (PMT" + (" × (1+i)" if antecipada else "") + ")) / ln(1 + i)"
            )
            self.tabela.clear("Tabela disponível apenas ao calcular Prestação ou Valor Presente.")
            if None in (pv, pmt, i) or carencia_invalida():
                self.periodos.set_value("")
                self.resultado.set_rows([("Prazo (n)", "—")])
                self.resultado.set_status(
                    "Preencha todos os campos (carência precisa ser um inteiro ≥ 0).", ok=False
                )
                return
            i_frac = i / 100
            if periodo_taxa != periodo_parcela:
                i_frac = taxa_equivalente(i_frac, periodo_taxa, periodo_parcela)
            if pmt <= 0:
                self.periodos.set_value("")
                self.resultado.set_rows([("Prazo (n)", "—")])
                self.resultado.set_status("A prestação deve ser maior que zero.", ok=False)
                return
            c = int(round(carencia_val))
            try:
                pv_para_formula = pv * (1 + i_frac) ** c if tipo_car == "capitaliza" else pv
            except OverflowError:
                self.periodos.set_value("")
                self.resultado.set_rows([("Prazo (n)", "—")])
                self.resultado.set_status("Carência grande demais para esses valores.", ok=False)
                return
            # Truque padrão de série antecipada: PV_antecipada = PV_postecipada × (1+i),
            # então basta usar o PMT "equivalente postecipado" na fórmula de sempre.
            pmt_equivalente = pmt * (1 + i_frac) if antecipada else pmt
            if i_frac == 0:
                n_calc = pv_para_formula / pmt_equivalente
            else:
                base = 1 - pv_para_formula * i_frac / pmt_equivalente
                if base <= 0:
                    self.periodos.set_value("")
                    self.resultado.set_rows([("Prazo (n)", "—")])
                    self.resultado.set_status(
                        "Essa prestação não cobre nem os juros do período (prazo infinito).", ok=False
                    )
                    return
                n_calc = -math.log(base) / math.log(1 + i_frac)
            self.periodos.set_value(f"{n_calc:.4f}")
            juros_carencia = 0.0 if tipo_car == "capitaliza" else c * pv * i_frac
            rows = [
                ("Prazo (n)", fmt_num(n_calc)),
                ("Total pago (aprox.)", fmt_moeda(pmt * n_calc + juros_carencia)),
            ]
            rows += linha_taxa_equivalente(i_frac)
            self.resultado.set_rows(rows)
            self.resultado.set_status("Calculado em tempo real ✓", ok=True)

        else:  # taxa — sem fórmula fechada: busca numérica (bisseção)
            self.resultado.set_formula(
                "i tal que PV = PMT · (1 − (1+i)⁻ⁿ) / i" + sufixo + "   (busca numérica)"
            )
            self.tabela.clear("Tabela disponível apenas ao calcular Prestação ou Valor Presente.")
            if None in (pv, pmt, n) or carencia_invalida():
                self.taxa.set_value("")
                self.resultado.set_rows([("Taxa (i)", "—")])
                self.resultado.set_status(
                    "Preencha todos os campos (carência precisa ser um inteiro ≥ 0).", ok=False
                )
                return
            if pv <= 0 or pmt <= 0 or n <= 0:
                self.taxa.set_value("")
                self.resultado.set_rows([("Taxa (i)", "—")])
                self.resultado.set_status("PV, PMT e prazo devem ser maiores que zero.", ok=False)
                return
            c = int(round(carencia_val))

            def pv_teorico(i_frac):
                fator_tempo = (1 + i_frac) if antecipada else 1.0
                try:
                    if abs(i_frac) < 1e-12:
                        pv_no_fim = pmt * n * fator_tempo
                    else:
                        pv_no_fim = pmt * (1 - (1 + i_frac) ** (-n)) / i_frac * fator_tempo
                    if tipo_car == "capitaliza":
                        pv_no_fim = pv_no_fim / (1 + i_frac) ** c
                    return pv_no_fim
                except (OverflowError, ZeroDivisionError):
                    return math.inf if i_frac < 0 else 0.0

            lo, hi = -0.999999, 10.0
            f_lo, f_hi = pv_teorico(lo) - pv, pv_teorico(hi) - pv
            if f_lo * f_hi > 0:
                self.taxa.set_value("")
                self.resultado.set_rows([("Taxa (i)", "—")])
                self.resultado.set_status(
                    "Não foi possível encontrar uma taxa nesse intervalo (−99,9999% a 1.000%).", ok=False
                )
                return
            for _ in range(200):
                meio = (lo + hi) / 2
                f_meio = pv_teorico(meio) - pv
                if abs(f_meio) < 1e-9:
                    lo = hi = meio
                    break
                if (f_lo < 0) == (f_meio < 0):
                    lo, f_lo = meio, f_meio
                else:
                    hi, f_hi = meio, f_meio
            i_frac_parcela = (lo + hi) / 2
            i_frac_exibir = (
                i_frac_parcela if periodo_taxa == periodo_parcela
                else taxa_equivalente(i_frac_parcela, periodo_parcela, periodo_taxa)
            )

            self.taxa.set_value(f"{i_frac_exibir * 100:.6f}")
            juros_carencia = 0.0 if tipo_car == "capitaliza" else c * pv * i_frac_parcela
            total_pago = pmt * n + juros_carencia
            rows = [
                ("Taxa (i)", fmt_pct(i_frac_exibir * 100, casas=6)),
                ("Total pago", fmt_moeda(total_pago)),
                ("Total de juros", fmt_moeda(total_pago - pv)),
            ]
            if periodo_taxa != periodo_parcela:
                rows.append((f"Taxa por parcela ({periodo_parcela.lower()})", fmt_pct(i_frac_parcela * 100, casas=6)))
            self.resultado.set_rows(rows)
            self.resultado.set_status("Calculado em tempo real ✓ (busca numérica)", ok=True)


class AbaEquivalencia(ttk.Frame):
    """Equivalência de taxas (regime composto), com foco em % ao mês.

    Converte qualquer periodicidade em dias (convenção comercial 30/360,
    ver DIAS_POR_PERIODO) e aplica:
        i_destino = (1 + i_origem) ** (dias_destino / dias_origem) - 1
    """

    def __init__(self, master):
        super().__init__(master, style="Card.TFrame", padding=24)
        ttk.Label(self, text="Equivalência de Taxas", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            self, text="(1 + i₁)^(1/t₁) = (1 + i₂)^(1/t₂)   —   convenção 30/360",
            style="Muted.TLabel"
        ).pack(anchor="w", pady=(2, 18))

        linha = ttk.Frame(self, style="Card.TFrame")
        linha.pack(fill="x")

        self.taxa = Field(linha, "Taxa conhecida (%)", "12", self.calcular)
        self.taxa.pack(side="left", padx=(0, 16))

        combo_origem = ttk.Frame(linha, style="Card.TFrame")
        combo_origem.pack(side="left", padx=(0, 16))
        ttk.Label(combo_origem, text="Período da taxa", style="Muted.TLabel").pack(anchor="w")
        self.periodo_origem = ttk.Combobox(
            combo_origem, values=list(DIAS_POR_PERIODO.keys()), state="readonly",
            style="Dark.TCombobox", font=FONT_MONO, width=14
        )
        self.periodo_origem.set("Anual")
        self.periodo_origem.pack(anchor="w", pady=(4, 0))
        self.periodo_origem.bind("<<ComboboxSelected>>", lambda *_: self.calcular())

        combo_destino = ttk.Frame(linha, style="Card.TFrame")
        combo_destino.pack(side="left")
        ttk.Label(combo_destino, text="Período desejado", style="Muted.TLabel").pack(anchor="w")
        self.periodo_destino = ttk.Combobox(
            combo_destino, values=list(DIAS_POR_PERIODO.keys()), state="readonly",
            style="Dark.TCombobox", font=FONT_MONO, width=14
        )
        self.periodo_destino.set("Mensal")
        self.periodo_destino.pack(anchor="w", pady=(4, 0))
        self.periodo_destino.bind("<<ComboboxSelected>>", lambda *_: self.calcular())

        self.resultado = ResultPanel(self, "i_destino = (1 + i_origem)^(dias_destino / dias_origem) − 1")
        self.resultado.pack(fill="x", pady=(24, 0))

        self.calcular()

    def calcular(self):
        i = self.taxa.get()
        if i is None:
            self.resultado.set_rows([("Taxa equivalente", "—")])
            self.resultado.set_status("Informe uma taxa válida.", ok=False)
            return

        i_destino = taxa_equivalente(i / 100, self.periodo_origem.get(), self.periodo_destino.get())

        self.resultado.set_rows([
            (f"Taxa equivalente ({self.periodo_destino.get()})", fmt_pct(i_destino * 100)),
        ])
        self.resultado.set_status("Calculado em tempo real ✓", ok=True)


# ----------------------------------------------------------------------
# Janela principal / navegação lateral
# ----------------------------------------------------------------------
class NavButton(tk.Button):
    def __init__(self, master, icon, text, command):
        super().__init__(
            master, text=f"  {icon}   {text}", command=command,
            font=FONT_NAV, anchor="w", bd=0, relief="flat",
            bg=BG_SIDEBAR, fg=TEXT_MUTED, activebackground=BG_CARD,
            activeforeground=TEXT, highlightthickness=0, padx=14, pady=12,
            cursor="hand2",
        )
        self.selected = False
        self.bind("<Enter>", self._hover_in)
        self.bind("<Leave>", self._hover_out)

    def _hover_in(self, _e):
        if not self.selected:
            self.configure(bg=BG_CARD, fg=TEXT)

    def _hover_out(self, _e):
        if not self.selected:
            self.configure(bg=BG_SIDEBAR, fg=TEXT_MUTED)

    def set_selected(self, sel: bool):
        self.selected = sel
        if sel:
            self.configure(bg=BG_CARD, fg=ACCENT, font=(FONT_NAV[0], FONT_NAV[1], "bold"))
        else:
            self.configure(bg=BG_SIDEBAR, fg=TEXT_MUTED, font=FONT_NAV)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora Financeira · Finanças Corporativas")
        self.geometry("960x720")
        self.minsize(880, 620)
        self.configure(bg=BG)

        self._setup_style()

        # --- topo -----------------------------------------------------
        header = tk.Frame(self, bg=BG, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="⚡ CALCULADORA FINANCEIRA", font=FONT_TITLE,
            bg=BG, fg=TEXT, padx=24
        ).pack(side="left")
        tk.Label(
            header, text="MBA Gestão Empresarial · FGV", font=FONT_UI,
            bg=BG, fg=TEXT_MUTED, padx=24
        ).pack(side="right")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # --- corpo: sidebar + conteúdo ---------------------------------
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=BG_SIDEBAR, width=210)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        content = tk.Frame(body, bg=BG)
        content.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self.frames = {
            "simples": AbaJurosSimples(content),
            "compostos": AbaJurosCompostos(content),
            "price": AbaPrice(content),
            "equivalencia": AbaEquivalencia(content),
        }
        for frame in self.frames.values():
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.nav_buttons = {}
        botoes = [
            ("simples", "📈", "Juros Simples"),
            ("compostos", "📊", "Juros Compostos"),
            ("price", "🏦", "Sistema Price"),
            ("equivalencia", "🔄", "Equivalência de Taxas"),
        ]
        for key, icon, texto in botoes:
            btn = NavButton(sidebar, icon, texto, command=lambda k=key: self.mostrar(k))
            btn.pack(fill="x", pady=(14 if key == "simples" else 2, 2), padx=8)
            self.nav_buttons[key] = btn

        tk.Frame(sidebar, bg=BG_SIDEBAR).pack(fill="both", expand=True)
        tk.Label(
            sidebar, text="Todos os campos\nrecalculam ao vivo.",
            font=("Segoe UI", 8), bg=BG_SIDEBAR, fg=TEXT_MUTED, justify="left",
        ).pack(anchor="w", padx=20, pady=16)

        self.mostrar("simples")

    def mostrar(self, key):
        for k, btn in self.nav_buttons.items():
            btn.set_selected(k == key)
        self.frames[key].tkraise()

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Card.TFrame", background=BG)
        style.configure("Display.TFrame", background=BG_CARD)

        style.configure("TLabel", background=BG, foreground=TEXT, font=FONT_UI)
        style.configure("Muted.TLabel", background=BG, foreground=TEXT_MUTED, font=FONT_UI)
        style.configure("Section.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 16))
        style.configure("SubSection.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 12))
        style.configure("Formula.TLabel", background=BG_CARD, foreground=ACCENT, font=FONT_MONO)
        style.configure("Status.TLabel", background=BG_CARD, foreground=OK, font=("Segoe UI", 9))
        style.configure("Value.TLabel", background=BG_CARD, foreground=TEXT, font=FONT_MONO_BIG)

        # Fundo do painel "display" com borda sutil
        style.configure(
            "Display.TFrame", background=BG_CARD, relief="flat",
        )
        style.configure(
            "Dark.TEntry",
            fieldbackground=BG_ENTRY, background=BG_ENTRY, foreground=ACCENT,
            insertcolor=ACCENT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
            relief="flat", padding=8,
        )
        style.map(
            "Dark.TEntry",
            fieldbackground=[("focus", BG_ENTRY), ("disabled", BG_CARD)],
            bordercolor=[("focus", ACCENT), ("disabled", BORDER)],
            foreground=[("disabled", TEXT_MUTED)],
        )

        style.configure(
            "Dark.TCombobox",
            fieldbackground=BG_ENTRY, background=BG_ENTRY, foreground=ACCENT,
            arrowcolor=ACCENT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
            relief="flat", padding=6,
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", BG_ENTRY)],
            foreground=[("readonly", ACCENT)],
        )
        self.option_add("*TCombobox*Listbox.background", BG_ENTRY)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT_DIM)
        self.option_add("*TCombobox*Listbox.font", FONT_MONO)

        style.configure(
            "Dark.Treeview",
            background=BG_ENTRY, fieldbackground=BG_ENTRY, foreground=TEXT,
            bordercolor=BORDER, borderwidth=0, rowheight=24, font=FONT_MONO,
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=BG_CARD, foreground=ACCENT, font=FONT_UI_BOLD,
            bordercolor=BORDER, relief="flat",
        )
        style.map(
            "Dark.Treeview",
            background=[("selected", ACCENT_DIM)],
            foreground=[("selected", TEXT)],
        )
        style.map("Dark.Treeview.Heading", background=[("active", BG_CARD)])
        style.layout("Dark.Treeview", style.layout("Treeview"))

        style.configure(
            "Dark.Vertical.TScrollbar",
            background=BG_CARD, troughcolor=BG, bordercolor=BORDER,
            arrowcolor=TEXT_MUTED, relief="flat",
        )
        style.map("Dark.Vertical.TScrollbar", background=[("active", ACCENT_DIM)])


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
