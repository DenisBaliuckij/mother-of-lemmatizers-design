# Lemmatizing with existing rules (Tier A)

Where curated grammar exists, the system combines exact rules with a statistical model that reads context. Rules guarantee that every lemma is a legitimate form of the language; the model decides among ambiguous analyses (German *Weg* as noun "way" vs particle *weg*, Russian стали as "steel" or "became").

1.  **Analysis.** Each token is run through the rule analyser (paradigm templates and alternation rules compiled from the grammar store). The result is a set of candidate analyses: lemma + part of speech + features.
2.  **Lexicon check.** Candidates whose lemma is in the lexicon are preferred; unknown lemmas are allowed but penalised.
3.  **Unknown words.** A guesser strips the most productive affixes (productivity = number of distinct stems observed with the affix) and proposes candidate lemmas ranked by paradigm fit.
4.  **Contextual choice.** A neural edit-script lemmatizer (the approach of the Universal Lemmatizer and Stanza/UDPipe, trained on Universal Dependencies) scores every candidate in its sentence. The output is constrained to the rule candidates whenever at least one exists, so the model cannot invent non-words.
