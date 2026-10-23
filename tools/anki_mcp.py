"""Anki MCP server — lets Claude Code search the Français deck, add cards, fix
the Front/Back text of existing ones, suspend or unsuspend single cards, and
move notes between Français decks.

Exposes eight tools: list_decks, search_deck, word_frequency, add_note,
update_note, suspend_card, unsuspend_card, change_deck. There is deliberately
NO way to delete anything: anki() only forwards actions in ALLOWED_ACTIONS, so
even a bug can't reach a delete action.

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
DIRECTIONS  = {"fr_to_en": 0, "en_to_fr": 1}   # card ord: Card 1 = Front→Back, Card 2 = Back→Front

# Read + add + Front/Back field edits + suspend/unsuspend + deck moves. Never add a delete action here.
ALLOWED_ACTIONS = frozenset({"version", "deckNames", "findNotes", "notesInfo", "findCards",
                             "cardsInfo", "addNote", "updateNoteFields", "suspend",
                             "unsuspend", "changeDeck"})

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
ARTICLE_RE = re.compile(r"^(?:de la |de l'|un/une |un/e |un |une |le |la |les |l'|des |du |d')")
# Gender/plural markers: "un.e citadin.e.s", "heureux.se.s", old "frais/e/s", "beauté(s)".
# Runs on folded text (accents stripped), so "aigu.ë.s" is already "aigu.e.s".
PLURAL_RE  = re.compile(r"(?<=\w)(?:\.[a-z]+)+\b|(?<=\w)(?:/[a-z]+)+\b|(?<=\w)\(s\)")

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

    Each hit has: note_id, deck, model, front, back, tags, matched_term,
    suspended — which of the note's cards are suspended ("fr_to_en" = Card 1,
    "en_to_fr" = Card 2) — and exact — true when the Front, minus its article
    and gender/plural markers ("un.e citadin.e.s" -> "citadin"), equals the
    term exactly (i.e. very likely a duplicate).
    """
    notes = anki("notesInfo", notes=anki("findNotes", query=f'deck:"{ROOT_DECK}"'))
    decks = _note_decks()
    suspended = {d: set(anki("findNotes", query=f'deck:"{ROOT_DECK}" card:{o + 1} is:suspended'))
                 for d, o in DIRECTIONS.items()}

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
                    "suspended": [d for d, nids in suspended.items() if n["noteId"] in nids],
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
    _check_deck(deck)
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


def _check_deck(deck):               # refuse decks outside the Français tree or not yet created
    if deck != ROOT_DECK and not deck.startswith(ROOT_DECK + "::"):
        raise ValueError(f"deck must be {ROOT_DECK!r} or one of its subdecks, got {deck!r}")
    if deck not in list_decks():
        raise ValueError(f"deck {deck!r} does not exist; choose one of {list_decks()}")


def _check_note(note_id):            # refuse notes outside the Français tree
    if note_id not in anki("findNotes", query=f'deck:"{ROOT_DECK}" nid:{note_id}'):
        raise ValueError(f"note {note_id} is not in the {ROOT_DECK!r} deck tree")


@mcp.tool()
def update_note(note_id: int, front: str | None = None, back: str | None = None) -> dict:
    """Change the Front and/or Back text of one existing note in a Français deck.

    Use only when the user explicitly asks to fix a specific existing card.
    Show them the old → new values and get confirmation before calling this.
    (The ajouter skill calls it only for edits the user asks for, and then also
    normalizes the note to current notation; adding cards never modifies existing ones.)

    Only the Front/Back fields change; deck, card type, scheduling, and tags are
    untouched. The write is re-read to verify it persisted — AnkiConnect silently
    skips notes open in the Browser/editor, so close it if this raises.
    """
    new = {k: v.strip() for k, v in (("Front", front), ("Back", back)) if v is not None}
    if not new:
        raise ValueError("give front and/or back")
    if not all(new.values()):
        raise ValueError("front and back must be non-empty when given")
    _check_note(note_id)

    def fields():
        f = anki("notesInfo", notes=[note_id])[0]["fields"]
        return {k: f[k]["value"] for k in ("Front", "Back")}

    old = fields()
    anki("updateNoteFields", note={"id": note_id, "fields": new})
    now = fields()
    if any(now[k] != v for k, v in new.items()):
        raise RuntimeError(f"note {note_id} did not update (is it open in the Anki Browser?)")
    return {"note_id": note_id,
            "old": {"front": clean(old["Front"]), "back": clean(old["Back"])},
            "new": {"front": clean(now["Front"]), "back": clean(now["Back"])}}


def _set_suspended(note_id, direction, suspend):
    _check_note(note_id)
    cards = anki("cardsInfo", cards=anki("findCards", query=f'deck:"{ROOT_DECK}" nid:{note_id}'))
    card = next((c for c in cards if c["ord"] == DIRECTIONS[direction]), None)
    if card is None:
        model = cards[0]["modelName"] if cards else "unknown model"
        raise ValueError(f"note {note_id} ({model}) has no {direction} card")
    cid, was = card["cardId"], card["queue"] == -1      # queue -1 = suspended
    if was != suspend:
        anki("suspend" if suspend else "unsuspend", cards=[cid])
        if (anki("cardsInfo", cards=[cid])[0]["queue"] == -1) != suspend:
            raise RuntimeError(f"card {cid} of note {note_id} did not change")
    f = anki("notesInfo", notes=[note_id])[0]["fields"]
    return {"note_id": note_id, "card_id": cid, "direction": direction,
            "front": clean(f.get("Front", {}).get("value", "")),
            "back": clean(f.get("Back", {}).get("value", "")),
            "was_suspended": was, "suspended": suspend}


@mcp.tool()
def suspend_card(note_id: int,
                 direction: Literal["fr_to_en", "en_to_fr"] = "en_to_fr") -> dict:
    """Suspend one card of a note in a Français deck, so Anki stops showing it.

    direction "en_to_fr" -> Card 2, the English→French reverse card of a
                            "Basic (and reversed card)" note. The usual case:
                            a more common synonym owns that English prompt.
              "fr_to_en" -> Card 1, the French→English card.

    Use only when the user asks to suspend a specific card, or approves it in an
    ajouter conflict question. Reversible with unsuspend_card. Only the card's
    suspended state changes; fields, tags, and scheduling are untouched. A card
    that is already suspended is left alone (was_suspended: true). The write is
    re-read to verify it persisted.
    """
    return _set_suspended(note_id, direction, True)


@mcp.tool()
def unsuspend_card(note_id: int,
                   direction: Literal["fr_to_en", "en_to_fr"] = "en_to_fr") -> dict:
    """Unsuspend one card of a note in a Français deck — the undo of suspend_card.

    Same direction values as suspend_card. Use only when the user asks.
    """
    return _set_suspended(note_id, direction, False)


@mcp.tool()
def change_deck(note_ids: list[int], deck: str) -> list[dict]:
    """Move whole notes (all their cards) to another deck in the Français tree.

    Use only when the user asks to move specific cards, e.g. ones just added to
    the wrong subdeck. The target must be an existing deck from list_decks —
    AnkiConnect would otherwise create it. Only the deck changes; fields, tags,
    card type, suspension, and scheduling are untouched. Reversible by moving
    the notes back. The write is re-read to verify it persisted.
    """
    _check_deck(deck)
    if not note_ids:
        raise ValueError("give at least one note id")
    for nid in note_ids:              # check every note before moving any
        _check_note(nid)
    query = f'deck:"{ROOT_DECK}" nid:{",".join(map(str, note_ids))}'
    cards = anki("cardsInfo", cards=anki("findCards", query=query))
    old = {}
    for c in cards:
        old.setdefault(c["note"], set()).add(c["deckName"])
    cids = [c["cardId"] for c in cards]
    anki("changeDeck", cards=cids, deck=deck)
    stray = [c["cardId"] for c in anki("cardsInfo", cards=cids) if c["deckName"] != deck]
    if stray:
        raise RuntimeError(f"cards {stray} did not move to {deck!r}")
    out = []
    for n in anki("notesInfo", notes=note_ids):
        f = n["fields"]
        out.append({"note_id": n["noteId"],
                    "front": clean(f.get("Front", {}).get("value", "")),
                    "back": clean(f.get("Back", {}).get("value", "")),
                    "old_deck": ", ".join(sorted(old.get(n["noteId"], ()))),
                    "deck": deck})
    return out


if __name__ == "__main__":
    mcp.run()
