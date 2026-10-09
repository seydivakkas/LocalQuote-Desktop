# Windows acceptance protocol — NOT YET VERIFIED

## Build (Windows 10/11 x64 machine, Python >= 3.10)
```powershell
.\packaging\build_windows.ps1
```
Deliver the full `dist\LocalQuote-Desktop` directory, not the EXE alone.

## Release gates
1. Start clean Windows 10/11 x64 VM **without Python** and disconnect network.
2. Copy the entire portable folder; launch `LocalQuote-Desktop.exe` from Explorer.
3. Add, update, archive customer; add/update service, create request and new quote.
4. Enter decimals `0,10`, `0,20`, test negative/NaN failures; verify price and VAT.
5. Approve quote. Attempt modification and second approval: both must fail.
6. Generate Turkish PDF and inspect long multiline texts, 50 rows, page footer.
7. Export CSV and confirm formula-like customer names are plain text.
8. Back up database, close application, restore to **empty new path**, reopen using `LOCALQUOTE_DATA_DIR`, compare records.
9. Reopen after unexpected close; verify previous records preserved. Check app cannot silently overwrite corrupted databases.
10. Measure launch time and install/copy size; record machine CPU, RAM, OS, test date and version.

A Windows GitHub Actions build is CI evidence only; *not* a substitute for clean GUI acceptance and offline operation on the intended customer hardware. Mark GA release HOLD until all steps are documented and passed.
