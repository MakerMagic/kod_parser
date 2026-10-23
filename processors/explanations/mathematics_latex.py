r"""Explanation-only TeX syntax validation; never rewrites stored LaTeX.

RAW's deliberately restricted grammar is not an explanation grammar. TeX permits
single-token arguments such as \frac12 and ordinary solution notation such as
binomial coefficients, integrals, sums and boxed results.
"""

import re
from xml.etree.ElementTree import Element

from parsers.mathematics.latex import InvalidLatex, Reader


class ExplanationReader(Reader):
    SYMBOLS = {
        "boxed": None, "binom": None,
        "implies": "⇒", "longrightarrow": "⟶", "ge": "≥", "le": "≤",
        "quad": " ", "qquad": " ", "diamond": "◇", "lfloor": "⌊",
        "rfloor": "⌋", "int": "∫", "sum": "∑", "cdots": "⋯",
        "gcd": "gcd", "mid": "∣", "lvert": "|", "rvert": "|",
        "infty": "∞", "lim": "lim", "therefore": "∴", "Rightarrow": "⇒",
        "$": "$",
        "#": "#",
        "lg": "lg",
        "ell": "ℓ", "rho": "ρ",
    }

    def __init__(self, text):
        # TeX consumes one character for an unbraced argument, including digits.
        self.tokens = re.findall(r"\\[a-zA-Z]+|\\.|[^\s]", text)
        self.i = 0

    def group(self):
        if self.i < len(self.tokens) and self.tokens[self.i] == "{":
            self.i += 1
            return self.row("}")
        return self.atom()

    def atom(self):
        token = self.tokens[self.i] if self.i < len(self.tokens) else None
        if token in {r"\boxed", r"\operatorname", r"\mathbin", r"\overline", r"\vec", r"\pmod"}:
            self.i += 1
            return self.group()
        if token == r"\binom":
            self.i += 1
            node = Element("mrow")
            node.extend([self.group(), self.group()])
            return node
        if token in {r"\tfrac", r"\dfrac"}:
            self.tokens[self.i] = r"\frac"
        elif token and token.startswith("\\") and token[1:] in self.SYMBOLS:
            self.i += 1
            node = Element("mo")
            node.text = self.SYMBOLS[token[1:]]
            return node
        return super().atom()


def validate(formula):
    if not isinstance(formula, str) or not formula.strip():
        return ["Empty formula"]
    if re.search(r"\\[\[\]()]|(?<!\\)\$|\(cid:", formula):
        return ["Delimiters/extraction artifacts inside a formula block"]
    try:
        ExplanationReader(formula).row()
    except InvalidLatex as error:
        return [str(error)]
    return []
