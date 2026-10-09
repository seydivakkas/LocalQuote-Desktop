# GitHub repository and P0 delivery

**Repository:** https://github.com/seydivakkas/LocalQuote-Desktop

The P0 source code, unit tests, README, Windows build script and CI workflow have been imported in commit [83e65fa](https://github.com/seydivakkas/LocalQuote-Desktop/commit/83e65fa02a4391636e287646ff7d7bc4127604f5). The repository is no longer empty.

## Verify the repository

```powershell
git clone https://github.com/seydivakkas/LocalQuote-Desktop.git
cd LocalQuote-Desktop
py -3 -m pip install -e .
py -3 -m unittest discover -s tests -v
py -3 -m localquote --smoke --db "$env:TEMP\localquote-smoke.sqlite3"
py -3 -m localquote --gui
```

Source dependencies must be installed on the *developer/build machine*, not on the shipped customer PC. Building may require network access once. The application core itself must work offline.

## Live status and open items

- CI and Windows preview: https://github.com/seydivakkas/LocalQuote-Desktop/actions
- Source code import: https://github.com/seydivakkas/LocalQuote-Desktop/issues/1
- Clean Windows offline acceptance: https://github.com/seydivakkas/LocalQuote-Desktop/issues/2
- Business CRUD and revisions: https://github.com/seydivakkas/LocalQuote-Desktop/issues/3
- PDF and backup restore: https://github.com/seydivakkas/LocalQuote-Desktop/issues/4
- Third-party licenses and independent release gate: https://github.com/seydivakkas/LocalQuote-Desktop/issues/5

**Release: HOLD** until Windows offline runtime tests, missing P0 features and redistribution license audit pass. Do not publish a customer-ready version merely because Linux tests or GitHub Actions are green.

Never commit real customer data, secrets, private databases, or internal invoices.
