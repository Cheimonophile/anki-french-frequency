# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A one-purpose tool that reorders the **new cards** in an Anki deck so the most
frequent French words come first. It normalizes each entry to its dictionary
lemma with Claude, scores that lemma against the Lexique 3.83 corpus, and
repositions the cards through AnkiConnect's local HTTP API.

It also has an **`ajouter` skill** for *adding* cards from Claude Code — see
"Adding cards" below.

## Adding cards: the `ajouter` skill and `anki` MCP server

- [.claude/skills/ajouter/SKILL.md](.claude/skills/ajouter/SKILL.md) — workflow:
  lemmatize → duplicate check → find in-deck synonyms → `word_frequency` ranks the
  synonym group → most common gets `Basic (and reversed card)`, the rest get
  `Basic` (French→English only) → preview → add on confirmation. Existing cards
  are never modified; reverse-card conflicts are only reported.
- [tools/anki_mcp.py](tools/anki_mcp.py) — stdio MCP server registered in
  [.mcp.json](.mcp.json). Tools: `list_decks`, `search_deck`, `word_frequency`,
  `add_note`. Frequency code is copied from the notebook (cells [2], [2.5], [5]);
  keep the two in sync if you change the lookup chain.
- **No delete, by design.** The user does not want Claude able to delete cards.
  `anki()` in the server enforces an `ALLOWED_ACTIONS` allowlist (read + `addNote`
  only) — don't add delete, update, or suspend actions to it. A `PreToolUse` hook
  ([.claude/hooks/guard_anki.py](.claude/hooks/guard_anki.py), wired in
  [.claude/settings.json](.claude/settings.json)) blocks Bash commands that hit
  port 8765 directly and code that names AnkiConnect delete actions. It is
  best-effort, not a sandbox.

## Source of truth: the notebook, not the markdown

[anki_french_frequency_sort.ipynb](anki_french_frequency_sort.ipynb) is the
live, end-to-end-run implementation. [anki-french-frequency-sort.md](anki-french-frequency-sort.md)
is the original design doc and has **diverged** — treat it as background prose,
not current behavior. Where they disagree, the notebook wins. Notable drifts the
markdown still describes but the notebook no longer does:

- No `DRY_RUN` / `AUTO_REPOSITION` flags. The preview cell ([6]) ends with
  `raise Exception(...)` to force a manual stop; you review the table, then run
  the lower cells by hand to sync.
- No `Lemma` / `Freq` field writing. Repositioning is now done **directly** by
  setting each card's `due`, with no intermediate note fields.
- `DECK_QUERY` targets `deck:"Français"`, and the preview is a pandas table.

If you change pipeline behavior, update the notebook; optionally reconcile the
markdown, but never assume the markdown reflects reality.

## Running it

Python 3.14 in `.venv`. The flow is a Jupyter notebook run top to bottom.

```bash
source .venv/bin/activate
pip install -r requirements.txt          # anthropic, wordfreq, requests, pandas
```

Required before running:
- **Anki desktop must be open** with the AnkiConnect add-on (code `2055492159`).
  Every `anki()` call POSTs to `http://localhost:8765`; if Anki is closed the
  request fails with connection refused.
- `ANTHROPIC_API_KEY` in the environment. `.vscode/settings.json` loads `.env`
  for the notebook kernel automatically.
- **Back up the collection** (File → Export → `.colpkg`) before the first real
  run — the reposition step writes `due` with `warning_check=True`, bypassing
  Anki's normal safety checks.

`Lexique383.tsv` (~30 MB) auto-downloads on first run and is gitignored; later
runs reuse it. Override its path with the `LEXIQUE_TSV` env var.

Notebook **outputs are stripped on commit** by an `nbstripout` git filter
(`.gitattributes` → `*.ipynb filter=nbstripout`); the working copy keeps its
outputs, git records none. The filter is defined in local `.git/config`, not in
the repo, so on a fresh clone run `nbstripout --install` once to re-enable it.

## Architecture — the one rule that matters

The pipeline deliberately splits three jobs across three tools, and the
correctness of the whole thing rests on **not blurring them**:

| Tool | Job | Never does |
|---|---|---|
| **Claude (Batches API)** | Normalize each entry to its lemma + flag typos | Produce frequency numbers — it would hallucinate inconsistent ranks |
| **Lexique 3.83** | Supply the frequency number (`freqlemfilms2`, lemma-level) | — |
| **AnkiConnect** | Read cards, write `due` to reposition | — |

**The LLM produces the lemma; the corpus produces the number.** Keep that
boundary. Lemma-level frequency is the point: `chien` and `chiens` resolve to one
lemma so they score identically regardless of which form was recorded.

Frequency lookup chain in `token_freq()`: Lexique lemma → Lexique surface form →
`wordfreq` fallback. Per-million counts convert to the Zipf scale
(`log10(per-million) + 3`). Unknown words score `0.0` and sink to the bottom.
Phrases are scored by their **rarest** component word (`freq_of` takes the `min`).

## Gotchas specific to this code

- **`due` must be written as an `int`.** Passing a string to
  `setSpecificValueOfCard` makes AnkiConnect silently no-op. Cell [7] writes ints
  and then re-reads the cards to assert the new `due` persisted — keep that
  verification if you touch the reposition code.
- The deck's **New-card gather/sort order must be position-based** ("Order
  added"), not Random, or setting `due` won't change study order.
- **Close the Anki Browser/editor** before syncing; AnkiConnect won't apply
  writes to a note open in the editor.
- Claude requests are **deduped by raw text** before batching (`idx2raw`), so
  identical card fronts cost one request, not many.
- Lemmas are **cached across runs** in a gitignored `shelve` KV store
  (`lemma_cache*`, override with `LEMMA_CACHE`); only cache *misses* hit the
  Batches API. The key is just the raw entry text, so the cache is reused even if
  you change the model or prompt — delete `lemma_cache*` to force a re-query under
  a new config. Failed requests aren't cached, so they retry next run.
