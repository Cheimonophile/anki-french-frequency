# Anki French Vocabulary — Frequency Sort

Reorder the **new cards** in an Anki deck so that the words/expressions you
encounter most often in real French come first. Words are normalized to their
dictionary form by an LLM, scored against a real frequency corpus, and the new
cards are repositioned via Anki's local HTTP API.

> Move this file into your new repo (rename to `README.md` if you like).

---

## Goal

I add French vocabulary to Anki as I run into it in daily life, so my "new card"
queue is in haphazard order. I want to study the **most common words first**,
without hand-ranking a long list.

---

## How it works (architecture)

Three components, each doing the job it's actually good at:

| Component | Role | Why |
|---|---|---|
| **Claude (LLM), batched** | **Normalization only** — turn each entry into its dictionary citation form (lemma) and flag likely typos. | Lemmatization with articles, elisions, irregular plurals, and verb forms is genuinely hard rule-based work; LLMs are excellent at it. |
| **`wordfreq` (corpus)** | **The frequency number** — `zipf_frequency(lemma, "fr")`. | A real corpus is accurate, reproducible, and free. |
| **AnkiConnect (HTTP)** | **Read + write + reposition** cards. | Local JSON-over-HTTP API into the running Anki app. |

**Key design rule:** the LLM produces the *lemma*; the corpus produces the
*number*. Do **not** ask the LLM to invent frequency values — it will
hallucinate inconsistent ranks. The LLM normalizes; the corpus ranks.

### Why normalize first?

Frequency lists are keyed on surface forms. `chien` and `chiens` are separate
entries with different frequencies, so the *same noun* would sort differently
depending on whether I happened to record the singular or the plural. Verbs are
worse (`manger` vs `mangé` vs `mangeaient`). Reducing every entry to one
citation form before the frequency lookup makes the sort consistent regardless
of how I recorded it. Articles (`le/la/les/un/une/des`, `l'`, `d'`) are stripped
in the same pass.

For phrases/expressions, there is no whole-phrase frequency, so we score by the
**rarest component word** — usually the word that governs whether you can read
the expression.

---

## How external programs talk to Anki

Via **AnkiConnect**, an add-on that runs a local HTTP+JSON server on
`http://localhost:8765` while the Anki desktop app is open. You POST
`{"action": ..., "version": 6, "params": ...}` and get JSON back.

Actions used here: `findCards`, `cardsInfo`, `updateNoteFields`,
`setSpecificValueOfCard`, `version`.

> AnkiConnect has **no clean "reposition" action**. New-card order is governed
> by each card's `due` value (its position in the new queue). We either write a
> frequency field and reposition manually in the Browser (safe), or set `due`
> directly with the low-level `setSpecificValueOfCard` (automated — see below).

---

## Prerequisites

```bash
pip install anthropic wordfreq requests
```

1. **AnkiConnect add-on** — in Anki: Tools → Add-ons → Get Add-ons → paste
   `2055492159` → restart Anki.
2. **Anki must be open** while the script runs (AnkiConnect is served by the
   desktop app).
3. **`ANTHROPIC_API_KEY`** set in the environment.
4. **Back up the collection** before the first real run (File → Export →
   `.colpkg`) — this script repositions cards.

---

## Configuration (set these for your collection)

| Setting | What it is |
|---|---|
| `DECK_QUERY` | Anki search selecting the new cards, e.g. `deck:"French" is:new` |
| `SOURCE_FIELD` | The note field holding the French word/expression (e.g. `Front`) |
| `MODEL` | `claude-opus-4-8` default; `claude-haiku-4-5` is much cheaper for this simple task |
| `WRITE_LEMMA_TO` / `WRITE_FREQ_TO` | Fields to store the lemma / zipf value (must already exist on the note type), or `None` |
| `DRY_RUN` | `True` = preview only, writes nothing |
| `AUTO_REPOSITION` | `False` = reposition manually in the Browser; `True` = script sets order directly |

To add the `Lemma` / `Freq` fields: Tools → Manage Note Types → (your type) →
Fields → Add.

---

## Pipeline

1. `findCards` + `cardsInfo` → pull the new cards' text (HTML stripped).
2. **Claude Batches API** → normalize each distinct entry to
   `{lemma, pos, is_suspect, suggestion}` via structured JSON output.
3. `wordfreq.zipf_frequency(lemma, "fr")` → frequency (rarest word for phrases).
4. Sort most-frequent-first; assign new-queue positions `1, 2, 3, …`.
5. Write back: optional `Lemma`/`Freq` fields, then reposition.

---

## Script

Cells delimited with `# %%` so it runs as a notebook or a plain script.

```python
# %% [0] Prerequisites
#   pip install anthropic wordfreq requests
#   - Anki OPEN with AnkiConnect (add-on code 2055492159)
#   - export ANTHROPIC_API_KEY=...
#   - BACK UP your collection first (File → Export → .colpkg)

import re, html, json, time, requests
from wordfreq import zipf_frequency
from anthropic import Anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

# %% [1] CONFIG — set these for your collection
DECK_QUERY   = 'deck:"French" is:new'   # which new cards to sort
SOURCE_FIELD = "Front"                  # field holding the French word/expression
MODEL        = "claude-opus-4-8"        # simple task — "claude-haiku-4-5" is much cheaper

WRITE_LEMMA_TO = "Lemma"   # store the lemma here, or None (field must exist)
WRITE_FREQ_TO  = "Freq"    # store the zipf value here, or None (field must exist)
DRY_RUN        = True      # True = preview only, writes NOTHING
AUTO_REPOSITION = False    # False = reposition manually in Browser (safe)
                           # True  = script sets new-card order directly (see caveats)

# %% [2] AnkiConnect bridge + helpers
def anki(action, **params):
    r = requests.post("http://localhost:8765",
                      json={"action": action, "version": 6, "params": params}, timeout=60).json()
    if r.get("error"):
        raise RuntimeError(f"AnkiConnect {action}: {r['error']}")
    return r["result"]

def clean(s):                       # Anki fields contain HTML
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

# %% [1.5] Connectivity check (optional)
print("AnkiConnect version:", anki("version"))   # → 6 if the bridge is up
print(len(anki("findCards", query=DECK_QUERY)), "new cards match your query")

# %% [3] Pull the new cards
items = [{"card_id": c["cardId"], "note_id": c["note"],
          "raw": clean(c["fields"][SOURCE_FIELD]["value"])}
         for c in anki("cardsInfo", cards=anki("findCards", query=DECK_QUERY))]
print(f"{len(items)} new cards found.")

# %% [4] Normalize each distinct entry with Claude (Batches API)
SYSTEM = (
    "You are a French lexicographer normalizing vocabulary flashcard entries. "
    "For the given entry, return its dictionary citation form (lemma): nouns as masculine "
    "singular with NO article, verbs as the infinitive, adjectives as masculine singular; "
    "strip articles and elisions (le/la/les/un/une/des, l', d'); lowercase unless a proper noun. "
    "For a multi-word expression, give the canonical form of the whole expression. "
    "Flag is_suspect=true only if the entry looks like a typo or is not valid French, and put "
    "the corrected French in 'suggestion' (empty string otherwise)."
)
SCHEMA = {
    "type": "object",
    "properties": {
        "lemma":      {"type": "string"},
        "pos":        {"type": "string",
                       "enum": ["noun","verb","adjective","adverb","pronoun","preposition",
                                "conjunction","determiner","interjection","phrase","other"]},
        "is_suspect": {"type": "boolean"},
        "suggestion": {"type": "string"},
    },
    "required": ["lemma","pos","is_suspect","suggestion"],
    "additionalProperties": False,
}

raws = sorted({it["raw"] for it in items if it["raw"]})   # dedupe identical text
idx2raw = {f"w{i}": r for i, r in enumerate(raws)}
client = Anthropic()

batch = client.messages.batches.create(requests=[
    Request(custom_id=cid, params=MessageCreateParamsNonStreaming(
        model=MODEL, max_tokens=300, system=SYSTEM,
        messages=[{"role": "user", "content": raw}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )) for cid, raw in idx2raw.items()
])
print("Batch:", batch.id, "— polling (usually minutes)…")

while client.messages.batches.retrieve(batch.id).processing_status != "ended":
    time.sleep(20)

norm = {}
for res in client.messages.batches.results(batch.id):
    if res.result.type == "succeeded":
        txt = next((b.text for b in res.result.message.content if b.type == "text"), "{}")
        norm[idx2raw[res.custom_id]] = json.loads(txt)
    else:
        print("FAILED:", idx2raw[res.custom_id], res.result.type)

# %% [5] Attach lemma + frequency (rarest component word for phrases)
def freq_of(lemma):
    toks = [t for t in lemma.lower().split() if t]
    return min((zipf_frequency(t, "fr") for t in toks), default=0.0)

for it in items:
    n = norm.get(it["raw"], {})
    it["lemma"]   = n.get("lemma", "")
    it["suspect"] = n.get("is_suspect", False)
    it["suggest"] = n.get("suggestion", "")
    it["zipf"]    = freq_of(it["lemma"]) if it["lemma"] else 0.0

ordered = sorted(items, key=lambda x: x["zipf"], reverse=True)   # most frequent first

# %% [6] Preview (always) — stop here if DRY_RUN
print(f"\n{'RAW':<22}{'LEMMA':<18}{'ZIPF':>6}  FLAG")
for it in ordered:
    flag = f"  ⚠ typo? → {it['suggest']}" if it["suspect"] else ""
    print(f"{it['raw'][:21]:<22}{it['lemma'][:17]:<18}{it['zipf']:>6.2f}{flag}")
print(f"\n{sum(it['suspect'] for it in ordered)} entries flagged as possible typos.")
assert not DRY_RUN, "DRY_RUN is True — nothing written. Review above, then set DRY_RUN=False."

# %% [7] Write back to Anki
# 7a. (optional) store Lemma / Freq fields — those fields must exist on the note type.
for it in items:
    fields = {}
    if WRITE_LEMMA_TO: fields[WRITE_LEMMA_TO] = it["lemma"]
    if WRITE_FREQ_TO:  fields[WRITE_FREQ_TO]  = f"{it['zipf']:05.2f}"   # zero-pad → text sort = numeric
    if fields:
        anki("updateNoteFields", note={"id": it["note_id"], "fields": fields})

# 7b. reposition the new cards so the most frequent come first
if AUTO_REPOSITION:
    # Sets each new card's `due` (its position in the new queue) directly.
    # Requires the deck's new-card sort order to be position/"order added" based.
    for pos, it in enumerate(ordered, start=1):
        anki("setSpecificValueOfCard",
             card=it["card_id"], keys=["due"], newValues=[str(pos)],
             warning_check=True)   # acknowledges this is a low-level write
    print("Repositioned", len(ordered), "cards.")
else:
    print("Freq written. Now in Anki: Browser → sort by Freq (descending) →"
          " select all → Cards → Reposition (start 1, step 1).")
```

---

## Reposition: safe vs. automated

- **`AUTO_REPOSITION = False` (default, safe):** the script writes the `Freq`
  field; you do the one-click **Browser → sort by Freq → select all → Cards →
  Reposition** (start 1, step 1). Anki validates everything. Use this first.
- **`AUTO_REPOSITION = True` (automated):** uses `setSpecificValueOfCard` to set
  each new card's `due` directly. This bypasses Anki's normal checks (hence
  `warning_check=True`), so **back up first**, and make sure the deck's *New
  card gather/sort order* is position-based ("Order added"), not Random.

---

## Gotchas

- **Anki must be running** or the HTTP POST fails (connection refused).
- **Close the Browser/editor** before cell [7]: AnkiConnect won't apply
  `updateNoteFields` to a note open in the editor — it silently no-ops.
- **`Lemma` / `Freq` fields must exist** on the note type before writing, or set
  those config values to `None`.
- **Zero-padding** the `Freq` value makes Anki's text sort match numeric order.
- **Unknown/typo words** get `zipf = 0.0` and sink to the bottom — usually what
  you want for "study common words first," and a handy review list of suspects.

---

## Alternative frequency source (optional upgrade)

`wordfreq` is surface-form based, so looking up the lemma gives a good proxy. For
the most accurate **lemma-level** French frequency (aggregated across all
inflected forms), swap in [Lexique](http://www.lexique.org/) and use its
`freqlemfilms2` column instead of `zipf_frequency`. More setup, better numbers
for verbs.

---

## References

- AnkiConnect — https://github.com/FooSoft/anki-connect (add-on code `2055492159`)
- wordfreq — https://pypi.org/project/wordfreq/ · Zipf scale: https://www.wellformedness.com/blog/zipf-scale/
- Lexique (French lexical database) — http://www.lexique.org/
- FrequencyMan (zero-code Anki add-on alternative) — https://ankiweb.net/shared/info/909420026
