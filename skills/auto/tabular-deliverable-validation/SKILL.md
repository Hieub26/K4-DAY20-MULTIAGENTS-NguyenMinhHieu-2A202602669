---
name: tabular-deliverable-validation
description: Use when analyzing tabular records and producing structured answer and cleaned-data files.
---
1. Follow every required output schema and file requirement exactly; validate the finished files rather than relying on analysis in the trace.
2. In `answer.json`, represent money values as integer cents and include the required `meta` object with the specified keys and counts.
3. For `clean.csv`, use the required header order and one row per distinct keyed record with a known amount.
4. Write amounts as integer cents, timestamps in the required UTC format, and categorical values in the required canonical spelling.
5. Count input rows with duplicates included where required; count distinct usable records separately where required.
6. Self-check that every required file exists and that its structure, values, row counts, and formatting meet the stated rules before finishing.
