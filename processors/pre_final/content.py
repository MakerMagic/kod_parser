"""Project accepted content into one asset-linked representation, without recovery."""

from copy import deepcopy

from .storage import InvalidInput


class Content:
    def __init__(self, store, question, matched):
        self.store, self.question, self.matched = store, question, matched
        self.assets = []
        self.by_id = {}
        self.raw_parent = store.path(question["raw_reference"]["path"]).parent
        self.clean_parent = store.path(matched["question_reference"]["path"]).parent

    def asset(self, original, role, option_label=None, *, explanation=False):
        if original.get("warnings"):
            raise InvalidInput("asset_issue", str(original["warnings"]))
        chosen = original.get("clean_asset") if role == "option" else None
        chosen = chosen or original
        if explanation:
            ref = self.matched.get("answer_reference")
            if not ref:
                raise InvalidInput("explanation_asset_reference_missing")
            base = self.store.path(ref["path"]).parent
        else:
            base = (
                self.clean_parent
                if chosen.get("path_base") == "clean_json_parent"
                else self.raw_parent
            )
        reference = chosen.get("path", chosen.get("local_path"))
        if not reference or "://" in reference:
            raise InvalidInput("asset_reference_missing")
        path = (base / reference).resolve()
        self.store.check({"path": str(path), "sha256": chosen.get("sha256")})
        identifier = original.get("image_id") or f"{role}:{len(self.assets) + 1}"
        if identifier in self.by_id:
            previous = self.by_id[identifier]
            if (previous["role"], previous["option_label"], previous["path"]) != (
                role,
                option_label,
                self.store.relative(path),
            ):
                raise InvalidInput("asset_association_conflict", identifier)
            return identifier
        item = {
            "id": identifier,
            "path": self.store.relative(path),
            "sha256": chosen["sha256"],
            "role": role,
            "option_label": option_label,
            "order": len(self.assets) + 1,
            "page": original.get("page"),
            "bbox": deepcopy(original.get("bbox")),
        }
        for key in ("axis_labels", "provenance"):
            if original.get(key):
                item[key] = deepcopy(original[key])
        self.assets.append(item)
        self.by_id[identifier] = item
        return identifier

    def question_content(self):
        q = self.question
        indexed = {a["image_id"]: a for a in q.get("visual_assets", [])}
        used = set()
        body = []
        for block in q["main_body"]:
            if block["type"] == "text":
                body.append({"type": "text", "text": block["text"]})
            elif block["type"] == "visual":
                identifier = block.get("asset_id")
                if identifier not in indexed:
                    raise InvalidInput("body_asset_missing", str(identifier))
                body.append(
                    {
                        "type": "visual",
                        "asset_id": self.asset(indexed[identifier], "body"),
                    }
                )
                used.add(identifier)
            else:
                raise InvalidInput("unsupported_body_block", block["type"])
        options = []
        for option in q["options"]:
            refs = []
            for image in option.get("images", []):
                if image.get("option_label") not in (None, option["label"]):
                    raise InvalidInput("option_asset_association_invalid")
                refs.append(self.asset(image, "option", option["label"]))
                used.add(image.get("image_id"))
            row = {
                "label": option["label"],
                "text": option.get("text", ""),
                "asset_ids": refs,
            }
            # This is an upstream validated rendering instruction, not re-normalization.
            if option.get("render_text_only"):
                row["render_text_only"] = True
            options.append(row)
        if set(indexed) - used:
            raise InvalidInput(
                "unplaced_question_asset", ",".join(sorted(set(indexed) - used))
            )
        for preview in q.get("visual_previews", []):
            self.asset(preview, "source_preview")
        return body, options

    def explanation(self, final):
        if final.get("status") == "unavailable":
            return None
        if final.get("status") != "available" or not final.get("blocks"):
            raise InvalidInput("explanation_state_invalid")
        answer = self.matched.get("answer") or {}
        source_assets = answer.get("explanation", {}).get("visual_assets", [])
        blocks = []
        for block in final["blocks"]:
            kind = block["type"]
            keep = ("type", "text", "role", "ordered", "transition")
            row = {k: deepcopy(block[k]) for k in keep if k in block}
            if kind == "list":
                row["items"] = [
                    {k: deepcopy(item[k]) for k in ("text", "label") if k in item}
                    for item in block["items"]
                ]
            elif kind == "visual":
                candidates = [
                    a
                    for a in source_assets
                    if (
                        block.get("asset_index") is not None
                        and a.get("asset_index") == block["asset_index"]
                    )
                    or (
                        block.get("source_url")
                        and a.get("source_url") == block["source_url"]
                    )
                ]
                if len(candidates) != 1:
                    raise InvalidInput("explanation_visual_unresolved")
                row["asset_id"] = self.asset(
                    candidates[0], "explanation", explanation=True
                )
            elif kind != "paragraph":
                raise InvalidInput("unsupported_explanation_block", kind)
            blocks.append(row)
        ref = final.get("source_reference")
        source_reference = None
        if ref:
            source_reference = self.store.reference(ref["path"])
            source_reference.update(
                {k: deepcopy(v) for k, v in ref.items() if k not in ("path", "sha256")}
            )
        provenance = {
            "source_type": final.get("source_type", "source_or_manual"),
            "source_reference": source_reference,
        }
        doc = answer.get("source_document") or {}
        provenance["source_document"] = {
            k: deepcopy(doc[k])
            for k in ("filename", "sha256", "source_url", "origin")
            if k in doc
        }
        if answer.get("provenance"):
            provenance["attribution"] = deepcopy(answer["provenance"])
        ai = self.matched.get("ai_explanation")
        if ai:
            provenance["ai_generation"] = deepcopy(ai)
        return {"blocks": blocks, "provenance": provenance}
