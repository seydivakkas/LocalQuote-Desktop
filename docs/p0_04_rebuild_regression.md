# P0-04 — Independent Windows build discrepancy and regression

## Baseline run (FAIL)

Actions run 38084626718 on commit 3b9bc105d6d21b732110e2215799d05d65e30ba8:

- Core unit/integration test matrix: PASS (Windows and Ubuntu, Python 3.11/3.13).
- __mypyc: exact SHA-256 matched the charset-normalizer 3.4.7 Windows wheel; wheel member and frozen PYD were byte-identical.
- First build 1,014 files; second build 1,011 files.
- Missing from the second build: ReportLab, Pillow, charset-normalizer LICENSE files.
- Differing: LocalQuote-Desktop.exe and _internal/base_library.zip.
- Reproducibility status: **FAIL**.

## Corrective implementation

- Stage exact same three Python runtime license files in each independent build using the isolated runtime license collector.
- Read runtime and build wheels from the **same previously downloaded, hash-checked wheelhouse** across both runners; each rebuild rechecks wheel bytes. This isolates build differences from changing upstream artifacts.
- Fix the PyInstaller input variables PYTHONHASHSEED=1 and SOURCE_DATE_EPOCH=1700000000 (the timestamp in Windows PE headers). These variables are controlled engineering build inputs, not user data.
- Give native-components.json explicit __mypyc provenance only when its frozen SHA-256 matches the expected charset-normalizer wheel member. A mismatch remains UNKNOWN_NATIVE.
- Fail CI on any differing output manifest rather than suppressing the result with a warning.

## Interpretation of future results

**PASS** means both runners, given those identical inputs, produced matching bytes for all files in the preview directory in that specific run. It does not guarantee all future runners/toolchains will reproduce the same outputs and is not a commercial release signoff.

**FAIL** means examine the uploaded build-comparison.json file; never erase/dismiss file differences to obtain a green check.

The first-party customer-use terms are a DRAFT and are not a public open-source grant. Native dependency redistribution, customer Windows GUI acceptance and source-code contract approval are separate HOLD gates.
