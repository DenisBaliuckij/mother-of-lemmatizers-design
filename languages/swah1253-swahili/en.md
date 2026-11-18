# Lemmatizer requirements: Swahili

*Swahili · glottocode `swah1253` · ISO 639-3 `swh` · Tier A (rules exist) · status: draft*

Swahili is a Bantu language: nouns fall into classes marked by a prefix, agreement (concord) runs through the clause, and the verb is a slot template of subject, tense, object, root and extensions. The requirements below are 21 properties of the language that the lemmatizer must handle. They are grouped by topic, and each names the Tier A component ([section 5](../../en/05-lemmatizing-with-existing-rules-tier-a.md)) it falls on. Three requirements are not covered by the language-resource ontology.

This file follows the Hungarian worked example; the requirement IDs (SW-01, SW-02, …) are assigned here and do not change. Refer to them in discussions ("SW-10: …").

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
| SW-01 | Digraphs ch, dh, gh, ng', ny, sh, th are single graphemes; ng' (with the apostrophe) is distinct from ng | *ng'ombe* "cow" ≠ *ngombe* | preprocessing, rules |
| SW-02 | Prenasalized consonants (mb, nd, ng, nj) and the syllabic nasal prefix m-/n- must be told apart: the nasal may be a class prefix or part of the stem | *mtu* (m-tu) vs *mbwa* "dog" | preprocessing, rules |

### Nominal morphology (noun classes)

| ID | Requirement | Example | Component |
|---|---|---|---|
| SW-03 | Noun-class prefixes: recover both the stem and the class; the classes pair up (m-/wa-, m-/mi-, ki-/vi-, ji-/ma-, N-/N-, u-/…) | *mtoto*/*watoto*, *kitabu*/*vitabu* | rules, lexicon |
| SW-04 | Number is marked by the class prefix, not a number suffix; define the lemma as the singular-class form | *watoto* → *mtoto* | rules, features |
| SW-05 | Classes 9/10 take a nasal or zero prefix that may assimilate or be null, making the stem hard to segment | *nyumba* (class 9) | lexicon, rules |
| SW-06 | The locative suffix -ni derives locatives (classes 16/17/18) from nouns; strip it to the base noun | *nyumbani* → *nyumba* | rules |
| SW-07 | Store the abstract class feature, not just the surface prefix; agreement depends on it | ki-/vi- = class 7/8 | rules, features |

### Agreement (concord)

| ID | Requirement | Example | Component |
|---|---|---|---|
| SW-08 | Concord: verbs, adjectives, possessives and demonstratives agree with the noun class; parse the agreement prefix and recover the lemma | *watoto wazuri wanacheza* | rules, features |
| SW-09 | Adjective and possessive stems take a class-agreement prefix; the lemma is the bare stem | *wazuri* → *-zuri* | rules, features |

### Verbal morphology

| ID | Requirement | Example | Component |
|---|---|---|---|
| SW-10 | The verb is a slot template (NEG–SUBJ–TENSE–OBJ–ROOT–EXT–FINAL); strip the slots to the verb lemma | *ninasoma* = ni + na + soma | rules, features |
| SW-11 | The subject-concord prefix (ni-, u-, a-, tu-, m-, wa- …) agrees with the subject's class | *anasoma* (a-) | rules, features |
| SW-12 | Tense/aspect markers (-na- present, -li- past, -ta- future, -me- perfect, -ki-, -ka-) fill the slot after the subject | *alisoma* (-li-) | rules, features |
| SW-13 | An optional object marker before the root agrees with the object's class | *ninakupenda* (-ku-) | rules, features |
| SW-14 | The final vowel -a (indicative) alternates with -e (subjunctive); verb extensions (applicative, passive -w-, causative -sh-, stative -k-) sit before it | *asome* (subj), *anasomwa* (pass) | rules, features |
| SW-15 | Negation: the prefix ha- (+ subject) and a final -i in the present, plus distinct negative tenses; recover the positive lemma and mark polarity | *hawasomi* → *soma*, Polarity=Neg | rules, features |
| SW-16 | The infinitive is class 15 ku- (*kusoma*); define the lemma convention (the verb stem *-soma*) | *kusoma* → *soma* | rules, lexicon |
| SW-17 | Relative and copula forms attach relative markers (amba-, -ye-, -cho- …); parse them off | *kitabu nilichokisoma* | rules, context |

### Derivation and lexicon

| ID | Requirement | Example | Component |
|---|---|---|---|
| SW-18 | Do not mix derivation (verb extensions, nominalization) and inflection: the ontology keeps these processes apart | — | rules |
| SW-19 | Borrowed nouns often have no overt prefix (classes 9/10 or 5/6); a lexical table assigns their class | *redio*, *daktari* | lexicon |
| SW-20 | A table of monosyllabic verbs that keep the infinitive ku- in some tenses (kula, kunywa, kuja) | *anakuja* → *ja* | lexicon |

### Context

| ID | Requirement | Example | Component |
|---|---|---|---|
| SW-21 | The object marker is optional and marks definiteness/specificity; its presence is syntactic, needed by the context module, not by the lemma | *ninasoma kitabu* / *ninakisoma* | context |

## What this means for the architecture

- **Most requirements fall on the rule-based analyzer.** The class prefixes, concord and the verb slot template (SW-03, SW-04, SW-06, SW-08–SW-16) are paradigm templates and alternation rules from the grammar store, as Tier A intends.
- **The noun class is a feature the whole clause depends on.** SW-07 and SW-08 mean the class must be stored as an abstract feature, because agreement on adjectives, verbs and possessives is computed from it, not from the surface prefix.
- **Exception tables need a place in the grammar store.** Borrowings with no overt prefix (SW-19) and monosyllabic verbs that keep ku- (SW-20) are lists, not rules, like the Hungarian case.
- **Some requirements concern features, not the lemma.** SW-04 (number), SW-07 (class) and SW-15 (polarity) change the output features while the lemma stays the same.
- **Relative and object marking need the context module.** SW-17 and SW-21 cannot be resolved inside one token; the relative marker and the optional object marker depend on the clause.

## Gaps in the ontology

Three requirements are not reflected in the language-resource ontology. They must be added for the profile to support a reliable lemmatizer.

| ID | What is missing |
|---|---|
| SW-05 | The N- class (9/10) prefix is listed, but there is no rule for its assimilation or zero realization, so the stem of *nyumba* is mis-segmented |
| SW-13 | The object marker is described, but it is not singled out as an optional slot inside the verb template that the analyzer must strip while keeping its class feature |
| SW-20 | Monosyllabic verbs are noted, but there is no rule that they keep the infinitive ku- in some tenses (*anakuja*), so the ku- is wrongly taken for an object marker |

## Proposed profile subsections

Machine-readable version: [`profile.yaml`](profile.yaml).

1. **noun_classes:** the singular/plural class pairs with their prefixes (m-/wa-, ki-/vi-, N-/N-, u-/…) and the locative -ni.
2. **verb_template:** the ordered slots (NEG–SUBJ–TENSE–OBJ–ROOT–EXT–FINAL), the subject concords, the tense/aspect markers and the extensions.
3. **negation:** the ha- prefix with final -i in the present and the distinct negative tenses.
4. **exception_tables:** borrowings with no overt prefix (*redio*, *daktari*) and monosyllabic verbs keeping ku- (*kuja*, *kula*, *kunywa*).

## Existing rule-based analyzers

Candidates Tier A can build on for Swahili. The assessments were not tested.

| Analyzer | Type | What it gives | Links |
|---|---|---|---|
| SALAMA / Helsinki Swahili FST | finite-state transducer (FST) | morphological analysis and lemmas, class and verb morphology | [Helsinki/GTweb](https://github.com/giellalt) |
| apertium-swa | FST, a module of the Apertium platform | a hand-written Swahili morphology | [GitHub](https://github.com/apertium/apertium-swa) |
| UDPipe (Swahili) | lexicon + suffix stripping for unknown words | trained on the Swahili UD treebank | [models](https://ufal.mff.cuni.cz/udpipe/models) |
| Stanza (Swahili) | neural tagger/lemmatizer | lemmas and UD analysis for Swahili | [website](https://stanfordnlp.github.io/stanza/) |
| TreeTagger (Swahili) | probabilistic tagger with a lemma lexicon | PoS tags and lemmas | [project page](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/) |
| spaCy (xx multilingual) | lemma lookup | fallback lookup lemmatization | [models](https://spacy.io/models) |

## Test cases

The examples from the requirements are collected in [`test-cases.tsv`](test-cases.tsv): form, context, expected lemma, expected features (where unambiguous) and requirement IDs. They can be run against every version of the Swahili Tier A grammar ([section 11](../../en/11-evaluation.md)).

## Notes on the transfer

- **Noun class as a feature.** The noun class is central to Swahili but is not a core Universal Dependencies feature, so the test cases keep the class in the note and assert only Number. A profile that adds a class feature (e.g. `NounClass`) should update the expected features.
- **Verb lemma.** The expected lemmas use the bare verb stem with its final vowel (*soma*, *penda*, *cheza*); a dictionary citation form would add the infinitive ku- (*kusoma*). Monosyllabic verbs are given as the stem (*ja* for *kuja*).
- **Adjective lemma.** Adjective stems are bound; the lemma is written with the leading hyphen (*-zuri*), the usual lexicographic convention.
- **Examples.** The examples were added for this draft and need checking by a native speaker or specialist.

## Sources

- Swahili grammar. Wikipedia. <https://en.wikipedia.org/wiki/Swahili_grammar>
- Swahili language. Wikipedia. <https://en.wikipedia.org/wiki/Swahili_language>
- Noun class. Wikipedia. <https://en.wikipedia.org/wiki/Noun_class>
- Ashton, E. O. (1947). *Swahili Grammar (Including Intonation)*. Longmans.
- Hurskainen, A. (1992). A two-level computational morphology for the Swahili language. <https://www.njas.fi/>
