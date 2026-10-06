---
name: code-regression-hygiene
description: Use when fixing bugs in a code package that requires tests, annotations, and a changelog.
---
1. Add type annotations for every parameter and return value of every public function (one whose name does not start with `_`).
2. Add `tests/test_regressions.py` with one test function for each bug fixed, and include at least three tests.
3. Record each fix in `CHANGELOG.md` under `## Unreleased`, using `- fix(<function name>): <short description>` bullets; include at least three bullets.
4. Run the regression tests and relevant existing tests. Investigate any failed check or assertion, then rerun after changes.
5. Self-check the annotations, required test file and test count, changelog heading and bullets, and final test results before finishing.
