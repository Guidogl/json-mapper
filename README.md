# json-mapper

[![skills.sh](https://skills.sh/b/guidogl/json-mapper)](https://skills.sh/guidogl/json-mapper)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](./LICENSE.txt)
[![Agent Skills Spec](https://img.shields.io/badge/Agent%20Skills-Specification-blue)](https://agentskills.io)
[![JSON Schema](https://img.shields.io/badge/JSON%20Schema-draft%202020--12-orange)](https://json-schema.org/)
[![Python](https://img.shields.io/badge/python-3.x-blue?logo=python&logoColor=white)](https://www.python.org)

An agent skill that maps, transforms, and validates arbitrary source data into JSON that
conforms to a target JSON Schema.

## What it does

Turn arbitrary source data (CSV, spreadsheets, JSON, XML, API payloads, or free-form
text/documents) into a JSON document that conforms to a given JSON Schema — then validate it.
The skill's core principle is to **not silently guess**: when a mapping decision is genuinely
ambiguous (date formats, enum members, branching schemas, missing required fields), it asks
the user targeted, batched questions instead of producing confidently-incorrect data.

## Install

**skills.sh**

```bash
npx skills add guidogl/json-mapper
```

**Claude Code plugin marketplace**

```
/plugin marketplace add guidogl/json-mapper
```

## Contents

- `SKILL.md` — the skill instructions and workflow.
- `references/json-schema-2020-12.md` — keyword-by-keyword JSON Schema (draft 2020-12) semantics
  for mapping data and explaining validation errors.
- `scripts/validate.py` — validates a JSON instance against a schema (draft 2020-12 aware) and
  reports every error with its instance location, the failing keyword, and a message.

## Requirements

The validator needs the `jsonschema` package:

```bash
pip install jsonschema --break-system-packages
```

## License

Apache-2.0 — see [`LICENSE.txt`](./LICENSE.txt).
