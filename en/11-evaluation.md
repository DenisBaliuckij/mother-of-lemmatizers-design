# Evaluation

Evaluation is organised around named metrics, a fixed set of baselines, and per-component test suites. The metrics are reported overall and broken down by tier, so that a gain in coverage is never confused with a gain in accuracy.

## Metrics

- **Lemma accuracy** — exact-match rate of the predicted lemma against the gold lemma, per token, micro-averaged. Reported overall and as a **per-tier breakdown** (A / B / C), because the three tiers carry very different confidence.
- **OOV lemma recall** — lemma accuracy restricted to tokens whose lemma is absent from the training lexicon. This isolates the guesser (Tier A) and the induced paradigms (Tiers B/C) from memorised forms.
- **Unknown-language recall** — the share of Tier-C target languages whose provisional grammar reaches a set lemma-accuracy threshold on held-out text. It answers "for how many unseen languages does the pipeline produce a usable grammar", not just "how good is the average grammar".
- **Recognition macro-F1** — language-detection F1 averaged over languages (not tokens), so that low-resource labels count as much as high-resource ones.
- **Open-set rejection rate** — on languages hidden from the classifier, the share correctly returned as `unknown` rather than forced into a known label, reported together with the **family-first rate** (how often the hidden language's true family heads the suggested relatives).

## Baselines

The provisional grammars and the Tier-C pipeline have no direct competitor, so comparison is against strong supervised lemmatizers on the tasks they *can* do (Tier A, Universal Dependencies). The table is a template the project fills as results land; `—` marks a value still to be measured and `n/a` a task the baseline does not attempt.

| System | Lemma acc. (all) | Tier A | Tier B | Tier C | OOV lemma recall | Recognition macro-F1 | Open-set rejection |
|----|----|----|----|----|----|----|----|
| This system | — | — | — | — | — | — | — |
| Stanza | — | — | n/a | n/a | — | n/a | n/a |
| UDPipe | — | — | n/a | n/a | — | n/a | n/a |
| Universal Lemmatizer (seq2seq) [10] | — | — | n/a | n/a | — | n/a | n/a |

## Test suites per component

- **Recognition:** accuracy and macro-F1 on held-out GlotLID/FLORES-style test sets; open-set rejection measured by hiding whole languages from the classifier and checking that they are rejected, and that the family of the hidden language comes first among the suggested relatives.
- **Tier A:** lemma accuracy on Universal Dependencies test treebanks, compared with Stanza/UDPipe and the seq2seq Universal Lemmatizer [10]; OOV lemma recall reported separately so the guesser is measured on its own.
- **Tier C by simulation:** the decisive test. Take a language that *has* a curated grammar and a treebank, pretend it is unknown, generate its grammar only from its relatives, and measure lemma accuracy against the treebank. Repeating this leave-one-language-out across families shows how accurate provisional grammars are as a function of relative distance and text size. Two factors are varied systematically:
  - **Donor distance.** Rerun the generation while withholding the nearest relatives, so the donors sit at increasing genealogical distance (sister → same genus → same family → outside the family). The accuracy-versus-distance curve shows how far transfer reaches before it collapses to induction-only.
  - **Target text size.** Subsample the target corpus (e.g. 1k, 10k, 100k, 1M tokens) and regenerate at each size. Crossing the two factors gives lemma accuracy as a surface over (distance, size), which tells the project how much text a newly encountered language needs at a given remove from its nearest documented relative.
- **Tier B:** extracted rules checked against the grammar book's own interlinear examples, then against a treebank where one exists.
- **Language requirements:** the test cases in `languages/<language>/test-cases.tsv` are run against every version of the language's Tier A grammar.
