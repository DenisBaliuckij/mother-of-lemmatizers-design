# Laws of language evolution the system relies on

"Common linguistic laws" is made concrete as five kinds of knowledge, each encoded as data rather than as hand-written code:

| Principle | Encoded as | Used in |
|----|----|----|
| Regularity of sound change: changes apply to all words with the same sound in the same environment | Correspondence tables learned by EM; only recurrent correspondences are accepted | Steps 1–3 |
| Directional tendencies of sound change (lenition, palatalisation before front vowels, final devoicing, vowel reduction, assimilation) | Prior probabilities over change types, from databases of attested sound changes | Initialising and regularising the correspondence table |
| Genealogical inheritance: related languages share morphology inherited from their ancestor; stable features change slowly | Glottolog tree; feature imputation weighted by tree distance | Donor ranking, typological priors |
| Typological universals: implicational tendencies (e.g. verb-final languages tend to have postpositions; suffixing preference) | Constraints and priors over Grambank/WALS features | Step 5 |
| Grammaticalisation paths: grammatical markers develop from lexical words along recurring paths (e.g. "go" → future) | Source → target mappings used to interpret affixes whose meaning is unclear | Labelling induced affixes with grammatical features |

> Neural reconstruction models (cognate reflex prediction, protoform reconstruction) can replace the EM correspondence learner once enough cognate sets exist for a family; they were the strongest systems in the SIGTYP 2022 shared task. The EM learner stays as the fallback for families with little data.
