# NL2Verus integration

Imported from the user-provided NL2Verus-Workbench backend and bundled data.
Original prompt attribution is preserved in `experiment_prompts.py` and the knowledge corpus README/manifest.
No private `.runtime` configuration, Windows binaries, research PDFs or historical user runs are included.

Adaptations: portable asset paths; platform-aware pinned Verus executable; uploaded Rust module snapshots;
platform model configuration fallback; durable platform task/artifact integration.
The workflow retains one candidate and up to three diagnostic-driven repairs, with no hidden provider retries.
