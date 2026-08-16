# Code-mixing lexicon — rejected candidates

Every Sinhala word considered for the code-mixing lexicon (scripts/build_codemix_lexicon.py) and explicitly excluded, with the reason. Mirrors the exclusion-list discipline used for the Phase 2 loanword table in src/romanizers/aksharamukha.py.

| Sinhala | Considered English | Reason excluded |
|---|---|---|
| වැඩ / වැඩක් / වැඩේ | work / job | Too idiomatically overloaded — most real uses are slang for 'the situation/matter', not literally 'work'; blind substitution would misrepresent most occurrences. |
| කතා / කතාව | talk / story | Meaning too broad/context-dependent for a safe single-target substitution. |
| ගෑණි | wife / woman | Frequently used pejoratively in this hate-speech corpus to mean 'woman' generically, not specifically 'wife' — high risk of mistranslating the actual sense. |
| ගෙදර | home | 'home' has ZERO attestation in the measured candidate vocabulary (all 3 evidence channels) despite being independently plausible — excluded per the attestation rule rather than trusted on intuition alone. |
| රට / රටේ / රටට / රටක් | country | 'country' has zero attestation in the measured candidate vocabulary; excluded per the attestation rule. |
| ලංකාව / ලංකාවේ / ලංකාවෙ | Sri Lanka / Lanka | Proper noun — not a meaningful translation target for a code-mixing substitution. |
| ප්‍රශ්නය / ප්‍රශ්නයක් | problem | 'problem' has zero attestation in the measured candidate vocabulary; excluded per the attestation rule despite being independently plausible. |
| පක්ෂය | party (political) | Ambiguous with 'party' (celebration) sense, which IS already a verified loanword (පාටි -> party) — substituting the political sense as bare 'party' risks being misread as the celebration sense, especially in political-commentary posts. |
| හිතන | thinking | Verb form — out of scope; this lexicon only performs verified NOUN surface substitutions, never morphological/verb analysis. |
| ගින්න | fire | Common Sinhala slang for 'angry/heated', not literally 'fire', in many real uses — polysemy risk, and low attestation. |
| දෙයක් / දේ / දේවල් | thing(s) | Too abstract/pronoun-like; not a concrete content-word substitution. |
| මිනිස්සු / මිනිස්සුන්ට | people | Redundant with ජනතාව -> people (already included); mixing both risks inconsistent output for near-synonyms. |
| කණ්ඩායම | team | SOLD frequency only 2 — negligible coverage value, and ටීම් (a direct Sinhala-script loanword for 'team', freq 14) already covers this concept more naturally. |
| චිත්‍රපටය | film | Zero attestation in SOLD at any inflection — casual Singlish doesn't use this formal word. |
| දුරකථනය | phone | Zero attestation in SOLD — casual speech has no separate native word for this; posters already just write 'phone'/'fone' directly, so there is no native form to substitute FROM. |
| උසාවිය | court | SOLD frequency only 1 — too rare to be worth the entry. |
| විරෝධතාව | protest | Zero occurrences of this exact form in SOLD. |
| ජනතාවගේ | people's | Grammatically awkward as a possessive English substitution; skipped even though the base noun ජනතාව is included. |
| මුස්ලිම් | muslim | Genuine, common loanword spelling (SOLD freq 59) — excluded anyway on purpose: this is a religious/ethnic identity term in a HATE-SPEECH-labeled corpus, and substituting identity markers inside potentially hateful sentences is a different, higher-risk kind of change than a neutral institutional/tech noun. Out of scope for a spelling/script-choice noiser regardless of frequency. |
| සඳ | scandal | 'සඳ' means 'moon' (common, poetic native word) — a coincidental CER-match false positive from the automated candidate scan, not scandal. |
| පොතේ | mother | 'පොතේ' means 'in the book' (පොත=book + locative) — false positive from the automated scan. |
| වේසිගෙ / වේසිගේ / වේසියේ | website | 'වේසිය' means 'prostitute' — a common slur in this corpus, not 'website'. The automated CER scan matched these purely on spelling; substituting a slur for 'website' would have been both wrong and a serious meaning-preservation failure. Flagged here explicitly given how easily this one could have slipped through on spelling alone. |
| ලෙඩේ / ලෙඩෙක් | leader | 'ලෙඩ' means 'sick/illness' (common slang for 'annoying person') — false positive from the automated scan. |
| පෝලිම් / පෝලිමේ | police | 'පෝලිම' means 'queue/line' — false positive from the automated scan; easily confused with the genuine පොලිසිය->police entry that IS included. |
| ගම් / ගමේ | game | 'ගම'='village' is one of the most common native Sinhala words in the corpus — false positive from the automated scan; genuine 'game' is covered instead via ගේම් (an unambiguous phonetic loanword spelling). |
| චාමර | camera | This is a common Sinhala given name (Chamara), not the word for 'camera' — false positive from the automated scan; genuine 'camera' is covered via කැමරා instead. |
| (~35 further automated-scan matches) | various | Rejected in bulk: pronouns/particles/verb-inflections that happen to romanize close to an English word (e.g. මට='to me'->'data', ට='to'->'tea', දාලා='having put'->'data'), the same false-positive class LOG.md already documented for the original loanword table. Not enumerated individually — none had a plausible correct English reading, unlike the entries above which are recorded because the false positive was specific and instructive. |

Low-confidence entries that WERE included (not rejected) but are flagged for extra scrutiny during human review: ඇමති/ඇමතිතුමා (minister — no direct latin-token attestation, plausibility-based), සල්ලි/මුදල් (money — high plausibility but latin-token count only 2), දරුවා/ළමයා/බිරිඳ (child/wife — latin-token count 1), අදහස (comment — semantic nuance from 'opinion' to 'comment'), මැතිවරණය (election — latin-token count 1), වීඩියෝ/මැසේජ් (video/message — verified overrides for a measurement-tool false negative, see module docstring).