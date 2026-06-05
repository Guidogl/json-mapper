# JSON Schema draft 2020-12 — keyword reference for mapping

Read this when the target schema uses a keyword you need to map data into or
explain a validation error for. This summarizes the behavior that matters when
*producing conforming data*, not the full spec.

## Contents
- [Identifying the dialect](#identifying-the-dialect)
- [Core structural keywords](#core-structural-keywords)
- [Types and the data model](#types-and-the-data-model)
- [Object keywords](#object-keywords)
- [Array keywords](#array-keywords)
- [String / number / generic assertions](#string--number--generic-assertions)
- [Conditional and combining keywords](#conditional-and-combining-keywords)
- [References: $ref, $defs, $dynamicRef](#references-ref-defs-dynamicref)
- [format values](#format-values)
- [Common mapping traps](#common-mapping-traps)

---

## Identifying the dialect
The schema's `$schema` URI names the dialect. `https://json-schema.org/draft/2020-12/schema`
is draft 2020-12. Older drafts differ in important ways (e.g. `items` as an array,
`additionalItems`, `definitions` instead of `$defs`). The validator script auto-detects
the dialect from `$schema`; if absent it assumes 2020-12. If the source schema is an
older draft, the keyword behavior below may not all apply — note this to the user.

## Core structural keywords
- `$id` — sets the canonical URI / base URI for resolving relative references inside this resource. Does not constrain data.
- `$defs` — a holding area for reusable subschemas. Referenced via `$ref`. Does not constrain data on its own.
- `$comment` — author notes; never affects validation and must not be shown to end users as data.
- `title` / `description` — annotations. Useful as hints for what a field *means* when deciding a mapping.
- `default` — annotation only; it does NOT auto-fill missing data during validation. If you want a default applied, you must write it into the output explicitly (and usually should ask the user first).
- `examples` — annotation; sample valid values, helpful for inferring intended format.

## Types and the data model
`type` may be a single string or an array of allowed types. The six primitive types:
`null`, `boolean`, `object`, `array`, `number`, `string`. Notes:
- `integer` is allowed as a `type` value and means a number with no fractional part. `1.0` counts as an integer; `1.5` does not.
- Numbers are arbitrary-precision base-10 decimals in the model. Do not silently lose precision.
- If `type` is an array (e.g. `["string","null"]`) the value may be any one of them.
- Most assertions only bite when the instance is the targeted type. E.g. `maxLength` ignores non-strings. So `{"type":["string","null"], "maxLength":255}` allows null. Don't assume a length/range keyword also restricts the type.

## Object keywords
- `properties` — maps property name → subschema. Only constrains properties that are present; does not make them required.
- `required` — array of property names that MUST be present. Missing required fields are the most common mapping gap — surface them.
- `additionalProperties`:
  - `false` → no properties beyond those in `properties`/`patternProperties` are allowed. Extra source fields must be dropped or the data fails. **Do not invent properties** under this.
  - a schema → every otherwise-unmatched property must validate against it.
- `patternProperties` — property names matching a regex must validate against the associated subschema.
- `propertyNames` — every property *name* (always a string) must validate against this schema (e.g. a pattern on keys).
- `dependentSchemas` — if property X is present, the whole object must also validate against the named subschema. Presence of one field can pull in extra requirements.
- `minProperties` / `maxProperties` — count bounds (Validation vocab).
- `unevaluatedProperties` — applies to properties not "evaluated" by adjacent `properties`/`patternProperties`/`additionalProperties` *including across `$ref`, `allOf`, `if/then`, etc.* `false` here is stricter than it looks: a property allowed only inside a branch that didn't run will be rejected. When you see this, be careful about which combining branch actually applies.

## Array keywords
- `prefixItems` — array of schemas; element i must match schema i (tuple validation). Does not bound length.
- `items` — in 2020-12 this is a *single schema* applied to every element after the `prefixItems` prefix (it took over the old `additionalItems` role). If there's no `prefixItems`, it applies to all elements.
- `contains` — at least one element must match. With `minContains: 0` an empty/all-non-matching array still passes.
- `minItems` / `maxItems` / `uniqueItems` — count and uniqueness bounds (Validation vocab).
- `unevaluatedItems` — like `unevaluatedProperties` but for array positions not evaluated by adjacent item keywords or in-place applicators.

## String / number / generic assertions
(These live in the Validation vocabulary but appear constantly.)
- Strings: `minLength`, `maxLength` (count Unicode code points, not bytes), `pattern` (ECMA-262 regex, **unanchored** — `"es"` matches `"expression"`; anchor with `^`/`$` if full-match is intended).
- Numbers: `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`.
- `enum` — value must be exactly one of the listed values (deep equality). Mapping source values to enum members is a frequent ambiguity — ask rather than guess.
- `const` — value must equal exactly this one value.

## Conditional and combining keywords
- `allOf` — must satisfy every subschema. Often used to compose/extend.
- `anyOf` — must satisfy at least one. Multiple may match.
- `oneOf` — must satisfy EXACTLY one. If the data could match two branches it fails. Picking the intended branch is a classic mapping decision — surface it.
- `not` — must NOT satisfy the subschema.
- `if` / `then` / `else` — if the data validates against `if`, it must also validate against `then`; otherwise against `else`. `then`/`else` are ignored when `if` is absent. Use this to figure out conditionally-required fields.

## References: $ref, $defs, $dynamicRef
- `$ref` is a URI-reference resolved against the current base URI. `#/$defs/point` points into the same document. A bare `#foo` resolves a plain-name `$anchor`. External refs (e.g. `other.json`) need that document to be available — if it isn't, validation of that branch can't complete; tell the user.
- In 2020-12, `$ref` may sit alongside other keywords in the same object (unlike draft-07).
- `$anchor` defines a plain-name fragment target; `$dynamicAnchor`/`$dynamicRef` are an advanced runtime-resolved extension mechanism for recursive schemas (e.g. extensible tree/meta-schemas). You rarely author these but may need to follow them to understand a recursive structure.
- Resolve refs to learn the real shape of a field before mapping into it.

## `format` values
`format` is an annotation by default and may or may not be asserted depending on the
implementation/vocabulary. Even when not enforced, treat it as the author's intent and
produce conforming values. Common values and what to emit:
- `date` → `YYYY-MM-DD`
- `date-time` → RFC 3339, e.g. `2023-01-30T08:30:00Z` (include timezone)
- `time` → `HH:MM:SS(.sss)(Z|±hh:mm)`
- `duration` → ISO 8601 duration, e.g. `P3DT4H`
- `email`, `idn-email`
- `hostname`, `idn-hostname`
- `ipv4`, `ipv6`
- `uri`, `uri-reference`, `iri`, `uuid`
- `regex` → ECMA-262 regular expression
- `json-pointer`, `relative-json-pointer`

When source data uses a different date/number format, **convert it** to the format the
schema expects; if the source format is ambiguous (e.g. `01/02/2023` — Jan 2 or Feb 1?),
ask.

## Common mapping traps
- A missing keyword imposes no constraint — don't manufacture rules the schema doesn't state.
- `default` does not auto-populate. `enum`/`const` are exact-match.
- Under `additionalProperties: false` (or strict `unevaluatedProperties: false`), surplus source fields must be dropped, not carried over.
- `required` + a value that's `null`: `null` satisfies "present"; it only fails if the field's own schema disallows null. Distinguish "absent" from "present and null".
- Numbers vs numeric strings: `"42"` is a string, `42` is a number. Coerce deliberately and only when the schema's `type` calls for it.
- `pattern`/`patternProperties` regexes are unanchored — a partial match passes.
- `oneOf` failing with "valid under more than one" means two branches matched; you must disambiguate which one is intended.
