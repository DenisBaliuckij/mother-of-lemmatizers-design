# Lemmatizer requirements: Spanish

*Spanish · glottocode `stan1288` · ISO 639-3 `spa` · Tier A (rules exist) · status: draft*

Spanish is fusional, with a rich verb conjugation, stem-vowel alternations, enclitic object pronouns and distinctive written accents. The requirements below are 20 properties of the language that the lemmatizer must handle. They are grouped by topic, and each names the Tier A component ([section 5](../../en/05-lemmatizing-with-existing-rules-tier-a.md)) it falls on. Two requirements are not covered by the language-resource ontology; both concern the enclitic clitics, which split a single orthographic word across several lemmas.

This file follows the Hungarian worked example; the requirement IDs (ES-01, ES-02, …) are assigned here and do not change. Refer to them in discussions ("ES-14: …").

**Tier A components** named in the tables:

- **rules**: the rule-based analyzer (paradigm templates) and alternation rules;
- **lexicon**: the lemma dictionary and exception tables;
- **guesser**: analysis of unknown words by productive affixes;
- **context**: choosing an analysis from context;
- **preprocessing**: tokenization and normalization before analysis;
- **features**: grammatical features in the output.

## Requirements

### Orthography

| ID | Requirement | Example | Component |
|---|---|---|---|
| ES-01 | Written accents are distinctive and must not be stripped: they mark stress and distinguish words | *papá* "dad" ≠ *papa* "potato"; *sí* ≠ *si* | preprocessing, lexicon |
| ES-02 | ñ is a distinct letter from n, and ü (in *güe/güi*) is distinct from u; do not normalize them away | *año* "year" ≠ *ano* | preprocessing |

### Morphophonology and stem alternations

| ID | Requirement | Example | Component |
|---|---|---|---|
| ES-03 | Stress and its written accent shift across a paradigm, so the lemma may differ in accentuation from the form | *nación* → *naciones* | rules |
| ES-04 | Orthographic stem changes keep the sound before an ending: c→qu, g→gu, z→c, gu→gü; reverse them to recover the infinitive | *busqué* → *buscar*, *pagué* → *pagar* | rules |
| ES-05 | Stem-vowel alternations (e→ie, o→ue, e→i) in stressed stems; recover the infinitive | *pienso* → *pensar*, *puedo* → *poder*, *pido* → *pedir* | rules, lexicon |

### Nominal and adjectival morphology

| ID | Requirement | Example | Component |
|---|---|---|---|
| ES-06 | Fusional affixes: one ending encodes several features at once; do not strip it morpheme by morpheme | -os = masculine + plural | rules, features |
| ES-07 | Grammatical gender (masculine/feminine): the gender is a lexical property of the noun; the lemma is its citation form | *niño* / *niña* | rules, features |
| ES-08 | Number: plural -s/-es, with the spelling change z→ces; recover the singular lemma | *luces* → *luz* | rules |
| ES-09 | Adjectives agree in gender and number; the lemma is the masculine singular | *rojas* → *rojo* | rules, features |
| ES-10 | -mente adverbs are productive (feminine adjective + -mente); define the lemma policy | *rápidamente* (base *rápido*) | rules, lexicon |

### Verbal morphology

| ID | Requirement | Example | Component |
|---|---|---|---|
| ES-11 | Rich fusional conjugation in three classes (-ar/-er/-ir); strip person, number, tense and mood to the infinitive lemma | *hablábamos* → *hablar* | rules, features |
| ES-12 | Many tenses and moods, including the subjunctive; the same stem takes different endings, sometimes told apart only by the accent | *hable* (subj) vs *hablé* (past) | rules, features |
| ES-13 | Irregular and suppletive verbs (ser, ir, haber): forms may share no stem with the lemma | *fue* → *ir*/*ser*, *voy* → *ir* | lexicon |
| ES-14 | Enclitic object pronouns (me, te, lo, la, le, se, nos, os …) attach to the imperative, infinitive and gerund and can stack; split them off | *dámelo* = da + me + lo → *dar* | preprocessing, rules |
| ES-15 | Enclisis can add or shift the written accent; reverse it to recover the verb form | *dámelo* → *dar*, *cómpramela* → *comprar* | preprocessing, rules |
| ES-16 | Non-finite forms (infinitive, gerund -ndo, participle -do) normalize to the infinitive lemma | *comiendo* → *comer* | rules |

### Derivation and lexicon

| ID | Requirement | Example | Component |
|---|---|---|---|
| ES-17 | Do not mix derivation and inflection: the ontology keeps these processes apart | — | rules |
| ES-18 | Diminutives/augmentatives and the superlative -ísimo are productive; decide the lemma policy | *casita* → *casa*? | rules, lexicon |
| ES-19 | The clitic *se* is multifunctional (reflexive, impersonal, passive, the spurious le→se); do not over-strip or mis-lemmatize it | *se lava* | rules, context |

### Context

| ID | Requirement | Example | Component |
|---|---|---|---|
| ES-20 | The interpretation of *se* and of the object clitics, and *lo* (neuter vs masculine), needs context; this is not the lemma itself | — | context |

## What this means for the architecture

- **Most requirements fall on the rule-based analyzer.** The conjugation classes, spelling changes and stem-vowel alternations (ES-03–ES-09, ES-11, ES-12, ES-16) are paradigm templates and alternation rules from the grammar store, as Tier A intends.
- **Enclitic pronouns split one token into several lemmas.** ES-14 and ES-15 turn *dámelo* into the verb *dar* plus two pronouns; the contract in section 9 returns one lemma per token, so it needs a way to emit several lemmas for a single written word (the mirror image of the Hungarian multi-token lemma HU-17).
- **Exception tables need a place in the grammar store.** Suppletive verbs (ES-13) are a list, not a rule, like the Hungarian case.
- **Some requirements concern features, not the lemma.** ES-06 (fused features), ES-07 (gender) and ES-09 (agreement) change the output features while the lemma stays the same.
- **The clitic *se* needs the context module.** ES-19 and ES-20 cannot be resolved inside one token; the reflexive, impersonal and passive readings depend on the clause.

## Gaps in the ontology

Two requirements are not reflected in the language-resource ontology. They must be added for the profile to support a reliable lemmatizer.

| ID | What is missing |
|---|---|
| ES-14 | Object clitics are described as words, but there is no rule splitting an enclitic chain off a single written verb form (*dámelo* → *dar* + *me* + *lo*) and emitting several lemmas for one token |
| ES-15 | The stress rules are described, but no rule reverses the accent that enclisis adds or shifts (*da* → *dámelo*), which is needed to match the verb form back to its paradigm |

## Proposed profile subsections

Machine-readable version: [`profile.yaml`](profile.yaml).

1. **stem_spelling_changes:** the orthographic alternations c→qu, g→gu, z→c, gu→gü before front-vowel endings.
2. **stem_vowel_changes:** the diphthongization/raising rules e→ie, o→ue, e→i.
3. **enclitic_pronouns:** the clitic list and the rule for splitting the chain off the verb and restoring its accentuation.
4. **exception_tables:** the suppletive verbs (*ir*, *ser*, *haber*), with a note that *fue* is ambiguous between *ir* and *ser*.

## Existing rule-based analyzers

Candidates Tier A can build on for Spanish. The assessments were not tested.

| Analyzer | Type | What it gives | Links |
|---|---|---|---|
| FreeLing | rule-based analyzer and lemmatizer | morphological analysis, lemmas, PoS for Spanish | [website](https://nlp.lsi.upc.edu/freeling/) |
| apertium-spa | finite-state transducer (FST), a module of Apertium | a large hand-written Spanish morphology | [GitHub](https://github.com/apertium/apertium-spa) |
| spaCy (es_core_news) | lemma rules + lookup tables | community Spanish models | [models](https://spacy.io/models/es) |
| UDPipe (Spanish models) | lexicon + suffix stripping for unknown words | trained on the Spanish UD treebanks (AnCora, GSD) | [models](https://ufal.mff.cuni.cz/udpipe/models) |
| Stanza (Spanish) | neural tagger/lemmatizer | lemmas and UD analysis for Spanish | [website](https://stanfordnlp.github.io/stanza/) |
| Hunspell (es-ES) | spellchecker; the .aff/.dic files define affix rules | lemma via hunspell-stem or wrappers | [LibreOffice dictionaries](https://github.com/LibreOffice/dictionaries) |

## Test cases

The examples from the requirements are collected in [`test-cases.tsv`](test-cases.tsv): form, context, expected lemma, expected features (where unambiguous) and requirement IDs. They can be run against every version of the Spanish Tier A grammar ([section 11](../../en/11-evaluation.md)).

## Notes on the transfer

- **Verb lemma.** The expected lemmas use the infinitive (*hablar*, *comer*), following the Spanish UD convention.
- **Enclitic forms.** For forms like *dámelo* the test case gives the verb lemma (*dar*); a full analysis would also emit the clitics *me* and *lo* as separate lemmas, which the one-lemma-per-token contract cannot yet express (see ES-14).
- **fue.** *fue* is ambiguous between *ir* and *ser*; the test case uses context and flags it.
- **ES-18 diminutive lemma.** Whether *casita* lemmatizes to *casa* or stays *casita* depends on the UD convention; the test case assumes *casa* and flags it.
- **Examples.** The examples were added for this draft and need checking by a native speaker or specialist.

## Sources

- Spanish grammar. Wikipedia. <https://en.wikipedia.org/wiki/Spanish_grammar>
- Spanish language. Wikipedia. <https://en.wikipedia.org/wiki/Spanish_language>
- Spanish verbs. Wikipedia. <https://en.wikipedia.org/wiki/Spanish_verbs>
- Butt, J. & Benjamin, C. (2011). *A New Reference Grammar of Modern Spanish*. Routledge.
- Real Academia Española. *Nueva gramática de la lengua española*. <https://www.rae.es/>
