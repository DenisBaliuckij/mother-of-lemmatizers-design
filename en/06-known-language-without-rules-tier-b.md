# Known language without rules (Tier B)

For most of the languages in our catalogue a grammar exists only as a book. Tier B converts those books and the available raw text into rules.

1.  **Retrieve.** Grammar books, sketches and textbooks whose described language is the target are fetched from the document catalogue.
2.  **Extract.** The local language model reads the paradigm tables and the morphology chapters and emits structured rules: affix, slot, features, conditions, examples. Interlinear examples (IGT) are parsed into morpheme–gloss pairs and used as test cases. Research on learning from grammar books (MTOB) shows that models profit mostly from examples and tables rather than prose explanations, so extraction concentrates on those.
3.  **Induce.** Independently, unsupervised segmentation (Morfessor FlatCat) and paradigm clustering on raw text propose affixes and paradigms.
4.  **Reconcile.** Extracted rules act as a prior; the induced segmentation provides evidence. Rules that the text confirms get high confidence; rules the text never exercises remain but are flagged; frequent unexplained patterns become new rule candidates.
5.  **Compile.** The result is written into the grammar store in the lingua-rules template format, so the Tier A engine can use it unchanged.
