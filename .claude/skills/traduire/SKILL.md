---
name: traduire
description: Translate a French word or expression into English — give the most common English translations ranked by real-world frequency of use, each with a bilingual example sentence and a note on nuance. Use when the user provides a French word or expression and wants its English meanings.
---

The user wants the English translation(s) of this French word or expression: **$ARGUMENTS**

Respond in French-and-English in this exact format:

1. **Header line** — the French word/expression in **bold**, followed by its part of speech in *italics* (e.g. *verbe*, *nom masculin*, *nom féminin*, *adjectif*, *expression*). If it is normally used pronominally (e.g. *se prélasser*) or only in a fixed construction, say so here.

2. **Translations ranked by frequency** — a numbered list of the most common English translations, ordered from the most frequent/idiomatic down to the rarest. Put the English term in **bold**, then a short gloss *in French* clarifying the sense or register (familier, soutenu, littéraire, vieilli, figuré, technique…).

3. **Example sentences** — for each distinct sense, one natural French sentence (target word in **bold**) immediately followed by its English translation, marked with `→`. Cover the different senses, not just the first one.

4. **Note (💡)** — a brief remark *in French* on nuance, register, common collocations, or false-friend traps. Include it only when it genuinely adds value.

Guidelines:
- Always pair French examples with their English translations, in the bilingual style above.
- Order the translations by real-world frequency of use, **not** alphabetically.
- If the input looks like a typo or a run-together form (e.g. `unsigle` → *un sigle*, `sepromener` → *se promener*), gently correct it first, then proceed with the corrected word.
- If the word has only one common sense, stay concise — don't pad with marginal meanings.
- If the input is several words/expressions at once, treat each one in turn using the same format.
