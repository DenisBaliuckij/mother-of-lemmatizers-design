# Overview

The input is raw text in any language and script. The output is the same text with a lemma for every word, plus the recognised language, the grammar that produced each lemma and a confidence. Every text goes through the same recognition stage, then is routed to one of three tiers depending on what the system knows about the language:

## Tier A · rules exist

*Language recognised, curated grammar available*

Rule-based analyser proposes all candidate lemmas; a contextual neural model chooses among them. Highest accuracy, fully explainable.

## Tier B · known, no rules

*Language recognised, no machine-readable grammar*

Rules are extracted from grammar books in the document catalogue and induced from raw text, then compiled into the same rule format.

## Tier C · unknown language

*Recogniser rejects all known labels*

Closest relatives are located in the family tree; their grammars are carried over through learned sound correspondences, fitted to the text, and checked against typological universals.

Grammars produced in tiers B and C are provisional. They are stored with their provenance and confidence, used immediately, and promoted to Tier A only after validation: automatic checks first, then a linguist's review. Each language processed this way improves the system for its neighbours in the tree.
