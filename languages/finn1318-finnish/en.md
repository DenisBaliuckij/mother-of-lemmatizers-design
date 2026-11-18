# Lemmatizer requirements: Finnish

*Finnish · glottocode `finn1318` · ISO 639-3 `fin` · Tier A (rules exist) · status: draft*

Finnish is agglutinative, with vowel harmony, consonant gradation, fifteen cases, possessive suffixes and stacking enclitics. The requirements below are 24 properties of the language that the lemmatizer must handle. They are grouped by topic, and each names the Tier A component ([section 5](../../en/05-lemmatizing-with-existing-rules-tier-a.md)) it falls on. Three requirements are not covered by the language-resource ontology; one of them (FI-16) also reaches into the context module, because negation splits the finite form across two words.

This file follows the Hungarian worked example; the requirement IDs (FI-01, FI-02, …) are assigned here and do not change. Refer to them in discussions ("FI-04: …").

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
| FI-01 | Vowel and consonant length is distinctive: single vs double letters are written out (a/aa, k/kk) and must not be normalized | *tuli* "fire" ≠ *tuuli* "wind" ≠ *tulli* "customs" | preprocessing, lexicon |
| FI-02 | ä, ö, y and a, o, u are distinct letters (the harmony pairs), not diacritic variants to be stripped | *pää* "head" ≠ *paa* | preprocessing, rules |

### Morphophonology and allomorphy

| ID | Requirement | Example | Component |
|---|---|---|---|
| FI-03 | Vowel harmony: back a/o/u vs front ä/ö/y, with neutral e/i; recover one morph behind two-way allomorphs -ssa/-ssä, -lla/-llä, -ko/-kö | *talossa*, *metsässä* → -ssa/-ssä | rules |
| FI-04 | Consonant gradation: reverse surface weakening (kk~k, pp~p, tt~t, t~d, k~∅, p~v, nt~nn) to recover the stem | *kukka* → *kukan*, *katu* → *kadun* | rules |
| FI-05 | The grade (strong/weak) depends on whether the following syllable is open or closed, so one stem alternates across its paradigm | *kukka* / *kukan* / *kukkaan* | rules |
| FI-06 | Stem-vowel alternations the chain cannot just cut off: e-stems (*vesi* ~ *vete-/vede-*) and the oblique plural -i-/-j- changing the stem vowel | *vesi* → *vedessä*, *talo* → *taloissa* | rules, lexicon |
| FI-07 | Store the abstract case morpheme, not the surface allomorphs: -ssa/-ssä is one inessive marker | -ssa/-ssä = inessive | rules, features |

### Nominal morphology

| ID | Requirement | Example | Component |
|---|---|---|---|
| FI-08 | Agglutination: analyze the suffix chain as a sequence of morphemes and strip them one by one | *taloissamme* = talo + i + ssa + mme | rules, guesser |
| FI-09 | Case is a separate layer; the usual count is 15 cases, including six local cases (inessive/elative/illative, adessive/ablative/allative) | *talossa*, *talosta*, *taloon* | rules, features |
| FI-10 | Possessive suffixes (-ni, -si, -nsa, -mme, -nne) combine with number and case; parse the case + possessive order | *taloni*, *talossani* | rules, features |
| FI-11 | No grammatical gender: *hän* is "he" and "she"; do not create gender-agreement rules | *hän* | rules |
| FI-12 | Number: nominative plural -t vs the oblique plural -i-/-j-; recover the singular lemma from both | *talot*, *taloissa* → *talo* | rules, features |
| FI-13 | The partitive is central and has allomorphs -a/-ä, -ta/-tä, -tta/-ttä; recover one marker | *taloa*, *vettä*, *perhettä* | rules |
| FI-14 | Pronouns: a table of irregular stems, since the oblique form may contain no obvious stem | *minua*, *minulle* → *minä* | lexicon |

### Verbal morphology

| ID | Requirement | Example | Component |
|---|---|---|---|
| FI-15 | Six verb types with different stem shapes; strip the personal endings (-n, -t, -mme, -tte, -vat) to the A-infinitive lemma | *puhun* → *puhua*, *menen* → *mennä* | rules, features |
| FI-16 | Negation uses the inflected auxiliary *ei* plus a connegative main verb; the main verb is not a full finite form, so the finite reading is split across two tokens | *en mene*, *ei puhu* | rules, context |
| FI-17 | Non-finite forms (infinitives, participles -nut/-va, agent nouns) normalize to the verb lemma | *puhunut* → *puhua* | rules |
| FI-18 | The impersonal/passive (-taan/-tään) reduces to the verb lemma while marking voice | *puhutaan* → *puhua* | rules, features |

### Clitics

| ID | Requirement | Example | Component |
|---|---|---|---|
| FI-19 | Enclitic particles (-kin, -kaan/-kään, -ko/-kö, -han/-hän, -pa/-pä, -s) attach after inflection and must be stripped before lemmatizing | *taloissakin*, *menetkö* | preprocessing, rules |
| FI-20 | A stripped clitic does not change the lemma but may carry its own feature (e.g. the question clitic); several can stack | *tulisikohan* | preprocessing, features |

### Derivation and lexicon

| ID | Requirement | Example | Component |
|---|---|---|---|
| FI-21 | Do not mix derivation and inflection: the ontology keeps these processes apart | — | rules |
| FI-22 | Productive compounding: otherwise a compound's component is taken for a lemma of its own | *kirjakauppa* | rules, lexicon |
| FI-23 | A table of suppletive and irregular stems is mandatory: some forms cannot be recovered by successive stripping | *parempi* → *hyvä* | lexicon |

### Context

| ID | Requirement | Example | Component |
|---|---|---|---|
| FI-24 | The object case (partitive vs genitive/accusative) depends on aspect and polarity; this is needed by the context module, not by the lemma itself | *luen kirjaa* / *luen kirjan* | context |

## What this means for the architecture

- **Most requirements fall on the rule-based analyzer.** Harmony, gradation, stem alternations and suffix chains (FI-03–FI-09, FI-12, FI-13, FI-15, FI-18) are paradigm templates and alternation rules from the grammar store, as Tier A intends.
- **Consonant gradation needs a paradigm-aware reverse rule.** FI-04 and FI-05 cannot be done by a lexical list alone: the grade depends on the syllable structure of the suffixed form, so the rule must know the paradigm slot.
- **Exception tables need a place in the grammar store.** Pronoun stems (FI-14) and suppletives (FI-23) are lists, not rules, like the Hungarian case.
- **Negation splits the finite form across two tokens.** FI-16 needs *ei* and the connegative verb read together; the contract in section 9 returns one lemma per token, so marking the connegative verb's polarity and tense needs the context module.
- **Some requirements concern features, not the lemma.** FI-07 (abstract morpheme), FI-12 (number) and FI-18 (voice) change the output features while the lemma stays the same.

## Gaps in the ontology

Three requirements are not reflected in the language-resource ontology. They must be added for the profile to support a reliable lemmatizer.

| ID | What is missing |
|---|---|
| FI-05 | Consonant gradation is listed as a phenomenon, but there is no computational rule tying the strong/weak grade to the open/closed syllable, which is what the reverse analysis needs |
| FI-16 | Negation is described as a verb, but there is no rule linking the auxiliary *ei* and the connegative main verb into one finite reading |
| FI-20 | Enclitic particles are listed, but the profile has no rule for stripping a stack of clitics (*tulisikohan*) after inflection |

## Proposed profile subsections

Machine-readable version: [`profile.yaml`](profile.yaml).

1. **vowel_harmony:** the back / front / neutral sets and the two-way allomorph pairs (-ssa/-ssä, -lla/-llä, -ko/-kö).
2. **gradation_rules (astevaihtelu):** the strong/weak alternations (kk~k, t~d, p~v, k~∅ …) and the rule that the grade follows the open/closed syllable.
3. **clitic_particles:** the list -kin, -kaan/-kään, -ko/-kö, -han/-hän, -pa/-pä, -s and the rule that they stack after inflection.
4. **exception_tables:** pronoun oblique stems (*minä* → *minua*, *minulle*) and suppletives (*hyvä* → *parempi*).

## Existing rule-based analyzers

Candidates Tier A can build on for Finnish. The assessments were not tested.

| Analyzer | Type | What it gives | Links |
|---|---|---|---|
| Omorfi | open-source finite-state transducer (FST) | morphological analysis and lemmas, built on the Giellatekno/HFST tooling | [GitHub](https://github.com/flammie/omorfi) |
| Voikko (libvoikko) | spellchecker + morphology (Suomi-malaga / Joukahainen lexicon) | lemma and analysis via the libvoikko API | [project page](https://voikko.puimula.org/) |
| apertium-fin | FST, a module of the Apertium platform | a hand-written Finnish morphology | [GitHub](https://github.com/apertium/apertium-fin) |
| UDPipe (Finnish models) | lexicon + suffix stripping for unknown words | trained on the Finnish UD treebanks (TDT, FTB) | [models](https://ufal.mff.cuni.cz/udpipe/models) |
| Turku neural parser pipeline | neural tagger/lemmatizer | lemmas and UD analysis for Finnish | [GitHub](https://github.com/TurkuNLP/Turku-neural-parser-pipeline) |
| Hunspell (fi-FI) | spellchecker; the .aff/.dic files define affix rules | lemma via hunspell-stem or wrappers | [Voikko/Hunspell dictionaries](https://voikko.puimula.org/) |

## Test cases

The examples from the requirements are collected in [`test-cases.tsv`](test-cases.tsv): form, context, expected lemma, expected features (where unambiguous) and requirement IDs. They can be run against every version of the Finnish Tier A grammar ([section 11](../../en/11-evaluation.md)).

## Notes on the transfer

- **Verb lemma.** The expected lemmas follow the Finnish UD convention (the A-infinitive, e.g. *puhua*, *mennä*). Dictionaries use the same citation form, so no separate convention is needed here.
- **Possessive ambiguity.** Forms such as *taloni* are ambiguous between nominative singular, nominative plural and genitive; the test cases prefer forms where case is overt (*talossani*).
- **FI-23 comparative lemma.** Whether *parempi* lemmatizes to *hyvä* (suppletion) or to *parempi* (its own lexeme) depends on the UD convention in force; the test case assumes *hyvä* and flags it.
- **Examples.** The examples were added for this draft and need checking by a native speaker or specialist.

## Sources

- Finnish grammar. Wikipedia. <https://en.wikipedia.org/wiki/Finnish_grammar>
- Finnish language. Wikipedia. <https://en.wikipedia.org/wiki/Finnish_language>
- Consonant gradation. Wikipedia. <https://en.wikipedia.org/wiki/Consonant_gradation>
- Karlsson, F. (2018). *Finnish: A Comprehensive Grammar*. Routledge.
- *Iso suomen kielioppi* (VISK), the online reference grammar. <https://kaino.kotus.fi/visk/>
