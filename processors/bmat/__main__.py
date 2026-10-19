"""Thin BMAT stage entrypoint; each implementation remains independently runnable."""

import argparse
import importlib

from .contracts import STAGES


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("stage", choices=[*STAGES, "inspect", "report", "list"])
    args, remaining = cli.parse_known_args(argv)
    if args.stage in {"inspect", "report", "list"}:
        return importlib.import_module("parsers.bmat.backtest").main(
            [args.stage, *remaining]
        )
    module = STAGES[args.stage]["module"]
    if module is None:
        cli.error(
            f"BMAT {args.stage} is intentionally not implemented: RAW review must finish first. Contract: {STAGES[args.stage]}"
        )
    return importlib.import_module(module + ".__main__").main(remaining)


if __name__ == "__main__":
    raise SystemExit(main())
