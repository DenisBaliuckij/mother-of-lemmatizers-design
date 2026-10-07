# Lemmatizer requirements: Hungarian

*Hungarian · glottocode `hung1274` · ISO 639-3 `hun` · Tier A (rules exist) · status: under review*

Hungarian is agglutinative, with vowel harmony, rich possessive morphology and two verb conjugations. The requirements below are 28 properties of the language that the lemmatizer must handle. They are grouped by topic, and each names the Tier A component ([section 5](../../en/05-lemmatizing-with-existing-rules-tier-a.md)) it falls on. Four requirements are not covered by the language-resource ontology. Two change the architecture itself: a lemma spanning several tokens (HU-17) and the context module (HU-28).

Source: the document "Требования к лемматизатору" (Lemmatizer requirements, `ontologiescorpus/требования к лемматизатору.docx`, in Russian). Requirement numbers are kept from it: HU-01 is its first requirement, and so on. Refer to them in discussions ("HU-12: …").

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
| HU-25 | Digraphs and the trigraph are grapheme units: cs, dz, dzs, gy, ly, ny, sz, ty, zs must not be analyzed as independent characters | *gy* in *magyar* is one grapheme | preprocessing, rules |
| HU-26 | Vowel length is distinctive: a/á, e/é, o/ó, ö/ő, u/ú, ü/ű are different letters, not variants of one; they must not be normalized | *kor* "age" ≠ *kór* "disease" | preprocessing, lexicon |

### Morphophonology and allomorphy

| ID | Requirement | Example | Component |
|---|---|---|---|
| HU-02 | Vowel harmony: recover one underlying morph behind -ban/-ben, -nak/-nek, -hoz/-hez/-höz, -val/-vel; the allomorph depends on the stem's vowels | *házban*, *kertben* → -ban/-ben | rules |
| HU-03 | The neutral front vowels i, í, e, é do not always make a stem front-harmonic: transparency and "last trigger" effects occur | *papír* + -nak → *papírnak* | rules, lexicon |
| HU-04 | Some suffixes distinguish front unrounded from front rounded: three-way -hoz/-hez/-höz | *házhoz*, *kézhez*, *könyvhöz* | rules |
| HU-05 | Stem alternations: a suffix cannot simply be cut off; final a/e lengthen before certain suffixes | *alma* → *almát*, *mese* → *mesét*, *pianó* → *pianót* | rules |
| HU-06 | Consonant assimilation: recover the underlying suffix behind surface assimilation | *kéz* + -vel → *kézzel* | rules |
| HU-07 | Store the abstract morpheme, not only surface forms: -nak/-nek is one grammatical marker | -nak/-nek = dative | rules, features |
| HU-27 | Harmony is less predictable in loanwords: a lexical-exception mechanism is needed | — | lexicon |

### Nominal morphology

| ID | Requirement | Example | Component |
|---|---|---|---|
| HU-01 | Agglutination: analyze a suffix chain as a sequence of morphemes and strip them one by one | *házainkban* = ház + ai + nk + ban | rules, guesser |
| HU-08 | Case is a separate layer of analysis; modern descriptions usually count 18 cases, though the boundaries of the category are debated | *házban*, *házból*, *házhoz* | rules, features |
| HU-09 | Possession: possessive morphemes and their combination with number and case | *házam*, *házad*, *háza*, *házaink* | rules, features |
| HU-10 | There is no grammatical gender: do not create gender-agreement rules | *ő* is both "he" and "she" | rules |
| HU-11 | Plural with case: recover -k in chains, including with possessive markers | *házakban* → *ház* | rules |
| HU-12 | After a numeral the noun usually stays singular; do not tag it as plural | *két alma* "two apples" | features, context |
| HU-23 | Pronouns: a separate table of irregular case forms, since the form may contain no obvious stem | *nekem* → *én*, *neked* → *te* | lexicon |
| HU-24 | Postpositions rather than prepositions; some have morphological and possessive forms | *a ház mögött*, *mögötte* | rules, lexicon |

### Verbal morphology

| ID | Requirement | Example | Component |
|---|---|---|---|
| HU-13 | Two conjugations, indefinite and definite (objective); strip the right set of verbal markers | *olvasok* / *olvasom* → *olvas* | rules, features |
| HU-14 | The verb form also depends on the definiteness of the object: a verb cannot be analyzed only as stem + tense + person | *látok egy házat* / *látom a házat* | rules, context |
| HU-15 | The special 1SG subject → 2SG object form (-lak/-lek) is not a sum of the standard person markers | *látlak* "I see you" → *lát* | rules, lexicon |
| HU-16 | Verbal prefixes (igekötők: meg-, el-, fel-, ki-, be-, át- and others) are a separate layer; their position depends on syntax, so the token is not always the lexical form | *megír*, *elmegy* | rules, context |
| HU-17 | Joined and separated prefixes give one lemma | *megírta*, *írta meg*, *nem írta meg* → *megír* | preprocessing, context |
| HU-18 | Normalize the infinitive and non-finite forms (-ni, participles, converbs) to the verb lemma | *olvasni* → *olvas* | rules |

### Derivation and lexicon

| ID | Requirement | Example | Component |
|---|---|---|---|
| HU-19 | Do not mix derivation and inflection: the ontology keeps these processes apart | — | rules |
| HU-20 | Productive compounding: otherwise a compound's component is taken for a lemma of its own | — | rules, lexicon |
| HU-21 | A list of lexicalized forms that look compositional but are separate lexemes | — | lexicon |
| HU-22 | A table of suppletive and irregular stems is mandatory: some forms cannot be recovered by successive stripping | *ment* → *megy* | lexicon |

### Context

| ID | Requirement | Example | Component |
|---|---|---|---|
| HU-28 | Information structure is not needed for the lemma itself but is needed by the context module for verb forms, because morphology and syntax interact closely | word order and prefix position | context |

## What this means for the architecture

- **Most requirements fall on the rule-based analyzer.** Harmony, alternations, assimilation and suffix chains (HU-01–HU-09, HU-11, HU-13, HU-18) are paradigm templates and alternation rules from the grammar store, as Tier A intends.
- **Exception tables need a place in the grammar store.** Pronouns (HU-23), suppletives (HU-22), lexicalized forms (HU-21) and loanwords with irregular harmony (HU-27) are lists, not rules. The scheme in section 5 does not yet separate them from the lexicon.
- **A lemma spanning several tokens is a gap in the architecture.** HU-17 needs *írta … meg* linked to the one lemma *megír*. The contract in section 9 returns one lemma per token, so it needs a way to say that a lemma covers several tokens. Options to discuss: a field pointing to the second token, or a separate layer of multi-word lemmas.
- **Some requirements concern features, not the lemma.** HU-12 (number after a numeral), HU-07 (abstract morpheme), HU-13 and HU-14 (conjugation type) change the output features while the lemma stays the same.
- **Verbs need the context module.** HU-14, HU-16, HU-17 and HU-28 need context wider than one token. In Tier A this choice is made by the neural lemmatizer; the rule for separated prefixes will have to be stated explicitly.

## Gaps in the ontology

Four requirements are not reflected in the language-resource ontology. They must be added for the profile to support a reliable lemmatizer.

| ID | What is missing |
|---|---|
| HU-12 | Numeral and singular number are described separately, but there is no rule that a noun after a numeral stays singular (*két alma*, not *két almák*) |
| HU-15 | Definite and indefinite conjugation are described in general, but the portmanteau morpheme -lak/-lek (*látlak*) is not singled out, although it is a critical exception to the standard paradigm |
| HU-17 | No preprocessing rule links *megírta*, *írta meg* and *nem írta meg* to the one lemma *megír*; this computational task is not reflected in the ontology |
| HU-23 | Personal_Pronoun is defined in GOLD, but the Hungarian profile has no table of irregular pronoun declension (*én* → *nekem*, *te* → *neked*, *ő* → *neki*) |

## Proposed profile subsections

Four computational subsections are proposed for the ontology's `Hungarian_Morphological_Profile`. Machine-readable version: [`profile.yaml`](profile.yaml).

1. **exception_tables:** suppletive verbs (stem / past pairs such as *megy* / *ment*), declension of *én*, *te*, *ő* etc., stems whose final a/e lengthens (*alma* → *almát*).
2. **verbal_prefixes (igekötők):** the list meg, el, fel, ki, be, át, le, össze, szét and the rule "attach a separated prefix to the verb lemma regardless of the syntactic gap" (*nem írta meg* → *megír*).
3. **special_morphemes:** the portmanteau morpheme -lak/-lek (subject 1SG, object 2SG, a special type of definite conjugation) and the infinitive marker -ni.
4. **assimilation_rules:** if the stem ends in a consonant, the *v* of -val/-vel assimilates to it and doubles it (*kéz* + -vel → *kézzel*); the lemmatizer must reverse this to recover -val/-vel.

## Existing rule-based analyzers

Candidates Tier A can build on for Hungarian. The assessments come from the source document and were not tested.

| Analyzer | Type | What it gives | Links |
|---|---|---|---|
| emMorph (e-magyar pipeline) | rule-based finite-state transducer (FST) | the reference morphological analyzer: lemmas and morphological tags, suffixation and harmony | [documentation](https://e-magyar.hu/en/textchain/emmorph), [GitHub](https://github.com/dlt-rilmta/emMorph) |
| magyarlanc | rule-based analyzer and lemmatizer | predecessor of e-magyar, fast, widely used in older systems | [project page](https://rgai.inf.u-szeged.hu/magyarlanc) |
| apertium-hun | FST, a module of the Apertium machine-translation platform | a large hand-written morphology | [wiki](https://wiki.apertium.org/wiki/Hungarian), [GitHub](https://github.com/apertium/apertium-hun) |
| UDPipe (Hungarian model) | lexicon + suffix stripping for unknown words | trained on Universal Dependencies treebanks | [models](https://ufal.mff.cuni.cz/udpipe/models) |
| HuSpaCy | lemma table + POS-specific exceptions | community spaCy models (*hu_core_news_lg*) | [GitHub](https://github.com/huspacy/huspacy) |
| Hunspell (Magyar Ispell) | spellchecker; the .aff/.dic files define the affix rules | lemma via hunspell-stem or wrappers such as PyHunspell | [Magyar Ispell](https://magyarispell.sourceforge.net/) |

## Test cases

The examples from the requirements are collected in [`test-cases.tsv`](test-cases.tsv): form, context, expected lemma, expected features (where unambiguous) and requirement IDs. They can be run against every version of the Hungarian Tier A grammar ([section 11](../../en/11-evaluation.md)).

## Notes on the transfer

What was changed, or needs checking, compared with the source document:

- **Links.** `utm_source=chatgpt.com` tags were removed. The magyarlanc link (`github.com/MTA-SZTAKI/magyarlanc2`) does not resolve; it was replaced by the University of Szeged project page. `spacy.io/models/hu` does not resolve; it was replaced by the HuSpaCy repository. The Hunspell link pointed to Hunspell's test folder, not a Hungarian dictionary; the Magyar Ispell link was kept. That site refuses automated requests (HTTP 403), so check it by hand.
- **Prefix list.** *fel* appeared twice in the source list; the duplicate was removed.
- **HU-12 "except egy".** The source says that after numerals *except egy* the noun stays singular. But it is also singular after *egy* (*egy alma*). Please clarify what was meant; perhaps the homonymy of *egy* as a numeral and the indefinite article.
- **HU-06 together with HU-25.** In -val/-vel assimilation only the first letter of a digraph is doubled: *rész* + -vel → *résszel*, not *résszszel*. So the reverse rule must work on graphemes, not single letters.
- **Examples in the tables.** The source had no examples for HU-03, HU-04, HU-08, HU-10, HU-14, HU-24, HU-26 and HU-27; examples were added during the transfer (*papírnak*, *házhoz*/*kézhez*/*könyvhöz*, *kor*/*kór*, *mögötte*, *látok*/*látom* and others) and need checking by a native speaker or specialist.

## Sources

- Hungarian grammar. Wikipedia. <https://en.wikipedia.org/wiki/Hungarian_grammar>
- Hungarian language. Wikipedia. <https://en.wikipedia.org/wiki/Hungarian_language>
- Hungarian verbs. Wikipedia. <https://en.wikipedia.org/wiki/Hungarian_verbs>
- Ozburn, A. (2019). A target-oriented approach to neutrality in vowel harmony: Evidence from Hungarian. *Glossa: a journal of general linguistics*, 4(1). <https://doi.org/10.5334/gjgl.681> — for HU-03 and HU-27.
- The *Glossa* article on assimilation cited by HU-06: <https://www.glossa-journal.org/article/5154/galley/12518/download/> — author and title could not be established; please check.
