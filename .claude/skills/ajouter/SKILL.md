---
name: ajouter
description: Add one or more French words or expressions to the user's Anki "Français" deck — lemmatize, check for duplicates, find near-synonyms already in the deck, and pick the card type so synonyms don't collide. Use when the user wants to add, create, or save French vocabulary / flashcards / cards to Anki.
allowed-tools: mcp__anki__list_decks, mcp__anki__search_deck, mcp__anki__word_frequency
---

The user wants to add this French vocabulary to Anki: **$ARGUMENTS**

Tools come from the `anki` MCP server: `list_decks`, `search_deck`, `word_frequency`, `add_note`. There is no delete tool, by design. The server's `update_note` tool exists only for fixes the user explicitly asks for — this skill **never** changes, suspends, or deletes existing cards, and never talks to AnkiConnect any other way. If a tool errors with a connection failure, tell the user to open Anki.

Division of labour (do not blur it): **you** produce lemmas, glosses, and synonym candidates; **`word_frequency`** produces every frequency number. Never estimate frequency yourself.

## Steps

1. **Normalize each entry.** If it looks like a typo or a run-together form (`unsigle` → *un sigle*), correct it and say so. **Classify the whole entry** — fixed expression, verb, noun (proper / definite / plural-only / uncountable / countable), adjective, or adverb — using the rules in [formatting.md](formatting.md); the category applies to the whole phrase, not just its head word. **Ignore the user's article:** an article or determiner typed with a noun (`le`, `la`, `l'`, `un`, `une`, `des`, `du`, `de la`) doesn't tell you the noun's type. Remove it, classify the bare noun from scratch (proper → usually definite → plural-only → uncountable → countable, per formatting.md §4), and choose the article from that type — e.g. `la cicatrice` → `une cicatrice.s`, `une presse` → `la presse`, `un blé` → `du blé`. Use the typed article only to work out the gender, or which word was meant, when the bare form is ambiguous. Determine its search lemma (the bare masculine singular without article — noting the gender; the infinitive of a verb phrase, keeping *se*, negation, pronouns and a governed preposition such as *se fier à*; a fixed expression as given), its main English gloss(es), and the French near-synonyms that mean basically the same thing, each with its English gloss.

2. **Ask for the subdeck** — once per invocation. Call `list_decks` and ask with AskUserQuestion which deck the new cards go into.

3. **Duplicate check.** `search_deck` with the lemma (and the entry as written) on `field="front"`. Matching is substring-based, so search the bare masculine stem — `citadin` finds `un.e citadin.e.s`, `citadine` does not. Any hit with `exact: true` is a duplicate: report it (front, back, deck) and skip that entry unless the user asks to add it anyway. Also mention close non-exact hits that look like the same word.

4. **Find synonyms in the deck.** `search_deck` with your French synonyms on `field="front"`, and with the English glosses on `field="back"`. Keep only hits that really mean basically the same thing as the new word — discard loose matches (e.g. *se confier à* "to confide in" is not a synonym of *se fier à* "to trust"; *une confiance* "trust" is a noun, not a synonym of a verb).

5. **Choose the card type.** The synonym group = the new word + the kept deck hits (+ any other new entries in this invocation that are synonyms of each other). Call `word_frequency` on every lemma in the group. Then:
   - No synonyms, or the new word has the highest zipf in its group → `card_type: "both"` (Basic and reversed: French→English and English→French).
   - Otherwise → `card_type: "fr_to_en"` (Basic: French→English only), so English→French recall is never ambiguous.
   - If the new word is the most common **and** an existing synonym's `model` is `Basic (and reversed card)`, add the new word as `both` and **report** the conflict: suggest the user suspend that existing note's reverse card in Anki. Do not change it yourself.
   - Ties (same zipf): prefer the more idiomatic everyday expression and say it was a tie.

6. **Format like the existing deck.**
   Format the front and back by category, following [formatting.md](formatting.md) exactly — articles per noun type (`un.e citadin.e.s`, `de l'incompréhension`, `des vacances`, `la presse`), dot notation for adjectives (`blanc.he.s`, split as `beau.x (bel), belle.s`), infinitives for verb phrases (`ne pas arriver à y croire`), fixed expressions verbatim (`je vous en prie`), adverbs as is. Back: `a scar`, `incomprehension`, `to trust`. For a `fr_to_en` card, you may add a short contrast in parentheses with the more common synonym, e.g. `to trust (≈ faire confiance à)`.

7. **Preview and confirm.** Show a table — Front | Back | Category | Card type | Deck | Synonym group with zipf scores | Reason — plus any duplicates skipped and conflicts found. If a front's article differs from the one the user typed, say so in Reason (e.g. "typed *la cicatrice*; countable → *une cicatrice.s*"). Ask the user to confirm (or edit) before adding anything.

8. **Add.** Call `add_note` once per confirmed card. Report the resulting note ids and repeat any conflicts the user should fix by hand. New cards go to the end of the new-card queue; mention that the frequency-sort notebook can reorder them later.
