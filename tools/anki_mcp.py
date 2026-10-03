"""Anki MCP server — lets Claude Code search the Français deck and add cards.

Exposes four tools: list_decks, search_deck, word_frequency, add_note.
There is deliberately NO way to delete, edit, or suspend anything: anki() only
forwards actions in ALLOWED_ACTIONS, so even a bug can't reach a delete action.

Same division of labour as the notebook: Claude (the caller) produces lemmas,
Lexique 3.83 produces frequency numbers, AnkiConnect reads/writes cards.

Run by Claude Code via .mcp.json (stdio). Needs Anki open with AnkiConnect.
"""

import csv, html, math, os, re, unicodedata
from pathlib import Path
from typing import Literal

import requests
from mcp.server import MCPServer
from wordfreq import zipf_frequency

ROOT        = Path(__file__).resolve().parent.parent
ANKI_URL    = "http://localhost:8765"
ROOT_DECK   = "Français"
LEXIQUE_TSV = Path(os.environ.get("LEXIQUE_TSV", ROOT / "Lexique383.tsv"))
LEXIQUE_COL = "freqlemfilms2"         # subtitles/everyday; "freqlemlivres" = books
ADDED_TAG   = "claude-added"
MODELS      = {"both": "Basic (and reversed card)", "fr_to_en": "Basic"}

# Read + add only. Never add a delete/update/suspend action here.
ALLOWED_ACTIONS = frozenset({"version", "deckNames", "findNotes", "notesInfo", "addNote"})

mcp = MCPServer("anki")


# ── AnkiConnect bridge (from notebook cell [2]) ─────────────────────────────
def anki(action, **params):
    if action not in ALLOWED_ACTIONS:
        raise PermissionError(f"AnkiConnect action {action!r} is not allowed by this server")
    r = requests.post(ANKI_URL, json={"action": action, "version": 6, "params": params},
                      timeout=60).json()
    if r.get("error"):
        raise RuntimeError(f"AnkiConnect {action}: {r['error']}")
    return r["result"]

def clean(s):                         # Anki fields contain HTML
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


# ── Normalization for matching ──────────────────────────────────────────────
ARTICLE_RE = re.compile(r"^(?:de la |de l'|un |une |le |la |les |l'|des |du |d')")
PLURAL_RE  = re.compile(r"\.(?:s|x|es)\b")    # deck style: "un tatouage.s"

def fold(s):                          # lowercase, accent-free, single-spaced
    s = unicodedata.normalize("NFKD", clean(s).lower().replace("’", "'"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip()

def front_key(s):                     # "un tatouage.s" -> "tatouage"
    return ARTICLE_RE.sub("", PLURAL_RE.sub("", fold(s))).strip(" .,;!?")


# ── Lexique frequency index (from notebook cells [2.5] and [5]) ─────────────
_lex = None                           # (lex_lemma, lex_ortho), loaded on first use

def _f(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0

def _lexique():
    global _lex
    if _lex is None:
        if not LEXIQUE_TSV.exists():
            raise FileNotFoundError(f"{LEXIQUE_TSV} missing — run the notebook once to download it")
        lex_lemma, lex_ortho = {}, {}
        with open(LEXIQUE_TSV, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                f = _f(row.get(LEXIQUE_COL))
                lem, ort = row["lemme"].strip().lower(), row["ortho"].strip().lower()
                if lem and f > lex_lemma.get(lem, -1.0): lex_lemma[lem] = f
                if ort and f > lex_ortho.get(ort, -1.0): lex_ortho[ort] = f
        _lex = (lex_lemma, lex_ortho)
    return _lex

def _zipf_equiv(f):                   # per-million -> Zipf scale (log10 per-billion)
    return math.log10(f) + 3.0 if f > 0 else 0.0

def token_freq(tok):                  # Lexique lemma -> Lexique surface -> wordfreq
    lex_lemma, lex_ortho = _lexique()
    if tok in lex_lemma:  return _zipf_equiv(lex_lemma[tok]), "lexique-lemma"
    if tok in lex_ortho:  return _zipf_equiv(lex_ortho[tok]), "lexique-form"
    z = zipf_frequency(tok, "fr")
    return z, ("wordfreq" if z > 0 else "none")

def freq_of(lemma):                   # a phrase scores as its rarest word
    toks = [t for t in re.split(r"[\s']+", lemma.lower()) if t]
    return min((token_freq(t) for t in toks), default=(0.0, "none"))


# ── Tools ───────────────────────────────────────────────────────────────────
@mcp.tool()
def list_decks() -> list[str]:
    """List the Français deck and its subdecks (the only decks cards can be added to)."""
    return sorted(d for d in anki("deckNames")
                  if d == ROOT_DECK or d.startswith(ROOT_DECK + "::"))


@mcp.tool()
def search_deck(terms: list[str],
                field: Literal["any", "front", "back"] = "any") -> list[dict]:
    """Search every note in the Français deck (all subdecks) for the given terms.

    Matching is case- and accent-insensitive substring matching on the cleaned
    field text. Front is French, Back is English. Use French lemmas/synonyms with
    field="front" and English glosses with field="back".

    Each hit has: note_id, deck, model, front, back, tags, matched_term, and
    exact — true when the Front, minus its article and plural marker (".s"),
    equals the term exactly (i.e. very likely a duplicate).
    """
    notes = anki("notesInfo", notes=anki("findNotes", query=f'deck:"{ROOT_DECK}"'))
    decks = _note_decks()

    wanted = [(t, fold(t), front_key(t)) for t in terms if t.strip()]
    hits = []
    for n in notes:
        fields = n["fields"]
        front = clean(fields.get("Front", {}).get("value", ""))
        back  = clean(fields.get("Back",  {}).get("value", ""))
        hay = {"front": fold(front), "back": fold(back)}
        for term, ft, fk in wanted:
            where = ["front", "back"] if field == "any" else [field]
            if any(ft in hay[w] for w in where):
                hits.append({
                    "note_id": n["noteId"],
                    "deck": decks.get(n["noteId"], ""),
                    "model": n["modelName"],
                    "front": front, "back": back, "tags": n["tags"],
                    "matched_term": term,
                    "exact": front_key(front) == fk,
                })
                break
    return hits


def _note_decks():                   # note_id -> deck (notesInfo doesn't report decks)
    out = {}
    for d in list_decks():            # one findNotes per deck, excluding its children
        for nid in anki("findNotes", query=f'deck:"{d}" -deck:"{d}::*"'):
            out[nid] = d
    return out


@mcp.tool()
def word_frequency(lemmas: list[str]) -> list[dict]:
    """Corpus frequency of French lemmas on the Zipf scale (Lexique 3.83 films
    column, wordfreq fallback). Higher = more common; ~7 very common, ~3 rare,
    0 = unknown. A multi-word expression scores as its rarest word.

    Always use this to decide which synonym is most common — never guess.
    """
    out = []
    for lemma in lemmas:
        z, src = freq_of(lemma)
        out.append({"lemma": lemma, "zipf": round(z, 2), "source": src})
    return out


@mcp.tool()
def add_note(deck: str, front: str, back: str,
             card_type: Literal["both", "fr_to_en"],
             tags: list[str] | None = None) -> dict:
    """Add one note to a Français deck. Front = French, Back = English.

    card_type "both"     -> "Basic (and reversed card)": French→English and English→French.
              "fr_to_en" -> "Basic": French→English only (for less common synonyms).

    The note is tagged "claude-added". Anki rejects exact duplicates of Front.
    Show the user the card and get their confirmation before calling this.
    """
    if deck != ROOT_DECK and not deck.startswith(ROOT_DECK + "::"):
        raise ValueError(f"deck must be {ROOT_DECK!r} or one of its subdecks, got {deck!r}")
    if deck not in list_decks():
        raise ValueError(f"deck {deck!r} does not exist; choose one of {list_decks()}")
    if not front.strip() or not back.strip():
        raise ValueError("front and back must both be non-empty")
    note_id = anki("addNote", note={
        "deckName": deck,
        "modelName": MODELS[card_type],
        "fields": {"Front": front.strip(), "Back": back.strip()},
        "tags": sorted({ADDED_TAG, *(tags or [])}),
        "options": {"allowDuplicate": False, "duplicateScope": "deck",
                    "duplicateScopeOptions": {"deckName": ROOT_DECK, "checkChildren": True}},
    })
    return {"note_id": note_id, "deck": deck, "model": MODELS[card_type],
            "front": front.strip(), "back": back.strip()}


if __name__ == "__main__":
    mcp.run()
