# Front formatting rules

How to write the French front (and English back) of a new card. Most examples
are real cards from the deck (a few, like `Paris` or `un œil<br>yeux`, are
illustrations). Follow the **recent** notation shown here; older
cards use `/s`, `(s)`, or both forms spelled out (`un fouet fouets`) on the
front, and a French synonym in parentheses on the back
(`from now on (≈ désormais)`) — don't copy those. When an existing card is
edited, rewrite its old notation:

## Old notation → current

| Old | Current | Example |
|---|---|---|
| plural spelled out | `.s` / `.x` marker | `une part parts` → `une part.s`, `un cadeau cadeaux` → `un cadeau.x` |
| `/s`, `(s)` | `.s` | `une fête/s` → `une fête.s` |
| `un/e`, `un(e)`, `/e`, `(e)` | `un.e`, `.e` | `un(e) photographe(s)` → `un.e photographe.s`, `un/e graphiste/s` → `un.e graphiste.s`, `violet/te/s` → `violet.te.s` |
| all four adjective forms spelled out | dot notation, or split form (§5) | `inhabituel, inhabituelle inhabituels, inhabituelles` → `inhabituel.le.s`, `inquiet, inquiète inquiets, inquiètes` → `inquiet.e.s` |
| `...ment` on the adjective's line | `...ment` on its own line (§5) | `fréquent.e.s ...ment` → `fréquent.e.s<br>...ment` |
| article missing or wrong for the noun's type | article per §4 | `participant/e/s` → `un.e participant.e.s` |
| French synonym in parentheses on the back: `(≈ …)`, `(= …)`, `(synonym: …)` | removed; the back keeps only its English gloss (§7) | `from now on (≈ désormais)` → `from now on`, `others (= les autres)` → `others` |

Irregular plurals keep the plural on its own line (`un œil<br>yeux`, §4), derived
adverbs keep `...ment` on its own line (`fréquent.e.s<br>...ment`, §5), and
adjectives that need it keep the split form (`beau.x (bel), belle.s`).

## 1. Classify the whole entry

The category applies to the **whole phrase**, not just its head word:
*ne pas arriver à y croire* is a verb, *une barrière linguistique* is a noun,
*ouvert d'esprit* is an adjective. Decide in this order:

1. **Fixed expression** — a frozen formula the speaker never conjugates or
   inflects: politeness formulas, set replies, interjections, exclamations,
   proverbs. Test: would a learner ever conjugate it in use? *Il n'arrivait
   pas à y croire* → yes → it's a verb phrase, not a fixed expression.
   *Je vous en prie* → no → fixed expression.
2. Otherwise, the part of speech of the phrase: **verb**, **noun**,
   **adjective**, or **adverb**.

## 2. Fixed expressions

Record exactly as given (lowercase the first letter unless it's a proper noun),
no article added, no infinitive:

`je vous en prie` · `un instant, s'il vous plaît` · `de rien` · `à tes souhaits`

## 3. Verbs and verb phrases

The infinitive of the whole phrase, keeping *se*, negation, object pronouns,
and the governed preposition:

`se fier à` · `ne pas arriver à y croire` · `ne pas en revenir` ·
`avoir du mal à suivre` · `être passionné.e.s par`

Keep the deck's placeholders for open slots: `avoir du mal à <infinitive>`,
`prêt.e.s <à>`. In the field they're escaped: `avoir du mal à
&lt;infinitive&gt;` (§8).

**Impersonal verbs** (only ever used with impersonal *il*) keep `il`, in the
present tense, instead of a bare infinitive: `il fait beau` · `il faut
<infinitive>` · `il y a`. They still conjugate in use (*il faisait beau*), so
they are verbs, not fixed expressions.

## 4. Nouns and noun phrases

Pick the first type that fits: **proper → usually definite → plural-only →
uncountable → countable**. Decide from the bare noun; the article in the
user's input doesn't count as evidence for the type (see SKILL.md step 1).

| Type | Front | Examples |
|---|---|---|
| Proper noun | no indefinite article; keep the definite article if the name takes one | `Paris`, `la France`, `le Moyen Âge` |
| Abstract, or rarely used indefinitely (singular or plural) | `le` / `la` / `l'` / `les` | `la presse`, `le bien-être`, `le télétravail`, `la mondialisation`, `l'ouverture d'esprit`, `les gros titres` |
| Plural-only (or effectively so) | `des` | `des vacances`, `des pâtes`, `des ciseaux`, `des retrouvailles`, `des données` |
| Uncountable | partitive `du` / `de la` / `de l'`, **no** plural marker | `du blé`, `du contenu`, `du bouche-à-oreille`, `de l'incompréhension` |
| Countable, one gender | `un` / `une` + plural marker | `une cicatrice.s`, `une gencive.s`, `un cadeau.x`, `un genou.x` |
| Countable, both genders | `un.e` + adjective-style gender marker + `.s` | `un.e citadin.e.s`, `un.e stagiaire.s` |

### Countable plural markers

| Plural | Marker | Examples |
|---|---|---|
| + s | `.s` | `une cicatrice.s`, `un foulard.s` |
| ‑eau, ‑eu, ‑ou (‑oux) → + x | `.x` | `un cadeau.x`, `un jeu.x`, `un bijou.x`, `un genou.x` |
| ‑al, ‑ail → ‑aux | `.x` (deck convention) | `un animal.x`, `un éditorial.x`, `un travail.x` |
| already ends in ‑s / ‑x / ‑z | no marker | `un pays`, `un prix`, `un nez` |
| irregular | singular, then the bare plural (no article) on a second line — write the break as `<br>` in the field | `un œil<br>yeux` |
| compounds | mark every part that pluralizes; *de*-complements stay singular | `un beau.x-père.s`, `une basse.s-cour.s`, `une proposition.s relative.s`, `un jeu.x de société`, `une barrière.s linguistique.s` |

### Both-gender nouns (people)

Use the adjective endings from §5 after the noun:
`un.e citadin.e.s` · `un.e informaticien.ne.s` · `un.e chasseur.se.s` ·
`un.e traducteur.rice.s` · `un.e chef.fe.s` · `un.e hôte.esse.s` ·
epicene (same form for both): `un.e stagiaire.s`, `un.e malade.s`.

## 5. Adjectives and adjective phrases

No article. Masculine singular, then `.feminine-ending`, then `.s`:

| Feminine | Marker | Examples |
|---|---|---|
| + e | `.e.s` | `fatigué.e.s`, `prêt.e.s`, `général.e.s` |
| ‑er → ‑ère, ‑et → ‑ète | `.e.s` (the grave accent is implied) | `fier.e.s`, `particulier.e.s`, `discret.e.s`, `inquiet.e.s`, `complet.e.s` |
| ‑el, ‑eil → ‑elle | `.le.s` | `actuel.le.s`, `ponctuel.le.s` |
| ‑et → ‑ette | `.te.s` | `violet.te.s`, `muet.te.s`, `net.te.s` |
| ‑ien, ‑on → ‑ienne | `.ne.s` | `péruvien.ne.s`, `aérien.ne.s` |
| ‑s → ‑sse, ‑x → ‑se, ‑eur → ‑euse | `.se.s` | `gros.se.s`, `heureux.se.s`, `travailleur.se.s` |
| ‑f → ‑ve | `.ve.s` | `actif.ve.s`, `veuf.ve.s` |
| ‑c → ‑che | `.he.s` | `blanc.he.s` |
| ‑teur → ‑trice | `.rice.s` | `révélateur.rice.s` |
| ‑g → ‑gue | `.ue.s` | `long.ue.s` |
| ‑gu → ‑guë | `.ë.s` | `aigu.ë.s`, `ambigu.ë.s` |
| ‑i → ‑ite | `.te.s` | `favori.te.s` |
| already ends in ‑e | `.s` only | `large.s` |

The masculine of ‑s/‑x adjectives doesn't change in the plural; the trailing `.s`
belongs to the feminine (`heureux.se.s` = heureux, heureuse, heureux, heureuses).
‑al adjectives don't show the ‑aux masculine plural: `général.e.s` (deck
convention, like `un animal.x` for nouns).

**Split side by side** when dot notation can't express the change (stem change,
an accent shift other than ‑er/‑et → ‑ère/‑ète, a special masculine form before
a vowel). Follow
`fou.s (fol), folle.s`: masculine with its plural marker, the pre-vowel
masculine in parentheses, then the feminine with its plural marker.

`beau.x (bel), belle.s` · `nouveau.x (nouvel), nouvelle.s` ·
`vieux (vieil), vieille.s` · `doux, douce.s` · `faux, fausse.s` ·
`frais, fraîche.s` · `sec.s, sèche.s` · `public.s, publique.s`

Phrases keep the markers on the adjective: `ouvert.e.s d'esprit`,
`fait.e.s maison`, `bien intentionné.e.s`.

### Derived adverbs (`...ment`)

When the adjective has a ‑ment adverb that means "in a [adjective] way", the card
gets a second line, `...ment`: write the break as `<br>` in the field. Never put
`...ment` on the adjective's line. This applies whether the user typed the
adjective or the adverb: the card is the adjective's, and its back is the
adjective's gloss only (§7).

`fréquent.e.s<br>...ment` → `frequent` · `discret.e.s<br>...ment` → `discreet` ·
`habile.s<br>...ment` → `skillful` · `doux, douce.s<br>...ment` → `soft`

The marker stands for the adverb even when its spelling is irregular
(*fréquemment*, *gentiment*, *brièvement*). An adverb whose core meaning isn't
the adjective's stays a plain adverb card (§6): `largement` (largely; *large* is
wide), `justement` (precisely), `carrément` (outright), `drôlement` (really).

## 6. Adverbs

An adverb formed from an adjective with ‑ment goes on the adjective's card (§5,
Derived adverbs). Other adverbs as they are: `largement` · `longtemps` ·
`là-bas` · `du coup`

## 7. Back (English)

| Category | Back | Examples |
|---|---|---|
| Countable noun | `a/an …` | `a scar`, `a city dweller` |
| Uncountable / abstract noun | no article | `incomprehension`, `well-being` |
| Definite noun for a specific thing | `the …` | `the press`, `the Middle Ages` |
| Plural-only noun | English plural (or mass noun) | `vacation`, `pasta`, `scissors`, `data` |
| Verb | `to …` | `to trust`, `to struggle to keep up` |
| Adjective / adverb | the English word | `dry`, `largely` |
| Adjective with `...ment` | the adjective's English word only | `frequent`, `discreet` |
| Fixed expression | the natural English equivalent | `one moment, please` |

Gloss the **core meaning only**, as **one English equivalent**: the one closest in
meaning, with no figurative or specialised senses. A second word goes on the line
only for an English cognate that means the same thing (next table), or when the
first word alone is ambiguous (the table after it):

| Case | Back | Examples |
|---|---|---|
| The closest word is itself the cognate | that word alone | `arriver` → `to arrive` |
| The closest word isn't a cognate, and a cognate means the same (differences of register or rarity are only nuance) | the closest word, then the cognate | `aider` → `to help, to aid` · `commencer` → `to start, to commence` · `vanter` → `to praise, to vaunt` |
| The cognate means something else (a false or partial friend) | the closest word only | `demander` → `to ask` (not *to demand*) · `rester` → `to stay` (not *to rest*) · `abattre` → `to knock down` (not *to abate*) |
| No cognate | the closest word only | `prôner` → `to advocate` |

**An ambiguous word gets company.** Read the back as a learner would, without
the French. If its word has another common sense, in the same part of speech,
that a reader could take instead, the gloss is ambiguous (`to` and `a/an`
already rule out another part of speech).

| Case | Back | Examples |
|---|---|---|
| The word's common senses all, or mostly, match the French word's | that word alone | `arriver` → `to arrive` |
| The closest word is ambiguous, but a close equivalent isn't | the unambiguous one alone | `visser` → `to screw in` (not *to screw*) |
| Every close equivalent is ambiguous | two of them, closest first, whose shared sense is the one meant; a third only if two still leave it open | `susciter` → `to arouse, to spark` (*arouse* alone reads as sexual, *spark* as setting alight) |

A cognate on the line counts as one of the words: `aider` → `to help, to aid`
needs nothing more.

A comma separates the words that gloss one meaning: the closest word, a cognate,
or a second word that settles an ambiguity. A semicolon only separates
unrelated core meanings the user chose to put on one card (`a lawyer; an
avocado`, SKILL.md step 1).

A sense that exists only in a context goes on its own context card (SKILL.md
step 1). Its back is the closest English phrase for the whole thing, by the
same rule, with no parentheses: `répondre au téléphone` → `to answer the phone`.
The base card keeps the core meaning: `décrocher` → `to unhook`.

Don't put a French synonym on the back: `to trust (≈ faire confiance à)`,
`others (= les autres)`, `there it is! (synonym: voilà)`. The card type keeps
synonyms apart (SKILL.md step 5).

## 8. Writing the fields (HTML)

Anki stores Front and Back as HTML, and `add_note` and `update_note` write the
text exactly as given. `<br>` is the only tag a field uses: it's the line break
(`un œil<br>yeux`). Escape every other `<`, `>` and `&`, or Anki reads it as
markup: a bare `<infinitive>` is an unknown tag, and the card shows nothing in
its place.

| Character | In the field | Example |
|---|---|---|
| `<` | `&lt;` | `être sur le point de <infinitive>` → `être sur le point de &lt;infinitive&gt;` |
| `>` | `&gt;` | `prêt.e.s <à>` → `prêt.e.s &lt;à&gt;` |
| `&` | `&amp;` | `R&D` → `R&amp;D` |

Accents, apostrophes, `!`, `?`, `…` and `« »` go in as they are.

Previews show a field the way this file writes it: `<br>` for a line break,
placeholders unescaped (`<infinitive>`). Only the tool call carries the escaped
form.

`search_deck` returns display text, with tags removed, entities decoded, and
line breaks as `\n`. When `update_note` rewrites a field taken from a search
hit, turn each `\n` back into `<br>` and escape the rest again. The same display
text shows whether a write came out right: a placeholder swallowed as a tag
leaves the front one word short (`être sur le point de`, no `<infinitive>`).
