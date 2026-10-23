"""Source glyph accounting with explicit fraction, radical and script geometry."""

import unicodedata
from itertools import pairwise

from .latex import SYMBOLS, validate

COMMANDS = {value: "\\" + key + " " for key, value in SYMBOLS.items()}
SUPERS = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-"))
SUBS = dict(zip("₀₁₂₃₄₅₆₇₈₉", "0123456789"))


class UncertainFormula(ValueError):
    pass


def bounds(items):
    return [
        min(c["x0"] for c in items),
        min(c["top"] for c in items),
        max(c["x1"] for c in items),
        max(c["bottom"] for c in items),
    ]


def glyph(text):
    decomposition = unicodedata.normalize("NFKD", text)
    if "⁄" in decomposition and text != "⁄":
        numerator, denominator = decomposition.split("⁄")
        if numerator.isdigit() and denominator.isdigit():
            return r"\frac{" + numerator + "}{" + denominator + "}"
    if text in COMMANDS:
        return COMMANDS[text]
    if text in SUPERS:
        return "^{" + SUPERS[text] + "}"
    if text in SUBS:
        return "_{" + SUBS[text] + "}"
    if text in {"%", "{", "}"}:
        return "\\" + text
    if text in {"−", "–"}:
        return "-"
    if text in {"√", "∛", "∜"} or "(cid:" in text or "�" in text:
        raise UncertainFormula("Unresolved radical/glyph mapping")
    # Unicode mathematical alphabet compatibility is representational only.
    if any("MATHEMATICAL" in unicodedata.name(c, "") for c in text):
        return unicodedata.normalize("NFKC", text)
    if any(unicodedata.category(c) in {"Co", "Cc"} for c in text):
        raise UncertainFormula("Unmapped glyph")
    return text


def radical_bar(root, chars, rules):
    """Find the source vinculum, allowing stretched font boxes and inner bars."""
    top = min(c["top"] for c in chars)
    scale = max(c["size"] for c in chars)
    bars = [
        r
        for r in rules
        if root["x0"] < r["x0"] <= root["x1"] + 2
        and top - scale <= r["top"] <= root["top"] + root["size"] * 0.25
        and r["x1"] > root["x1"]
        and not any(
            parent["x0"] < root["x0"] - 0.8
            and parent["x1"] >= root["x1"]
            and r["bottom"] < parent["top"] < root["top"]
            for parent in rules
        )
    ]
    if bars:
        highest = min(r["top"] for r in bars)
        upper = [r for r in bars if abs(r["top"] - highest) < 0.2]
        if len(upper) == 1 and all(
            upper[0]["x0"] - 0.8 <= r["x0"] and r["x1"] <= upper[0]["x1"] + 0.8
            for r in bars
        ):
            return upper[0]
    raise UncertainFormula("Radical extent is not uniquely supported by an overbar")


def formula_bounds(chars, rules):
    """Include supported rules outside font metrics in crops and stored geometry."""
    box = bounds(chars)
    padding = (
        max(1, max(c["size"] for c in chars) * 0.3)
        if any(c.get("geometry_order") for c in chars)
        else 1
    )
    supported = [
        r
        for r in rules
        if box[0] - padding <= r["x0"]
        and r["x1"] <= box[2] + padding
        and box[1] <= r["top"] <= box[3]
    ]
    for c in chars:
        if c["text"] == "√":
            try:
                supported.append(radical_bar(c, chars, rules))
            except UncertainFormula:
                pass
    if supported:
        box = bounds([*chars, *supported])
    return box


def rule_contains(c, rule):
    """Legacy font side bearings may overhang the actual fraction-rule ink."""
    if "pdf_text_x0" in c:
        return (
            rule["x0"] - 0.8 <= c["pdf_text_x0"]
            and c["pdf_text_x1"] <= rule["x1"] + 0.8
        )
    padding = max(0.8, c["size"] * 0.18) if c.get("geometry_order") else 0.8
    return rule["x0"] - padding <= c["x0"] and c["x1"] <= rule["x1"] + padding


def literal_radicand(root_index, chars):
    """Read an unbarred source √ only with explicit, adjacent inline scope."""
    root = chars[root_index]
    tail = list(range(root_index + 1, len(chars)))
    if not tail:
        raise UncertainFormula("Missing literal radical operand")
    previous = root
    accepted = []
    stack = []
    grouped = chars[tail[0]]["text"] in {"(", "["}
    for j in tail:
        c = chars[j]
        if (
            abs(c["bottom"] - root["bottom"]) > root["size"] * 0.1
            or abs(c["size"] - root["size"]) > root["size"] * 0.1
            or not -1 <= c["x0"] - previous["x1"] <= root["size"] * 0.65
        ):
            break
        value = c["text"]
        if grouped:
            if value in {"(", "["}:
                stack.append(value)
            elif value in {")", "]"} and (
                not stack or stack.pop() != ("(" if value == ")" else "[")
            ):
                break
            accepted.append(j)
            if not stack:
                return accepted
        elif value.isdigit():
            accepted.append(j)
        else:
            break
        previous = c
    if accepted and not grouped:
        return accepted
    raise UncertainFormula("Literal radical scope is not explicitly supported")


def assembled_delimiters(chars):
    """Assemble evidenced Adobe Symbol delimiter pieces, including extensions."""
    result = list(chars)
    for pieces, value in (
        (("\uf8f1", "\uf8f2", "\uf8f3"), "{"),
        (("\uf8fc", "\uf8fd", "\uf8fe"), "}"),
        (("\uf8eb", "\uf8ec", "\uf8ed"), "("),
        (("\uf8f6", "\uf8f7", "\uf8f8"), ")"),
    ):
        for top in [c for c in result if c["text"] == pieces[0]]:
            bottoms = [
                c
                for c in result
                if c["text"] == pieces[2]
                and abs(c["x0"] - top["x0"]) < 1
                and c["top"] > top["top"]
            ]
            if not bottoms:
                continue
            bottom = min(bottoms, key=lambda c: c["top"])
            middle = sorted(
                (
                    c
                    for c in result
                    if c["text"] == pieces[1]
                    and abs(c["x0"] - top["x0"]) < 1
                    and top["top"] < c["top"] < bottom["top"]
                ),
                key=lambda c: c["top"],
            )
            group = [top, *middle, bottom]
            if not middle or any(
                b["top"] > a["bottom"] + a["size"] * 0.3 for a, b in pairwise(group)
            ):
                continue
            box = bounds(group)
            delimiter = {
                **top,
                "text": value,
                "x0": box[0],
                "top": box[1],
                "x1": box[2],
                "bottom": box[3],
                "assembled_delimiter": True,
                "pdf_baseline": middle[len(middle) // 2].get(
                    "pdf_baseline", middle[len(middle) // 2]["bottom"]
                ),
            }
            at = min(result.index(c) for c in group)
            result = [c for c in result if c not in group]
            result.insert(at, delimiter)
    return result


def equation_system(chars, rules, depth):
    braces = [c for c in chars if c["text"] == "{"]
    if len(braces) != 1 or any(c["text"] == "}" for c in chars):
        return None
    brace = braces[0]
    relations = sorted(
        (c for c in chars if c["text"] in "=<>≤≥"), key=lambda c: c["top"]
    )
    rows = []
    for relation in relations:
        baseline = relation.get("pdf_baseline", relation["bottom"])
        if not rows or baseline - rows[-1] > relation["size"] * 0.8:
            rows.append(baseline)
    if len(rows) < 2:
        return None
    if not all(c["x0"] >= brace["x0"] for c in chars):
        raise UncertainFormula("System brace does not enclose a unique row group")
    cuts = [(a + b) / 2 for a, b in pairwise(rows)]
    groups = [[] for _ in rows]
    for c in chars:
        if c is brace:
            continue
        middle = (c["top"] + c["bottom"]) / 2
        groups[sum(middle > cut for cut in cuts)].append(c)
    if any(not any(c["text"] in "=<>≤≥" for c in group) for group in groups):
        raise UncertainFormula("System rows do not each have an observed relation")
    return (
        r"\begin{cases}"
        + r"\\".join(reconstruct(group, rules, depth + 1) for group in groups)
        + r"\end{cases}"
    )


def reconstruct(chars, rules, depth=0):
    chars = [c for c in chars if c["text"].strip()]
    if not chars or depth > 10:
        raise UncertainFormula("Empty or excessively nested expression")
    chars = assembled_delimiters(chars)
    system = equation_system(chars, rules, depth)
    if system:
        return system
    box = bounds(chars)
    scale = max(c["size"] for c in chars)
    structures = []
    for i, slash in enumerate(chars):
        if slash["text"] != "⁄":
            continue
        # A source fraction slash can be emitted after both operands. Use its
        # raised-left/lowered-right geometry, never PDF stream order or solving.
        numerator = [
            j
            for j, c in enumerate(chars)
            if c["text"].isdigit()
            and 0.15 * slash["size"] < slash["top"] - c["top"] < slash["size"]
            and slash["x0"] - slash["size"]
            < c["x1"]
            <= slash["x0"] + slash["size"] * 0.2
        ]
        denominator = [
            j
            for j, c in enumerate(chars)
            if c["text"].isdigit()
            and 0.15 * slash["size"] < c["bottom"] - slash["bottom"] < slash["size"]
            and slash["x1"] - slash["size"] * 0.2
            <= c["x0"]
            < slash["x1"] + slash["size"]
        ]
        if len(numerator) != 1 or len(denominator) != 1:
            raise UncertainFormula(
                "Fraction slash operands are not uniquely supported by glyph geometry"
            )
        structures.append(
            ("fraction", [i, *numerator, *denominator], numerator, denominator, slash)
        )
    for rule in rules:
        y = (rule["top"] + rule["bottom"]) / 2
        padding = (
            max(1, scale * 0.3) if any(c.get("geometry_order") for c in chars) else 1
        )
        if not (box[0] - padding <= rule["x0"] and rule["x1"] <= box[2] + padding):
            continue
        inside = [(i, c) for i, c in enumerate(chars) if rule_contains(c, rule)]
        num = [
            i
            for i, c in inside
            if c.get("pdf_baseline", c["bottom"]) <= y + 0.8
            and 0 < y - c["top"] < scale * 3
        ]
        den = [
            i
            for i, c in inside
            if c["top"] >= y - 0.8 and 0 < c["bottom"] - y < scale * 3
        ]
        if num and den:
            structures.append(("fraction", num + den, num, den, rule))
    for i, c in enumerate(chars):
        if c["text"] != "√":
            continue
        try:
            r = radical_bar(c, chars, rules)
        except UncertainFormula:
            # Explicit source syntax is sufficient only when there is no nearby
            # drawn bar. Never bypass ambiguous or clipped vinculum evidence.
            if any(
                c["x0"] < rule["x0"] <= c["x1"] + 2
                and c["top"] - scale <= rule["top"] <= c["bottom"]
                for rule in rules
            ):
                raise
            rad = literal_radicand(i, chars)
            structures.append(("root", [i, *rad], rad, [], c))
            continue
        # A stretched radical's PDF font box need not enclose its radicand.
        # Use the vinculum's full span and an enclosing fraction's separator,
        # rather than clipping against ordinary glyph line height.
        lower = min(
            (
                other["top"]
                for other in rules
                if other["x0"] < c["x0"] - 0.8
                and other["x1"] >= r["x1"] - 0.8
                and other["top"] > r["bottom"]
            ),
            default=float("inf"),
        )
        rad = [
            j
            for j, x in enumerate(chars)
            if j != i
            and rule_contains(x, r)
            and r["bottom"] - 1 <= x["top"]
            and x["bottom"] <= lower + 0.8
        ]
        index = [
            j
            for j, x in enumerate(chars)
            if j != i
            and x["size"] < c["size"] * 0.87
            and c["x0"] - c["size"] * 0.5 <= x["x0"]
            and x.get("pdf_text_x1", x["x1"]) < r["x0"] + 0.5
            and x["top"]
            < (
                c["bottom"] - c["size"] * 0.5
                if c.get("method") == "connected_vector_radical"
                else c["top"]
            )
            and x.get("pdf_baseline", x["bottom"]) < c["bottom"] - c["size"] * 0.4
        ]
        if not rad:
            raise UncertainFormula("No glyph-supported radicand")
        delimiter_stack = []
        for j in (
            sorted(rad, key=lambda j: chars[j]["x0"])
            if any(x.get("geometry_order") for x in chars)
            else rad
        ):
            value = chars[j]["text"]
            if value in {"(", "["}:
                delimiter_stack.append(value)
            elif value in {")", "]"} and (
                not delimiter_stack
                or delimiter_stack.pop() != ("(" if value == ")" else "[")
            ):
                raise UncertainFormula(
                    "Radicand delimiter boundary is not fully supported by vinculum geometry"
                )
        if delimiter_stack:
            raise UncertainFormula(
                "Radicand delimiter boundary is not fully supported by vinculum geometry"
            )
        structures.append(("root", [i, *rad, *index], rad, index, r))
    used = set()
    tokens = []
    for kind, owned, first, second, rule in sorted(
        structures, key=lambda s: -len(s[1])
    ):
        if used.intersection(owned):
            continue
        nested = [r for r in rules if r is not rule]
        a = reconstruct([chars[i] for i in first], nested, depth + 1)
        if kind == "fraction":
            b = reconstruct([chars[i] for i in second], nested, depth + 1)
            value = r"\frac{" + a + "}{" + b + "}"
        else:
            index = (
                reconstruct([chars[i] for i in second], nested, depth + 1)
                if second
                else ""
            )
            value = r"\sqrt" + ("[" + index + "]" if index else "") + "{" + a + "}"
        owned_box = bounds([chars[i] for i in owned])
        token_scale = max(chars[i]["size"] for i in owned)
        y = (rule["top"] + rule["bottom"]) / 2
        baseline = (
            chars[owned[0]].get("baseline", chars[owned[0]]["bottom"])
            if kind == "root"
            else y + token_scale * 0.5
        )
        tokens.append(
            {
                "value": value,
                "order": min(owned),
                "x0": owned_box[0],
                "x1": owned_box[2],
                "top": baseline - token_scale,
                "bottom": baseline,
                "size": token_scale,
            }
        )
        used.update(owned)
    for i, c in enumerate(chars):
        if i not in used:
            tokens.append({**c, "value": glyph(c["text"]), "order": i})
    tokens.sort(
        key=lambda t: (
            (t["x0"], t["top"])
            if any(c.get("geometry_order") for c in chars)
            else (t["order"],)
        )
    )
    result = []
    i = 0
    baselines = []
    while i < len(tokens):
        base = tokens[i]
        value = base["value"]
        if not base.get("assembled_delimiter") and value != "∫":
            baselines.append(base.get("pdf_baseline", base["bottom"]))
        j = i + 1
        for kind in ("^", "_"):
            script = []
            while j < len(tokens) and base["value"] != "∫":
                t = tokens[j]
                if t["value"] in {",", ";"}:
                    break
                shifted = (
                    t["bottom"] < base["bottom"] - base["size"] * 0.2
                    and t["top"] <= base["top"] + base["size"] * 0.15
                    if kind == "^"
                    else t["bottom"] > base["bottom"] + base["size"] * 0.15
                )
                if "pdf_baseline" in t and "pdf_baseline" in base:
                    shifted = (
                        t["pdf_baseline"] < base["pdf_baseline"] - base["size"] * 0.15
                        if kind == "^"
                        else t["pdf_baseline"]
                        > base["pdf_baseline"] + base["size"] * 0.15
                    )
                if not (
                    t["size"] <= base["size"] * 0.87
                    and shifted
                    and t.get("pdf_text_x0", t["x0"])
                    >= base.get("pdf_text_x1", base["x1"]) - 1
                ):
                    break
                script.append(t["value"])
                j += 1
            if script:
                value += kind + "{" + "".join(script) + "}"
        result.append(value)
        i = j
    if len(baselines) > 1 and max(baselines) - min(baselines) > scale * 0.45:
        if any(c["text"] == "∫" for c in chars):
            raise UncertainFormula(
                "Native integral limits and integrand require unsupported multi-baseline grouping"
            )
        raise UncertainFormula(
            "Unexplained multiple baselines / possible system or matrix"
        )
    return "".join(result)


def recover(chars, rules):
    try:
        latex = reconstruct(chars, rules)
        errors = validate(latex)
        if errors:
            return None, "malformed_latex", "; ".join(errors)
        return latex, None, None
    except (UncertainFormula, RecursionError) as error:
        return None, "uncertain_formula", str(error)
