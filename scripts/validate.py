#!/usr/bin/env python3
"""
Validate a JSON instance against a JSON Schema (draft 2020-12 by default).

Reports EVERY error found (not just the first), each with:
  - instance location (JSON Pointer into the data)
  - the keyword that failed
  - a human-readable message
  - the schema location that produced the error

Usage:
    python validate.py <instance.json> <schema.json>
    python validate.py <instance.json> <schema.json> --json   # machine-readable output

Exit code: 0 if valid, 1 if invalid, 2 on usage/load error.

The draft is auto-detected from the schema's "$schema" keyword when present;
otherwise draft 2020-12 is assumed.
"""
import argparse
import json
import sys


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)


def pointer(error):
    """Build a JSON Pointer string for the instance location of an error."""
    parts = list(error.absolute_path)
    if not parts:
        return ""  # root
    return "/" + "/".join(str(p) for p in parts)


def schema_pointer(error):
    parts = list(error.absolute_schema_path)
    return "/" + "/".join(str(p) for p in parts) if parts else ""


def main():
    ap = argparse.ArgumentParser(description="Validate JSON against a JSON Schema.")
    ap.add_argument("instance", help="Path to the data/instance JSON file")
    ap.add_argument("schema", help="Path to the JSON Schema file")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="Emit machine-readable JSON instead of text")
    args = ap.parse_args()

    try:
        from jsonschema import validators
        from jsonschema.exceptions import SchemaError
    except ImportError:
        print("ERROR: the 'jsonschema' package is required. "
              "Install it with: pip install jsonschema --break-system-packages",
              file=sys.stderr)
        sys.exit(2)

    schema = load_json(args.schema)
    instance = load_json(args.instance)

    # Pick the validator class from $schema, defaulting to draft 2020-12.
    try:
        ValidatorClass = validators.validator_for(
            schema, default=validators.Draft202012Validator
        )
        ValidatorClass.check_schema(schema)
    except SchemaError as e:
        print(f"ERROR: the schema itself is invalid: {e.message}", file=sys.stderr)
        sys.exit(2)

    validator = ValidatorClass(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))

    findings = []
    for e in errors:
        findings.append({
            "instanceLocation": pointer(e) or "(root)",
            "keyword": e.validator,
            "message": e.message,
            "schemaLocation": schema_pointer(e),
        })

    if args.as_json:
        print(json.dumps({
            "valid": len(findings) == 0,
            "errorCount": len(findings),
            "errors": findings,
        }, indent=2))
        sys.exit(0 if not findings else 1)

    # Human-readable output
    if not findings:
        print("VALID — the data conforms to the schema.")
        sys.exit(0)

    print(f"INVALID — {len(findings)} error(s) found:\n")
    for i, f in enumerate(findings, 1):
        print(f"{i}. at {f['instanceLocation']}")
        print(f"   keyword: {f['keyword']}")
        print(f"   problem: {f['message']}")
        print(f"   schema : {f['schemaLocation']}")
        print()
    sys.exit(1)


if __name__ == "__main__":
    main()
