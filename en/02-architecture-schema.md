# Architecture schema

```mermaid
flowchart TD
  IN[/"Input text"/] --> NORM["Normalisation<br/>Unicode NFC · script detection · transliteration to Latin for scoring"]
  NORM --> SEG["Segmentation<br/>sentences · tokens · script-aware word splitting"]
  SEG --> LID{"Language recognition<br/>GlotLID + OpenLID ensemble<br/>MaskLID for mixed-language text<br/>open-set rejection"}
  LID -->|"known + grammar rules"| A["Tier A<br/>rule analyser → candidate lemmas<br/>→ contextual disambiguation"]
  LID -->|"known, no rules"| B["Tier B<br/>rule extraction from grammar books<br/>+ unsupervised morphology"]
  LID -->|"unknown"| REL["Finding relatives<br/>n-gram · lexical · typological similarity<br/>ranked donor languages + tree position"]
  REL --> C["Tier C<br/>grammar generation<br/>sound correspondences · affix transfer<br/>induction · universals"]
  B --> STORE[("Grammar store<br/>lingua-rules ASP templates<br/>status: provisional")]
  C --> STORE
  STORE --> ENGINE["Lemmatization engine<br/>same engine for all tiers"]
  A --> ENGINE
  ENGINE --> OUT[/"Lemmas + language + confidence + provenance"/]
  STORE -. "validated" .-> REVIEW["Validation<br/>coverage · stability · expert review"]
  REVIEW -. "promoted to curated" .-> CURATED[("Curated grammars<br/>Tier A")]
  CURATED --> A
  KB[("Knowledge bases<br/>Glottolog tree · Grambank/WALS/URIEL+<br/>UniMorph · UD treebanks · lexicons")] --- REL
  KB --- C
  DOCS[("Document catalogue<br/>grammar books by described language")] --- B
  DOCS --- C
  classDef known fill:#e4e8f4,stroke:#2e3f7a,stroke-width:2px,color:#1f2421
  classDef inferred fill:#f5ebd8,stroke:#a9741c,stroke-width:2px,stroke-dasharray:5 3,color:#1f2421
  class A,CURATED known
  class B,C,REL,STORE inferred
```

*Figure 1. Components and data flow. Solid blue marks curated knowledge; dashed ochre marks inferred knowledge that carries a confidence and waits for validation.*

## Components

| Component | Job | Method |
|----|----|----|
| Normalisation | Make text comparable across sources | Unicode NFC, removal of zero-width characters, script detection by Unicode script property (ISO 15924), romanisation (uroman-style) used only for similarity scoring, never for output |
| Segmentation | Sentences and word tokens | Rule-based for spaced scripts; dictionary/statistical segmentation for scripts without spaces (Thai, Chinese, Japanese) |
| Language recognition | Language label per segment, or "unknown" | Ensemble of fastText classifiers, code-switching detection, calibrated open-set rejection (section 3) |
| Finding relatives | For an unknown language: donors and tree position | Character n-gram, lexical (cognate) and typological similarity combined by a learned ranker (section 4) |
| Grammar store | One format for all grammars | Paradigm and rule templates in the lingua-rules ASP format, with confidence, provenance and status per rule |
| Lemmatization engine | Word → lemma in context | Rule analyser generates candidates; neural edit-script model scores them in context; guesser handles unknown words |
| Validation | Decide when inferred rules can be trusted | Corpus coverage, bootstrap stability, round-trip generation, held-out checks, expert review queue |
