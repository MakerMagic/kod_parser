"""Shared text/asset primitives for simulation and report, from the same record."""

import base64
import mimetypes
import re
from html import escape

from .storage import ROOT, InvalidInput, Store


def text(value):
    return "<p class='text'>" + escape(str(value)) + "</p>"


class QuestionContent:
    def __init__(self, question, *, root=ROOT):
        self.question = question
        self.store = Store(root)
        self.assets = {a["id"]: a for a in question["assets"]}
        self.images = {}

    def figure(self, identifier, *, caption=True):
        if identifier not in self.assets:
            raise ValueError(
                f"Cannot render {self.question['id']}: asset {identifier} is absent"
            )
        asset = self.assets[identifier]
        if identifier not in self.images:
            try:
                path = self.store.check(asset)
                self.store.relative(path)
                mime = mimetypes.guess_type(path.name)[0]
                if mime not in {"image/png", "image/jpeg", "image/webp"}:
                    raise ValueError("unsupported saved image format")
                self.images[identifier] = (
                    "data:"
                    + mime
                    + ";base64,"
                    + base64.b64encode(path.read_bytes()).decode("ascii")
                )
            except (OSError, ValueError) as error:
                if isinstance(error, InvalidInput):
                    raise InvalidInput(
                        error.code,
                        f"Cannot render {self.question['id']} asset {identifier}: {error}",
                    ) from error
                raise ValueError(
                    f"Cannot render {self.question['id']} asset {identifier}: {error}"
                ) from error
        alt = asset["role"] + (
            " " + asset["option_label"] if asset.get("option_label") else ""
        )
        return (
            "<figure><img alt='"
            + escape(alt, quote=True)
            + "' src='"
            + self.images[identifier]
            + "'>"
            + (
                "<figcaption>"
                + escape(alt)
                + " · page "
                + escape(str(asset.get("page")))
                + "</figcaption>"
                if caption
                else ""
            )
            + "</figure>"
        )

    def body(self, *, caption=True):
        return "".join(
            text(b["text"])
            if b["type"] == "text"
            else self.figure(b["asset_id"], caption=caption)
            for b in self.question["main_body"]
        )

    def answer(self, answer, *, caption=True):
        return text(answer["text"]) + (
            ""
            if answer.get("render_text_only")
            else "".join(self.figure(i, caption=caption) for i in answer["asset_ids"])
        )

    def explanation(self):
        explanation = self.question["explanation"]
        if explanation is None:
            return text("Not supplied by the accepted upstream source.")
        parts = []
        for block in explanation["blocks"]:
            if block["type"] == "paragraph":
                parts.append(text(block["text"]))
            elif block["type"] == "visual":
                parts.append(self.figure(block["asset_id"]))
            else:
                tag = "ol" if block.get("ordered") else "ul"
                items = []
                for item in block["items"]:
                    label, value = item.get("label"), item["text"]
                    prefix = (
                        label + ": "
                        if label
                        and not re.match(
                            r"^" + re.escape(label) + r"\s*[-–—.:)]", value
                        )
                        else ""
                    )
                    items.append("<li class='text'>" + escape(prefix + value) + "</li>")
                parts.append("<" + tag + ">" + "".join(items) + "</" + tag + ">")
                if block.get("transition"):
                    transition = block["transition"]
                    parts.append(
                        text(
                            transition["text"]
                            if isinstance(transition, dict)
                            else transition
                        )
                    )
        return "".join(parts)
