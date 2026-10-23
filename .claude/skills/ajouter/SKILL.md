---
name: ajouter
description: Add one or more French words or expressions to the user's Anki "Français" deck — lemmatize, check for duplicates, find near-synonyms already in the deck, and pick the card type so synonyms don't collide. Use when the user wants to add, create, or save French vocabulary / flashcards / cards to Anki, or to suspend, unsuspend, or move one of its cards.
allowed-tools: AskUserQuestion, mcp__anki__list_decks, mcp__anki__search_deck, mcp__anki__word_frequency
---

The user wants to add this French vocabulary to Anki: **$ARGUMENTS**

Tools come from the `anki` MCP server: `list_decks`, `search_deck`, `word_frequency`, `add_note`, `suspend_card`, `unsuspend_card`, `change_deck`. There is no delete tool, by design. The server's `update_note` tool exists only for fixes the user explicitly asks for (see "Editing an existing card" below) — this skill **never** changes existing cards on its own initiative: it suspends a card only when the user approves it in step 7 or asks for it (see "Suspending or unsuspending a card" below), moves notes to another deck only when the user asks (see "Moving a card to another deck" below), never deletes, and never talks to AnkiConnect any other way. If a tool errors with a connection failure, tell the user to open Anki.

Division of labour (do not blur it): **you** produce lemmas, glosses, and synonym candidates; **`word_frequency`** produces every frequency number. Never estimate frequency yourself.

## Steps

1. **Normalize each entry.** If it looks like a typo or a run-together form (`unsigle` → *un sigle*), correct it and say so. **Classify the whole entry** — fixed expression, verb, noun (proper / definite / plural-only / uncountable / countable), adjective, or adverb — using the rules in [formatting.md](formatting.md); the category applies to the whole phrase, not just its head word. **Ignore the user's article:** an article or determiner typed with a noun (`le`, `la`, `l'`, `un`, `une`, `des`, `du`, `de la`) doesn't tell you the noun's type. Remove it, classify the bare noun from scratch (proper → usually definite → plural-only → uncountable → countable, per formatting.md §4), and choose the article from that type — e.g. `la cicatrice` → `une cicatrice.s`, `une presse` → `la presse`, `un blé` → `du blé`. Use the typed article only to work out the gender, or which word was meant, when the bare form is ambiguous. Determine its search lemma (the bare masculine singular without article — noting the gender; the infinitive of a verb phrase, keeping *se*, negation, pronouns and a governed preposition such as *se fier à*; a fixed expression as given), its English gloss, and the French near-synonyms that mean basically the same thing, each with its English gloss.

   **Gloss the core meaning only:** the word's literal, primary sense, as the **one** closest English equivalent (`abattre` → `to knock down`). Add an English cognate as a second word only if the closest word isn't one and the cognate means the same thing, apart from nuance such as register or rarity (`aider` → `to help, to aid`). A cognate with a different meaning stays off the card (`demander` → `to ask`, not *to demand*). The full rule is in formatting.md §7. Leave out figurative, extended, and specialised senses (*abattre*: to slaughter, to shoot down, to demoralise) unless the user asks for them — except common context-only senses, which get their own card (next paragraph). Look for synonyms (step 4) of the core meaning only.

   **Context-only senses get their own card.** Some common senses exist only in a particular context: *décrocher* is to unhook, but with the phone it means to pick up, and with a job, to land. Keep these off the base card (`décrocher` → `to unhook`) and propose a separate **context card** for each common one (usually one or two), even if the user didn't ask:
   - **Front:** the most common French phrase for that meaning in that context, which may use a different word — `répondre au téléphone`, not `décrocher le téléphone`. Pick it with the step 5 winner rule; the candidates are the word's own phrase, the usual alternatives, and any deck cards with that meaning found in steps 3–4 (*décrocher un emploi*, *trouver un emploi*, *se trouver une job* → `se trouver une job`). If a deck card wins, the sense is already covered: report it and propose no card.
   - **Back:** the closest English phrase for the whole thing, by the same one-gloss rule, with no parentheses (`to answer the phone`, `to find a job`).
   - From step 3 on, each context card is its own entry: its own duplicate check, synonym search, card type, and confirmation question. Propose it even when the base word is a duplicate.
   - This is for senses you split off a word. A phrase the user typed (`décrocher le téléphone`) is added as typed; if a more common phrase exists, offer it as the alternative option in step 7.

   **Several core meanings:** if the word has two or more unrelated core meanings, where neither comes from the other and a learner would want both (*un avocat*: a lawyer / an avocado; *une capsule*: a bottle cap / a space capsule), say so and ask with `AskUserQuestion` before going further with that entry. This question can go in the same call as the step 2 deck question. Give one option per meaning, plus "Both on one card" with a combined back (`a lawyer; an avocado`). There is no "separate cards" option, because Anki rejects duplicate Fronts. Use the chosen meaning for the gloss, the synonym search, and the frequency group. This is only for meanings the bare word has on its own; context-only senses get context cards (above).

2. **Ask for the subdeck** — once per invocation. Call `list_decks` and ask with AskUserQuestion which deck the new cards go into.

3. **Duplicate check.** `search_deck` with the lemma (and the entry as written) on `field="front"`. Matching is substring-based, so search the bare masculine stem — `citadin` finds `un.e citadin.e.s`, `citadine` does not. Any hit with `exact: true` is a duplicate: report it (front, back, deck) and skip that entry unless the user asks to add it anyway. Also mention close non-exact hits that look like the same word. If a reported hit uses old notation (see formatting.md, "Old notation → current") — on its front, or a French synonym on its back — say in one line that it can be reformatted if the user wants; don't offer more than that. For a context card, also look at the base word's card: if its back still lists that sense (`décrocher` → `to pick up (the phone); to unhook; to land (a job)`), say in one line that it can be trimmed to the core meaning if the user wants, and offer nothing more.

4. **Find synonyms in the deck.** `search_deck` with your French synonyms on `field="front"`, and with the English glosses on `field="back"`. Keep only hits that really mean basically the same thing as the new word — discard loose matches (e.g. *se confier à* "to confide in" is not a synonym of *se fier à* "to trust"; *une confiance* "trust" is a noun, not a synonym of a verb).

5. **Choose the card type.** The synonym group = the new word + the kept deck hits (+ any other new entries in this invocation that are synonyms of each other). Call `word_frequency` on every lemma in the group. The group's **winner** is chosen this way:
   - **Canadian usage first.** The user is learning French in Canada. If one member of the group is the usual Canadian (Québécois) term and the others are mainly European French (*fin de semaine* vs *week-end*, *courriel* vs *e-mail*), that member wins even if its zipf is lower, because Lexique's corpus is mostly European. Still show every zipf score, and say in Reason that Canadian usage overrode zipf (e.g. "Canadian usage; *week-end* has higher zipf in Lexique").
   - Otherwise, the member with the highest zipf wins.
   - Ties (same zipf): prefer the Canadian term, then the more idiomatic everyday expression, and say it was a tie.

   Then:
   - No synonyms, or the new word is the winner → `card_type: "both"` (Basic and reversed: French→English and English→French).
   - Otherwise → `card_type: "fr_to_en"` (Basic: French→English only), so English→French recall is never ambiguous.
   - If the new word is the winner **and** an existing synonym's `model` is `Basic (and reversed card)`, add the new word as `both`. That synonym's reverse card now competes for the same English prompt, so make it a **suspend candidate** for step 7 — unless its search hit already lists `en_to_fr` in `suspended`.

6. **Format like the existing deck.**
   Format the front and back by category, following [formatting.md](formatting.md) exactly — articles per noun type (`un.e citadin.e.s`, `de l'incompréhension`, `des vacances`, `la presse`), dot notation for adjectives (`blanc.he.s`, split as `beau.x (bel), belle.s`), infinitives for verb phrases (`ne pas arriver à y croire`), fixed expressions verbatim (`je vous en prie`), adverbs as is. Back: `a scar`, `incomprehension`, `to trust`. Never add a French synonym to the back (`to trust (≈ faire confiance à)`, `others (= les autres)`): the card type keeps synonyms apart (step 5).

7. **Preview and confirm — always, with the `AskUserQuestion` tool.** First show a table — Front | Back | Category | Card type | Deck | Synonym group with zipf scores | Reason — plus any duplicates skipped and conflicts found. If a front's article differs from the one the user typed, say so in Reason (e.g. "typed *la cicatrice*; countable → *une cicatrice.s*"). If you left out other senses, say so too (e.g. "core meaning; omitted *to slaughter*, *to shoot down*"). Likewise name any English equivalents you dropped, and any cognate you left off (e.g. "closest *to advocate*; dropped *to champion*", "*to demand* is a false friend, left off"). For a context card, say which word and sense it comes from, with the candidates' zipf scores (e.g. "context sense of *décrocher*; *décrocher le téléphone* 4.40").

   Then confirm every card with the **`AskUserQuestion`** tool, never with a plain-text question in chat. Do this every time: for a single card, and even if the user said "just add it".
   - Ask one question per card, naming the lemma, with the short lemma as the header (≤12 chars). The tool takes at most 4 questions per call, so if there are more than 4 cards, make several calls.
   - Use single-select options. Each option has a `preview` showing the card exactly as it will be created:
     ```
     Front: un.e citadin.e.s
     Back:  a city dweller
     Type:  Basic (and reversed card)
     Deck:  Français::Vocab
     ```
   - Options: **"Add as shown (Recommended)"** and **"Skip this card"**. If there's a real alternative (the other card type, a different article, or a runner-up gloss when two English words are a real toss-up), add it as a third option with its own preview. The user can always pick "Other" to type edits.
   - If the user edits a card, apply the edit and confirm the changed card again with `AskUserQuestion` before adding it.
   - For each suspend candidate (step 5), ask one more question in the same calls, with the synonym's short front as the header. Its preview shows the existing note:
     ```
     Front: percuter
     Back:  to hit; to crash into
     Deck:  Français::2 Vie Quotidienne
     Reverse card (English→French): active → suspended
     ```
     Options: **"Suspend reverse card (Recommended)"** and **"Leave it active"**. These questions count toward the 4-per-call limit.

8. **Add.** Add only the cards the user approved through `AskUserQuestion` in step 7. Call `add_note` once per approved card, with exactly the Front, Back, card type, and deck shown in its approved preview. Then call `suspend_card(note_id, "en_to_fr")` for each suspend candidate the user approved whose new card was added. Report the resulting note ids and each suspension (front, `was_suspended → suspended`). A candidate the user left active is still a conflict: mention it once more. New cards go to the end of the new-card queue; mention that the frequency-sort notebook can reorder them later.

## Editing an existing card

Only when the user explicitly asks to change a specific existing note (a new gloss, a removed sense, a fixed front). Never edit a card just because it showed up as a duplicate or synonym hit.

1. **Apply the requested change** to Front and/or Back. If it removes a context-only sense from the back, propose a context card for that sense (see Steps, step 1) in the same `AskUserQuestion` call, going into the edited note's deck.
2. **Normalize to current notation** in the same edit, even if the user only asked about one field: re-classify the entry (formatting.md §1, §4) and rewrite old markers per formatting.md, "Old notation → current" — e.g. `une part parts` → `une part.s`, `un(e) photographe(s)` → `un.e photographe.s`, `une fête/s` → `une fête.s`, `inhabituel, inhabituelle inhabituels, inhabituelles` → `inhabituel.le.s`, `participant/e/s` → `un.e participant.e.s`. On the back, remove a French synonym in parentheses (`from now on (≈ désormais)` → `from now on`). Normalize the back's *form* (its article or `to`) only where §7 calls for it (`graphic artist` → `a graphic artist` on a countable noun); don't drop glosses or change its meaning beyond what the user asked — propose any sense change as a separate option.
3. **Duplicate check on the new front.** `search_deck` with the bare stem on `field="front"`. If a *different* note already has the normalized front (`exact: true`), report it and keep the old notation rather than create a duplicate front.
4. **Confirm with `AskUserQuestion`**, one question per note. The preview shows `old → new` for each changed field and marks the reformatting apart from the requested change:
   ```
   Front: une part parts  →  une part.s   (notation)
   Back:  a share a piece; a slice  →  a piece; a slice (of cake, pizza)
   ```
   Options: **"Update as shown (Recommended)"**, **"Only the requested change"** (keeps the old notation; preview it), and **"Don't change it"**.
5. **Update.** Call `update_note` with exactly the approved fields and report old → new from its result. If it raises because the note didn't change, tell the user to close the Anki Browser and retry.

## Suspending or unsuspending a card

Only when the user asks to suspend or unsuspend a specific card (e.g. "suspend the reverse of *percuter*"). The request is the confirmation, and the change is reversible.

1. **Find the note** with `search_deck` on `field="front"`. If more than one note could be the one meant, ask with `AskUserQuestion` which.
2. **Pick the card.** "Reverse", "English→French", or no card named on a `Basic (and reversed card)` note → `en_to_fr`. "Forward" or "French→English" → `fr_to_en`. A `Basic` note has only `fr_to_en`.
3. **Call** `suspend_card` or `unsuspend_card` and report the front, the card, and `was_suspended → suspended` from its result.

## Moving a card to another deck

Only when the user asks to move specific notes to another deck (e.g. "put these in Vie Quotidienne" after adding them to the wrong one). The request is the confirmation, and the change is reversible. A note moves whole — both its cards.

1. **Find the notes.** Use the note ids from this session's `add_note` results, or `search_deck` on `field="front"`. If it's unclear which notes are meant, ask with `AskUserQuestion`.
2. **Pick the deck** from `list_decks`. If the user's name for it matches more than one deck, ask which.
3. **Call** `change_deck` once with all the note ids, and report the front and `old_deck → deck` for each note from its result. If it raises because cards didn't move, tell the user to close the Anki Browser and retry.
