"""Hash-checked canonical references and owned output, independent of parsers."""

import json
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "pre_final_v1"


class InvalidInput(ValueError):
    def __init__(self, code, detail=""):
        super().__init__(detail or code)
        self.code = code


def digest(value):
    return sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


class Store:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.documents = {}
        self.hashes = {}
        self.paths = {}

    def path(self, value):
        key = str(value)
        if key not in self.paths:
            self.paths[key] = (self.root / value).resolve()
        return self.paths[key]

    def relative(self, value):
        try:
            return self.path(value).relative_to(self.root).as_posix()
        except ValueError as error:
            raise InvalidInput("reference_outside_workspace", str(value)) from error

    def check(self, reference):
        path = self.path(reference["path"])
        if path not in self.hashes:
            try:
                self.hashes[path] = sha256(path.read_bytes()).hexdigest()
            except OSError as error:
                raise InvalidInput("reference_missing", self.relative(path)) from error
        if reference.get("sha256") != self.hashes[path]:
            raise InvalidInput("reference_changed", self.relative(path))
        return path

    def load(self, path):
        path = self.path(path)
        if path not in self.documents:
            data = path.read_bytes()
            self.hashes[path] = sha256(data).hexdigest()
            self.documents[path] = json.loads(data)
        return self.documents[path]

    def record(self, reference):
        path = self.check(reference)
        value = self.load(path)
        try:
            for token in reference["json_pointer"].strip("/").split("/"):
                token = token.replace("~1", "/").replace("~0", "~")
                value = value[int(token)] if isinstance(value, list) else value[token]
        except (KeyError, IndexError, ValueError, TypeError) as error:
            raise InvalidInput("record_reference_invalid") from error
        if (
            reference.get("record_sha256")
            and digest(value) != reference["record_sha256"]
        ):
            raise InvalidInput("record_reference_changed")
        return value

    def reference(self, path, pointer=None):
        path = self.path(path)
        if path not in self.hashes:
            self.hashes[path] = sha256(path.read_bytes()).hexdigest()
        result = {"path": self.relative(path), "sha256": self.hashes[path]}
        if pointer is not None:
            result["json_pointer"] = pointer
        return result


def write_owned(path, data, root=ROOT):
    """Never overwrite upstream directories or an unrelated existing artifact."""
    path, root = Path(path).resolve(), Path(root).resolve()
    protected = [
        root / "data" / n for n in ("input", "raw", "clean", "merged", "categorized")
    ]
    if any(path.is_relative_to(p) for p in protected):
        raise ValueError("Pre-final output cannot overwrite an upstream directory")
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("owner") != OWNER or old.get("stage") != data["stage"]:
            raise ValueError("Refusing to overwrite unrelated output")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
