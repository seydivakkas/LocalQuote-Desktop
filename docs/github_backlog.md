# GitHub issue drafts — DO NOT MARK COMPLETE UNTIL EVIDENCE EXISTS

## P0-01 · Verify Windows portable EXE offline [LQ-F001/F016]
**PASS:** clean Windows 10/11 x64 VM without Python; disconnected network; copy built folder; GUI CRUD/PDF smoke; attach screenshot, console output and VM metadata.

## P0-02 · Add non-destructive schema v1→v2 migration [LQ-F002]
**PASS:** fixture v1 database migrates and preserves rows/foreign keys; corrupted/unknown future version fails closed.

## P0-03 · Service package aggregation + request editing [LQ-F004/F005]
**PASS:** create and edit bundles of services and correctly track downstream quote snapshots; original request edits don't rewrite approved quotes.

## P0-04 · Quote revision history and approval evidence [LQ-F009]
**PASS:** versioned quote revision/approval audit records with user identity or single-user approval semantics; forbidden transition tests.

## P0-05 · PDF polish and logo in UI [LQ-F010]
**PASS:** saved logo selection from local image, 50-line 3-page golden fixture, Unicode extraction on Windows, no clipping.

## P0-06 · Search benchmark and UX [LQ-F012]
**PASS:** 1,000 quotes search p95 latency captured on target hardware; empty states and UI inputs validated.

## P0-07 · Portable restore from GUI [LQ-F014]
**PASS:** restore to separate data folder, explicitly reopen, validate hash equality after reopening, no in-place overwrite.

## P0-08 · Windows reliability and errors [LQ-F015]
**PASS:** disk full, read-only directory and corrupt db produce understandable errors without losing user data.

## P0-09 · License and SBOM audit [LQ-F016]
**PASS:** exact runtime + transitive dependencies inventoried; full notices bundled; redistribution licenses reviewed; no external fonts distributed.

## P0-10 · GitHub CI results and release evidence [LQ-F017]
**PASS:** Windows+Linux tests green, Windows EXE preview artifact green, customer hardware smoke completed, independent checklist signed, release HOLD removed.

## P1 (locked until P0 acceptance)
Optional llama.cpp/Qwen local inference to parse brief, local indexed document knowledge, human verification, benchmarked LLM quality and PC compatibility.
