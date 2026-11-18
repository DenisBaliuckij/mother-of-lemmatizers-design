# Lemmatizer requirements: Turkish

*Turkish · glottocode `nucl1301` · ISO 639-3 `tur` · Tier A (rules exist) · status: draft*

Turkish is agglutinative, with two vowel-harmony systems, a fixed suffix order, consonant softening and inserted buffer consonants. The requirements below are 24 properties of the language that the lemmatizer must handle. They are grouped by topic, and each names the Tier A component ([section 5](../../en/05-lemmatizing-with-existing-rules-tier-a.md)) it falls on. Three requirements are not covered by the language-resource ontology.

This file follows the Hungarian worked example; the requirement IDs (TR-01, TR-02, …) are assigned here and do not change. Refer to them in discussions ("TR-05: …").

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
| TR-01 | Dotted/dotless i (i/ı) and the pairs o/ö, u/ü, g/ğ, s/ş, c/ç are distinct letters, not diacritic variants to be normalized | *kış* "winter" ≠ *kis* | preprocessing, lexicon |
| TR-02 | Case folding is locale-specific: İ→i and I→ı; naive lowercasing destroys the stem | *İstanbul* → *istanbul*, not *ıstanbul* | preprocessing |

### Morphophonology and allomorphy

| ID | Requirement | Example | Component |
|---|---|---|---|
| TR-03 | Two-way (backness) harmony: the low-vowel suffix is realized -a/-e | *evde*, *okulda* | rules |
| TR-04 | Four-way (backness + rounding) harmony: the high-vowel suffix is realized -ı/-i/-u/-ü | *evi*, *kolu*, *gözü*, *kışı* | rules |
| TR-05 | Final-stop softening: p→b, ç→c, t→d, k→ğ before a vowel-initial suffix; reverse it to recover the stem | *kitap* → *kitabı*, *ağaç* → *ağacı* | rules |
| TR-06 | Suffix-initial consonant assimilates in voicing: -de/-te, -dir/-tir after a voiceless stem | *kitapta* vs *evde* | rules |
| TR-07 | Buffer consonants -y- and -n- are inserted to break vowel hiatus; remove them to recover the suffix | *kapı* → *kapıyı*, *ev-i-n-de* | rules |
| TR-08 | Store the abstract morpheme, not the surface allomorphs: the locative is one marker realized -de/-da/-te/-ta | locative = -DA | rules, features |

### Nominal morphology

| ID | Requirement | Example | Component |
|---|---|---|---|
| TR-09 | Agglutination: strip the suffix chain morpheme by morpheme | *evlerimizden* = ev + ler + imiz + den | rules, guesser |
| TR-10 | Fixed suffix order (plural – possessive – case): use the template to segment | *ev + ler + im + de* | rules |
| TR-11 | Possessive suffixes (-im, -in, -i, -imiz, -iniz, -leri) carry harmony and combine with number and case | *evim*, *evimiz* | rules, features |
| TR-12 | No grammatical gender: *o* is "he", "she" and "it"; do not create gender-agreement rules | *o* | rules |
| TR-13 | Plural -ler/-lar (by harmony); recover the singular lemma | *evler* → *ev*, *kitaplar* → *kitap* | rules, features |
| TR-14 | After a numeral the noun stays singular; do not tag it as plural | *üç ev* "three houses" | features, context |
| TR-15 | Pronouns: a table of irregular stems (*ben* → *ban-*, *bu* → *bun-*) | *bana* → *ben* | lexicon |

### Verbal morphology

| ID | Requirement | Example | Component |
|---|---|---|---|
| TR-16 | The verb is a suffix chain (voice – negation – tense/aspect – person); strip it to the verb stem (the lemma; dictionaries cite it with -mek/-mak) | *geliyordum* → *gel* | rules, features |
| TR-17 | Negation -me/-ma sits before the tense marker; recover the positive stem but mark polarity | *gelmiyor* → *gel*, Polarity=Neg | rules, features |
| TR-18 | The aorist and other tenses have allomorphs (-ir/-ar/-r), and person endings come from two paradigms | *gelir*, *yazar* | rules |
| TR-19 | Non-finite forms (infinitive -mek/-mak, participles, converbs -erek/-ince) reduce to the verb lemma | *gelince* → *gel* | rules |
| TR-20 | The question particle mı/mi/mu/mü is a separate clitic word (written apart) carrying harmony; do not attach it to the stem's lemma | *geliyor mu* | preprocessing, features |

### Derivation and lexicon

| ID | Requirement | Example | Component |
|---|---|---|---|
| TR-21 | Do not mix derivation and inflection: the ontology keeps these processes apart | — | rules |
| TR-22 | Productive derivation (-ci, -lik, -li, -siz): do not strip derivational suffixes as if they were inflectional | *işçi*, *evsiz* | rules, lexicon |
| TR-23 | A table of irregular stems: vowel drop (*ağız* → *ağz-*) and irregular buffering (*su* → *suy-*) | *ağzı* → *ağız* | lexicon |

### Context

| ID | Requirement | Example | Component |
|---|---|---|---|
| TR-24 | The accusative marks a definite/specific object; its presence is syntactic, needed by the context module, not by the lemma | *ev aldım* / *evi aldım* | context |

## What this means for the architecture

- **Most requirements fall on the rule-based analyzer.** The two harmony systems, softening, voicing assimilation, buffers and the fixed suffix order (TR-03–TR-11, TR-13) are paradigm templates and alternation rules from the grammar store, as Tier A intends.
- **The fixed suffix order is an asset.** Unlike the free order some languages allow, Turkish slots are deterministic (TR-10, TR-16), so a template segmenter is reliable once harmony and softening are reversed.
- **Exception tables need a place in the grammar store.** Pronoun stems (TR-15) and vowel-drop stems (TR-23) are lists, not rules, like the Hungarian case.
- **Some requirements concern features, not the lemma.** TR-08 (abstract morpheme), TR-13 (number) and TR-17 (polarity) change the output features while the lemma stays the same.
- **The question particle is a token of its own.** TR-20 is written separately, so tokenization must keep it apart rather than fold it into the verb lemma.

## Gaps in the ontology

Three requirements are not reflected in the language-resource ontology. They must be added for the profile to support a reliable lemmatizer.

| ID | What is missing |
|---|---|
| TR-05 | Final-stop softening is noted, but there is no computational reverse rule tying the surface voiced consonant to the underlying voiceless stem (*kitabı* → *kitap*) |
| TR-07 | The buffer consonants -y-/-n- are described phonologically, but no rule removes them during segmentation, so the suffix is mis-identified |
| TR-17 | Negation is described, but the infix -me/-ma inside the verb chain is not singled out as a slot the analyzer must strip while marking polarity |

## Proposed profile subsections

Machine-readable version: [`profile.yaml`](profile.yaml).

1. **case_folding:** the locale-aware rules İ→i, I→ı and the note that the paired letters are distinct.
2. **vowel_harmony:** the two-way archiphoneme A (-a/-e) and the four-way archiphoneme I (-ı/-i/-u/-ü).
3. **consonant_rules:** final-stop softening, voicing assimilation of suffix consonants, and the buffer consonants -y-/-n-.
4. **exception_tables:** irregular pronoun stems (*ben* → *bana*) and vowel-drop stems (*ağız* → *ağz-*, *su* → *suy-*).

## Existing rule-based analyzers

Candidates Tier A can build on for Turkish. The assessments were not tested.

| Analyzer | Type | What it gives | Links |
|---|---|---|---|
| TRmorph | open-source finite-state transducer (FST) | morphological analysis and lemmas | [GitHub](https://github.com/coltekin/TRmorph) |
| Zemberek | Java morphology library | analysis, lemmatization, normalization | [GitHub](https://github.com/ahmetaa/zemberek-nlp) |
| apertium-tur | FST, a module of the Apertium platform | a hand-written Turkish morphology | [GitHub](https://github.com/apertium/apertium-tur) |
| UDPipe (Turkish models) | lexicon + suffix stripping for unknown words | trained on the Turkish UD treebanks (IMST, BOUN) | [models](https://ufal.mff.cuni.cz/udpipe/models) |
| Stanza (Turkish) | neural tagger/lemmatizer | lemmas and UD analysis for Turkish | [website](https://stanfordnlp.github.io/stanza/) |
| Hunspell (tr-TR) | spellchecker; the .aff/.dic files define affix rules | lemma via hunspell-stem or wrappers | [LibreOffice dictionaries](https://github.com/LibreOffice/dictionaries) |

## Test cases

The examples from the requirements are collected in [`test-cases.tsv`](test-cases.tsv): form, context, expected lemma, expected features (where unambiguous) and requirement IDs. They can be run against every version of the Turkish Tier A grammar ([section 11](../../en/11-evaluation.md)).

## Notes on the transfer

- **Verb lemma.** The expected lemmas use the bare verb stem (*gel*, *yaz*, *al*), following the Turkish UD treebanks; a dictionary citation form would add -mek/-mak (*gelmek*). If a later convention prefers the infinitive, update the test cases.
- **Possessive vs accusative.** Forms such as *evi* are ambiguous between accusative "the house" and third-person possessive "his house"; the test cases add context to force the accusative reading.
- **yazar.** *yazar* is both the aorist "writes" and the noun "writer"; the test case uses context.
- **Examples.** The examples were added for this draft and need checking by a native speaker or specialist.

## Sources

- Turkish grammar. Wikipedia. <https://en.wikipedia.org/wiki/Turkish_grammar>
- Turkish language. Wikipedia. <https://en.wikipedia.org/wiki/Turkish_language>
- Vowel harmony. Wikipedia. <https://en.wikipedia.org/wiki/Vowel_harmony>
- Göksel, A. & Kerslake, C. (2005). *Turkish: A Comprehensive Grammar*. Routledge.
- Çöltekin, Ç. (2010). A freely available morphological analyzer for Turkish. *LREC 2010*. <https://aclanthology.org/L10-1024/>
