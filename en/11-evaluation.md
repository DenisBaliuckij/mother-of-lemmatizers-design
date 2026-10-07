# Evaluation

- **Recognition:** accuracy and macro-F1 on held-out GlotLID/FLORES-style test sets; open-set rejection measured by hiding whole languages from the classifier and checking that they are rejected, and that the family of the hidden language comes first among the suggested relatives.
- **Tier A:** lemma accuracy on Universal Dependencies test treebanks, compared with Stanza/UDPipe.
- **Tier C by simulation:** the decisive test. Take a language that *has* a curated grammar and a treebank, pretend it is unknown, generate its grammar only from its relatives, and measure lemma accuracy against the treebank. Repeating this leave-one-language-out across families shows how accurate provisional grammars are as a function of relative distance and text size.
- **Tier B:** extracted rules checked against the grammar book's own interlinear examples, then against a treebank where one exists.
- **Language requirements:** the test cases in `languages/<language>/test-cases.tsv` are run against every version of the language's Tier A grammar.
