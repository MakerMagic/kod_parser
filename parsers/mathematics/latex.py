"""Conservative LaTeX subset validation and offline native MathML rendering."""

import re
from xml.etree.ElementTree import Element, tostring

SYMBOLS = {
    "neq": "≠",
    "leq": "≤",
    "geq": "≥",
    "pm": "±",
    "times": "×",
    "div": "÷",
    "cdot": "·",
    "infty": "∞",
    "pi": "π",
    "alpha": "α",
    "beta": "β",
    "theta": "θ",
    "gamma": "γ",
    "Delta": "Δ",
    "delta": "δ",
    "lambda": "λ",
    "mu": "μ",
    "sigma": "σ",
    "angle": "∠",
    "triangle": "△",
    "circ": "°",
    "in": "∈",
    "notin": "∉",
    "cup": "∪",
    "cap": "∩",
    "subset": "⊂",
    "subseteq": "⊆",
    "approx": "≈",
    "to": "→",
    "ldots": "…",
    "parallel": "∥",
    "perp": "⊥",
    "equiv": "≡",
}
FUNCTIONS = {"sin", "cos", "tan", "cot", "log", "ln", "sec", "csc"}


class InvalidLatex(ValueError):
    pass


class Reader:
    def __init__(self, text):
        self.tokens = re.findall(r"\\[a-zA-Z]+|\\.|[0-9]+(?:\.[0-9]+)?|[^\s]", text)
        self.i = 0

    def take(self):
        if self.i >= len(self.tokens):
            raise InvalidLatex("Unexpected end of formula")
        t = self.tokens[self.i]
        self.i += 1
        return t

    def row(self, end=None):
        row = Element("mrow")
        while self.i < len(self.tokens):
            if end and self.tokens[self.i] == end:
                self.i += 1
                return row
            node = self.atom()
            if self.i < len(self.tokens) and self.tokens[self.i] in {"^", "_"}:
                scripts = {}
                while self.i < len(self.tokens) and self.tokens[self.i] in {"^", "_"}:
                    kind = self.take()
                    if kind in scripts:
                        raise InvalidLatex("Repeated script")
                    scripts[kind] = self.atom()
                wrapper = Element(
                    "msubsup"
                    if len(scripts) == 2
                    else "msup"
                    if "^" in scripts
                    else "msub"
                )
                wrapper.append(node)
                for key in ("_", "^"):
                    if key in scripts:
                        wrapper.append(scripts[key])
                node = wrapper
            row.append(node)
        if end:
            raise InvalidLatex("Unbalanced delimiter")
        return row

    def group(self):
        if self.take() != "{":
            raise InvalidLatex("Command requires a braced argument")
        return self.row("}")

    def atom(self):
        t = self.take()
        if t == "{":
            return self.row("}")
        if t in {"}", "^", "_", "$"}:
            raise InvalidLatex("Unexpected delimiter/script")
        if t == r"\frac":
            node = Element("mfrac")
            node.extend([self.group(), self.group()])
            return node
        if t == r"\sqrt":
            index = None
            if self.i < len(self.tokens) and self.tokens[self.i] == "[":
                self.i += 1
                index = self.row("]")
            node = Element("mroot" if index is not None else "msqrt")
            node.append(self.group())
            if index is not None:
                node.append(index)
            return node
        if t in {r"\mathrm", r"\text", r"\mathit", r"\mathbf"}:
            return self.group()
        if t.startswith("\\"):
            name = t[1:]
            if name in {"left", "right"}:
                return self.atom()
            if name in SYMBOLS:
                t = SYMBOLS[name]
            elif name in FUNCTIONS:
                t = name
            elif name in {"%", "{", "}", "[", "]", "|", ",", " ", ";", "!"}:
                t = name if name not in {",", ";", "!"} else " "
            else:
                raise InvalidLatex(f"Unsupported command: {name}")
        if any(ord(c) >= 0xE000 and ord(c) <= 0xF8FF for c in t) or "�" in t:
            raise InvalidLatex("Unmapped glyph")
        tag = "mn" if t[:1].isdigit() else "mi" if t.isalpha() else "mo"
        node = Element(tag)
        node.text = t
        return node


def mathml(latex, *, display=False):
    if not isinstance(latex, str) or not latex.strip():
        raise InvalidLatex("Empty formula")
    if re.search(r"\\[\[\]()]|\$|\(cid:", latex):
        raise InvalidLatex("Delimiters/extraction artifacts inside a formula block")
    root = Element(
        "math",
        xmlns="http://www.w3.org/1998/Math/MathML",
        display="block" if display else "inline",
    )
    root.append(Reader(latex).row())
    return tostring(root, encoding="unicode")


def validate(latex):
    try:
        mathml(latex)
        return []
    except InvalidLatex as error:
        return [str(error)]
