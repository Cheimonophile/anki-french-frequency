---
name: ajouter
description: Add one or more French words or expressions to the user's Anki "Français" deck — lemmatize, check for duplicates, find near-synonyms already in the deck, and pick the card type so synonyms don't collide. Use when the user wants to add, create, or save French vocabulary / flashcards / cards to Anki.
allowed-tools: mcp__anki__list_decks, mcp__anki__search_deck, mcp__anki__word_frequency
---

The user wants to add this French vocabulary to Anki: **$ARGUMENTS**

Tools come from the `anki` MCP server: `list_decks`, `search_deck`, `word_frequency`, `add_note`. There is no delete or edit tool, by design — **never** change, suspend, or delete existing cards, and never talk to AnkiConnect any other way. If a tool errors with a connection failure, tell the user to open Anki.

Division of labour (do not blur it): **you** produce lemmas, glosses, and synonym candidates; **`word_frequency`** produces every frequency number. Never estimate frequency yourself.

## Steps

1. **Normalize each entry.** If it looks like a typo or a run-together form (`unsigle` → *un sigle*), correct it and say so. Determine its lemma (noun: masculine-singular form without article — but note its gender; verb: infinitive, keeping *se* and a governed preposition such as *se fier à*; adjective: masculine singular), part of speech, its main English gloss(es), and the French near-synonyms that mean basically the same thing, each with its English gloss.

2. **Ask for the subdeck** — once per invocation. Call `list_decks` and ask with AskUserQuestion which deck the new cards go into.

3. **Duplicate check.** `search_deck` with the lemma (and the entry as written) on `field="front"`. Any hit with `exact: true` is a duplicate: report it (front, back, deck) and skip that entry unless the user asks to add it anyway. Also mention close non-exact hits that look like the same word.

4. **Find synonyms in the deck.** `search_deck` with your French synonyms on `field="front"`, and with the English glosses on `field="back"`. Keep only hits that really mean basically the same thing as the new word — discard loose matches (e.g. *se confier à* "to confide in" is not a synonym of *se fier à* "to trust"; *une confiance* "trust" is a noun, not a synonym of a verb).

5. **Choose the card type.** The synonym group = the new word + the kept deck hits (+ any other new entries in this invocation that are synonyms of each other). Call `word_frequency` on every lemma in the group. Then:
   - No synonyms, or the new word has the highest zipf in its group → `card_type: "both"` (Basic and reversed: French→English and English→French).
   - Otherwise → `card_type: "fr_to_en"` (Basic: French→English only), so English→French recall is never ambiguous.
   - If the new word is the most common **and** an existing synonym's `model` is `Basic (and reversed card)`, add the new word as `both` and **report** the conflict: suggest the user suspend that existing note's reverse card in Anki. Do not change it yourself.
   - Ties (same zipf): prefer the more idiomatic everyday expression and say it was a tie.

6. **Format like the existing deck.**
   - Front (French): nouns with their indefinite article and the deck's plural marker — `un tatouage.s`, `une cicatrice.s`, `une proposition.s relative.s` (use `.x` for -x plurals such as `un bateau.x`, and the full plural when irregular). Verbs as the infinitive with *se* / preposition: `se fier à`. Adjectives in masculine form (add the feminine ending if it's irregular).
   - Back (English): `a scar`, `to trust`. For a `fr_to_en` card, you may add a short contrast in parentheses with the more common synonym, e.g. `to trust (≈ faire confiance à)`.

7. **Preview and confirm.** Show a table — Front | Back | Card type | Deck | Synonym group with zipf scores | Reason — plus any duplicates skipped and conflicts found. Ask the user to confirm (or edit) before adding anything.

8. **Add.** Call `add_note` once per confirmed card. Report the resulting note ids and repeat any conflicts the user should fix by hand. New cards go to the end of the new-card queue; mention that the frequency-sort notebook can reorder them later.
