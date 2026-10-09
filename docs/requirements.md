# LocalQuote P0 — Requirement and acceptance contract

## Problem
Small Turkish digital agencies spend time copying customer requirements into proposals and computing service prices. Offline-first desktop app; no recurring paid services or API.

## Users / operations
- Add/update/archive customers, add/update/deactivate services.
- Save a manual client request (plain text and optional deadline).
- Convert request into quote, select predefined service, adjust snapshot unit price, quantity, discount, and VAT.
- Validate line totals with integer kuruş; discount before VAT, HALF_UP per line.
- Lock after human approval; approved or previously exported quotes can be rendered as final PDF.
- Browse/search customers/quotes; save UTF-8-SIG CSV, create a consistent SQLite backup.
- Restore into **a new empty data path** (never overwrite a running database).

## 3 synthetic acceptance examples
1. Website: 1 × 12,500 TL, 10% line discount, 20% VAT → 13,500 TL total.
2. Two services: 1 × 100 TL @ 10% VAT and 1 × 100 TL @ 20% VAT → 230 TL total.
3. Half-kuruş rounding: 0.5 × 0.01 TL → 0.01 TL with HALF_UP.

## Excluded from P0
LLM, RAG, invoice/e-invoice, automatic outbound email, CRM sync, electronic signatures, multi-user concurrency, universal Turkish tax compliance, inventory/accounting and multi-tenant SaaS.

## Acceptance vs evidence
- Local Linux headless tests show software logic works; **not** evidence of Windows portability.
- Windows EXE, clean Windows VM, disconnected network, GUI tasks, real-world workflow validation remain release HOLD until executed.
- Never mark a PDF as invoicing/official fiscal document; it is a sales proposal only.
