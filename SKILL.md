---
name: json-mapper
description: >-
  Map, transform, or convert source data into JSON that conforms to a target JSON Schema,
  then validate it. Use this skill whenever a user wants to fit, shape, mold, coerce, or
  restructure data (CSV, spreadsheets, JSON, XML, API payloads, or free-form text/documents)
  into a given JSON Schema, populate a schema from data, "make this data match this schema,"
  build a conforming JSON instance, or check whether data satisfies a schema. Trigger it even
  when the user just provides some data and a schema and asks to "fill it in" or "convert it,"
  without saying the words "map" or "JSON Schema." The skill resolves ambiguous field
  mappings by asking the user targeted questions rather than guessing.
license: Complete terms in LICENSE.txt
---

# JSON Mapper

Turn arbitrary source data into a JSON document that conforms to a target JSON Schema, asking
the user to resolve genuine ambiguities along the way, and validate the result.

The whole point of this skill is to **not silently guess** when a mapping decision is unclear.
A wrong-but-plausible guess that passes validation is worse than asking, because it produces
confidently-incorrect data. So the skill is built around distinguishing "I can map this
confidently" from "this needs the user's call."

## Workflow

### 1. Gather both inputs
You need (a) the source data and (b) the target schema.
- If a file was uploaded but its content isn't in context, read it (use the `file-reading`
  skill's guidance for the right tool per format — PDFs, xlsx, docx, etc.).
- If the **schema is missing**, ask for it. Never invent the target schema.
- If the **data is missing**, ask for it.
- Note the schema dialect from `$schema`. If it's older than draft 2020-12, say so — some
  keyword behavior in the reference won't apply.

### 2. Understand the target schema
Walk the schema and build a picture of what conforming data must look like:
- Resolve `$ref` / `$defs` so you know the real shape of every field.
- List **required** properties, allowed **types**, **enum**/**const** constraints,
  **format** expectations, **pattern**s, nested objects/arrays, and any
  `oneOf`/`anyOf`/`if-then-else`/`dependentSchemas` branching.
- Note whether `additionalProperties`/`unevaluatedProperties` is `false` (surplus source
  fields must be dropped, not carried over).

When you hit a keyword you're unsure about, read
`references/json-schema-2020-12.md` for its mapping semantics.

### 3. Draft the field mapping and classify every target field
For each field the schema expects, decide which bucket it falls into:

- **Confident** — an obvious 1:1 match, same type, no transformation, or a transformation
  that has exactly one sensible interpretation (e.g. trimming whitespace, an unambiguous
  `"42"` → `42` when the schema wants a number). Map these directly.
- **Needs the user** — see the next section. Collect these into a question batch.
- **Missing** — a required field with no corresponding source data. Always surface these.

### 4. Ask about ambiguities — batched, not one at a time
Gather all the open questions and ask them together in a single, scannable message
(grouped, numbered, with your best-guess default noted for each). Asking ten questions
across ten turns is exhausting; one well-organized batch respects the user's time.
On a chat client, tappable options are ideal for choice-style questions.

**Ask when:**
- A source field could map to more than one target field, or vice versa.
- A source value must be mapped to an `enum`/`const` and the right member isn't obvious
  (e.g. source `"M"` → `"male"`? `"medium"`?).
- A required field has no source data — should it be omitted (and fail), filled with a
  specific value, or is the source incomplete?
- A `oneOf`/`anyOf` branch must be chosen and the data fits more than one (or none) cleanly.
- A format/type conversion is ambiguous — classically dates (`01/02/2023`: Jan 2 or Feb 1?),
  units, currency, number-vs-string, timezone assumptions, splitting one field into several
  or combining several into one.
- The source has data with no home in the schema and `additionalProperties: false` — confirm
  it should be dropped.
- A `default` exists for a missing field — confirm whether to write it in (defaults are NOT
  auto-applied by validation).

**Don't ask when** the answer is unambiguous, already stated, or trivially inferable — that
just adds friction. Calibrate: confident moves are silent; real forks get a question.

State any assumptions you *did* make inline alongside the result, so the user can catch a
wrong guess even on the fields you didn't ask about.

### 5. Produce the mapped JSON
Build the instance from the confident mappings plus the user's answers. Honor exact-match
keywords (`enum`, `const`), convert `format` values to what the schema expects (see the
reference), respect `required`, and drop fields that have no place under a closed schema.
Preserve numeric precision.

### 6. Validate and report
Run the validator and show the result:

```bash
python scripts/validate.py <instance.json> <schema.json>
```

It auto-detects the dialect from `$schema` (defaults to draft 2020-12) and reports **every**
error with its instance location (JSON Pointer), the failing keyword, and a message. Add
`--json` for machine-readable output.

- If valid: say so and present the data.
- If invalid: walk through each error, explain what it means in plain terms, and either fix
  it (if the fix is unambiguous) or ask the user how to resolve it, then re-validate. Loop
  until it's clean or the user accepts the remaining gaps (e.g. genuinely missing source data).

### 7. Deliver both outputs
Provide the conforming JSON **inline** in the chat so the user can read it, **and** save it
as a `.json` file and present it for download. If validation still has unresolved errors,
say so clearly next to the output rather than implying it's clean.

## Worked example (the asking behavior)

**Source (CSV row):** `name=Jane Doe, dob=03/04/1990, gender=F, status=active`
**Target schema (excerpt):** `birthDate` (`format: date`, required), `sex` (`enum: ["male","female","other"]`), `accountState` (`enum: ["ACTIVE","SUSPENDED","CLOSED"]`)

Confident: `name` → `fullName`. Mapped silently.
Batched questions:
1. `dob` `03/04/1990` → `birthDate` needs `YYYY-MM-DD`. Is this **March 4** (US `MM/DD`) or **April 3** (`DD/MM`)?
2. `gender=F` → `sex` enum. Map to `"female"`? (best guess: yes)
3. `status=active` → `accountState` enum is uppercase. Map to `"ACTIVE"`? (best guess: yes)

After answers, produce the instance, validate, deliver inline + file.

## Files
- `scripts/validate.py` — validates an instance against a schema (draft 2020-12 aware), reports all errors.
- `references/json-schema-2020-12.md` — keyword-by-keyword semantics for mapping and explaining errors. Read it when a keyword's behavior matters.
