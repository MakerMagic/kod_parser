"""Recover only font-proven glyphs; raw page strings and spans stay unchanged."""

import io
import re
import struct
from hashlib import sha256

from pdfminer.pdffont import TrueTypeFont
from pdfminer.pdftypes import resolve1


def round_outline(raw, ttf, cid):
    """Recognize a small filled circle from its native TrueType contour, not CID."""
    try:
        head = ttf.tables[b"head"][0]
        em = struct.unpack_from(">H", raw, head + 18)[0]
        fmt = struct.unpack_from(">h", raw, head + 50)[0]
        size = 4 if fmt else 2
        code = ">II" if fmt else ">HH"
        begin, end = struct.unpack_from(code, raw, ttf.tables[b"loca"][0] + size * cid)
        scale = 1 if fmt else 2
        if begin == end:
            return None
        start = ttf.tables[b"glyf"][0] + begin * scale
        contours, x0, y0, x1, y1 = struct.unpack_from(">hhhhh", raw, start)
        w, h = x1 - x0, y1 - y0
        if (
            contours != 1
            or min(w, h) <= 0
            or not 0.9 <= w / h <= 1.1
            or max(w, h) > em * 0.6
        ):
            return None
        count = struct.unpack_from(">H", raw, start + 10)[0] + 1
        if not 8 <= count <= 40:
            return None
        instructions = struct.unpack_from(">H", raw, start + 12)[0]
        pos = start + 14 + instructions
        flags = []
        while len(flags) < count:
            flag = raw[pos]
            pos += 1
            copies = 1
            if flag & 8:
                copies += raw[pos]
                pos += 1
            flags.extend([flag] * copies)
        if len(flags) != count or sum(not f & 1 for f in flags) < 4:
            return None
        axes = []
        for short, same in ((2, 16), (4, 32)):
            values, coordinate = [], 0
            for flag in flags:
                if flag & short:
                    delta = raw[pos] * (1 if flag & same else -1)
                    pos += 1
                elif flag & same:
                    delta = 0
                else:
                    delta = struct.unpack_from(">h", raw, pos)[0]
                    pos += 2
                coordinate += delta
                values.append(coordinate)
            axes.append(values)
        radii = [
            ((x - (x0 + x1) / 2) / (w / 2)) ** 2 + ((y - (y0 + y1) / 2) / (h / 2)) ** 2
            for x, y in zip(*axes)
        ]
        if not all(0.8 <= r <= 1.6 for r in radii):
            return None
        return {
            "cid": cid,
            "contours": contours,
            "point_count": count,
            "bbox": [x0, y0, x1, y1],
            "units_per_em": em,
            "method": "single_small_filled_round_native_contour",
        }
    except (KeyError, IndexError, struct.error, ZeroDivisionError):
        return None


def font_maps(page):
    maps, evidence = {}, []
    for ref in page.page_obj.resources.get("Font", {}).values():
        spec = resolve1(ref)
        if not spec.get("DescendantFonts"):
            continue
        descendant = resolve1(resolve1(spec["DescendantFonts"])[0])
        descriptor = resolve1(descendant.get("FontDescriptor", {}))
        stream = resolve1(descriptor.get("FontFile2"))
        if not stream or str(descendant.get("CIDToGIDMap")) != "/'Identity'":
            continue
        raw = stream.get_data()
        ttf = TrueTypeFont("embedded", io.BytesIO(raw))
        name = str(spec.get("BaseFont")).strip("/'")
        mapping = {}
        try:
            mapping.update(ttf.create_unicode_map().cid2unichr)
        except TrueTypeFont.CMapNotFound:
            pass
        # Positive-advance, zero-outline glyphs are spacing glyphs. This fixes
        # unmapped typographic spaces without guessing a glyph from its CID.
        if all(
            k in ttf.tables
            for k in (b"head", b"loca", b"glyf", b"hmtx", b"hhea", b"maxp")
        ):
            head = ttf.tables[b"head"][0]
            count = struct.unpack_from(">H", raw, ttf.tables[b"maxp"][0] + 4)[0]
            fmt = struct.unpack_from(">h", raw, head + 50)[0]
            metrics = struct.unpack_from(">H", raw, ttf.tables[b"hhea"][0] + 34)[0]
            loca = ttf.tables[b"loca"][0]
            locations = struct.unpack_from(
                ">" + ("I" if fmt else "H") * (count + 1), raw, loca
            )
            for cid in range(count):
                advance = struct.unpack_from(
                    ">H", raw, ttf.tables[b"hmtx"][0] + 4 * min(cid, metrics - 1)
                )[0]
                glyph = ttf.tables[b"glyf"][0] + locations[cid] * (1 if fmt else 2)
                zero_area = locations[cid] != locations[cid + 1] and struct.unpack_from(
                    ">hhhh", raw, glyph + 2
                ) == (0, 0, 0, 0)
                if (
                    cid
                    and (locations[cid] == locations[cid + 1] or zero_area)
                    and advance > 0
                ):
                    mapping.setdefault(cid, " ")
        circles = []
        if all(k in ttf.tables for k in (b"head", b"maxp", b"loca", b"glyf")):
            count = struct.unpack_from(">H", raw, ttf.tables[b"maxp"][0] + 4)[0]
            circles = [
                proof
                for cid in range(count)
                if cid not in mapping and (proof := round_outline(raw, ttf, cid))
            ]
        maps[name] = mapping
        evidence.append(
            {
                "font": name,
                "embedded_sha256": sha256(raw).hexdigest(),
                "method": "embedded_unicode_cmap_or_positive_advance_zero_ink_outline",
                **({"unmapped_round_glyphs": circles} if circles else {}),
            }
        )
    return maps, evidence


def annotate_lines(page, lines, shifted, decode_shifted):
    maps, evidence = font_maps(page)
    circles = {
        (e["font"], f"(cid:{p['cid']})")
        for e in evidence
        for p in e.get("unmapped_round_glyphs", [])
    }
    list_markers = {}
    for i, line in enumerate(lines):
        prefix = re.match(r"^\s*(\(cid:\d+\))\s+\S", line["text"])
        if not prefix or i == 0 or not lines[i - 1]["text"].rstrip().endswith(":"):
            continue
        run = []
        for candidate in lines[i:]:
            if (
                not candidate["text"].lstrip().startswith(prefix[1])
                or abs(candidate["x0"] - line["x0"]) > 2
            ):
                break
            glyphs = [
                c
                for c in page.chars
                if c["text"] == prefix[1]
                and candidate["top"] - 0.1 <= c["top"]
                and c["bottom"] <= candidate["bottom"] + 0.1
            ]
            if not glyphs or not all(
                (c["fontname"], c["text"]) in circles for c in glyphs
            ):
                break
            run.append(candidate)
        if len(run) >= 2:
            for candidate in run:
                list_markers[id(candidate)] = prefix[1]
    unknown = {}
    for c in page.chars:
        if not re.fullmatch(r"\(cid:\d+\)", c["text"]):
            continue
        value = maps.get(c["fontname"], {}).get(int(c["text"][5:-1]))
        if value is not None:
            unknown.setdefault((c["text"], c["fontname"]), value)
    for line in lines:
        chars = [
            c
            for c in page.chars
            if line["top"] - 0.1 <= c["top"]
            and c["bottom"] <= line["bottom"] + 0.1
            and line["x0"] - 0.1 <= c["x0"]
            and c["x1"] <= line["x1"] + 0.1
        ]
        local = {}
        for c in chars:
            if (c["text"], c["fontname"]) in unknown:
                local.setdefault(c["text"], set()).add(
                    unknown[(c["text"], c["fontname"])]
                )
        substitutions = {k: next(iter(v)) for k, v in local.items() if len(v) == 1}
        if id(line) in list_markers:
            substitutions[list_markers[id(line)]] = "•"
            line["list_marker_evidence"] = (
                "repeated_initial_filled_round_native_glyph_after_list_lead_in"
            )

        def decode(value, substitutions=substitutions):
            value = re.sub(
                r"\(cid:\d+\)",
                lambda token: substitutions.get(token[0], token[0]),
                value,
            )
            return decode_shifted(value) if shifted else value

        line["readable_text"] = decode(line["text"])
        line["word_texts"] = [decode(t) for t in line["word_texts"]]
        line["cid_substitutions"] = {
            m[0]: decode(m[0])
            for m in re.finditer(r"\(cid:\d+\)", line["text"])
            if decode(m[0]) != m[0]
        }
    return evidence


def decode_block(value, lines):
    """Exact whole-line interpretation avoids assuming a font for a full page."""

    def decode(text):
        line = next(
            (
                l
                for l in lines
                if l["text"] == text or text and l["text"].endswith(text)
            ),
            None,
        )
        if line is None:
            return text
        return re.sub(
            r"\(cid:\d+\)",
            lambda m: line.get("cid_substitutions", {}).get(m[0], m[0]),
            text,
        )

    return "\n".join(decode(t) for t in value.split("\n"))
