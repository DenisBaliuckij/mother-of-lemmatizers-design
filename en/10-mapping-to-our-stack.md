# Mapping to our stack

Most of the knowledge the design needs is already being collected on corpus-host:

| Design element | Existing asset | State (27 Sep 2026) |
|----|----|----|
| Language inventory and family tree | Glottolog language list on the host | 8,624 languages |
| Grammar books for Tier B | Document catalogue, field "described language" | 1,718 languages with a confirmed grammar |
| Grammar store format | lingua-rules (ASP rule templates, generators, golden tests) | Curated rules for English, German, Russian, Finnish |
| Rule extraction and relative ranking model | Local LLM on the RTX 5090 (qwen3.8, 128k context) | Running; already classifies catalogue documents |
| Retrieval of grammar documents | Corpus catalogue REST API (`/corpus/api/documents?described=…`) | Live, HTTPS |
| Raw text for induction and n-gram profiles | Language corpus and grammar collections | ≈ 290,000 documents registered |

Missing pieces: GlotLID/OpenLID models, the UD and UniMorph data, Grambank/URIEL+ vectors and an implementation of the correspondence learner (LingPy provides SCA alignment and LexStat).
