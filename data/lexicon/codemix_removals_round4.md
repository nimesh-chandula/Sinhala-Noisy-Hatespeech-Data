# Code-mix word bank: round-4 removal proposal

**Status: PROPOSAL — nothing in this document has been applied.** This is Stage 0 of round 4 (see the approved plan): a read-only report. Removals only reach `data/lexicon/codemix_wordbank.jsonl` after this list is approved and `scripts/apply_codemix_removals.py` is run against `codemix_removals_round4.csv`'s `decision` column.

## Why this round exists

A reviewer objected that code-mixing is unnatural because switched words "appear in certain places in a sentence more often than others." Tested against SOLD's own naturally-occurring code-switching (956 intrasentential English insertions extracted from the corpus), that claim does not hold for POSITION: this noiser does in-place type substitution (see `src/noisers/codemix.py`), so the switch site is always inherited from a real Sinhala sentence, never chosen by the algorithm. Measured positional JSD against natural switches is 0.0017 (0-1 scale); the share followed by an `එක`/`කර` (eka/kara) licensor is 0.42 generated vs 0.44 natural.

It DOES hold for WORD CHOICE — some bank entries are switches no bilingual speaker would make. The three tiers below are that defect, sorted by severity and by how confidently each can be fixed by removal alone.

**Critical finding:** `slur_flag` is `True` for 0/7969 worklist rows — it has never fired, matching the `_SLUR_SUBSTRINGS` wrong-import no-op bug recorded in LOG.md Phase 3 v2. No slur filtering has ever actually been applied to this bank. Tier 1 is that cleanup.

2969 of 4118 bank entries fired during generation. 30 entries / 853 firings flagged tier 1, 67 / 477 tier 2, 606 / 1898 tier 3.

Coverage cost if removed (share of posts with >=1 eligible candidate today that would lose their last one): tier 1 alone 0.87%, tier 1+2 2.22%, tier 1+2+3 10.95%.

## TIER 1 — affect-bearing (label-integrity risk). Recommended: REMOVE.

Sinhala insults read weaker once rendered in English — this can silently weaken whether a post still reads as offensive, which is a label-integrity problem, not a style one. Bilinguals also independently prefer L1 for negative affect (Rudra et al., EMNLP 2016); this repo's own SOLD data agrees (see the natural-switch-rate-by-label line in the script log).

### 1.1. `පිස්සු` -> `crazy`
- impact: 394 posts (160 light, 234 heavy), 137 of them labelled OFF, 432 total occurrences
- source: native, codemix_plausible: True
  - [NOT] before: @USER  @USER පෝය ලංඋනාම ඔහොම වෙනවා වැඩි ..මොකද පිස්සා හිතන්නෙ ඌට නෙවෙයි අනිත් එකාට පිස්සු කියලා ..
  - [NOT] after:  @USER  @USER පෝය ලංඋනාම ඔහොම වෙනවා වැඩි ..මොකද පිස්සා හිතන්නෙ ඌට නෙවෙයි අනිත් එකාට crazy කියලා ..
  - [NOT] before: යකෝ අර Livingstone කාරයා දර පලනවනේ.පිස්සු ගැහිල්ලක්.
  - [NOT] after:  යකෝ අර Livingstone කාරයා දර පලනවනේ.crazy ගැහිල්ලක්.
  - [OFF] before: එදා මම කීව ..ඤඅර දොරවකෙන් ආපු පිස්සු හුත්තිගේ මෙඩල් එක විකුණ ගන්න දීල ඔය ප්‍රරශනේ විසඳන එක අනාගතයට වාසියි කියල. කෝ ඇහුවද ? පඩිත් දීල වාහනත් දීල ගෙවලුත් දුන්නා.
  - [OFF] after:  එදා මම කීව ..ඤඅර දොරවකෙන් ආපු crazy හුත්තිගේ මෙඩල් එක විකුණ ගන්න දීල ඔය ප්‍රරශනේ විසඳන එක අනාගතයට වාසියි කියල. කෝ ඇහුවද ? පඩිත් දීල වාහනත් දීල ගෙවලුත් දුන්නා.

### 1.2. `පිස්සා` -> `maniac`
- impact: 175 posts (66 light, 109 heavy), 64 of them labelled OFF, 199 total occurrences
- source: human_corrected, codemix_plausible: True
  - [OFF] before: කෝ අර පිස්සා... wedding එකට ගිහින් sure එකට කෑලි බල බල ඇති
  - [OFF] after:  කෝ අර maniac... wedding එකට ගිහින් sure එකට කෑලි බල බල ඇති
  - [NOT] before: DSLR එකක් නැති එකම DSLR පිස්සා මමද එතකොට
  - [NOT] after:  DSLR එකක් නැති එකම DSLR maniac මමද එතකොට
  - [NOT] before: @USER මූන පිස්සා කියන්නෙ මොකෙක්ද?
  - [NOT] after:  @USER මූන maniac කියන්නෙ මොකෙක්ද?

### 1.3. `බල්ලා` -> `dog`
- impact: 58 posts (23 light, 35 heavy), 19 of them labelled OFF, 61 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මේ බල්ලා එල්ලන්න ඕනි..!!!
  - [NOT] after:  @USER මේ dog එල්ලන්න ඕනි..!!!
  - [OFF] before: @USER පද හදන්න එපා පර බල්ලා තෝ...
  - [OFF] after:  @USER පද හදන්න එපා පර dog තෝ...
  - [OFF] before: බුදුදුහමට නිග්‍රහ කරන බල්ලා ඇන ගනි  බුදුදුහමට නිග්‍රහ කරන බල්ලා ඇනගනි...  මුගෙන් ඉගන ගත්තු උන්ට දෙවිපිහිටයි ..... URL
  - [OFF] after:  බුදුදුහමට නිග්‍රහ කරන dog ඇන ගනි  බුදුදුහමට නිග්‍රහ කරන dog ඇනගනි...  මුගෙන් ඉගන ගත්තු උන්ට දෙවිපිහිටයි ..... URL

### 1.4. `හොර` -> `thief`
- impact: 44 posts (17 light, 27 heavy), 25 of them labelled OFF, 48 total occurrences
- source: native, codemix_plausible: True
  - [OFF] before: @USER ඔවුන් සාදාකාලික සිරකරුවන් වෙති ශ්‍රිලංකා දිපයේ...  හොර පාස්පොට් හදල රටත් කාපු අවජාතක හැත්ත කියද්දි සමහරුන්ට රිදෙනව අැයිද දන්නැ
  - [OFF] after:  @USER ඔවුන් සාදාකාලික සිරකරුවන් වෙති ශ්‍රිලංකා දිපයේ...  thief පාස්පොට් හදල රටත් කාපු අවජාතක හැත්ත කියද්දි සමහරුන්ට රිදෙනව අැයිද දන්නැ
  - [NOT] before: @USER  @USER යකූ... !!!!!හරිනේ මෙවුන් කෙල්ලොනේ.. පිස්සු හැදෙයි.. හොර ඡන්ද ගහනවා ඊට වඩා ලාබයි!
  - [NOT] after:  @USER  @USER යකූ... !!!!!හරිනේ මෙවුන් කෙල්ලොනේ.. පිස්සු හැදෙයි.. thief ඡන්ද ගහනවා ඊට වඩා ලාබයි!
  - [OFF] before: @USER දියවන්නාවෙ කාලකණ්ණි ටික මරල දාන්නම ඕන , පොන්න රනිල, හොර මහින්ද ඕකුන්ගෙ හෙන්චයියන් ඔක්කොම මරල දාල උන්ගෙ ගෑනුටික ගණිකා සේවයේ දාන්න ඕන
  - [OFF] after:  @USER දියවන්නාවෙ කාලකණ්ණි ටික මරල දාන්නම ඕන , පොන්න රනිල, thief මහින්ද ඕකුන්ගෙ හෙන්චයියන් ඔක්කොම මරල දාල උන්ගෙ ගෑනුටික ගණිකා සේවයේ දාන්න ඕන

### 1.5. `හොරා` -> `thief`
- impact: 30 posts (11 light, 19 heavy), 20 of them labelled OFF, 33 total occurrences
- source: native, codemix_plausible: True
  - [OFF] before: @USER ,  @USER  @USER ලොවට හොරා යූ එන් පීයට හෝ ජ වි පෙ ට  පුක දෙන සොහොයුරෙක්
  - [OFF] after:  @USER ,  @USER  @USER ලොවට thief යූ එන් පීයට හෝ ජ වි පෙ ට  පුක දෙන සොහොයුරෙක්
  - [OFF] before: උඹේ සාහිත්‍ය දැනුම තියෙන්නෙ මේ වගේ කුණුහරප කියන්න විතරයි. තෝ ඒකනේ තොට ලියන්න බැරි නිසා අනුන්ගෙ ඒවා හොරා කන්නේ. #TweetHora
  - [OFF] after:  උඹේ සාහිත්‍ය දැනුම තියෙන්නෙ මේ වගේ කුණුහරප කියන්න විතරයි. තෝ ඒකනේ තොට ලියන්න බැරි නිසා අනුන්ගෙ ඒවා thief කන්නේ. #TweetHora
  - [OFF] before: තෝ මේ ගැන්සියේ හොරා, කෝ ඒ solo පිස්සා තොපේ අක්කා වේසා, Danza Kuduro #misheardsinhalalyrics
  - [OFF] after:  තෝ මේ ගැන්සියේ thief, කෝ ඒ solo පිස්සා තොපේ අක්කා වේසා, Danza Kuduro #misheardsinhalalyrics

### 1.6. `පිස්සුද` -> `crazy`
- impact: 29 posts (10 light, 19 heavy), 7 of them labelled OFF, 29 total occurrences
- source: llm, codemix_plausible: True
  - [OFF] before: @USER  උඹට පිස්සුද ගෑණියේ ඇත්තටම...???
  - [OFF] after:  @USER  උඹට crazy ගෑණියේ ඇත්තටම...???
  - [NOT] before: @USER පිස්සුද අයිසෙ. මොනාද මේ කියවන්නෙ. ඒව කරන්න පුලුවන් දින්න නම් විතරයි. පැරදිලා බෑ.
  - [NOT] after:  @USER crazy අයිසෙ. මොනාද මේ කියවන්නෙ. ඒව කරන්න පුලුවන් දින්න නම් විතරයි. පැරදිලා බෑ.
  - [NOT] before: @USER  @USER  10 others පිස්සුද ඩාලින් වහ ඇලජික් වෙලා ඔයාගෙ රැවුල හැලුනොත්. ඔන්නොහේ ඔහොම ඉන්න.
  - [NOT] after:  @USER  @USER  10 others crazy ඩාලින් වහ ඇලජික් වෙලා ඔයාගෙ රැවුල හැලුනොත්. ඔන්නොහේ ඔහොම ඉන්න.

### 1.7. `මෝඩයා` -> `idiot`
- impact: 20 posts (8 light, 12 heavy), 14 of them labelled OFF, 21 total occurrences
- source: llm, codemix_plausible: True
  - [OFF] before: 'නාතන් මෝඩයා  #askprisoner"ඉතා මෝඩ <3
  - [OFF] after:  'නාතන් idiot  #askprisoner"ඉතා මෝඩ <3
  - [OFF] before: @USER අනේ මේ....  ඌරා ගොනා හරකා මෝඩයා
  - [OFF] after:  @USER අනේ මේ....  ඌරා ගොනා හරකා idiot
  - [OFF] before: @USER @USER  මෝඩයා DM එනවා හරකා
  - [OFF] after:  @USER @USER  idiot DM එනවා හරකා

### 1.8. `හොරෙක්` -> `thief කෙනෙක්`
- impact: 11 posts (4 light, 7 heavy), 6 of them labelled OFF, 11 total occurrences
- source: human_corrected, codemix_plausible: True
  - [NOT] before: @USER හම්මේ මම හොරෙක් මම රටට ආදරේ නෑ
  - [NOT] after:  @USER හම්මේ මම thief කෙනෙක් මම රටට ආදරේ නෑ
  - [NOT] before: @USER අනේ පව්! මෙයා හොරෙක් නෙවෙයි
  - [NOT] after:  @USER අනේ පව්! මෙයා thief කෙනෙක් නෙවෙයි
  - [OFF] before: @USER  @USER මේ නාවලපිටයේ ඉන්න පට්ට හොරෙක්. නුවර ටවුමේ ඉස්කෝල හදන්නේ මෙයාගේ  අම්මගේ අප්පා ගේ බූදලෙන් ද දන්නේ නෑ නේද? තියෙන ඉස්කෝලත් වැඩිවෙලා නගරයෙන් පිටට ගෙනියන්න ප්ලෑන් හදද්දි මේ වගේ පිංගුත්තරයෝ  කොහෙන් හරි ඇවිත්  නුවරම කන්න හදනවා.
  - [OFF] after:  @USER  @USER මේ නාවලපිටයේ ඉන්න පට්ට thief කෙනෙක්. නුවර ටවුමේ ඉස්කෝල හදන්නේ මෙයාගේ  අම්මගේ අප්පා ගේ බූදලෙන් ද දන්නේ නෑ නේද? තියෙන ඉස්කෝලත් වැඩිවෙලා නගරයෙන් පිටට ගෙනියන්න plan හදද්දි මේ වගේ පිංගුත්තරයෝ  කොහෙන් හරි ඇවිත්  නුවරම කන්න හදනවා.

### 1.9. `පිස්සො` -> `crazy`
- impact: 9 posts (4 light, 5 heavy), 4 of them labelled OFF, 9 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: පිස්සා සැරදේවා මට සිංහල ටයිප් කරන්න කියලා දුන්නට. thanks පිස්සො!
  - [NOT] after:  පිස්සා සැරදේවා මට සිංහල ටයිප් කරන්න කියලා දුන්නට. thanks crazy!
  - [OFF] before: @USER ,  @USER  @USER උබ psychiatrist ව හම්බෙන්න පලයන්, වැව් ගාව ඕව කරන්නෙ පිස්සො යකෝ.
  - [OFF] after:  @USER ,  @USER  @USER උබ psychiatrist ව හම්බෙන්න පලයන්, වැව් ගාව ඕව කරන්නෙ crazy යකෝ.
  - [OFF] before: "අරූට පිස්සු. මූට පිස්සු. ආ ඌටත් පිස්සු. ආ උං පිස්සො. තමුසෙලා මෝඩයෝ." - සරත් ෆොන්සේකා
  - [OFF] after:  "අරූට පිස්සු. මූට පිස්සු. ආ ඌටත් පිස්සු. ආ උං crazy. තමුසෙලා මෝඩයෝ." - සරත් ෆොන්සේකා

### 1.10. `මෝඩයෙක්` -> `idiot`
- impact: 8 posts (4 light, 4 heavy), 6 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: True
  - [OFF] before: මම මෝඩ කතා කියන්නෙ මෝඩ කමට නෙවෙයි හනේ. අනිත් මෝඩයො මාව මෝඩයෙක් ගානට දානවද බලන්ට! පව් ඉතිම්    #sithuwili
  - [OFF] after:  මම මෝඩ කතා කියන්නෙ මෝඩ කමට නෙවෙයි හනේ. අනිත් මෝඩයො මාව idiot ගානට දානවද බලන්ට! පව් ඉතිම්    #sithuwili
  - [NOT] before: Other universities  : මං තමුසෙට ආදරෙයි මෝඩියේ/ මෝඩයෝ   අපේ : තමුසෙ මෝඩයෙක් ඕයි.
  - [NOT] after:  Other universities  : මං තමුසෙට ආදරෙයි මෝඩියේ/ මෝඩයෝ   අපේ : තමුසෙ idiot ඕයි.
  - [OFF] before: තෝ නම් මෝඩයෙක්  Rukhshan @USER  · 17 May 2016 ඇයි Thor?
  - [OFF] after:  තෝ නම් idiot  Rukhshan @USER  · 17 May 2016 ඇයි Thor?

### 1.11. `ඌරෙක්` -> `pig කෙනෙක්`
- impact: 8 posts (4 light, 4 heavy), 2 of them labelled OFF, 8 total occurrences
- source: human_corrected, codemix_plausible: True
  - [OFF] before: @USER සබරි කියන්නේ රාජපස්ස වළව්වේ අසූචි කන ඌරෙක්..!!!!
  - [OFF] after:  @USER සබරි කියන්නේ රාජපස්ස වළව්වේ අසූචි කන pig කෙනෙක්..!!!!
  - [NOT] before: අන්න හරි මං වල් ඌරෙක්...මං වල් ඌරා... #BestCartoonEver — watching සූර පප්පා
  - [NOT] after:  අන්න හරි මං වල් pig කෙනෙක්...මං වල් ඌරා... #BestCartoonEver — watching සූර පප්පා
  - [NOT] before: මේ ටුවීටුව දෙස බලනු !!! මෙතැන් පටන් නුඹ වල් ඌරෙක් හා දැන් ශබ්ද නගල කියන්න " මං වල් ඌර... මං වල් ඌරා...." කියලා
  - [NOT] after:  මේ ටුවීටුව දෙස බලනු !!! මෙතැන් පටන් නුඹ වල් pig කෙනෙක් හා දැන් ශබ්ද නගල කියන්න " මං වල් ඌර... මං වල් ඌරා...." කියලා

### 1.12. `මොඩ` -> `stupid`
- impact: 8 posts (2 light, 6 heavy), 7 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: True
  - [OFF] before: @USER අනේ තෝ වගේ මොඩ මුසලයෙක් ගොන් අලියෙක් හිවලෙක්,මදුරුවො කවදද බොල හරක් මස් කෑවේ
  - [OFF] after:  @USER අනේ තෝ වගේ stupid මුසලයෙක් ගොන් අලියෙක් හිවලෙක්,මදුරුවො කවදද බොල හරක් මස් කෑවේ
  - [OFF] before: @USER තෝ වගේ මොඩ මුසලයෙක්
  - [OFF] after:  @USER තෝ වගේ stupid මුසලයෙක්
  - [OFF] before: @USER අනේ තෝ වගේ මොඩ මුසලයෙක් ගොන් අලියෙක් හිවලෙක්,මදුරුවො කවදද බොල හරක් මස් කෑවේ
  - [OFF] after:  @USER අනේ තෝ වගේ stupid මුසලයෙක් ගොන් අලියෙක් හිවලෙක්,මදුරුවො කවදද බොල හරක් meat කෑවේ

### 1.13. `ශිට්` -> `shit`
- impact: 6 posts (2 light, 4 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: "තෝ මට පිරිමි සංහතියම එපා කරා.. මමනං ආයෙ මැරෙන තුරාවට පිරිමියෙක් දිහානං ඇහැක් ඇරලවත් බලන්නෙ නෑ අම්මපා.ශිට් ! අනේ... පිරිමි හැමෝම එකයි"  කියලා යන කෙල්ලො ඔක්කොම ඇත්තටම එතනින් පස්සෙ පිරිමියෙක් දිහා ඇහැක් ඇරලාවත් බලන්නෙ නැතුව හිටියනං මේ වෙනකොට සිංහල ජාතිය සුළු ජාතියක් වෙලා ගොඩක් කල්
  - [NOT] after:  "තෝ මට පිරිමි සංහතියම එපා කරා.. මමනං ආයෙ මැරෙන තුරාවට පිරිමියෙක් දිහානං ඇහැක් ඇරලවත් බලන්නෙ නෑ අම්මපා.shit ! අනේ... පිරිමි හැමෝම එකයි"  කියලා යන කෙල්ලො ඔක්කොම ඇත්තටම එතනින් පස්සෙ පිරිමියෙක් දිහා ඇහැක් ඇරලාවත් බලන්නෙ නැතුව හිටියනං මේ වෙනකොට සිංහල ජාතිය සුළු ජාතියක් වෙලා ගොඩක් කල්
  - [NOT] before: "තෝ මට පිරිමි සංහතියම එපා කරා.. මමනං ආයෙ මැරෙන තුරාවට පිරිමියෙක් දිහානං ඇහැක් ඇරලවත් බලන්නෙ නෑ අම්මපා.ශිට් ! අනේ... පිරිමි හැමෝම එකයි"  කියලා යන කෙල්ලො ඔක්කොම ඇත්තටම එතනින් පස්සෙ පිරිමියෙක් දිහා ඇහැක් ඇරලාවත් බලන්නෙ නැතුව හිටියනං මේ වෙනකොට සිංහල ජාතිය සුළු ජාතියක් වෙලා ගොඩක් කල්
  - [NOT] after:  "තෝ මට පිරිමි සංහතියම එපා කරා.. මමනං ආයෙ මැරෙන තුරාවට පිරිමියෙක් දිහානං ඇහැක් ඇරලවත් බලන්නෙ නෑ අම්මපා.shit ! අනේ... පිරිමි හැමෝම එකයි"  කියලා යන කෙල්ලො ඔක්කොම ඇත්තටම එතනින් පස්සෙ පිරිමියෙක් දිහා ඇහැක් ඇරලාවත් බලන්නෙ නැතුව හිටියනං මේ වෙනකොට Sinhala ජාතිය සුළු ජාතියක් වෙලා ගොඩක් කල්
  - [OFF] before: තමන්ගේ උනුත් අන්ත අසරණ උන වෙලාවකටවත් උදවුවක් දෙන්නවත් යන්න බැරි කාලකණ්ණි රස්සාවල් කරන අපි..ශිට්..
  - [OFF] after:  තමන්ගේ උනුත් අන්ත අසරණ උන වෙලාවකටවත් උදවුවක් දෙන්නවත් යන්න බැරි කාලකණ්ණි jobs කරන අපි..shit..

### 1.14. `ඌරු` -> `pig`
- impact: 6 posts (3 light, 3 heavy), 6 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER අශ්ව පඩ බැටලු පඩ අලි පඩ ඔටු පඩ ඩොල්ෆින් පඩ වඳුරු පඩ බැල්ලි පඩ පූස් පඩ කොටි පඩ කුකුල් පඩ බලු බඩ ඌරු පඩ මී පඩ මී හරක් පඩ පඩ පඩ
  - [OFF] after:  @USER අශ්ව පඩ බැටලු පඩ අලි පඩ ඔටු පඩ ඩොල්ෆින් පඩ වඳුරු පඩ බැල්ලි පඩ පූස් පඩ කොටි පඩ කුකුල් පඩ බලු බඩ pig පඩ මී පඩ මී හරක් පඩ පඩ පඩ
  - [OFF] before: @USER අශ්ව පඩ බැටලු පඩ අලි පඩ ඔටු පඩ ඩොල්ෆින් පඩ වඳුරු පඩ බැල්ලි පඩ පූස් පඩ කොටි පඩ කුකුල් පඩ බලු බඩ ඌරු පඩ මී පඩ මී හරක් පඩ පඩ පඩ
  - [OFF] after:  @USER අශ්ව පඩ බැටලු පඩ අලි පඩ ඔටු පඩ ඩොල්ෆින් පඩ වඳුරු පඩ බැල්ලි පඩ පූස් පඩ tiger පඩ කුකුල් පඩ බලු බඩ pig පඩ මී පඩ මී හරක් පඩ පඩ පඩ
  - [OFF] before: ගොන් බූරු තකතීරු ගොබ්බ හැත්ත. අජූත පජාත කුජීත අවලාත අවලස්සන නිකෘෂ්ඨ අධර්මිෂ්ඨ පාපචර කාලකණ්ණියා මෝඩ ගඳ ගහන කුණු කන්ද . කුණු ගොඩේ ලගින ඌරු රංචුව . බැටළු කොටුව. අලියාගේ තට්ටම . En TPWK @USER  · 2 Jan  @USER If Harry had a problem with being sexualised he wouldnt wear the outfits he does on tour.  This is a fake tweet.  He sexualises himself it sells his music. Such is life.
  - [OFF] after:  ගොන් බූරු තකතීරු ගොබ්බ හැත්ත. අජූත පජාත කුජීත අවලාත අවලස්සන නිකෘෂ්ඨ අධර්මිෂ්ඨ පාපචර කාලකණ්ණියා මෝඩ ගඳ ගහන කුණු කන්ද . කුණු ගොඩේ ලගින pig රංචුව . බැටළු කොටුව. අලියාගේ තට්ටම . En TPWK @USER  · 2 Jan  @USER If Harry had a problem with being sexualised he wouldnt wear the outfits he does on tour.  This is a fake tweet.  He sexualises himself it sells his music. Such is life.

### 1.15. `යකෙක්` -> `devil කෙනෙක්`
- impact: 6 posts (3 light, 3 heavy), 4 of them labelled OFF, 6 total occurrences
- source: human_corrected, codemix_plausible: True
  - [NOT] before: ආදරය.....  මම පණටත් වැඩිට⁣යෙන් ආදරේයි වස්තුව ....ඔයා නැතිව මට ජීවත් වෙන්න බැ..  ලිංගිකත්වය ...  බැයිද තමුසෙට දෙන්න.... එහෙනමි මම වෙන කෙනෙක් ලගට යනවා ...  උඹට වෙන මොකෙක් හරි ඇති එකනේ මට නොදෙන්නේ   වැලන්ටයින් උඹ පිස්සු යකෙක් බං මෙිවා පෙනුන් නැති .  කෝ එතකොට ආදරේ  ?
  - [NOT] after:  ආදරය.....  මම පණටත් වැඩිට⁣යෙන් ආදරේයි වස්තුව ....ඔයා නැතිව මට ජීවත් වෙන්න බැ..  ලිංගිකත්වය ...  බැයිද තමුසෙට දෙන්න.... එහෙනමි මම වෙන කෙනෙක් ලගට යනවා ...  උඹට වෙන මොකෙක් හරි ඇති එකනේ මට නොදෙන්නේ   වැලන්ටයින් උඹ පිස්සු devil කෙනෙක් බං මෙිවා පෙනුන් නැති .  කෝ එතකොට ආදරේ  ?
  - [OFF] before: @USER මදෑ යකෙක් කියල ගෙනාවේ නිව්මෝනියා කාරයෙක්
  - [OFF] after:  @USER මදෑ devil කෙනෙක් කියල ගෙනාවේ නිව්මෝනියා කාරයෙක්
  - [NOT] before: ආදරය.....  මම පණටත් වැඩිට⁣යෙන් ආදරේයි වස්තුව ....ඔයා නැතිව මට ජීවත් වෙන්න බැ..  ලිංගිකත්වය ...  බැයිද තමුසෙට දෙන්න.... එහෙනමි මම වෙන කෙනෙක් ලගට යනවා ...  උඹට වෙන මොකෙක් හරි ඇති එකනේ මට නොදෙන්නේ   වැලන්ටයින් උඹ පිස්සු යකෙක් බං මෙිවා පෙනුන් නැති .  කෝ එතකොට ආදරේ  ?
  - [NOT] after:  ආදරය.....  මම පණටත් වැඩිට⁣යෙන් ආදරේයි වස්තුව ....ඔයා නැතිව මට ජීවත් වෙන්න බැ..  ලිංගිකත්වය ...  බැයිද තමුසෙට දෙන්න.... එහෙනමි මම වෙන කෙනෙක් ලගට යනවා ...  උඹට වෙන මොකෙක් හරි ඇති එකනේ මට නොදෙන්නේ   වැලන්ටයින් උඹ පිස්සු devil කෙනෙක් බං මෙිවා පෙනුන් නැති .  කෝ එතකොට love එක  ?

### 1.16. `දේශද්‍රෝහී` -> `traitor`
- impact: 5 posts (2 light, 3 heavy), 3 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: @USER ජාතීද්‍රෝහී දේශද්‍රෝහී නා ගොඩහේවා ඉතාම පිළිකුල් කෙනෙක් බවට පත්විය
  - [NOT] after:  @USER ජාතීද්‍රෝහී traitor නා ගොඩහේවා ඉතාම පිළිකුල් කෙනෙක් බවට පත්විය
  - [OFF] before: @USER @USER මොනාද අයිසේ තමුසෙ මේ කරන දේශද්‍රෝහී වැඩ
  - [OFF] after:  @USER @USER මොනාද අයිසේ තමුසෙ මේ කරන traitor වැඩ
  - [NOT] before: @USER ජාතීද්‍රෝහී දේශද්‍රෝහී නා ගොඩහේවා ඉතාම පිළිකුල් කෙනෙක් බවට පත්විය
  - [NOT] after:  @USER ජාතීද්‍රෝහී traitor නා ගොඩහේවා ඉතාම පිළිකුල් කෙනෙක් බවට පත්විය

### 1.17. `හොරෙක්ට` -> `thief කෙනෙක්ට`
- impact: 5 posts (2 light, 3 heavy), 5 of them labelled OFF, 5 total occurrences
- source: human_corrected, codemix_plausible: True
  - [OFF] before: @USER ගොසිප් පීපල් නෙමේ හුත්තො. තෝ වගේ හොරෙක්ට මේකෙ ආයෙ දඩයං හොයන්න දෙන්නෑ. එච්චරයි
  - [OFF] after:  @USER ගොසිප් පීපල් නෙමේ හුත්තො. තෝ වගේ thief කෙනෙක්ට මේකෙ ආයෙ දඩයං හොයන්න දෙන්නෑ. එච්චරයි
  - [OFF] before: @USER මේ වගේ තුට්ටු දෙකේ පල් හොරෙක්ට තමන්ට ඕන වෙලාවක කෙලින්ම ගිහින් වැඩ බැරි ටාසන්ව හම්බ වෙන්න පුලුහන්. ඒත් සාධාරණ ඉල්ලීමක් වෙනුවෙන් සටන් කරන කාලකණ්ණි ගුරුවරුන් ට බෑ. ඕකගෙ කලිසම ඔළුවෙන් ගලවලා යවන්න තිබ්බෙ පල් හොරාගෙ.
  - [OFF] after:  @USER මේ වගේ තුට්ටු දෙකේ පල් thief කෙනෙක්ට තමන්ට ඕන වෙලාවක කෙලින්ම ගිහින් වැඩ බැරි ටාසන්ව හම්බ වෙන්න පුලුහන්. ඒත් සාධාරණ ඉල්ලීමක් වෙනුවෙන් සටන් කරන කාලකණ්ණි ගුරුවරුන් ට බෑ. ඕකගෙ කලිසම ඔළුවෙන් ගලවලා යවන්න තිබ්බෙ පල් හොරාගෙ.
  - [OFF] before: @USER ගොසිප් පීපල් නෙමේ හුත්තො. තෝ වගේ හොරෙක්ට මේකෙ ආයෙ දඩයං හොයන්න දෙන්නෑ. එච්චරයි
  - [OFF] after:  @USER ගොසිප් පීපල් නෙමේ හුත්තො. තෝ වගේ thief කෙනෙක්ට මේකෙ ආයෙ දඩයං හොයන්න දෙන්නෑ. එච්චරයි

### 1.18. `බල්ලව` -> `dog ව`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: human_corrected, codemix_plausible: True
  - [OFF] before: @USER ඇම්ඩ පාරෙයද්දි කහ ඉර ගාව බල්ලෙක් සහ බැල්ලියෙක් සෙල්ලමලු.. ඇම්ඩ ඒ මොකද්ද අහල.. ඇම්ඩව එක්කරං ගිය සීයා කියනවා." ආ ඒ අර බැල්ලි බල්ලව කර තියාගෙන පාර මාරුකරනවා නෙ පුතා " කියල. ඇම්ඩා ගත් කටටම..එහෙව් කරුණාවන්ත බැල්ලිට නේද මේ වල් පර බල්ලා උකන්නේ..කියල රංජත් ඒම  උධව් කරන අය කියලා ඇරල නෑ.
  - [OFF] after:  @USER ඇම්ඩ පාරෙයද්දි කහ ඉර ගාව බල්ලෙක් සහ බැල්ලියෙක් සෙල්ලමලු.. ඇම්ඩ ඒ මොකද්ද අහල.. ඇම්ඩව එක්කරං ගිය සීයා කියනවා." ආ ඒ අර බැල්ලි dog ව කර තියාගෙන පාර මාරුකරනවා නෙ පුතා " කියල. ඇම්ඩා ගත් කටටම..එහෙව් කරුණාවන්ත බැල්ලිට නේද මේ වල් පර බල්ලා උකන්නේ..කියල රංජත් ඒම  උධව් කරන අය කියලා ඇරල නෑ.
  - [OFF] before: @USER ඇම්ඩ පාරෙයද්දි කහ ඉර ගාව බල්ලෙක් සහ බැල්ලියෙක් සෙල්ලමලු.. ඇම්ඩ ඒ මොකද්ද අහල.. ඇම්ඩව එක්කරං ගිය සීයා කියනවා." ආ ඒ අර බැල්ලි බල්ලව කර තියාගෙන පාර මාරුකරනවා නෙ පුතා " කියල. ඇම්ඩා ගත් කටටම..එහෙව් කරුණාවන්ත බැල්ලිට නේද මේ වල් පර බල්ලා උකන්නේ..කියල රංජත් ඒම  උධව් කරන අය කියලා ඇරල නෑ.
  - [OFF] after:  @USER ඇම්ඩ පාරෙයද්දි කහ ඉර ගාව බල්ලෙක් සහ බැල්ලියෙක් සෙල්ලමලු.. ඇම්ඩ ඒ මොකද්ද අහල.. ඇම්ඩව එක්කරං ගිය සීයා කියනවා." ආ ඒ අර බැල්ලි dog ව කර තියාගෙන පාර මාරුකරනවා නෙ son " කියල. ඇම්ඩා ගත් කටටම..එහෙව් කරුණාවන්ත බැල්ලිට නේද මේ වල් පර බල්ලා උකන්නේ..කියල රංජත් ඒම  උධව් කරන අය කියලා ඇරල නෑ.
  - [OFF] before: ඔය වේස බල්ලව අච්චාරු දාන්න ඕනේ The following media includes potentially sensitive content. Change settings View
  - [OFF] after:  ඔය වේස dog ව අච්චාරු දාන්න ඕනේ The following media includes potentially sensitive content. Change settings View

### 1.19. `යකා` -> `devil`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: උපයාගත්ත ආකාරය ඔප්පු කිරීමට නොහැකි බව කියන කාරනාව වෙනන ඕනෙ  මෝඩ යකා තුරුම්පුව කරගත්තෙ.
  - [OFF] after:  උපයාගත්ත ආකාරය ඔප්පු කිරීමට නොහැකි බව කියන කාරනාව වෙනන ඕනෙ  මෝඩ devil තුරුම්පුව කරගත්තෙ.
  - [OFF] before: උපයාගත්ත ආකාරය ඔප්පු කිරීමට නොහැකි බව කියන කාරනාව වෙනන ඕනෙ  මෝඩ යකා තුරුම්පුව කරගත්තෙ.
  - [OFF] after:  උපයාගත්ත ආකාරය prove කිරීමට නොහැකි බව කියන කාරනාව වෙනන ඕනෙ  මෝඩ devil තුරුම්පුව කරගත්තෙ.
  - [OFF] before: @USER  @USER මගෙ මල යකා අවුස්ස නොගෙන කටපියන් ඉන්නවද පැන්ඩෙ..  ඒකි වටේ ඉන්න එකියක් නෙවෙයිනෙ...ඒකි මගේ මම ඒකි එක්ක යනව..
  - [OFF] after:  @USER  @USER මගෙ මල devil අවුස්ස නොගෙන කටපියන් ඉන්නවද පැන්ඩෙ..  ඒකි වටේ ඉන්න එකියක් නෙවෙයිනෙ...ඒකි මගේ මම ඒකි එක්ක යනව..

### 1.20. `ඌරා` -> `pig`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: හරකා ඌරා කුකුලා කියන්නෙ වඳවෙන සත්තුත් නෙමේ  උන්ව කන්නෙ අවිහිංසාවාදී දහමේ නමිනුත් නෙමේ  ඒ නිසා ඒක සත්ත්ව හිංසාවට... URL
  - [NOT] after:  හරකා pig කුකුලා කියන්නෙ වඳවෙන සත්තුත් නෙමේ  උන්ව කන්නෙ අවිහිංසාවාදී දහමේ නමිනුත් නෙමේ  ඒ නිසා ඒක සත්ත්ව හිංසාවට... URL
  - [OFF] before: @USER  @USER මෝඩ රනිදු ඌරා
  - [OFF] after:  @USER  @USER මෝඩ රනිදු pig
  - [NOT] before: හරකා ඌරා කුකුලා කියන්නෙ වඳවෙන සත්තුත් නෙමේ  උන්ව කන්නෙ අවිහිංසාවාදී දහමේ නමිනුත් නෙමේ  ඒ නිසා ඒක සත්ත්ව හිංසාවට... URL
  - [NOT] after:  හරකා pig chicken කියන්නෙ වඳවෙන සත්තුත් නෙමේ  උන්ව කන්නෙ අවිහිංසාවාදී දහමේ නමිනුත් නෙමේ  ඒ නිසා ඒක සත්ත්ව හිංසාවට... URL

### 1.21. `ශික්` -> `shit`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: True
  - [OFF] before: ඕනම වෙලාවල් වලට තමයි ෆෝන් එක කැඩෙන්නෙත්. හුත්ත. ශික්.
  - [OFF] after:  ඕනම වෙලාවල් වලට තමයි ෆෝන් එක කැඩෙන්නෙත්. හුත්ත. shit.
  - [OFF] before: ඕනම වෙලාවල් වලට තමයි ෆෝන් එක කැඩෙන්නෙත්. හුත්ත. ශික්.
  - [OFF] after:  ඕනම වෙලාවල් වලට තමයි phone එක කැඩෙන්නෙත්. හුත්ත. shit.
  - [OFF] before: ශික් මේ KG singh රුවුලා හැටි.. එකට ලංකාවේ කොල්ලෝ.. රුවුල එක්ක මාර පට්ට .. නොදකින් මු දැක්කාහම අප්පිරියයි ..
  - [OFF] after:  shit මේ KG singh රුවුලා හැටි.. එකට ලංකාවේ boys.. රුවුල එක්ක මාර පට්ට .. නොදකින් මු දැක්කාහම අප්පිරියයි ..

### 1.22. `දේශදෝරහි` -> `traitor`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: True
  - [OFF] before: @USER Traitor  @USER  දේශදෝරහි පිපිම්පියා. මූටත් ගහලා එලවන්න ඕනේ
  - [OFF] after:  @USER Traitor  @USER  traitor පිපිම්පියා. මූටත් ගහලා එලවන්න ඕනේ
  - [OFF] before: @USER Traitor  @USER  දේශදෝරහි පිපිම්පියා. මූටත් ගහලා එලවන්න ඕනේ
  - [OFF] after:  @USER Traitor  @USER  traitor පිපිම්පියා. මූටත් ගහලා එලවන්න ඕනේ

### 1.23. `අමනයා` -> `idiot`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ,  @USER  @USER චික් බූරු ගොන් කාලකණ්ණි බේබදු කුහක නොසන්ඩාල අපත අමනයා
  - [OFF] after:  @USER ,  @USER  @USER චික් බූරු ගොන් කාලකණ්ණි බේබදු කුහක නොසන්ඩාල අපත idiot
  - [OFF] before: @USER ,  @USER  @USER චික් බූරු ගොන් කාලකණ්ණි බේබදු කුහක නොසන්ඩාල අපත අමනයා
  - [OFF] after:  @USER ,  @USER  @USER චික් බූරු ගොන් කාලකණ්ණි බේබදු fake නොසන්ඩාල අපත idiot

### 1.24. `රාක්ෂ` -> `demon`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  මොකා රාක්ෂ ගෑණි :O
  - [OFF] after:  @USER @USER  මොකා demon ගෑණි :O
  - [OFF] before: @USER @USER  මොකා රාක්ෂ ගෑණි :O
  - [OFF] after:  @USER @USER  මොකා demon ගෑණි :O

### 1.25. `මැට්ටා` -> `idiot`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER අහ්හ් මැට්ටා ගොනා පොල්බූරුවා  @USER  @USER  @USER  @USER
  - [OFF] after:  @USER අහ්හ් idiot ගොනා පොල්බූරුවා  @USER  @USER  @USER  @USER
  - [OFF] before: @USER අහ්හ් මැට්ටා ගොනා පොල්බූරුවා  @USER  @USER  @USER  @USER
  - [OFF] after:  @USER අහ්හ් idiot ගොනා පොල්බූරුවා  @USER  @USER  @USER  @USER

### 1.26. `යකු` -> `demon`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER ටහුඩු යකු එහෙත් දැන් IT ක්ලාසස් තියනවද?
  - [NOT] after:  @USER  @USER ටහුඩු demon එහෙත් දැන් IT ක්ලාසස් තියනවද?
  - [NOT] before: @USER  @USER ටහුඩු යකු එහෙත් දැන් IT ක්ලාසස් තියනවද?
  - [NOT] after:  @USER  @USER ටහුඩු demon එහෙත් දැන් IT ක්ලාසස් තියනවද?

### 1.27. `සුන්ඛයා` -> `dog`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER අඩො කැරියා කිව්වා නම් මාත් එනවනෙ සුන්ඛයා
  - [OFF] after:  @USER අඩො කැරියා කිව්වා නම් මාත් එනවනෙ dog
  - [OFF] before: @USER අඩො කැරියා කිව්වා නම් මාත් එනවනෙ සුන්ඛයා
  - [OFF] after:  @USER අඩො කැරියා කිව්වා නම් මාත් එනවනෙ dog

### 1.28. `කුපාඩියා` -> `rascal`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  නොදකින් කුපාඩියා -,-  @USER
  - [NOT] after:  @USER @USER  නොදකින් rascal -,-  @USER
  - [NOT] before: @USER @USER  නොදකින් කුපාඩියා -,-  @USER
  - [NOT] after:  @USER @USER  නොදකින් rascal -,-  @USER

### 1.29. `මැට්ටෝ` -> `idiot`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER ආපෝ.. ඔයා බල්ලෙක් නෙමෙයිනේ මැට්ටෝ...මං කිව්වේ අපේ බල්ලා ගැන
  - [NOT] after:  @USER  @USER ආපෝ.. ඔයා බල්ලෙක් නෙමෙයිනේ idiot...මං කිව්වේ අපේ dog ගැන

### 1.30. `බොරුකාර` -> `liar`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මට මතකයි..  දවසක් එයා කිව්වා  ....  "ඔයා නැති දවසක මම නම් ජිවත් වෙන එකකුත් නෑ" කියලා  ඔය ඉන්නේ යස අගේට  බොරුකාර මී හරකා...   #copied
  - [OFF] after:  මට මතකයි..  දවසක් එයා කිව්වා  ....  "ඔයා නැති දවසක මම නම් live වෙන එකකුත් නෑ" කියලා  ඔය ඉන්නේ යස අගේට  liar මී හරකා...   #copied

## TIER 2 — native Sinhala verb -> bare English verb (placement defect). Recommended: REMOVE.

Sinhala borrows English verbs as `V + කරනවා/කරන්න/කරලා`, never bare — `කියන්න -> say` is not a construction a real bilingual would produce. `source=loanword` entries are excluded here on purpose: switching an English word already spelled in Sinhala script back to Latin (`කෝල් -> call`) is the most natural move available, not a defect.

### 2.1. `කියන්න` -> `say`
- impact: 60 posts (26 light, 34 heavy), 30 of them labelled OFF, 63 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER කැත කතා කියන්න,එපා
  - [NOT] after:  @USER  @USER කැත කතා say,එපා
  - [NOT] before: @USER  @USER උඹට තේරුනේ නැහැ. ඒකි කියන්න ඇත්‍තෙ photo එක ඒකිගෙ කියලා.
  - [NOT] after:  @USER  @USER උඹට තේරුනේ නැහැ. ඒකි say ඇත්‍තෙ photo එක ඒකිගෙ කියලා.
  - [NOT] before: අම්මෝ යකෝ ඇගටගොඩවෙන්න එන්නෙ  නෑ නෑ කසන්නෙ නෑ  මොකුත්ම කියන්න බෑනෙ ඉක්මනටම ඩෝං යනවා දැන්
  - [NOT] after:  අම්මෝ යකෝ ඇගටගොඩවෙන්න එන්නෙ  නෑ නෑ කසන්නෙ නෑ  මොකුත්ම say බෑනෙ ඉක්මනටම ඩෝං යනවා දැන්

### 2.2. `උදව්` -> `help`
- impact: 27 posts (10 light, 17 heavy), 11 of them labelled OFF, 29 total occurrences
- source: native, codemix_plausible: True
  - [NOT] before: ඇඟේ දුවන්නේ මොන ලේ ද කියලා වැඩක් නෑ..මේ රටේ දියුණුවට උඹ උදව් කරනවනම් උන් ලක් අම්මගේ දරුවො ..ආගම ජාතිය මොකක් වුනත්. #මේ රටට මේ පොළවේ මිනිස්සුන්ට වෛර කරනවනම් අයහපතක් කරනවනම් ඇඟේ දුවන්නේ මොන ලේ උනත් ඌ අවජාතකයෙක්..
  - [NOT] after:  ඇඟේ දුවන්නේ මොන ලේ ද කියලා වැඩක් නෑ..මේ රටේ දියුණුවට උඹ help කරනවනම් උන් ලක් අම්මගේ දරුවො ..ආගම ජාතිය මොකක් වුනත්. #මේ රටට මේ පොළවේ මිනිස්සුන්ට වෛර කරනවනම් අයහපතක් කරනවනම් ඇඟේ දුවන්නේ මොන ලේ උනත් ඌ අවජාතකයෙක්..
  - [OFF] before: Admins: යකාට බය නම් සොහොනෙ ගෙවල් හදන්නෑ පකෝ..   Also Admins: යාලු මගේ කලින් පේජ් එක රිපෝට් කරල බ්ලොක් වෙලා. අලුත් එකට ලයික් කරල ෂෙයා කරල රීච් එක හදාගන්න මට උදව් කරන්න යාලු. දවස් හතකින් කන්නත් නෑ.  #SLPageAdminsbelike
  - [OFF] after:  Admins: යකාට බය නම් සොහොනෙ ගෙවල් හදන්නෑ පකෝ..   Also Admins: යාලු මගේ කලින් පේජ් එක රිපෝට් කරල බ්ලොක් වෙලා. අලුත් එකට ලයික් කරල ෂෙයා කරල රීච් එක හදාගන්න මට help කරන්න යාලු. දවස් හතකින් කන්නත් නෑ.  #SLPageAdminsbelike
  - [NOT] before: කවුරු උදව්වක් ඉල්ලුවහම හෙවිල්ලක්  බැලිල්ලක් නැතුව අනික් පැත්තට බොක්කෙන්ම උදව් කරන්න යන ගොනා විකුණන්නොනි. මේක හරියන් නැ
  - [NOT] after:  කවුරු උදව්වක් ඉල්ලුවහම හෙවිල්ලක්  බැලිල්ලක් නැතුව අනික් පැත්තට බොක්කෙන්ම help කරන්න යන ගොනා විකුණන්නොනි. මේක හරියන් නැ

### 2.3. `කන්න` -> `eat`
- impact: 26 posts (10 light, 16 heavy), 11 of them labelled OFF, 30 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මේ වගේ වේස බල්ලො එල්ලන්න ඕන ################   කන්න දුන්නු අත හපා කෑ තවත් සුනඛයෙක්.  මූ නමින් අජිත් සුසන්ත, ඉන්නෙ... URL
  - [OFF] after:  මේ වගේ වේස බල්ලො එල්ලන්න ඕන ################   eat දුන්නු අත හපා කෑ තවත් සුනඛයෙක්.  මූ නමින් අජිත් සුසන්ත, ඉන්නෙ... URL
  - [NOT] before: අන්න හරකා පැලේ කන්න යනවා
  - [NOT] after:  අන්න හරකා පැලේ eat යනවා
  - [OFF] before: @USER ඔව් ඇවිල්ලා නාකි මැන්ටල් අයියලා දෙන්නගෙයි, මෝඩ මොංගල් බූරු මල්ලිලා දෙන්නගෙයි වලු කඩං කන්න තමයි ඉතුරුවෙලා තියෙන්නේ
  - [OFF] after:  @USER ඔව් ඇවිල්ලා නාකි මැන්ටල් අයියලා දෙන්නගෙයි, මෝඩ මොංගල් බූරු මල්ලිලා දෙන්නගෙයි වලු කඩං eat තමයි ඉතුරුවෙලා තියෙන්නේ

### 2.4. `දන්න` -> `know`
- impact: 24 posts (11 light, 13 heavy), 13 of them labelled OFF, 28 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔ්... එ් අපි දන්න තරම තමා..  නාකි විසේ ගෙටත් උසේ කියනවනෙ...
  - [NOT] after:  @USER ඔ්... එ් අපි know තරම තමා..  නාකි විසේ ගෙටත් උසේ කියනවනෙ...
  - [OFF] before: @USER අනේ මේ යන්ඩ තිෂ් ඔවා දන්න බිජ්ජ...
  - [OFF] after:  @USER අනේ මේ යන්ඩ තිෂ් ඔවා know බිජ්ජ...
  - [NOT] before: @USER  @USER  යකෝ මූ දන්න දේවල්
  - [NOT] after:  @USER  @USER  යකෝ මූ know දේවල්

### 2.5. `දන්නේ` -> `know`
- impact: 22 posts (10 light, 12 heavy), 10 of them labelled OFF, 24 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER තව එකෙක් පස්සෙන් එන්න වෙයිද දන්නේ නෑ බැහැපු ලබ්බ දූවිලි ගෑවෙන්න නොදී උස්සන් එන්න
  - [OFF] after:  @USER තව එකෙක් පස්සෙන් එන්න වෙයිද know නෑ බැහැපු ලබ්බ දූවිලි ගෑවෙන්න නොදී උස්සන් එන්න
  - [NOT] before: @USER දැන්  @USER  මේවා දන්නේ කොහොමද? බලන් හිටියද? ඕව ඇත්ත කියල අපි කොහොමද දන්නේ?? #LKA
  - [NOT] after:  @USER දැන්  @USER  මේවා know කොහොමද? බලන් හිටියද? ඕව ඇත්ත කියල අපි කොහොමද know?? #LKA
  - [NOT] before: @USER  @USER තෝ මොනවද දන්නේ
  - [NOT] after:  @USER  @USER තෝ මොනවද know

### 2.6. `මැරියන්` -> `die`
- impact: 17 posts (7 light, 10 heavy), 17 of them labelled OFF, 17 total occurrences
- source: human_corrected, codemix_plausible: True
  - [OFF] before: දැන් ඉන්න හුජ්ජ කොල්ලො කෙල්ලෙක් නිසා යාලුවට පිහියෙන් ඇන්නට අපි ඔය කාලේ බොක්කෙන් ලව් කරේ කෙල්ලන්ව බෙදාගෙන..  විලියම් ටෙල් එකේ වාරා බීබීසී රොබින් හුඩ් එකේ මැරියන් රොබින්සන් අන්දරය එකේ ජොආනා සක්වල ඳගකාරයෝ එකේ ලුසී රිදී ඉර එකේ පැන්චා....  #මතක
  - [OFF] after:  දැන් ඉන්න හුජ්ජ කොල්ලො කෙල්ලෙක් නිසා යාලුවට පිහියෙන් ඇන්නට අපි ඔය කාලේ බොක්කෙන් ලව් කරේ කෙල්ලන්ව බෙදාගෙන..  විලියම් ටෙල් එකේ වාරා බීබීසී රොබින් හුඩ් එකේ die රොබින්සන් අන්දරය එකේ ජොආනා සක්වල ඳගකාරයෝ එකේ ලුසී රිදී ඉර එකේ පැන්චා....  #මතක
  - [OFF] before: @USER ,  @USER  @USER මැරියන් මුසලයා -_-
  - [OFF] after:  @USER ,  @USER  @USER die මුසලයා -_-
  - [OFF] before: @USER  @USER    මැරියන් ඉන්ද්‍රජිත්  තෝ පණුවො දාලා කුණු වෙලා මැරෙන්නේ
  - [OFF] after:  @USER  @USER    die ඉන්ද්‍රජිත්  තෝ පණුවො දාලා කුණු වෙලා මැරෙන්නේ

### 2.7. `එන්න` -> `come`
- impact: 17 posts (7 light, 10 heavy), 11 of them labelled OFF, 23 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: නිරෝදායනයට යන්න එනවද කියලා මීනාක්ශිගෙන් ඇහුවා එන්න බෑලු   + එහෙනම් උඹ එන්නෑ - නැහැ +පරට්ටි !  #ගුහාසටනපොකුර
  - [OFF] after:  නිරෝදායනයට යන්න එනවද කියලා මීනාක්ශිගෙන් ඇහුවා come බෑලු   + එහෙනම් උඹ එන්නෑ - නැහැ +පරට්ටි !  #ගුහාසටනපොකුර
  - [NOT] before: @USER අනේ ....එපා පැත්තපලාතක එපා එන්න
  - [NOT] after:  @USER අනේ ....එපා පැත්තපලාතක එපා come
  - [OFF] before: එන්න එන්නම එපා කරවනවා!! නපුන්සක Thilanga Sumathipala ගොං පොන්නයා!! මකබෑවිලා යන්නේ නෑ නේ පාරේ බල්ලේක් වගේ මූව!! තූ නොදකින්!!!  URL
  - [OFF] after:  come එන්නම එපා කරවනවා!! නපුන්සක Thilanga Sumathipala ගොං පොන්නයා!! මකබෑවිලා යන්නේ නෑ නේ පාරේ බල්ලේක් වගේ මූව!! තූ නොදකින්!!!  URL

### 2.8. `පාවිච්චි` -> `use`
- impact: 16 posts (6 light, 10 heavy), 9 of them labelled OFF, 16 total occurrences
- source: llm, codemix_plausible: True
  - [OFF] before: පර බල්ලෝ , ගොන් හරක් යන නම භාවිතයට විරුද්දව හරක් සහ බල්ලෝ නිතී ක්‍රියා මාර්ග ගැනීමට සැරසේ - පුවතක්   යකෝ උන්ගේ නම් පාවිච්චි කරන්න එපා අපේ මිනිසුන්ට :  මොකෝ ඒ තිරිසන් සතුන් බෝම්බ පුපුරුවන්, කුඩු ගහලා , සුදු දාලා , හොරා කන්නේ නැ
  - [OFF] after:  පර බල්ලෝ , ගොන් හරක් යන නම භාවිතයට විරුද්දව හරක් සහ බල්ලෝ නිතී ක්‍රියා මාර්ග ගැනීමට සැරසේ - පුවතක්   යකෝ උන්ගේ නම් use කරන්න එපා අපේ මිනිසුන්ට :  මොකෝ ඒ තිරිසන් සතුන් බෝම්බ පුපුරුවන්, කුඩු ගහලා , සුදු දාලා , හොරා කන්නේ නැ
  - [NOT] before: ඇමෙරිකාවේත් රුපියල් පාවිච්චි කරානම් මේ මුකුත් නෑනේ. රෙද්ද
  - [NOT] after:  ඇමෙරිකාවේත් රුපියල් use කරානම් මේ මුකුත් නෑනේ. රෙද්ද
  - [OFF] before: @USER මම තෝ වගේ කොන්ඩම් පාවිච්චි කරලා නෑ යකෝ...  ජීවිතේටම එක පාරයි අැස් දෙකට දැකලා තියෙන්නෙත්...
  - [OFF] after:  @USER මම තෝ වගේ කොන්ඩම් use කරලා නෑ යකෝ...  ජීවිතේටම එක පාරයි අැස් දෙකට දැකලා තියෙන්නෙත්...

### 2.9. `නතර` -> `stop`
- impact: 15 posts (5 light, 10 heavy), 8 of them labelled OFF, 15 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: මේක මාලිංගගේ  ඉත්තෑව විසින් ප්‍රකාස කරන ලද්දක් බවට කරුනාවෙං සලකන්න.  කොහෙද මේ ටුවිටරේ ඉඩිට් බටන් එකක් නෑනෙ... රෙද්ද.. මීට මගේ ඉත්තෑව.. ගම්ම @USER  · 4 Jun 2019 හයියෙං වැහැපු හින්ද නතර කලේ.. යන්තං වැස්ස නම් කුඩයක් ඉහලගෙන හරි ගහනව...  මීට මාලිංග
  - [NOT] after:  මේක මාලිංගගේ  ඉත්තෑව විසින් ප්‍රකාස කරන ලද්දක් බවට කරුනාවෙං සලකන්න.  කොහෙද මේ ටුවිටරේ ඉඩිට් බටන් එකක් නෑනෙ... රෙද්ද.. මීට මගේ ඉත්තෑව.. ගම්ම @USER  · 4 Jun 2019 හයියෙං වැහැපු හින්ද stop කලේ.. යන්තං වැස්ස නම් කුඩයක් ඉහලගෙන හරි ගහනව...  මීට මාලිංග
  - [OFF] before: කාලකණ්ණි ගේම් එක අන්තිමේට අතින් කයිට් වෙන ඇත්ත පූල් බෝඩ් එක්කින් අපිව නතර කරේ VK @USER  · 13 Sep 2020  Ball Pool ප්ලේ කරන්න කවුරුත් නැද්ද
  - [OFF] after:  කාලකණ්ණි ගේම් එක අන්තිමේට අතින් කයිට් වෙන ඇත්ත පූල් බෝඩ් එක්කින් අපිව stop කරේ VK @USER  · 13 Sep 2020  Ball Pool ප්ලේ කරන්න කවුරුත් නැද්ද
  - [OFF] before: විල්පත්තුවට කෙලින්න පටන් ගත්තෙ මහින්දගෙ කාලෙ කියන උන්ම තමයි මහා බැන්කුවට කෙලින්න පටන් ගත්තෙ මහින්දගෙ කාලෙ කියල ඒ මගඩිය සධාරණී කලෙ නිවට පිම්පියො  තූ ! නොදකින්  මේවා කවද හරි කොහෙන් හරි නතර කරන්න ඔනෙ නැද්ද් ???? — feeling shame
  - [OFF] after:  විල්පත්තුවට කෙලින්න පටන් ගත්තෙ මහින්දගෙ කාලෙ කියන උන්ම තමයි මහා බැන්කුවට කෙලින්න පටන් ගත්තෙ මහින්දගෙ කාලෙ කියල ඒ මගඩිය සධාරණී කලෙ නිවට පිම්පියො  තූ ! නොදකින්  මේවා කවද හරි කොහෙන් හරි stop කරන්න ඔනෙ නැද්ද් ???? — feeling shame

### 2.10. `අත්අඩංගුවට` -> `arrest`
- impact: 13 posts (5 light, 8 heavy), 4 of them labelled OFF, 13 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: ජෝන්ගේ පස්ස අත්අඩංගුවට ගන්න කියලා (වීඩියෝ) URL via  @USER  #lka #srilanka
  - [NOT] after:  ජෝන්ගේ පස්ස arrest ගන්න කියලා (වීඩියෝ) URL via  @USER  #lka #srilanka
  - [NOT] before: @USER ඒ කියන්නේ DIG නාලකව අත්අඩංගුවට ගැනීමේ මෙහෙයුමෙන් මුස්ලිම් අන්තවාදී දෙශපාලකයන් ඉන්නවා...
  - [NOT] after:  @USER ඒ කියන්නේ DIG නාලකව arrest ගැනීමේ මෙහෙයුමෙන් මුස්ලිම් අන්තවාදී දෙශපාලකයන් ඉන්නවා...
  - [NOT] before: @USER එක්කෙනෙක් අත්අඩංගුවට ගනින පූලූවන්ද
  - [NOT] after:  @USER එක්කෙනෙක් arrest ගනින පූලූවන්ද

### 2.11. `කට්` -> `cut`
- impact: 13 posts (4 light, 9 heavy), 0 of them labelled OFF, 14 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: උබේ ඩාලින් සයිමා කට් වෙලා   Good Bye Legend! #SunilPerera
  - [NOT] after:  උබේ ඩාලින් සයිමා cut වෙලා   Good Bye Legend! #SunilPerera
  - [NOT] before: උබ හොදට මිරිකලා දෙහි ටික ගනින්කො විමලා අනේ උබෙ ඩාලින් සයිම කට් වෙලා....  URL
  - [NOT] after:  උබ හොදට මිරිකලා දෙහි ටික ගනින්කො විමලා අනේ උබෙ ඩාලින් සයිම cut වෙලා....  URL
  - [NOT] before: "ගාල්ලේ පංති කට් කරපු උන්ගේ සංගමය "                                   පට්ට ඕයි.
  - [NOT] after:  "ගාල්ලේ පංති cut කරපු උන්ගේ සංගමය "                                   පට්ට ඕයි.

### 2.12. `හිනා` -> `laugh`
- impact: 13 posts (6 light, 7 heavy), 4 of them labelled OFF, 13 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER හිනා උනේ පකෝ වරෙන් ඒක හාන්න
  - [OFF] after:  @USER  @USER laugh උනේ පකෝ වරෙන් ඒක හාන්න
  - [NOT] before: @USER  @USER මේවට අපි කොහෙන්ද හිනා වෙන්න ඕනේ!?
  - [NOT] after:  @USER  @USER මේවට අපි කොහෙන්ද laugh වෙන්න ඕනේ!?
  - [OFF] before: @USER  දීපිකා නෙමේ බොල ප්‍රියංකා... අහවල් පොල්ල  හිනා ගිහින් සික්ස් පැක්ස් ආවා කියහන්කෝ
  - [OFF] after:  @USER  දීපිකා නෙමේ බොල ප්‍රියංකා... අහවල් පොල්ල  laugh ගිහින් සික්ස් පැක්ස් ආවා කියහන්කෝ

### 2.13. `වරෙන්` -> `come`
- impact: 11 posts (5 light, 6 heavy), 7 of them labelled OFF, 11 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: වරෙන්  #MY3 තෝ ඉල්ලන් කෑවා #lka #CoupLk #CoupSL #ConstitutionalCrisisSriLanka
  - [OFF] after:  come  #MY3 තෝ ඉල්ලන් කෑවා #lka #CoupLk #CoupSL #ConstitutionalCrisisSriLanka
  - [NOT] before: ටහුඩු...  ගෙඩි 2ම කන්න ඕනි... Maduwa @USER  · 23 Jun 2019 ගුඩි මෝනිං කොමඩු කමුද වරෙන්
  - [NOT] after:  ටහුඩු...  ගෙඩි 2ම කන්න ඕනි... Maduwa @USER  · 23 Jun 2019 ගුඩි මෝනිං කොමඩු කමුද come
  - [OFF] before: @USER  @USER වෙන්නෙ නෑ තමා. මම මොකාද කියල දාපු එකා දන්නවා ඇති. ඒකයි පන තියේ නම් වරෙන් කීවෙ.  යකෝ... ආතල් එකක් ගන්න ඕන නම් ගන්න පුලුවන් තැන් තියෙනවා. පලයංකෝ එහෙම. ඔච්චරම අමාරුයි නම්.
  - [OFF] after:  @USER  @USER වෙන්නෙ නෑ තමා. මම මොකාද කියල දාපු එකා දන්නවා ඇති. ඒකයි පන තියේ නම් come කීවෙ.  යකෝ... ආතල් එකක් ගන්න ඕන නම් ගන්න පුලුවන් තැන් තියෙනවා. පලයංකෝ එහෙම. ඔච්චරම අමාරුයි නම්.

### 2.14. `තේරුම්` -> `understand`
- impact: 11 posts (4 light, 7 heavy), 5 of them labelled OFF, 13 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මේ වේස හුකන්නොන්ට ඔහොම වෙලා මදි.. සේවකයො කියන්නෙ තොපේ අත පල්ලෙන් වැටිච්ච උන් නෙමෙයි කියල දැන්වත් තේරුම් ගනිව්..... URL
  - [OFF] after:  මේ වේස හුකන්නොන්ට ඔහොම වෙලා මදි.. සේවකයො කියන්නෙ තොපේ අත පල්ලෙන් වැටිච්ච උන් නෙමෙයි කියල දැන්වත් understand ගනිව්..... URL
  - [NOT] before: @USER  @USER අහ්හ් කපුටා ඇහැරලද? ඔයාට ඒක තේරුම් ගන්න බෑ සුප්පා  බල්ලා කවුද, මැක්කා කවුද කියලා කසුනායියා තේරුම් ගනී.
  - [NOT] after:  @USER  @USER අහ්හ් කපුටා ඇහැරලද? ඔයාට ඒක understand ගන්න බෑ සුප්පා  බල්ලා කවුද, මැක්කා කවුද කියලා කසුනායියා understand ගනී.
  - [NOT] before: යම් වෘත්තියක අවශ්‍යතාවය තමන්ට නැතිනම් එම වෘත්තියට ගරු කිරීමට ඉගෙන ගත් යුතු යි....  රූපලාවන්‍ය වෘත්තීය යනු එක එකාට රෙද්ද ඉස්සීම නොවන වග කවුරු කවුරුත් තේරුම් ගත යුතුය... Dilan @USER  · 18 May 2021 Comment එකහ් ....
  - [NOT] after:  යම් වෘත්තියක අවශ්‍යතාවය තමන්ට නැතිනම් එම වෘත්තියට ගරු කිරීමට ඉගෙන ගත් යුතු යි....  රූපලාවන්‍ය වෘත්තීය යනු එක එකාට රෙද්ද ඉස්සීම නොවන වග කවුරු කවුරුත් understand ගත යුතුය... Dilan @USER  · 18 May 2021 Comment එකහ් ....

### 2.15. `පටන්` -> `start`
- impact: 9 posts (4 light, 5 heavy), 8 of them labelled OFF, 9 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: පරට්ට බැල්ලි කියලා පටන් ගන්නේ
  - [OFF] after:  පරට්ට බැල්ලි කියලා start ගන්නේ
  - [OFF] before: ඒ ගොන් මෝඩ මී හරකා මගේ දඬුමොණරෙ බිම දැම්මා මදිවට තව ඉවකරන්නත් පටන් ගත්තා.
  - [OFF] after:  ඒ ගොන් මෝඩ මී හරකා මගේ දඬුමොණරෙ බිම දැම්මා මදිවට තව ඉවකරන්නත් start ගත්තා.
  - [OFF] before: අරේසි දාලා ගිහින් ටෞකණ්ඩපුතානෝ පැරදිලා 2020 පටන් ගත්තේ කැද වගතු නැ ඔයි...නොදකින්
  - [OFF] after:  අරේසි දාලා ගිහින් ටෞකණ්ඩපුතානෝ පැරදිලා 2020 start ගත්තේ කැද වගතු නැ ඔයි...නොදකින්

### 2.16. `හදන්න` -> `make`
- impact: 9 posts (3 light, 6 heavy), 4 of them labelled OFF, 9 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හතුරුසින්හ නෙවෙ මොන පයිය ආවත් අපේ උන්ව හදන්න බැ
  - [OFF] after:  හතුරුසින්හ නෙවෙ මොන පයිය ආවත් අපේ උන්ව make බැ
  - [NOT] before: charger එක දෙන්න බරිනුම් phone හදන්න එපා ,රෙද්ද
  - [NOT] after:  charger එක දෙන්න බරිනුම් phone make එපා ,රෙද්ද
  - [NOT] before: @USER  @USER හදන්න නෙමේ බොල බලන්න ගන්නවනේ
  - [NOT] after:  @USER  @USER make නෙමේ බොල බලන්න ගන්නවනේ

### 2.17. `පෙන්නන්න` -> `show`
- impact: 9 posts (4 light, 5 heavy), 7 of them labelled OFF, 9 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER සීරාවටම මුන් ඔක්කොම ගෙනල්ලා පෙන්නන්න ඔනේ කාලකණ්ණි හැත්තට
  - [OFF] after:  @USER සීරාවටම මුන් ඔක්කොම ගෙනල්ලා show ඔනේ කාලකණ්ණි හැත්තට
  - [NOT] before: @USER එහෙනම් ෆොන්සේකට අරක දෙන්න ඔයා කියන දේ ඔප්පු කරලම පෙන්නන්න.
  - [NOT] after:  @USER එහෙනම් ෆොන්සේකට අරක දෙන්න ඔයා කියන දේ ඔප්පු කරලම show.
  - [OFF] before: @USER සීරාවටම මුන් ඔක්කොම ගෙනල්ලා පෙන්නන්න ඔනේ කාලකණ්ණි හැත්තට
  - [OFF] after:  @USER සීරාවටම මුන් ඔක්කොම ගෙනල්ලා show ඔනේ කාලකණ්ණි හැත්තට

### 2.18. `ජීවත්` -> `live`
- impact: 8 posts (3 light, 5 heavy), 2 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ජීවත් වෙලා ඉන්න කං උන්නද මලාද කියලා හොයන්න එකෙක් නෑ, මැරැණම දානේ කන්න නම් එයි පෙරේත හැත්ත
  - [OFF] after:  live වෙලා ඉන්න කං උන්නද මලාද කියලා හොයන්න එකෙක් නෑ, මැරැණම දානේ කන්න නම් එයි පෙරේත හැත්ත
  - [NOT] before: ජීවත් වෙන්නේ කොහොමද ඔබගෙන් මිදිලා මේ සන්සාරේ ඔබේ සතුටයි මට ඕනා   කියාවි කියලා හිතන් ඇත්තේ ඒකි.. පව්
  - [NOT] after:  live වෙන්නේ කොහොමද ඔබගෙන් මිදිලා මේ සන්සාරේ ඔබේ සතුටයි මට ඕනා   කියාවි කියලා හිතන් ඇත්තේ ඒකි.. පව්
  - [NOT] before: ගෑණි එක්ක ජීවත් වෙන්න බෑ කියල යාලුවට කිව්වම  තවත් රස කතා මෙතනින් බලන්න ->URL URL
  - [NOT] after:  ගෑණි එක්ක live වෙන්න බෑ කියල යාලුවට කිව්වම  තවත් රස talk මෙතනින් බලන්න ->URL URL

### 2.19. `නින්ද` -> `sleep`
- impact: 8 posts (4 light, 4 heavy), 2 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: නින්ද යන්නෙත් නෑ ඕයි රෙද්ද -_-
  - [NOT] after:  sleep යන්නෙත් නෑ ඕයි රෙද්ද -_-
  - [OFF] before: අද මේකෙ ඉන්නවා එකෙක් ලෛ එන්නෙ නෑ.අපිට පොඩ්ඩක් නින්ද යනවා නේද මුන් ලෛ ඇවිල්ලා සහනාධාරත් බෙදලා ගෙවලුත් හදලා දෙනවා හුත්ත
  - [OFF] after:  අද මේකෙ ඉන්නවා එකෙක් ලෛ එන්නෙ නෑ.අපිට පොඩ්ඩක් sleep යනවා නේද මුන් ලෛ ඇවිල්ලා සහනාධාරත් බෙදලා ගෙවලුත් හදලා දෙනවා හුත්ත
  - [NOT] before: දවල්ටත් නිකම් මැරිච්ච වගේ නින්ද ගියානෙ බොල.මහ මුස්පේත්තු දවසක්..
  - [NOT] after:  දවල්ටත් නිකම් මැරිච්ච වගේ sleep ගියානෙ බොල.මහ මුස්පේත්තු දවසක්..

### 2.20. `උදවු` -> `help`
- impact: 7 posts (3 light, 4 heavy), 2 of them labelled OFF, 9 total occurrences
- source: native, codemix_plausible: True
  - [OFF] before: කාලකණ්ණි අවස්ථාවාදී දේශාපාලුවන් දැන සිටි පාස්කු ඉරිදා ත්‍රස්ත ප්‍රහාරයට මාස පහයි..මියගිය සියලුම දෙනාට මෝක් සුවය ලැබේවා.. ප්‍රහාරයට උදවු කරපු, ප්‍රහාරය දැනසිට ජාතික සමගිය සහ රටේ සාමකාමී බව නැති කරපු කාලකණ්නි හැතිකරේට හෙන හතම වැදෙවා !!! #lka #SriLanka
  - [OFF] after:  කාලකණ්ණි අවස්ථාවාදී දේශාපාලුවන් දැන සිටි පාස්කු ඉරිදා ත්‍රස්ත ප්‍රහාරයට මාස පහයි..මියගිය සියලුම දෙනාට මෝක් සුවය ලැබේවා.. ප්‍රහාරයට help කරපු, ප්‍රහාරය දැනසිට ජාතික සමගිය සහ රටේ සාමකාමී බව නැති කරපු කාලකණ්නි හැතිකරේට හෙන හතම වැදෙවා !!! #lka #SriLanka
  - [NOT] before: යකෝ බලාගෙන යනකොට මේක පිටිපස්සේ ඉන්නේ  @USER  යේ සිරිකොතේ නායකයාද කියලාත් රටේ ජනතාවට හෙට අනිද්දා වෙනකොට හිතුනොත් එකේ වරදක් නැති වෙයි. දැන් අහුවෙන / උදවු දීපු උන් ඔක්කොම ඉන්නේ  @USER  ත් වැඩිය UNP එකේනේ  @USER  @USER  #srilanka  @USER
  - [NOT] after:  යකෝ බලාගෙන යනකොට මේක පිටිපස්සේ ඉන්නේ  @USER  යේ සිරිකොතේ නායකයාද කියලාත් රටේ ජනතාවට හෙට අනිද්දා වෙනකොට හිතුනොත් එකේ වරදක් නැති වෙයි. දැන් අහුවෙන / help දීපු උන් ඔක්කොම ඉන්නේ  @USER  ත් වැඩිය UNP එකේනේ  @USER  @USER  #srilanka  @USER
  - [OFF] before: කාලකණ්ණි අවස්ථාවාදී දේශාපාලුවන් දැන සිටි පාස්කු ඉරිදා ත්‍රස්ත ප්‍රහාරයට මාස පහයි..මියගිය සියලුම දෙනාට මෝක් සුවය ලැබේවා.. ප්‍රහාරයට උදවු කරපු, ප්‍රහාරය දැනසිට ජාතික සමගිය සහ රටේ සාමකාමී බව නැති කරපු කාලකණ්නි හැතිකරේට හෙන හතම වැදෙවා !!! #lka #SriLanka
  - [OFF] after:  කාලකණ්ණි අවස්ථාවාදී දේශාපාලුවන් දැන සිටි පාස්කු ඉරිදා ත්‍රස්ත ප්‍රහාරයට මාස පහයි..මියගිය සියලුම දෙනාට මෝක් සුවය ලැබේවා.. ප්‍රහාරයට help කරපු, ප්‍රහාරය දැනසිට ජාතික සමගිය සහ රටේ සාමකාමී බව නැති කරපු කාලකණ්නි හැතිකරේට very හතම වැදෙවා !!! #lka #SriLanka

### 2.21. `දන්නවා` -> `know`
- impact: 7 posts (2 light, 5 heavy), 6 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: පතායා Thanos කියලා දාගෙන...යකෝ Thanos දන්නවා නං දෙකට නැමිලා හපාගෙන මැරෙනවා.
  - [OFF] after:  පතායා Thanos කියලා දාගෙන...යකෝ Thanos know නං දෙකට නැමිලා හපාගෙන මැරෙනවා.
  - [OFF] before: @USER  නෙද්දකින් තෝ නම්.මං දන්නවා බොල ඒක
  - [OFF] after:  @USER  නෙද්දකින් තෝ නම්.මං know බොල ඒක
  - [OFF] before: පතායා Thanos කියලා දාගෙන...යකෝ Thanos දන්නවා නං දෙකට නැමිලා හපාගෙන මැරෙනවා.
  - [OFF] after:  පතායා Thanos කියලා දාගෙන...යකෝ Thanos know නං දෙකට නැමිලා හපාගෙන මැරෙනවා.

### 2.22. `පෙන්නන්නේ` -> `show`
- impact: 6 posts (3 light, 3 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER පස්ස තමයි ලොකුවට පෙන්නන්නේ
  - [NOT] after:  @USER පස්ස තමයි ලොකුවට show
  - [NOT] before: @USER පස්ස තමයි ලොකුවට පෙන්නන්නේ
  - [NOT] after:  @USER පස්ස තමයි ලොකුවට show
  - [NOT] before: පකෝ  පව් යකෝ Channa Lakshitha @USER  · 8 Nov 2016 ඔන්න ඔහොමයි ලොකු කරලා පෙන්නන්නේ
  - [NOT] after:  පකෝ  පව් යකෝ Channa Lakshitha @USER  · 8 Nov 2016 ඔන්න ඔහොමයි ලොකු කරලා show

### 2.23. `දැනගන්න` -> `know`
- impact: 6 posts (3 light, 3 heavy), 4 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඇයි බැරි..?? අපි දැනගන්න ඕන කවුද ඒවා තියාගෙන හිටියේ, කොච්චර තිබ්බාද කියලා..
  - [NOT] after:  @USER ඇයි බැරි..?? අපි know ඕන කවුද ඒවා තියාගෙන හිටියේ, කොච්චර තිබ්බාද කියලා..
  - [OFF] before: බල්ලෝ බලල්ලු හදන හැත්ත දැනගන්න ඕනේ උන් හදන සත්තු උන්ගේ වතුවල විතරක් මළපහ කරන විදිහට  හදාගන්න. පාරේ, අනික් මිනිස්සුන්ගේ වතුවල මළපහ කරන්න ඉඩ දීලා ඔහේ බලං ඉන්න උන් බඩ ගිහිල්ලා මැරෙන්න ඕනේ   #සාප
  - [OFF] after:  බල්ලෝ බලල්ලු හදන හැත්ත know ඕනේ උන් හදන සත්තු උන්ගේ වතුවල විතරක් මළපහ කරන විදිහට  හදාගන්න. පාරේ, අනික් මිනිස්සුන්ගේ වතුවල මළපහ කරන්න ඉඩ දීලා ඔහේ බලං ඉන්න උන් බඩ ගිහිල්ලා මැරෙන්න ඕනේ   #සාප
  - [OFF] before: @USER  @USER බිජ්ජ දන්න පුක :3 කාටවත් කියන්නෙපා බුකියෙ ඉන්නෙ හොරාට. මේක මගෙ කියල දැනගත්තට කමක් නෑ හැබැයි බුකියෙ රික් මං කියල දැනගන්න දෙන්නෙපා :3
  - [OFF] after:  @USER  @USER බිජ්ජ දන්න පුක :3 කාටවත් කියන්නෙපා බුකියෙ ඉන්නෙ හොරාට. මේක මගෙ කියල දැනගත්තට කමක් නෑ හැබැයි බුකියෙ රික් මං කියල know දෙන්නෙපා :3

### 2.24. `විශ්වාස` -> `believe`
- impact: 6 posts (3 light, 3 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER කටින් කියන ශාක්සි නම් අදත් හෙටත් හැමදාමත් එයි..හැබැයි ඉතින් ඒවා විශ්වාස කරන්න තරම් මෝඩ වෙන්න එපා
  - [NOT] after:  @USER  @USER කටින් කියන ශාක්සි නම් අදත් හෙටත් හැමදාමත් එයි..හැබැයි ඉතින් ඒවා believe කරන්න තරම් මෝඩ වෙන්න එපා
  - [NOT] before: @USER  @USER කටින් කියන ශාක්සි නම් අදත් හෙටත් හැමදාමත් එයි..හැබැයි ඉතින් ඒවා විශ්වාස කරන්න තරම් මෝඩ වෙන්න එපා
  - [NOT] after:  @USER  @USER කටින් කියන ශාක්සි නම් අදත් හෙටත් හැමදාමත් එයි..හැබැයි ඉතින් ඒවා believe කරන්න තරම් මෝඩ වෙන්න එපා
  - [NOT] before: @USER මම නම් විශ්වාස කලේ නැහැ.
  - [NOT] after:  @USER මම නම් believe කලේ නැහැ.

### 2.25. `නිදි` -> `sleep`
- impact: 6 posts (2 light, 4 heavy), 1 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මොන වලිද අයිසෙ මං නිදි
  - [NOT] after:  @USER මොන වලිද අයිසෙ මං sleep
  - [NOT] before: @USER  නිදි මරාගෙන කොහොමද බොල අඳින්නේ
  - [NOT] after:  @USER  sleep මරාගෙන කොහොමද බොල අඳින්නේ
  - [NOT] before: @USER මොන වලිද අයිසෙ මං නිදි
  - [NOT] after:  @USER මොන වලිද අයිසෙ මං sleep

### 2.26. `කපලා` -> `cut`
- impact: 5 posts (1 light, 4 heavy), 5 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ළමා අපචාර කරන උන්දලගෙ බිජ්ජ කපලා කව්වන්න ඕන උන්ටම.. මූසල බල්ලො... මොන කාලකන්නිකමකට ඉපදුනාද මංදා
  - [OFF] after:  ළමා අපචාර කරන උන්දලගෙ බිජ්ජ cut කව්වන්න ඕන උන්ටම.. මූසල බල්ලො... මොන කාලකන්නිකමකට ඉපදුනාද මංදා
  - [OFF] before: @USER ඕකුන්ගෙ පයිය කපලා හරි තලලා හරි දමන්න ගට තියෙන දායක ඇත්තො ඔය හතර පේරුවෙම නැද්දැ?
  - [OFF] after:  @USER ඕකුන්ගෙ පයිය cut හරි තලලා හරි දමන්න ගට තියෙන දායක ඇත්තො ඔය four පේරුවෙම නැද්දැ?
  - [OFF] before: ළමා අපචාර කරන උන්දලගෙ බිජ්ජ කපලා කව්වන්න ඕන උන්ටම.. මූසල බල්ලො... මොන කාලකන්නිකමකට ඉපදුනාද මංදා
  - [OFF] after:  child අපචාර කරන උන්දලගෙ බිජ්ජ cut කව්වන්න ඕන උන්ටම.. මූසල බල්ලො... මොන කාලකන්නිකමකට ඉපදුනාද මංදා

### 2.27. `නිදාගන්න` -> `sleep`
- impact: 5 posts (2 light, 3 heavy), 0 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පිං මදිද දන්නෑ... කරුම යද දන්නෑ... ST II මතක් වෙද්දි  නිදාගන්න හිතෙන්නෑ... — feeling sleepy
  - [NOT] after:  පිං මදිද දන්නෑ... කරුම යද දන්නෑ... ST II මතක් වෙද්දි  sleep හිතෙන්නෑ... — feeling sleepy
  - [NOT] before: පිං මදිද දන්නෑ... කරුම යද දන්නෑ... ST II මතක් වෙද්දි  නිදාගන්න හිතෙන්නෑ... — feeling sleepy
  - [NOT] after:  පිං මදිද දන්නෑ... කරුම යද දන්නෑ... ST II මතක් වෙද්දි  sleep හිතෙන්නෑ... — feeling sleepy
  - [NOT] before: නිදාගන්න පැය දෙක තුනටත් පේන්නේ මහ කාලකණ්ණි හීන
  - [NOT] after:  sleep පැය දෙක තුනටත් පේන්නේ මහ කාලකණ්ණි හීන

### 2.28. `දන්නව` -> `know`
- impact: 5 posts (2 light, 3 heavy), 5 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER කියන්න ඕනෙ නැ බන්. අපි දන්නව . . . . . . . . . . . . . . . . . . . . උබ ගොනා කියල
  - [OFF] after:  @USER  @USER say ඕනෙ නැ බන්. අපි know . . . . . . . . . . . . . . . . . . . . උබ ගොනා කියල
  - [OFF] before: @USER  @USER ඕකව මට පේන්න බෑ සක්කිලිය මං නම් දන්නව ඕක ගැන.ඒත් අපේ මෝඩ ගෑණු ටිකක් ඉන්නව Twitter එකේ ඕකව අදහන
  - [OFF] after:  @USER  @USER ඕකව මට පේන්න බෑ සක්කිලිය මං නම් know ඕක ගැන.ඒත් අපේ මෝඩ ගෑණු ටිකක් ඉන්නව Twitter එකේ ඕකව අදහන
  - [OFF] before: @USER ඔව් උඹ ගොනා කියල කොයිකවුරුත් දන්නව
  - [OFF] after:  @USER ඔව් උඹ ගොනා කියල කොයිකවුරුත් know

### 2.29. `නවත්වන්න` -> `stop`
- impact: 5 posts (2 light, 3 heavy), 2 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: @USER භුගත ජලයට තෙල් එකතු වීම නවත්වන්න ඒ ප්‍රදේශයේ වැසියන්ගේ දරන උත්සහය අගය කල යුතුයි .
  - [NOT] after:  @USER භුගත ජලයට තෙල් එකතු වීම stop ඒ ප්‍රදේශයේ වැසියන්ගේ දරන උත්සහය අගය කල යුතුයි .
  - [OFF] before: ඈත පලාතකින් කොළඹ ඉන්ටවීව් එක්කට එන කෙල්ලෙක්ට හුජ්ජ බරක් මගදි හැදෙනෝ. බස් කාරයට නවත්වන්න කීවම එහෙනම් ඔයාල බැහැගන්න කියනෝ. අර කට්ටියට ඉන්ටවීව් යන්න පරක්ක්කුය් ලු. ඉතිං ඒකට සහභාගි  වෙන්න ඕනි කියල කිව්වම ඩ්‍රය්වර ඒත් ඇහුවෙ නෑල්ලු.. මට අනුව ඩ්‍රය්වර හරි..
  - [OFF] after:  ඈත පලාතකින් කොළඹ ඉන්ටවීව් එක්කට එන කෙල්ලෙක්ට හුජ්ජ බරක් මගදි හැදෙනෝ. බස් කාරයට stop කීවම එහෙනම් ඔයාල බැහැගන්න කියනෝ. අර කට්ටියට ඉන්ටවීව් යන්න පරක්ක්කුය් ලු. ඉතිං ඒකට සහභාගි  වෙන්න ඕනි කියල කිව්වම ඩ්‍රය්වර ඒත් ඇහුවෙ නෑල්ලු.. මට අනුව ඩ්‍රය්වර හරි..
  - [NOT] before: @USER භුගත ජලයට තෙල් එකතු වීම නවත්වන්න ඒ ප්‍රදේශයේ වැසියන්ගේ දරන උත්සහය අගය කල යුතුයි .
  - [NOT] after:  @USER භුගත ජලයට තෙල් එකතු වීම stop ඒ area එකේ වැසියන්ගේ දරන උත්සහය අගය කල යුතුයි .

### 2.30. `වීවෘත` -> `open`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: @USER ගොඩගම පිවිසුම සිට ඇති කොටස වීවෘත කරලද?
  - [NOT] after:  @USER ගොඩගම පිවිසුම සිට ඇති කොටස open කරලද?
  - [NOT] before: @USER ගොඩගම සිට වීවෘත කරලද?
  - [NOT] after:  @USER ගොඩගම සිට open කරලද?
  - [NOT] before: @USER ගොඩගම පිවිසුම සිට ඇති කොටස වීවෘත කරලද?
  - [NOT] after:  @USER ගොඩගම පිවිසුම සිට ඇති part එක open කරලද?

### 2.31. `මැරිය` -> `die`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  තෝ මැරිය බැල්ලි  @USER  #එකළඟට්වීට්
  - [OFF] after:  @USER  තෝ die බැල්ලි  @USER  #එකළඟට්වීට්
  - [OFF] before: @USER තෝ මැරිය ජිල් හබ් දන් නැත්තම්. තො එක්කො ගේ. නැත්තම් උබට බිජ්ජක් නෑ   @USER
  - [OFF] after:  @USER තෝ die ජිල් හබ් දන් නැත්තම්. තො එක්කො ගේ. නැත්තම් උබට බිජ්ජක් නෑ   @USER
  - [OFF] before: @USER  තෝ මැරිය බැල්ලි  @USER  #එකළඟට්වීට්
  - [OFF] after:  @USER  තෝ die බැල්ලි  @USER  #එකළඟට්වීට්

### 2.32. `බීම` -> `drink`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: native, codemix_plausible: True
  - [OFF] before: @USER @USER  අවජාතක බීම බොන්න ශුවර් නෑ යකෝ.
  - [OFF] after:  @USER @USER  අවජාතක drink බොන්න ශුවර් නෑ යකෝ.
  - [OFF] before: @USER @USER  අවජාතක බීම බොන්න ශුවර් නෑ යකෝ.
  - [OFF] after:  @USER @USER  අවජාතක drink බොන්න sure නෑ යකෝ.
  - [NOT] before: @USER  @USER මෙහෙට සාපේක්ශව පඩි හොදයි නේ. සාමාන්‍ය පෙල කල අයට 40,000කට වැඩි පඩියක් දෙනවා. කියන විදියට වැඩ ගොඩක් අමාරු නෑ. නිල ඇදුම කෑම බීම ප්‍රවාහනයත් එක්ක.
  - [NOT] after:  @USER  @USER මෙහෙට සාපේක්ශව පඩි හොදයි නේ. සාමාන්‍ය පෙල කල අයට 40,000කට වැඩි පඩියක් දෙනවා. කියන විදියට වැඩ ගොඩක් අමාරු නෑ. නිල ඇදුම කෑම drink ප්‍රවාහනයත් එක්ක.

### 2.33. `බොන්න` -> `drink`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කලින් කෑල්ල කිව්වෙ බොන්න එපා මල්ලී කියලා. ඔතන්න එපා කිව්වෙ නෑනේ. ඒ නිසා බොන්නෑ
  - [NOT] after:  @USER කලින් කෑල්ල කිව්වෙ drink එපා මල්ලී කියලා. ඔතන්න එපා කිව්වෙ නෑනේ. ඒ නිසා බොන්නෑ
  - [NOT] before: @USER @USER  කැරකිලා නැමිලා බොන්න බෑ යකූ! උඹ හිතුවද සර්කස් එකක් කියලා :) වාඩිවෙලා බොමු ;-)
  - [NOT] after:  @USER @USER  කැරකිලා නැමිලා drink බෑ යකූ! උඹ හිතුවද සර්කස් එකක් කියලා :) වාඩිවෙලා බොමු ;-)
  - [NOT] before: @USER කලින් කෑල්ල කිව්වෙ බොන්න එපා මල්ලී කියලා. ඔතන්න එපා කිව්වෙ නෑනේ. ඒ නිසා බොන්නෑ
  - [NOT] after:  @USER කලින් girl කිව්වෙ drink එපා මල්ලී කියලා. ඔතන්න එපා කිව්වෙ නෑනේ. ඒ නිසා බොන්නෑ

### 2.34. `අමතන්න` -> `call`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: "ඔබ ඇමතූ ග්‍රාහකයා මේ මොහොතේ සම්බන්දකල නොහැක කරුනාකර මද වෙලාවකින් පසුව අමතන්න...."  "පසුව ගන්න ඔනේනම් දැන් ගන්නවද යකෝ...."  #අපිටඇහෙනකෝල්
  - [NOT] after:  "ඔබ ඇමතූ ග්‍රාහකයා මේ මොහොතේ සම්බන්දකල නොහැක කරුනාකර මද වෙලාවකින් පසුව call...."  "පසුව ගන්න ඔනේනම් දැන් ගන්නවද යකෝ...."  #අපිටඇහෙනකෝල්
  - [NOT] before: "ඔබ ඇමතූ ග්‍රාහකයා මේ මොහොතේ සම්බන්දකල නොහැක කරුනාකර මද වෙලාවකින් පසුව අමතන්න...."  "පසුව ගන්න ඔනේනම් දැන් ගන්නවද යකෝ...."  #අපිටඇහෙනකෝල්
  - [NOT] after:  "ඔබ ඇමතූ ග්‍රාහකයා මේ moment එකේ සම්බන්දකල නොහැක කරුනාකර මද වෙලාවකින් පසුව call...."  "පසුව ගන්න ඔනේනම් දැන් ගන්නවද යකෝ...."  #අපිටඇහෙනකෝල්
  - [OFF] before: ටෞකණ්ඩ  යකෝ...ඒක... V I S H W A @USER  · 14 Sep 2017 ඔබත් තරැණියන්ට සිත නොනැමෙන සියුමැලි තරැණයන්ටම සිත ඇදෙන නීරෝගී තරැණයෙක්ද? ලතැවෙන්න එපා. අමතන්න #TweepsKinkini මුසාප් අහමඩ් බාරේ.
  - [OFF] after:  ටෞකණ්ඩ  යකෝ...ඒක... V I S H W A @USER  · 14 Sep 2017 ඔබත් තරැණියන්ට සිත නොනැමෙන සියුමැලි තරැණයන්ටම සිත ඇදෙන නීරෝගී තරැණයෙක්ද? ලතැවෙන්න එපා. call #TweepsKinkini මුසාප් අහමඩ් බාරේ.

### 2.35. `තේරෙන්නේ` -> `understand`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මටම තේරෙන්නේ නෑ සාන්ත .....
  - [NOT] after:  @USER මටම understand නෑ සාන්ත .....
  - [NOT] before: @USER ඔන්න ඔය තිත්ත ඇත්ත අපේ ගොන් වහන්සෙලට තේරෙන්නේ නෑනේ
  - [NOT] after:  @USER ඔන්න ඔය තිත්ත ඇත්ත අපේ ගොන් වහන්සෙලට understand නෑනේ
  - [NOT] before: @USER මටම තේරෙන්නේ නෑ සාන්ත .....
  - [NOT] after:  @USER මටම understand නෑ සාන්ත .....

### 2.36. `බොන` -> `drink`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඇයි උඹ වෙන කොහෙවත් බොන උන් දැකල නැද්ද
  - [NOT] after:  @USER ඇයි උඹ වෙන කොහෙවත් drink උන් දැකල නැද්ද
  - [NOT] before: @USER ඇයි උඹ වෙන කොහෙවත් බොන උන් දැකල නැද්ද
  - [NOT] after:  @USER ඇයි උඹ වෙන කොහෙවත් drink උන් seen නැද්ද
  - [NOT] before: @USER සුරාවේ ඇති රසයත් එහි ඇති මනා ගුණයත් බොන උතුමෝ මිසක් නොබොන ගොන් තඩි කිසිත් නොදනිත්
  - [NOT] after:  @USER සුරාවේ ඇති රසයත් එහි ඇති මනා ගුණයත් drink උතුමෝ මිසක් නොබොන ගොන් තඩි කිසිත් නොදනිත්

### 2.37. `නිදියන්න` -> `sleep`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මම සහාරාන්ව මෙහෙ උරන් ඵක්ක නිදියන්න දාලා තියෙන්නෙ.
  - [NOT] after:  @USER මම සහාරාන්ව මෙහෙ උරන් ඵක්ක sleep දාලා තියෙන්නෙ.
  - [NOT] before: එහෙනම් මට කලින් තෝ තමයි නිදියන්න ඕන
  - [NOT] after:  එහෙනම් මට කලින් තෝ තමයි sleep ඕන
  - [NOT] before: @USER මම සහාරාන්ව මෙහෙ උරන් ඵක්ක නිදියන්න දාලා තියෙන්නෙ.
  - [NOT] after:  @USER මම සහාරාන්ව මෙහෙ උරන් ඵක්ක sleep දාලා තියෙන්නෙ.

### 2.38. `යවන්න` -> `send`
- impact: 4 posts (1 light, 3 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ගෝපියො  අපේ බැල්ලි වටේ යවන්න එපා
  - [OFF] after:  ගෝපියො  අපේ බැල්ලි වටේ send එපා
  - [NOT] before: උපන් කැත යවන්න බෑ කිව්වවට youcam perfect  එකෙන් ඒකත් පුලුවන් බන්..
  - [NOT] after:  born කැත send බෑ කිව්වවට youcam perfect  එකෙන් ඒකත් පුලුවන් බන්..
  - [NOT] before: @USER දක්සයාට උඩ යන්න දෙන්නෑ මේ වල් හැත්ත. වලටම තමා යවන්න හදන්නේ. ඔයා දුක් වෙන්න එප සුප්පයියේ
  - [NOT] after:  @USER දක්සයාට උඩ යන්න දෙන්නෑ මේ wild හැත්ත. වලටම තමා send හදන්නේ. ඔයා දුක් වෙන්න එප සුප්පයියේ

### 2.39. `දුවනවා` -> `run`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සැරයන් දුවනවා හුත්තො රා ටික දාලා.  තොපි දැක්ක ද
  - [OFF] after:  සැරයන් run හුත්තො රා ටික දාලා.  තොපි දැක්ක ද
  - [OFF] before: සැරයන් දුවනවා හුත්තො රා ටික දාලා.  තොපි දැක්ක ද
  - [OFF] after:  සැරයන් run හුත්තො රා ටික දාලා.  තොපි දැක්ක ද
  - [NOT] before: @USER  @USER කනවා කියන්නෙ... පැලේ අත උස්සගෙනම අනේ මාව කන්න ගොනා අයියේ අනේ මාව කන්න කියනවා.. ගොනා පස්ස නොබලා දුවනවා
  - [NOT] after:  @USER  @USER කනවා කියන්නෙ... පැලේ අත උස්සගෙනම අනේ මාව eat ගොනා අයියේ අනේ මාව eat කියනවා.. ගොනා පස්ස නොබලා run

### 2.40. `තේරෙන්නෙ` -> `understand`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තොට සිංහළ තේරෙන්නෙ නැද්ද ගොන් බිජ්ජො??   This is not a question of "Fake Profiles" or "Real Profiles" .... this is a question of තෝ වගේ කිබි උකුණෙක් අහක යන බඩුවක් නිසා ගූ අැදගෙන නාන එක.  නිකන් පු.. දෙන්නේනැතුව වැඩක් බලාගනින් කිම්බි උකුණො!!! GIF
  - [OFF] after:  @USER  @USER තොට සිංහළ understand නැද්ද ගොන් බිජ්ජො??   This is not a question of "Fake Profiles" or "Real Profiles" .... this is a question of තෝ වගේ කිබි උකුණෙක් අහක යන බඩුවක් නිසා ගූ අැදගෙන නාන එක.  නිකන් පු.. දෙන්නේනැතුව වැඩක් බලාගනින් කිම්බි උකුණො!!! GIF
  - [NOT] before: ශගුන් කියයි ඉශිත කියයි රමං බල්ලා කියයි මොන කුනුහබ්බද බං මේ >:( මට නං තේරෙන්නෙ නෑ -_-  . — feeling angry
  - [NOT] after:  ශගුන් කියයි ඉශිත කියයි රමං dog කියයි මොන කුනුහබ්බද බං මේ >:( මට නං understand නෑ -_-  . — feeling angry
  - [OFF] before: @USER  @USER තොට සිංහළ තේරෙන්නෙ නැද්ද ගොන් බිජ්ජො??   This is not a question of "Fake Profiles" or "Real Profiles" .... this is a question of තෝ වගේ කිබි උකුණෙක් අහක යන බඩුවක් නිසා ගූ අැදගෙන නාන එක.  නිකන් පු.. දෙන්නේනැතුව වැඩක් බලාගනින් කිම්බි උකුණො!!! GIF
  - [OFF] after:  @USER  @USER තොට සිංහළ understand නැද්ද ගොන් බිජ්ජො??   This is not a question of "Fake Profiles" or "Real Profiles" .... this is a question of තෝ වගේ කිබි උකුණෙක් අහක යන බඩුවක් නිසා ගූ අැදගෙන නාන එක.  නිකන් පු.. දෙන්නේනැතුව work බලාගනින් කිම්බි උකුණො!!! GIF

### 2.41. `හොයාගන්න` -> `find`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඊයා ඌ හරකෙක් බන්...ඌව කන්න එකෙක් හොයාගන්න අමාරු වෙයි
  - [OFF] after:  @USER ඊයා ඌ හරකෙක් බන්...ඌව කන්න එකෙක් find අමාරු වෙයි
  - [OFF] before: @USER ඊයා ඌ හරකෙක් බන්...ඌව කන්න එකෙක් හොයාගන්න අමාරු වෙයි
  - [OFF] after:  @USER ඊයා ඌ හරකෙක් බන්...ඌව eat එකෙක් find අමාරු වෙයි
  - [NOT] before: @USER ඇත්ත ම කිව්වොත් කව්ද බල්ලා කියල හොයාගන්න අමාරු උනා එකපාරටම ටිකක් .
  - [NOT] after:  @USER ඇත්ත ම කිව්වොත් කව්ද බල්ලා කියල find අමාරු උනා suddenly ටිකක් .

### 2.42. `ජිවත්` -> `live`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මට මතකයි..  දවසක් එයා කිව්වා  ....  "ඔයා නැති දවසක මම නම් ජිවත් වෙන එකකුත් නෑ" කියලා  ඔය ඉන්නේ යස අගේට  බොරුකාර මී හරකා...   #copied
  - [OFF] after:  මට මතකයි..  දවසක් එයා කිව්වා  ....  "ඔයා නැති දවසක මම නම් live වෙන එකකුත් නෑ" කියලා  ඔය ඉන්නේ යස අගේට  බොරුකාර මී හරකා...   #copied
  - [OFF] before: මට මතකයි..  දවසක් එයා කිව්වා  ....  "ඔයා නැති දවසක මම නම් ජිවත් වෙන එකකුත් නෑ" කියලා  ඔය ඉන්නේ යස අගේට  බොරුකාර මී හරකා...   #copied
  - [OFF] after:  මට මතකයි..  දවසක් එයා කිව්වා  ....  "ඔයා නැති දවසක මම නම් live වෙන එකකුත් නෑ" කියලා  ඔය ඉන්නේ යස අගේට  liar මී හරකා...   #copied
  - [OFF] before: @USER මේ වගේ පොන්න නායකයන්ට යට වෙලා අපිටත් ජිවත් වෙන්න උනානේ.
  - [OFF] after:  @USER මේ වගේ පොන්න නායකයන්ට under වෙලා අපිටත් live වෙන්න උනානේ.

### 2.43. `අල්ලන` -> `catch`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  අල්ලන කෙනෙක් නෑ අෆ්ෆා
  - [NOT] after:  @USER  catch කෙනෙක් නෑ අෆ්ෆා
  - [NOT] before: @USER මුංව අල්ලන්ඩ එපා කියනව නෙමෙයි. මේ හාල්මැස්සො අල්ලන දැලට අර්ජුන් මහේන්ද්‍රන් වගේ මෝරු අහුවෙන්නෙ නැති එකයි පුදුමෙ !
  - [NOT] after:  @USER මුංව අල්ලන්ඩ එපා කියනව නෙමෙයි. මේ හාල්මැස්සො catch දැලට Arjun මහේන්ද්‍රන් වගේ මෝරු අහුවෙන්නෙ නැති එකයි පුදුමෙ !
  - [NOT] before: @USER  අල්ලන කෙනෙක් නෑ අෆ්ෆා
  - [NOT] after:  @USER  catch කෙනෙක් නෑ අෆ්ෆා

### 2.44. `අනුගමනය` -> `follow`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: True
  - [OFF] before: ඔහේප් ... පලයන් ..... ඒ කතාව මොකක්ද .. ? ඒ කියන්නේ යකෝ රට පාවා දෙන සිංහලයෝ  අර දොන් ජුවාන් ධර්මපාල නියායද මේ අනුගමනය කරන්නේ. ගෝල්ෆේස් පිට්ටනියට ගෙනත් සියලු දෙනාගේම දැනගැනීම දඬුවම පිණිස "හරක් ගොම" ගහන්න යෝජනා කරමු neetwit @USER  · 9 Dec 2019 #lka #sriLanka #SriLankanPolitics #Colombo @USER @USER @USER
  - [OFF] after:  ඔහේප් ... පලයන් ..... ඒ කතාව මොකක්ද .. ? ඒ කියන්නේ යකෝ රට පාවා දෙන සිංහලයෝ  අර දොන් ජුවාන් ධර්මපාල නියායද මේ follow කරන්නේ. ගෝල්ෆේස් පිට්ටනියට ගෙනත් සියලු දෙනාගේම දැනගැනීම දඬුවම පිණිස "හරක් ගොම" ගහන්න යෝජනා කරමු neetwit @USER  · 9 Dec 2019 #lka #sriLanka #SriLankanPolitics #Colombo @USER @USER @USER
  - [OFF] before: ඔහේප් ... පලයන් ..... ඒ කතාව මොකක්ද .. ? ඒ කියන්නේ යකෝ රට පාවා දෙන සිංහලයෝ  අර දොන් ජුවාන් ධර්මපාල නියායද මේ අනුගමනය කරන්නේ. ගෝල්ෆේස් පිට්ටනියට ගෙනත් සියලු දෙනාගේම දැනගැනීම දඬුවම පිණිස "හරක් ගොම" ගහන්න යෝජනා කරමු neetwit @USER  · 9 Dec 2019 #lka #sriLanka #SriLankanPolitics #Colombo @USER @USER @USER
  - [OFF] after:  ඔහේප් ... පලයන් ..... ඒ කතාව මොකක්ද .. ? ඒ කියන්නේ යකෝ රට පාවා දෙන සිංහලයෝ  අර දොන් ජුවාන් ධර්මපාල නියායද මේ follow කරන්නේ. ගෝල්ෆේස් පිට්ටනියට ගෙනත් සියලු දෙනාගේම දැනගැනීම දඬුවම පිණිස "හරක් ගොම" ගහන්න proposal කරමු neetwit @USER  · 9 Dec 2019 #lka #sriLanka #SriLankanPolitics #Colombo @USER @USER @USER

### 2.45. `මැරියං` -> `die`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER මැරියං තෝ ලබ්බා
  - [OFF] after:  @USER  @USER die තෝ ලබ්බා
  - [OFF] before: @USER  @USER මැරියං තෝ ලබ්බා
  - [OFF] after:  @USER  @USER die තෝ ලබ්බා

### 2.46. `බලාංකො` -> `look`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ,  @USER  @USER ටහුඩු. මේකි බලාංකො.
  - [NOT] after:  @USER ,  @USER  @USER ටහුඩු. මේකි look.
  - [NOT] before: @USER ,  @USER  @USER ටහුඩු. මේකි බලාංකො.
  - [NOT] after:  @USER ,  @USER  @USER ටහුඩු. මේකි look.

### 2.47. `ලං` -> `close`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඝනිකාවෝ සහා බල්ලියොත් එක්ක නිදාගත්තාම උ විතරක් නෙමෙයි වෙන උන්ටත් නැගිටින්න වෙන්නේ මැක්කියොත් එක්ක තමයි. ඕක බඩුව කියලා නොදැනද කවුරු කවුරුත් ලං කර ගත්තේ. මුන් නිසා ගම්වල පරම්පරා ගානක් කබුරන පාක්ෂිකයින්ටත් වෙන්නේ අසාධාරණයක්.  @USER  #SriLanka #SriLankan  @USER  @USER
  - [OFF] after:  @USER ඝනිකාවෝ සහා බල්ලියොත් එක්ක නිදාගත්තාම උ විතරක් නෙමෙයි වෙන උන්ටත් නැගිටින්න වෙන්නේ මැක්කියොත් එක්ක තමයි. ඕක බඩුව කියලා නොදැනද කවුරු කවුරුත් close කර ගත්තේ. මුන් නිසා ගම්වල පරම්පරා ගානක් කබුරන පාක්ෂිකයින්ටත් වෙන්නේ අසාධාරණයක්.  @USER  #SriLanka #SriLankan  @USER  @USER
  - [OFF] before: @USER ඝනිකාවෝ සහා බල්ලියොත් එක්ක නිදාගත්තාම උ විතරක් නෙමෙයි වෙන උන්ටත් නැගිටින්න වෙන්නේ මැක්කියොත් එක්ක තමයි. ඕක බඩුව කියලා නොදැනද කවුරු කවුරුත් ලං කර ගත්තේ. මුන් නිසා ගම්වල පරම්පරා ගානක් කබුරන පාක්ෂිකයින්ටත් වෙන්නේ අසාධාරණයක්.  @USER  #SriLanka #SriLankan  @USER  @USER
  - [OFF] after:  @USER ඝනිකාවෝ සහා බල්ලියොත් එක්ක නිදාගත්තාම උ විතරක් නෙමෙයි වෙන උන්ටත් නැගිටින්න වෙන්නේ මැක්කියොත් එක්ක තමයි. ඕක බඩුව කියලා නොදැනද කවුරු කවුරුත් close කර ගත්තේ. මුන් නිසා ගම්වල පරම්පරා ගානක් කබුරන පාක්ෂිකයින්ටත් වෙන්නේ අසාධාරණයක්.  @USER  #SriLanka #SriLankan  @USER  @USER

### 2.48. `ඉගෙනගන්න` -> `learn`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER " වේසි " ඔයා වේසි කියල හඟවන්නේ කා හටද? ඒසේ කීම සදාචාරාත්මක නැති බව වැටහෙන්නෙ නැතිද.මේ ඔයාටත්.නංගියෙක් අක්කේ්ක් නැද්ද?ඇයි මේ වගේ ඒවා දාන්නෙ ? අනික කාන්තාවකට මුලින්ම ගරුකරන්න ඉගෙනගන්න.   මේ ඇති නේද..අහල අහල එපාවෙලා තියෙන්නෙ
  - [OFF] after:  @USER " වේසි " ඔයා වේසි කියල හඟවන්නේ කා හටද? ඒසේ කීම සදාචාරාත්මක නැති බව වැටහෙන්නෙ නැතිද.මේ ඔයාටත්.නංගියෙක් අක්කේ්ක් නැද්ද?ඇයි මේ වගේ ඒවා දාන්නෙ ? අනික කාන්තාවකට මුලින්ම ගරුකරන්න learn.   මේ ඇති නේද..අහල අහල එපාවෙලා තියෙන්නෙ
  - [OFF] before: @USER " වේසි " ඔයා වේසි කියල හඟවන්නේ කා හටද? ඒසේ කීම සදාචාරාත්මක නැති බව වැටහෙන්නෙ නැතිද.මේ ඔයාටත්.නංගියෙක් අක්කේ්ක් නැද්ද?ඇයි මේ වගේ ඒවා දාන්නෙ ? අනික කාන්තාවකට මුලින්ම ගරුකරන්න ඉගෙනගන්න.   මේ ඇති නේද..අහල අහල එපාවෙලා තියෙන්නෙ
  - [OFF] after:  @USER " වේසි " ඔයා වේසි කියල හඟවන්නේ කා හටද? ඒසේ කීම සදාචාරාත්මක නැති බව වැටහෙන්නෙ නැතිද.මේ ඔයාටත්.නංගියෙක් අක්කේ්ක් නැද්ද?ඇයි මේ වගේ ඒවා දාන්නෙ ? අනික කාන්තාවකට මුලින්ම ගරුකරන්න learn.   මේ ඇති නේද..අහල අහල එපාවෙලා තියෙන්නෙ

### 2.49. `බාවිතා` -> `use`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER ඇක බාවිතා කරාට කමක් නෑ පුක බාවිතා කරන්න දෙන්න එපා
  - [OFF] after:  @USER  @USER ඇක use කරාට කමක් නෑ පුක use කරන්න දෙන්න එපා
  - [OFF] before: @USER  @USER ඇක බාවිතා කරාට කමක් නෑ පුක බාවිතා කරන්න දෙන්න එපා
  - [OFF] after:  @USER  @USER ඇක use කරාට කමක් නෑ පුක use කරන්න දෙන්න එපා

### 2.50. `සවාරි` -> `ride`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: බලු සිරිසේනගේ අවජාතක පුත්‍රයා ගේ සවාරි යෑම් URL
  - [OFF] after:  බලු සිරිසේනගේ අවජාතක පුත්‍රයා ගේ ride යෑම් URL
  - [OFF] before: බලු සිරිසේනගේ අවජාතක පුත්‍රයා ගේ සවාරි යෑම් URL
  - [OFF] after:  බලු සිරිසේනගේ අවජාතක son ගේ ride යෑම් URL

### 2.51. `බලන්ඩ` -> `see`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER බලන්ඩ දෙයක් නැහැ ඒකත් මැටි ලේඛයක්ම වෙන්ඩඇති
  - [NOT] after:  @USER see දෙයක් නැහැ ඒකත් මැටි ලේඛයක්ම වෙන්ඩඇති
  - [NOT] before: @USER බලන්ඩ දෙයක් නැහැ ඒකත් මැටි ලේඛයක්ම වෙන්ඩඇති
  - [NOT] after:  @USER see thing නැහැ ඒකත් මැටි ලේඛයක්ම වෙන්ඩඇති

### 2.52. `හිටු` -> `stop`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER අනේ මේ පයිය.කට වහන් හිටු
  - [OFF] after:  @USER අනේ මේ පයිය.කට වහන් stop
  - [OFF] before: @USER අනේ මේ පයිය.කට වහන් හිටු
  - [OFF] after:  @USER අනේ මේ පයිය.කට වහන් stop

### 2.53. `භාවිතා` -> `use`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මේ දීමනාව භාවිතා කොට , මේ සක්කිලි හැත්තගේ පුකේ මුද්දර ගසා මුරුසි දිවයිනට තැපල් කල යුතුය. #ජනපතිගෙන්තෑගි Azzam Ameen @USER  · 2 Jan 2018 The annual free stamp allowance for MPs increased 100% from January 1st. Stamp allowance of Rs.175,000 a year will be increased to Rs. 350,000 a year
  - [OFF] after:  මේ දීමනාව use කොට , මේ සක්කිලි හැත්තගේ පුකේ මුද්දර ගසා මුරුසි දිවයිනට තැපල් කල යුතුය. #ජනපතිගෙන්තෑගි Azzam Ameen @USER  · 2 Jan 2018 The annual free stamp allowance for MPs increased 100% from January 1st. Stamp allowance of Rs.175,000 a year will be increased to Rs. 350,000 a year
  - [OFF] before: මේ දීමනාව භාවිතා කොට , මේ සක්කිලි හැත්තගේ පුකේ මුද්දර ගසා මුරුසි දිවයිනට තැපල් කල යුතුය. #ජනපතිගෙන්තෑගි Azzam Ameen @USER  · 2 Jan 2018 The annual free stamp allowance for MPs increased 100% from January 1st. Stamp allowance of Rs.175,000 a year will be increased to Rs. 350,000 a year
  - [OFF] after:  මේ දීමනාව use කොට , මේ සක්කිලි හැත්තගේ පුකේ මුද්දර ගසා මුරුසි දිවයිනට තැපල් කල යුතුය. #ජනපතිගෙන්තෑගි Azzam Ameen @USER  · 2 Jan 2018 The annual free stamp allowance for MPs increased 100% from January 1st. Stamp allowance of Rs.175,000 a year will be increased to Rs. 350,000 a year

### 2.54. `ෆොලෝ` -> `follow`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: True
  - [OFF] before: @USER  @USER    අපරාදේ  තෝ වගේ අපතයෙක් ෆොලෝ කලේ
  - [OFF] after:  @USER  @USER    අපරාදේ  තෝ වගේ අපතයෙක් follow කලේ
  - [OFF] before: @USER  @USER    අපරාදේ  තෝ වගේ අපතයෙක් ෆොලෝ කලේ
  - [OFF] after:  @USER  @USER    අපරාදේ  තෝ වගේ අපතයෙක් follow කලේ

### 2.55. `පාවිච්චිකරනව` -> `use`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER  11 others පල පල  යන්න  . . . තෝ බිජ්ජ දිහා බලන්න පීනිස්කෝප් එකක් පාවිච්චිකරනව නේද ?
  - [OFF] after:  @USER  @USER  11 others පල පල  යන්න  . . . තෝ බිජ්ජ දිහා බලන්න පීනිස්කෝප් එකක් use නේද ?
  - [OFF] before: @USER  @USER  11 others පල පල  යන්න  . . . තෝ බිජ්ජ දිහා බලන්න පීනිස්කෝප් එකක් පාවිච්චිකරනව නේද ?
  - [OFF] after:  @USER  @USER  11 others පල පල  යන්න  . . . තෝ බිජ්ජ දිහා බලන්න පීනිස්කෝප් එකක් use නේද ?

### 2.56. `ඉදපන්` -> `wait`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: තෝ අදෝනා දෙන්නේ නැතුව ඉදපන්
  - [OFF] after:  තෝ අදෝනා දෙන්නේ නැතුව wait
  - [OFF] before: තෝ අදෝනා දෙන්නේ නැතුව ඉදපන්
  - [OFF] after:  තෝ අදෝනා දෙන්නේ නැතුව wait

### 2.57. `කියපං` -> `tell`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER එකටම බන්ඩාරවෙල ඇටම්පිටිය පාර කරන්න කියපං
  - [NOT] after:  @USER එකටම බන්ඩාරවෙල ඇටම්පිටිය පාර කරන්න tell
  - [NOT] before: @USER එකටම බන්ඩාරවෙල ඇටම්පිටිය පාර කරන්න කියපං
  - [NOT] after:  @USER එකටම බන්ඩාරවෙල ඇටම්පිටිය පාර කරන්න tell

### 2.58. `අහපං` -> `ask`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පොන්න පකෝ, තොගෙ තාත්තව  ලබන ආත්මෙදි හරි හම්බුනොත් අහපං "ඇයි තාත්තෙ එදා සරමෙ පිහදා ගන්නෙ නැතුව අම්මට මාව දුන්නෙ" කැරි තම්බියෙක්වත් කියපු නැති කතා කියන්න තොගෙ බූදලයක්ද පකො මේක
  - [OFF] after:  @USER පොන්න පකෝ, තොගෙ තාත්තව  ලබන ආත්මෙදි හරි හම්බුනොත් ask "ඇයි තාත්තෙ එදා සරමෙ පිහදා ගන්නෙ නැතුව අම්මට මාව දුන්නෙ" කැරි තම්බියෙක්වත් කියපු නැති කතා කියන්න තොගෙ බූදලයක්ද පකො මේක
  - [OFF] before: @USER පොන්න පකෝ, තොගෙ තාත්තව  ලබන ආත්මෙදි හරි හම්බුනොත් අහපං "ඇයි තාත්තෙ එදා සරමෙ පිහදා ගන්නෙ නැතුව අම්මට මාව දුන්නෙ" කැරි තම්බියෙක්වත් කියපු නැති කතා කියන්න තොගෙ බූදලයක්ද පකො මේක
  - [OFF] after:  @USER පොන්න පකෝ, තොගෙ තාත්තව  ලබන ආත්මෙදි හරි හම්බුනොත් ask "ඇයි තාත්තෙ එදා සරමෙ පිහදා ගන්නෙ නැතුව අම්මට මාව දුන්නෙ" කැරි තම්බියෙක්වත් කියපු නැති talk කියන්න තොගෙ බූදලයක්ද පකො මේක

### 2.59. `පැරදුනාම` -> `lose`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER රෙද්ද උස්සලා යන්න 10 වෙනිදට පැරදුනාම හූ
  - [OFF] after:  @USER රෙද්ද උස්සලා යන්න 10 වෙනිදට lose හූ
  - [OFF] before: @USER රෙද්ද උස්සලා යන්න 10 වෙනිදට පැරදුනාම හූ
  - [OFF] after:  @USER රෙද්ද උස්සලා යන්න 10 වෙනිදට lose හූ

### 2.60. `තෙරුම්` -> `understand`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඒක මෝඩ වැඩක් කියල පස්සේ තෙරුම් ගත්තා
  - [NOT] after:  @USER ඒක මෝඩ work කියල පස්සේ understand ගත්තා

### 2.61. `ෆලෝත්` -> `follow`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: True
  - [NOT] before: @USER පිස්සා කිය කිය ෆලෝත් කරලා
  - [NOT] after:  @USER maniac කිය කිය follow කරලා

### 2.62. `වරෙං` -> `come`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: දැං රෙද්ද උස්සං වරෙන් UNP ගාගෙන. රස්තියාදුවගේ ඊයේ ට්වීට්ස් බලල වරෙං රෙද්ද උස්සන් එන්න කලින්
  - [OFF] after:  දැං රෙද්ද උස්සං වරෙන් UNP ගාගෙන. රස්තියාදුවගේ ඊයේ ට්වීට්ස් බලල come රෙද්ද උස්සන් come කලින්

### 2.63. `නිදා` -> `sleep`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: කොයි බල්ලා උනත් වට තුන කැරකිලා තමයි නිදා ගන්නේ...
  - [NOT] after:  කොයි බල්ලා උනත් round තුන කැරකිලා තමයි sleep ගන්නේ...

### 2.64. `දුවන්න` -> `run`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: රුවක් ඇඳෙනවා කවුදෝ එනවා අප්පාහ් සසිනි නේද    සසිනි ඔයා හරියට සඳක් වගේ   මන් එච්චම ලස්සනයිද   ඔව්ව් දුරට ලස්සනයි ලගට එච්චර නෑ    දුවන්න එපා තෝ ඔහොම නැවතියන්   මා නැවති සිටිමි ඔබද නවතින්න..
  - [OFF] after:  රුවක් ඇඳෙනවා කවුදෝ එනවා අප්පාහ් සසිනි නේද    සසිනි ඔයා හරියට සඳක් වගේ   මන් එච්චම ලස්සනයිද   ඔව්ව් දුරට ලස්සනයි ලගට that much නෑ    run එපා තෝ ඔහොම නැවතියන්   මා නැවති සිටිමි ඔබද නවතින්න..

### 2.65. `කිට්ටු` -> `close`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER වොක්ස්වැගන් එකටත් කිට්ටු නිසා නැගල යයි... අනේ වාසනාවන්...
  - [NOT] after:  @USER වොක්ස්වැගන් එකටත් close නිසා නැගල යයි... අනේ lucky...

### 2.66. `තියාගනින්` -> `keep`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER සිකේ උඹේ කෑල්ල උඹ තියාගනින්
  - [OFF] after:  @USER  @USER සිකේ උඹේ girl උඹ keep

### 2.67. `දීපං` -> `give`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: දිව්‍යපුත්‍රයට පුක දුන්න කියල තොට රත්තරන් රෙන්ඩ බෑ.. ආං ඒක මතකතියාගෙන දීපං හරී..
  - [OFF] after:  දිව්‍යපුත්‍රයට පුක දුන්න කියල තොට gold රෙන්ඩ බෑ.. ආං ඒක මතකතියාගෙන give හරී..

## TIER 3 — codemix_plausible=False, fires only via fallback. Recommended: YOUR CALL, not bundled into the removal set.

Already judged implausible by human reviewers in rounds 1-3, but still fires: `_apply()` falls back to the full eligible pool when a post has no plausible candidate, rather than leaving it untouched — a deliberate density trade-off (LOG.md Phase 3). Removing all 606 would cost ~10% touched-post coverage; consider trimming to the highest-firing subset instead of an all-or-nothing call.

### 3.1. `කතා` -> `talk`
- impact: 59 posts (25 light, 34 heavy), 32 of them labelled OFF, 66 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හම්බන්තොටයි, මත්තලයි ගැන කතා කරන්න පුලුවන්ද බන් රෙද්ද ඇදන් උබලට, ඒ වගේ 10ක් කරන්න තිබුනා මහ බැංකුවෙන් ගහපු ගැහිල්ලෙන්
  - [NOT] after:  @USER හම්බන්තොටයි, මත්තලයි ගැන talk කරන්න පුලුවන්ද බන් රෙද්ද ඇදන් උබලට, ඒ වගේ 10ක් කරන්න තිබුනා මහ බැංකුවෙන් ගහපු ගැහිල්ලෙන්
  - [OFF] before: @USER ,  @USER  @USER මම නෑ උඹලගේ වල් කතා වලට
  - [OFF] after:  @USER ,  @USER  @USER මම නෑ උඹලගේ වල් talk වලට
  - [NOT] before: @USER All the best ස'. පැය 11-12ක ෆ්ලයිට් එකක නාකි පප්පලා දෙන්නෙක් යනවා ඩිප්ලොමැටික් දේවල් කතා කරන්න.
  - [NOT] after:  @USER All the best ස'. පැය 11-12ක ෆ්ලයිට් එකක නාකි පප්පලා දෙන්නෙක් යනවා ඩිප්ලොමැටික් දේවල් talk කරන්න.

### 3.2. `කෑල්ල` -> `girl`
- impact: 57 posts (26 light, 31 heavy), 11 of them labelled OFF, 57 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER සිකේ උඹේ කෑල්ල උඹ තියාගනින්
  - [OFF] after:  @USER  @USER සිකේ උඹේ girl උඹ තියාගනින්
  - [NOT] before: @USER  @USER ඕගොල්ලොත් හැකි පමණ දායක වෙන්න. ගෑණු ළමයින්ට කෑල්ල කියන්න එපා කිව්වා, දැන් යස අගේට ඔය යුවතිය කියන්නෙ  @USER
  - [NOT] after:  @USER  @USER ඕගොල්ලොත් හැකි පමණ දායක වෙන්න. ගෑණු ළමයින්ට girl කියන්න එපා කිව්වා, දැන් යස අගේට ඔය යුවතිය කියන්නෙ  @USER
  - [NOT] before: @USER කෑල්ල අනේ  එයා දැන් මැද පහන විද්‍යාලයට යයි
  - [NOT] after:  @USER girl අනේ  එයා දැන් මැද පහන විද්‍යාලයට යයි

### 3.3. `වැඩක්` -> `work`
- impact: 55 posts (25 light, 30 heavy), 25 of them labelled OFF, 63 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඒක තමයි කියන්නෙ. ලබ්බ මොකද්ද කියල දන්නැත් නම් දන්නෑ කියල අහන්න ඕනෙ. තප්පුලන්න එපා.. වැඩක් කරන්න බැරිනම් වහගෙන කරන උන්ට කරන්න දීපන්
  - [OFF] after:  @USER ඒක තමයි කියන්නෙ. ලබ්බ මොකද්ද කියල දන්නැත් නම් දන්නෑ කියල අහන්න ඕනෙ. තප්පුලන්න එපා.. work කරන්න බැරිනම් වහගෙන කරන උන්ට කරන්න දීපන්
  - [NOT] before: මට ඉන්නෙ මං උඹට ඉන්නෙ උඹ තමන්ගෙ වැඩක් බලන් පාඩුවෙ හිටපන්...
  - [NOT] after:  මට ඉන්නෙ මං උඹට ඉන්නෙ උඹ තමන්ගෙ work බලන් පාඩුවෙ හිටපන්...
  - [NOT] before: @USER බඩුව ඔරිජිනල්ද වැඩක් නැනේ කන්න පුළුවන් නමි
  - [NOT] after:  @USER බඩුව ඔරිජිනල්ද work නැනේ කන්න පුළුවන් නමි

### 3.4. `වල්` -> `wild`
- impact: 25 posts (10 light, 15 heavy), 16 of them labelled OFF, 29 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ඔීං වල් විදිහට හිතන්න එපා ඈ උබලා
  - [NOT] after:  ඔීං wild විදිහට හිතන්න එපා ඈ උබලා
  - [OFF] before: @USER  @USER තෝ ඒකත් බැලුවද? වල් පරයා.
  - [OFF] after:  @USER  @USER තෝ ඒකත් බැලුවද? wild පරයා.
  - [OFF] before: @USER ගස් ගෙම්බා සමනලයා වල්  ඌරා හරකා මී හරකා රෙපේතයා
  - [OFF] after:  @USER ගස් ගෙම්බා සමනලයා wild  ඌරා හරකා මී හරකා රෙපේතයා

### 3.5. `තාම` -> `still`
- impact: 25 posts (11 light, 14 heavy), 15 of them labelled OFF, 25 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මන් බැලුවා තෝ මොකද තාම මේවා එලියට දැම්මේ නැත්තේ කියලා
  - [NOT] after:  @USER මන් බැලුවා තෝ මොකද still මේවා එලියට දැම්මේ නැත්තේ කියලා
  - [NOT] before: @USER තෝ තාම නිදාගත්තෙ නැද්ද යකෝ
  - [NOT] after:  @USER තෝ still නිදාගත්තෙ නැද්ද යකෝ
  - [OFF] before: @USER පොරගේ වයර් ශෝට් හොඳටම. මූ හිතං ඉන්නේ හිටලර් කියලා. තාම අප්ඩේඩ් කරේ නෑනේ පොරගේ ටිවිටර් එක.
  - [OFF] after:  @USER පොරගේ වයර් ශෝට් හොඳටම. මූ හිතං ඉන්නේ හිටලර් කියලා. still අප්ඩේඩ් කරේ නෑනේ පොරගේ ටිවිටර් එක.

### 3.6. `ගෑනු` -> `women`
- impact: 20 posts (9 light, 11 heavy), 14 of them labelled OFF, 22 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මැරිලත් ඉන්න දෙන්නෙ නෑ මේ ගෑනු නම්
  - [OFF] after:  @USER මැරිලත් ඉන්න දෙන්නෙ නෑ මේ women නම්
  - [OFF] before: මෝඩ වේස ගෑනු  Officer dibble @USER  · 3 Jun 2019 Am I surprised at the response of this Yahapalanaya political stooge for her mockingly catcalling, targetted hate & bigotry towards #SriLanka Maha Sangha? #lka Do you have a choice in disassociating yourself with this type of a person? @USER @USER
  - [OFF] after:  මෝඩ වේස women  Officer dibble @USER  · 3 Jun 2019 Am I surprised at the response of this Yahapalanaya political stooge for her mockingly catcalling, targetted hate & bigotry towards #SriLanka Maha Sangha? #lka Do you have a choice in disassociating yourself with this type of a person? @USER @USER
  - [NOT] before: උඹ එ් පාර මේකත් හබක් කරන්නද යන්නෙ මම ගෑනු ළමයෙක් පස්සෙන් යන මෙතන මට අාදරෙයි කියන්.
  - [NOT] after:  උඹ එ් පාර මේකත් හබක් කරන්නද යන්නෙ මම women ළමයෙක් පස්සෙන් යන මෙතන මට අාදරෙයි කියන්.

### 3.7. `දෙයක්` -> `thing`
- impact: 20 posts (8 light, 12 heavy), 7 of them labelled OFF, 21 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER වැඩි කරන්න දෙයක් නෑනේ බං ඔවිවා නැතිම කරලා දාපල්ලා
  - [NOT] after:  @USER වැඩි කරන්න thing නෑනේ බං ඔවිවා නැතිම කරලා දාපල්ලා
  - [OFF] before: @USER අන්න ඒකයි බන් වටින්නේ... දෙයක් කරලා වේසි වගේ කියව කියව වටේ යන එවුන්ට වඩා බන්
  - [OFF] after:  @USER අන්න ඒකයි බන් වටින්නේ... thing කරලා වේසි වගේ කියව කියව වටේ යන එවුන්ට වඩා බන්
  - [NOT] before: @USER @USER  @USER අම්මෝ ඒක නම් ලොකු දෙයක්
  - [NOT] after:  @USER @USER  @USER අම්මෝ ඒක නම් ලොකු thing

### 3.8. `බොරු` -> `lies`
- impact: 18 posts (9 light, 9 heavy), 8 of them labelled OFF, 20 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER විසිල් විතරයි බල්ටි නැති රාජිත පනින්නට ඉණිමං නැති රාජිත දත් නොගලවන දත්දොස්තර රාජිත ඇයිද බය බොරු නොවේ නම් රාජිත
  - [NOT] after:  @USER විසිල් විතරයි බල්ටි නැති රාජිත පනින්නට ඉණිමං නැති රාජිත දත් නොගලවන දත්දොස්තර රාජිත ඇයිද බය lies නොවේ නම් රාජිත
  - [NOT] before: අයිසෙ ඔහොම බොරු කියන්නෙපා කෝලා  @USER @USER   #එකලගටුවිට්ස්
  - [NOT] after:  අයිසෙ ඔහොම lies කියන්නෙපා කෝලා  @USER @USER   #එකලගටුවිට්ස්
  - [NOT] before: @USER පුරවැසිභාවය නැත්නම් ඔච්චර දගලන්න දෙයක් නෑ නේ.ගෝඨට පුළුවන් වෙන්න ඕනේ ඒක නිතීයානුකූලව ඔප්පු කරන්න.මොකටද නිකන් හෙන්චයියන් දාලා එක එක බොරු කිය කිය දගලන්නේ?
  - [NOT] after:  @USER පුරවැසිභාවය නැත්නම් ඔච්චර දගලන්න දෙයක් නෑ නේ.ගෝඨට පුළුවන් වෙන්න ඕනේ ඒක නිතීයානුකූලව ඔප්පු කරන්න.මොකටද නිකන් හෙන්චයියන් දාලා එක එක lies කිය කිය දගලන්නේ?

### 3.9. `දේවල්` -> `things`
- impact: 15 posts (6 light, 9 heavy), 7 of them labelled OFF, 15 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පුක දීලාම ගෙවිලා ඇති දැන්. ඒත් මිනිහා මේ වෙන දේවල් මාරෙට ඉවසනවා කියලා තේරිලා දුක හිතුනා
  - [OFF] after:  @USER පුක දීලාම ගෙවිලා ඇති දැන්. ඒත් මිනිහා මේ වෙන things මාරෙට ඉවසනවා කියලා තේරිලා දුක හිතුනා
  - [NOT] before: @USER අම්මපා නාකි මටත් හිතෙන දේවල් කොහෙද ඉතිං මුංගේ මේව දැක්කම ඉන්නත් බෑ නොවැ
  - [NOT] after:  @USER අම්මපා නාකි මටත් හිතෙන things කොහෙද ඉතිං මුංගේ මේව දැක්කම ඉන්නත් බෑ නොවැ
  - [OFF] before: මේ අයිසෙ,  වියානා සම්මුතියෙ අපි වගේ බල්ලොන්ට වැඩදායී දේවල් මුකුත් නැද්ද?  Please ignore that හොටුකෑල්ල in my nose
  - [OFF] after:  මේ අයිසෙ,  වියානා සම්මුතියෙ අපි වගේ බල්ලොන්ට වැඩදායී things මුකුත් නැද්ද?  Please ignore that හොටුකෑල්ල in my nose

### 3.10. `ගොඩක්` -> `lot`
- impact: 15 posts (6 light, 9 heavy), 4 of them labelled OFF, 16 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අඩො මෙන්ඩියා දැක්කෙමනෑ  කුණු ගොඩක් නැද්ද මුකුත් අවුස්සලා ගන්න
  - [NOT] after:  අඩො මෙන්ඩියා දැක්කෙමනෑ  කුණු lot නැද්ද මුකුත් අවුස්සලා ගන්න
  - [OFF] before: @USER අන්න ඒකනේ ගොඩක් ගෝත කරුම mute කරලා තියෙන්නේ
  - [OFF] after:  @USER අන්න ඒකනේ lot ගෝත කරුම mute කරලා තියෙන්නේ
  - [NOT] before: යකෝ...ගොඩක් කට්ටිය මොන ගස්ලබ්බකටද...  සමවයසෙ , ලොකු , එක්කෙනෙක් තියල තියන්නම් හොඳේ
  - [NOT] after:  යකෝ...lot කට්ටිය මොන ගස්ලබ්බකටද...  සමවයසෙ , ලොකු , එක්කෙනෙක් තියල තියන්නම් හොඳේ

### 3.11. `අවුරුදු` -> `years`
- impact: 15 posts (7 light, 8 heavy), 8 of them labelled OFF, 15 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අවුරුදු 5ක් කලා  @USER  @USER  @USER  @USER  @USER
  - [NOT] after:  @USER years 5ක් කලා  @USER  @USER  @USER  @USER  @USER
  - [OFF] before: @USER Bro  @USER  , එහෙනන් ලබ්බටද යකෝ අවුරුදු 5ක් ඕව විසදුවේ නැත්තේ. -_-
  - [OFF] after:  @USER Bro  @USER  , එහෙනන් ලබ්බටද යකෝ years 5ක් ඕව විසදුවේ නැත්තේ. -_-
  - [OFF] before: @USER අවුරුදු 27 ක් ඌට නොදකින්
  - [OFF] after:  @USER years 27 ක් ඌට නොදකින්

### 3.12. `අනිත්` -> `other`
- impact: 14 posts (5 light, 9 heavy), 7 of them labelled OFF, 14 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ,  @USER  @USER පුක දෙන එකෙක් වෙන්ටැ. අනිත් ඒව වැඩක් නෑනෙ.
  - [OFF] after:  @USER ,  @USER  @USER පුක දෙන එකෙක් වෙන්ටැ. other ඒව වැඩක් නෑනෙ.
  - [NOT] before: @USER අනිත් උන් ටික යන්නෙ නැද්ද?
  - [NOT] after:  @USER other උන් ටික යන්නෙ නැද්ද?
  - [OFF] before: @USER උඹට එච්චර දෙයක් කරගන්ඩ බෑ.. අනිත් එක තෝ කොහෙන්ද යකෝ එන්නෙ  මොන මගුලක්ද   @USER  @USER
  - [OFF] after:  @USER උඹට එච්චර දෙයක් කරගන්ඩ බෑ.. other එක තෝ කොහෙන්ද යකෝ එන්නෙ  මොන මගුලක්ද   @USER  @USER

### 3.13. `ආයෙ` -> `again`
- impact: 12 posts (6 light, 6 heavy), 4 of them labelled OFF, 12 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER ආයෙ බැල්ලි කියන්න එපා  අපේ හිත්මයි කිලිටි වෙන්නේ
  - [NOT] after:  @USER  @USER again බැල්ලි කියන්න එපා  අපේ හිත්මයි කිලිටි වෙන්නේ
  - [NOT] before: @USER  @USER අඩො මටත් ,ආයෙ බොන්නෙ නෑ කියලා දාන එව්වා දැක්කම
  - [NOT] after:  @USER  @USER අඩො මටත් ,again බොන්නෙ නෑ කියලා දාන එව්වා දැක්කම
  - [NOT] before: චැන්ඩ්ලර් මරු බඩුව ඈ  කොම හරි ආයෙ සූටි කෙල්ලෙක්ව අල්ලගෙන... #lastship
  - [NOT] after:  චැන්ඩ්ලර් මරු බඩුව ඈ  කොම හරි again සූටි කෙල්ලෙක්ව අල්ලගෙන... #lastship

### 3.14. `ගෙම්බා` -> `frog`
- impact: 12 posts (5 light, 7 heavy), 9 of them labelled OFF, 14 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER    නාකි කැහුට්ටු  ගොන් ගෙම්බා
  - [OFF] after:  @USER  @USER    නාකි කැහුට්ටු  ගොන් frog
  - [OFF] before: @USER ඉතිම් ඒකනේ මාත් කිව්වේ ගොනා හකරා ගෙම්බා තඩියා තට්ටයා කොන්ඩයා යනවා යන්න
  - [OFF] after:  @USER ඉතිම් ඒකනේ මාත් කිව්වේ ගොනා හකරා frog තඩියා තට්ටයා කොන්ඩයා යනවා යන්න
  - [NOT] before: ගෙම්බා අද සද්දයක් නැත්තෙ මොකෝ කියලා බැලුවා.. ටහුඩු ඉන්දියවට වඩාගෙන ගහලා ඊයේ
  - [NOT] after:  frog අද සද්දයක් නැත්තෙ මොකෝ කියලා බැලුවා.. ටහුඩු ඉන්දියවට වඩාගෙන ගහලා ඊයේ

### 3.15. `සිරිසේන` -> `Sirisena`
- impact: 11 posts (5 light, 6 heavy), 5 of them labelled OFF, 14 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER අනේ තෝ පලයන් යකෝ යන්න - මීට සිරිසේන
  - [OFF] after:  @USER  @USER අනේ තෝ පලයන් යකෝ යන්න - මීට Sirisena
  - [NOT] before: @USER ඒක නිසා නේ උන් එළවලා දැම්මෙ.. සිරිසේන සූරයා මෙහෙම බලද්දි...
  - [NOT] after:  @USER ඒක නිසා නේ උන් එළවලා දැම්මෙ.. Sirisena සූරයා මෙහෙම බලද්දි...
  - [OFF] before: දෙමළට පුක දීල උඹ පුකේ ඇරවගනින් සිරිසේන URL
  - [OFF] after:  දෙමළට පුක දීල උඹ පුකේ ඇරවගනින් Sirisena URL

### 3.16. `බෙහෙත්` -> `medicine`
- impact: 10 posts (5 light, 5 heavy), 4 of them labelled OFF, 14 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER තව ටික දවසයිනේ බෙහෙත් නොබිව්වට කමක්.නෑ.
  - [NOT] after:  @USER තව ටික දවසයිනේ medicine නොබිව්වට කමක්.නෑ.
  - [OFF] before: මෝඩ කමට බෙහෙත් නෑ.... තිබුණට ඩැඩකුත් නෑ..... මොකද දුන්නට ඔයා ගන්නෙත් නෑ.... ඉතිං මෝඩ කමට බෙහෙත් නෑ.....
  - [OFF] after:  මෝඩ කමට medicine නෑ.... තිබුණට ඩැඩකුත් නෑ..... මොකද දුන්නට ඔයා ගන්නෙත් නෑ.... ඉතිං මෝඩ කමට medicine නෑ.....
  - [OFF] before: @USER  @USER කාලකන්නි ඕකුනගෙ පුක මහලා බඩයන්න බෙහෙත් දෙන්න ඕනා
  - [OFF] after:  @USER  @USER කාලකන්නි ඕකුනගෙ පුක මහලා බඩයන්න medicine දෙන්න ඕනා

### 3.17. `හද` -> `heart`
- impact: 9 posts (3 light, 6 heavy), 3 of them labelled OFF, 12 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER හුජ්ජ කිරීමට මතක් කිරීම සම්බන්ධයෙන්  @USER  මගේ හද පිරි මේව්වා එක
  - [OFF] after:  @USER හුජ්ජ කිරීමට මතක් කිරීම සම්බන්ධයෙන්  @USER  මගේ heart පිරි මේව්වා එක
  - [NOT] before: වලාකුලු වහගත්තට,අහසෙම උන්නට.හාවා තුරුලෙ හිටියට,අඩො හද උබ අයිති මට. .
  - [NOT] after:  වලාකුලු වහගත්තට,අහසෙම උන්නට.හාවා තුරුලෙ හිටියට,අඩො heart උබ belongs මට. .
  - [OFF] before: @USER හුජ්ජ කිරීමට මතක් කිරීම සම්බන්ධයෙන්  @USER  මගේ හද පිරි මේව්වා එක
  - [OFF] after:  @USER හුජ්ජ කිරීමට මතක් කිරීම සම්බන්ධයෙන්  @USER  මගේ heart පිරි මේව්වා එක

### 3.18. `ආයේ` -> `again`
- impact: 8 posts (4 light, 4 heavy), 4 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සෑහෙන හැදිලා ඉන්නේ ගෙදරින් ආවට පස්සේ. ඒත් මේ සමහර ගොන් පක්කු ආයේ මාව සතා කරගන්න දඟලනවා. හුත්ත පාඩුවේ ඉන්න දෙන්නෙ නෑනේ
  - [OFF] after:  සෑහෙන හැදිලා ඉන්නේ ගෙදරින් ආවට පස්සේ. ඒත් මේ සමහර ගොන් පක්කු again මාව සතා කරගන්න දඟලනවා. හුත්ත පාඩුවේ ඉන්න දෙන්නෙ නෑනේ
  - [NOT] before: @USER ආයේ නාවට කමක් නේ
  - [NOT] after:  @USER again නාවට කමක් නේ
  - [OFF] before: BCD 1975 මේ පොන්න හුකන්නා ආයේ පුත්තලමේ මගේ ඇස් දෙකට පේන්නනම් එන්න එපා කැරි හම්බයා
  - [OFF] after:  BCD 1975 මේ පොන්න හුකන්නා again පුත්තලමේ මගේ ඇස් දෙකට පේන්නනම් එන්න එපා කැරි හම්බයා

### 3.19. `මනුස්සයා` -> `man`
- impact: 8 posts (3 light, 5 heavy), 0 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER    ලෝගගෙ කැත ෆොටෝම ගන්න එපා බොලව් පවු ඒ මනුස්සයා
  - [NOT] after:  @USER  @USER    ලෝගගෙ කැත ෆොටෝම ගන්න එපා බොලව් පවු ඒ man
  - [NOT] before: @USER  ඒ මනුස්සයා මොනව කරන්නද ,නියෝග දුන්න කෙනා කෝ
  - [NOT] after:  @USER  ඒ man මොනව කරන්නද ,නියෝග දුන්න කෙනා කෝ
  - [NOT] before: @USER මනුස්සයා අනුරාධපුරෙ පුරවැසියෙක් වෙලා ඉන්නකොට ඔහොම අහන්නෙ මොන හිතකින්ද අයිසෙ
  - [NOT] after:  @USER man අනුරාධපුරෙ පුරවැසියෙක් වෙලා ඉන්නකොට ඔහොම අහන්නෙ මොන හිතකින්ද අයිසෙ

### 3.20. `උඩ` -> `up`
- impact: 8 posts (3 light, 5 heavy), 3 of them labelled OFF, 10 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හුම්ම්ම් උං උඩයන්න උඩ යන්න අපිටයි අමාරු.
  - [NOT] after:  @USER හුම්ම්ම් උං උඩයන්න up යන්න අපිටයි අමාරු.
  - [NOT] before: @USER @USER කව්ද බොල උඩ බලන් හිටියේ .   @USER
  - [NOT] after:  @USER @USER කව්ද බොල up බලන් හිටියේ .   @USER
  - [NOT] before: @USER හුම්ම්ම් උං උඩයන්න උඩ යන්න අපිටයි අමාරු.
  - [NOT] after:  @USER හුම්ම්ම් උං උඩයන්න up යන්න අපිටයි අමාරු.

### 3.21. `පහුගිය` -> `last`
- impact: 8 posts (4 light, 4 heavy), 2 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER වහ ඉල්ලා උද්ගොශනය කරා නේද පහුගිය කාලේ.
  - [NOT] after:  @USER වහ ඉල්ලා උද්ගොශනය කරා නේද last කාලේ.
  - [NOT] before: @USER පහුගිය අවුරැදු හතර හමාරේ වගේ ,
  - [NOT] after:  @USER last අවුරැදු හතර හමාරේ වගේ ,
  - [NOT] before: @USER හයියෝ පොඩි ස' නන්දිකඩාල් ගිහිං හිටියද? දැක්කෙත් නෑ පහුගිය කාලේ
  - [NOT] after:  @USER හයියෝ පොඩි ස' නන්දිකඩාල් ගිහිං හිටියද? දැක්කෙත් නෑ last කාලේ

### 3.22. `අසරණ` -> `helpless`
- impact: 8 posts (3 light, 5 heavy), 3 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කොහෙන් ගියත් හිටං තමයි අසරණ වෙන්නේ    ලක්ශේ ඔයාලට සාප වෙනවා මේ කරපු අපරාදෙට   #lka #PoliticalCrisisLK
  - [OFF] after:  කොහෙන් ගියත් හිටං තමයි helpless වෙන්නේ    ලක්ශේ ඔයාලට සාප වෙනවා මේ කරපු අපරාදෙට   #lka #PoliticalCrisisLK
  - [NOT] before: තනි වුනු ඇයයි . අසරණ ඔබයි මට සාප කර යාවිදෝ  #sajje
  - [NOT] after:  තනි වුනු ඇයයි . helpless ඔබයි මට සාප කර යාවිදෝ  #sajje
  - [OFF] before: කොහෙන් ගියත් හිටං තමයි අසරණ වෙන්නේ    ලක්ශේ ඔයාලට සාප වෙනවා මේ කරපු අපරාදෙට   #lka #PoliticalCrisisLK
  - [OFF] after:  කොහෙන් ගියත් හිටං තමයි helpless වෙන්නේ    ලක්ශේ ඔයාලට සාප වෙනවා මේ කරපු අපරාදෙට   #lka #PoliticalCrisisLK

### 3.23. `එච්චර` -> `that much`
- impact: 8 posts (3 light, 5 heavy), 5 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER ශැහ් එච්චර නාකි කරන්න එපා අපේකාන්තනාව
  - [NOT] after:  @USER  @USER ශැහ් that much නාකි කරන්න එපා අපේකාන්තනාව
  - [OFF] before: @USER උඹට එච්චර දෙයක් කරගන්ඩ බෑ.. අනිත් එක තෝ කොහෙන්ද යකෝ එන්නෙ  මොන මගුලක්ද   @USER  @USER
  - [OFF] after:  @USER උඹට that much දෙයක් කරගන්ඩ බෑ.. other එක තෝ කොහෙන්ද යකෝ එන්නෙ  මොන මගුලක්ද   @USER  @USER
  - [NOT] before: @USER  @USER ජූඩි ඔයා එච්චර මෝඩ වැඩක් කළා කියලා මට විශ්වාස කරන්නත් බෑ
  - [NOT] after:  @USER  @USER ජූඩි ඔයා that much මෝඩ වැඩක් did කියලා මට විශ්වාස කරන්නත් බෑ

### 3.24. `එහෙනං` -> `then`
- impact: 8 posts (4 light, 4 heavy), 4 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අඩො sale දාලද  ගන්න ඕනෙ එහෙනං
  - [NOT] after:  @USER අඩො sale දාලද  ගන්න ඕනෙ then
  - [OFF] before: @USER එහෙනං තෝ පල මංම කොරගන්නං
  - [OFF] after:  @USER then තෝ පල මංම කොරගන්නං
  - [NOT] before: @USER කලින් තිබ්බ ටික තියාගන්න තිබ්බෙ  එහෙනං මෙච්චර කාලකණ්ණි වෙන්නෙ නෑ බ්ස්ං
  - [NOT] after:  @USER කලින් තිබ්බ ටික තියාගන්න තිබ්බෙ  then මෙච්චර කාලකණ්ණි වෙන්නෙ නෑ බ්ස්ං

### 3.25. `ඔවු` -> `yes`
- impact: 8 posts (4 light, 4 heavy), 4 of them labelled OFF, 10 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔවු අයිසෙ ,කට වහගෙන හිනා උනෙ මන්
  - [NOT] after:  @USER yes අයිසෙ ,කට වහගෙන හිනා උනෙ මන්
  - [NOT] before: @USER ඔවු ඔවු ඒකි තමා #පිංකිකෙල්ල
  - [NOT] after:  @USER yes yes ඒකි තමා #පිංකිකෙල්ල
  - [OFF] before: @USER ඔවු කාලකන්නි සක්කිලි ..
  - [OFF] after:  @USER yes කාලකන්නි සක්කිලි ..

### 3.26. `නිවන්` -> `nirvana`
- impact: 8 posts (4 light, 4 heavy), 0 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔබතුමාට නිවන් සුව ලැබේ වා
  - [NOT] after:  @USER ඔබතුමාට nirvana සුව ලැබේ වා
  - [NOT] before: @USER  @USER නිවන් සුව ඔබ තුමියට ...!!!
  - [NOT] after:  @USER  @USER nirvana සුව ඔබ තුමියට ...!!!
  - [NOT] before: @USER නිවන් සුව අත් වේවා
  - [NOT] after:  @USER nirvana සුව අත් වේවා

### 3.27. `හැමෝටම` -> `everyone`
- impact: 7 posts (3 light, 4 heavy), 4 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: පයිය කොට හැමෝටම රිදිලා නේද.?
  - [OFF] after:  පයිය කොට everyone රිදිලා නේද.?
  - [NOT] before: මගේ නම කියලා හැමෝටම කතා කරන්න එපා..      මීට ගොනා.
  - [NOT] after:  මගේ නම කියලා everyone talk කරන්න එපා..      මීට ගොනා.
  - [OFF] before: පයිය කොට හැමෝටම රිදිලා නේද.?
  - [OFF] after:  පයිය කොට everyone රිදිලා නේද.?

### 3.28. `පාරේ` -> `road එකේ`
- impact: 7 posts (2 light, 5 heavy), 1 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පුතී අයින් වීලා පාරේ පලයන්
  - [NOT] after:  පුතී අයින් වීලා road එකේ පලයන්
  - [NOT] before: අම්මෝහ් මාව හරි පාරේ එක්කන් පලයන් හොදේ ජී Kaushalya Jee  URL
  - [NOT] after:  අම්මෝහ් මාව හරි road එකේ එක්කන් පලයන් ok ජී Kaushalya Jee  URL
  - [OFF] before: එන්න එන්නම එපා කරවනවා!! නපුන්සක Thilanga Sumathipala ගොං පොන්නයා!! මකබෑවිලා යන්නේ නෑ නේ පාරේ බල්ලේක් වගේ මූව!! තූ නොදකින්!!!  URL
  - [OFF] after:  come එන්නම එපා කරවනවා!! නපුන්සක Thilanga Sumathipala ගොං පොන්නයා!! මකබෑවිලා යන්නේ නෑ නේ road එකේ බල්ලේක් වගේ මූව!! තූ නොදකින්!!!  URL

### 3.29. `කඩ්ඩ` -> `English`
- impact: 7 posts (3 light, 4 heavy), 1 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ටහුඩු... කඩ්ඩ...  Nimesh Nishara @USER  · 16 Dec 2015  @USER @USER as far as I know there is no rollback action  that thing happened to me too,but there's no reverse :(
  - [NOT] after:  ටහුඩු... English...  Nimesh Nishara @USER  · 16 Dec 2015  @USER @USER as far as I know there is no rollback action  that thing happened to me too,but there's no reverse :(
  - [NOT] before: ටහුඩු ඒ කියන්නෙ මගෙ කඩ්ඩ පොලිශ් වෙනවා ඉස්සරහට  සුලා @USER  · 24 Jan 2019 ජෙරියගේ අනාගත කාල SS එකක් හම්බුණා ප්‍රෙන්ස්..  @USER
  - [NOT] after:  ටහුඩු ඒ කියන්නෙ මගෙ English පොලිශ් වෙනවා ඉස්සරහට  සුලා @USER  · 24 Jan 2019 ජෙරියගේ අනාගත කාල SS එකක් හම්බුණා ප්‍රෙන්ස්..  @USER
  - [NOT] before: ටහුඩු... කඩ්ඩ...  Nimesh Nishara @USER  · 16 Dec 2015  @USER @USER as far as I know there is no rollback action  that thing happened to me too,but there's no reverse :(
  - [NOT] after:  ටහුඩු... English...  Nimesh Nishara @USER  · 16 Dec 2015  @USER @USER as far as I know there is no rollback action  that thing happened to me too,but there's no reverse :(

### 3.30. `කොහෙන්ද` -> `where from`
- impact: 7 posts (2 light, 5 heavy), 4 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER කොහෙන්ද ඩෑලෙකක්  පහත්වෙලා නොදකින්..*කැරියා.. *හුත්තටත් වදිනවා මූසලයා කියලා බැනලා එලෙව්වලු නේ..  පෟ නේද?
  - [OFF] after:  @USER where from ඩෑලෙකක්  පහත්වෙලා නොදකින්..*කැරියා.. *හුත්තටත් වදිනවා මූසලයා කියලා බැනලා එලෙව්වලු නේ..  පෟ නේද?
  - [NOT] before: @USER  @USER මේවට අපි කොහෙන්ද හිනා වෙන්න ඕනේ!?
  - [NOT] after:  @USER  @USER මේවට අපි where from laugh වෙන්න ඕනේ!?
  - [OFF] before: @USER කොහෙන්ද ඩෑලෙකක්  පහත්වෙලා නොදකින්..*කැරියා.. *හුත්තටත් වදිනවා මූසලයා කියලා බැනලා එලෙව්වලු නේ..  පෟ නේද?
  - [OFF] after:  @USER where from ඩෑලෙකක්  පහත්වෙලා නොදකින්..*කැරියා.. *හුත්තටත් වදිනවා මූසලයා කියලා බැනලා එලෙව්වලු නේ..  පෟ නේද?

### 3.31. `හැදුවේ` -> `made`
- impact: 7 posts (3 light, 4 heavy), 5 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: කොච්චර අමාරු වුණත් මැරෙන්න කලින් කොකිස් ටිකක් කෑවා  @USER  තමයි හැදුවේ #මැරෙන්න_කලින්
  - [NOT] after:  කොච්චර අමාරු වුණත් මැරෙන්න කලින් කොකිස් ටිකක් කෑවා  @USER  තමයි made #මැරෙන්න_කලින්
  - [OFF] before: @USER පල යන්න :@  තෝ මාව ගොනාට අන්දන්න නේ හැදුවේ
  - [OFF] after:  @USER පල යන්න :@  තෝ මාව ගොනාට අන්දන්න නේ made
  - [OFF] before: @USER ,  @USER  @USER කව්ද යකෝ දිලීපයියගේ පක කන්න හැදුවේ.
  - [OFF] after:  @USER ,  @USER  @USER කව්ද යකෝ දිලීපයියගේ පක කන්න made.

### 3.32. `හතර` -> `four`
- impact: 7 posts (3 light, 4 heavy), 4 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඕකුන්ගෙ පයිය කපලා හරි තලලා හරි දමන්න ගට තියෙන දායක ඇත්තො ඔය හතර පේරුවෙම නැද්දැ?
  - [OFF] after:  @USER ඕකුන්ගෙ පයිය කපලා හරි තලලා හරි දමන්න ගට තියෙන දායක ඇත්තො ඔය four පේරුවෙම නැද්දැ?
  - [OFF] before: @USER  @USER තෝ කියන්නෙ මගෙ පයිය මෙන්නෙ මෙච්චරයි කිය කිය හතර වටේ යන්ඩද.
  - [OFF] after:  @USER  @USER තෝ කියන්නෙ මගෙ පයිය මෙන්නෙ මෙච්චරයි කිය කිය four වටේ යන්ඩද.
  - [OFF] before: @USER ඕකුන්ගෙ පයිය කපලා හරි තලලා හරි දමන්න ගට තියෙන දායක ඇත්තො ඔය හතර පේරුවෙම නැද්දැ?
  - [OFF] after:  @USER ඕකුන්ගෙ පයිය cut හරි තලලා හරි දමන්න ගට තියෙන දායක ඇත්තො ඔය four පේරුවෙම නැද්දැ?

### 3.33. `වද` -> `trouble`
- impact: 7 posts (3 light, 4 heavy), 5 of them labelled OFF, 9 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පල හුත්තී යන්න වද වේසී
  - [OFF] after:  @USER පල හුත්තී යන්න trouble වේසී
  - [OFF] before: @USER  @USER    ඒක අම්මට යසට මගේ අප්පා කලා. උඹ ඒකට වද වෙන්න එපා පක චලකයෝ
  - [OFF] after:  @USER  @USER    ඒක අම්මට යසට මගේ අප්පා කලා. උඹ ඒකට trouble වෙන්න එපා පක චලකයෝ
  - [NOT] before: @USER වද කොත්තු, වද බෙශියර් මතක් උනාද?
  - [NOT] after:  @USER trouble කොත්තු, trouble බෙශියර් මතක් උනාද?

### 3.34. `අස්සේ` -> `inside`
- impact: 7 posts (3 light, 4 heavy), 5 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: නොම්බරේ ලියලා තිබ්බ කොල කෑල්ල headup display එක අස්සේ වැටුනා කියාන්කො
  - [NOT] after:  නොම්බරේ ලියලා තිබ්බ කොල කෑල්ල headup display එක inside වැටුනා කියාන්කො
  - [OFF] before: මහින්දගේ රෙද්ද අස්සේ දෙහි ගෙඩි 3 යි හොඬල අලයයි URL
  - [OFF] after:  මහින්දගේ රෙද්ද inside දෙහි ගෙඩි 3 යි හොඬල අලයයි URL
  - [NOT] before: නොම්බරේ ලියලා තිබ්බ කොල කෑල්ල headup display එක අස්සේ වැටුනා කියාන්කො
  - [NOT] after:  නොම්බරේ ලියලා තිබ්බ leaf කෑල්ල headup display එක inside වැටුනා කියාන්කො

### 3.35. `සද්ද` -> `noise`
- impact: 7 posts (3 light, 4 heavy), 6 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  @USER   අඩො සද්ද තියාගන්න එපා
  - [OFF] after:  @USER @USER  @USER   අඩො noise තියාගන්න එපා
  - [OFF] before: ඇයි සද්ද කළොත් අල්ලා ලබ්බ තලයිද..?   . . . . . . . . . . අල්ලාගේ ලබ්බ තමයි!!!    #IslamicExtremism #SriLanka #wtdPerera
  - [OFF] after:  ඇයි noise කළොත් අල්ලා ලබ්බ තලයිද..?   . . . . . . . . . . අල්ලාගේ ලබ්බ තමයි!!!    #IslamicExtremism #SriLanka #wtdPerera
  - [OFF] before: @USER @USER  @USER  අඩො සද්ද දාන්න එපා
  - [OFF] after:  @USER @USER  @USER  අඩො noise දාන්න එපා

### 3.36. `හින්ද` -> `because`
- impact: 7 posts (3 light, 4 heavy), 4 of them labelled OFF, 9 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER අනේ යකෝ. කෙල වෙලා තියෙන්නෙ වෙන කවිරුත් හින්ද නෙමෙයි තමුසෙලා වගේ ගොන්නු හින්දා. හැම ප්‍රශ්නෙම අනුන්ගෙ පිට දාන්නැතුව තමුන් හැදෙන්න බලපන්. මෝඩ ගෙම්බා..
  - [OFF] after:  @USER  @USER අනේ යකෝ. කෙල වෙලා තියෙන්නෙ වෙන කවිරුත් because නෙමෙයි තමුසෙලා වගේ ගොන්නු හින්දා. හැම ප්‍රශ්නෙම අනුන්ගෙ පිට දාන්නැතුව තමුන් හැදෙන්න බලපන්. මෝඩ ගෙම්බා..
  - [OFF] before: @USER  @USER ඇයි ඒ කරන්නෙ... අපිට ඕනි හින්ද පකෝ...  තොට ඕනිනම් අහක බල0 පල...
  - [OFF] after:  @USER  @USER ඇයි ඒ කරන්නෙ... අපිට ඕනි because පකෝ...  තොට ඕනිනම් අහක බල0 පල...
  - [NOT] before: දිව්‍ය අන්ගනාවන්ට අපට වාගෙ තරහ යන්නෙ නෑ ඒක හින්ද ඒ උදවිය කිසිමදාක නාකි වෙන්නෙ නෑ.. #sajje
  - [NOT] after:  දිව්‍ය අන්ගනාවන්ට අපට like තරහ යන්නෙ නෑ ඒක because ඒ උදවිය කිසිමදාක නාකි වෙන්නෙ නෑ.. #sajje

### 3.37. `පස්සෙන්` -> `behind`
- impact: 7 posts (3 light, 4 heavy), 4 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: උඹ එ් පාර මේකත් හබක් කරන්නද යන්නෙ මම ගෑනු ළමයෙක් පස්සෙන් යන මෙතන මට අාදරෙයි කියන්.
  - [NOT] after:  උඹ එ් පාර මේකත් හබක් කරන්නද යන්නෙ මම women ළමයෙක් behind යන මෙතන මට අාදරෙයි කියන්.
  - [OFF] before: @USER ඊයා ඕයී මේ මොකාද, මෙහෙ ඉස්සර හිටියා පොන්න සරා කියලා එකෙක් මේක දැක්කම ඌවම මතක් උනා ඌ වගේමයි. ඒ ප$& මගෙ පස්සෙන් ඇවිත්.... නෑ ඔය ඇති
  - [OFF] after:  @USER ඊයා ඕයී මේ මොකාද, මෙහෙ ඉස්සර හිටියා පොන්න සරා කියලා එකෙක් මේක දැක්කම ඌවම මතක් උනා ඌ වගේමයි. ඒ ප$& මගෙ behind ඇවිත්.... නෑ ඔය ඇති
  - [NOT] before: @USER ඔව් කරුම පස්සෙන් එනවා ආච්චියා..
  - [NOT] after:  @USER ඔව් කරුම behind එනවා ආච්චියා..

### 3.38. `බයයි` -> `scared`
- impact: 7 posts (3 light, 4 heavy), 0 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අපේ අම්මට බල්ලත් බයයි කියපංකෝ  දුප් කිව්වගමන් බල්ලා කුඩුවට ගිහින් දොරත් වහගන්නවා
  - [NOT] after:  අපේ අම්මට බල්ලත් scared කියපංකෝ  දුප් කිව්වගමන් බල්ලා කුඩුවට ගිහින් දොරත් වහගන්නවා
  - [NOT] before: @USER අප්පටෛකේ යකෝ මේ ගෑණි   ගිණිපෙනෙල්ලෙන් බැට කාපු උන් LED එකටත් බයයි කියලා කිව්වට මේකටත් ඩොනේට් කරන උන් ඉඳී කියලා සෑහෙන්න විශ්වාසයක් තියෙනවා මට නම්
  - [NOT] after:  @USER අප්පටෛකේ යකෝ මේ ගෑණි   ගිණිපෙනෙල්ලෙන් බැට කාපු උන් LED එකටත් scared කියලා කිව්වට මේකටත් ඩොනේට් කරන උන් ඉඳී කියලා සෑහෙන්න විශ්වාසයක් තියෙනවා මට නම්
  - [NOT] before: හමයයි නෙමේ යකෝ..ගිනිගත්තොත් ඒම කාට කියන්නද.. P U S P E @USER  · 5 Dec 2019  @USER හමයයි කියලා බයයි බන්
  - [NOT] after:  හමයයි නෙමේ යකෝ..ගිනිගත්තොත් ඒම කාට කියන්නද.. P U S P E @USER  · 5 Dec 2019  @USER හමයයි කියලා scared බන්

### 3.39. `ඊයෙ` -> `yesterday`
- impact: 6 posts (3 light, 3 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඊයෙ පෙරේද⁣ ආවෙ බොල. Kamikaze
  - [NOT] after:  @USER yesterday පෙරේද⁣ ආවෙ බොල. Kamikaze
  - [NOT] before: @USER ,  @USER  @USER අඩො අයියෙ ඊයෙ මොනාද විකුන්නෙ
  - [NOT] after:  @USER ,  @USER  @USER අඩො අයියෙ yesterday මොනාද විකුන්නෙ
  - [NOT] before: @USER ඊයෙ පෙරේද⁣ ආවෙ බොල. Kamikaze
  - [NOT] after:  @USER yesterday පෙරේද⁣ ආවෙ බොල. Kamikaze

### 3.40. `පැතුම්` -> `wishes`
- impact: 6 posts (3 light, 3 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER    සුභ පැතුම් තඩි බෝලයා
  - [NOT] after:  @USER  @USER    සුභ wishes තඩි බෝලයා
  - [NOT] before: @USER සුභ පැතුම් විතරක් ඇති ...
  - [NOT] after:  @USER සුභ wishes විතරක් ඇති ...
  - [NOT] before: @USER  @USER    සුභ පැතුම් තඩි බෝලයා
  - [NOT] after:  @USER  @USER    සුභ wishes තඩි බෝලයා

### 3.41. `වට` -> `round`
- impact: 6 posts (3 light, 3 heavy), 4 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: කොයි බල්ලා උනත් වට තුන කැරකිලා තමයි නිදා ගන්නේ...
  - [NOT] after:  කොයි බල්ලා උනත් round තුන කැරකිලා තමයි නිදා ගන්නේ...
  - [OFF] before: @USER ආහ් ආවද පොන්න පකයා. අල්ලා??? තොගෙ පයිය අල්ලලා වට කරලා ඇදලා ගහ ගනින් තොගෙ පුකේ.. වනචර බල්ලා
  - [OFF] after:  @USER ආහ් ආවද පොන්න පකයා. අල්ලා??? තොගෙ පයිය අල්ලලා round කරලා ඇදලා ගහ ගනින් තොගෙ පුකේ.. වනචර බල්ලා
  - [NOT] before: කොයි බල්ලා උනත් වට තුන කැරකිලා තමයි නිදා ගන්නේ...
  - [NOT] after:  කොයි බල්ලා උනත් round තුන කැරකිලා තමයි sleep ගන්නේ...

### 3.42. `ඇහුවෙ` -> `asked`
- impact: 6 posts (3 light, 3 heavy), 4 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඔව් ඇත්තටම කවුරැත් ඇහුවෙ නෑනෙ අරාබි පක්කො මෙහෙ ගෙන්නගෙන මොනවද කරන්න හැදුවෙ කියලා
  - [OFF] after:  @USER ඔව් ඇත්තටම කවුරැත් asked නෑනෙ අරාබි පක්කො මෙහෙ ගෙන්නගෙන මොනවද කරන්න හැදුවෙ කියලා
  - [OFF] before: @USER ඔව් ඇත්තටම කවුරැත් ඇහුවෙ නෑනෙ අරාබි පක්කො මෙහෙ ගෙන්නගෙන මොනවද කරන්න හැදුවෙ කියලා
  - [OFF] after:  @USER ඔව් ඇත්තටම කවුරැත් asked නෑනෙ arabi පක්කො මෙහෙ ගෙන්නගෙන මොනවද කරන්න හැදුවෙ කියලා
  - [OFF] before: තෝ තමා ඔක්කොම කලේ බරී කැල්ලා  @USER  @USER  දැක්කා නේ deffy: @USER  · 25 Jan 2019 හැම එකක්ම ඇහුවෙ මම මුං කනියව අහුකරලා twitter.com/Its_DHD/status…
  - [OFF] after:  තෝ තමා ඔක්කොම කලේ බරී කැල්ලා  @USER  @USER  දැක්කා නේ deffy: @USER  · 25 Jan 2019 හැම එකක්ම asked මම මුං කනියව අහුකරලා twitter.com/Its_DHD/status…

### 3.43. `ගාව` -> `near`
- impact: 6 posts (3 light, 3 heavy), 4 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මම හැරිසන් ගාව හිටියේ තොපේ අමිමලාට ………….වනවා බයියලාගේ .මම ලංකාවට ඇවිත් තොට කන පැලෙන්න ගහනවා. මම සිසිර කුමාර... URL
  - [OFF] after:  මම හැරිසන් near හිටියේ තොපේ අමිමලාට ………….වනවා බයියලාගේ .මම ලංකාවට ඇවිත් තොට කන පැලෙන්න ගහනවා. මම සිසිර කුමාර... URL
  - [OFF] before: මිනිහා වෙනම වාඩිවෙලා ගෑණි තමුසෙ ගාව වාඩි කරන්න ඕනේ
  - [OFF] after:  මිනිහා වෙනම වාඩිවෙලා ගෑණි තමුසෙ near වාඩි කරන්න ඕනේ
  - [OFF] before: මම හැරිසන් ගාව හිටියේ තොපේ අමිමලාට ………….වනවා බයියලාගේ .මම ලංකාවට ඇවිත් තොට කන පැලෙන්න ගහනවා. මම සිසිර කුමාර... URL
  - [OFF] after:  මම හැරිසන් near හිටියේ තොපේ අමිමලාට ………….වනවා බයියලාගේ .මම ලංකාවට ඇවිත් තොට කන පැලෙන්න ගහනවා. මම සිසිර කුමාර... URL

### 3.44. `ගහෙන්` -> `tree`
- impact: 6 posts (3 light, 3 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඒකත්  හරියට ගහෙන් වැටුණු  මිනිහට  ගොනා  ඇන්න  වගෙයි
  - [NOT] after:  @USER ඒකත්  හරියට tree වැටුණු  මිනිහට  ගොනා  ඇන්න  වගෙයි
  - [NOT] before: ගහෙන් වැටුණ මිනිහට ගොනා අනිනවා වගේ වැඩක් තමයි ලෙඩ වුනාම බේත් බොන්න වෙන එකත්
  - [NOT] after:  tree වැටුණ මිනිහට ගොනා අනිනවා වගේ වැඩක් තමයි ලෙඩ වුනාම බේත් බොන්න වෙන එකත්
  - [NOT] before: @USER ගහෙන් වැටිලා ඉන්න මිනිහට කිරිවැස්සී  ඇන්නා වගේ..
  - [NOT] after:  @USER tree වැටිලා ඉන්න මිනිහට කිරිවැස්සී  ඇන්නා වගේ..

### 3.45. `එය` -> `it`
- impact: 6 posts (2 light, 4 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඔබ දුටු මුල් දා එදා. දැක්කේ අරකම තම. එය දැකලා, පක නැගලා. දුටුවා මුහුණත් එදා.
  - [OFF] after:  @USER ඔබ දුටු මුල් දා එදා. දැක්කේ අරකම තම. it දැකලා, පක නැගලා. දුටුවා මුහුණත් එදා.
  - [NOT] before: පයිය බිහි වීම.  පුරාණ රාවණ සෙල් ලිපි වලට අනුව රාවණ රජුගේ ලිංගය විශාල යන්ත්‍රයක් වැනිය.  පස් යොදුනක් දිග+ඉන්නක් වැනි+යන්ත්‍රය = පයිය  මේ සෙල්ලිපි අද්‍යනය කිරීමෙන් පසු අපට හැගී යන්නේ රාවණා රජුගේ ලිංගය අති විශාල වූවා පමණක් නොව එය සීතා වැනි ස්ත්‍රියකට කිසි සේත් දරා ගත නොහැකි බවයි.
  - [NOT] after:  පයිය බිහි වීම.  පුරාණ රාවණ සෙල් ලිපි වලට අනුව රාවණ රජුගේ ලිංගය විශාල යන්ත්‍රයක් වැනිය.  පස් යොදුනක් දිග+ඉන්නක් වැනි+යන්ත්‍රය = පයිය  මේ සෙල්ලිපි අද්‍යනය කිරීමෙන් පසු අපට හැගී යන්නේ රාවණා රජුගේ ලිංගය අති විශාල වූවා පමණක් නොව it සීතා වැනි ස්ත්‍රියකට කිසි සේත් දරා ගත නොහැකි බවයි.
  - [OFF] before: @USER ඔබ දුටු මුල් දා එදා. දැක්කේ අරකම තම. එය දැකලා, පක නැගලා. දුටුවා මුහුණත් එදා.
  - [OFF] after:  @USER ඔබ දුටු first දා එදා. දැක්කේ අරකම තම. it දැකලා, පක නැගලා. දුටුවා මුහුණත් එදා.

### 3.46. `ආය` -> `again`
- impact: 6 posts (3 light, 3 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හරි ඉතින් ආය.. ඕකට සාප කරන්නේ.. ගොනා
  - [NOT] after:  @USER හරි ඉතින් again.. ඕකට සාප කරන්නේ.. ගොනා
  - [NOT] before: මොන කරුමයක්ද ඕයී අපිට මේ වුනේ..ශැක් මේ වගේ කාලකණ්ණි කාලයක් ආය බලන්න වුනානේ
  - [NOT] after:  මොන කරුමයක්ද ඕයී අපිට මේ වුනේ..ශැක් මේ වගේ කාලකණ්ණි කාලයක් again බලන්න වුනානේ
  - [NOT] before: @USER ජය වෙිවා ,ආය කවුරුත් නැද්ද ,මමත් ඉල්ලන්න ඉන්නේ හිතුනොත් .
  - [NOT] after:  @USER ජය වෙිවා ,again කවුරුත් නැද්ද ,මමත් ඉල්ලන්න ඉන්නේ හිතුනොත් .

### 3.47. `උඩින්` -> `above`
- impact: 6 posts (3 light, 3 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මේකට උඩින් tweet එක දාපු එකා හරකා. යටින් දාපු එකා බූරුවා.
  - [OFF] after:  මේකට above tweet එක දාපු එකා හරකා. යටින් දාපු එකා බූරුවා.
  - [NOT] before: @USER ^ටහුඩු..!! මුං   @USER  දැං උඩින් යන්නේ නෙහ්..
  - [NOT] after:  @USER ^ටහුඩු..!! මුං   @USER  දැං above යන්නේ නෙහ්..
  - [NOT] before: කෙනෙක් නොදන්න  දෙයක් ඇහුවාම, දන්නේ නෑ කියලවත්, උඹට වඩා උඩින් යයි කියලා බයේ බාගෙටවත් දෙයක් කියලා දෙන්න එපා. කියලා දියන් උඹ  දන්න දේ උපරිමෙන්ම කවදා හරි උඹට පෙරලා කරපුව ලැබෙනවා හොදක් උනත් නරකක් උනත්
  - [NOT] after:  කෙනෙක් නොදන්න  දෙයක් ඇහුවාම, දන්නේ නෑ කියලවත්, උඹට වඩා above යයි කියලා බයේ බාගෙටවත් දෙයක් කියලා දෙන්න එපා. කියලා දියන් උඹ  දන්න දේ උපරිමෙන්ම කවදා හරි උඹට පෙරලා කරපුව ලැබෙනවා හොදක් උනත් නරකක් උනත්

### 3.48. `කොහේ` -> `where`
- impact: 6 posts (3 light, 3 heavy), 4 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කොහේ තරහ වෙන්නද උත්ටෝ. කරන්න අමාරු වැඩක් නෙවේ කරන්න බැරි වැඩක්...
  - [OFF] after:  where තරහ වෙන්නද උත්ටෝ. කරන්න අමාරු වැඩක් නෙවේ කරන්න බැරි වැඩක්...
  - [OFF] before: කොහේ තරහ වෙන්නද උත්ටෝ. කරන්න අමාරු වැඩක් නෙවේ කරන්න බැරි වැඩක්...
  - [OFF] after:  where angry වෙන්නද උත්ටෝ. කරන්න අමාරු වැඩක් නෙවේ කරන්න බැරි වැඩක්...
  - [OFF] before: Imagine... කිම්බ කිම්බ ඉජු ඉජු..මේ කිම්බ කොහේ ගිහින්ද මන්ද... Yare @USER  · 25 Dec 2018 Dad 5 years ago: no dogs!!   My dad now: Show this thread
  - [OFF] after:  Imagine... කිම්බ කිම්බ ඉජු ඉජු..මේ කිම්බ where ගිහින්ද මන්ද... Yare @USER  · 25 Dec 2018 Dad 5 years ago: no dogs!!   My dad now: Show this thread

### 3.49. `සත්තු` -> `animals`
- impact: 6 posts (3 light, 3 heavy), 6 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ගොං කියන්නෙ ගොනාට  බූරුවා .තඩි හරකා  සත්තු තුන්දෙනෙක් .එකට බ්ලෙන්ඩර් කරාම හැදෙන එකා
  - [OFF] after:  @USER ගොං කියන්නෙ ගොනාට  බූරුවා .තඩි හරකා  animals තුන්දෙනෙක් .එකට බ්ලෙන්ඩර් කරාම හැදෙන එකා
  - [OFF] before: මේ වේස පකයො රැස්වීම් තියන්න රතිඤ්ඤා පත්තු කරනවා.සත්තු පණ බයෙ දුවනවා.නද්දකින් ගොන් පක්කු.!
  - [OFF] after:  මේ වේස පකයො රැස්වීම් තියන්න රතිඤ්ඤා පත්තු කරනවා.animals පණ බයෙ දුවනවා.නද්දකින් ගොන් පක්කු.!
  - [OFF] before: @USER ගොං කියන්නෙ ගොනාට  බූරුවා .තඩි හරකා  සත්තු තුන්දෙනෙක් .එකට බ්ලෙන්ඩර් කරාම හැදෙන එකා
  - [OFF] after:  @USER ගොං කියන්නෙ ගොනාට  බූරුවා .තඩි හරකා  animals තුන්දෙනෙක් .එකට බ්ලෙන්ඩර් කරාම හැදෙන එකා

### 3.50. `ආයෙත්` -> `again`
- impact: 6 posts (3 light, 3 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඕවා අමතක වෙලා දැන්. ආයෙත් මතක් කරන්න වෙලා..
  - [NOT] after:  @USER ඕවා අමතක වෙලා දැන්. again මතක් කරන්න වෙලා..
  - [NOT] before: @USER එතකොට 11 මුලු රටම ආයෙත් කලින් වගේ අරිනව කියලද කියන්නෙ..?
  - [NOT] after:  @USER එතකොට 11 මුලු රටම again කලින් වගේ අරිනව කියලද කියන්නෙ..?
  - [NOT] before: @USER ආයෙත් අහලා.. ඒකි මැරිල නෑ
  - [NOT] after:  @USER again අහලා.. ඒකි මැරිල නෑ

### 3.51. `කවි` -> `poems`
- impact: 6 posts (3 light, 3 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හිතේ දුකට කවි සීපද කියවෙනවා
  - [NOT] after:  @USER හිතේ දුකට poems සීපද කියවෙනවා
  - [NOT] before: "කකුල් තද කොට බැඳෙමු - කැත හිත්වලට කවි !!" URL
  - [NOT] after:  "කකුල් තද කොට බැඳෙමු - කැත හිත්වලට poems !!" URL
  - [NOT] before: @USER හිතේ දුකට කවි සීපද කියවෙනවා
  - [NOT] after:  @USER හිතේ දුකට poems සීපද කියවෙනවා

### 3.52. `නමක්` -> `name`
- impact: 6 posts (3 light, 3 heavy), 4 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER නමක් නැද්ද මේ කරන අයගේ?
  - [NOT] after:  @USER name නැද්ද මේ කරන අයගේ?
  - [OFF] before: හුට්ටප්පරී හුච්චී හුක්කුච්චි හුජ්ජි හුමාලි හුංගාරි හුයන්නී හුත්තී හුකන්නී යම රජතුමා @USER  · 22 Nov 2019 පුලුවන් නම් "හු" අකුරෙන් පටන් ගන්න කෙල්ලෙක්ගෙ නමක් කියන්න.
  - [OFF] after:  හුට්ටප්පරී හුච්චී හුක්කුච්චි හුජ්ජි හුමාලි හුංගාරි හුයන්නී හුත්තී හුකන්නී යම රජතුමා @USER  · 22 Nov 2019 පුලුවන් නම් "හු" අකුරෙන් පටන් ගන්න කෙල්ලෙක්ගෙ name කියන්න.
  - [NOT] before: @USER නමක් නැද්ද මේ කරන අයගේ?
  - [NOT] after:  @USER name නැද්ද මේ කරන අයගේ?

### 3.53. `කෝමද` -> `how`
- impact: 6 posts (3 light, 3 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: තොපිට අගේ නෑ බොල   අමා කෝමද දැන්
  - [NOT] after:  තොපිට අගේ නෑ බොල   අමා how දැන්
  - [NOT] before: Awwwwww  I love this. පිටිපස්සෙන්  @USER  ඉන්න නිසා පොඩ්ඩක් කැත වෙලා. #ගයියා @USER  · 17 Dec 2017 අඩේ this is nice  Thankx @USER for the click. චූටි කෝමද මේක #TweetupSL
  - [NOT] after:  Awwwwww  I love this. පිටිපස්සෙන්  @USER  ඉන්න නිසා පොඩ්ඩක් කැත වෙලා. #ගයියා @USER  · 17 Dec 2017 අඩේ this is nice  Thankx @USER for the click. චූටි how මේක #TweetupSL
  - [NOT] before: තොපිට අගේ නෑ බොල   අමා කෝමද දැන්
  - [NOT] after:  තොපිට අගේ නෑ බොල   අමා how දැන්

### 3.54. `අහු` -> `caught`
- impact: 6 posts (3 light, 3 heavy), 4 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER අහු වෙයංකෝ තෝ පාරක්දි
  - [OFF] after:  @USER caught වෙයංකෝ තෝ පාරක්දි
  - [NOT] before: @USER මට iPhone එක ගෙනාවෙ නැතොත් මේ එකක්ට අහුවෙනඑක අහු වෙනවම තමයි. @USER
  - [NOT] after:  @USER මට iPhone එක ගෙනාවෙ නැතොත් මේ එකක්ට අහුවෙනඑක caught වෙනවම තමයි. @USER
  - [OFF] before: අපෝ හුත්ත අර වඳුරට දැලි පිහිය අහු උනා වගේ නේ යකෝ මේ හුකන්නලට Calls ගන්න Feature එක දීලා. මල වදේ දැන් Calls එනවා... URL
  - [OFF] after:  අපෝ හුත්ත අර වඳුරට දැලි පිහිය caught උනා වගේ නේ යකෝ මේ හුකන්නලට Calls ගන්න Feature එක දීලා. මල වදේ දැන් Calls එනවා... URL

### 3.55. `මුලු` -> `whole`
- impact: 6 posts (2 light, 4 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හිත් පිත් නැති කාලකන්නි ටිකක් නිසා මුලු ටුවිටරයම එපා විය   මනුස්සකමක් නැති කාලකන්නි ,සක්කිලි , නොදකින් මෙහෙව් උන්
  - [OFF] after:  හිත් පිත් නැති කාලකන්නි ටිකක් නිසා whole ටුවිටරයම එපා විය   මනුස්සකමක් නැති කාලකන්නි ,සක්කිලි , නොදකින් මෙහෙව් උන්
  - [NOT] before: කොනටයි ,පහලටයි යන්න ගිහිං තොපි දෙන්නා හදන්නේ මුලු රවුම් කරගන්න  @USER  &  @USER  2
  - [NOT] after:  කොනටයි ,පහලටයි යන්න ගිහිං තොපි දෙන්නා හදන්නේ whole රවුම් කරගන්න  @USER  &  @USER  2
  - [OFF] before: හිත් පිත් නැති කාලකන්නි ටිකක් නිසා මුලු ටුවිටරයම එපා විය   මනුස්සකමක් නැති කාලකන්නි ,සක්කිලි , නොදකින් මෙහෙව් උන්
  - [OFF] after:  heart පිත් නැති කාලකන්නි ටිකක් නිසා whole ටුවිටරයම එපා විය   මනුස්සකමක් නැති කාලකන්නි ,සක්කිලි , නොදකින් මෙහෙව් උන්

### 3.56. `ලග` -> `near`
- impact: 6 posts (3 light, 3 heavy), 2 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හෑ මං දැක්කේ සාය වගේ  ඔව් ඔව් ගුරුමුට්ටිය නෑ මං ලග ඒක බිදුනා අම්බලමේ පිනාගෙ ගොනා ඇනලා
  - [NOT] after:  @USER හෑ මං දැක්කේ සාය වගේ  ඔව් ඔව් ගුරුමුට්ටිය නෑ මං near ඒක බිදුනා අම්බලමේ පිනාගෙ ගොනා ඇනලා
  - [NOT] before: @USER උඹ ලග නැති උනාට බැසිල් ලග තියෙනව.
  - [NOT] after:  @USER උඹ near නැති උනාට බැසිල් near තියෙනව.
  - [OFF] before: @USER  @USER    බිජ්ජෝ තොට දෙන්න මගෙ ලග empty bottle  එකකුත් තියාගන ඉන්නේ .
  - [OFF] after:  @USER  @USER    බිජ්ජෝ තොට දෙන්න මගෙ near empty bottle  එකකුත් තියාගන ඉන්නේ .

### 3.57. `විතරද` -> `only`
- impact: 6 posts (2 light, 4 heavy), 6 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER   ක් විතරද පිරිමි, තූ නොදකින්
  - [OFF] after:  @USER   ක් only පිරිමි, තූ නොදකින්
  - [OFF] before: @USER රෙන කං කියල කියෙව්වෙ මං විතරද දන්නෑ?
  - [OFF] after:  @USER රෙන කං කියල කියෙව්වෙ මං only දන්නෑ?
  - [OFF] before: @USER   ක් විතරද පිරිමි, තූ නොදකින්
  - [OFF] after:  @USER   ක් only men, තූ නොදකින්

### 3.58. `ඉතුරු` -> `remaining`
- impact: 6 posts (2 light, 4 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ටහුඩු ඒමත් එකක්ද ??  @USER  අඩෝ ඉන්දිකයා මම ටෝව ඉතුරු කරම්නෑ
  - [NOT] after:  @USER ටහුඩු ඒමත් එකක්ද ??  @USER  අඩෝ ඉන්දිකයා මම ටෝව remaining කරම්නෑ
  - [NOT] before: @USER උන්ගේ අම්මලා තාත්තලා මෝඩ නං අපි මෙහේ ඉතුරු වෙද්දී උන්ව එහෙ යවයිද
  - [NOT] after:  @USER උන්ගේ අම්මලා තාත්තලා මෝඩ නං අපි මෙහේ remaining වෙද්දී උන්ව එහෙ යවයිද
  - [NOT] before: @USER ටහුඩු ඒමත් එකක්ද ??  @USER  අඩෝ ඉන්දිකයා මම ටෝව ඉතුරු කරම්නෑ
  - [NOT] after:  @USER ටහුඩු ඒමත් එකක්ද ??  @USER  අඩෝ ඉන්දිකයා මම ටෝව remaining කරම්නෑ

### 3.59. `වැස්ස` -> `rain`
- impact: 6 posts (3 light, 3 heavy), 0 of them labelled OFF, 8 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: වැස්ස සීතල  මතක  උඹ.. #witch
  - [NOT] after:  rain සීතල  මතක  උඹ.. #witch
  - [NOT] before: අනුරාධපුරේ ට පෑව්වත් අප්පිරියයි වැස්සත් අප්පිරියයි . වැස්ස නං ඉතින් යලට එකයි මහට එකයි නේ...  #mosthatedcity #කරුම
  - [NOT] after:  අනුරාධපුරේ ට පෑව්වත් අප්පිරියයි වැස්සත් අප්පිරියයි . rain නං ඉතින් යලට එකයි මහට එකයි නේ...  #mosthatedcity #කරුම
  - [NOT] before: @USER වැස්ස නිසා හොඳට ගියා..
  - [NOT] after:  @USER rain නිසා හොඳට ගියා..

### 3.60. `එක්කෝ` -> `either`
- impact: 6 posts (3 light, 3 heavy), 4 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ටහුඩු අද #internationaldayofthegirl ද? අද දවසම .... එක්කෝ ඕනේ නෑ...
  - [NOT] after:  ටහුඩු අද #internationaldayofthegirl ද? අද දවසම .... either ඕනේ නෑ...
  - [OFF] before: බෑ ඕයි එක්කෝ එන වෙලාවක එයිනේ...රෙද්ද....
  - [OFF] after:  බෑ ඕයි either එන වෙලාවක එයිනේ...රෙද්ද....
  - [OFF] before: @USER  @USER ඒක පැහැදිලිව දාපන් එක්කෝ වරහන් වල   තෝ AL fail ම වෙන්න ඕන ගොං බූතයා
  - [OFF] after:  @USER  @USER ඒක පැහැදිලිව දාපන් either වරහන් වල   තෝ AL fail ම වෙන්න ඕන ගොං බූතයා

### 3.61. `බඩු` -> `stuff`
- impact: 5 posts (2 light, 3 heavy), 4 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හුකහන් පකෝ. තොටත් එක්ක බඩු ගත්තහම ඔච්චර කියලත් ආවෙ නෑ
  - [OFF] after:  හුකහන් පකෝ. තොටත් එක්ක stuff ගත්තහම ඔච්චර කියලත් ආවෙ නෑ
  - [OFF] before: @USER අයිසෙ ස්ලෑස්, තමුසෙ තායි බඩු ගහද්දි අපිට මසා එකක්වත් සෙට්කරනවකො  @USER
  - [OFF] after:  @USER අයිසෙ ස්ලෑස්, තමුසෙ තායි stuff ගහද්දි අපිට මසා එකක්වත් සෙට්කරනවකො  @USER
  - [OFF] before: හුකහන් පකෝ. තොටත් එක්ක බඩු ගත්තහම ඔච්චර කියලත් ආවෙ නෑ
  - [OFF] after:  හුකහන් පකෝ. තොටත් එක්ක stuff ගත්තහම ඔච්චර කියලත් ආවෙ නෑ

### 3.62. `කෙල්ලෙ` -> `girl`
- impact: 5 posts (2 light, 3 heavy), 5 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER අනේ පලයන් කෙල්ලෙ යන්න
  - [OFF] after:  @USER අනේ පලයන් girl යන්න
  - [OFF] before: @USER අනේ පලයන් කෙල්ලෙ යන්න
  - [OFF] after:  @USER අනේ පලයන් girl යන්න
  - [OFF] before: @USER  අඩෝ තොට සුභ මෙව්වා එකක් වේවා කෙල්ලෙ
  - [OFF] after:  @USER  අඩෝ තොට සුභ මෙව්වා එකක් වේවා girl

### 3.63. `උපන්` -> `born`
- impact: 5 posts (2 light, 3 heavy), 3 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: උපන් කැත යවන්න බෑ කිව්වවට youcam perfect  එකෙන් ඒකත් පුලුවන් බන්..
  - [NOT] after:  born කැත යවන්න බෑ කිව්වවට youcam perfect  එකෙන් ඒකත් පුලුවන් බන්..
  - [NOT] before: උපන් කැත යවන්න බෑ කිව්වවට youcam perfect  එකෙන් ඒකත් පුලුවන් බන්..
  - [NOT] after:  born කැත send බෑ කිව්වවට youcam perfect  එකෙන් ඒකත් පුලුවන් බන්..
  - [OFF] before: @USER තූ නොදකින් මූ වගේ ගොන් කතා කියන එකෙක් ආතල් දෙන්න උපන් එකෙක් වෙන නෑ අක්කේ..
  - [OFF] after:  @USER තූ නොදකින් මූ වගේ ගොන් talk කියන එකෙක් ආතල් දෙන්න born එකෙක් වෙන නෑ අක්කේ..

### 3.64. `ඉස්සරහට` -> `forward`
- impact: 5 posts (2 light, 3 heavy), 0 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මං එයාගේ ඉස්සරහට වඩා පස්ස දැකලා තින්නේ
  - [NOT] after:  මං එයාගේ forward වඩා පස්ස දැකලා තින්නේ
  - [NOT] before: ටහුඩු ඒ කියන්නෙ මගෙ කඩ්ඩ පොලිශ් වෙනවා ඉස්සරහට  සුලා @USER  · 24 Jan 2019 ජෙරියගේ අනාගත කාල SS එකක් හම්බුණා ප්‍රෙන්ස්..  @USER
  - [NOT] after:  ටහුඩු ඒ කියන්නෙ මගෙ English පොලිශ් වෙනවා forward  සුලා @USER  · 24 Jan 2019 ජෙරියගේ අනාගත කාල SS එකක් හම්බුණා ප්‍රෙන්ස්..  @USER
  - [NOT] before: මං එයාගේ ඉස්සරහට වඩා පස්ස දැකලා තින්නේ
  - [NOT] after:  මං එයාගේ forward වඩා පස්ස දැකලා තින්නේ

### 3.65. `ජය` -> `victory`
- impact: 5 posts (2 light, 3 heavy), 2 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER රටම බලන් ඉන්නේ එකම ගලවුම් කරුවානනි ඔනට ජය
  - [NOT] after:  @USER රටම බලන් ඉන්නේ එකම ගලවුම් කරුවානනි ඔනට victory
  - [OFF] before: @USER  @USER    පක තමයි ජය ගන්නෙ. අනේ හුත්තිගෙ පකයෝ හැමිනෙන්නෙ නැතුව හිටපන්.
  - [OFF] after:  @USER  @USER    පක තමයි victory ගන්නෙ. අනේ හුත්තිගෙ පකයෝ හැමිනෙන්නෙ නැතුව හිටපන්.
  - [NOT] before: @USER රටම බලන් ඉන්නේ එකම ගලවුම් කරුවානනි ඔනට ජය
  - [NOT] after:  @USER රටම බලන් ඉන්නේ එකම ගලවුම් කරුවානනි ඔනට victory

### 3.66. `පැය` -> `hour`
- impact: 5 posts (1 light, 4 heavy), 3 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අනිත් එවුන් පැයෙන් එන දුර අර පරට්ට ඩ්‍රයිවර් කාරයා පැය දෙකක් ආවනේ ටෞකන්ඩ!
  - [OFF] after:  අනිත් එවුන් පැයෙන් එන දුර අර පරට්ට ඩ්‍රයිවර් කාරයා hour දෙකක් ආවනේ ටෞකන්ඩ!
  - [NOT] before: @USER All the best ස'. පැය 11-12ක ෆ්ලයිට් එකක නාකි පප්පලා දෙන්නෙක් යනවා ඩිප්ලොමැටික් දේවල් කතා කරන්න.
  - [NOT] after:  @USER All the best ස'. hour 11-12ක ෆ්ලයිට් එකක නාකි පප්පලා දෙන්නෙක් යනවා ඩිප්ලොමැටික් දේවල් talk කරන්න.
  - [OFF] before: අනිත් එවුන් පැයෙන් එන දුර අර පරට්ට ඩ්‍රයිවර් කාරයා පැය දෙකක් ආවනේ ටෞකන්ඩ!
  - [OFF] after:  other එවුන් පැයෙන් එන දුර අර පරට්ට ඩ්‍රයිවර් කාරයා hour දෙකක් ආවනේ ටෞකන්ඩ!

### 3.67. `කොහෙ` -> `where`
- impact: 5 posts (2 light, 3 heavy), 3 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මිතුරෙක් - බලහං කඩවත ඉඳං මාතරට එනකං එක දංසලක් නෑනේ... 2මිතුරා - හයිවේ එකේ කොහෙ දන්සල්ද? පකෝ... #සිරාසිද්ධි
  - [OFF] after:  මිතුරෙක් - බලහං කඩවත ඉඳං මාතරට එනකං එක දංසලක් නෑනේ... 2මිතුරා - හයිවේ එකේ where දන්සල්ද? පකෝ... #සිරාසිද්ධි
  - [OFF] before: මිතුරෙක් - බලහං කඩවත ඉඳං මාතරට එනකං එක දංසලක් නෑනේ... 2මිතුරා - හයිවේ එකේ කොහෙ දන්සල්ද? පකෝ... #සිරාසිද්ධි
  - [OFF] after:  මිතුරෙක් - බලහං කඩවත from මාතරට එනකං එක දංසලක් නෑනේ... 2මිතුරා - හයිවේ එකේ where දන්සල්ද? පකෝ... #සිරාසිද්ධි
  - [OFF] before: වේසියෙක් "වේසියෙක්" වෙන්නෙ කොහෙ හරි ඉන්න වනචර වලත්ත වේසෙක් නිසා.  වේසියන්ට "වේසි" කියනවා නම් වේසොන්ට "වේසා" කියලත් කියපන්!  ඒත් එහෙම කියන්නෙ නෑ නේද?  ඇයි ඒ?  අනුන්ගෙ වේසකම් නෙමේ තමන්ගෙ වේසකම් හොයාගනිල්ලා!  ගතින් කළත් නොකළත් හිතින් කරපු වේසකම් තේරුම් ගනිල්ලා!  #Life #SriLanka #LKA
  - [OFF] after:  වේසියෙක් "වේසියෙක්" වෙන්නෙ where හරි ඉන්න වනචර වලත්ත වේසෙක් නිසා.  වේසියන්ට "වේසි" කියනවා නම් වේසොන්ට "වේසා" කියලත් කියපන්!  ඒත් එහෙම කියන්නෙ නෑ නේද?  ඇයි ඒ?  අනුන්ගෙ වේසකම් නෙමේ තමන්ගෙ වේසකම් හොයාගනිල්ලා!  ගතින් කළත් නොකළත් හිතින් කරපු වේසකම් understand ගනිල්ලා!  #Life #SriLanka #LKA

### 3.68. `වහ` -> `poison`
- impact: 5 posts (2 light, 3 heavy), 2 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER දැං අපේ උන්ගෙ ඇස් වහ කට වහ වැදිලා හෙට වෙන කොට ඔකටත් කෙලවෙයි
  - [NOT] after:  @USER දැං අපේ උන්ගෙ ඇස් poison කට poison වැදිලා හෙට වෙන කොට ඔකටත් කෙලවෙයි
  - [NOT] before: @USER වහ ඉල්ලා උද්ගොශනය කරා නේද පහුගිය කාලේ.
  - [NOT] after:  @USER poison ඉල්ලා උද්ගොශනය කරා නේද last කාලේ.
  - [NOT] before: @USER දැං අපේ උන්ගෙ ඇස් වහ කට වහ වැදිලා හෙට වෙන කොට ඔකටත් කෙලවෙයි
  - [NOT] after:  @USER දැං අපේ උන්ගෙ ඇස් poison කට poison වැදිලා හෙට වෙන කොට ඔකටත් කෙලවෙයි

### 3.69. `ඉක්මනට` -> `quickly`
- impact: 5 posts (2 light, 3 heavy), 5 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මල්සරො විදිනවානම් විදපන් ඉක්මනට නැත්‍තන් පල යන්ට මුසලයා
  - [OFF] after:  මල්සරො විදිනවානම් විදපන් quickly නැත්‍තන් පල යන්ට මුසලයා
  - [OFF] before: මල්සරො විදිනවානම් විදපන් ඉක්මනට නැත්‍තන් පල යන්ට මුසලයා
  - [OFF] after:  මල්සරො විදිනවානම් විදපන් quickly නැත්‍තන් පල යන්ට මුසලයා
  - [OFF] before: අනේ බාබරයෝ, ඉක්මනට Nimalkaගේ කොන්ඩේ කපහං..  උඹේ සාප්පුවේ දාලා තියෙන මේ ආදරයයි ඇහෙන කොට වමනෙට එනවා යකෝ — feeling... URL
  - [OFF] after:  අනේ බාබරයෝ, quickly Nimalkaගේ hair කපහං..  උඹේ සාප්පුවේ දාලා තියෙන මේ ආදරයයි ඇහෙන කොට වමනෙට එනවා යකෝ — feeling... URL

### 3.70. `සෑම` -> `every`
- impact: 5 posts (2 light, 3 heavy), 1 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සෑම Campus එකකම ඉන්න බල්ලන් ලවා ජාතක උනු පොන්න හැත්ත... මේවගේ උන් ගන්න  නැතුව ඉන්න ඔනේ
  - [OFF] after:  every Campus එකකම ඉන්න dogs ලවා ජාතක උනු පොන්න හැත්ත... මේවගේ උන් ගන්න  නැතුව ඉන්න ඔනේ
  - [NOT] before: @USER මැතිවරණයක් පවත්තන සෑම අවස්ථාවකම තාජිඩීන් ගොඩ දාපු උදවිය නාහින් අඩනවා සන්දීප්  සම්පත් විකුනන් දේසපාලන පලි ගන්නවලු.. මේවට කොහොම හිනාවෙන්නද මන්දා..
  - [NOT] after:  @USER මැතිවරණයක් පවත්තන every අවස්ථාවකම තාජිඩීන් ගොඩ දාපු උදවිය නාහින් අඩනවා සන්දීප්  සම්පත් විකුනන් දේසපාලන පලි ගන්නවලු.. මේවට කොහොම හිනාවෙන්නද මන්දා..
  - [NOT] before: @USER තමන් විසින් තමන් වනා ගැනීම .... සෑම විපතක් අවසානයේම තමන් උත්කර්ෂයට නැගීම .. ඔබට සහතික මිනිසුන් දෙවි..බලෙන් ලබා ගැනීමට යෑම බොරදියේ මාළු බැමකි
  - [NOT] after:  @USER තමන් විසින් තමන් වනා ගැනීම .... every විපතක් අවසානයේම තමන් උත්කර්ෂයට නැගීම .. ඔබට සහතික මිනිසුන් දෙවි..බලෙන් ලබා ගැනීමට යෑම බොරදියේ මාළු බැමකි

### 3.71. `ඊයේ` -> `yesterday`
- impact: 5 posts (2 light, 3 heavy), 0 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ,  @USER  @USER අද මන් ගත්ත තැනත් ඊයේ හවස ඇවිත් තියෙන්නේ කොට්ට පනහයී මන් යද්දී තිබ්බේ හයයී, සිමෙන්තී වැඩි දවසක් තියා ගන්නත් අමාරු නිසා හන්ගනවා කියන්න බෑ
  - [NOT] after:  @USER ,  @USER  @USER අද මන් ගත්ත තැනත් yesterday හවස ඇවිත් තියෙන්නේ කොට්ට පනහයී මන් යද්දී තිබ්බේ හයයී, සිමෙන්තී වැඩි දවසක් තියා ගන්නත් අමාරු නිසා හන්ගනවා කියන්න බෑ
  - [NOT] before: @USER ,  @USER  @USER අද මන් ගත්ත තැනත් ඊයේ හවස ඇවිත් තියෙන්නේ කොට්ට පනහයී මන් යද්දී තිබ්බේ හයයී, සිමෙන්තී වැඩි දවසක් තියා ගන්නත් අමාරු නිසා හන්ගනවා කියන්න බෑ
  - [NOT] after:  @USER ,  @USER  @USER අද මන් ගත්ත place yesterday හවස ඇවිත් තියෙන්නේ කොට්ට පනහයී මන් යද්දී තිබ්බේ හයයී, සිමෙන්තී වැඩි දවසක් තියා ගන්නත් අමාරු නිසා හන්ගනවා කියන්න බෑ
  - [NOT] before: ගෙම්බා අද සද්දයක් නැත්තෙ මොකෝ කියලා බැලුවා.. ටහුඩු ඉන්දියවට වඩාගෙන ගහලා ඊයේ
  - [NOT] after:  frog අද සද්දයක් නැත්තෙ මොකෝ කියලා බැලුවා.. ටහුඩු ඉන්දියවට වඩාගෙන ගහලා yesterday

### 3.72. `අපිව` -> `us`
- impact: 5 posts (2 light, 3 heavy), 5 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: පුතේ නාකි සීයට කියන්න අපිව නයකරා ඇති කියල!  Gotabaya Rajapaksa @USER  · 4 Oct 2021 Meeting my granddaughter Dulanya for the first time.
  - [OFF] after:  පුතේ නාකි සීයට කියන්න us නයකරා ඇති කියල!  Gotabaya Rajapaksa @USER  · 4 Oct 2021 Meeting my granddaughter Dulanya for the first time.
  - [OFF] before: නොදකිං මේ වගේ එලොවටත් නැති මෙලොවටත් නැති පොන්න පකයො නම්   PS : බයට නෙවේ SS දැම්මෙ quote කරන්න බෑ අපිව blocked
  - [OFF] after:  නොදකිං මේ වගේ එලොවටත් නැති මෙලොවටත් නැති පොන්න පකයො නම්   PS : බයට නෙවේ SS දැම්මෙ quote කරන්න බෑ us blocked
  - [OFF] before: කුසල් මෙන්ඩිස්! මේ වේසි අපිව කෑවා!!
  - [OFF] after:  කුසල් Mendis! මේ වේසි us කෑවා!!

### 3.73. `නුවන්` -> `eyes`
- impact: 5 posts (2 light, 3 heavy), 0 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: උපුල් නුවන් විදහා ඔබ සිනාසුනා මම ගොනා උනා  #රතුමකරාFM
  - [NOT] after:  උපුල් eyes විදහා ඔබ සිනාසුනා මම ගොනා උනා  #රතුමකරාFM
  - [NOT] before: උපුල් නුවන් විදහා ඔබ ගොනා උනා  මම සිනා සුනා
  - [NOT] after:  උපුල් eyes විදහා ඔබ ගොනා උනා  මම සිනා සුනා
  - [NOT] before: උපුල් නුවන් විදහා ඔබ සිනාසුනා මම ගොනා උනා  #රතුමකරාFM
  - [NOT] after:  උපුල් eyes විදහා ඔබ සිනාසුනා මම ගොනා උනා  #රතුමකරාFM

### 3.74. `හාල්` -> `rice`
- impact: 5 posts (1 light, 4 heavy), 3 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER තොට දෙයියන්ගෙ හාල් කැවිලද?
  - [OFF] after:  @USER තොට දෙයියන්ගෙ rice කැවිලද?
  - [OFF] before: @USER තොට දෙයියන්ගෙ හාල් කැවිලද?
  - [OFF] after:  @USER තොට දෙයියන්ගෙ rice කැවිලද?
  - [NOT] before: @USER මෙච්චර කල් රාජපක්ෂලට හාල් ගරලා දැන් බයිලා කියෝනවා.
  - [NOT] after:  @USER මෙච්චර කල් රාජපක්ෂලට rice ගරලා දැන් baila කියෝනවා.

### 3.75. `අනික්` -> `other`
- impact: 5 posts (2 light, 3 heavy), 4 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මාත් නංගිගේ බබාට පිටකොටුවේ නීරෝ සීඩි හවුස් එකෙන් කාටුන් වගෑක් ගෙනිච්චා.. තූ නොදකින්..කොලිටි සෑහෙන අඩුයි..ඉන් පස්සේ දැන් පෙන් එකකටවත් දාල දෙන්න ඕනි.. ඒත් පෙන් එකක් දෙන්න බැහැ අනික් අයිය බුවාල ආවම උන්ගේ වැල එහෙ මෙහෙ ගෙනියන්න ඒක ගන්නවා.
  - [OFF] after:  @USER මාත් නංගිගේ බබාට පිටකොටුවේ නීරෝ සීඩි හවුස් එකෙන් කාටුන් වගෑක් ගෙනිච්චා.. තූ නොදකින්..කොලිටි සෑහෙන අඩුයි..ඉන් පස්සේ දැන් පෙන් එකකටවත් දාල දෙන්න ඕනි.. ඒත් පෙන් එකක් දෙන්න බැහැ other අයිය බුවාල ආවම උන්ගේ වැල එහෙ මෙහෙ ගෙනියන්න ඒක ගන්නවා.
  - [OFF] before: @USER ඒ කියන්නේ ගෑනු කිව්වොත් මේ පුක කහනවා කියලා..කහන්නේ පුක නෙමෙයි අනික් පැත්තද?  දන් නැති නිසයි ඇහුවේ ඉතිං..
  - [OFF] after:  @USER ඒ කියන්නේ ගෑනු කිව්වොත් මේ පුක කහනවා කියලා..කහන්නේ පුක නෙමෙයි other පැත්තද?  දන් නැති නිසයි ඇහුවේ ඉතිං..
  - [OFF] before: @USER මාත් නංගිගේ බබාට පිටකොටුවේ නීරෝ සීඩි හවුස් එකෙන් කාටුන් වගෑක් ගෙනිච්චා.. තූ නොදකින්..කොලිටි සෑහෙන අඩුයි..ඉන් පස්සේ දැන් පෙන් එකකටවත් දාල දෙන්න ඕනි.. ඒත් පෙන් එකක් දෙන්න බැහැ අනික් අයිය බුවාල ආවම උන්ගේ වැල එහෙ මෙහෙ ගෙනියන්න ඒක ගන්නවා.
  - [OFF] after:  @USER මාත් නංගිගේ බබාට පිටකොටුවේ නීරෝ සීඩි හවුස් එකෙන් කාටුන් වගෑක් ගෙනිච්චා.. තූ නොදකින්..කොලිටි සෑහෙන අඩුයි..ඉන් පස්සේ දැන් පෙන් එකකටවත් දාල දෙන්න ඕනි.. ඒත් පෙන් එකක් දෙන්න බැහැ other brother බුවාල ආවම උන්ගේ වැල එහෙ මෙහෙ ගෙනියන්න ඒක ගන්නවා.

### 3.76. `ජනතාවට` -> `public එකට`
- impact: 5 posts (2 light, 3 heavy), 2 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ජනතාවට බුදුසරණයි දෙවි පිහිටයි
  - [NOT] after:  @USER public එකට බුදුසරණයි දෙවි පිහිටයි
  - [NOT] before: @USER කවදාද දන්නේ නැහැ සහනේ ජනතාවට ලැබෙන්නේ ?
  - [NOT] after:  @USER when දන්නේ නැහැ සහනේ public එකට ලැබෙන්නේ ?
  - [NOT] before: @USER ජනතාවට බුදුසරණයි දෙවි පිහිටයි
  - [NOT] after:  @USER public එකට බුදුසරණයි god පිහිටයි

### 3.77. `චූටි` -> `small`
- impact: 5 posts (2 light, 3 heavy), 4 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER කිම්බ අස්සේ රිංගන්න එපා.. චූටි මීයොන්ට ඉඩ නැ
  - [OFF] after:  @USER  @USER කිම්බ අස්සේ රිංගන්න එපා.. small මීයොන්ට ඉඩ නැ
  - [OFF] before: @USER උගේ පුක චූටි නිසා ඒ නම තිබ්බේ
  - [OFF] after:  @USER උගේ පුක small නිසා ඒ නම තිබ්බේ
  - [OFF] before: @USER  @USER කිම්බ අස්සේ රිංගන්න එපා.. චූටි මීයොන්ට ඉඩ නැ
  - [OFF] after:  @USER  @USER කිම්බ inside රිංගන්න එපා.. small මීයොන්ට ඉඩ නැ

### 3.78. `දෙවි` -> `god`
- impact: 5 posts (2 light, 3 heavy), 2 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සඝ රජුට කල මෙී අපරාධයට සම්බන්ධ සියල්ලන්ටම සාප වෙීවා..... සියලු දෙවි දේවතාවන් උන්ට සාප කරත්වා..... සියලු දෙනා එක හිතින් ප්‍රාර්ථනා කරන්න....
  - [OFF] after:  සඝ රජුට කල මෙී අපරාධයට සම්බන්ධ සියල්ලන්ටම සාප වෙීවා..... සියලු god දේවතාවන් උන්ට සාප කරත්වා..... සියලු දෙනා එක හිතින් ප්‍රාර්ථනා කරන්න....
  - [NOT] before: @USER ජනතාවට බුදුසරණයි දෙවි පිහිටයි
  - [NOT] after:  @USER public එකට බුදුසරණයි god පිහිටයි
  - [OFF] before: සඝ රජුට කල මෙී අපරාධයට සම්බන්ධ සියල්ලන්ටම සාප වෙීවා..... සියලු දෙවි දේවතාවන් උන්ට සාප කරත්වා..... සියලු දෙනා එක හිතින් ප්‍රාර්ථනා කරන්න....
  - [OFF] after:  සඝ රජුට කල මෙී අපරාධයට සම්බන්ධ සියල්ලන්ටම සාප වෙීවා..... සියලු god දේවතාවන් උන්ට සාප කරත්වා..... සියලු people එක හිතින් ප්‍රාර්ථනා කරන්න....

### 3.79. `අලි` -> `elephants`
- impact: 5 posts (2 light, 3 heavy), 3 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අලි නාවන තඩි වල වල් TL එකේ ඇති බැවින් තමාගෙ ආරක්ශාව තමන් සලසගන්න..!
  - [NOT] after:  elephants නාවන තඩි වල වල් TL එකේ ඇති බැවින් තමාගෙ ආරක්ශාව තමන් සලසගන්න..!
  - [OFF] before: @USER හබරල කොල හිල් වෙන්න හුජ්ජ කරන්න ඉතින් අලි පයියක් වෙන්න ඕනේ
  - [OFF] after:  @USER හබරල leaf හිල් වෙන්න හුජ්ජ කරන්න ඉතින් elephants පයියක් වෙන්න ඕනේ
  - [NOT] before: අලි නාවන තඩි වල වල් TL එකේ ඇති බැවින් තමාගෙ ආරක්ශාව තමන් සලසගන්න..!
  - [NOT] after:  elephants නාවන තඩි වල වල් TL එකේ ඇති since තමාගෙ ආරක්ශාව තමන් සලසගන්න..!

### 3.80. `ගති` -> `nature`
- impact: 5 posts (2 light, 3 heavy), 2 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: බල්ලා ගැන ශෝකයෙන් මැරී බලු ගති ඇති ප්‍රේතයකුව URL
  - [NOT] after:  බල්ලා ගැන ශෝකයෙන් මැරී බලු nature ඇති ප්‍රේතයකුව URL
  - [OFF] before: අනුරගෙ සට්ටැඹියන්ගෙ ඉත්තෑවො දුඑඅන එක අහන්නදෙයක්ද  තව බැනපල්ල ට්ගව මඩගහපල්ල  උඹලගෙ සක්කිලි පර ගති ලෝකෙටම පෙන්නපල්ල.   %ට ඇදල දැම්මෙත් මේකෙ ඇමනෙන සිප්පිකටු
  - [OFF] after:  අනුරගෙ සට්ටැඹියන්ගෙ ඉත්තෑවො දුඑඅන එක අහන්නදෙයක්ද  තව බැනපල්ල ට්ගව මඩගහපල්ල  උඹලගෙ සක්කිලි පර nature ලෝකෙටම පෙන්නපල්ල.   %ට ඇදල දැම්මෙත් මේකෙ ඇමනෙන සිප්පිකටු
  - [NOT] before: බල්ලා ගැන ශෝකයෙන් මැරී බලු ගති ඇති ප්‍රේතයකුව URL
  - [NOT] after:  dog ගැන ශෝකයෙන් මැරී බලු nature ඇති ප්‍රේතයකුව URL

### 3.81. `ඇහුවා` -> `asked`
- impact: 5 posts (2 light, 3 heavy), 1 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මම චනදෘ ගෙන් ඇහුවා උඹ හිතන්නේ මොන භාෂාවෙන්ද කියලා ඌ මට කිව්වා "මම සිංහලෙන් හිතන්නේ ඒත් අමාරු දේවල් දෙමලෙන් හිතන්නේ "කියලා
  - [NOT] after:  මම චනදෘ ගෙන් asked උඹ හිතන්නේ මොන භාෂාවෙන්ද කියලා ඌ මට කිව්වා "මම සිංහලෙන් හිතන්නේ ඒත් අමාරු දේවල් දෙමලෙන් හිතන්නේ "කියලා
  - [NOT] before: @USER @USER  හරි දැං මගෙන් තමුසෙ ඇහුවා කියලා දැම්මේ නෑනේ :V
  - [NOT] after:  @USER @USER  හරි දැං මගෙන් තමුසෙ asked කියලා දැම්මේ නෑනේ :V
  - [OFF] before: නිරෝදායනයට යන්න එනවද කියලා මීනාක්ශිගෙන් ඇහුවා එන්න බෑලු   + එහෙනම් උඹ එන්නෑ - නැහැ +පරට්ටි !  #ගුහාසටනපොකුර
  - [OFF] after:  නිරෝදායනයට යන්න එනවද කියලා මීනාක්ශිගෙන් asked come බෑලු   + එහෙනම් උඹ එන්නෑ - නැහැ +පරට්ටි !  #ගුහාසටනපොකුර

### 3.82. `තරහ` -> `angry`
- impact: 5 posts (2 light, 3 heavy), 3 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කොහෙවත් යන ගොන් ලොංත කාලකන්නි කැරි බල්ලෙක් මල පැන්නුව. ශැක්. දැන් කන පැලෙන්න ගහනකන් තරහ නිවෙන්නෙ නෑ.
  - [OFF] after:  කොහෙවත් යන ගොන් ලොංත කාලකන්නි කැරි බල්ලෙක් මල පැන්නුව. ශැක්. දැන් කන පැලෙන්න ගහනකන් angry නිවෙන්නෙ නෑ.
  - [NOT] before: @USER @USER  @USER අන්න තරා ගියා. දැක්කනෙ. නාකි වෙනකොට තරහ යනව කියල මං අහල තියනව.
  - [NOT] after:  @USER @USER  @USER අන්න තරා ගියා. දැක්කනෙ. නාකි වෙනකොට angry යනව කියල මං අහල තියනව.
  - [OFF] before: කොහේ තරහ වෙන්නද උත්ටෝ. කරන්න අමාරු වැඩක් නෙවේ කරන්න බැරි වැඩක්...
  - [OFF] after:  where angry වෙන්නද උත්ටෝ. කරන්න අමාරු වැඩක් නෙවේ කරන්න බැරි වැඩක්...

### 3.83. `හොදේ` -> `ok`
- impact: 5 posts (2 light, 3 heavy), 2 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අම්මෝහ් මාව හරි පාරේ එක්කන් පලයන් හොදේ ජී Kaushalya Jee  URL
  - [NOT] after:  අම්මෝහ් මාව හරි පාරේ එක්කන් පලයන් ok ජී Kaushalya Jee  URL
  - [NOT] before: අම්මෝහ් මාව හරි පාරේ එක්කන් පලයන් හොදේ ජී Kaushalya Jee  URL
  - [NOT] after:  අම්මෝහ් මාව හරි road එකේ එක්කන් පලයන් ok ජී Kaushalya Jee  URL
  - [NOT] before: දැන් ඉතින් තියෙන්නේ හරකාට වෙලාවට කන්න බොන දෙන එක විතරයි.නැත්නම් හරකා අහල පහල වතුවලට පැනලා වගා හානි කරන්න ඉඩ තියෙනවා.ඒ වගේම තමයි පොඩි අය මේවා තනියම හදන්න යන්නෙපා..අම්මලා තාත්තලා පොඩි අයට මේවා හදලා දෙන්න හොදේ.
  - [NOT] after:  දැන් ඉතින් තියෙන්නේ හරකාට වෙලාවට කන්න බොන දෙන එක විතරයි.නැත්නම් හරකා අහල පහල වතුවලට පැනලා cultivate හානි කරන්න ඉඩ තියෙනවා.ඒ වගේම තමයි පොඩි අය මේවා තනියම හදන්න යන්නෙපා..අම්මලා තාත්තලා පොඩි අයට මේවා හදලා දෙන්න ok.

### 3.84. `ජාතිය` -> `nation`
- impact: 5 posts (2 light, 3 heavy), 5 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER කවුද මේ ගෑණි. ජාතිය අවුල්නේ මේකිගේ
  - [OFF] after:  @USER කවුද මේ ගෑණි. nation අවුල්නේ මේකිගේ
  - [OFF] before: @USER කවුද මේ ගෑණි. ජාතිය අවුල්නේ මේකිගේ
  - [OFF] after:  @USER කවුද මේ ගෑණි. nation අවුල්නේ මේකිගේ
  - [OFF] before: මූ සිව්‍රක් පොරොගෙන ඉන්න පොන්න පකෙක් තො ඔක ගල්වපන් අපෙ ජාතිය විනාස කරන්නැතුව... URL
  - [OFF] after:  මූ සිව්‍රක් පොරොගෙන ඉන්න පොන්න පකෙක් තො ඔක ගල්වපන් අපෙ nation destroy කරන්නැතුව... URL

### 3.85. `සැප` -> `comfort`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අැවිත් සැප ඉල්ලා වැලපෙයිද?
  - [NOT] after:  @USER අැවිත් comfort ඉල්ලා වැලපෙයිද?
  - [OFF] before: පයිය කොටා කුක්කුවට සැප දෙන්නේ මෙහෙමයි
  - [OFF] after:  පයිය කොටා කුක්කුවට comfort දෙන්නේ මෙහෙමයි
  - [NOT] before: @USER අැවිත් සැප ඉල්ලා වැලපෙයිද?
  - [NOT] after:  @USER අැවිත් comfort ඉල්ලා වැලපෙයිද?

### 3.86. `පිටිපස්සේ` -> `behind`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER පිටිපස්සේ තියෙන්නේ mosque. ඒකටම කරයි.
  - [NOT] after:  @USER behind තියෙන්නේ mosque. ඒකටම කරයි.
  - [NOT] before: @USER පිටිපස්සේ තියෙන්නේ mosque. ඒකටම කරයි.
  - [NOT] after:  @USER behind තියෙන්නේ mosque. ඒකටම කරයි.
  - [OFF] before: අපි මීටරෙන් හිටියට වැඩක් නෑනේ පිටිපස්සේ ඉන්න ගොන් හරකා  මීටටෙන් ඉන්නේ නෑ නම්
  - [OFF] after:  අපි මීටරෙන් හිටියට වැඩක් නෑනේ behind ඉන්න ගොන් හරකා  මීටටෙන් ඉන්නේ නෑ නම්

### 3.87. `තාමත්` -> `still`
- impact: 4 posts (1 light, 3 heavy), 1 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: තමුසෙ තාමත් කියන්නෙ චන්දුවා කොලු සින් නෙවෙ කියලදොයි
  - [OFF] after:  තමුසෙ still කියන්නෙ චන්දුවා boy සින් නෙවෙ කියලදොයි
  - [NOT] before: @USER බූ, හා, හා. අන්දරේලා තාමත් ඉන්නවානෙ?
  - [NOT] after:  @USER බූ, හා, හා. අන්දරේලා still ඉන්නවානෙ?
  - [NOT] before: @USER බූ, හා, හා. අන්දරේලා තාමත් ඉන්නවානෙ?
  - [NOT] after:  @USER බූ, හා, හා. අන්දරේලා still ඉන්නවානෙ?

### 3.88. `බුලත්` -> `betel`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  ඔහේ දන්නැති උනාට ඒකි වටේ ගිය එකක්,ඔය ලමය ඔහේගෙමයි කියල විස්සාසද? •බුලත් කෙල පාරක් ගහමින්• ඔය ලමයට තිවුනනේ තව ටිකක් හොයල බලන්ට
  - [OFF] after:  @USER @USER  ඔහේ දන්නැති උනාට ඒකි වටේ ගිය එකක්,ඔය ලමය ඔහේගෙමයි කියල විස්සාසද? •betel කෙල පාරක් ගහමින්• ඔය ලමයට තිවුනනේ තව ටිකක් හොයල බලන්ට
  - [OFF] before: @USER පකද බලන්නෙ?කුනුහරපයක් නොවන බැව් කියා සිටිමි.බුලත් පයිය.
  - [OFF] after:  @USER පකද බලන්නෙ?කුනුහරපයක් නොවන බැව් කියා සිටිමි.betel පයිය.
  - [OFF] before: @USER @USER  ඔහේ දන්නැති උනාට ඒකි වටේ ගිය එකක්,ඔය ලමය ඔහේගෙමයි කියල විස්සාසද? •බුලත් කෙල පාරක් ගහමින්• ඔය ලමයට තිවුනනේ තව ටිකක් හොයල බලන්ට
  - [OFF] after:  @USER @USER  ඔහේ දන්නැති උනාට ඒකි වටේ ගිය එකක්,ඔය ලමය ඔහේගෙමයි කියල විස්සාසද? •betel කෙල පාරක් ගහමින්• ඔය ලමයට තිවුනනේ තව ටිකක් හොයල බලන්ට

### 3.89. `වෙනම` -> `separately`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER නෑ තොට වෙනම බනින්නම්
  - [NOT] after:  @USER  @USER නෑ තොට separately බනින්නම්
  - [NOT] before: @USER Queer කියල කියන්නෙ LGBTQ සියලු දෙනාටම පාව්ච්චි කරන්න පුලුවන් අර්ථයක් (an umbrella term). මේ සම්බන්ධ පාඨමාලා තියනවා විශ්වවිද්‍යාල වල queer studies නමින්. වෙනම ජානරයක් තියනවා කලාව හා සිනෙමාව සම්බන්ධයෙන්.  මොකද්ද කියල නිශ්චය කරගන්න අමාරු අය හඳුන්වනවා.
  - [NOT] after:  @USER Queer කියල කියන්නෙ LGBTQ සියලු දෙනාටම පාව්ච්චි කරන්න පුලුවන් අර්ථයක් (an umbrella term). මේ සම්බන්ධ පාඨමාලා තියනවා විශ්වවිද්‍යාල වල queer studies නමින්. separately ජානරයක් තියනවා කලාව හා සිනෙමාව සම්බන්ධයෙන්.  මොකද්ද කියල නිශ්චය කරගන්න අමාරු අය හඳුන්වනවා.
  - [NOT] before: @USER  @USER නෑ තොට වෙනම බනින්නම්
  - [NOT] after:  @USER  @USER නෑ තොට separately බනින්නම්

### 3.90. `බිබී` -> `drinking`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සතුරු කැලම සඳළු තලේ හිඳිති මඳු බිබී, අපේ හැත්ත එල්ලී යති උන්ට පුක දිදී..
  - [OFF] after:  සතුරු කැලම සඳළු තලේ හිඳිති මඳු drinking, අපේ හැත්ත එල්ලී යති උන්ට පුක දිදී..
  - [OFF] before: @USER අනේ මෑටි මෝලෝ. හාමුදුරුවෝ කියලා තියන්නේ මාරාන්තික උපවාසය කියලානේ   කබරයත් තලගොයා කරන්න එපා මෝඩ චූන් ගන්න   ජීවනී බිබී චූන් එකේ උපවාස කරන එකත් කජ්ජක්ද?
  - [OFF] after:  @USER අනේ මෑටි මෝලෝ. හාමුදුරුවෝ කියලා තියන්නේ මාරාන්තික උපවාසය කියලානේ   කබරයත් තලගොයා කරන්න එපා මෝඩ චූන් ගන්න   ජීවනී drinking චූන් එකේ උපවාස කරන එකත් කජ්ජක්ද?
  - [OFF] before: සතුරු කැලම සඳළු තලේ හිඳිති මඳු බිබී, අපේ හැත්ත එල්ලී යති උන්ට පුක දිදී..
  - [OFF] after:  සතුරු කැලම සඳළු තලේ හිඳිති මඳු drinking, අපේ හැත්ත එල්ලී යති උන්ට පුක දිදී..

### 3.91. `එකතු` -> `collect`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: එකතු කරන්නේ.. එකතු...  ළගදි එකක් වැනිෂ් කරමු.  මම උස්සන් එන්නම්.. තෝ බීපන්
  - [NOT] after:  collect කරන්නේ.. collect...  ළගදි එකක් වැනිෂ් කරමු.  මම උස්සන් එන්නම්.. තෝ බීපන්
  - [NOT] before: එකතු කරන්නේ.. එකතු...  ළගදි එකක් වැනිෂ් කරමු.  මම උස්සන් එන්නම්.. තෝ බීපන්
  - [NOT] after:  collect කරන්නේ.. collect...  ළගදි එකක් වැනිෂ් කරමු.  මම උස්සන් එන්නම්.. තෝ බීපන්
  - [NOT] before: @USER කෑලි එකතු කරනව ඇති දැන් ,පව්
  - [NOT] after:  @USER කෑලි collect කරනව ඇති දැන් ,පව්

### 3.92. `තනියම` -> `alone`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER තනියම යන්නෙපා යකෝ අපිවත් එක්ක පලයන්
  - [NOT] after:  @USER  @USER alone යන්නෙපා යකෝ අපිවත් එක්ක පලයන්
  - [NOT] before: @USER  @USER තනියම යන්නෙපා යකෝ අපිවත් එක්ක පලයන්
  - [NOT] after:  @USER  @USER alone යන්නෙපා යකෝ අපිවත් එක්ක පලයන්
  - [NOT] before: @USER ,  @USER  @USER ටහුඩු ඒකි තනියම ජීවත් වෙන්න වෙරදරන එක්කෙනෙක් වෙන්න ඇති
  - [NOT] after:  @USER ,  @USER  @USER ටහුඩු ඒකි alone ජීවත් වෙන්න වෙරදරන එක්කෙනෙක් වෙන්න ඇති

### 3.93. `බුදුන්` -> `Buddha`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER What is sin???  පන්චසිලය රකිනවද ?? බුදුන්  කි පරිදි ජිවත් වන එක නායකයේක් ඉන්නවද ? බොරැ නොකියන .හොරකන් නොකරන
  - [NOT] after:  @USER What is sin???  පන්චසිලය රකිනවද ?? Buddha  කි පරිදි ජිවත් වන එක නායකයේක් ඉන්නවද ? බොරැ නොකියන .හොරකන් නොකරන
  - [NOT] before: " මෝඩ පුද්ගලයකු තමන් මෝඩයකු  බව දන්නේ නම් ඔහු එක්තරා ආකාරයක පණ්ඩිතයෙකි.  මෝඩ පුද්ගලයකු තමන් පණ්ඩිතකු යැයි සිතන්නෙම් නම්  ඔහු සැබෑම මෝඩයෙකි "  -බුදුන් වහන්සේ-
  - [NOT] after:  " මෝඩ පුද්ගලයකු තමන් මෝඩයකු  බව දන්නේ නම් ඔහු එක්තරා ආකාරයක පණ්ඩිතයෙකි.  මෝඩ පුද්ගලයකු තමන් පණ්ඩිතකු යැයි සිතන්නෙම් නම්  ඔහු සැබෑම මෝඩයෙකි "  -Buddha වහන්සේ-
  - [NOT] before: @USER What is sin???  පන්චසිලය රකිනවද ?? බුදුන්  කි පරිදි ජිවත් වන එක නායකයේක් ඉන්නවද ? බොරැ නොකියන .හොරකන් නොකරන
  - [NOT] after:  @USER What is sin???  පන්චසිලය රකිනවද ?? Buddha  කි පරිදි ජිවත් වන එක නායකයේක් ඉන්නවද ? lie නොකියන .හොරකන් නොකරන

### 3.94. `මංගල` -> `wedding`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER බන්දුල එන තුරු මංගල බලා සිටී..
  - [NOT] after:  @USER බන්දුල එන තුරු wedding බලා සිටී..
  - [OFF] before: @USER උන් වැඩි හරියක් මේ රටවල් වලත් නැ අපි ඉන්න ඕනනේ බං මංගල වගේ අපතයොන්ටම ගැලපෙනවා මේ ⁣වගේ සිල්ලර ගෑනු චීවරේ හංවඩු ගහපු හැටි මතකයි මේකි මංගල එක්ක එකතු වෙලා.හොඳට මතකයි මැරිලා යන්නේ නැනේ මේ වගේ කාලකණ්ණි ගෑණු
  - [OFF] after:  @USER උන් වැඩි හරියක් මේ රටවල් වලත් නැ අපි ඉන්න ඕනනේ බං wedding වගේ අපතයොන්ටම ගැලපෙනවා මේ ⁣වගේ සිල්ලර ගෑනු චීවරේ හංවඩු ගහපු හැටි මතකයි මේකි wedding එක්ක එකතු වෙලා.හොඳට මතකයි මැරිලා යන්නේ නැනේ මේ වගේ කාලකණ්ණි ගෑණු
  - [NOT] before: @USER බන්දුල එන තුරු මංගල බලා සිටී..
  - [NOT] after:  @USER බන්දුල එන තුරු wedding බලා සිටී..

### 3.95. `පසුව` -> `after`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අශ්වයා පැනලා ගියායින් පසුව දැන් තමයි ඉස්තාලයේ දොරවැසිමට මතක්වෙලා තියෙන්නේ.
  - [NOT] after:  @USER අශ්වයා පැනලා ගියායින් after දැන් තමයි ඉස්තාලයේ දොරවැසිමට මතක්වෙලා තියෙන්නේ.
  - [OFF] before: @USER @USER  ඔබ කියන ‘අවජාතක‘ බව ඔබේ හැදින්වීමෙන්ම පේනවා! ඉස්සල්ලා ශිෂ්ඨ වෙන්න! පසුව සංවාද කරමු  @USER  #lka
  - [OFF] after:  @USER @USER  ඔබ කියන ‘අවජාතක‘ බව ඔබේ හැදින්වීමෙන්ම පේනවා! ඉස්සල්ලා ශිෂ්ඨ වෙන්න! after සංවාද කරමු  @USER  #lka
  - [NOT] before: @USER අශ්වයා පැනලා ගියායින් පසුව දැන් තමයි ඉස්තාලයේ දොරවැසිමට මතක්වෙලා තියෙන්නේ.
  - [NOT] after:  @USER horse පැනලා ගියායින් after දැන් තමයි ඉස්තාලයේ දොරවැසිමට මතක්වෙලා තියෙන්නේ.

### 3.96. `යමු` -> `let's go`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: නන්නාඳුනන ලෙසේ මග තොට යලි හමුවෙලා, මහ මෙර හිසින් දරාගෙන අපි යමු දුරස් වෙලා... #SomethingsJustNeverMeantToHappen
  - [NOT] after:  නන්නාඳුනන ලෙසේ මග තොට යලි හමුවෙලා, මහ මෙර හිසින් දරාගෙන අපි let's go දුරස් වෙලා... #SomethingsJustNeverMeantToHappen
  - [NOT] before: @USER @USER  @USER  ඒකි කොරලවැල්ලෙද කොහෙද බං ? ;-) මෙහ් අපි යමු එයාව බලන්න පව් නේ බං
  - [NOT] after:  @USER @USER  @USER  ඒකි කොරලවැල්ලෙද කොහෙද බං ? ;-) මෙහ් අපි let's go එයාව බලන්න පව් නේ බං
  - [NOT] before: නන්නාඳුනන ලෙසේ මග තොට යලි හමුවෙලා, මහ මෙර හිසින් දරාගෙන අපි යමු දුරස් වෙලා... #SomethingsJustNeverMeantToHappen
  - [NOT] after:  නන්නාඳුනන ලෙසේ මග තොට again හමුවෙලා, මහ මෙර හිසින් දරාගෙන අපි let's go දුරස් වෙලා... #SomethingsJustNeverMeantToHappen

### 3.97. `බැන` -> `scold`
- impact: 4 posts (1 light, 3 heavy), 3 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මෙන්න මේ යහපාලන පොන්න පකයාගේ තරම .............. අනේ අම්මපා ගොන්නු ගිය උඩ කිරිඇල්ල නැමැති ගොනා මාධ්‍යවේදියෙකුට බැන... URL
  - [OFF] after:  මෙන්න මේ යහපාලන පොන්න පකයාගේ තරම .............. අනේ අම්මපා ගොන්නු ගිය උඩ කිරිඇල්ල නැමැති ගොනා මාධ්‍යවේදියෙකුට scold... URL
  - [OFF] before: මෙන්න මේ යහපාලන පොන්න පකයාගේ තරම .............. අනේ අම්මපා ගොන්නු ගිය උඩ කිරිඇල්ල නැමැති ගොනා මාධ්‍යවේදියෙකුට බැන... URL
  - [OFF] after:  මෙන්න මේ යහපාලන පොන්න පකයාගේ තරම .............. අනේ අම්මපා ගොන්නු ගිය up කිරිඇල්ල නැමැති ගොනා මාධ්‍යවේදියෙකුට scold... URL
  - [OFF] before: මොකාද මේ සාරි ඇදගෙන ගාල කඩාගෙන බැන බැන ගියපු බලු හරකා..
  - [OFF] after:  මොකාද මේ saree ඇදගෙන ගාල කඩාගෙන scold scold ගියපු බලු හරකා..

### 3.98. `කරත්ත` -> `cart`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මං නම් කියන්නෙ මේක සද්දෙට දාගෙන අපේ ගොනා අපිට හොදා කියලා කෑගගහා ගොන් කරත්ත වල යන්නෝනෙ URL
  - [NOT] after:  මං නම් කියන්නෙ මේක සද්දෙට දාගෙන අපේ ගොනා අපිට හොදා කියලා කෑගගහා ගොන් cart වල යන්නෝනෙ URL
  - [NOT] before: පුල්ලි ගොනා පුරුදු කාරයා මම ගොනා කරත්ත කාරයා #MisheardSinhalaLyrics
  - [NOT] after:  පුල්ලි ගොනා පුරුදු කාරයා මම ගොනා cart කාරයා #MisheardSinhalaLyrics
  - [NOT] before: මං නම් කියන්නෙ මේක සද්දෙට දාගෙන අපේ ගොනා අපිට හොදා කියලා කෑගගහා ගොන් කරත්ත වල යන්නෝනෙ URL
  - [NOT] after:  මං නම් කියන්නෙ මේක සද්දෙට දාගෙන අපේ ගොනා අපිට good කියලා කෑගගහා ගොන් cart වල යන්නෝනෙ URL

### 3.99. `පාත්` -> `down`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: වදින්න ගිය දේවාලේ ගොනා ඇනලා ගහෙන් වැටිච්ච මිහිහට ඉහේ කඩා පාත් උනා වගේ  #lka
  - [NOT] after:  වදින්න ගිය දේවාලේ ගොනා ඇනලා ගහෙන් වැටිච්ච මිහිහට ඉහේ කඩා down උනා වගේ  #lka
  - [NOT] before: වදින්න ගිය දේවාලේ ගොනා ඇනලා ගහෙන් වැටිච්ච මිහිහට ඉහේ කඩා පාත් උනා වගේ  #lka
  - [NOT] after:  වදින්න ගිය temple ගොනා ඇනලා ගහෙන් වැටිච්ච මිහිහට ඉහේ කඩා down උනා වගේ  #lka
  - [NOT] before: @USER  @USER තෝ කොහෙන්ද පාත් වුනේ
  - [NOT] after:  @USER  @USER තෝ කොහෙන්ද down වුනේ

### 3.100. `මෙවා` -> `these`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කොහොමද රග මෙවා වෙන්න පුලුවන් එවාද මෙවා බලල unp  එකට පුක දෙන කාලකණ්ණි සිංහලු දැනගනියව් කෙලවගන්නෙ සිංහලුම කියල පරයින්ගෙන්
  - [OFF] after:  කොහොමද රග these වෙන්න පුලුවන් එවාද these බලල unp  එකට පුක දෙන කාලකණ්ණි සිංහලු දැනගනියව් කෙලවගන්නෙ සිංහලුම කියල පරයින්ගෙන්
  - [NOT] before: @USER මෙවා අනික් අයට පේන්නේ නැද්ද ?
  - [NOT] after:  @USER these අනික් අයට පේන්නේ නැද්ද ?
  - [OFF] before: කොහොමද රග මෙවා වෙන්න පුලුවන් එවාද මෙවා බලල unp  එකට පුක දෙන කාලකණ්ණි සිංහලු දැනගනියව් කෙලවගන්නෙ සිංහලුම කියල පරයින්ගෙන්
  - [OFF] after:  කොහොමද රග these වෙන්න පුලුවන් එවාද these බලල unp  එකට පුක දෙන කාලකණ්ණි සිංහලු දැනගනියව් කෙලවගන්නෙ සිංහලුම කියල පරයින්ගෙන්

### 3.101. `පැතුම` -> `wish`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER පුංචි අපෙනුත් සුභ පැතුම !!
  - [NOT] after:  @USER පුංචි අපෙනුත් සුභ wish !!
  - [NOT] before: ඒකි :- "මගේ facebook account එකට අමතරව තව fake accounts පහක් හදාගන්න කිව්වා. මට තියෙන්නේ අයියේ, ස'ගේ page එකේ post වලට "ජය නියතයි", "ඌවේ පැතුම ඔබයි", "ඔබයි නියතව ජය ගන්නවා" වගේ comments දාලා post ටිකත් එයාලගේම group එකේ share කරන්න විතරයි තියෙන්නේ...  (2/4)
  - [NOT] after:  ඒකි :- "මගේ facebook account එකට අමතරව තව fake accounts පහක් හදාගන්න කිව්වා. මට තියෙන්නේ අයියේ, ස'ගේ page එකේ post වලට "ජය නියතයි", "ඌවේ wish ඔබයි", "ඔබයි නියතව ජය ගන්නවා" වගේ comments දාලා post ටිකත් එයාලගේම group එකේ share කරන්න විතරයි තියෙන්නේ...  (2/4)
  - [NOT] before: @USER පුංචි අපෙනුත් සුභ පැතුම !!
  - [NOT] after:  @USER small අපෙනුත් සුභ wish !!

### 3.102. `අයිති` -> `belongs`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: වලාකුලු වහගත්තට,අහසෙම උන්නට.හාවා තුරුලෙ හිටියට,අඩො හද උබ අයිති මට. .
  - [NOT] after:  වලාකුලු වහගත්තට,අහසෙම උන්නට.හාවා තුරුලෙ හිටියට,අඩො හද උබ belongs මට. .
  - [OFF] before: ගොන් වානරයෝ කවද්ද තේරුම් ගන්නේ මේ ලොකේ උන්ට විතරක් නෙමේ අයිති හැම ජිවීයෙක්ටම අයිතී කියන එක? කුඹියට ඇමීබාවට තියන අයිතියම තමා මුන්ටත් තියෙන්නේ කියන එක? URL
  - [OFF] after:  ගොන් වානරයෝ කවද්ද තේරුම් ගන්නේ මේ ලොකේ උන්ට විතරක් නෙමේ belongs හැම ජිවීයෙක්ටම අයිතී කියන එක? කුඹියට ඇමීබාවට තියන අයිතියම තමා මුන්ටත් තියෙන්නේ කියන එක? URL
  - [NOT] before: වලාකුලු වහගත්තට,අහසෙම උන්නට.හාවා තුරුලෙ හිටියට,අඩො හද උබ අයිති මට. .
  - [NOT] after:  වලාකුලු වහගත්තට,අහසෙම උන්නට.හාවා තුරුලෙ හිටියට,අඩො heart උබ belongs මට. .

### 3.103. `මිනිහා` -> `guy`
- impact: 4 posts (1 light, 3 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මේ මිනිහා මොනව කියනවද මන්දා...
  - [NOT] after:  @USER මේ guy මොනව කියනවද මන්දා...
  - [NOT] before: @USER මේ මිනිහා මොනව කියනවද මන්දා...
  - [NOT] after:  @USER මේ guy මොනව කියනවද මන්දා...
  - [OFF] before: @USER පුක දීලාම ගෙවිලා ඇති දැන්. ඒත් මිනිහා මේ වෙන දේවල් මාරෙට ඉවසනවා කියලා තේරිලා දුක හිතුනා
  - [OFF] after:  @USER පුක දීලාම ගෙවිලා ඇති දැන්. ඒත් guy මේ වෙන things මාරෙට ඉවසනවා කියලා තේරිලා දුක හිතුනා

### 3.104. `දන්නා` -> `known`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මේ වල් කතාවේ අපි නො දන්නා හරිය URL
  - [NOT] after:  මේ වල් කතාවේ අපි නො known හරිය URL
  - [NOT] before: මේ වල් කතාවේ අපි නො දන්නා හරිය URL
  - [NOT] after:  මේ wild කතාවේ අපි නො known හරිය URL
  - [OFF] before: @USER පරාද වෙන්නේ නැති බව දන්නා නිසා මේ හාල් පාරුවා නෙගන්නවා නම් හොඳයී කියලා හිතෙනවා
  - [OFF] after:  @USER පරාද වෙන්නේ නැති බව known නිසා මේ හාල් පාරුවා නෙගන්නවා නම් හොඳයී කියලා හිතෙනවා

### 3.105. `නැත්තං` -> `otherwise`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඒකි ring එකේ ගොංනේ නැත්තං ලස්සනයි
  - [OFF] after:  @USER ඒකි ring එකේ ගොංනේ otherwise ලස්සනයි
  - [OFF] before: වාසනා එමෙ නැත්තං චේතනා බඩුව කියලද උඹ කියන්නෙ ?
  - [OFF] after:  වාසනා එමෙ otherwise චේතනා බඩුව කියලද උඹ කියන්නෙ ?
  - [OFF] before: @USER ඒකි ring එකේ ගොංනේ නැත්තං ලස්සනයි
  - [OFF] after:  @USER ඒකි ring එකේ ගොංනේ otherwise ලස්සනයි

### 3.106. `රත්` -> `hot`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: Messi ත් ආතල් ගන්නවද කොහෙද ලබ්බ  එකක් කියන්නෙ නෑ. අපි රත් වෙවී ඉන්නව
  - [NOT] after:  Messi ත් ආතල් ගන්නවද කොහෙද ලබ්බ  එකක් කියන්නෙ නෑ. අපි hot වෙවී ඉන්නව
  - [NOT] before: Messi ත් ආතල් ගන්නවද කොහෙද ලබ්බ  එකක් කියන්නෙ නෑ. අපි රත් වෙවී ඉන්නව
  - [NOT] after:  Messi ත් ආතල් ගන්නවද කොහෙද ලබ්බ  එකක් කියන්නෙ නෑ. අපි hot වෙවී ඉන්නව
  - [OFF] before: @USER ඔහොම රත් උනොත් තෝ වඳවෙයි
  - [OFF] after:  @USER ඔහොම hot උනොත් තෝ වඳවෙයි

### 3.107. `පැණි` -> `honey`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තෝ පල පැණි සෙවෙල චමත් මීමා
  - [OFF] after:  @USER  @USER තෝ පල honey සෙවෙල චමත් මීමා
  - [NOT] before: @USER පැණි පොකුරු පොකුරු ඔබ යන කල ඔබ දෙසටම නැමීයන්... මම කාලි
  - [NOT] after:  @USER honey පොකුරු පොකුරු ඔබ යන කල ඔබ දෙසටම නැමීයන්... මම කාලි
  - [OFF] before: @USER  @USER තෝ පල පැණි සෙවෙල චමත් මීමා
  - [OFF] after:  @USER  @USER තෝ පල honey සෙවෙල චමත් buffalo

### 3.108. `බාලයි` -> `younger`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER තමුසෙට වඩා ඒකි බාලයි ද?
  - [NOT] after:  @USER තමුසෙට වඩා ඒකි younger ද?
  - [NOT] before: @USER ඒකි හිතන්නේ අපි එකිට වඩා බාලයි. අපි පොඩි උන් එකි තමා ලොකු එකී කියලා
  - [NOT] after:  @USER ඒකි හිතන්නේ අපි එකිට වඩා younger. අපි පොඩි උන් එකි තමා ලොකු එකී කියලා
  - [NOT] before: @USER තමුසෙට වඩා ඒකි බාලයි ද?
  - [NOT] after:  @USER තමුසෙට වඩා ඒකි younger ද?

### 3.109. `සේරම` -> `all`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔවුන් සේරම එලවනේ නැතුව හදන්න වෙන්නේ නෑ...
  - [NOT] after:  @USER ඔවුන් all එලවනේ නැතුව හදන්න වෙන්නේ නෑ...
  - [NOT] before: @USER තඩි කට්ටක් ගහල සේරම ටික ගන්නෝන
  - [NOT] after:  @USER තඩි කට්ටක් ගහල all ටික ගන්නෝන
  - [NOT] before: @USER ඔවුන් සේරම එලවනේ නැතුව හදන්න වෙන්නේ නෑ...
  - [NOT] after:  @USER ඔවුන් all එලවනේ නැතුව make වෙන්නේ නෑ...

### 3.110. `පිට` -> `back`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පිට රටින් එන හැම විදේස නියෝජිතයෙක්ම ඉස්සෙල්ලාම යන්නේ උතුරේ ^_^  යකෝ වරෙන්කො සබරගමුවට රෙද්ද අපි වේලෙනවා -_-   #prayforsrilanka  :3
  - [NOT] after:  back රටින් එන හැම විදේස නියෝජිතයෙක්ම ඉස්සෙල්ලාම යන්නේ උතුරේ ^_^  යකෝ වරෙන්කො සබරගමුවට රෙද්ද අපි වේලෙනවා -_-   #prayforsrilanka  :3
  - [OFF] before: ගොන් අලියෙකු.. පිට නැගි.. ගොන් අලියා...!!!  අපේ ගොනා.. අපට හොදා - මීට..UNP පාක්ෂිකයන් !!!!
  - [OFF] after:  ගොන් අලියෙකු.. back නැගි.. ගොන් අලියා...!!!  අපේ ගොනා.. අපට හොදා - මීට..UNP පාක්ෂිකයන් !!!!
  - [NOT] before: පිට රටින් එන හැම විදේස නියෝජිතයෙක්ම ඉස්සෙල්ලාම යන්නේ උතුරේ ^_^  යකෝ වරෙන්කො සබරගමුවට රෙද්ද අපි වේලෙනවා -_-   #prayforsrilanka  :3
  - [NOT] after:  back රටින් එන හැම විදේස නියෝජිතයෙක්ම first යන්නේ උතුරේ ^_^  යකෝ වරෙන්කො සබරගමුවට රෙද්ද අපි වේලෙනවා -_-   #prayforsrilanka  :3

### 3.111. `ලඟ` -> `near`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER නෙද්දකිං...  එවුන්ද ලඟ ලොකුව නැතෙයි..?
  - [NOT] after:  @USER නෙද්දකිං...  එවුන්ද near ලොකුව නැතෙයි..?
  - [OFF] before: හෙ යකඩ පයිය මගේ නුඹ ලඟ හඬා වැලපුනා මල්ලේ   #විනී
  - [OFF] after:  හෙ යකඩ පයිය මගේ නුඹ near හඬා වැලපුනා මල්ලේ   #විනී
  - [NOT] before: @USER නෙද්දකිං...  එවුන්ද ලඟ ලොකුව නැතෙයි..?
  - [NOT] after:  @USER නෙද්දකිං...  එවුන්ද near ලොකුව නැතෙයි..?

### 3.112. `කෙල්ලේ` -> `girl`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පයිය කෙලින් උනා කෙල්ලේ
  - [OFF] after:  @USER පයිය කෙලින් උනා girl
  - [OFF] before: @USER @USER අනේ පලයන් කෙල්ලේ යන්න..
  - [OFF] after:  @USER @USER අනේ පලයන් girl යන්න..
  - [OFF] before: @USER පයිය කෙලින් උනා කෙල්ලේ
  - [OFF] after:  @USER පයිය straight උනා girl

### 3.113. `කුඩු` -> `drugs`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER තෝ කුඩු ගහලද කසිප්පු ගහලද
  - [OFF] after:  @USER තෝ drugs ගහලද කසිප්පු ගහලද
  - [NOT] before: @USER  @USER තෝ කසිප්පු ගහලද කුඩු ගහලද
  - [NOT] after:  @USER  @USER තෝ කසිප්පු ගහලද drugs ගහලද
  - [OFF] before: @USER තෝ කුඩු ගහලද කසිප්පු ගහලද
  - [OFF] after:  @USER තෝ drugs ගහලද කසිප්පු ගහලද

### 3.114. `අවුල්` -> `trouble`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER සාදු සාදු සාදු. අර පොඩි එකා වැන්දම තමා අවුල්.
  - [NOT] after:  @USER සාදු සාදු සාදු. අර පොඩි එකා වැන්දම තමා trouble.
  - [NOT] before: @USER සාදු සාදු සාදු. අර පොඩි එකා වැන්දම තමා අවුල්.
  - [NOT] after:  @USER සාදු සාදු සාදු. අර පොඩි එකා වැන්දම තමා trouble.
  - [NOT] before: @USER  @USER ඇයි අවුල් ද?
  - [NOT] after:  @USER  @USER ඇයි trouble ද?

### 3.115. `හතරක්` -> `four`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හරි දෙකක් නෙවේ තුන හතරක් අැති
  - [NOT] after:  @USER හරි දෙකක් නෙවේ තුන four අැති
  - [NOT] before: @USER හරි දෙකක් නෙවේ තුන හතරක් අැති
  - [NOT] after:  @USER හරි දෙකක් නෙවේ තුන four අැති
  - [NOT] before: මගේ බල්ලා නැති වෙලා අවුරුද්දකුත් මාස හතරක් වෙනවා. තාමත් සමහර දාට පාන්දරට එයා එලියෙ ඉඳං කූංකූං ගානවා ඇහෙනවා. හිතේ තියෙන එකද මන්දා.
  - [NOT] after:  මගේ බල්ලා නැති වෙලා අවුරුද්දකුත් මාස four වෙනවා. තාමත් සමහර දාට පාන්දරට එයා එලියෙ ඉඳං කූංකූං ගානවා ඇහෙනවා. හිතේ තියෙන එකද මන්දා.

### 3.116. `දෙයියෝ` -> `god`
- impact: 4 posts (1 light, 3 heavy), 3 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ප්ලේන් එකේ යන්න බල්ලෙක් ඉන්නවා කිවුවම ඉතින් දෙයියෝ සිහි වෙනවා.. මිහිහෙක්ට වඩා බල්ලා වටිනවා.
  - [NOT] after:  ප්ලේන් එකේ යන්න බල්ලෙක් ඉන්නවා කිවුවම ඉතින් god සිහි වෙනවා.. මිහිහෙක්ට වඩා dog වටිනවා.
  - [OFF] before: ඕනෙ නෑ කෙල්ලෙ සක්කර වට්ටම නිකං දුන්නත් වගේ අවුරුදු වට්ටම ඇවිත් ඩිංගක් උඹ තුරුලු කර ගත්තම පද්දපං උඹට දෙයියෝ දුන්න වත්කම.... GIF
  - [OFF] after:  ඕනෙ නෑ කෙල්ලෙ සක්කර වට්ටම නිකං දුන්නත් වගේ අවුරුදු වට්ටම ඇවිත් ඩිංගක් උඹ තුරුලු කර ගත්තම පද්දපං උඹට god දුන්න වත්කම.... GIF
  - [OFF] before: බනින එකා බැනපන් පැයකට එක වතාවක් වගේ,යකෝ..  තත්පරේටත් දෙක ගානෙ  හචින් ගිහින් මැරෙන්න යන්නෙ.. තරහයි කියලා එහෙම  පලි ගන්න එපා දෙයියෝ..සහ ගහනවා මේවට හරිය.
  - [OFF] after:  scold එකා බැනපන් පැයකට එක වතාවක් වගේ,යකෝ..  තත්පරේටත් දෙක ගානෙ  හචින් ගිහින් මැරෙන්න යන්නෙ.. තරහයි කියලා එහෙම  පලි ගන්න එපා god..සහ ගහනවා මේවට හරිය.

### 3.117. `කකුල්` -> `legs`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඉස්සරහා කකුල් කොහෙද යකෝ. කකුල් දෙකයි නේ තියෙන්නේ. තෝ කුකුලා කියලා හරකා කනවාද දන්නේ නෑ
  - [NOT] after:  @USER ඉස්සරහා legs කොහෙද යකෝ. legs දෙකයි නේ තියෙන්නේ. තෝ කුකුලා කියලා හරකා කනවාද දන්නේ නෑ
  - [NOT] before: @USER ඉස්සරහා කකුල් කොහෙද යකෝ. කකුල් දෙකයි නේ තියෙන්නේ. තෝ කුකුලා කියලා හරකා කනවාද දන්නේ නෑ
  - [NOT] after:  @USER front legs කොහෙද යකෝ. legs දෙකයි නේ තියෙන්නේ. තෝ කුකුලා කියලා හරකා කනවාද දන්නේ නෑ
  - [OFF] before: @USER කකුල් දෙක මැදින් බිජ්ජ උල් වෙලා වගෙ
  - [OFF] after:  @USER legs දෙක මැදින් බිජ්ජ උල් වෙලා වගෙ

### 3.118. `ඔයාලගේ` -> `your`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ශා ඔයාලගේ බල්ලා නම් මාරයි ආආආ
  - [NOT] after:  @USER ශා your බල්ලා නම් මාරයි ආආආ
  - [OFF] before: @USER  @USER    අනේ අයියේ මේක ඔයාලගේ මෙක ඔයාලගේ ලොකු අම්මගෙර් හුත්ත නෙවේ ඔයාට ඕන ඕන විදිහට අඹරන්න අපි ඒකේ ඉන්න ශුක්‍රාණුත් නෙවේ ඔයාලට ඕන ඕන විදිහට ඇඹරෙන්න
  - [OFF] after:  @USER  @USER    අනේ අයියේ මේක your මෙක your ලොකු අම්මගෙර් හුත්ත නෙවේ ඔයාට ඕන ඕන විදිහට අඹරන්න අපි ඒකේ ඉන්න ශුක්‍රාණුත් නෙවේ ඔයාලට ඕන ඕන විදිහට ඇඹරෙන්න
  - [NOT] before: @USER ශා ඔයාලගේ බල්ලා නම් මාරයි ආආආ
  - [NOT] after:  @USER ශා your බල්ලා නම් awesome ආආආ

### 3.119. `බයේ` -> `scared`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අයියෝ සිරිසේන මේ හුජ්ජ දෙමල ත්‍රස්තවාදීයාට බයේ දැන් එතකොට...යන්නෙම නැද්ද..අෑැැහ්  ??? විළිලැජ්ජයි..සිරිසේන දීපිය ඔය ජනපතිකම ළමයෙකුට..
  - [OFF] after:  අයියෝ සිරිසේන මේ හුජ්ජ දෙමල ත්‍රස්තවාදීයාට scared දැන් එතකොට...යන්නෙම නැද්ද..අෑැැහ්  ??? විළිලැජ්ජයි..සිරිසේන දීපිය ඔය ජනපතිකම ළමයෙකුට..
  - [OFF] before: ලියනගේ පයිය කපනවයි කියන්නේ?බයේ බෑ බං :3
  - [OFF] after:  ලියනගේ පයිය කපනවයි කියන්නේ?scared බෑ බං :3
  - [OFF] before: අයියෝ සිරිසේන මේ හුජ්ජ දෙමල ත්‍රස්තවාදීයාට බයේ දැන් එතකොට...යන්නෙම නැද්ද..අෑැැහ්  ??? විළිලැජ්ජයි..සිරිසේන දීපිය ඔය ජනපතිකම ළමයෙකුට..
  - [OFF] after:  අයියෝ Sirisena මේ හුජ්ජ දෙමල ත්‍රස්තවාදීයාට scared දැන් එතකොට...යන්නෙම නැද්ද..අෑැැහ්  ??? විළිලැජ්ජයි..Sirisena දීපිය ඔය ජනපතිකම ළමයෙකුට..

### 3.120. `අර්ජුන්` -> `Arjun`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මුංව අල්ලන්ඩ එපා කියනව නෙමෙයි. මේ හාල්මැස්සො අල්ලන දැලට අර්ජුන් මහේන්ද්‍රන් වගේ මෝරු අහුවෙන්නෙ නැති එකයි පුදුමෙ !
  - [NOT] after:  @USER මුංව අල්ලන්ඩ එපා කියනව නෙමෙයි. මේ හාල්මැස්සො අල්ලන දැලට Arjun මහේන්ද්‍රන් වගේ මෝරු අහුවෙන්නෙ නැති එකයි පුදුමෙ !
  - [OFF] before: අලියා- අර්ජුන් මහේන්ද්‍ර හොදායි අත- කිලී මහේන්ද්‍ර හොදායි පොහොට්ටුව-පර්සි මහේන්ද්‍ර හොදායි මම? නොදකින් විතරක් — feeling disappointed
  - [OFF] after:  අලියා- Arjun මහේන්ද්‍ර හොදායි අත- කිලී මහේන්ද්‍ර හොදායි පොහොට්ටුව-පර්සි මහේන්ද්‍ර හොදායි මම? නොදකින් විතරක් — feeling disappointed
  - [NOT] before: @USER මුංව අල්ලන්ඩ එපා කියනව නෙමෙයි. මේ හාල්මැස්සො අල්ලන දැලට අර්ජුන් මහේන්ද්‍රන් වගේ මෝරු අහුවෙන්නෙ නැති එකයි පුදුමෙ !
  - [NOT] after:  @USER මුංව අල්ලන්ඩ එපා කියනව නෙමෙයි. මේ හාල්මැස්සො catch දැලට Arjun මහේන්ද්‍රන් වගේ මෝරු අහුවෙන්නෙ නැති එකයි පුදුමෙ !

### 3.121. `මහත්` -> `fat`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER මේ ගෑණි මාසෙට මහත් වෙලා නෙ ..
  - [OFF] after:  @USER  @USER මේ ගෑණි මාසෙට fat වෙලා නෙ ..
  - [NOT] before: නහපුඩු මහත් කොට මී ගොන් මුලුබ නැඩ කිමිදෙති නැවුම් පුස්ඹෙහි වෙල් කුඹුරු බඩ  හැමදාම වහිනකොට මට මේක මතක් වෙනව අෆ්ෆා... අදත් එහෙමයි....
  - [NOT] after:  නහපුඩු fat කොට මී ගොන් මුලුබ නැඩ කිමිදෙති නැවුම් පුස්ඹෙහි වෙල් කුඹුරු බඩ  හැමදාම වහිනකොට මට මේක මතක් වෙනව අෆ්ෆා... අදත් එහෙමයි....
  - [OFF] before: @USER  @USER මේ ගෑණි මාසෙට මහත් වෙලා නෙ ..
  - [OFF] after:  @USER  @USER මේ ගෑණි මාසෙට fat වෙලා නෙ ..

### 3.122. `බීලා` -> `drunk`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අයිසෙ මහත්තයා, දන් නැත්නම් පොඩ්ඩක් ඇස් ඇරලා බලාගන්න  @USER    තේකක් බීලා ඉන්නෙ නැතිව යනවා ගොවි අරගල බලන්න
  - [NOT] after:  අයිසෙ මහත්තයා, දන් නැත්නම් පොඩ්ඩක් ඇස් ඇරලා බලාගන්න  @USER    තේකක් drunk ඉන්නෙ නැතිව යනවා ගොවි අරගල බලන්න
  - [NOT] before: @USER @USER  තමුසෙ බීලා...  :P
  - [NOT] after:  @USER @USER  තමුසෙ drunk...  :P
  - [NOT] before: අයිසෙ මහත්තයා, දන් නැත්නම් පොඩ්ඩක් ඇස් ඇරලා බලාගන්න  @USER    තේකක් බීලා ඉන්නෙ නැතිව යනවා ගොවි අරගල බලන්න
  - [NOT] after:  අයිසෙ මහත්තයා, දන් නැත්නම් පොඩ්ඩක් ඇස් ඇරලා බලාගන්න  @USER    තේකක් drunk ඉන්නෙ නැතිව යනවා farmer අරගල බලන්න

### 3.123. `කැස්ස` -> `cough`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: උන කැස්ස හෙම්බ උගුරු අමරුව දැන් සතියක් තිස්සෙ. ඒ අස්සෙ නිදි උලුක්කුවක් ආව. ට හුකන අපලයක් යකෝ මට තියෙන්නෙ
  - [OFF] after:  උන cough හෙම්බ උගුරු අමරුව දැන් සතියක් තිස්සෙ. ඒ අස්සෙ නිදි උලුක්කුවක් ආව. ට හුකන අපලයක් යකෝ මට තියෙන්නෙ
  - [OFF] before: උන කැස්ස හෙම්බ උගුරු අමරුව දැන් සතියක් තිස්සෙ. ඒ අස්සෙ නිදි උලුක්කුවක් ආව. ට හුකන අපලයක් යකෝ මට තියෙන්නෙ
  - [OFF] after:  උන cough හෙම්බ උගුරු අමරුව දැන් සතියක් තිස්සෙ. ඒ අස්සෙ sleep උලුක්කුවක් ආව. ට හුකන අපලයක් යකෝ මට තියෙන්නෙ
  - [NOT] before: කැස්ස නම් පස්ස උස්සලා බිම අනින්න
  - [NOT] after:  cough නම් පස්ස උස්සලා බිම අනින්න

### 3.124. `දත්` -> `teeth`
- impact: 4 posts (1 light, 3 heavy), 1 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඒකි මොනා හිතුවඩ දන්නෑ සෝනෙගෙ දත් නැ හිතන්නැති ඔන්න
  - [NOT] after:  @USER ඒකි මොනා හිතුවඩ දන්නෑ සෝනෙගෙ teeth නැ හිතන්නැති ඔන්න
  - [NOT] before: @USER ඒකි මොනා හිතුවඩ දන්නෑ සෝනෙගෙ දත් නැ හිතන්නැති ඔන්න
  - [NOT] after:  @USER ඒකි මොනා හිතුවඩ දන්නෑ සෝනෙගෙ teeth නැ හිතන්නැති ඔන්න
  - [NOT] before: @USER @USER  දත් නැති උන්ටනෙ බං සාමාන්‍යයෙන් හපල කන්න අමාරු.මට අමතක උනා වයසක උන්ටත් දත් නෑ කියල ඒකයි උබට ළඳරුවා කිව්වෙ sry ආ
  - [NOT] after:  @USER @USER  teeth නැති උන්ටනෙ බං සාමාන්‍යයෙන් හපල eat අමාරු.මට අමතක උනා වයසක උන්ටත් teeth නෑ කියල ඒකයි උබට ළඳරුවා කිව්වෙ sry ආ

### 3.125. `පූසො` -> `cats`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER    මම නම් එක පූසයි නේ තෝ පූසො ගොඩක් තියාගෙන ඉන්නවා නේ
  - [NOT] after:  @USER  @USER    මම නම් එක පූසයි නේ තෝ cats ගොඩක් තියාගෙන ඉන්නවා නේ
  - [NOT] before: @USER  @USER    මම නම් එක පූසයි නේ තෝ පූසො ගොඩක් තියාගෙන ඉන්නවා නේ
  - [NOT] after:  @USER  @USER    මම නම් එක cat නේ තෝ cats ගොඩක් තියාගෙන ඉන්නවා නේ
  - [NOT] before: මොනවද අයිසෙ ඔය කරන්නෙ. GIF Mr.Gauwa | @USER  · 26 Aug 2020 එහෙනම් පූසො අපි ගියා!  Show this thread
  - [NOT] after:  මොනවද අයිසෙ ඔය කරන්නෙ. GIF Mr.Gauwa | @USER  · 26 Aug 2020 එහෙනම් cats අපි ගියා!  Show this thread

### 3.126. `හොදා` -> `good`
- impact: 4 posts (1 light, 3 heavy), 3 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තූහ් නොදකින්  මේවගෙ හද්ද නාකියෙක් ? මූ හොදා අපෙ බල්ලො බලාගන්ඩ
  - [OFF] after:  @USER  @USER තූහ් නොදකින්  මේවගෙ හද්ද නාකියෙක් ? මූ good අපෙ බල්ලො බලාගන්ඩ
  - [NOT] before: මං නම් කියන්නෙ මේක සද්දෙට දාගෙන අපේ ගොනා අපිට හොදා කියලා කෑගගහා ගොන් කරත්ත වල යන්නෝනෙ URL
  - [NOT] after:  මං නම් කියන්නෙ මේක සද්දෙට දාගෙන අපේ ගොනා අපිට good කියලා කෑගගහා ගොන් cart වල යන්නෝනෙ URL
  - [OFF] before: @USER  @USER තූහ් නොදකින්  මේවගෙ හද්ද නාකියෙක් ? මූ හොදා අපෙ බල්ලො බලාගන්ඩ
  - [OFF] after:  @USER  @USER තූහ් නොදකින්  මේවගෙ හද්ද නාකියෙක් ? මූ good අපෙ බල්ලො බලාගන්ඩ

### 3.127. `දුක්` -> `sad`
- impact: 4 posts (1 light, 3 heavy), 1 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඉද ඉද ළුක ‌ව‌ෙහෙර -විද විද දහම් මනහර -සිද බිද දුක් සසර- අහෝ ‌දෙව්දත් ‌නෙ‌ාදිටිි ‌මොක්පුර.
  - [NOT] after:  @USER ඉද ඉද ළුක ‌ව‌ෙහෙර -විද විද දහම් මනහර -සිද බිද sad සසර- අහෝ ‌දෙව්දත් ‌නෙ‌ාදිටිි ‌මොක්පුර.
  - [NOT] before: @USER ඉද ඉද ළුක ‌ව‌ෙහෙර -විද විද දහම් මනහර -සිද බිද දුක් සසර- අහෝ ‌දෙව්දත් ‌නෙ‌ාදිටිි ‌මොක්පුර.
  - [NOT] after:  @USER ඉද ඉද ළුක ‌ව‌ෙහෙර -විද විද dhamma මනහර -සිද බිද sad සසර- අහෝ ‌දෙව්දත් ‌නෙ‌ාදිටිි ‌මොක්පුර.
  - [OFF] before: @USER ඔව් බං ඒක ඇත්ත. වේස පක්කු එකෙක් ඇවිල්ල නෑ තාම සැප දුක් බලන්න.
  - [OFF] after:  @USER ඔව් බං ඒක ඇත්ත. වේස පක්කු එකෙක් ඇවිල්ල නෑ still සැප sad බලන්න.

### 3.128. `හොරෙන්` -> `secretly`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER අඩෝ ඒකි හොරෙන් ගනී
  - [NOT] after:  @USER  @USER අඩෝ ඒකි secretly ගනී
  - [NOT] before: @USER මෙය වනාහී ඈතට ඇදී යන ලදකගේ තඩි පුපක් දිහා අනූසයා හොරෙන් බලාගෙන සිටන අවස්තාවක ඌට මතක් වූ පද පේලියකි..
  - [NOT] after:  @USER මෙය වනාහී ඈතට ඇදී යන ලදකගේ තඩි පුපක් දිහා අනූසයා secretly බලාගෙන සිටන අවස්තාවක ඌට මතක් වූ පද පේලියකි..
  - [NOT] before: @USER  @USER අඩෝ ඒකි හොරෙන් ගනී
  - [NOT] after:  @USER  @USER අඩෝ ඒකි secretly ගනී

### 3.129. `අදාල` -> `relevant`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER රෙද්ද උස්සගෙන එයිද අදාල උන්..
  - [OFF] after:  @USER  @USER රෙද්ද උස්සගෙන එයිද relevant උන්..
  - [OFF] before: @USER @USER   උඹ පල.  උඹ අදාල නෑ. @USER  @USER  @USER  @USER  @USER
  - [OFF] after:  @USER @USER   උඹ පල.  උඹ relevant නෑ. @USER  @USER  @USER  @USER  @USER
  - [OFF] before: @USER  @USER රෙද්ද උස්සගෙන එයිද අදාල උන්..
  - [OFF] after:  @USER  @USER රෙද්ද උස්සගෙන එයිද relevant උන්..

### 3.130. `මචං` -> `machan`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අඩො මචං නැද්ද බං දිරච්ච ලනුවකුයි කල් ඉකුත් වෙච්ච වහා බොතලයකුයි ගන්න...
  - [NOT] after:  @USER අඩො machan නැද්ද බං දිරච්ච ලනුවකුයි කල් ඉකුත් වෙච්ච වහා බොතලයකුයි ගන්න...
  - [NOT] before: @USER අඩො මචං නැද්ද බං දිරච්ච ලනුවකුයි කල් ඉකුත් වෙච්ච වහා බොතලයකුයි ගන්න...
  - [NOT] after:  @USER අඩො machan නැද්ද බං දිරච්ච ලනුවකුයි කල් ඉකුත් වෙච්ච වහා බොතලයකුයි ගන්න...
  - [OFF] before: @USER මේකෙ ඉන්න පරිනත වේසියන්ටයි උනගේ ගොම අදින පිම්පියන්ටයි ඕවා තේරෙන්නේ නැහැ මචං.උන් දන්නෙ උන්ට වැඩිය දෙයක් මේකෙ කිව්වොත් වටකරලා පච්චල් කරන්න විතරයි අවජාතක හැත්ත
  - [OFF] after:  @USER මේකෙ ඉන්න පරිනත වේසියන්ටයි උනගේ ගොම අදින පිම්පියන්ටයි ඕවා තේරෙන්නේ නැහැ machan.උන් දන්නෙ උන්ට වැඩිය දෙයක් මේකෙ කිව්වොත් වටකරලා පච්චල් කරන්න විතරයි අවජාතක හැත්ත

### 3.131. `ඔලුව` -> `head`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අහක යන ඒවට ඔලුව දාන්නෙ ඇයි මලේ නාකි ගෑණු වගේ
  - [OFF] after:  අහක යන ඒවට head දාන්නෙ ඇයි මලේ නාකි ගෑණු වගේ
  - [NOT] before: ඔලුව දාලා යන්න ආවා  තොපි මැරිලාද
  - [NOT] after:  head දාලා යන්න ආවා  තොපි මැරිලාද
  - [OFF] before: අහක යන ඒවට ඔලුව දාන්නෙ ඇයි මලේ නාකි ගෑණු වගේ
  - [OFF] after:  අහක යන ඒවට head දාන්නෙ ඇයි මලේ නාකි ගෑණු වගේ

### 3.132. `ළඟ` -> `near`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: -නවක වදය රෙද්ද අස්සෙන් බේරීම- එකෙක් හෙළුවෙන් හිටගෙන ඉන්නව. තව එකෙක් ඌ ළඟ බිම ඇණ තියල වාඩිවෙලා උගේ අහවල් එකට අතින්... URL
  - [OFF] after:  -නවක වදය රෙද්ද අස්සෙන් බේරීම- එකෙක් හෙළුවෙන් හිටගෙන ඉන්නව. තව එකෙක් ඌ near බිම ඇණ තියල වාඩිවෙලා උගේ අහවල් එකට අතින්... URL
  - [OFF] before: -නවක වදය රෙද්ද අස්සෙන් බේරීම- එකෙක් හෙළුවෙන් හිටගෙන ඉන්නව. තව එකෙක් ඌ ළඟ බිම ඇණ තියල වාඩිවෙලා උගේ අහවල් එකට අතින්... URL
  - [OFF] after:  -නවක වදය රෙද්ද අස්සෙන් බේරීම- එකෙක් හෙළුවෙන් හිටගෙන ඉන්නව. තව එකෙක් ඌ near බිම ඇණ තියල වාඩිවෙලා උගේ අහවල් එකට අතින්... URL
  - [NOT] before: ඇත්ත ඒකි මගේ  පොඩි එකී හැම දුකම කඳුළම එක්ක  මගේ ළඟ හිනාවෙලා හුරතලෙන් ඉන්න මගේ පැංචී උඹ හරි හයියක් මට ඇත්තමයි උඹ මගෙම පොඩ්ඩි  @USER
  - [NOT] after:  ඇත්ත ඒකි මගේ  පොඩි එකී හැම දුකම කඳුළම එක්ක  මගේ near හිනාවෙලා හුරතලෙන් ඉන්න මගේ පැංචී උඹ හරි හයියක් මට ඇත්තමයි උඹ මගෙම පොඩ්ඩි  @USER

### 3.133. `ඉබ්බෙක්` -> `tortoise`
- impact: 4 posts (2 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: 96.1 FM or 96.3 FM Island wide... __________________________ තඩි කොමඩු ගෙඩියක් කුඩු පට්ටම් කරන ඉබ්බෙක්..!!... URL
  - [NOT] after:  96.1 FM or 96.3 FM Island wide... __________________________ තඩි කොමඩු ගෙඩියක් කුඩු පට්ටම් කරන tortoise..!!... URL
  - [NOT] before: 96.1 FM or 96.3 FM Island wide... __________________________ තඩි කොමඩු ගෙඩියක් කුඩු පට්ටම් කරන ඉබ්බෙක්..!!... URL
  - [NOT] after:  96.1 FM or 96.3 FM Island wide... __________________________ තඩි watermelon ගෙඩියක් කුඩු පට්ටම් කරන tortoise..!!... URL
  - [NOT] before: මාත් දානො තඩි ඉබ්බෙක් Profile එකට   හුම්ම්
  - [NOT] after:  මාත් දානො තඩි tortoise Profile එකට   හුම්ම්

### 3.134. `අමාරුයි` -> `hard`
- impact: 4 posts (1 light, 3 heavy), 1 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER බැල්ලි, මම ගොඩක් අමාරුයි ��
  - [NOT] after:  @USER බැල්ලි, මම ගොඩක් hard ��
  - [NOT] before: @USER බැල්ලි, මම ගොඩක් අමාරුයි ��
  - [NOT] after:  @USER බැල්ලි, මම lot hard ��
  - [NOT] before: @USER  @USER නෑ ඒකෙ අඳුරගන්න අමාරුයි වගේ ඔයාව අර නාකි පෙනුම කොහෙ ගිහින්ද නෑ
  - [NOT] after:  @USER  @USER නෑ ඒකෙ අඳුරගන්න hard වගේ ඔයාව අර නාකි පෙනුම where ගිහින්ද නෑ

### 3.135. `රත්තරන්` -> `gold`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: දිව්‍යපුත්‍රයට පුක දුන්න කියල තොට රත්තරන් රෙන්ඩ බෑ.. ආං ඒක මතකතියාගෙන දීපං හරී..
  - [OFF] after:  දිව්‍යපුත්‍රයට පුක දුන්න කියල තොට gold රෙන්ඩ බෑ.. ආං ඒක මතකතියාගෙන දීපං හරී..
  - [OFF] before: දිව්‍යපුත්‍රයට පුක දුන්න කියල තොට රත්තරන් රෙන්ඩ බෑ.. ආං ඒක මතකතියාගෙන දීපං හරී..
  - [OFF] after:  දිව්‍යපුත්‍රයට පුක දුන්න කියල තොට gold රෙන්ඩ බෑ.. ආං ඒක මතකතියාගෙන give හරී..
  - [OFF] before: @USER උඹ පොන්නයෙක් නොවී privacy අයින් කරපන් rt කරන්න මගේ රත්තරන් යාලුවේ
  - [OFF] after:  @USER උඹ පොන්නයෙක් නොවී privacy අයින් කරපන් rt කරන්න මගේ gold යාලුවේ

### 3.136. `කොලු` -> `boy`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: තමුසෙ තාමත් කියන්නෙ චන්දුවා කොලු සින් නෙවෙ කියලදොයි
  - [OFF] after:  තමුසෙ තාමත් කියන්නෙ චන්දුවා boy සින් නෙවෙ කියලදොයි
  - [OFF] before: ඉයා පොප් තිසර උබ දැන් බඩුත් ගහනවද?? — feeling කොලු බඩුව at Gurukula URL
  - [OFF] after:  ඉයා පොප් තිසර උබ දැන් බඩුත් ගහනවද?? — feeling boy බඩුව at Gurukula URL
  - [OFF] before: තමුසෙ තාමත් කියන්නෙ චන්දුවා කොලු සින් නෙවෙ කියලදොයි
  - [OFF] after:  තමුසෙ still කියන්නෙ චන්දුවා boy සින් නෙවෙ කියලදොයි

### 3.137. `අශ්වයා` -> `horse`
- impact: 4 posts (1 light, 3 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අශ්වයා පැනලා ගියායින් පසුව දැන් තමයි ඉස්තාලයේ දොරවැසිමට මතක්වෙලා තියෙන්නේ.
  - [NOT] after:  @USER horse පැනලා ගියායින් after දැන් තමයි ඉස්තාලයේ දොරවැසිමට මතක්වෙලා තියෙන්නේ.
  - [NOT] before: ඉස්තාලයෙ ලගින අශ්වයා සහා වල් බල්ලා
  - [NOT] after:  ඉස්තාලයෙ ලගින horse සහා වල් බල්ලා
  - [NOT] before: @USER අශ්වයා ගියාම ගාල වහල වැඩක් තියෙද? #ලොකේපජික්
  - [NOT] after:  @USER horse ගියාම ගාල වහල work තියෙද? #ලොකේපජික්

### 3.138. `වැලි` -> `sand`
- impact: 4 posts (1 light, 3 heavy), 4 of them labelled OFF, 7 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: වල් බැල්ලි ගහනව තොට වැලි  @USER    අප්පටසිරි  Dinal @USER  · 26 Dec 2017 Type “වල් බැල්ලි ගහනවා තොට වැලි"@ the 3rd “girl” in your list
  - [OFF] after:  වල් බැල්ලි ගහනව තොට sand  @USER    අප්පටසිරි  Dinal @USER  · 26 Dec 2017 Type “වල් බැල්ලි ගහනවා තොට sand"@ the 3rd “girl” in your list
  - [OFF] before: වල් බැල්ලි ගහනව තොට වැලි  @USER  The following media includes potentially sensitive content. Change settings View
  - [OFF] after:  wild බැල්ලි ගහනව තොට sand  @USER  The following media includes potentially sensitive content. Change settings View
  - [OFF] before: වල් බැල්ලි ගහනවා තොට වැලි  @USER Dinal @USER  · 26 Dec 2017 Type “වල් බැල්ලි ගහනවා තොට වැලි"@ the 3rd “girl” in your list
  - [OFF] after:  wild බැල්ලි ගහනවා තොට sand  @USER Dinal @USER  · 26 Dec 2017 Type “wild බැල්ලි ගහනවා තොට sand"@ the 3rd “girl” in your list

### 3.139. `ගණන්` -> `expensive`
- impact: 4 posts (2 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ගෑණි මාව ගණන් ගන්නේ නෑ. ඒකයි එයාව මරලා දැම්මේ #murder #womenkilled URL
  - [NOT] after:  ගෑණි මාව expensive ගන්නේ නෑ. ඒකයි එයාව මරලා දැම්මේ #murder #womenkilled URL
  - [NOT] before: ගෑණි මාව ගණන් ගන්නේ නෑ. ඒකයි එයාව මරලා දැම්මේ #murder #womenkilled URL
  - [NOT] after:  ගෑණි මාව expensive ගන්නේ නෑ. ඒකයි එයාව මරලා දැම්මේ #murder #womenkilled URL
  - [OFF] before: “ගෑණි මාව ගණන් ගන්නේ නෑ.. ඒකයි එයාව මරලා දැම්මේ” URL
  - [OFF] after:  “ගෑණි මාව expensive ගන්නේ නෑ.. ඒකයි එයාව මරලා දැම්මේ” URL

### 3.140. `යක්කු` -> `devils`
- impact: 4 posts (2 light, 2 heavy), 4 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER Ow මෝඩ යක්කු ගැනු කීවොත් ඇති.
  - [OFF] after:  @USER Ow මෝඩ devils ගැනු කීවොත් ඇති.
  - [OFF] before: @USER Ow මෝඩ යක්කු ගැනු කීවොත් ඇති.
  - [OFF] after:  @USER Ow මෝඩ devils ගැනු කීවොත් ඇති.
  - [OFF] before: ඔය ගොන් මොරාල් එවුන් එක්ක ඔච්චර පැටලෙන්න යන්න එපා. ඔය වගේ මෝඩ යක්කු තමයි මොකක් හරි ගොන් තෙලක් වැදුනම සහරාන්ලා වගේ මරාගෙන මැරෙන්න යන්නෙ
  - [OFF] after:  ඔය ගොන් මොරාල් එවුන් එක්ක ඔච්චර පැටලෙන්න යන්න එපා. ඔය වගේ මෝඩ devils තමයි මොකක් හරි ගොන් තෙලක් වැදුනම සහරාන්ලා වගේ මරාගෙන මැරෙන්න යන්නෙ

### 3.141. `හට` -> `to`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මා හට ලැබුනු කිව්වෙ, කා හට ලැබුනු ද
  - [NOT] after:  @USER මා to received කිව්වෙ, කා to received ද
  - [NOT] before: අන්න ආහරෙ සුගලා බෑදලා..තොපි දෙන්නම පලයවු මා හට වෑදලා :D :D URL
  - [NOT] after:  අන්න ආහරෙ සුගලා බෑදලා..තොපි දෙන්නම පලයවු මා to වෑදලා :D :D URL
  - [NOT] before: අන්න ආහරෙ සුගලා බෑදලා..තොපි දෙන්නම පලයවු මා හට වෑදලා :D :D URL
  - [NOT] after:  අන්න ආහරෙ සුගලා බෑදලා..තොපි both පලයවු මා to වෑදලා :D :D URL

### 3.142. `කකුල` -> `leg`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අන්න බයිඩන් සීයා බල්ලත් එක්ක සෙල්ලන් කරලා කකුල කඩා ගෙන.  නාකි විසේ!
  - [OFF] after:  අන්න බයිඩන් සීයා බල්ලත් එක්ක සෙල්ලන් කරලා leg කඩා ගෙන.  නාකි විසේ!
  - [OFF] before: අන්න බයිඩන් සීයා බල්ලත් එක්ක සෙල්ලන් කරලා කකුල කඩා ගෙන.  නාකි විසේ!
  - [OFF] after:  අන්න බයිඩන් grandpa බල්ලත් එක්ක සෙල්ලන් කරලා leg කඩා ගෙන.  නාකි විසේ!
  - [NOT] before: @USER අඩේ අපේ එකත් කටුගම්බියකද කොහෙද කකුල කපං ඇවිත්  මුං දෙන්නා එක ගමනක්වත්ද ගියේ   බෙහෙත් දානකං හිටියේ කකුල් පන නැති එකා වගේ නැගිටින්නෙත් නැතුව කෙදිරි ගගා. බෙහෙත් ටික දාපු ගමන් කරෙ  අමාරු කොහෙන් ගියාද මන්දා
  - [NOT] after:  @USER අඩේ අපේ එකත් කටුගම්බියකද කොහෙද leg කපං ඇවිත්  මුං දෙන්නා එක ගමනක්වත්ද ගියේ   medicine දානකං හිටියේ කකුල් පන නැති එකා වගේ නැගිටින්නෙත් නැතුව කෙදිරි ගගා. medicine ටික දාපු ගමන් කරෙ  අමාරු කොහෙන් ගියාද මන්දා

### 3.143. `හවස` -> `evening`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හවස 5න් පස්සේ යන්නම බෑ.. එන්නේ රංචු පිටින්.. පස්ස මිරිකනවා, පියයුරු මිරිකනවා.. සිසුවියන්ට, කාර්යාල නිළධාරිනියන්ට... URL
  - [OFF] after:  evening 5න් පස්සේ යන්නම බෑ.. එන්නේ රංචු පිටින්.. පස්ස මිරිකනවා, පියයුරු මිරිකනවා.. සිසුවියන්ට, කාර්යාල නිළධාරිනියන්ට... URL
  - [OFF] before: @USER නෑ බං ඊයෙ හවස දාලා තියෙන්නෙ.. තාම බැල්ලි ආවෙ නෑ..
  - [OFF] after:  @USER නෑ බං ඊයෙ evening දාලා තියෙන්නෙ.. still බැල්ලි ආවෙ නෑ..
  - [OFF] before: හවස 5න් පස්සේ යන්නම බෑ.. එන්නේ රංචු පිටින්.. පස්ස මිරිකනවා, පියයුරු මිරිකනවා.. සිසුවියන්ට, කාර්යාල නිළධාරිනියන්ට... URL
  - [OFF] after:  evening 5න් පස්සේ යන්නම බෑ.. එන්නේ රංචු පිටින්.. පස්ස මිරිකනවා, පියයුරු මිරිකනවා.. සිසුවියන්ට, කාර්යාල නිළධාරිනියන්ට... URL

### 3.144. `බිහි` -> `born`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තු හ් නොදකින් මෙවන් දේවදත්තයො මතුවටවත්මේ හෙල දිවයිනෙ බිහි නොවෙවා
  - [OFF] after:  @USER  @USER තු හ් නොදකින් මෙවන් දේවදත්තයො මතුවටවත්මේ හෙල දිවයිනෙ born නොවෙවා
  - [NOT] before: අමාරුවෙන් ලැබෙන දෙය හැම විටම ශ්‍රේෂ්ඨයි !  ඇතින්නියක් සහ බැල්ලියෙකු එකවර ගැබ් ගත්තේය. මාස තුනකට පසු බැල්ලි බලු පැටවුන් හය දෙනෙකු බිහි කළේය. මාස හයකට පසු, බැල්ලි නැවත ගැබ්ගෙන ඇති අතර, මාස නවයකදී එහි තවත් බලු පැටවුන් දුසිමක් බිහි කළේය. රටාව දිගටම පැවතුනි.
  - [NOT] after:  අමාරුවෙන් ලැබෙන දෙය හැම විටම ශ්‍රේෂ්ඨයි !  ඇතින්නියක් සහ බැල්ලියෙකු එකවර ගැබ් ගත්තේය. months තුනකට පසු බැල්ලි බලු පැටවුන් හය දෙනෙකු born කළේය. months හයකට පසු, බැල්ලි නැවත ගැබ්ගෙන ඇති අතර, months නවයකදී එහි තවත් බලු පැටවුන් දුසිමක් born කළේය. රටාව දිගටම පැවතුනි.
  - [OFF] before: @USER  @USER තු හ් නොදකින් මෙවන් දේවදත්තයො මතුවටවත්මේ හෙල දිවයිනෙ බිහි නොවෙවා
  - [OFF] after:  @USER  @USER තු හ් නොදකින් such දේවදත්තයො මතුවටවත්මේ හෙල දිවයිනෙ born නොවෙවා

### 3.145. `පුංචි` -> `small`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: බලපන් මේ ගෑණි මේ පුංචි එකාට කවන්නෙ මොනවද කියල නොදකිං
  - [OFF] after:  බලපන් මේ ගෑණි මේ small එකාට කවන්නෙ මොනවද කියල නොදකිං
  - [NOT] before: @USER පුංචි අපෙනුත් සුභ පැතුම !!
  - [NOT] after:  @USER small අපෙනුත් සුභ wish !!
  - [OFF] before: බලපන් මේ ගෑණි මේ පුංචි එකාට කවන්නෙ මොනවද කියල නොදකිං
  - [OFF] after:  බලපන් මේ ගෑණි මේ small එකාට කවන්නෙ මොනවද කියල නොදකිං

### 3.146. `කොල` -> `leaf`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER හබරල කොල හිල් වෙන්න හුජ්ජ කරන්න ඉතින් අලි පයියක් වෙන්න ඕනේ
  - [OFF] after:  @USER හබරල leaf හිල් වෙන්න හුජ්ජ කරන්න ඉතින් අලි පයියක් වෙන්න ඕනේ
  - [OFF] before: @USER හබරල කොල හිල් වෙන්න හුජ්ජ කරන්න ඉතින් අලි පයියක් වෙන්න ඕනේ
  - [OFF] after:  @USER හබරල leaf හිල් වෙන්න හුජ්ජ කරන්න ඉතින් elephants පයියක් වෙන්න ඕනේ
  - [NOT] before: නොම්බරේ ලියලා තිබ්බ කොල කෑල්ල headup display එක අස්සේ වැටුනා කියාන්කො
  - [NOT] after:  නොම්බරේ ලියලා තිබ්බ leaf කෑල්ල headup display එක inside වැටුනා කියාන්කො

### 3.147. `කීයක්` -> `how many`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER හිරගෙවල් කීයක් කියල හදන්නද ඇල්ලුවනම්
  - [NOT] after:  @USER  @USER හිරගෙවල් how many කියල හදන්නද ඇල්ලුවනම්
  - [OFF] before: @USER පලයන් කැරි පොන්නයා යන්න. ඕව තොපේ හිත්වල තියෙන ඒවා තමා. උඹ හිතුවද වහගත්තු පලොයට ඔක්කොමහොද උන් කියලා. හොයලා බලපන් උඹලගෙම උන් කීයක් වටේ යන්වද කියලා. තෝ හිතුවද ඔක්කොම වහන් ගෝනි බිල්ලො වගේ නැති ගෑනු ඔක්කොම ගණිකාවො කියලා වේස පකා
  - [OFF] after:  @USER පලයන් කැරි පොන්නයා යන්න. ඕව තොපේ හිත්වල තියෙන ඒවා තමා. උඹ හිතුවද වහගත්තු පලොයට ඔක්කොමහොද උන් කියලා. හොයලා බලපන් උඹලගෙම උන් how many වටේ යන්වද කියලා. තෝ හිතුවද ඔක්කොම වහන් ගෝනි බිල්ලො වගේ නැති women ඔක්කොම ගණිකාවො කියලා වේස පකා
  - [NOT] before: @USER  @USER හිරගෙවල් කීයක් කියල හදන්නද ඇල්ලුවනම්
  - [NOT] after:  @USER  @USER prisons how many කියල හදන්නද ඇල්ලුවනම්

### 3.148. `පරිස්සමෙන්` -> `carefully`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: තොට අද කෑවා ඇති නේද මචන්..........අනිත් එක්කනා ට තව වැඩි කල් නෑ පරිස්සමෙන් — feeling crazy
  - [NOT] after:  තොට අද කෑවා ඇති නේද machan..........අනිත් එක්කනා ට තව වැඩි කල් නෑ carefully — feeling crazy
  - [NOT] before: @USER ඒකිත් පට්ටනේ.හැබැයි ඒකි පෙන්ගුවින් එක්ක ඇරියස් පරිස්සමෙන්.
  - [NOT] after:  @USER ඒකිත් පට්ටනේ.හැබැයි ඒකි පෙන්ගුවින් එක්ක ඇරියස් carefully.
  - [NOT] before: @USER ඒකිත් පට්ටනේ.හැබැයි ඒකි පෙන්ගුවින් එක්ක ඇරියස් පරිස්සමෙන්.
  - [NOT] after:  @USER ඒකිත් පට්ටනේ.හැබැයි ඒකි පෙන්ගුවින් එක්ක ඇරියස් carefully.

### 3.149. `තද` -> `tight`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ටහුඩු  තද තද චතුරිකා නගා
  - [NOT] after:  @USER ටහුඩු  tight tight චතුරිකා නගා
  - [NOT] before: @USER ටහුඩු  තද තද චතුරිකා නගා
  - [NOT] after:  @USER ටහුඩු  tight tight චතුරිකා නගා
  - [NOT] before: "කකුල් තද කොට බැඳෙමු - කැත හිත්වලට කවි !!" URL
  - [NOT] after:  "කකුල් tight කොට බැඳෙමු - කැත හිත්වලට poems !!" URL

### 3.150. `අලියා` -> `elephant`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: දුප් බල්ලා දුප්  චිප් චිප් පුසා  ජඃ ජඃ වස්සා   දහ අලියා දහ   වලස්සු එලවන්නෙ කොහොමද?   Scott Bixby @USER  · 17 Jun 2020 Any tips for bear-proofing a birdfeeder? Show this thread
  - [NOT] after:  දුප් බල්ලා දුප්  චිප් චිප් පුසා  ජඃ ජඃ වස්සා   දහ elephant දහ   වලස්සු එලවන්නෙ කොහොමද?   Scott Bixby @USER  · 17 Jun 2020 Any tips for bear-proofing a birdfeeder? Show this thread
  - [NOT] before: දුප් බල්ලා දුප්  චිප් චිප් පුසා  ජඃ ජඃ වස්සා   දහ අලියා දහ   වලස්සු එලවන්නෙ කොහොමද?   Scott Bixby @USER  · 17 Jun 2020 Any tips for bear-proofing a birdfeeder? Show this thread
  - [NOT] after:  දුප් dog දුප්  චිප් චිප් පුසා  ජඃ ජඃ වස්සා   දහ elephant දහ   වලස්සු එලවන්නෙ කොහොමද?   Scott Bixby @USER  · 17 Jun 2020 Any tips for bear-proofing a birdfeeder? Show this thread
  - [OFF] before: ගොන් අලියෙකු.. පිට නැගි.. ගොන් අලියා...!!!  අපේ ගොනා.. අපට හොදා - මීට..UNP පාක්ෂිකයන් !!!!
  - [OFF] after:  ගොන් අලියෙකු.. back නැගි.. ගොන් elephant...!!!  අපේ ගොනා.. අපට හොදා - මීට..UNP පාක්ෂිකයන් !!!!

### 3.151. `මෙහේ` -> `here`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අරූ පැය 2කට කලින් War is over කියලත් දාලා අපි මෙහේ නැගිටගෙන බලන් ඉන්නව.. මොනෞත්තක්ද අයිසෙ
  - [OFF] after:  අරූ පැය 2කට කලින් War is over කියලත් දාලා අපි here නැගිටගෙන බලන් ඉන්නව.. මොනෞත්තක්ද අයිසෙ
  - [OFF] before: අරූ පැය 2කට කලින් War is over කියලත් දාලා අපි මෙහේ නැගිටගෙන බලන් ඉන්නව.. මොනෞත්තක්ද අයිසෙ
  - [OFF] after:  අරූ hour 2කට කලින් War is over කියලත් දාලා අපි here නැගිටගෙන බලන් ඉන්නව.. මොනෞත්තක්ද අයිසෙ
  - [OFF] before: @USER  @USER මොන නවනිංගිරාවක්ද මේ? කලුතරට පිටින් ආපු කාලකණ්ණි රැලක් කරපු වැඩක්..  කලුතර බෝධිය පහුකරද්දි නැගිටලා වැඳලා පඬුරකුත් දාලා යන අය මෙහේ ඉන්නේ ..
  - [OFF] after:  @USER  @USER මොන නවනිංගිරාවක්ද මේ? කලුතරට පිටින් ආපු කාලකණ්ණි රැලක් කරපු work..  කලුතර බෝධිය පහුකරද්දි නැගිටලා වැඳලා පඬුරකුත් දාලා යන අය here ඉන්නේ ..

### 3.152. `සම්බන්ධ` -> `related`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හරි සම්බන්ධ කට්ටිය කවුද කියන්නකෝ
  - [NOT] after:  @USER හරි related කට්ටිය කවුද කියන්නකෝ
  - [NOT] before: @USER හරි සම්බන්ධ කට්ටිය කවුද කියන්නකෝ
  - [NOT] after:  @USER හරි related කට්ටිය කවුද කියන්නකෝ
  - [NOT] before: @USER Queer කියල කියන්නෙ LGBTQ සියලු දෙනාටම පාව්ච්චි කරන්න පුලුවන් අර්ථයක් (an umbrella term). මේ සම්බන්ධ පාඨමාලා තියනවා විශ්වවිද්‍යාල වල queer studies නමින්. වෙනම ජානරයක් තියනවා කලාව හා සිනෙමාව සම්බන්ධයෙන්.  මොකද්ද කියල නිශ්චය කරගන්න අමාරු අය හඳුන්වනවා.
  - [NOT] after:  @USER Queer කියල කියන්නෙ LGBTQ සියලු දෙනාටම පාව්ච්චි කරන්න පුලුවන් අර්ථයක් (an umbrella term). මේ related පාඨමාලා තියනවා විශ්වවිද්‍යාල වල queer studies නමින්. separately ජානරයක් තියනවා කලාව හා සිනෙමාව සම්බන්ධයෙන්.  මොකද්ද කියල නිශ්චය කරගන්න අමාරු අය හඳුන්වනවා.

### 3.153. `තිසර` -> `Thisara`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හංදි ගානෙ ගිහින් තිසර පට විකුනපං ගොන් හරකා
  - [OFF] after:  හංදි ගානෙ ගිහින් Thisara පට විකුනපං ගොන් හරකා
  - [OFF] before: හංදි ගානෙ ගිහින් තිසර පට විකුනපං ගොන් හරකා
  - [OFF] after:  හංදි ගානෙ ගිහින් Thisara පට විකුනපං ගොන් හරකා
  - [OFF] before: ඉයා පොප් තිසර උබ දැන් බඩුත් ගහනවද?? — feeling කොලු බඩුව at Gurukula URL
  - [OFF] after:  ඉයා පොප් Thisara උබ දැන් බඩුත් ගහනවද?? — feeling boy බඩුව at Gurukula URL

### 3.154. `සීයා` -> `grandpa`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER දත් නැති නිසා කට වහන් ඉන්නවා... මෝඩ සීයා..
  - [OFF] after:  @USER  @USER දත් නැති නිසා කට වහන් ඉන්නවා... මෝඩ grandpa..
  - [OFF] before: @USER  @USER දත් නැති නිසා කට වහන් ඉන්නවා... මෝඩ සීයා..
  - [OFF] after:  @USER  @USER teeth නැති නිසා කට වහන් ඉන්නවා... මෝඩ grandpa..
  - [OFF] before: අන්න බයිඩන් සීයා බල්ලත් එක්ක සෙල්ලන් කරලා කකුල කඩා ගෙන.  නාකි විසේ!
  - [OFF] after:  අන්න බයිඩන් grandpa බල්ලත් එක්ක සෙල්ලන් කරලා leg කඩා ගෙන.  නාකි විසේ!

### 3.155. `පියා` -> `father`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අවුලෙ පියා කවුද, තමන් මිස වෙන කවුද
  - [NOT] after:  @USER අවුලෙ father කවුද, තමන් මිස වෙන කවුද
  - [NOT] before: @USER අවුලෙ පියා කවුද, තමන් මිස වෙන කවුද
  - [NOT] after:  @USER අවුලෙ father කවුද, තමන් මිස වෙන කවුද
  - [NOT] before: @USER එයා අප්පච්චි... මෙයා පියා.....
  - [NOT] after:  @USER එයා father... මෙයා father.....

### 3.156. `තේ` -> `tea`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මං ඉපදිලා හැබැයි තේ⁣⁣රෙන වයසක නෙමෙයි. හැබැයි 80 ගණන්වල එයාලාගෙ ක්‍රියාකලාපය ගැනයි මේ ළඟකදි එයාලගෙ ක්‍රියාකලාපය ගැන මටනම් කිසිම පැහැදීමක් නෑ. ඒත everybody is entitled to their opinion.
  - [NOT] after:  @USER මං ඉපදිලා හැබැයි tea⁣⁣රෙන වයසක නෙමෙයි. හැබැයි 80 ගණන්වල එයාලාගෙ ක්‍රියාකලාපය ගැනයි මේ ළඟකදි එයාලගෙ ක්‍රියාකලාපය ගැන මටනම් කිසිම පැහැදීමක් නෑ. ඒත everybody is entitled to their opinion.
  - [NOT] before: @USER මං ඉපදිලා හැබැයි තේ⁣⁣රෙන වයසක නෙමෙයි. හැබැයි 80 ගණන්වල එයාලාගෙ ක්‍රියාකලාපය ගැනයි මේ ළඟකදි එයාලගෙ ක්‍රියාකලාපය ගැන මටනම් කිසිම පැහැදීමක් නෑ. ඒත everybody is entitled to their opinion.
  - [NOT] after:  @USER මං ඉපදිලා හැබැයි tea⁣⁣රෙන වයසක නෙමෙයි. හැබැයි 80 ගණන්වල එයාලාගෙ ක්‍රියාකලාපය ගැනයි මේ ළඟකදි එයාලගෙ ක්‍රියාකලාපය ගැන මටනම් කිසිම පැහැදීමක් නෑ. ඒත everybody is entitled to their opinion.
  - [NOT] before: @USER රස තේ ඵකක් මෙයාට හදලා දෙන්න
  - [NOT] after:  @USER රස tea one මෙයාට හදලා දෙන්න

### 3.157. `වාගෙ` -> `like`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: දිව්‍ය අන්ගනාවන්ට අපට වාගෙ තරහ යන්නෙ නෑ ඒක හින්ද ඒ උදවිය කිසිමදාක නාකි වෙන්නෙ නෑ.. #sajje
  - [NOT] after:  දිව්‍ය අන්ගනාවන්ට අපට like තරහ යන්නෙ නෑ ඒක හින්ද ඒ උදවිය කිසිමදාක නාකි වෙන්නෙ නෑ.. #sajje
  - [OFF] before: අගමැතියා ඇමෙරිකා ගියා ලෙඩ්ඩු බිම බුදියනවා කියාගෙන කට අරින තොපි වාගෙ නිවට නියාලු බූරූ මොංගලයොම තමා මහ ඉස්පිරිතාලේ... URL
  - [OFF] after:  අගමැතියා ඇමෙරිකා ගියා ලෙඩ්ඩු බිම බුදියනවා කියාගෙන කට අරින තොපි like coward නියාලු බූරූ මොංගලයොම තමා මහ ඉස්පිරිතාලේ... URL
  - [NOT] before: දිව්‍ය අන්ගනාවන්ට අපට වාගෙ තරහ යන්නෙ නෑ ඒක හින්ද ඒ උදවිය කිසිමදාක නාකි වෙන්නෙ නෑ.. #sajje
  - [NOT] after:  දිව්‍ය අන්ගනාවන්ට අපට like තරහ යන්නෙ නෑ ඒක because ඒ උදවිය කිසිමදාක නාකි වෙන්නෙ නෑ.. #sajje

### 3.158. `මිනිස්සුන්ගේ` -> `people`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: බල්ලෝ බලල්ලු හදන හැත්ත දැනගන්න ඕනේ උන් හදන සත්තු උන්ගේ වතුවල විතරක් මළපහ කරන විදිහට  හදාගන්න. පාරේ, අනික් මිනිස්සුන්ගේ වතුවල මළපහ කරන්න ඉඩ දීලා ඔහේ බලං ඉන්න උන් බඩ ගිහිල්ලා මැරෙන්න ඕනේ   #සාප
  - [OFF] after:  බල්ලෝ බලල්ලු හදන හැත්ත know ඕනේ උන් හදන සත්තු උන්ගේ වතුවල විතරක් මළපහ කරන විදිහට  හදාගන්න. පාරේ, අනික් people වතුවල මළපහ කරන්න ඉඩ දීලා ඔහේ බලං ඉන්න උන් බඩ ගිහිල්ලා මැරෙන්න ඕනේ   #සාප
  - [NOT] before: මිනිස්සුන්ගේ සාප වලින් බේරෙන්න බෑ මොන දේවාලේ ගියත්.. NewsWire @USER  · 24 Dec 2021 Sri Lanka PM Rajapaksa worships at Lord Venkateswara temple - PTI URL
  - [NOT] after:  people සාප වලින් බේරෙන්න බෑ මොන දේවාලේ ගියත්.. NewsWire @USER  · 24 Dec 2021 Sri Lanka PM Rajapaksa worships at Lord Venkateswara temple - PTI URL
  - [NOT] before: මිනිස්සුන්ගේ සාප වලින් බේරෙන්න බෑ මොන දේවාලේ ගියත්.. NewsWire @USER  · 24 Dec 2021 Sri Lanka PM Rajapaksa worships at Lord Venkateswara temple - PTI URL
  - [NOT] after:  people සාප වලින් බේරෙන්න බෑ මොන temple ගියත්.. NewsWire @USER  · 24 Dec 2021 Sri Lanka PM Rajapaksa worships at Lord Venkateswara temple - PTI URL

### 3.159. `අයිය` -> `brother`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ස’ කැරකිල කැරකිල ගහන්නෙම රටවිරුවොන්ට... පව්  @USER  අයිය
  - [NOT] after:  @USER ස’ කැරකිල කැරකිල ගහන්නෙම රටවිරුවොන්ට... පව්  @USER  brother
  - [OFF] before: @USER මාත් නංගිගේ බබාට පිටකොටුවේ නීරෝ සීඩි හවුස් එකෙන් කාටුන් වගෑක් ගෙනිච්චා.. තූ නොදකින්..කොලිටි සෑහෙන අඩුයි..ඉන් පස්සේ දැන් පෙන් එකකටවත් දාල දෙන්න ඕනි.. ඒත් පෙන් එකක් දෙන්න බැහැ අනික් අයිය බුවාල ආවම උන්ගේ වැල එහෙ මෙහෙ ගෙනියන්න ඒක ගන්නවා.
  - [OFF] after:  @USER මාත් නංගිගේ බබාට පිටකොටුවේ නීරෝ සීඩි හවුස් එකෙන් කාටුන් වගෑක් ගෙනිච්චා.. තූ නොදකින්..කොලිටි සෑහෙන අඩුයි..ඉන් පස්සේ දැන් පෙන් එකකටවත් දාල දෙන්න ඕනි.. ඒත් පෙන් එකක් දෙන්න බැහැ other brother බුවාල ආවම උන්ගේ වැල එහෙ මෙහෙ ගෙනියන්න ඒක ගන්නවා.
  - [NOT] before: @USER ස’ කැරකිල කැරකිල ගහන්නෙම රටවිරුවොන්ට... පව්  @USER  අයිය
  - [NOT] after:  @USER ස’ කැරකිල කැරකිල ගහන්නෙම රටවිරුවොන්ට... පව්  @USER  brother

### 3.160. `ඉස්සෙල්ල` -> `first`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඉස්සෙල්ල මේ මනුස්සයා තුරන් කරන්න කෞරුට් නැද්ද
  - [NOT] after:  @USER first මේ මනුස්සයා තුරන් කරන්න කෞරුට් නැද්ද
  - [NOT] before: @USER ඉස්සෙල්ල මේ මනුස්සයා තුරන් කරන්න කෞරුට් නැද්ද
  - [NOT] after:  @USER first මේ man තුරන් කරන්න කෞරුට් නැද්ද
  - [OFF] before: මවලා පෙන්නන්නේ  මොනවටද බොල තෝ වගේ සැබෑ පොන්නයෝ ඉන්න කොට!  ⓜⓡ.ⓩⓘⓓ @USER  · 10 Feb 2018  @USER ඒකගැන හිතන්න ඉස්සෙල්ල උඹ මුලින්ම කිව්ව ටික කල්පනා කරල බලහන් පොන්නකම් මවා පාන්න එපා
  - [OFF] after:  මවලා show  මොනවටද බොල තෝ වගේ සැබෑ පොන්නයෝ ඉන්න කොට!  ⓜⓡ.ⓩⓘⓓ @USER  · 10 Feb 2018  @USER ඒකගැන හිතන්න first උඹ මුලින්ම කිව්ව ටික කල්පනා කරල බලහන් පොන්නකම් මවා පාන්න එපා

### 3.161. `පිදුරු` -> `straw`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: බල්ලා පිදුරු කන්නෙත් නෑ කන ටිල්සිට දුන්නෙත් නෑ.  කවුද යකෝ මට බල්ලා කිව්වේ? - අමිලයියා
  - [OFF] after:  බල්ලා straw කන්නෙත් නෑ කන ටිල්සිට දුන්නෙත් නෑ.  කවුද යකෝ මට බල්ලා කිව්වේ? - අමිලයියා
  - [NOT] before: බල්ලා පිදුරු කන්නෙත් නැ කන ගොනාට දෙන්නෙත් නැති IPL Team එක තමයි RCB
  - [NOT] after:  dog straw කන්නෙත් නැ කන ගොනාට දෙන්නෙත් නැති IPL Team එක තමයි RCB
  - [OFF] before: බල්ලා පිදුරු කන්නෙත් නෑ කන ටිල්සිට දුන්නෙත් නෑ.  කවුද යකෝ මට බල්ලා කිව්වේ? - අමිලයියා
  - [OFF] after:  dog straw කන්නෙත් නෑ කන ටිල්සිට දුන්නෙත් නෑ.  කවුද යකෝ මට dog කිව්වේ? - අමිලයියා

### 3.162. `අමාරැ` -> `hard`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER එකනේ මොනා කරන්නද අමාරැ උනත් පොඩි උන් ආරක්ෂා කරගන්න ඔනනේ..මුං අපේ නිදහසත් නැති කරානේ කාලකණ්ණි
  - [OFF] after:  @USER එකනේ මොනා කරන්නද hard උනත් පොඩි උන් protect කරගන්න ඔනනේ..මුං අපේ නිදහසත් නැති කරානේ කාලකණ්ණි
  - [OFF] before: @USER ,  @USER  @USER මුන් අරින කොට තොට අමාරැ වෙනවා
  - [OFF] after:  @USER ,  @USER  @USER මුන් අරින කොට තොට hard වෙනවා
  - [OFF] before: @USER ,  @USER  @USER මුන් අරින කොට තොට අමාරැ වෙනවා
  - [OFF] after:  @USER ,  @USER  @USER මුන් අරින කොට තොට hard වෙනවා

### 3.163. `දෙන්නම` -> `both`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ඔබ හිතුවද මේ සමියා මෝඩ බවක්  ඔය තතු මම දැනගෙන දැන් බොහෝකලක්  තොපි දෙන්නම මට වැඩියෙන් නාකි උනත්  තොපිට වැඩිය ගස්... URL
  - [NOT] after:  ඔබ හිතුවද මේ සමියා මෝඩ බවක්  ඔය තතු මම දැනගෙන දැන් බොහෝකලක්  තොපි both මට වැඩියෙන් නාකි උනත්  තොපිට වැඩිය ගස්... URL
  - [NOT] before: ඔබ හිතුවද මේ සමියා මෝඩ බවක්  ඔය තතු මම දැනගෙන දැන් බොහෝකලක්  තොපි දෙන්නම මට වැඩියෙන් නාකි උනත්  තොපිට වැඩිය ගස්... URL
  - [NOT] after:  ඔබ හිතුවද මේ සමියා මෝඩ බවක්  ඔය තතු මම දැනගෙන දැන් බොහෝකලක්  තොපි both මට වැඩියෙන් නාකි උනත්  තොපිට වැඩිය ගස්... URL
  - [NOT] before: අන්න ආහරෙ සුගලා බෑදලා..තොපි දෙන්නම පලයවු මා හට වෑදලා :D :D URL
  - [NOT] after:  අන්න ආහරෙ සුගලා බෑදලා..තොපි both පලයවු මා to වෑදලා :D :D URL

### 3.164. `මැටි` -> `clay`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඔය මැටි මොල දැනන් හිට්යනම් කොරන්නේ මොකක්ද කියල අහන්න එකෙක් නෑනේ....
  - [OFF] after:  @USER ඔය clay මොල දැනන් හිට්යනම් කොරන්නේ මොකක්ද කියල අහන්න එකෙක් නෑනේ....
  - [OFF] before: @USER ඔය මැටි මොල දැනන් හිට්යනම් කොරන්නේ මොකක්ද කියල අහන්න එකෙක් නෑනේ....
  - [OFF] after:  @USER ඔය clay මොල දැනන් හිට්යනම් කොරන්නේ මොකක්ද කියල අහන්න එකෙක් නෑනේ....
  - [OFF] before: ලොම්බා ගොනා, ගොන් මෝඩයයා  මෝඩ මැටි ඌරු තඩියා
  - [OFF] after:  ලොම්බා ගොනා, ගොන් මෝඩයයා  මෝඩ clay pig තඩියා

### 3.165. `බණ` -> `sermon`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: බණ අහන්න දෙවිදේවතාවුන් වහන්සේලා  පොඩි ඉඩෙත් දාස් ගනන් රැස් උනාලු..එතකොට පුක ලොකු දේවතාවියන්ට අපහසුකම් ඇතිවෙන්න ඇති..
  - [OFF] after:  sermon අහන්න දෙවිදේවතාවුන් වහන්සේලා  පොඩි ඉඩෙත් දාස් ගනන් රැස් උනාලු..එතකොට පුක ලොකු දේවතාවියන්ට අපහසුකම් ඇතිවෙන්න ඇති..
  - [OFF] before: බණ අහන්න දෙවිදේවතාවුන් වහන්සේලා  පොඩි ඉඩෙත් දාස් ගනන් රැස් උනාලු..එතකොට පුක ලොකු දේවතාවියන්ට අපහසුකම් ඇතිවෙන්න ඇති..
  - [OFF] after:  sermon අහන්න දෙවිදේවතාවුන් වහන්සේලා  පොඩි ඉඩෙත් දාස් ගනන් රැස් උනාලු..එතකොට පුක ලොකු දේවතාවියන්ට අපහසුකම් ඇතිවෙන්න ඇති..
  - [NOT] before: @USER මේතාමත් බූදූ බණ ඇහෙන කාලයක් අබූද්දස්ස කාලයක් නෙමෙයි. මූන්ට වැඩිහිටියෝ කන් පිරෙන්න කියන්න ඕනේ. අනික් ගෑණි රුකගන්න බැරි උන්ට හිර නොදන්න බලාගන්න ඕනේ
  - [NOT] after:  @USER මේතාමත් බූදූ sermon ඇහෙන කාලයක් අබූද්දස්ස කාලයක් නෙමෙයි. මූන්ට වැඩිහිටියෝ කන් පිරෙන්න say ඕනේ. අනික් ගෑණි රුකගන්න බැරි උන්ට හිර නොදන්න බලාගන්න ඕනේ

### 3.166. `දෙනා` -> `people`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සඝ රජුට කල මෙී අපරාධයට සම්බන්ධ සියල්ලන්ටම සාප වෙීවා..... සියලු දෙවි දේවතාවන් උන්ට සාප කරත්වා..... සියලු දෙනා එක හිතින් ප්‍රාර්ථනා කරන්න....
  - [OFF] after:  සඝ රජුට කල මෙී අපරාධයට සම්බන්ධ සියල්ලන්ටම සාප වෙීවා..... සියලු god දේවතාවන් උන්ට සාප කරත්වා..... සියලු people එක හිතින් ප්‍රාර්ථනා කරන්න....
  - [NOT] before: @USER ඔය ඉන්න සිවු දෙනා ද...
  - [NOT] after:  @USER ඔය ඉන්න සිවු people ද...
  - [NOT] before: @USER ඔය ඉන්න සිවු දෙනා ද...
  - [NOT] after:  @USER ඔය ඉන්න four people ද...

### 3.167. `නාකියි` -> `old`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මම කවදාවත් හිතුවේ නෑ cricket ගහලා මෙහෙම අමාරු වෙයි කියල මාස ගානක් නිකන්ම ඉන්දලා එක පාර cricket ගැහුවා දැන් මුලු ඇගම රිදෙනවා දැන් නාකියි අපි.
  - [NOT] after:  මම කවදාවත් හිතුවේ නෑ cricket ගහලා මෙහෙම අමාරු වෙයි කියල මාස ගානක් නිකන්ම ඉන්දලා එක පාර cricket ගැහුවා දැන් මුලු ඇගම රිදෙනවා දැන් old අපි.
  - [NOT] before: මම කවදාවත් හිතුවේ නෑ cricket ගහලා මෙහෙම අමාරු වෙයි කියල මාස ගානක් නිකන්ම ඉන්දලා එක පාර cricket ගැහුවා දැන් මුලු ඇගම රිදෙනවා දැන් නාකියි අපි.
  - [NOT] after:  මම කවදාවත් හිතුවේ නෑ cricket ගහලා මෙහෙම අමාරු වෙයි කියල මාස ගානක් නිකන්ම ඉන්දලා එක පාර cricket ගැහුවා දැන් whole ඇගම රිදෙනවා දැන් old අපි.
  - [OFF] before: @USER  @USER තොපි දෙන්නම නාකියි. හූ හූ. . .  . . . . . .  . . . .  . . . . මම අනූ තුනේ ඕලෙවල්
  - [OFF] after:  @USER  @USER තොපි දෙන්නම old. හූ හූ. . .  . . . . . .  . . . .  . . . . මම ninety තුනේ ඕලෙවල්

### 3.168. `කෙලින්` -> `straight`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER දැක්කම පයිය කෙලින් උනා...
  - [OFF] after:  @USER දැක්කම පයිය straight උනා...
  - [OFF] before: @USER පයිය කෙලින් උනා කෙල්ලේ
  - [OFF] after:  @USER පයිය straight උනා girl
  - [OFF] before: @USER දැක්කම පයිය කෙලින් උනා...
  - [OFF] after:  @USER දැක්කම පයිය straight උනා...

### 3.169. `අමු` -> `raw`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ආයෙ ඉතින් මූ අමු ගවයා ඈ
  - [OFF] after:  @USER again ඉතින් මූ raw ගවයා ඈ
  - [NOT] before: එම්බල පුරෝහිත තොට අමු කැවිලද.?
  - [NOT] after:  එම්බල පුරෝහිත තොට raw කැවිලද.?
  - [NOT] before: එම්බල පුරෝහිත තොට අමු කැවිලද.?
  - [NOT] after:  එම්බල පුරෝහිත තොට raw කැවිලද.?

### 3.170. `අම්මයි` -> `mother`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තෝ දාන එ්වා අම්මයි තාත්තයි දැක්ක දවසට එ් මිනිස්සුන්ටත් හිතේවි  @USER  හරි කියල
  - [OFF] after:  @USER  @USER තෝ දාන එ්වා mother තාත්තයි දැක්ක දවසට එ් මිනිස්සුන්ටත් හිතේවි  @USER  හරි කියල
  - [OFF] before: @USER  @USER තෝ දාන එ්වා අම්මයි තාත්තයි දැක්ක දවසට එ් මිනිස්සුන්ටත් හිතේවි  @USER  හරි කියල
  - [OFF] after:  @USER  @USER තෝ දාන එ්වා mother father දැක්ක දවසට එ් මිනිස්සුන්ටත් හිතේවි  @USER  හරි කියල
  - [NOT] before: @USER මම මගෙ අම්මයි තාත්තයි හොයනව මට උදව්කරන්න කව්රැවත් මේවෙනකල් හමුඋනේනෑ පුලුවන්නම් මට උදව්කරන්න.
  - [NOT] after:  @USER මම මගෙ mother father හොයනව මට උදව්කරන්න කව්රැවත් මේවෙනකල් හමුඋනේනෑ පුලුවන්නම් මට උදව්කරන්න.

### 3.171. `පිරිමි` -> `men`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: පොන්නයෝ 3 දෙනාගේ පොන්න ජවනිකාව. චාමරට නෙවෙයි ළග පහතක හිටියනම් තොපි ගැන බලා ගන්න තිබ්බා ගොබ්බයෝ. තොපි පිරිමි... URL
  - [OFF] after:  පොන්නයෝ 3 දෙනාගේ පොන්න ජවනිකාව. චාමරට නෙවෙයි ළග පහතක හිටියනම් තොපි ගැන බලා ගන්න තිබ්බා ගොබ්බයෝ. තොපි men... URL
  - [OFF] before: පොන්නයෝ 3 දෙනාගේ පොන්න ජවනිකාව. චාමරට නෙවෙයි ළග පහතක හිටියනම් තොපි ගැන බලා ගන්න තිබ්බා ගොබ්බයෝ. තොපි පිරිමි... URL
  - [OFF] after:  පොන්නයෝ 3 දෙනාගේ පොන්න ජවනිකාව. චාමරට නෙවෙයි near පහතක හිටියනම් තොපි ගැන බලා ගන්න තිබ්බා ගොබ්බයෝ. තොපි men... URL
  - [OFF] before: @USER   ක් විතරද පිරිමි, තූ නොදකින්
  - [OFF] after:  @USER   ක් only men, තූ නොදකින්

### 3.172. `දැකල` -> `seen`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  ඇයි උඹ මීට කලින් tweet දැකල නැද්ද? නිකන් පුක නොදී පලයං මිනිහෝ :P :P
  - [OFF] after:  @USER @USER  ඇයි උඹ මීට කලින් tweet seen නැද්ද? නිකන් පුක නොදී පලයං මිනිහෝ :P :P
  - [NOT] before: @USER ඇයි උඹ වෙන කොහෙවත් බොන උන් දැකල නැද්ද
  - [NOT] after:  @USER ඇයි උඹ වෙන කොහෙවත් drink උන් seen නැද්ද
  - [OFF] before: @USER @USER  ඇයි උඹ මීට කලින් tweet දැකල නැද්ද? නිකන් පුක නොදී පලයං මිනිහෝ :P :P
  - [OFF] after:  @USER @USER  ඇයි උඹ මීට කලින් tweet seen නැද්ද? නිකන් පුක නොදී පලයං මිනිහෝ :P :P

### 3.173. `වෙලාවකට` -> `sometimes`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: එක වෙලාවකට මේ මගුලේ  #pornස්ටාර්ස්ලා විතරයි  මොලෙත් වික්ෂිප්ත වෙනවා රෙද්ද
  - [NOT] after:  එක sometimes මේ මගුලේ  #pornස්ටාර්ස්ලා විතරයි  brain වික්ෂිප්ත වෙනවා රෙද්ද
  - [NOT] before: වෙලාවකට හිතෙනවා මේ ඔක්කොම අත ඇරලා දාලා අර Facebook එකේ cooking vidoes කරන Azerbarjani couple එකේ බල්ලා වෙන්න තියනවානම් කියලා
  - [NOT] after:  sometimes හිතෙනවා මේ ඔක්කොම අත ඇරලා දාලා අර Facebook එකේ cooking vidoes කරන Azerbarjani couple එකේ බල්ලා වෙන්න තියනවානම් කියලා
  - [NOT] before: වෙලාවකට හිතෙනවා මේ ඔක්කොම අත ඇරලා දාලා අර Facebook එකේ cooking vidoes කරන Azerbarjani couple එකේ බල්ලා වෙන්න තියනවානම් කියලා
  - [NOT] after:  sometimes හිතෙනවා මේ ඔක්කොම අත ඇරලා දාලා අර Facebook එකේ cooking vidoes කරන Azerbarjani couple එකේ dog වෙන්න තියනවානම් කියලා

### 3.174. `ඉතාමත්` -> `very`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඉතාමත් ඉහලින් සමත් වු බැවින් විභාග කොමසාරිස් ඉල්ලා අස් විය.
  - [NOT] after:  @USER very ඉහලින් සමත් වු බැවින් විභාග කොමසාරිස් ඉල්ලා අස් විය.
  - [OFF] before: @USER ඉතාමත් නිවැරදියි.මහත්මයෙක් හා ගොබ්බයෙක් අතර සටනකින් මහත්මයා දිනුවා.එච්චරයි.
  - [OFF] after:  @USER very නිවැරදියි.මහත්මයෙක් හා ගොබ්බයෙක් අතර සටනකින් gentleman දිනුවා.එච්චරයි.
  - [NOT] before: @USER ඉතාමත් ඉහලින් සමත් වු බැවින් විභාග කොමසාරිස් ඉල්ලා අස් විය.
  - [NOT] after:  @USER very ඉහලින් සමත් වු since විභාග කොමසාරිස් ඉල්ලා අස් විය.

### 3.175. `දෙකයි` -> `two`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අද නම් ටික්ක අමාරු දවසක්,  තුවාල දෙකයි..
  - [NOT] after:  අද නම් ටික්ක අමාරු දවසක්,  wounds two..
  - [OFF] before: @USER @USER  මට අනුව ටුයිටරය වර්ග දෙකයි අෙප හාමුදුරුවනේ...එකක් පුක දෙන අය අනික් අය පුක නොදෙන අය..
  - [OFF] after:  @USER @USER  මට අනුව ටුයිටරය වර්ග two අෙප හාමුදුරුවනේ...එකක් පුක දෙන අය අනික් අය පුක නොදෙන අය..
  - [OFF] before: @USER @USER  මට අනුව ටුයිටරය වර්ග දෙකයි අෙප හාමුදුරුවනේ...එකක් පුක දෙන අය අනික් අය පුක නොදෙන අය..
  - [OFF] after:  @USER @USER  මට අනුව ටුයිටරය types two අෙප හාමුදුරුවනේ...එකක් පුක දෙන අය අනික් අය පුක නොදෙන අය..

### 3.176. `අඩුයි` -> `low`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  සංශෝධනයට එරෙහිවත් හිටියෙ මේ අයම නේද...විජේදාස රාජපක්ෂ අඩුයි වගේ..!
  - [NOT] after:  @USER  සංශෝධනයට එරෙහිවත් හිටියෙ මේ අයම නේද...විජේදාස රාජපක්ෂ low වගේ..!
  - [NOT] before: @USER  සංශෝධනයට එරෙහිවත් හිටියෙ මේ අයම නේද...විජේදාස රාජපක්ෂ අඩුයි වගේ..!
  - [NOT] after:  @USER  සංශෝධනයට against හිටියෙ මේ අයම නේද...විජේදාස රාජපක්ෂ low වගේ..!
  - [NOT] before: @USER  ඒම කියන්න එපා.. ඔයාලට සාපේක්ශව අපේ අඩුයි ඩාලින්‍
  - [NOT] after:  @USER  ඒම say එපා.. ඔයාලට සාපේක්ශව අපේ low ඩාලින්‍

### 3.177. `තමුසෙලා` -> `you all`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අයිසෙ තමුසෙලා මාධ්‍යවේදීන් නෙමෙයි ඕයි &#8211; මාධ්‍යවේදියකුට කිරිඇල්ල තග දායි URL
  - [NOT] after:  අයිසෙ you all මාධ්‍යවේදීන් නෙමෙයි ඕයි &#8211; මාධ්‍යවේදියකුට කිරිඇල්ල තග දායි URL
  - [OFF] before: @USER  @USER අනේ යකෝ. කෙල වෙලා තියෙන්නෙ වෙන කවිරුත් හින්ද නෙමෙයි තමුසෙලා වගේ ගොන්නු හින්දා. හැම ප්‍රශ්නෙම අනුන්ගෙ පිට දාන්නැතුව තමුන් හැදෙන්න බලපන්. මෝඩ ගෙම්බා..
  - [OFF] after:  @USER  @USER අනේ යකෝ. කෙල වෙලා තියෙන්නෙ වෙන කවිරුත් because නෙමෙයි you all වගේ ගොන්නු හින්දා. හැම ප්‍රශ්නෙම අනුන්ගෙ පිට දාන්නැතුව තමුන් හැදෙන්න බලපන්. මෝඩ ගෙම්බා..
  - [NOT] before: අයිසෙ තමුසෙලා මාධ්‍යවේදීන් නෙමෙයි ඕයි &#8211; මාධ්‍යවේදියකුට කිරිඇල්ල තග දායි URL
  - [NOT] after:  අයිසෙ you all මාධ්‍යවේදීන් නෙමෙයි ඕයි &#8211; මාධ්‍යවේදියකුට කිරිඇල්ල තග දායි URL

### 3.178. `පුල්ලි` -> `spotted`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓  පුල්ලි ගොනා පුරුදුකාරයා මම ජෙමා කරත්තකාරයා  අහල තියෙනවනේ  මේකෙ මේ ජෙමා... URL
  - [NOT] after:  ░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓  spotted ගොනා පුරුදුකාරයා මම ජෙමා කරත්තකාරයා  අහල තියෙනවනේ  මේකෙ මේ ජෙමා... URL
  - [NOT] before: පුල්ලි ගොනා පුරුදු කාරයා මම ගොනා කරත්ත කාරයා #MisheardSinhalaLyrics
  - [NOT] after:  spotted ගොනා පුරුදු කාරයා මම ගොනා cart කාරයා #MisheardSinhalaLyrics
  - [NOT] before: ░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓  පුල්ලි ගොනා පුරුදුකාරයා මම ජෙමා කරත්තකාරයා  අහල තියෙනවනේ  මේකෙ මේ ජෙමා... URL
  - [NOT] after:  ░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓  spotted ගොනා පුරුදුකාරයා මම ජෙමා cart man  අහල තියෙනවනේ  මේකෙ මේ ජෙමා... URL

### 3.179. `ගියෙ` -> `went`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: #නොදකින් මොන මගුලකටද මුන් ගියෙ.....
  - [OFF] after:  #නොදකින් මොන මගුලකටද මුන් went.....
  - [OFF] before: #නොදකින් මොන මගුලකටද මුන් ගියෙ.....
  - [OFF] after:  #නොදකින් මොන මගුලකටද මුන් went.....
  - [NOT] before: @USER ගනේමුල්ල කොහෙද ගියෙ බොල..
  - [NOT] after:  @USER Ganemulla කොහෙද went බොල..

### 3.180. `කෙනා` -> `person`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  ඔව් ඔව්.... DP එකෙ හිටපු කෙනා නෙමෙ නේ  කොන්ඩෙ ගොතලා සායක් ඇදලා... ගැමිකම වැක්කෙරෙනවා  @USER  නේ බොල
  - [NOT] after:  @USER @USER  ඔව් ඔව්.... DP එකෙ හිටපු person නෙමෙ නේ  කොන්ඩෙ ගොතලා සායක් ඇදලා... ගැමිකම වැක්කෙරෙනවා  @USER  නේ බොල
  - [NOT] before: @USER @USER  ඔව් ඔව්.... DP එකෙ හිටපු කෙනා නෙමෙ නේ  කොන්ඩෙ ගොතලා සායක් ඇදලා... ගැමිකම වැක්කෙරෙනවා  @USER  නේ බොල
  - [NOT] after:  @USER @USER  ඔව් ඔව්.... DP එකෙ හිටපු person නෙමෙ නේ  hair ගොතලා සායක් ඇදලා... ගැමිකම වැක්කෙරෙනවා  @USER  නේ බොල
  - [NOT] before: @USER  ඒ මනුස්සයා මොනව කරන්නද ,නියෝග දුන්න කෙනා කෝ
  - [NOT] after:  @USER  ඒ man මොනව කරන්නද ,නියෝග දුන්න person කෝ

### 3.181. `කොහෙවත්` -> `anywhere`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කොහෙවත් යන ගොන් ලොංත කාලකන්නි කැරි බල්ලෙක් මල පැන්නුව. ශැක්. දැන් කන පැලෙන්න ගහනකන් තරහ නිවෙන්නෙ නෑ.
  - [OFF] after:  anywhere යන ගොන් ලොංත කාලකන්නි කැරි බල්ලෙක් මල පැන්නුව. ශැක්. දැන් කන පැලෙන්න ගහනකන් angry නිවෙන්නෙ නෑ.
  - [OFF] before: @USER අනේ පොන්න පකෝ මට කොහෙවත් නැති එකියක්ට හුකන්න ඕන නෑ.... තොට මුනට කිව්වා වගේ තාමා මේම දැම්මාම... එක පුක ඉරාගෙන දගලන්නේ ගෝතයා...
  - [OFF] after:  @USER අනේ පොන්න පකෝ මට anywhere නැති එකියක්ට හුකන්න ඕන නෑ.... තොට මුනට කිව්වා වගේ තාමා මේම දැම්මාම... එක පුක ඉරාගෙන දගලන්නේ ගෝතයා...
  - [OFF] before: @USER අනේ පොන්න පකෝ මට කොහෙවත් නැති එකියක්ට හුකන්න ඕන නෑ.... තොට මුනට කිව්වා වගේ තාමා මේම දැම්මාම... එක පුක ඉරාගෙන දගලන්නේ ගෝතයා...
  - [OFF] after:  @USER අනේ පොන්න පකෝ මට anywhere නැති එකියක්ට හුකන්න ඕන නෑ.... තොට මුනට කිව්වා වගේ තාමා මේම දැම්මාම... එක පුක ඉරාගෙන දගලන්නේ ගෝතයා...

### 3.182. `ගරු` -> `respect`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: යම් වෘත්තියක අවශ්‍යතාවය තමන්ට නැතිනම් එම වෘත්තියට ගරු කිරීමට ඉගෙන ගත් යුතු යි....  රූපලාවන්‍ය වෘත්තීය යනු එක එකාට රෙද්ද ඉස්සීම නොවන වග කවුරු කවුරුත් තේරුම් ගත යුතුය... Dilan @USER  · 18 May 2021 Comment එකහ් ....
  - [NOT] after:  යම් වෘත්තියක අවශ්‍යතාවය තමන්ට නැතිනම් එම වෘත්තියට respect කිරීමට ඉගෙන ගත් යුතු යි....  රූපලාවන්‍ය වෘත්තීය යනු එක එකාට රෙද්ද ඉස්සීම නොවන වග කවුරු කවුරුත් understand ගත යුතුය... Dilan @USER  · 18 May 2021 Comment එකහ් ....
  - [OFF] before: @USER @USER  පුක් චාරය -_- මුන් පුක උස්සලා ගරු කරන්නේ
  - [OFF] after:  @USER @USER  පුක් චාරය -_- මුන් පුක උස්සලා respect කරන්නේ
  - [OFF] before: @USER @USER  පුක් චාරය -_- මුන් පුක උස්සලා ගරු කරන්නේ
  - [OFF] after:  @USER @USER  පුක් චාරය -_- මුන් පුක උස්සලා respect කරන්නේ

### 3.183. `හෝ` -> `or`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER එන්නද කොය්ද හදන්නෙ......හෆ්...හෝ...........ය් GIF
  - [NOT] after:  @USER එන්නද කොය්ද හදන්නෙ......හෆ්...or...........ය් GIF
  - [NOT] before: එළුවා දිනයිද.. නැත්තන් හරකා පරාද වෙයිද  ෂා FM 90.9න් හෝ 91.1න් දිවයින පුරා.. URL
  - [NOT] after:  එළුවා දිනයිද.. නැත්තන් හරකා defeat වෙයිද  ෂා FM 90.9න් or 91.1න් දිවයින පුරා.. URL
  - [NOT] before: @USER එන්නද කොය්ද හදන්නෙ......හෆ්...හෝ...........ය් GIF
  - [NOT] after:  @USER එන්නද කොය්ද හදන්නෙ......හෆ්...or...........ය් GIF

### 3.184. `ඉස්සෙල්ලා` -> `first`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER    අඩො උඹ කිව්වේ ඉස්සෙල්ලා
  - [NOT] after:  @USER  @USER    අඩො උඹ කිව්වේ first
  - [NOT] before: @USER උංගෙ මර්ධනය කරගෙන ඉන්ට කියපිය ඉස්සෙල්ලා
  - [NOT] after:  @USER their මර්ධනය කරගෙන ඉන්ට කියපිය first
  - [NOT] before: @USER  @USER    අඩො උඹ කිව්වේ ඉස්සෙල්ලා
  - [NOT] after:  @USER  @USER    අඩො උඹ කිව්වේ first

### 3.185. `ඉස්සෙල්ලාම` -> `first`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ඉස්සෙල්ලාම දුන්න පෙම්හසුනට ලැබුන ප්‍රතිචාරය තමයි. බූරුවා හරකා මට වදදෙන්නෙ නැතුව ඉන්න කියන ඒවා #පෙම්හසුන්_කතා
  - [OFF] after:  first දුන්න පෙම්හසුනට ලැබුන ප්‍රතිචාරය තමයි. බූරුවා හරකා මට වදදෙන්නෙ නැතුව ඉන්න කියන ඒවා #පෙම්හසුන්_කතා
  - [OFF] before: ඉස්සෙල්ලාම දුන්න පෙම්හසුනට ලැබුන ප්‍රතිචාරය තමයි. බූරුවා හරකා මට වදදෙන්නෙ නැතුව ඉන්න කියන ඒවා #පෙම්හසුන්_කතා
  - [OFF] after:  first දුන්න පෙම්හසුනට ලැබුන ප්‍රතිචාරය තමයි. බූරුවා හරකා මට වදදෙන්නෙ නැතුව ඉන්න කියන ඒවා #පෙම්හසුන්_talk
  - [NOT] before: පිට රටින් එන හැම විදේස නියෝජිතයෙක්ම ඉස්සෙල්ලාම යන්නේ උතුරේ ^_^  යකෝ වරෙන්කො සබරගමුවට රෙද්ද අපි වේලෙනවා -_-   #prayforsrilanka  :3
  - [NOT] after:  back රටින් එන හැම විදේස නියෝජිතයෙක්ම first යන්නේ උතුරේ ^_^  යකෝ වරෙන්කො සබරගමුවට රෙද්ද අපි වේලෙනවා -_-   #prayforsrilanka  :3

### 3.186. `ඇතුලෙ` -> `inside`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: යකෝ මේ පැය විසි හතරට නානෙව අමතක වුනාද? ඌ තාම ඇතුලෙ යකූ. කෝ අපේ බහුජ්ජයො?
  - [OFF] after:  යකෝ මේ පැය විසි හතරට නානෙව අමතක වුනාද? ඌ තාම inside යකූ. කෝ අපේ බහුජ්ජයො?
  - [NOT] before: @USER Reply නෑ. වරහන් ඇතුලෙ කෑල්ල තිබ්බෙ නැත්නම් බලන්න තිබ්බ මෙතන.
  - [NOT] after:  @USER Reply නෑ. වරහන් inside girl තිබ්බෙ නැත්නම් බලන්න තිබ්බ මෙතන.
  - [OFF] before: යකෝ මේ පැය විසි හතරට නානෙව අමතක වුනාද? ඌ තාම ඇතුලෙ යකූ. කෝ අපේ බහුජ්ජයො?
  - [OFF] after:  යකෝ මේ පැය විසි හතරට නානෙව අමතක වුනාද? ඌ still inside යකූ. කෝ අපේ බහුජ්ජයො?

### 3.187. `කුකුලා` -> `chicken`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හරකා එලුවා කුකුලා ඔක්කොම එහෙම තමා දැන්
  - [NOT] after:  @USER හරකා එලුවා chicken ඔක්කොම එහෙම තමා දැන්
  - [NOT] before: @USER හරකා එලුවා කුකුලා ඔක්කොම එහෙම තමා දැන්
  - [NOT] after:  @USER හරකා goat chicken ඔක්කොම එහෙම තමා දැන්
  - [NOT] before: හරකා ඌරා කුකුලා කියන්නෙ වඳවෙන සත්තුත් නෙමේ  උන්ව කන්නෙ අවිහිංසාවාදී දහමේ නමිනුත් නෙමේ  ඒ නිසා ඒක සත්ත්ව හිංසාවට... URL
  - [NOT] after:  හරකා pig chicken කියන්නෙ වඳවෙන සත්තුත් නෙමේ  උන්ව කන්නෙ අවිහිංසාවාදී දහමේ නමිනුත් නෙමේ  ඒ නිසා ඒක සත්ත්ව හිංසාවට... URL

### 3.188. `දින්නා` -> `won`
- impact: 3 posts (1 light, 2 heavy), 0 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අපි දින්නා යකෝ අපි දින්නා කියහන්කෝ #SAvSL
  - [NOT] after:  අපි won යකෝ අපි won කියහන්කෝ #SAvSL
  - [NOT] before: අපි දින්නා යකෝ අපි දින්නා කියහන්කෝ #SAvSL
  - [NOT] after:  අපි won යකෝ අපි won කියහන්කෝ #SAvSL
  - [NOT] before: @USER @USER  අඩො උන් පැරදුනා ද ? අඩෝ මන් හිතුවේ උන් ඉයියේ දින්නා කියලා. දැන් නේ මතක් උනේ අද April Fools Day නේ
  - [NOT] after:  @USER @USER  අඩො උන් පැරදුනා ද ? අඩෝ මන් හිතුවේ උන් yesterday won කියලා. දැන් නේ මතක් උනේ අද April Fools Day නේ

### 3.189. `පොකුරු` -> `bunch`
- impact: 3 posts (1 light, 2 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER පැණි පොකුරු පොකුරු ඔබ යන කල ඔබ දෙසටම නැමීයන්... මම කාලි
  - [NOT] after:  @USER honey bunch bunch ඔබ යන කල ඔබ දෙසටම නැමීයන්... මම කාලි
  - [OFF] before: @USER උගෙ අම්මගෙ රෙද්ද බෝ වුන උන්ද එතකොට මේ පොකුරු පිටින් අහුවෙන්නෙ
  - [OFF] after:  @USER උගෙ අම්මගෙ රෙද්ද බෝ වුන උන්ද එතකොට මේ bunch පිටින් අහුවෙන්නෙ
  - [OFF] before: @USER උගෙ අම්මගෙ රෙද්ද බෝ වුන උන්ද එතකොට මේ පොකුරු පිටින් අහුවෙන්නෙ
  - [OFF] after:  @USER උගෙ අම්මගෙ රෙද්ද බෝ වුන උන්ද එතකොට මේ bunch පිටින් අහුවෙන්නෙ

### 3.190. `රිලවා` -> `monkey`
- impact: 3 posts (1 light, 2 heavy), 3 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ඌරා හරකා ගෙම්බා වඳුරා නරියා හැලි වඳුරා හැල ගෙම්බා ගස් රිලවා I hate you
  - [OFF] after:  ඌරා හරකා frog වඳුරා නරියා හැලි වඳුරා හැල frog ගස් monkey I hate you
  - [OFF] before: @USER කෝ අර නාකි රිලවා
  - [OFF] after:  @USER කෝ අර නාකි monkey
  - [OFF] before: @USER කෝ අර නාකි රිලවා
  - [OFF] after:  @USER කෝ අර නාකි monkey

### 3.191. `හීන` -> `dreams`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 5 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අම්බලමේ පිනා  අම්බලමේ          පිනා  වලං කදක්      ගෙනා එක බිදපි       ගොනා එකට මට         හිනා  හුරුබුහුටිට      මනා තෝඩු දෙකක්    තම හිතේ හීන        තනා අම්බලමේ         පින  පිනාගේ පොඩි   ළමා මිදුලට දුව         එනා බිදුනු හීන          බලා කද ළග ගොලු   වුනා
  - [NOT] after:  අම්බලමේ පිනා  අම්බලමේ          පිනා  වලං කදක්      ගෙනා එක බිදපි       ගොනා එකට මට         හිනා  හුරුබුහුටිට      මනා තෝඩු දෙකක්    තම හිතේ dreams        තනා අම්බලමේ         පින  පිනාගේ පොඩි   ළමා මිදුලට දුව         එනා බිදුනු dreams          බලා කද ළග ගොලු   වුනා
  - [NOT] before: අම්බලමේ පිනා  අම්බලමේ          පිනා  වලං කදක්      ගෙනා එක බිදපි       ගොනා එකට මට         හිනා  හුරුබුහුටිට      මනා තෝඩු දෙකක්    තම හිතේ හීන        තනා අම්බලමේ         පින  පිනාගේ පොඩි   ළමා මිදුලට දුව         එනා බිදුනු හීන          බලා කද ළග ගොලු   වුනා
  - [NOT] after:  අම්බලමේ පිනා  අම්බලමේ          පිනා  වලං කදක්      ගෙනා එක බිදපි       ගොනා එකට මට         හිනා  හුරුබුහුටිට      මනා තෝඩු දෙකක්    තම හිතේ dreams        තනා අම්බලමේ         පින  පිනාගේ පොඩි   child මිදුලට දුව         එනා බිදුනු dreams          බලා කද ළග ගොලු   වුනා
  - [OFF] before: Dear Sri Lanka Cricket Fan  අනේ නිකන් වැඩක් බලන් පලයන් යන්න...හීන දකින්නෙ නැතුව.. ᴳᵃᵛᵉᵉⁿ @USER  · 25 May 2018 Dear Sri Lankan Cricket team, Please ImproveLet's kick India out from the next World Cup.
  - [OFF] after:  Dear Sri Lanka Cricket Fan  අනේ නිකන් work බලන් පලයන් යන්න...dreams දකින්නෙ නැතුව.. ᴳᵃᵛᵉᵉⁿ @USER  · 25 May 2018 Dear Sri Lankan Cricket team, Please ImproveLet's kick India out from the next World Cup.

### 3.192. `යටින්` -> `below`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අද vet එකට ආපු ඇල්ටේශන් mega size බල්ලා. ආච්චි කෙනෙක් එක්ක ආපු වල් බල්ලා එක පාරයි බිරුවෙ නැට්ටත් පස්සේ ගහගෙන හැංගුණා කියන්නකො    . . . මේ යටින් ඉන්න ඒ වල් බලුස්
  - [NOT] after:  අද vet එකට ආපු ඇල්ටේශන් mega size බල්ලා. ආච්චි කෙනෙක් එක්ක ආපු වල් බල්ලා එක පාරයි බිරුවෙ නැට්ටත් පස්සේ ගහගෙන හැංගුණා කියන්නකො    . . . මේ below ඉන්න ඒ වල් බලුස්
  - [OFF] before: මේකට උඩින් tweet එක දාපු එකා හරකා. යටින් දාපු එකා බූරුවා.
  - [OFF] after:  මේකට above tweet එක දාපු එකා හරකා. below දාපු එකා බූරුවා.
  - [NOT] before: අද vet එකට ආපු ඇල්ටේශන් mega size බල්ලා. ආච්චි කෙනෙක් එක්ක ආපු වල් බල්ලා එක පාරයි බිරුවෙ නැට්ටත් පස්සේ ගහගෙන හැංගුණා කියන්නකො    . . . මේ යටින් ඉන්න ඒ වල් බලුස්
  - [NOT] after:  අද vet එකට ආපු ඇල්ටේශන් mega size බල්ලා. ආච්චි කෙනෙක් එක්ක ආපු wild බල්ලා එක පාරයි බිරුවෙ නැට්ටත් පස්සේ ගහගෙන හැංගුණා කියන්නකො    . . . මේ below ඉන්න ඒ wild බලුස්

### 3.193. `තාත්තයි` -> `father`
- impact: 3 posts (1 light, 2 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තෝ දාන එ්වා අම්මයි තාත්තයි දැක්ක දවසට එ් මිනිස්සුන්ටත් හිතේවි  @USER  හරි කියල
  - [OFF] after:  @USER  @USER තෝ දාන එ්වා mother father දැක්ක දවසට එ් මිනිස්සුන්ටත් හිතේවි  @USER  හරි කියල
  - [NOT] before: @USER මම මගෙ අම්මයි තාත්තයි හොයනව මට උදව්කරන්න කව්රැවත් මේවෙනකල් හමුඋනේනෑ පුලුවන්නම් මට උදව්කරන්න.
  - [NOT] after:  @USER මම මගෙ අම්මයි father හොයනව මට උදව්කරන්න කව්රැවත් මේවෙනකල් හමුඋනේනෑ පුලුවන්නම් මට උදව්කරන්න.
  - [NOT] before: @USER මම මගෙ අම්මයි තාත්තයි හොයනව මට උදව්කරන්න කව්රැවත් මේවෙනකල් හමුඋනේනෑ පුලුවන්නම් මට උදව්කරන්න.
  - [NOT] after:  @USER මම මගෙ mother father හොයනව මට උදව්කරන්න කව්රැවත් මේවෙනකල් හමුඋනේනෑ පුලුවන්නම් මට උදව්කරන්න.

### 3.194. `ස්ත්‍රී` -> `female`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER අනිත් උන් ස්ත්‍රී සැප ලබද්දී මම මේ උඩ බලන් ඉන්නෙම හුත්තී..
  - [OFF] after:  @USER අනිත් උන් female සැප ලබද්දී මම මේ උඩ බලන් ඉන්නෙම හුත්තී..
  - [OFF] before: @USER අනිත් උන් ස්ත්‍රී සැප ලබද්දී මම මේ උඩ බලන් ඉන්නෙම හුත්තී..
  - [OFF] after:  @USER other උන් female සැප ලබද්දී මම මේ උඩ බලන් ඉන්නෙම හුත්තී..

### 3.195. `දඩ` -> `fine`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER දඩ මාධ්‍යවලින් කොහොමටත් කරන්න හැමදාම බොරුවට මිනිස්සුන්ව බය කරන එක ඒ මනුස්සයා එහෙම කියලා හරි මිනිස්සුන්ගෙ හිත්වල තියෙන බය නැති කෙරුවා.. ජඩමාධ්‍ය කාරයෝ දැන් ඒක විහිළුවට අරගෙන
  - [NOT] after:  @USER fine මාධ්‍යවලින් කොහොමටත් කරන්න හැමදාම බොරුවට මිනිස්සුන්ව බය කරන එක ඒ මනුස්සයා එහෙම කියලා හරි මිනිස්සුන්ගෙ හිත්වල තියෙන බය නැති කෙරුවා.. ජඩමාධ්‍ය කාරයෝ දැන් ඒක විහිළුවට අරගෙන
  - [NOT] before: @USER දඩ මාධ්‍යවලින් කොහොමටත් කරන්න හැමදාම බොරුවට මිනිස්සුන්ව බය කරන එක ඒ මනුස්සයා එහෙම කියලා හරි මිනිස්සුන්ගෙ හිත්වල තියෙන බය නැති කෙරුවා.. ජඩමාධ්‍ය කාරයෝ දැන් ඒක විහිළුවට අරගෙන
  - [NOT] after:  @USER fine මාධ්‍යවලින් කොහොමටත් කරන්න හැමදාම බොරුවට මිනිස්සුන්ව බය කරන එක ඒ man එහෙම කියලා හරි මිනිස්සුන්ගෙ හිත්වල තියෙන බය නැති කෙරුවා.. ජඩමාධ්‍ය කාරයෝ දැන් ඒක විහිළුවට අරගෙන

### 3.196. `ගොවි` -> `farmer`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ගොවි අරගලයට බේහේත් දේනවා වාගේ....
  - [NOT] after:  @USER farmer අරගලයට බේහේත් දේනවා like....
  - [NOT] before: අයිසෙ මහත්තයා, දන් නැත්නම් පොඩ්ඩක් ඇස් ඇරලා බලාගන්න  @USER    තේකක් බීලා ඉන්නෙ නැතිව යනවා ගොවි අරගල බලන්න
  - [NOT] after:  අයිසෙ මහත්තයා, දන් නැත්නම් පොඩ්ඩක් ඇස් ඇරලා බලාගන්න  @USER    තේකක් drunk ඉන්නෙ නැතිව යනවා farmer අරගල බලන්න

### 3.197. `පාටයි` -> `colour`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER මොකෙක්ද මේ? සමනල් පාටයි යකෝ..
  - [OFF] after:  @USER  @USER මොකෙක්ද මේ? සමනල් colour යකෝ..
  - [OFF] before: @USER  @USER මොකෙක්ද මේ? සමනල් පාටයි යකෝ..
  - [OFF] after:  @USER  @USER මොකෙක්ද මේ? සමනල් colour යකෝ..

### 3.198. `පරාද` -> `defeat`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: එළුවා දිනයිද.. නැත්තන් හරකා පරාද වෙයිද  ෂා FM 90.9න් හෝ 91.1න් දිවයින පුරා.. URL
  - [NOT] after:  එළුවා දිනයිද.. නැත්තන් හරකා defeat වෙයිද  ෂා FM 90.9න් හෝ 91.1න් දිවයින පුරා.. URL
  - [NOT] before: එළුවා දිනයිද.. නැත්තන් හරකා පරාද වෙයිද  ෂා FM 90.9න් හෝ 91.1න් දිවයින පුරා.. URL
  - [NOT] after:  එළුවා දිනයිද.. නැත්තන් හරකා defeat වෙයිද  ෂා FM 90.9න් or 91.1න් දිවයින පුරා.. URL

### 3.199. `බාල` -> `junior`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ටහුඩු , බාල බඩු එහෙනම්
  - [NOT] after:  @USER ටහුඩු , junior බඩු එහෙනම්
  - [NOT] before: @USER ටහුඩු , බාල බඩු එහෙනම්
  - [NOT] after:  @USER ටහුඩු , junior stuff එහෙනම්

### 3.200. `මාතෘ` -> `mother`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER  @USER  @USER  @USER  @USER  @USER   කවුද මේ හූල් කියන්නේ ... දේශදොහියෙකි URL අප මාතෘ භුමිය විනාශ කිරිමට මාන බලන LTTE මහා මොලකරැය
  - [NOT] after:  @USER  @USER  @USER  @USER  @USER  @USER  @USER   කවුද මේ හූල් කියන්නේ ... දේශදොහියෙකි URL අප mother භුමිය විනාශ කිරිමට මාන බලන LTTE මහා මොලකරැය
  - [NOT] before: @USER  @USER  @USER  @USER  @USER  @USER  @USER   කවුද මේ හූල් කියන්නේ ... දේශදොහියෙකි URL අප මාතෘ භුමිය විනාශ කිරිමට මාන බලන LTTE මහා මොලකරැය
  - [NOT] after:  @USER  @USER  @USER  @USER  @USER  @USER  @USER   කවුද මේ හූල් කියන්නේ ... දේශදොහියෙකි URL අප mother භුමිය destroy කිරිමට මාන බලන LTTE මහා මොලකරැය

### 3.201. `බැන්ද` -> `married`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඒකි බැන්ද නම් උඹව දරුකමට ගන්න තරම් උඹට වඩා ලොකුයි.
  - [NOT] after:  @USER ඒකි married නම් උඹව දරුකමට ගන්න තරම් උඹට වඩා ලොකුයි.
  - [NOT] before: @USER ඒකි බැන්ද නම් උඹව දරුකමට ගන්න තරම් උඹට වඩා ලොකුයි.
  - [NOT] after:  @USER ඒකි married නම් උඹව දරුකමට ගන්න තරම් උඹට වඩා big.

### 3.202. `දොර` -> `door`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: රෙද්ද තමයි. ඔය දොර ඇරගෙන වෙන මොකෙක් හරි එකෙක් ඇතුලට ගිහිල්ල එළියටත් ඇවිල්ල ඉඳීවි
  - [NOT] after:  රෙද්ද තමයි. ඔය door ඇරගෙන වෙන මොකෙක් හරි එකෙක් ඇතුලට ගිහිල්ල එළියටත් ඇවිල්ල ඉඳීවි
  - [NOT] before: රෙද්ද තමයි. ඔය දොර ඇරගෙන වෙන මොකෙක් හරි එකෙක් ඇතුලට ගිහිල්ල එළියටත් ඇවිල්ල ඉඳීවි
  - [NOT] after:  රෙද්ද තමයි. ඔය door ඇරගෙන වෙන මොකෙක් හරි එකෙක් inside ගිහිල්ල එළියටත් ඇවිල්ල ඉඳීවි

### 3.203. `අප්පච්චි` -> `father`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER එයා අප්පච්චි... මෙයා පියා.....
  - [NOT] after:  @USER එයා father... මෙයා පියා.....
  - [NOT] before: @USER එයා අප්පච්චි... මෙයා පියා.....
  - [NOT] after:  @USER එයා father... මෙයා father.....

### 3.204. `ගනේමුල්ල` -> `Ganemulla`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ගනේමුල්ල කොහෙද ගියෙ බොල..
  - [NOT] after:  @USER Ganemulla කොහෙද ගියෙ බොල..
  - [NOT] before: @USER ගනේමුල්ල කොහෙද ගියෙ බොල..
  - [NOT] after:  @USER Ganemulla කොහෙද went බොල..

### 3.205. `දකුණේ` -> `south`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔය වගේ දකුණේ ඒවටත් පලකො...
  - [NOT] after:  @USER ඔය වගේ south ඒවටත් පලකො...
  - [NOT] before: @USER ඔය වගේ දකුණේ ඒවටත් පලකො...
  - [NOT] after:  @USER ඔය වගේ south ඒවටත් පලකො...

### 3.206. `මඩුශාන්` -> `Madushan`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මොකාද් හුත්ත නිසල් මඩුශාන් කියන්නෙ
  - [OFF] after:  මොකාද් හුත්ත නිසල් Madushan කියන්නෙ
  - [OFF] before: මොකාද් හුත්ත නිසල් මඩුශාන් කියන්නෙ
  - [OFF] after:  මොකාද් හුත්ත නිසල් Madushan කියන්නෙ

### 3.207. `හොදයිනෙ` -> `good`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඒක ඒකාලෙම කරා නම් හොදයිනෙ...
  - [NOT] after:  @USER ඒක ඒකාලෙම කරා නම් good...
  - [NOT] before: @USER ඒක ඒකාලෙම කරා නම් හොදයිනෙ...
  - [NOT] after:  @USER ඒක ඒකාලෙම කරා නම් good...

### 3.208. `දෙබලක` -> `fork`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER ඇරපන් ගස් දෙබලක පොන්න හුත්තා ,,  @USER
  - [OFF] after:  @USER @USER ඇරපන් ගස් fork පොන්න හුත්තා ,,  @USER
  - [OFF] before: @USER @USER ඇරපන් ගස් දෙබලක පොන්න හුත්තා ,,  @USER
  - [OFF] after:  @USER @USER ඇරපන් ගස් fork පොන්න හුත්තා ,,  @USER

### 3.209. `ගෙනාපු` -> `brought`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඒපා මිනිහෝ.. Twitter එකේ ආදායමත් වැටිල තියෙන වෙලාවක උඹ මොකද්ද මේ කරන්න හදන්නෙ..?? අඩො.. ගෙනාපු චොක්ලට් ඉවරද ??
  - [NOT] after:  @USER ඒපා මිනිහෝ.. Twitter එකේ ආදායමත් වැටිල තියෙන වෙලාවක උඹ මොකද්ද මේ කරන්න හදන්නෙ..?? අඩො.. brought චොක්ලට් ඉවරද ??
  - [NOT] before: @USER ඒපා මිනිහෝ.. Twitter එකේ ආදායමත් වැටිල තියෙන වෙලාවක උඹ මොකද්ද මේ කරන්න හදන්නෙ..?? අඩො.. ගෙනාපු චොක්ලට් ඉවරද ??
  - [NOT] after:  @USER ඒපා මිනිහෝ.. Twitter එකේ ආදායමත් වැටිල තියෙන වෙලාවක උඹ මොකද්ද මේ කරන්න හදන්නෙ..?? අඩො.. brought චොක්ලට් ඉවරද ??

### 3.210. `කිහිප` -> `few`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER නැත ඔහු මෙලොව වසනා කාලකණ්ණි කිහිප දෙනාගෙන් එකෙකි
  - [NOT] after:  @USER නැත ඔහු මෙලොව වසනා කාලකණ්ණි few දෙනාගෙන් එකෙකි
  - [NOT] before: @USER නැත ඔහු මෙලොව වසනා කාලකණ්ණි කිහිප දෙනාගෙන් එකෙකි
  - [NOT] after:  @USER නැත ඔහු මෙලොව වසනා කාලකණ්ණි few දෙනාගෙන් එකෙකි

### 3.211. `කැලණියෙ` -> `Kelaniya`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කැලණියෙ 1500-1750, ඒකත් 5 දෙන්නෙ
  - [NOT] after:  @USER Kelaniya 1500-1750, ඒකත් 5 දෙන්නෙ
  - [NOT] before: @USER කැලණියෙ 1500-1750, ඒකත් 5 දෙන්නෙ
  - [NOT] after:  @USER Kelaniya 1500-1750, ඒකත් 5 දෙන්නෙ

### 3.212. `නැගිටහන්` -> `get up`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මයෙ මෙතූ... නැගිටහන් බොල @USER
  - [NOT] after:  @USER මයෙ මෙතූ... get up බොල @USER
  - [NOT] before: @USER මයෙ මෙතූ... නැගිටහන් බොල @USER
  - [NOT] after:  @USER my මෙතූ... get up බොල @USER

### 3.213. `හිස්` -> `empty`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අපිද මහත්තයා හිස් කරේ
  - [NOT] after:  @USER අපිද මහත්තයා empty කරේ
  - [NOT] before: @USER අපිද මහත්තයා හිස් කරේ
  - [NOT] after:  @USER අපිද මහත්තයා empty කරේ

### 3.214. `කිසිදා` -> `never`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER සිත්කින් නොවේ කිසිදා හැර යන්නෙ මා
  - [NOT] after:  @USER සිත්කින් නොවේ never හැර යන්නෙ මා
  - [NOT] before: @USER සිත්කින් නොවේ කිසිදා හැර යන්නෙ මා
  - [NOT] after:  @USER සිත්කින් නොවේ never හැර යන්නෙ මා

### 3.215. `කලබල` -> `panic`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  @USER   හා හා තොපි කලබල නොවි හිටපියව් @USER
  - [NOT] after:  @USER @USER  @USER   හා හා තොපි panic නොවි හිටපියව් @USER
  - [NOT] before: @USER @USER  @USER   හා හා තොපි කලබල නොවි හිටපියව් @USER
  - [NOT] after:  @USER @USER  @USER   හා හා තොපි panic නොවි හිටපියව් @USER

### 3.216. `අම්මයර්` -> `umpire`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කැරි පොන්න අම්මයර් out එක දුන්නා එක out නෑ හුත්තෝ කැරි indian පොන්නයන්ට අත දෙන කැරියෙක් පොන්නයා
  - [OFF] after:  කැරි පොන්න umpire out එක දුන්නා එක out නෑ හුත්තෝ කැරි indian පොන්නයන්ට අත දෙන කැරියෙක් පොන්නයා
  - [OFF] before: කැරි පොන්න අම්මයර් out එක දුන්නා එක out නෑ හුත්තෝ කැරි indian පොන්නයන්ට අත දෙන කැරියෙක් පොන්නයා
  - [OFF] after:  කැරි පොන්න umpire out එක දුන්නා එක out නෑ හුත්තෝ කැරි indian පොන්නයන්ට අත දෙන කැරියෙක් පොන්නයා

### 3.217. `මැස්සා` -> `fly`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කාලකණ්ණි මී මැස්සා මැරිල පලයන්
  - [OFF] after:  කාලකණ්ණි මී fly මැරිල පලයන්
  - [OFF] before: කාලකණ්ණි මී මැස්සා මැරිල පලයන්
  - [OFF] after:  කාලකණ්ණි මී fly මැරිල පලයන්

### 3.218. `කටු` -> `thorns`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මගේ හද මඩල මල්යහනකි ප්‍රබවති, ඔබේ හද මඩල කටු යහනකි ප්ර්බාවති, කටුයහනේ ඉනට බැ ප්ර්බවති මල්යහනෙනේ බස පලයන් ප්‍රබාවති.
  - [NOT] after:  මගේ හද මඩල මල්යහනකි ප්‍රබවති, ඔබේ හද මඩල thorns යහනකි ප්ර්බාවති, කටුයහනේ ඉනට බැ ප්ර්බවති මල්යහනෙනේ බස පලයන් ප්‍රබාවති.
  - [NOT] before: මගේ හද මඩල මල්යහනකි ප්‍රබවති, ඔබේ හද මඩල කටු යහනකි ප්ර්බාවති, කටුයහනේ ඉනට බැ ප්ර්බවති මල්යහනෙනේ බස පලයන් ප්‍රබාවති.
  - [NOT] after:  මගේ heart මඩල මල්යහනකි ප්‍රබවති, ඔබේ heart මඩල thorns යහනකි ප්ර්බාවති, කටුයහනේ ඉනට බැ ප්ර්බවති මල්යහනෙනේ බස පලයන් ප්‍රබාවති.

### 3.219. `ළමා` -> `child`
- impact: 2 posts (0 light, 2 heavy), 1 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අම්බලමේ පිනා  අම්බලමේ          පිනා  වලං කදක්      ගෙනා එක බිදපි       ගොනා එකට මට         හිනා  හුරුබුහුටිට      මනා තෝඩු දෙකක්    තම හිතේ හීන        තනා අම්බලමේ         පින  පිනාගේ පොඩි   ළමා මිදුලට දුව         එනා බිදුනු හීන          බලා කද ළග ගොලු   වුනා
  - [NOT] after:  අම්බලමේ පිනා  අම්බලමේ          පිනා  වලං කදක්      ගෙනා එක බිදපි       ගොනා එකට මට         හිනා  හුරුබුහුටිට      මනා තෝඩු දෙකක්    තම හිතේ dreams        තනා අම්බලමේ         පින  පිනාගේ පොඩි   child මිදුලට දුව         එනා බිදුනු dreams          බලා කද ළග ගොලු   වුනා
  - [OFF] before: ළමා අපචාර කරන උන්දලගෙ බිජ්ජ කපලා කව්වන්න ඕන උන්ටම.. මූසල බල්ලො... මොන කාලකන්නිකමකට ඉපදුනාද මංදා
  - [OFF] after:  child අපචාර කරන උන්දලගෙ බිජ්ජ cut කව්වන්න ඕන උන්ටම.. මූසල බල්ලො... මොන කාලකන්නිකමකට ඉපදුනාද මංදා

### 3.220. `මීයා` -> `rat`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER නිකමට හිතුනා සක්කිලි මීයා දකියි කියලා
  - [OFF] after:  @USER  @USER නිකමට හිතුනා සක්කිලි rat දකියි කියලා
  - [OFF] before: @USER  @USER නිකමට හිතුනා සක්කිලි මීයා දකියි කියලා
  - [OFF] after:  @USER  @USER නිකමට හිතුනා සක්කිලි rat දකියි කියලා

### 3.221. `උත්සව` -> `festivals`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අපේ උත්සව දැන් ඔහොම ලොකුවට ගත්තට කමක් නැද්ද?
  - [NOT] after:  @USER අපේ festivals දැන් ඔහොම ලොකුවට ගත්තට කමක් නැද්ද?
  - [NOT] before: @USER අපේ උත්සව දැන් ඔහොම ලොකුවට ගත්තට කමක් නැද්ද?
  - [NOT] after:  @USER අපේ festivals දැන් ඔහොම ලොකුවට ගත්තට කමක් නැද්ද?

### 3.222. `අනුන්` -> `others`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: තුක් නොදකින් මුසලයා... අනුන් දුන්න එවා තමාගේ නම ගහලා බෙදනවා URL
  - [OFF] after:  තුක් නොදකින් මුසලයා... others දුන්න එවා තමාගේ නම ගහලා බෙදනවා URL
  - [OFF] before: තුක් නොදකින් මුසලයා... අනුන් දුන්න එවා තමාගේ නම ගහලා බෙදනවා URL
  - [OFF] after:  තුක් නොදකින් මුසලයා... others දුන්න එවා තමාගේ නම ගහලා බෙදනවා URL

### 3.223. `හැමතැනම` -> `everywhere`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER දැං පොන්න පොරවල් හැමතැනම.
  - [OFF] after:  @USER  @USER දැං පොන්න පොරවල් everywhere.
  - [OFF] before: @USER  @USER දැං පොන්න පොරවල් හැමතැනම.
  - [OFF] after:  @USER  @USER දැං පොන්න පොරවල් everywhere.

### 3.224. `පෙර` -> `before`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔබමද මේ පෙර උන් එයා
  - [NOT] after:  @USER ඔබමද මේ before උන් එයා
  - [NOT] before: @USER ඔබමද මේ පෙර උන් එයා
  - [NOT] after:  @USER ඔබමද මේ before උන් එයා

### 3.225. `මහන්සිත්` -> `tired`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ජයාගේ බිජ්ජ බලලා කට්ටියට මහන්සිත් ඇති නේහ්... =D
  - [OFF] after:  ජයාගේ බිජ්ජ බලලා කට්ටියට tired ඇති නේහ්... =D
  - [OFF] before: ජයාගේ බිජ්ජ බලලා කට්ටියට මහන්සිත් ඇති නේහ්... =D
  - [OFF] after:  ජයාගේ බිජ්ජ බලලා කට්ටියට tired ඇති නේහ්... =D

### 3.226. `කොයි` -> `which`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER බිව්ව නොබිව්ව කෙසේ වෙතත් ඔය කොයි කවෘත් බලන් ඉන්නෙ රෙද්ද අස්සෙ රිංඟන්න තමා..
  - [OFF] after:  @USER බිව්ව නොබිව්ව කෙසේ වෙතත් ඔය which කවෘත් බලන් ඉන්නෙ රෙද්ද අස්සෙ රිංඟන්න තමා..
  - [OFF] before: @USER බිව්ව නොබිව්ව කෙසේ වෙතත් ඔය කොයි කවෘත් බලන් ඉන්නෙ රෙද්ද අස්සෙ රිංඟන්න තමා..
  - [OFF] after:  @USER බිව්ව නොබිව්ව කෙසේ වෙතත් ඔය which කවෘත් බලන් ඉන්නෙ රෙද්ද අස්සෙ රිංඟන්න තමා..

### 3.227. `පහලට` -> `down`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: DP changed  දැං ඉතිං මේක දැක දැක පහලට යන්නැතුව ලැයික්ස් එකක් රීටිවිට්ස් එකක් දාපල්ලා හැත්ත...
  - [NOT] after:  DP changed  දැං ඉතිං මේක දැක දැක down යන්නැතුව ලැයික්ස් එකක් රීටිවිට්ස් එකක් දාපල්ලා හැත්ත...
  - [NOT] before: DP changed  දැං ඉතිං මේක දැක දැක පහලට යන්නැතුව ලැයික්ස් එකක් රීටිවිට්ස් එකක් දාපල්ලා හැත්ත...
  - [NOT] after:  DP changed  දැං ඉතිං මේක දැක දැක down යන්නැතුව ලැයික්ස් එකක් රීටිවිට්ස් එකක් දාපල්ලා හැත්ත...

### 3.228. `වගා` -> `cultivate`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: දැන් ඉතින් තියෙන්නේ හරකාට වෙලාවට කන්න බොන දෙන එක විතරයි.නැත්නම් හරකා අහල පහල වතුවලට පැනලා වගා හානි කරන්න ඉඩ තියෙනවා.ඒ වගේම තමයි පොඩි අය මේවා තනියම හදන්න යන්නෙපා..අම්මලා තාත්තලා පොඩි අයට මේවා හදලා දෙන්න හොදේ.
  - [NOT] after:  දැන් ඉතින් තියෙන්නේ හරකාට වෙලාවට කන්න බොන දෙන එක විතරයි.නැත්නම් හරකා අහල පහල වතුවලට පැනලා cultivate හානි කරන්න ඉඩ තියෙනවා.ඒ වගේම තමයි පොඩි අය මේවා තනියම හදන්න යන්නෙපා..අම්මලා තාත්තලා පොඩි අයට මේවා හදලා දෙන්න හොදේ.
  - [NOT] before: දැන් ඉතින් තියෙන්නේ හරකාට වෙලාවට කන්න බොන දෙන එක විතරයි.නැත්නම් හරකා අහල පහල වතුවලට පැනලා වගා හානි කරන්න ඉඩ තියෙනවා.ඒ වගේම තමයි පොඩි අය මේවා තනියම හදන්න යන්නෙපා..අම්මලා තාත්තලා පොඩි අයට මේවා හදලා දෙන්න හොදේ.
  - [NOT] after:  දැන් ඉතින් තියෙන්නේ හරකාට වෙලාවට කන්න බොන දෙන එක විතරයි.නැත්නම් හරකා අහල පහල වතුවලට පැනලා cultivate හානි කරන්න ඉඩ තියෙනවා.ඒ වගේම තමයි පොඩි අය මේවා තනියම හදන්න යන්නෙපා..අම්මලා තාත්තලා පොඩි අයට මේවා හදලා දෙන්න ok.

### 3.229. `ලෙවකන` -> `licking`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඇත්තටම බන්. අන්තිමට ඉවර වෙන්නෙම රාජපක්ෂගේ පස්ස ලෙවකන එකෙක් කියල.
  - [OFF] after:  @USER ඇත්තටම බන්. අන්තිමට ඉවර වෙන්නෙම රාජපක්ෂගේ පස්ස licking එකෙක් කියල.
  - [OFF] before: @USER ඇත්තටම බන්. අන්තිමට ඉවර වෙන්නෙම රාජපක්ෂගේ පස්ස ලෙවකන එකෙක් කියල.
  - [OFF] after:  @USER ඇත්තටම බන්. අන්තිමට ඉවර වෙන්නෙම රාජපක්ෂගේ පස්ස licking එකෙක් කියල.

### 3.230. `මසුන්` -> `fish`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හුරතල් මසුන් වගේ ඇති කරන්නද
  - [NOT] after:  @USER හුරතල් fish වගේ ඇති කරන්නද
  - [NOT] before: @USER හුරතල් මසුන් වගේ ඇති කරන්නද
  - [NOT] after:  @USER හුරතල් fish වගේ ඇති කරන්නද

### 3.231. `රංජන්ගේ` -> `Ranjan's`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඇයි තෝ දන්නැද්ද? රංජන්ගේ කෑල්ල
  - [NOT] after:  @USER ඇයි තෝ දන්නැද්ද? Ranjan's කෑල්ල
  - [NOT] before: @USER ඇයි තෝ දන්නැද්ද? රංජන්ගේ කෑල්ල
  - [NOT] after:  @USER ඇයි තෝ දන්නැද්ද? Ranjan's girl

### 3.232. `නරකෙයි` -> `bad`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඒත් පොඩ්ඩක් ඇවිල්ලා ගියානං නරකෙයි?  රෙද්ද.
  - [OFF] after:  @USER ඒත් පොඩ්ඩක් ඇවිල්ලා ගියානං bad?  රෙද්ද.
  - [OFF] before: @USER ඒත් පොඩ්ඩක් ඇවිල්ලා ගියානං නරකෙයි?  රෙද්ද.
  - [OFF] after:  @USER ඒත් පොඩ්ඩක් ඇවිල්ලා ගියානං bad?  රෙද්ද.

### 3.233. `ලැඡ්ඡා` -> `shame`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ලැඡ්ඡා නැතුව ඇහුවනේ, නොදකින් ... The following media includes potentially sensitive content. Change settings View
  - [OFF] after:  shame නැතුව ඇහුවනේ, නොදකින් ... The following media includes potentially sensitive content. Change settings View
  - [OFF] before: ලැඡ්ඡා නැතුව ඇහුවනේ, නොදකින් ... The following media includes potentially sensitive content. Change settings View
  - [OFF] after:  shame නැතුව ඇහුවනේ, නොදකින් ... The following media includes potentially sensitive content. Change settings View

### 3.234. `හත` -> `seven`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ඔන්න තව අවුරුදු 5කින් සර්වආගමික හැත්තට කියන්න පුලුවන් අඩේ ISIS අයියලා මම මීට අවුරුදු හත අටකට කලින් ඉඳන්ම පුක... URL
  - [OFF] after:  ඔන්න තව අවුරුදු 5කින් සර්වආගමික හැත්තට කියන්න පුලුවන් අඩේ ISIS අයියලා මම මීට අවුරුදු seven අටකට කලින් ඉඳන්ම පුක... URL
  - [OFF] before: ඔන්න තව අවුරුදු 5කින් සර්වආගමික හැත්තට කියන්න පුලුවන් අඩේ ISIS අයියලා මම මීට අවුරුදු හත අටකට කලින් ඉඳන්ම පුක... URL
  - [OFF] after:  ඔන්න තව අවුරුදු 5කින් සර්වආගමික හැත්තට say පුලුවන් අඩේ ISIS අයියලා මම මීට අවුරුදු seven අටකට කලින් ඉඳන්ම පුක... URL

### 3.235. `වීදියේ` -> `street එකේ`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සෙක්කු වීදියේ කිම්බා දැක උඹ මට මතක් උනා... කයිමන් දොරකඩ ඉඳපං මං එනතුරු සෙලෙස්තිනා.... (Excuse any typos.)
  - [OFF] after:  සෙක්කු street එකේ කිම්බා දැක උඹ මට මතක් උනා... කයිමන් දොරකඩ ඉඳපං මං එනතුරු සෙලෙස්තිනා.... (Excuse any typos.)
  - [OFF] before: සෙක්කු වීදියේ කිම්බා දැක උඹ මට මතක් උනා... කයිමන් දොරකඩ ඉඳපං මං එනතුරු සෙලෙස්තිනා.... (Excuse any typos.)
  - [OFF] after:  සෙක්කු street එකේ කිම්බා දැක උඹ මට මතක් උනා... කයිමන් දොරකඩ ඉඳපං මං එනතුරු සෙලෙස්තිනා.... (Excuse any typos.)

### 3.236. `තේරවිලි` -> `riddles`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: රෙද්ද කැඩුව බූසි දැක්ක. බූසි කැඩුව ඇටේ දැක්ක #තේරවිලි
  - [OFF] after:  රෙද්ද කැඩුව බූසි දැක්ක. බූසි කැඩුව ඇටේ දැක්ක #riddles
  - [OFF] before: රෙද්ද කැඩුව බූසි දැක්ක. බූසි කැඩුව ඇටේ දැක්ක #තේරවිලි
  - [OFF] after:  රෙද්ද කැඩුව බූසි දැක්ක. බූසි කැඩුව ඇටේ දැක්ක #riddles

### 3.237. `නාකිය` -> `old man`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER ඒ පලයන් නාකිය උබ.. ආව මෙතන
  - [OFF] after:  @USER  @USER ඒ පලයන් old man උබ.. ආව මෙතන
  - [OFF] before: @USER  @USER ඒ පලයන් නාකිය උබ.. ආව මෙතන
  - [OFF] after:  @USER  @USER ඒ පලයන් old man උබ.. ආව මෙතන

### 3.238. `තෝව` -> `you`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හී පහරින් සමුගත්තේ මගෙ පණ රැකදෙන්නයි ඔයා - Song Lyrics  තෝව බේරල මං ඇනගෙන මැරෙන්න? කසිප්පු ගහලද ඈහ්. පලයන් ඩෝහ් යන්න - Real Life
  - [OFF] after:  හී පහරින් සමුගත්තේ මගෙ පණ රැකදෙන්නයි ඔයා - Song Lyrics  you බේරල මං ඇනගෙන මැරෙන්න? කසිප්පු ගහලද ඈහ්. පලයන් ඩෝහ් යන්න - Real Life
  - [OFF] before: හී පහරින් සමුගත්තේ මගෙ පණ රැකදෙන්නයි ඔයා - Song Lyrics  තෝව බේරල මං ඇනගෙන මැරෙන්න? කසිප්පු ගහලද ඈහ්. පලයන් ඩෝහ් යන්න - Real Life
  - [OFF] after:  හී පහරින් සමුගත්තේ මගෙ පණ රැකදෙන්නයි ඔයා - Song Lyrics  you බේරල මං ඇනගෙන මැරෙන්න? කසිප්පු ගහලද ඈහ්. පලයන් ඩෝහ් යන්න - Real Life

### 3.239. `මල්ලෙන්` -> `bag එකෙන්`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: හරි හරි බල්ලා පැන්නා මල්ලෙන් එලියට
  - [NOT] after:  හරි හරි බල්ලා පැන්නා bag එකෙන් එලියට
  - [NOT] before: හරි හරි බල්ලා පැන්නා මල්ලෙන් එලියට
  - [NOT] after:  හරි හරි dog පැන්නා bag එකෙන් එලියට

### 3.240. `ලූෂන්` -> `Lushan`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER Congratulations ලූෂන් අයියේ ඔබට චිරං ජයතු.ජයවේවා
  - [NOT] after:  @USER Congratulations Lushan අයියේ ඔබට චිරං ජයතු.ජයවේවා
  - [NOT] before: @USER Congratulations ලූෂන් අයියේ ඔබට චිරං ජයතු.ජයවේවා
  - [NOT] after:  @USER Congratulations Lushan අයියේ ඔබට චිරං ජයතු.ජයවේවා

### 3.241. `මොනවහරි` -> `something`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මේක වැඩි වෙන්න කලින් මොනවහරි කරන්න වෙනවා
  - [NOT] after:  @USER මේක වැඩි වෙන්න කලින් something කරන්න වෙනවා
  - [NOT] before: @USER මේක වැඩි වෙන්න කලින් මොනවහරි කරන්න වෙනවා
  - [NOT] after:  @USER මේක වැඩි වෙන්න කලින් something කරන්න වෙනවා

### 3.242. `ඉයියේ` -> `yesterday`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  අඩො උන් පැරදුනා ද ? අඩෝ මන් හිතුවේ උන් ඉයියේ දින්නා කියලා. දැන් නේ මතක් උනේ අද April Fools Day නේ
  - [NOT] after:  @USER @USER  අඩො උන් පැරදුනා ද ? අඩෝ මන් හිතුවේ උන් yesterday දින්නා කියලා. දැන් නේ මතක් උනේ අද April Fools Day නේ
  - [NOT] before: @USER @USER  අඩො උන් පැරදුනා ද ? අඩෝ මන් හිතුවේ උන් ඉයියේ දින්නා කියලා. දැන් නේ මතක් උනේ අද April Fools Day නේ
  - [NOT] after:  @USER @USER  අඩො උන් පැරදුනා ද ? අඩෝ මන් හිතුවේ උන් yesterday won කියලා. දැන් නේ මතක් උනේ අද April Fools Day නේ

### 3.243. `හොරට` -> `fake`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  උඹ වගේ හොරට ආචාරියෙක් උන්නෑ බොල......  @USER  @USER
  - [OFF] after:  @USER  උඹ වගේ fake ආචාරියෙක් උන්නෑ බොල......  @USER  @USER
  - [OFF] before: @USER  උඹ වගේ හොරට ආචාරියෙක් උන්නෑ බොල......  @USER  @USER
  - [OFF] after:  @USER  උඹ වගේ fake ආචාරියෙක් උන්නෑ බොල......  @USER  @USER

### 3.244. `මහත්තයො` -> `sir`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අතරමං වෙලාද මහත්තයො ?
  - [NOT] after:  @USER අතරමං වෙලාද sir ?
  - [NOT] before: @USER අතරමං වෙලාද මහත්තයො ?
  - [NOT] after:  @USER lost වෙලාද sir ?

### 3.245. `නිල` -> `official`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER ඇයි බන් කටුස්සි උබ ඔහොම ගොන් මෝඩ ගොබ්බ හරක් මී හරක් වහු පෙරේත කුම්බාන්ඩ මීමැසි ගොයන් මැසි නිල මැසි බලු සුනක බලල් හිකනල් ආකරයට හැසිරෙන්නේ
  - [OFF] after:  @USER  @USER ඇයි බන් කටුස්සි උබ ඔහොම ගොන් මෝඩ ගොබ්බ හරක් මී හරක් වහු පෙරේත කුම්බාන්ඩ මීමැසි ගොයන් මැසි official මැසි බලු සුනක බලල් හිකනල් ආකරයට හැසිරෙන්නේ
  - [OFF] before: @USER  @USER ඇයි බන් කටුස්සි උබ ඔහොම ගොන් මෝඩ ගොබ්බ හරක් මී හරක් වහු පෙරේත කුම්බාන්ඩ මීමැසි ගොයන් මැසි නිල මැසි බලු සුනක බලල් හිකනල් ආකරයට හැසිරෙන්නේ
  - [OFF] after:  @USER  @USER ඇයි බන් කටුස්සි උබ ඔහොම ගොන් මෝඩ ගොබ්බ හරක් මී හරක් වහු පෙරේත කුම්බාන්ඩ මීමැසි ගොයන් මැසි official මැසි බලු සුනක බලල් හිකනල් ආකරයට හැසිරෙන්නේ

### 3.246. `ආච්චි` -> `grandma`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER නාකි ආච්චි කෙනෙක් වගෙද
  - [NOT] after:  @USER නාකි grandma කෙනෙක් වගෙද
  - [NOT] before: @USER නාකි ආච්චි කෙනෙක් වගෙද
  - [NOT] after:  @USER නාකි grandma කෙනෙක් වගෙද

### 3.247. `මදුරුවො` -> `mosquitoes`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: එක අතකින් TL එක හසුරුව ගමන්  අනිත් අතින් වේස මදුරුවො කාපුව කසන ගමන් ඉන්නෙ...
  - [OFF] after:  එක අතකින් TL එක හසුරුව ගමන්  අනිත් අතින් වේස mosquitoes කාපුව කසන ගමන් ඉන්නෙ...
  - [OFF] before: එක අතකින් TL එක හසුරුව ගමන්  අනිත් අතින් වේස මදුරුවො කාපුව කසන ගමන් ඉන්නෙ...
  - [OFF] after:  එක අතකින් TL එක හසුරුව ගමන්  other අතින් වේස mosquitoes කාපුව කසන ගමන් ඉන්නෙ...

### 3.248. `ඉතිරි` -> `rest`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER ගොඩක් අය හිතන් ඉන්නෙ Windows වල GUI Shell එක තමයි OS එක කියලා. ඇත්තටම OS කියන එක අපිට පේන්නෙ නැති බව වත් දන්නෑ. ඉස්සර Monitors කියලා ආව මෘදුකාංග කෑල්ල පස්සෙ OS එක වෙලා දැන් ඒකෙන් ඉතිරි වෙලා තියෙන්නෙ Kernel එක විතරයි බවත්, අපි ඒක ඇක්සස් කරන Shell එක විතරක් අපිට පේන බවත් දන්නෑ.
  - [NOT] after:  @USER  @USER ගොඩක් අය හිතන් ඉන්නෙ Windows වල GUI Shell එක තමයි OS එක කියලා. ඇත්තටම OS කියන එක අපිට පේන්නෙ නැති බව වත් දන්නෑ. ඉස්සර Monitors කියලා ආව මෘදුකාංග කෑල්ල පස්සෙ OS එක වෙලා දැන් ඒකෙන් rest වෙලා තියෙන්නෙ Kernel එක විතරයි බවත්, අපි ඒක ඇක්සස් කරන Shell එක විතරක් අපිට පේන බවත් දන්නෑ.
  - [NOT] before: @USER  @USER ගොඩක් අය හිතන් ඉන්නෙ Windows වල GUI Shell එක තමයි OS එක කියලා. ඇත්තටම OS කියන එක අපිට පේන්නෙ නැති බව වත් දන්නෑ. ඉස්සර Monitors කියලා ආව මෘදුකාංග කෑල්ල පස්සෙ OS එක වෙලා දැන් ඒකෙන් ඉතිරි වෙලා තියෙන්නෙ Kernel එක විතරයි බවත්, අපි ඒක ඇක්සස් කරන Shell එක විතරක් අපිට පේන බවත් දන්නෑ.
  - [NOT] after:  @USER  @USER lot අය හිතන් ඉන්නෙ Windows වල GUI Shell එක තමයි OS එක කියලා. ඇත්තටම OS කියන එක අපිට පේන්නෙ නැති බව වත් දන්නෑ. ඉස්සර Monitors කියලා ආව මෘදුකාංග කෑල්ල පස්සෙ OS එක වෙලා දැන් ඒකෙන් rest වෙලා තියෙන්නෙ Kernel එක විතරයි බවත්, අපි ඒක ඇක්සස් කරන Shell එක විතරක් අපිට පේන බවත් දන්නෑ.

### 3.249. `යහපාලන` -> `good governance`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  යහපාලන මල්ලිලගේ කටවල්, පු*වල් වී ඇති බැවින් මොකුත් කතා නැත
  - [OFF] after:  @USER @USER  good governance මල්ලිලගේ කටවල්, පු*වල් වී ඇති බැවින් මොකුත් කතා නැත
  - [OFF] before: @USER @USER  යහපාලන මල්ලිලගේ කටවල්, පු*වල් වී ඇති බැවින් මොකුත් කතා නැත
  - [OFF] after:  @USER @USER  good governance මල්ලිලගේ mouths, පු*වල් වී ඇති බැවින් මොකුත් කතා නැත

### 3.250. `කුරුම්බා` -> `king coconut`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: තඩි තඩි තඩි ද කුරුම්බා?
  - [NOT] after:  තඩි තඩි තඩි ද king coconut?
  - [NOT] before: තඩි තඩි තඩි ද කුරුම්බා?
  - [NOT] after:  තඩි තඩි තඩි ද king coconut?

### 3.251. `නඩුත්` -> `case`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: නඩුත් හාමුදුරුවන්ගේ බඩුත් හාමුදුරුවන්ගේ කිව්වහම හාමුදුරුවන්ගෙ බඩුව පිනට ඉල්ලගන්න බැරිවෙයි ද දන් නෑ කියලා හිතන පෞකාර මම.
  - [OFF] after:  case හාමුදුරුවන්ගේ බඩුත් හාමුදුරුවන්ගේ කිව්වහම හාමුදුරුවන්ගෙ බඩුව පිනට ඉල්ලගන්න බැරිවෙයි ද දන් නෑ කියලා හිතන පෞකාර මම.
  - [OFF] before: නඩුත් හාමුදුරුවන්ගේ බඩුත් හාමුදුරුවන්ගේ කිව්වහම හාමුදුරුවන්ගෙ බඩුව පිනට ඉල්ලගන්න බැරිවෙයි ද දන් නෑ කියලා හිතන පෞකාර මම.
  - [OFF] after:  case හාමුදුරුවන්ගේ බඩුත් හාමුදුරුවන්ගේ කිව්වහම හාමුදුරුවන්ගෙ බඩුව පිනට ඉල්ලගන්න බැරිවෙයි ද දන් නෑ කියලා හිතන පෞකාර මම.

### 3.252. `පදිංචි` -> `settled`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER එහෙම පදිංචි උනානන් හරී
  - [NOT] after:  @USER එහෙම settled උනානන් හරී
  - [NOT] before: @USER එහෙම පදිංචි උනානන් හරී
  - [NOT] after:  @USER එහෙම settled උනානන් හරී

### 3.253. `උරුම` -> `inherited`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: පොරත්වය ලබා ගනු වස් උප්පත්තියෙන් උරුම කර ගත් ගොන්කම ප්‍රදර්ශණය කරන්නාවූ හුජ්ජ ලොල්ලෙක්....       #lka   URL
  - [OFF] after:  පොරත්වය ලබා ගනු වස් උප්පත්තියෙන් inherited කර ගත් ගොන්කම ප්‍රදර්ශණය කරන්නාවූ හුජ්ජ ලොල්ලෙක්....       #lka   URL
  - [OFF] before: පොරත්වය ලබා ගනු වස් උප්පත්තියෙන් උරුම කර ගත් ගොන්කම ප්‍රදර්ශණය කරන්නාවූ හුජ්ජ ලොල්ලෙක්....       #lka   URL
  - [OFF] after:  පොරත්වය ලබා ගනු වස් උප්පත්තියෙන් inherited කර ගත් ගොන්කම ප්‍රදර්ශණය කරන්නාවූ හුජ්ජ ලොල්ලෙක්....       #lka   URL

### 3.254. `ෆක්` -> `fuck`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ෆක් අයිසේ.........  (හුකනව කිව්වෙ නෑ කැත නිසා)
  - [OFF] after:  @USER fuck අයිසේ.........  (හුකනව කිව්වෙ නෑ කැත නිසා)
  - [OFF] before: @USER ෆක් අයිසේ.........  (හුකනව කිව්වෙ නෑ කැත නිසා)
  - [OFF] after:  @USER fuck අයිසේ.........  (හුකනව කිව්වෙ නෑ කැත නිසා)

### 3.255. `ඇදුම්` -> `clothes`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මගෙ ඇදුම් ඉඹ ඉඹා අඩන හැටි මැවෙනවා… ඔය ගෑණි මං නැතුව ඉදලා නෑ දන්නවා… දොර ළගම බලාගෙන අනේ ඇති හිතෙනවා…. නොකියාම ගිය හින්දා තරහින්ද හිතෙනවා… (2/3)
  - [NOT] after:  මගෙ clothes ඉඹ ඉඹා අඩන හැටි මැවෙනවා… ඔය ගෑණි මං නැතුව ඉදලා නෑ දන්නවා… දොර ළගම බලාගෙන අනේ ඇති හිතෙනවා…. නොකියාම ගිය හින්දා තරහින්ද හිතෙනවා… (2/3)
  - [NOT] before: මගෙ ඇදුම් ඉඹ ඉඹා අඩන හැටි මැවෙනවා… ඔය ගෑණි මං නැතුව ඉදලා නෑ දන්නවා… දොර ළගම බලාගෙන අනේ ඇති හිතෙනවා…. නොකියාම ගිය හින්දා තරහින්ද හිතෙනවා… (2/3)
  - [NOT] after:  මගෙ clothes ඉඹ ඉඹා අඩන හැටි මැවෙනවා… ඔය ගෑණි මං නැතුව ඉදලා නෑ know… දොර ළගම බලාගෙන අනේ ඇති හිතෙනවා…. නොකියාම ගිය හින්දා තරහින්ද හිතෙනවා… (2/3)

### 3.256. `ව්තරක්` -> `only`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: යකෝ කවකට්ට ව්තරක් 1000ක් වෙනව කොරන්න බෑ යකෝ....
  - [NOT] after:  යකෝ කවකට්ට only 1000ක් වෙනව කොරන්න බෑ යකෝ....
  - [NOT] before: යකෝ කවකට්ට ව්තරක් 1000ක් වෙනව කොරන්න බෑ යකෝ....
  - [NOT] after:  යකෝ කවකට්ට only 1000ක් වෙනව කොරන්න බෑ යකෝ....

### 3.257. `ඉස්සරහා` -> `front`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඉස්සරහා කකුල් කොහෙද යකෝ. කකුල් දෙකයි නේ තියෙන්නේ. තෝ කුකුලා කියලා හරකා කනවාද දන්නේ නෑ
  - [NOT] after:  @USER front legs කොහෙද යකෝ. legs දෙකයි නේ තියෙන්නේ. තෝ කුකුලා කියලා හරකා කනවාද දන්නේ නෑ
  - [NOT] before: - අය්යේ ඉස්සරහා හුඹහා ගාවින් බස්සලා යන්න - තමුසෙ නයෙක් ද ඕයි හුඹහ ගාවින් බහින්න  - නෑ වේයෙක්. තමුසෙ බස්සනවකෝ...
  - [NOT] after:  - අය්යේ front හුඹහා ගාවින් බස්සලා යන්න - තමුසෙ snake ද ඕයි හුඹහ ගාවින් බහින්න  - නෑ වේයෙක්. තමුසෙ බස්සනවකෝ...

### 3.258. `දැනට` -> `currently`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ඔය best life කියල තියන මගුල් කරන්න ගිහින් life එකේ දැනට තියන best එකත් නැති කර ගන්න තරම් මෝඩ වෙන්න එපා.
  - [NOT] after:  ඔය best life කියල තියන මගුල් කරන්න ගිහින් life එකේ currently තියන best එකත් නැති කර ගන්න තරම් මෝඩ වෙන්න එපා.
  - [NOT] before: ඔය best life කියල තියන මගුල් කරන්න ගිහින් life එකේ දැනට තියන best එකත් නැති කර ගන්න තරම් මෝඩ වෙන්න එපා.
  - [NOT] after:  ඔය best life කියල තියන මගුල් කරන්න ගිහින් life එකේ currently තියන best එකත් නැති කර ගන්න තරම් මෝඩ වෙන්න එපා.

### 3.259. `මචන්` -> `machan`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: තොට අද කෑවා ඇති නේද මචන්..........අනිත් එක්කනා ට තව වැඩි කල් නෑ පරිස්සමෙන් — feeling crazy
  - [NOT] after:  තොට අද කෑවා ඇති නේද machan..........අනිත් එක්කනා ට තව වැඩි කල් නෑ පරිස්සමෙන් — feeling crazy
  - [NOT] before: තොට අද කෑවා ඇති නේද මචන්..........අනිත් එක්කනා ට තව වැඩි කල් නෑ පරිස්සමෙන් — feeling crazy
  - [NOT] after:  තොට අද කෑවා ඇති නේද machan..........අනිත් එක්කනා ට තව වැඩි කල් නෑ carefully — feeling crazy

### 3.260. `පෙම්` -> `love`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මූ යකෝ මුලින්ම ස්කොලේ ගිහිල්ලා ඉවර කරහන් ආවා මෙතන පෙම් කරන්න ගහප් තොට
  - [OFF] after:  @USER මූ යකෝ මුලින්ම ස්කොලේ ගිහිල්ලා ඉවර කරහන් ආවා මෙතන love කරන්න ගහප් තොට
  - [OFF] before: @USER මූ යකෝ මුලින්ම ස්කොලේ ගිහිල්ලා ඉවර කරහන් ආවා මෙතන පෙම් කරන්න ගහප් තොට
  - [OFF] after:  @USER මූ යකෝ මුලින්ම ස්කොලේ ගිහිල්ලා ඉවර කරහන් ආවා මෙතන love කරන්න ගහප් තොට

### 3.261. `වෙසක්` -> `vesak`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මේ තරම් සංහාරයක් වෙලා තියෙද්දි කොහොම වෙසක් සමරන්නද?
  - [NOT] after:  @USER මේ තරම් සංහාරයක් වෙලා තියෙද්දි කොහොම vesak සමරන්නද?
  - [NOT] before: @USER මේ තරම් සංහාරයක් වෙලා තියෙද්දි කොහොම වෙසක් සමරන්නද?
  - [NOT] after:  @USER මේ තරම් සංහාරයක් වෙලා තියෙද්දි කොහොම vesak සමරන්නද?

### 3.262. `පී` -> `P`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  @USER  @USER  @USER  පල ඩෝ යන්න.අපි ඔය පිලිපීන් එවුන් පස්සෙ යන්නෙ නෑ...යකෝ අපි තවම වර්ජින්....පී
  - [OFF] after:  @USER @USER  @USER  @USER  @USER  පල ඩෝ යන්න.අපි ඔය පිලිපීන් එවුන් පස්සෙ යන්නෙ නෑ...යකෝ අපි තවම වර්ජින්....P
  - [OFF] before: @USER @USER  @USER  @USER  @USER  පල ඩෝ යන්න.අපි ඔය පිලිපීන් එවුන් පස්සෙ යන්නෙ නෑ...යකෝ අපි තවම වර්ජින්....පී
  - [OFF] after:  @USER @USER  @USER  @USER  @USER  පල ඩෝ යන්න.අපි ඔය පිලිපීන් එවුන් පස්සෙ යන්නෙ නෑ...යකෝ අපි still වර්ජින්....P

### 3.263. `ඔයාල` -> `you all`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ටහුඩු , ඔයාල Ground එකේ?  @USER
  - [NOT] after:  @USER ටහුඩු , you all Ground එකේ?  @USER
  - [NOT] before: @USER ටහුඩු , ඔයාල Ground එකේ?  @USER
  - [NOT] after:  @USER ටහුඩු , you all Ground එකේ?  @USER

### 3.264. `රත්‍රං` -> `gold`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: වාඩිවෙන පුක රත්‍රං ද දන්නෙ නෑ ? යකො මෙහෙම ගැහිලි  Azzam Ameen @USER  · 9 Aug 2018 “Rs 650,000 estimated cost of One Chair at the new western provincial council building” JVP complains to western province governor
  - [OFF] after:  වාඩිවෙන පුක gold ද දන්නෙ නෑ ? යකො මෙහෙම ගැහිලි  Azzam Ameen @USER  · 9 Aug 2018 “Rs 650,000 estimated cost of One Chair at the new western provincial council building” JVP complains to western province governor
  - [OFF] before: වාඩිවෙන පුක රත්‍රං ද දන්නෙ නෑ ? යකො මෙහෙම ගැහිලි  Azzam Ameen @USER  · 9 Aug 2018 “Rs 650,000 estimated cost of One Chair at the new western provincial council building” JVP complains to western province governor
  - [OFF] after:  වාඩිවෙන පුක gold ද දන්නෙ නෑ ? යකො මෙහෙම ගැහිලි  Azzam Ameen @USER  · 9 Aug 2018 “Rs 650,000 estimated cost of One Chair at the new western provincial council building” JVP complains to western province governor

### 3.265. `නොහැක` -> `cannot`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ඇය.;;... පැදුරේදී මැණික වී සමාජයේදී බඩුව විය නොහැක..
  - [NOT] after:  ඇය.;;... පැදුරේදී මැණික වී සමාජයේදී බඩුව විය cannot..
  - [NOT] before: ඇය.;;... පැදුරේදී මැණික වී සමාජයේදී බඩුව විය නොහැක..
  - [NOT] after:  ඇය.;;... පැදුරේදී මැණික වී සමාජයේදී බඩුව විය cannot..

### 3.266. `බයිලා` -> `baila`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මෙච්චර කල් රාජපක්ෂලට හාල් ගරලා දැන් බයිලා කියෝනවා.
  - [NOT] after:  @USER මෙච්චර කල් රාජපක්ෂලට හාල් ගරලා දැන් baila කියෝනවා.
  - [NOT] before: @USER මෙච්චර කල් රාජපක්ෂලට හාල් ගරලා දැන් බයිලා කියෝනවා.
  - [NOT] after:  @USER මෙච්චර කල් රාජපක්ෂලට rice ගරලා දැන් baila කියෝනවා.

### 3.267. `බොරැ` -> `lie`
- impact: 2 posts (0 light, 2 heavy), 1 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER What is sin???  පන්චසිලය රකිනවද ?? බුදුන්  කි පරිදි ජිවත් වන එක නායකයේක් ඉන්නවද ? බොරැ නොකියන .හොරකන් නොකරන
  - [NOT] after:  @USER What is sin???  පන්චසිලය රකිනවද ?? Buddha  කි පරිදි ජිවත් වන එක නායකයේක් ඉන්නවද ? lie නොකියන .හොරකන් නොකරන
  - [OFF] before: ඇත්ත කීවනම් මන් මොනාත් කියන් නෑ නේ..ඇයි බොරැ කීවේ මට ඒ වෙලේ ...   ඇත්ත කීවා කියහන්කෝ...  තමුසෙ මහ බූරුවෙක් වංචාකාරයෙක් තක්කඩියෙක් ..... පලප් මගෙ දෑහට නොපෙනි ..  #bestexcuseslka
  - [OFF] after:  ඇත්ත කීවනම් මන් මොනාත් කියන් නෑ නේ..ඇයි lie කීවේ මට ඒ වෙලේ ...   ඇත්ත said කියහන්කෝ...  තමුසෙ මහ බූරුවෙක් වංචාකාරයෙක් තක්කඩියෙක් ..... පලප් මගෙ දෑහට නොපෙනි ..  #bestexcuseslka

### 3.268. `වෙස්` -> `mask`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER වෙස් මුහුණු බැදන් අාවට නැ අපි රැවටෙන්නෙ
  - [NOT] after:  @USER mask මුහුණු බැදන් අාවට නැ අපි රැවටෙන්නෙ
  - [NOT] before: @USER වෙස් මුහුණු බැදන් අාවට නැ අපි රැවටෙන්නෙ
  - [NOT] after:  @USER mask masks බැදන් අාවට නැ අපි රැවටෙන්නෙ

### 3.269. `ශාලුක` -> `Shaluka`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ගොන් ගෑණියෙක් නිසා අඩන්නෙපා පරයො! Shaluka | ශාලුක ® @USER  · 23 Jul 2017 May u see this.... URL
  - [OFF] after:  ගොන් ගෑණියෙක් නිසා අඩන්නෙපා පරයො! Shaluka | Shaluka ® @USER  · 23 Jul 2017 May u see this.... URL
  - [OFF] before: ගොන් ගෑණියෙක් නිසා අඩන්නෙපා පරයො! Shaluka | ශාලුක ® @USER  · 23 Jul 2017 May u see this.... URL
  - [OFF] after:  ගොන් ගෑණියෙක් නිසා අඩන්නෙපා පරයො! Shaluka | Shaluka ® @USER  · 23 Jul 2017 May u see this.... URL

### 3.270. `සුද්ද` -> `clean`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: වල් වැදී ඇති දියවන්නාව කිඹුල් හිස් ඇත උඩ බලාන ගැන්වූ කැති මුගුරු හා පෑන සුද්ද කරනට එය මනාව
  - [NOT] after:  වල් වැදී ඇති දියවන්නාව කිඹුල් හිස් ඇත උඩ බලාන ගැන්වූ කැති මුගුරු හා පෑන clean කරනට එය මනාව
  - [NOT] before: වල් වැදී ඇති දියවන්නාව කිඹුල් හිස් ඇත උඩ බලාන ගැන්වූ කැති මුගුරු හා පෑන සුද්ද කරනට එය මනාව
  - [NOT] after:  වල් වැදී ඇති දියවන්නාව කිඹුල් හිස් ඇත up බලාන ගැන්වූ කැති මුගුරු හා පෑන clean කරනට එය මනාව

### 3.271. `දේශපාලනටෝක්ස්` -> `politics talks`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: තෝ වගේ ගොන් හරකෙක්, මෝඩ මුසලයෙක්! #දේශපාලනටෝක්ස්
  - [OFF] after:  තෝ වගේ ගොන් හරකෙක්, මෝඩ මුසලයෙක්! #politics talks
  - [OFF] before: තෝ වගේ ගොන් හරකෙක්, මෝඩ මුසලයෙක්! #දේශපාලනටෝක්ස්
  - [OFF] after:  තෝ වගේ ගොන් හරකෙක්, මෝඩ මුසලයෙක්! #politics talks

### 3.272. `මිනිසුන්` -> `people`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මිනිසුන් ගේ ඉවසීම පරික්ෂා කිරීමට තව කල් තීබේ
  - [NOT] after:  @USER people ගේ patience පරික්ෂා කිරීමට තව කල් තීබේ
  - [NOT] before: @USER තමන් විසින් තමන් වනා ගැනීම .... සෑම විපතක් අවසානයේම තමන් උත්කර්ෂයට නැගීම .. ඔබට සහතික මිනිසුන් දෙවි..බලෙන් ලබා ගැනීමට යෑම බොරදියේ මාළු බැමකි
  - [NOT] after:  @USER තමන් විසින් තමන් වනා ගැනීම .... every විපතක් අවසානයේම තමන් උත්කර්ෂයට නැගීම .. ඔබට සහතික people දෙවි..බලෙන් ලබා ගැනීමට යෑම බොරදියේ මාළු බැමකි

### 3.273. `කාගේ` -> `whose`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER Many are guessing " කාගේ බලාපොරොත්තුවද ඉටුවන්නේ කියලා"
  - [NOT] after:  @USER Many are guessing " whose බලාපොරොත්තුවද ඉටුවන්නේ කියලා"
  - [NOT] before: @USER Many are guessing " කාගේ බලාපොරොත්තුවද ඉටුවන්නේ කියලා"
  - [NOT] after:  @USER Many are guessing " whose expectation ඉටුවන්නේ කියලා"

### 3.274. `මරූ` -> `awesome`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER   සා. . .  මරූ නේ
  - [NOT] after:  @USER @USER   සා. . .  awesome නේ
  - [NOT] before: @USER @USER   සා. . .  මරූ නේ
  - [NOT] after:  @USER @USER   සා. . .  awesome නේ

### 3.275. `ඉල්ලනව` -> `asking`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER ඔය ගස් බල්ලා මේක ඉල්ලනව විසිදාහකට.අල්ලන්නවත් දෙන්නේ නෑ යකෝ.
  - [OFF] after:  @USER  @USER ඔය ගස් බල්ලා මේක asking විසිදාහකට.අල්ලන්නවත් දෙන්නේ නෑ යකෝ.
  - [OFF] before: @USER  @USER ඔය ගස් බල්ලා මේක ඉල්ලනව විසිදාහකට.අල්ලන්නවත් දෙන්නේ නෑ යකෝ.
  - [OFF] after:  @USER  @USER ඔය ගස් dog මේක asking විසිදාහකට.අල්ලන්නවත් දෙන්නේ නෑ යකෝ.

### 3.276. `අක්ක` -> `sister`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  උඹ ඒක දිහ කන්න වගෙ බලම් ඇති අක්ක ඩැන් ඔරවයි කියල
  - [NOT] after:  @USER @USER  උඹ ඒක දිහ කන්න වගෙ බලම් ඇති sister ඩැන් ඔරවයි කියල
  - [NOT] before: @USER @USER  උඹ ඒක දිහ කන්න වගෙ බලම් ඇති අක්ක ඩැන් ඔරවයි කියල
  - [NOT] after:  @USER @USER  උඹ ඒක දිහ eat වගෙ බලම් ඇති sister ඩැන් ඔරවයි කියල

### 3.277. `මොලෙත්` -> `brain`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: එක වෙලාවකට මේ මගුලේ  #pornස්ටාර්ස්ලා විතරයි  මොලෙත් වික්ෂිප්ත වෙනවා රෙද්ද
  - [NOT] after:  එක වෙලාවකට මේ මගුලේ  #pornස්ටාර්ස්ලා විතරයි  brain වික්ෂිප්ත වෙනවා රෙද්ද
  - [NOT] before: එක වෙලාවකට මේ මගුලේ  #pornස්ටාර්ස්ලා විතරයි  මොලෙත් වික්ෂිප්ත වෙනවා රෙද්ද
  - [NOT] after:  එක sometimes මේ මගුලේ  #pornස්ටාර්ස්ලා විතරයි  brain වික්ෂිප්ත වෙනවා රෙද්ද

### 3.278. `නයා` -> `cobra`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ගෑණි නයා වෙද්දි - ශිවන්‍යා නම් පොළඟා නය වෙද්දි - පොළන්‍යා..  ලොල් ඕයි...  What a creativity.... :D N. @USER  · 24 Aug 2016  @USER පොළන්‍යා
  - [NOT] after:  ගෑණි cobra වෙද්දි - ශිවන්‍යා නම් පොළඟා නය වෙද්දි - පොළන්‍යා..  ලොල් ඕයි...  What a creativity.... :D N. @USER  · 24 Aug 2016  @USER පොළන්‍යා
  - [NOT] before: ගෑණි නයා වෙද්දි - ශිවන්‍යා නම් පොළඟා නය වෙද්දි - පොළන්‍යා..  ලොල් ඕයි...  What a creativity.... :D N. @USER  · 24 Aug 2016  @USER පොළන්‍යා
  - [NOT] after:  ගෑණි cobra වෙද්දි - ශිවන්‍යා නම් පොළඟා නය වෙද්දි - පොළන්‍යා..  ලොල් ඕයි...  What a creativity.... :D N. @USER  · 24 Aug 2016  @USER පොළන්‍යා

### 3.279. `එත්` -> `but`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: උඹට මඩගහන්න.. උඹේ අඩුපාඩු දකින්නම ඔනේ තරම් කට්ටිය ඉදිවී එත් උඹේ ගමන උඹට ඔනේ විදිහට පලයන් උන්ට ඔනේ ෆුකක් කියන්න... URL
  - [OFF] after:  උඹට මඩගහන්න.. උඹේ අඩුපාඩු දකින්නම ඔනේ තරම් කට්ටිය ඉදිවී but උඹේ ගමන උඹට ඔනේ විදිහට පලයන් උන්ට ඔනේ ෆුකක් කියන්න... URL
  - [OFF] before: උඹට මඩගහන්න.. උඹේ අඩුපාඩු දකින්නම ඔනේ තරම් කට්ටිය ඉදිවී එත් උඹේ ගමන උඹට ඔනේ විදිහට පලයන් උන්ට ඔනේ ෆුකක් කියන්න... URL
  - [OFF] after:  උඹට මඩගහන්න.. උඹේ අඩුපාඩු දකින්නම ඔනේ තරම් කට්ටිය ඉදිවී but උඹේ trip උඹට ඔනේ විදිහට පලයන් උන්ට ඔනේ ෆුකක් කියන්න... URL

### 3.280. `සාරි` -> `saree`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මොකාද මේ සාරි ඇදගෙන ගාල කඩාගෙන බැන බැන ගියපු බලු හරකා..
  - [OFF] after:  මොකාද මේ saree ඇදගෙන ගාල කඩාගෙන බැන බැන ගියපු බලු හරකා..
  - [OFF] before: මොකාද මේ සාරි ඇදගෙන ගාල කඩාගෙන බැන බැන ගියපු බලු හරකා..
  - [OFF] after:  මොකාද මේ saree ඇදගෙන ගාල කඩාගෙන scold scold ගියපු බලු හරකා..

### 3.281. `කොමඩු` -> `watermelon`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ටහුඩු...  ගෙඩි 2ම කන්න ඕනි... Maduwa @USER  · 23 Jun 2019 ගුඩි මෝනිං කොමඩු කමුද වරෙන්
  - [NOT] after:  ටහුඩු...  ගෙඩි 2ම කන්න ඕනි... Maduwa @USER  · 23 Jun 2019 ගුඩි මෝනිං watermelon කමුද come
  - [NOT] before: 96.1 FM or 96.3 FM Island wide... __________________________ තඩි කොමඩු ගෙඩියක් කුඩු පට්ටම් කරන ඉබ්බෙක්..!!... URL
  - [NOT] after:  96.1 FM or 96.3 FM Island wide... __________________________ තඩි watermelon ගෙඩියක් කුඩු පට්ටම් කරන tortoise..!!... URL

### 3.282. `බනින` -> `scold`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: බනින එකා බැනපන් පැයකට එක වතාවක් වගේ,යකෝ..  තත්පරේටත් දෙක ගානෙ  හචින් ගිහින් මැරෙන්න යන්නෙ.. තරහයි කියලා එහෙම  පලි ගන්න එපා දෙයියෝ..සහ ගහනවා මේවට හරිය.
  - [OFF] after:  scold එකා බැනපන් පැයකට එක වතාවක් වගේ,යකෝ..  තත්පරේටත් දෙක ගානෙ  හචින් ගිහින් මැරෙන්න යන්නෙ.. තරහයි කියලා එහෙම  පලි ගන්න එපා දෙයියෝ..සහ ගහනවා මේවට හරිය.
  - [OFF] before: බනින එකා බැනපන් පැයකට එක වතාවක් වගේ,යකෝ..  තත්පරේටත් දෙක ගානෙ  හචින් ගිහින් මැරෙන්න යන්නෙ.. තරහයි කියලා එහෙම  පලි ගන්න එපා දෙයියෝ..සහ ගහනවා මේවට හරිය.
  - [OFF] after:  scold එකා බැනපන් පැයකට එක වතාවක් වගේ,යකෝ..  තත්පරේටත් දෙක ගානෙ  හචින් ගිහින් මැරෙන්න යන්නෙ.. තරහයි කියලා එහෙම  පලි ගන්න එපා god..සහ ගහනවා මේවට හරිය.

### 3.283. `බැන්දා` -> `married`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  බැන්දා කියන්නෙත් මැරුණා වගේ තමා.. ඒ හින්දා පලයන් එහේ
  - [NOT] after:  @USER @USER  married කියන්නෙත් මැරුණා වගේ තමා.. ඒ හින්දා පලයන් එහේ
  - [NOT] before: @USER @USER  බැන්දා කියන්නෙත් මැරුණා වගේ තමා.. ඒ හින්දා පලයන් එහේ
  - [NOT] after:  @USER @USER  married කියන්නෙත් මැරුණා වගේ තමා.. ඒ හින්දා පලයන් එහේ

### 3.284. `සැම` -> `all`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER රෝගී වූ සියලු දෙනාම ඉක්මන් සුවය ලැබේවා.. නිරෝගී සැම දෙනා ආරක්ෂා වේවා..සැමට තෙරුවන් සරණයි.
  - [NOT] after:  @USER රෝගී වූ සියලු දෙනාම quick සුවය ලැබේවා.. නිරෝගී all දෙනා ආරක්ෂා වේවා..සැමට තෙරුවන් සරණයි.
  - [NOT] before: @USER අපි සැම එක්වී අ.ජලීට හද පතුලින්ම සුභ පතමු.......... මීගමුවට....... තවත් බැබලෙන තරැවක්
  - [NOT] after:  @USER අපි all එක්වී අ.ජලීට heart පතුලින්ම සුභ පතමු.......... මීගමුවට....... තවත් බැබලෙන තරැවක්

### 3.285. `දහවෙනිදා` -> `tenth`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER දහවෙනිදා වෙනකන් දෙන්න නෑ ...
  - [NOT] after:  @USER tenth වෙනකන් දෙන්න නෑ ...
  - [NOT] before: @USER දහවෙනිදා වෙනකන් දෙන්න නෑ ...
  - [NOT] after:  @USER tenth වෙනකන් දෙන්න නෑ ...

### 3.286. `ඇගිලි` -> `fingers`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අංගුලිමාල ඇගිලි නැතුව බිජ්ජ කැපුව නම් තොරන් වලට චිත්‍රමූර්ති වලට අදින්න වෙන්නේ නැහැ නෙ.  ඒකත් වෙලාවට හරි දේ බලලා කපලා තියෙන්නේ.
  - [OFF] after:  අංගුලිමාල fingers නැතුව බිජ්ජ කැපුව නම් තොරන් වලට චිත්‍රමූර්ති වලට අදින්න වෙන්නේ නැහැ නෙ.  ඒකත් වෙලාවට හරි දේ බලලා කපලා තියෙන්නේ.
  - [OFF] before: අංගුලිමාල ඇගිලි නැතුව බිජ්ජ කැපුව නම් තොරන් වලට චිත්‍රමූර්ති වලට අදින්න වෙන්නේ නැහැ නෙ.  ඒකත් වෙලාවට හරි දේ බලලා කපලා තියෙන්නේ.
  - [OFF] after:  අංගුලිමාල fingers නැතුව බිජ්ජ කැපුව නම් තොරන් වලට චිත්‍රමූර්ති වලට අදින්න වෙන්නේ නැහැ නෙ.  ඒකත් වෙලාවට හරි දේ බලලා cut තියෙන්නේ.

### 3.287. `කැටයම්` -> `carvings`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ටහුඩු. ඒකි  ꧁𓊈𒆜𝕊ᗩ爪卩ꪖㄒꫝ𒆜𓊉꧂ @USER  · 3 Mar 2020 එ්කිගේ කැටයම්
  - [OFF] after:  ටහුඩු. ඒකි  ꧁𓊈𒆜𝕊ᗩ爪卩ꪖㄒꫝ𒆜𓊉꧂ @USER  · 3 Mar 2020 එ්කිගේ carvings
  - [OFF] before: ටහුඩු. ඒකි  ꧁𓊈𒆜𝕊ᗩ爪卩ꪖㄒꫝ𒆜𓊉꧂ @USER  · 3 Mar 2020 එ්කිගේ කැටයම්
  - [OFF] after:  ටහුඩු. ඒකි  ꧁𓊈𒆜𝕊ᗩ爪卩ꪖㄒꫝ𒆜𓊉꧂ @USER  · 3 Mar 2020 එ්කිගේ carvings

### 3.288. `වහල්` -> `slave`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER    පුලුවන් නම් ගලවල පෙන්නපන්. තොගේ බිජ්ජ කපලා poster ගහවි! වහල් රිලවා!
  - [OFF] after:  @USER  @USER    පුලුවන් නම් ගලවල පෙන්නපන්. තොගේ බිජ්ජ කපලා poster ගහවි! slave රිලවා!
  - [OFF] before: @USER  @USER    පුලුවන් නම් ගලවල පෙන්නපන්. තොගේ බිජ්ජ කපලා poster ගහවි! වහල් රිලවා!
  - [OFF] after:  @USER  @USER    පුලුවන් නම් ගලවල පෙන්නපන්. තොගේ බිජ්ජ cut poster ගහවි! slave රිලවා!

### 3.289. `මිනිහ` -> `guy`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: රිලාජ් පව් නේ. මිනිහ මැරුණු ගෑණි වගේ අඬන්නේ
  - [NOT] after:  රිලාජ් පව් නේ. guy මැරුණු ගෑණි වගේ අඬන්නේ
  - [NOT] before: රිලාජ් පව් නේ. මිනිහ මැරුණු ගෑණි වගේ අඬන්නේ
  - [NOT] after:  රිලාජ් පව් නේ. guy dead ගෑණි වගේ අඬන්නේ

### 3.290. `තොපෙ` -> `your`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER පක තමා තොපෙ
  - [OFF] after:  @USER  @USER පක තමා your
  - [OFF] before: @USER  @USER පක තමා තොපෙ
  - [OFF] after:  @USER  @USER පක තමා your

### 3.291. `ලියන්නේ` -> `writing`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER වෙනදට කියලා එන කිඹුලා අද නොකියා ඇවිත් ද ? කව්ද ඕයි මේ හෙඩිං ලියන්නේ
  - [NOT] after:  @USER වෙනදට කියලා එන කිඹුලා අද නොකියා ඇවිත් ද ? කව්ද ඕයි මේ හෙඩිං writing
  - [NOT] before: @USER වෙනදට කියලා එන කිඹුලා අද නොකියා ඇවිත් ද ? කව්ද ඕයි මේ හෙඩිං ලියන්නේ
  - [NOT] after:  @USER වෙනදට කියලා එන කිඹුලා අද නොකියා ඇවිත් ද ? කව්ද ඕයි මේ හෙඩිං writing

### 3.292. `හ්ම්ම්ම්` -> `hmm`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හ්ම්ම්ම් හ්ම්ම්ම්...  කොහෙන්ද හිනාවෙන්නෝනි
  - [NOT] after:  @USER hmm hmm...  කොහෙන්ද හිනාවෙන්නෝනි
  - [NOT] before: @USER හ්ම්ම්ම් හ්ම්ම්ම්...  කොහෙන්ද හිනාවෙන්නෝනි
  - [NOT] after:  @USER hmm hmm...  where from හිනාවෙන්නෝනි

### 3.293. `අඬන්න` -> `cry`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඒ උනාට අඬන්න එපා සාදු හොඳේ
  - [NOT] after:  @USER ඒ උනාට cry එපා සාදු හොඳේ
  - [NOT] before: @USER ඒ උනාට අඬන්න එපා සාදු හොඳේ
  - [NOT] after:  @USER ඒ උනාට cry එපා සාදු හොඳේ

### 3.294. `අලුතෙන්` -> `newly`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ටහුඩු DP එක ,මන් ඒත් බැලුවා කවුද මේ අලුතෙන් බැහැලු කෑල්ල කීලා
  - [OFF] after:  @USER ටහුඩු DP එක ,මන් ඒත් බැලුවා කවුද මේ newly බැහැලු කෑල්ල කීලා
  - [OFF] before: @USER ටහුඩු DP එක ,මන් ඒත් බැලුවා කවුද මේ අලුතෙන් බැහැලු කෑල්ල කීලා
  - [OFF] after:  @USER ටහුඩු DP එක ,මන් ඒත් බැලුවා කවුද මේ newly බැහැලු girl කීලා

### 3.295. `එකක්‌` -> `one`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මං කවදද බූරුවෝ match එකක්‌ නොබැලුවේ. තමුසෙ කට වහන් බලනවා
  - [OFF] after:  @USER මං කවදද බූරුවෝ match one නොබැලුවේ. තමුසෙ කට වහන් බලනවා
  - [OFF] before: @USER මං කවදද බූරුවෝ match එකක්‌ නොබැලුවේ. තමුසෙ කට වහන් බලනවා
  - [OFF] after:  @USER මං කවදද බූරුවෝ match one නොබැලුවේ. තමුසෙ කට වහන් බලනවා

### 3.296. `නුඹ` -> `you`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මක්නිසාද නපුරු ක්‍රියා කරන්නෝ සිඳිනු ලබන්නනෝය.   නුමුත් ස්වාමීන් කෙරෙහි බලා සිටින්නෝ දේශය උරුමකරගන්නෝය.   මද කලකින් දුෂ්ටයා නැතිවන්නේය. එසේය, නුඹ ඔහුගේ ස්ථානය පරීක්ෂාකර බලන්නෙහිය,  ඔහු සම්බනොවන්නේය.  ගීතාවලිය 37:9-10
  - [NOT] after:  @USER මක්නිසාද නපුරු ක්‍රියා කරන්නෝ සිඳිනු ලබන්නනෝය.   නුමුත් ස්වාමීන් කෙරෙහි බලා සිටින්නෝ දේශය උරුමකරගන්නෝය.   මද කලකින් දුෂ්ටයා නැතිවන්නේය. එසේය, you ඔහුගේ ස්ථානය පරීක්ෂාකර බලන්නෙහිය,  ඔහු සම්බනොවන්නේය.  ගීතාවලිය 37:9-10
  - [NOT] before: @USER මක්නිසාද නපුරු ක්‍රියා කරන්නෝ සිඳිනු ලබන්නනෝය.   නුමුත් ස්වාමීන් කෙරෙහි බලා සිටින්නෝ දේශය උරුමකරගන්නෝය.   මද කලකින් දුෂ්ටයා නැතිවන්නේය. එසේය, නුඹ ඔහුගේ ස්ථානය පරීක්ෂාකර බලන්නෙහිය,  ඔහු සම්බනොවන්නේය.  ගීතාවලිය 37:9-10
  - [NOT] after:  @USER මක්නිසාද නපුරු ක්‍රියා කරන්නෝ සිඳිනු ලබන්නනෝය.   නුමුත් ස්වාමීන් කෙරෙහි බලා සිටින්නෝ දේශය උරුමකරගන්නෝය.   මද කලකින් දුෂ්ටයා නැතිවන්නේය. එසේය, you his ස්ථානය පරීක්ෂාකර බලන්නෙහිය,  ඔහු සම්බනොවන්නේය.  ගීතාවලිය 37:9-10

### 3.297. `බැවින්` -> `since`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අලි නාවන තඩි වල වල් TL එකේ ඇති බැවින් තමාගෙ ආරක්ශාව තමන් සලසගන්න..!
  - [NOT] after:  elephants නාවන තඩි වල වල් TL එකේ ඇති since තමාගෙ ආරක්ශාව තමන් සලසගන්න..!
  - [NOT] before: @USER ඉතාමත් ඉහලින් සමත් වු බැවින් විභාග කොමසාරිස් ඉල්ලා අස් විය.
  - [NOT] after:  @USER very ඉහලින් සමත් වු since විභාග කොමසාරිස් ඉල්ලා අස් විය.

### 3.298. `මැස්සො` -> `flies`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER නිල මැස්සො වගේ මුන්. ඒතරං අප්පිරියයි දැං..
  - [OFF] after:  @USER නිල flies වගේ මුන්. ඒතරං අප්පිරියයි දැං..
  - [OFF] before: @USER නිල මැස්සො වගේ මුන්. ඒතරං අප්පිරියයි දැං..
  - [OFF] after:  @USER නිල flies වගේ මුන්. that much අප්පිරියයි දැං..

### 3.299. `ශීමේල්` -> `shemale`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අනේ දෙයියනේ මූට සෙට්වෙයං තඩි ශීමේල් දෙකක්
  - [NOT] after:  @USER අනේ දෙයියනේ මූට සෙට්වෙයං තඩි shemale දෙකක්
  - [NOT] before: @USER අනේ දෙයියනේ මූට සෙට්වෙයං තඩි ශීමේල් දෙකක්
  - [NOT] after:  @USER අනේ දෙයියනේ මූට සෙට්වෙයං තඩි shemale දෙකක්

### 3.300. `මලික්` -> `Malik`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මලික් සමරවික්‍රම  ? #srilanka
  - [NOT] after:  @USER Malik සමරවික්‍රම  ? #srilanka
  - [NOT] before: @USER මලික් සමරවික්‍රම  ? #srilanka
  - [NOT] after:  @USER Malik සමරවික්‍රම  ? #srilanka

### 3.301. `ඔක්කොටම` -> `all`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  ඇත්තටම රෙද්ද තමයි ඔක්කොටම මුල
  - [NOT] after:  @USER @USER  ඇත්තටම රෙද්ද තමයි all මුල
  - [NOT] before: @USER @USER  ඇත්තටම රෙද්ද තමයි ඔක්කොටම මුල
  - [NOT] after:  @USER @USER  ඇත්තටම රෙද්ද තමයි all මුල

### 3.302. `එකපාරටම` -> `suddenly`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඇත්ත ම කිව්වොත් කව්ද බල්ලා කියල හොයාගන්න අමාරු උනා එකපාරටම ටිකක් .
  - [NOT] after:  @USER ඇත්ත ම කිව්වොත් කව්ද බල්ලා කියල හොයාගන්න අමාරු උනා suddenly ටිකක් .
  - [NOT] before: @USER ඇත්ත ම කිව්වොත් කව්ද බල්ලා කියල හොයාගන්න අමාරු උනා එකපාරටම ටිකක් .
  - [NOT] after:  @USER ඇත්ත ම කිව්වොත් කව්ද බල්ලා කියල find අමාරු උනා suddenly ටිකක් .

### 3.303. `ප්‍රවෘත්තිත්` -> `news`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER උබලගෙ ප්‍රවෘත්තිත් වෙපා කාලකන්න
  - [NOT] after:  @USER උබලගෙ news වෙපා කාලකන්න
  - [NOT] before: @USER උබලගෙ ප්‍රවෘත්තිත් වෙපා කාලකන්න
  - [NOT] after:  @USER උබලගෙ news වෙපා කාලකන්න

### 3.304. `පාලම්` -> `bridge`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අම්මගේ රෙද්ද තමයි..... රටම පාවා දුන්න අවජාතකයාගේ මඩ හාේදන පාලම් කොක්කු ඉන්නවනේ.... URL
  - [OFF] after:  අම්මගේ රෙද්ද තමයි..... රටම පාවා දුන්න අවජාතකයාගේ මඩ හාේදන bridge කොක්කු ඉන්නවනේ.... URL
  - [OFF] before: අම්මගේ රෙද්ද තමයි..... රටම පාවා දුන්න අවජාතකයාගේ මඩ හාේදන පාලම් කොක්කු ඉන්නවනේ.... URL
  - [OFF] after:  අම්මගේ රෙද්ද තමයි..... රටම පාවා දුන්න අවජාතකයාගේ mud හාේදන bridge කොක්කු ඉන්නවනේ.... URL

### 3.305. `ආයුධ` -> `weapons`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER කැරි තම්බියා, ආයුධ පෙන්නන්න එක්ක ගියා නම් හරි
  - [OFF] after:  @USER කැරි තම්බියා, weapons පෙන්නන්න එක්ක ගියා නම් හරි
  - [OFF] before: @USER කැරි තම්බියා, ආයුධ පෙන්නන්න එක්ක ගියා නම් හරි
  - [OFF] after:  @USER කැරි තම්බියා, weapons show එක්ක ගියා නම් හරි

### 3.306. `මිහිරි` -> `sweet`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අප්ෙපාචිචලා මිහිරි තිරන ගත්ත කියලත් මතකයක් නෑ ආයුෙබාවන්
  - [NOT] after:  @USER අප්ෙපාචිචලා sweet තිරන ගත්ත කියලත් මතකයක් නෑ ආයුෙබාවන්
  - [NOT] before: @USER අප්ෙපාචිචලා මිහිරි තිරන ගත්ත කියලත් මතකයක් නෑ ආයුෙබාවන්
  - [NOT] after:  @USER අප්ෙපාචිචලා sweet තිරන ගත්ත කියලත් මතකයක් නෑ ආයුෙබාවන්

### 3.307. `දුවයි` -> `daughter`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පක ලොකු පුතයි කට ලොකු දුවයි තමයි ඉතිං
  - [OFF] after:  @USER පක ලොකු පුතයි කට ලොකු daughter තමයි ඉතිං
  - [OFF] before: @USER පක ලොකු පුතයි කට ලොකු දුවයි තමයි ඉතිං
  - [OFF] after:  @USER පක ලොකු son කට ලොකු daughter තමයි ඉතිං

### 3.308. `හාමුදුරුවෝත්` -> `monk`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER සෝම හාමුදුරුවෝත් නැතිලු  game කාරයො
  - [NOT] after:  @USER සෝම monk නැතිලු  game කාරයො
  - [NOT] before: @USER සෝම හාමුදුරුවෝත් නැතිලු  game කාරයො
  - [NOT] after:  @USER සෝම monk නැතිලු  game කාරයො

### 3.309. `කැරපොත්තා` -> `cockroach`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ගොනා හරකා කැරපොත්තා හිකනලා බස්සා ඌරු මීයා ඌරා වල් ඌරා ගෙම්බා තලගොයා හැකරැල්ලා කපුටා මයිනා
  - [OFF] after:  @USER ගොනා හරකා cockroach හිකනලා බස්සා ඌරු මීයා ඌරා වල් ඌරා ගෙම්බා තලගොයා හැකරැල්ලා කපුටා මයිනා
  - [OFF] before: @USER ගොනා හරකා කැරපොත්තා හිකනලා බස්සා ඌරු මීයා ඌරා වල් ඌරා ගෙම්බා තලගොයා හැකරැල්ලා කපුටා මයිනා
  - [OFF] after:  @USER ගොනා හරකා cockroach හිකනලා බස්සා ඌරු මීයා ඌරා වල් ඌරා ගෙම්බා තලගොයා හැකරැල්ලා crow මයිනා

### 3.310. `වැඩියි` -> `too much`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER දගලනවා වැඩියි ඒකි
  - [NOT] after:  @USER  @USER දගලනවා too much ඒකි
  - [NOT] before: @USER  @USER දගලනවා වැඩියි ඒකි
  - [NOT] after:  @USER  @USER දගලනවා too much ඒකි

### 3.311. `බේත්` -> `medicine`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අම්මට බේත් ටික අරන් දෙන්න වත් යන්න දෙන්න පිං
  - [NOT] after:  @USER අම්මට medicine ටික අරන් දෙන්න වත් යන්න දෙන්න පිං
  - [NOT] before: @USER අම්මට බේත් ටික අරන් දෙන්න වත් යන්න දෙන්න පිං
  - [NOT] after:  @USER අම්මට medicine ටික අරන් දෙන්න වත් යන්න දෙන්න පිං

### 3.312. `මෙන්` -> `like`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ටයරය මැදින් පෙකනිය ඉහලට රුප්පා සළු පිලි හැර දමා පෙන්වන් නී පුප්පා තන් හංසයන් වන් මෙන් chathu @USER  · 12 Nov 2015 පෙකණිය නො දක්වා සළු ඇඳ බොලට දක්වා නොපව තන සක්වා සිනා නොමසන් දසන් දක්වා - කාව්‍යශේඛරය -
  - [NOT] after:  ටයරය මැදින් පෙකනිය ඉහලට රුප්පා සළු පිලි හැර දමා පෙන්වන් නී පුප්පා තන් හංසයන් වන් like chathu @USER  · 12 Nov 2015 පෙකණිය නො දක්වා සළු ඇඳ බොලට දක්වා නොපව තන සක්වා සිනා නොමසන් දසන් දක්වා - කාව්‍යශේඛරය -
  - [NOT] before: ටයරය මැදින් පෙකනිය ඉහලට රුප්පා සළු පිලි හැර දමා පෙන්වන් නී පුප්පා තන් හංසයන් වන් මෙන් chathu @USER  · 12 Nov 2015 පෙකණිය නො දක්වා සළු ඇඳ බොලට දක්වා නොපව තන සක්වා සිනා නොමසන් දසන් දක්වා - කාව්‍යශේඛරය -
  - [NOT] after:  ටයරය මැදින් පෙකනිය ඉහලට රුප්පා සළු පිලි හැර දමා පෙන්වන් නී පුප්පා තන් හංසයන් වන් like chathu @USER  · 12 Nov 2015 පෙකණිය නො දක්වා සළු ඇඳ බොලට දක්වා නොපව තන සක්වා සිනා නොමසන් දසන් දක්වා - කාව්‍යශේඛරය -

### 3.313. `බඩවල්` -> `bellies`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඔයාලට වගේ කැත තඩි බඩවල් අපිට නැ
  - [OFF] after:  @USER ඔයාලට වගේ කැත තඩි bellies අපිට නැ
  - [OFF] before: @USER ඔයාලට වගේ කැත තඩි බඩවල් අපිට නැ
  - [OFF] after:  @USER ඔයාලට වගේ කැත තඩි bellies අපිට නැ

### 3.314. `කළා` -> `did`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER ජූඩි ඔයා එච්චර මෝඩ වැඩක් කළා කියලා මට විශ්වාස කරන්නත් බෑ
  - [NOT] after:  @USER  @USER ජූඩි ඔයා එච්චර මෝඩ වැඩක් did කියලා මට විශ්වාස කරන්නත් බෑ
  - [NOT] before: @USER  @USER ජූඩි ඔයා එච්චර මෝඩ වැඩක් කළා කියලා මට විශ්වාස කරන්නත් බෑ
  - [NOT] after:  @USER  @USER ජූඩි ඔයා that much මෝඩ වැඩක් did කියලා මට විශ්වාස කරන්නත් බෑ

### 3.315. `ක්වින්ඩාඕ` -> `Qingdao`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ක්වින්ඩාඕ නෙවෙයි යකෝ ඡිංදාඹ්.
  - [NOT] after:  @USER Qingdao නෙවෙයි යකෝ ඡිංදාඹ්.
  - [NOT] before: @USER ක්වින්ඩාඕ නෙවෙයි යකෝ ඡිංදාඹ්.
  - [NOT] after:  @USER Qingdao නෙවෙයි යකෝ ඡිංදාඹ්.

### 3.316. `ගඩොල්` -> `brick`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මුලින්ම බලද්දි දැක්කෙ ගඩොල් කැට ටිකක් වගේපස්සෙ තමා #Caption එක දැක්කෙ
  - [NOT] after:  @USER මුලින්ම බලද්දි දැක්කෙ brick කැට ටිකක් වගේපස්සෙ තමා #Caption එක දැක්කෙ
  - [NOT] before: @USER මුලින්ම බලද්දි දැක්කෙ ගඩොල් කැට ටිකක් වගේපස්සෙ තමා #Caption එක දැක්කෙ
  - [NOT] after:  @USER මුලින්ම බලද්දි දැක්කෙ brick blocks ටිකක් වගේපස්සෙ තමා #Caption එක දැක්කෙ

### 3.317. `ගැහැණු` -> `women`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: කුළු මිමාගේ ගැහැණු සතා කුළු බඩුව වේ .. මාළුවාගේ ගැහැණු සතා මාළු කැල්ල වන අතර හාවාගේ ගැහැණු සතා හා හා ලදේ වේ ..... URL
  - [NOT] after:  කුළු මිමාගේ women සතා කුළු බඩුව වේ .. මාළුවාගේ women සතා මාළු කැල්ල වන අතර හාවාගේ women සතා හා හා ලදේ වේ ..... URL
  - [NOT] before: කුළු මිමාගේ ගැහැණු සතා කුළු බඩුව වේ .. මාළුවාගේ ගැහැණු සතා මාළු කැල්ල වන අතර හාවාගේ ගැහැණු සතා හා හා ලදේ වේ ..... URL
  - [NOT] after:  කුළු මිමාගේ women සතා කුළු බඩුව වේ .. මාළුවාගේ women සතා fish කැල්ල වන අතර හාවාගේ women සතා හා හා ලදේ වේ ..... URL

### 3.318. `සීනී` -> `sugar`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER අඩො උඹ අද සීනී 500 ක් අරන් කලුබොවිල හිටිය ද ?
  - [NOT] after:  @USER  @USER අඩො උඹ අද sugar 500 ක් අරන් කලුබොවිල හිටිය ද ?
  - [NOT] before: @USER  @USER අඩො උඹ අද සීනී 500 ක් අරන් කලුබොවිල හිටිය ද ?
  - [NOT] after:  @USER  @USER අඩො උඹ අද sugar 500 ක් අරන් Kalubowila හිටිය ද ?

### 3.319. `සොඳුර` -> `darling`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ටහුඩු.. තපස්සු සොඳුර කියන්නේ නෑ බං..
  - [NOT] after:  ටහුඩු.. තපස්සු darling කියන්නේ නෑ බං..
  - [NOT] before: ටහුඩු.. තපස්සු සොඳුර කියන්නේ නෑ බං..
  - [NOT] after:  ටහුඩු.. තපස්සු darling කියන්නේ නෑ බං..

### 3.320. `පුරුදු` -> `habit`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: නුහුරු සෙනෙහසේ.. හුරු පුරුදු තනිකම හොයන... එකම එක අන් ගොනා... මන්   ඕයි.... :/
  - [NOT] after:  නුහුරු සෙනෙහසේ.. හුරු habit තනිකම හොයන... එකම එක අන් ගොනා... මන්   ඕයි.... :/
  - [NOT] before: නුහුරු සෙනෙහසේ.. හුරු පුරුදු තනිකම හොයන... එකම එක අන් ගොනා... මන්   ඕයි.... :/
  - [NOT] after:  නුහුරු සෙනෙහසේ.. හුරු habit තනිකම හොයන... එකම එක other ගොනා... මන්   ඕයි.... :/

### 3.321. `උගත්කම` -> `education`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මේ උගත්කම ද? මෝඩ කමද?  URL
  - [NOT] after:  මේ education ද? මෝඩ කමද?  URL
  - [NOT] before: මේ උගත්කම ද? මෝඩ කමද?  URL
  - [NOT] after:  මේ education ද? මෝඩ කමද?  URL

### 3.322. `හැමොටම` -> `everyone`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: රෙද්ද ඉස්සුවාට වැඩක් නෑ  @USER  වගේ නමල ගන්න හැමොටම බෑ.. The following media includes potentially sensitive content. Change settings View
  - [NOT] after:  රෙද්ද ඉස්සුවාට වැඩක් නෑ  @USER  වගේ නමල ගන්න everyone බෑ.. The following media includes potentially sensitive content. Change settings View
  - [NOT] before: රෙද්ද ඉස්සුවාට වැඩක් නෑ  @USER  වගේ නමල ගන්න හැමොටම බෑ.. The following media includes potentially sensitive content. Change settings View
  - [NOT] after:  රෙද්ද ඉස්සුවාට work නෑ  @USER  වගේ නමල ගන්න everyone බෑ.. The following media includes potentially sensitive content. Change settings View

### 3.323. `කොන්ඩේ` -> `hair`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අනේ බාබරයෝ, ඉක්මනට Nimalkaගේ කොන්ඩේ කපහං..  උඹේ සාප්පුවේ දාලා තියෙන මේ ආදරයයි ඇහෙන කොට වමනෙට එනවා යකෝ — feeling... URL
  - [OFF] after:  අනේ බාබරයෝ, ඉක්මනට Nimalkaගේ hair කපහං..  උඹේ සාප්පුවේ දාලා තියෙන මේ ආදරයයි ඇහෙන කොට වමනෙට එනවා යකෝ — feeling... URL
  - [OFF] before: අනේ බාබරයෝ, ඉක්මනට Nimalkaගේ කොන්ඩේ කපහං..  උඹේ සාප්පුවේ දාලා තියෙන මේ ආදරයයි ඇහෙන කොට වමනෙට එනවා යකෝ — feeling... URL
  - [OFF] after:  අනේ බාබරයෝ, quickly Nimalkaගේ hair කපහං..  උඹේ සාප්පුවේ දාලා තියෙන මේ ආදරයයි ඇහෙන කොට වමනෙට එනවා යකෝ — feeling... URL

### 3.324. `නිදහසේ` -> `freely`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: චික් නොදකින් අසහනකාරයා නාකි ගෑනියෙකුට නිදහසේ යන්න නෑනේ
  - [OFF] after:  චික් නොදකින් අසහනකාරයා නාකි ගෑනියෙකුට freely යන්න නෑනේ
  - [OFF] before: චික් නොදකින් අසහනකාරයා නාකි ගෑනියෙකුට නිදහසේ යන්න නෑනේ
  - [OFF] after:  චික් නොදකින් අසහනකාරයා නාකි ගෑනියෙකුට freely යන්න නෑනේ

### 3.325. `තෙත්` -> `wet`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER උඹ නිකන් තෙත් කරා වගේ කියන්නෙ. උබනේ යකෝ තෙත් කරගෙන ආවෙ
  - [OFF] after:  @USER උඹ නිකන් wet කරා වගේ කියන්නෙ. උබනේ යකෝ wet කරගෙන ආවෙ
  - [OFF] before: @USER උඹ නිකන් තෙත් කරා වගේ කියන්නෙ. උබනේ යකෝ තෙත් කරගෙන ආවෙ
  - [OFF] after:  @USER උඹ නිකන් wet කරා වගේ කියන්නෙ. උබනේ යකෝ wet කරගෙන ආවෙ

### 3.326. `කකුලට` -> `leg එකට`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කන පැලෙන්න ගහනව කකුලට, බල්ලා. #SriLankanThreats
  - [OFF] after:  කන පැලෙන්න ගහනව leg එකට, බල්ලා. #SriLankanThreats
  - [OFF] before: කන පැලෙන්න ගහනව කකුලට, බල්ලා. #SriLankanThreats
  - [OFF] after:  කන පැලෙන්න ගහනව leg එකට, dog. #SriLankanThreats

### 3.327. `රජා` -> `king`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පොන්න රජා..පොන්සියා.  පක බුරියා...කැරි තඩියා .  අඟලේ පකා...
  - [OFF] after:  @USER පොන්න king..පොන්සියා.  පක බුරියා...කැරි තඩියා .  අඟලේ පකා...
  - [OFF] before: @USER පොන්න රජා..පොන්සියා.  පක බුරියා...කැරි තඩියා .  අඟලේ පකා...
  - [OFF] after:  @USER පොන්න king..පොන්සියා.  පක බුරියා...කැරි තඩියා .  inch පකා...

### 3.328. `ගොඩවල්` -> `heaps`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER දැන් ගූ ගොඩවල් HD වලින් බලන්න පුලුවන්... මරු
  - [NOT] after:  @USER දැන් ගූ heaps HD වලින් බලන්න පුලුවන්... මරු
  - [NOT] before: @USER දැන් ගූ ගොඩවල් HD වලින් බලන්න පුලුවන්... මරු
  - [NOT] after:  @USER දැන් ගූ heaps HD වලින් බලන්න පුලුවන්... මරු

### 3.329. `ලන්කාවත්` -> `Lanka`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  රාජපක්ලා යුද්දෙ ඉවර කරෙ නැත්තම් ලන්කාවත් ඔය වගෙ තමා
  - [NOT] after:  @USER  රාජපක්ලා යුද්දෙ ඉවර කරෙ නැත්තම් Lanka ඔය වගෙ තමා
  - [NOT] before: @USER  රාජපක්ලා යුද්දෙ ඉවර කරෙ නැත්තම් ලන්කාවත් ඔය වගෙ තමා
  - [NOT] after:  @USER  රාජපක්ලා war ඉවර කරෙ නැත්තම් Lanka ඔය වගෙ තමා

### 3.330. `කෙලින්ම` -> `directly`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කෙලින්ම යම ලොවට ඇරියොත්.
  - [NOT] after:  @USER directly යම ලොවට ඇරියොත්.
  - [NOT] before: @USER කෙලින්ම යම ලොවට ඇරියොත්.
  - [NOT] after:  @USER directly යම ලොවට ඇරියොත්.

### 3.331. `ආස` -> `like`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මමත් ආස ලොකු තන් ලොකු පුක් තමා ඉතින්
  - [OFF] after:  @USER මමත් like ලොකු තන් ලොකු පුක් තමා ඉතින්
  - [OFF] before: @USER මමත් ආස ලොකු තන් ලොකු පුක් තමා ඉතින්
  - [OFF] after:  @USER මමත් like ලොකු තන් ලොකු පුක් තමා ඉතින්

### 3.332. `හම` -> `skin`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පලතුරු කෑවම හම පැහැපත් වෙනවලු...  ආච්චිගේ රෙද්ද  මීට, #වදුරෝ
  - [NOT] after:  පලතුරු කෑවම skin පැහැපත් වෙනවලු...  ආච්චිගේ රෙද්ද  මීට, #වදුරෝ
  - [NOT] before: පලතුරු කෑවම හම පැහැපත් වෙනවලු...  ආච්චිගේ රෙද්ද  මීට, #වදුරෝ
  - [NOT] after:  fruits කෑවම skin පැහැපත් වෙනවලු...  ආච්චිගේ රෙද්ද  මීට, #වදුරෝ

### 3.333. `ඡාතික` -> `national`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පොන්ගල සමනලවීර. ඡාතික ශාපී.......... .
  - [OFF] after:  @USER පොන්ගල සමනලවීර. national ශාපී.......... .
  - [OFF] before: @USER පොන්ගල සමනලවීර. ඡාතික ශාපී.......... .
  - [OFF] after:  @USER පොන්ගල සමනලවීර. national ශාපී.......... .

### 3.334. `එවුන්ගෙ` -> `their`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER අපේ එවුන්ගෙ කිවු කිම්බ
  - [OFF] after:  @USER අපේ their කිවු කිම්බ
  - [OFF] before: @USER අපේ එවුන්ගෙ කිවු කිම්බ
  - [OFF] after:  @USER අපේ their කිවු කිම්බ

### 3.335. `තවම` -> `still`
- impact: 2 posts (0 light, 2 heavy), 1 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  @USER  @USER  @USER  පල ඩෝ යන්න.අපි ඔය පිලිපීන් එවුන් පස්සෙ යන්නෙ නෑ...යකෝ අපි තවම වර්ජින්....පී
  - [OFF] after:  @USER @USER  @USER  @USER  @USER  පල ඩෝ යන්න.අපි ඔය පිලිපීන් එවුන් පස්සෙ යන්නෙ නෑ...යකෝ අපි still වර්ජින්....P
  - [NOT] before: අද නම් කන්න ගෙනාවා.... තවම කන්න හම්බුනේ නෑ....... මෙහෙමත් කරුම.
  - [NOT] after:  අද නම් eat ගෙනාවා.... still eat හම්බුනේ නෑ....... මෙහෙමත් කරුම.

### 3.336. `ඉක්මන්` -> `quick`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER රෝගී වූ සියලු දෙනාම ඉක්මන් සුවය ලැබේවා.. නිරෝගී සැම දෙනා ආරක්ෂා වේවා..සැමට තෙරුවන් සරණයි.
  - [NOT] after:  @USER රෝගී වූ සියලු දෙනාම quick සුවය ලැබේවා.. නිරෝගී සැම දෙනා ආරක්ෂා වේවා..සැමට තෙරුවන් සරණයි.
  - [NOT] before: @USER රෝගී වූ සියලු දෙනාම ඉක්මන් සුවය ලැබේවා.. නිරෝගී සැම දෙනා ආරක්ෂා වේවා..සැමට තෙරුවන් සරණයි.
  - [NOT] after:  @USER රෝගී වූ සියලු දෙනාම quick සුවය ලැබේවා.. නිරෝගී all දෙනා ආරක්ෂා වේවා..සැමට තෙරුවන් සරණයි.

### 3.337. `කීවා` -> `said`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ඇත්ත කීවනම් මන් මොනාත් කියන් නෑ නේ..ඇයි බොරැ කීවේ මට ඒ වෙලේ ...   ඇත්ත කීවා කියහන්කෝ...  තමුසෙ මහ බූරුවෙක් වංචාකාරයෙක් තක්කඩියෙක් ..... පලප් මගෙ දෑහට නොපෙනි ..  #bestexcuseslka
  - [OFF] after:  ඇත්ත කීවනම් මන් මොනාත් කියන් නෑ නේ..ඇයි බොරැ කීවේ මට ඒ වෙලේ ...   ඇත්ත said කියහන්කෝ...  තමුසෙ මහ බූරුවෙක් වංචාකාරයෙක් තක්කඩියෙක් ..... පලප් මගෙ දෑහට නොපෙනි ..  #bestexcuseslka
  - [OFF] before: ඇත්ත කීවනම් මන් මොනාත් කියන් නෑ නේ..ඇයි බොරැ කීවේ මට ඒ වෙලේ ...   ඇත්ත කීවා කියහන්කෝ...  තමුසෙ මහ බූරුවෙක් වංචාකාරයෙක් තක්කඩියෙක් ..... පලප් මගෙ දෑහට නොපෙනි ..  #bestexcuseslka
  - [OFF] after:  ඇත්ත කීවනම් මන් මොනාත් කියන් නෑ නේ..ඇයි lie කීවේ මට ඒ වෙලේ ...   ඇත්ත said කියහන්කෝ...  තමුසෙ මහ බූරුවෙක් වංචාකාරයෙක් තක්කඩියෙක් ..... පලප් මගෙ දෑහට නොපෙනි ..  #bestexcuseslka

### 3.338. `අම්මේ` -> `mom`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ,  @USER  @USER මේ පත්තිනි අම්මේ.  තී වතාවක් දරෙන් රෙද්ද ගලවගත්තැහේ මේ පාර තිගෙ බොඩියවත් ඉතිරිවෙන්නේ නෑ තංගැට දෙක වහගන්ටවත්. ආං ඒක මතක තියාන අටවගත්ත රෙද්දවල් අකුලන හුම්මෙ ගහන එන දරත් ඇන්න පල   ගත්තරු පරට්ටි එනවා මෙතන ජාතක මයින්ඩ
  - [OFF] after:  @USER ,  @USER  @USER මේ පත්තිනි mom.  තී වතාවක් දරෙන් රෙද්ද ගලවගත්තැහේ මේ පාර තිගෙ බොඩියවත් ඉතිරිවෙන්නේ නෑ තංගැට දෙක වහගන්ටවත්. ආං ඒක මතක තියාන අටවගත්ත රෙද්දවල් අකුලන හුම්මෙ ගහන එන දරත් ඇන්න පල   ගත්තරු පරට්ටි එනවා මෙතන ජාතක මයින්ඩ
  - [OFF] before: @USER ,  @USER  @USER මේ පත්තිනි අම්මේ.  තී වතාවක් දරෙන් රෙද්ද ගලවගත්තැහේ මේ පාර තිගෙ බොඩියවත් ඉතිරිවෙන්නේ නෑ තංගැට දෙක වහගන්ටවත්. ආං ඒක මතක තියාන අටවගත්ත රෙද්දවල් අකුලන හුම්මෙ ගහන එන දරත් ඇන්න පල   ගත්තරු පරට්ටි එනවා මෙතන ජාතක මයින්ඩ
  - [OFF] after:  @USER ,  @USER  @USER මේ පත්තිනි mom.  තී වතාවක් දරෙන් රෙද්ද ගලවගත්තැහේ මේ පාර තිගෙ බොඩියවත් ඉතිරිවෙන්නේ නෑ තංගැට දෙක වහගන්ටවත්. ආං ඒක මතක තියාන අටවගත්ත රෙද්දවල් අකුලන හුම්මෙ ගහන එන දරත් ඇන්න පල   ගත්තරු පරට්ටි එනවා මෙතන ජාතක මයින්ඩ

### 3.339. `පනුවො` -> `worms`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මෙවගෙ එවුන්න්ව පනුවො ගහල මරෙන්න ඔන සක්කිලි හැත්ත .... URL
  - [OFF] after:  මෙවගෙ එවුන්න්ව worms ගහල මරෙන්න ඔන සක්කිලි හැත්ත .... URL
  - [OFF] before: මෙවගෙ එවුන්න්ව පනුවො ගහල මරෙන්න ඔන සක්කිලි හැත්ත .... URL
  - [OFF] after:  මෙවගෙ එවුන්න්ව worms ගහල මරෙන්න ඔන සක්කිලි හැත්ත .... URL

### 3.340. `පූසා` -> `cat`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: තඩි පූසා කවදාවත් නැතුව මගේ ළඟ නිදි  මූට මොනව වෙලාද මන්ද
  - [NOT] after:  තඩි cat කවදාවත් නැතුව මගේ ළඟ නිදි  මූට මොනව වෙලාද මන්ද
  - [NOT] before: තඩි පූසා කවදාවත් නැතුව මගේ ළඟ නිදි  මූට මොනව වෙලාද මන්ද
  - [NOT] after:  තඩි cat කවදාවත් නැතුව මගේ ළඟ sleep  මූට මොනව වෙලාද මන්ද

### 3.341. `නිදාගෙන` -> `sleeping`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER කොහොමද උඹ කට ඇරන් නිදාගෙන ඉද්දි බිජ්ජ හැලුනොත්?
  - [OFF] after:  @USER කොහොමද උඹ කට ඇරන් sleeping ඉද්දි බිජ්ජ හැලුනොත්?
  - [OFF] before: @USER කොහොමද උඹ කට ඇරන් නිදාගෙන ඉද්දි බිජ්ජ හැලුනොත්?
  - [OFF] after:  @USER කොහොමද උඹ කට ඇරන් sleeping ඉද්දි බිජ්ජ හැලුනොත්?

### 3.342. `තිහයි` -> `thirty`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කෙසෙල් ගෙඩියක් රුපියල් තිහයි
  - [NOT] after:  @USER කෙසෙල් ගෙඩියක් රුපියල් thirty
  - [NOT] before: @USER කෙසෙල් ගෙඩියක් රුපියල් තිහයි
  - [NOT] after:  @USER කෙසෙල් ගෙඩියක් rupees thirty

### 3.343. `කිරිබත්ගොඩ` -> `Kiribathgoda`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER නෑ නෑ කොළොන්නාව නෙවෙයි.. කිරිබත්ගොඩ
  - [NOT] after:  @USER නෑ නෑ කොළොන්නාව නෙවෙයි.. Kiribathgoda
  - [NOT] before: @USER නෑ නෑ කොළොන්නාව නෙවෙයි.. කිරිබත්ගොඩ
  - [NOT] after:  @USER නෑ නෑ Kolonnawa නෙවෙයි.. Kiribathgoda

### 3.344. `ලේසියෙන්` -> `easily`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ජාකෝලිස් හදපු නැකතක් කොහෙද ලේසියෙන් වරදින්නෙ   දැන් චුට්ටකට කලින් ඒ කෑල්ල බැලුවේ
  - [NOT] after:  @USER ජාකෝලිස් හදපු නැකතක් කොහෙද easily වරදින්නෙ   දැන් චුට්ටකට කලින් ඒ කෑල්ල බැලුවේ
  - [NOT] before: @USER ජාකෝලිස් හදපු නැකතක් කොහෙද ලේසියෙන් වරදින්නෙ   දැන් චුට්ටකට කලින් ඒ කෑල්ල බැලුවේ
  - [NOT] after:  @USER ජාකෝලිස් හදපු නැකතක් කොහෙද easily වරදින්නෙ   දැන් චුට්ටකට කලින් ඒ girl බැලුවේ

### 3.345. `මාලු` -> `fish`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ,  @USER  @USER නිකන් පල මාලු වේසි යන්න. මංගලගෙ ඇටේ උරල එනව දැන් අපිට පුක දෙන්න
  - [OFF] after:  @USER ,  @USER  @USER නිකන් පල fish වේසි යන්න. මංගලගෙ ඇටේ උරල එනව දැන් අපිට පුක දෙන්න
  - [OFF] before: @USER ,  @USER  @USER නිකන් පල මාලු වේසි යන්න. මංගලගෙ ඇටේ උරල එනව දැන් අපිට පුක දෙන්න
  - [OFF] after:  @USER ,  @USER  @USER නිකන් පල fish වේසි යන්න. මංගලගෙ ඇටේ උරල එනව දැන් අපිට පුක දෙන්න

### 3.346. `පුද්ගලයින්` -> `people`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මනුස්සයන්ගේ අසරණ කමින් ප්‍රයොජන ගන්න සක්කිලි නිසා....    දකුණු අප්‍රිකාවේ පුද්ගලයින් 59කු “#ඩෙටෝල්” නම් විශබීජ නාශක දියරය පානය කිරීම හේතුවෙන් මියගොස් තිබෙනවා. එරට #පූජකයකු විසින් සිය දේව මෙහෙය අතර තුර #covid19 බේරිමට  සිය අනුගාමිකයින්ට මෙම දියරය පානය සඳහා ලබා දී ඇත.
  - [NOT] after:  මනුස්සයන්ගේ අසරණ කමින් ප්‍රයොජන ගන්න සක්කිලි නිසා....    දකුණු අප්‍රිකාවේ people 59කු “#ඩෙටෝල්” නම් විශබීජ නාශක දියරය පානය කිරීම හේතුවෙන් මියගොස් තිබෙනවා. එරට #පූජකයකු විසින් සිය දේව මෙහෙය අතර තුර #covid19 බේරිමට  සිය අනුගාමිකයින්ට මෙම දියරය පානය සඳහා ලබා දී ඇත.
  - [NOT] before: මනුස්සයන්ගේ අසරණ කමින් ප්‍රයොජන ගන්න සක්කිලි නිසා....    දකුණු අප්‍රිකාවේ පුද්ගලයින් 59කු “#ඩෙටෝල්” නම් විශබීජ නාශක දියරය පානය කිරීම හේතුවෙන් මියගොස් තිබෙනවා. එරට #පූජකයකු විසින් සිය දේව මෙහෙය අතර තුර #covid19 බේරිමට  සිය අනුගාමිකයින්ට මෙම දියරය පානය සඳහා ලබා දී ඇත.
  - [NOT] after:  මනුස්සයන්ගේ helpless කමින් ප්‍රයොජන ගන්න සක්කිලි නිසා....    දකුණු අප්‍රිකාවේ people 59කු “#ඩෙටෝල්” නම් විශබීජ නාශක දියරය පානය කිරීම හේතුවෙන් මියගොස් තිබෙනවා. එරට #පූජකයකු විසින් සිය දේව මෙහෙය අතර තුර #covid19 බේරිමට  සිය අනුගාමිකයින්ට මෙම දියරය පානය සඳහා ලබා දී ඇත.

### 3.347. `වහිනවා` -> `raining`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: යන්න හදද්දි ඇද රෙද්ද මිරිකා ගන්නවා වගේ එව්වා තමා අපි නම් අහලා තියෙන්නේ LuckyGirlමලී @USER  · 24 Oct 2019 යන්න හදද්දි වහිනවා..
  - [NOT] after:  යන්න හදද්දි ඇද රෙද්ද මිරිකා ගන්නවා වගේ එව්වා තමා අපි නම් අහලා තියෙන්නේ LuckyGirlමලී @USER  · 24 Oct 2019 යන්න හදද්දි raining..
  - [NOT] before: යන්න හදද්දි ඇද රෙද්ද මිරිකා ගන්නවා වගේ එව්වා තමා අපි නම් අහලා තියෙන්නේ LuckyGirlමලී @USER  · 24 Oct 2019 යන්න හදද්දි වහිනවා..
  - [NOT] after:  යන්න හදද්දි bed රෙද්ද මිරිකා ගන්නවා වගේ එව්වා තමා අපි නම් අහලා තියෙන්නේ LuckyGirlමලී @USER  · 24 Oct 2019 යන්න හදද්දි raining..

### 3.348. `දිගයි` -> `long`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER කොට උනාට පයිය දිගයි නේ. #Teamදිගපයිය
  - [OFF] after:  @USER  @USER කොට උනාට පයිය long නේ. #Teamදිගපයිය
  - [OFF] before: @USER  @USER කොට උනාට පයිය දිගයි නේ. #Teamදිගපයිය
  - [OFF] after:  @USER  @USER කොට උනාට පයිය long නේ. #Teamදිගපයිය

### 3.349. `ටූ` -> `too`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තෝ ටූ හරකා
  - [OFF] after:  @USER  @USER තෝ too හරකා
  - [OFF] before: @USER  @USER තෝ ටූ හරකා
  - [OFF] after:  @USER  @USER තෝ too හරකා

### 3.350. `නැටුවා` -> `danced`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: Enrique වගේද සනී ලියෝන් , කියපු වෙලාවට ආවා..රෙද්ද ගැලෙව්වා..පොඩ්ඩක් නැටුවා... ගියා...   #EnriqueInSL
  - [NOT] after:  Enrique වගේද සනී ලියෝන් , කියපු වෙලාවට ආවා..රෙද්ද ගැලෙව්වා..පොඩ්ඩක් danced... ගියා...   #EnriqueInSL
  - [NOT] before: Enrique වගේද සනී ලියෝන් , කියපු වෙලාවට ආවා..රෙද්ද ගැලෙව්වා..පොඩ්ඩක් නැටුවා... ගියා...   #EnriqueInSL
  - [NOT] after:  Enrique වගේද සනී ලියෝන් , කියපු වෙලාවට ආවා..රෙද්ද ගැලෙව්වා..පොඩ්ඩක් danced... ගියා...   #EnriqueInSL

### 3.351. `දිනුවා` -> `won`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හුකනවා හුත්තෝ අපි දිනුවා   පකෝ මට බැ හුත්තො .......
  - [OFF] after:  හුකනවා හුත්තෝ අපි won   පකෝ මට බැ හුත්තො .......
  - [OFF] before: හුකනවා හුත්තෝ අපි දිනුවා   පකෝ මට බැ හුත්තො .......
  - [OFF] after:  හුකනවා හුත්තෝ අපි won   පකෝ මට බැ හුත්තො .......

### 3.352. `ගහ` -> `tree`
- impact: 2 posts (0 light, 2 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ආහ් ආවද පොන්න පකයා. අල්ලා??? තොගෙ පයිය අල්ලලා වට කරලා ඇදලා ගහ ගනින් තොගෙ පුකේ.. වනචර බල්ලා
  - [OFF] after:  @USER ආහ් ආවද පොන්න පකයා. අල්ලා??? තොගෙ පයිය අල්ලලා round කරලා ඇදලා tree ගනින් තොගෙ පුකේ.. වනචර බල්ලා
  - [OFF] before: @USER  @USER උබ හිතන් ඉන්නෙ උන හැදුනු ගමන් අමා මැරෙනවා කියලාද පලයන් ගොන් ගහ යන්න.කට කැඩිච්ච කතා කියන්නෙ
  - [OFF] after:  @USER  @USER උබ හිතන් ඉන්නෙ උන හැදුනු ගමන් අමා මැරෙනවා කියලාද පලයන් ගොන් tree යන්න.කට කැඩිච්ච talk කියන්නෙ

### 3.353. `ලැබුනු` -> `received`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මා හට ලැබුනු කිව්වෙ, කා හට ලැබුනු ද
  - [NOT] after:  @USER මා හට received කිව්වෙ, කා හට received ද
  - [NOT] before: @USER මා හට ලැබුනු කිව්වෙ, කා හට ලැබුනු ද
  - [NOT] after:  @USER මා to received කිව්වෙ, කා to received ද

### 3.354. `අයහපත්` -> `bad`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER " @USER : අයහපත් කාලගුණයෙන් මිය ගිය ගණන 8 ක් දක්වා ඉහළට #lka #WeatherSL URL
  - [NOT] after:  @USER " @USER : bad කාලගුණයෙන් මිය ගිය ගණන 8 ක් දක්වා ඉහළට #lka #WeatherSL URL
  - [NOT] before: @USER " @USER : අයහපත් කාලගුණයෙන් මිය ගිය ගණන 8 ක් දක්වා ඉහළට #lka #WeatherSL URL
  - [NOT] after:  @USER " @USER : bad weather මිය ගිය ගණන 8 ක් දක්වා ඉහළට #lka #WeatherSL URL

### 3.355. `සබන්` -> `soap`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: සබන් බොල..  :04 ,422 views
  - [NOT] after:  soap බොල..  :04 ,422 views
  - [NOT] before: සබන් බොල..  :04 ,422 views
  - [NOT] after:  soap බොල..  :04 ,422 views

### 3.356. `කව්රු` -> `who`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: “අම්මට... ඈ යකෝ තෝ හිතාගෙන ඉන්නේ මාත් තෝ වගේ පොන්නයෙක් කියලද? තෝ කියන කොට දිව්රුම් දෙන්නයි, තෝ කියන කොට ඉල්ලා අස්වෙන්නයි මං කව්රු කියලද හිතාගෙන ඉන්නේ?”
  - [OFF] after:  “අම්මට... ඈ යකෝ තෝ හිතාගෙන ඉන්නේ මාත් තෝ වගේ පොන්නයෙක් කියලද? තෝ කියන කොට දිව්රුම් දෙන්නයි, තෝ කියන කොට ඉල්ලා අස්වෙන්නයි මං who කියලද හිතාගෙන ඉන්නේ?”
  - [OFF] before: “අම්මට... ඈ යකෝ තෝ හිතාගෙන ඉන්නේ මාත් තෝ වගේ පොන්නයෙක් කියලද? තෝ කියන කොට දිව්රුම් දෙන්නයි, තෝ කියන කොට ඉල්ලා අස්වෙන්නයි මං කව්රු කියලද හිතාගෙන ඉන්නේ?”
  - [OFF] after:  “අම්මට... ඈ යකෝ තෝ හිතාගෙන ඉන්නේ මාත් තෝ වගේ පොන්නයෙක් කියලද? තෝ කියන කොට දිව්රුම් දෙන්නයි, තෝ කියන කොට ඉල්ලා අස්වෙන්නයි මං who කියලද හිතාගෙන ඉන්නේ?”

### 3.357. `හ්ම්ම්` -> `hmm`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: හ්ම්ම් ඒක තමා. දැනෙන එකක් නෑ. ඒත් ඇයි එහෙම කරන්නේ අපි. අපේ මෝඩ කම @USER
  - [NOT] after:  hmm ඒක තමා. දැනෙන එකක් නෑ. ඒත් ඇයි එහෙම කරන්නේ අපි. අපේ මෝඩ කම @USER
  - [NOT] before: හ්ම්ම් ඒක තමා. දැනෙන එකක් නෑ. ඒත් ඇයි එහෙම කරන්නේ අපි. අපේ මෝඩ කම @USER
  - [NOT] after:  hmm ඒක තමා. දැනෙන එකක් නෑ. ඒත් ඇයි එහෙම කරන්නේ අපි. අපේ මෝඩ කම @USER

### 3.358. `නැතිවුනානේ` -> `lost`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  උබේ රෙද්ද නැතිවුනානේ අද
  - [NOT] after:  @USER @USER  උබේ රෙද්ද lost අද
  - [NOT] before: @USER @USER  උබේ රෙද්ද නැතිවුනානේ අද
  - [NOT] after:  @USER @USER  උබේ රෙද්ද lost අද

### 3.359. `මිනිහො` -> `man`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER කුම්බ කිම්බ පටලගන්න එපා මිනිහො..
  - [OFF] after:  @USER  @USER කුම්බ කිම්බ පටලගන්න එපා man..
  - [OFF] before: @USER  @USER කුම්බ කිම්බ පටලගන්න එපා මිනිහො..
  - [OFF] after:  @USER  @USER කුම්බ කිම්බ පටලගන්න එපා man..

### 3.360. `කවුරුහරි` -> `someone`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: JVP  කියන්නේ මොළ කාරයෝ කියලා කවුරුහරි කිව්වොත් මෙන්න මේක පෙන්නපන් ගොන් හැත්ත.... URL
  - [OFF] after:  JVP  කියන්නේ මොළ කාරයෝ කියලා someone කිව්වොත් මෙන්න මේක පෙන්නපන් ගොන් හැත්ත.... URL
  - [OFF] before: JVP  කියන්නේ මොළ කාරයෝ කියලා කවුරුහරි කිව්වොත් මෙන්න මේක පෙන්නපන් ගොන් හැත්ත.... URL
  - [OFF] after:  JVP  කියන්නේ brain කාරයෝ කියලා someone කිව්වොත් මෙන්න මේක පෙන්නපන් ගොන් හැත්ත.... URL

### 3.361. `තුවාල` -> `wounds`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අද නම් ටික්ක අමාරු දවසක්,  තුවාල දෙකයි..
  - [NOT] after:  අද නම් ටික්ක අමාරු දවසක්,  wounds දෙකයි..
  - [NOT] before: අද නම් ටික්ක අමාරු දවසක්,  තුවාල දෙකයි..
  - [NOT] after:  අද නම් ටික්ක අමාරු දවසක්,  wounds two..

### 3.362. `යටට` -> `under`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පොන්න පකෙක්.  අපී මෙහේ සීතලට අදින ඇදුම් .ගිනි ගහන රස්නේ මේ මීහරකා යටට ඇදලා බිජ්ජ halfboill වෙලා ඇතී
  - [OFF] after:  @USER පොන්න පකෙක්.  අපී මෙහේ සීතලට අදින ඇදුම් .ගිනි ගහන රස්නේ මේ මීහරකා under ඇදලා බිජ්ජ halfboill වෙලා ඇතී
  - [OFF] before: @USER පොන්න පකෙක්.  අපී මෙහේ සීතලට අදින ඇදුම් .ගිනි ගහන රස්නේ මේ මීහරකා යටට ඇදලා බිජ්ජ halfboill වෙලා ඇතී
  - [OFF] after:  @USER පොන්න පකෙක්.  we මෙහේ සීතලට අදින ඇදුම් .ගිනි ගහන රස්නේ මේ මීහරකා under ඇදලා බිජ්ජ halfboill වෙලා ඇතී

### 3.363. `මනමාලයා` -> `groom`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER ඕකා මනමාලයා...නාකි ඉලන්දාරියා...
  - [OFF] after:  @USER  @USER ඕකා groom...නාකි ඉලන්දාරියා...
  - [OFF] before: @USER  @USER ඕකා මනමාලයා...නාකි ඉලන්දාරියා...
  - [OFF] after:  @USER  @USER ඕකා groom...නාකි ඉලන්දාරියා...

### 3.364. `කීව` -> `said`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අඩේ උන් කොහෙද යනව කීව නේද
  - [NOT] after:  @USER අඩේ උන් කොහෙද යනව said නේද
  - [NOT] before: @USER අඩේ උන් කොහෙද යනව කීව නේද
  - [NOT] after:  @USER අඩේ උන් කොහෙද යනව said නේද

### 3.365. `දරුවො` -> `kids`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පොඩි දරුවො ගොරවනවට බයයි ඔච්චර ලොකු වෙලත් උඹ ඒක දන්නැද්ද.!
  - [NOT] after:  පොඩි kids ගොරවනවට බයයි ඔච්චර ලොකු වෙලත් උඹ ඒක දන්නැද්ද.!
  - [NOT] before: පොඩි දරුවො ගොරවනවට බයයි ඔච්චර ලොකු වෙලත් උඹ ඒක දන්නැද්ද.!
  - [NOT] after:  පොඩි kids ගොරවනවට scared ඔච්චර ලොකු වෙලත් උඹ ඒක දන්නැද්ද.!

### 3.366. `ආච්චී` -> `grandma`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ආපෝ පයිය නැලූ  හම්මේ ආච්චී... ඔයා නම්ම්..:
  - [OFF] after:  ආපෝ පයිය නැලූ  හම්මේ grandma... ඔයා නම්ම්..:
  - [OFF] before: ආපෝ පයිය නැලූ  හම්මේ ආච්චී... ඔයා නම්ම්..:
  - [OFF] after:  ආපෝ පයිය නැලූ  හම්මේ grandma... ඔයා නම්ම්..:

### 3.367. `නන්ගි` -> `sister`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  දැන්වත් හොඳට හිනාවෙලා ඉන්න අපේ මෝඩ නන්ගි
  - [NOT] after:  @USER @USER  දැන්වත් හොඳට හිනාවෙලා ඉන්න අපේ මෝඩ sister
  - [NOT] before: @USER @USER  දැන්වත් හොඳට හිනාවෙලා ඉන්න අපේ මෝඩ නන්ගි
  - [NOT] after:  @USER @USER  දැන්වත් හොඳට smiling ඉන්න අපේ මෝඩ sister

### 3.368. `ආරක්ෂා` -> `protect`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER එකනේ මොනා කරන්නද අමාරැ උනත් පොඩි උන් ආරක්ෂා කරගන්න ඔනනේ..මුං අපේ නිදහසත් නැති කරානේ කාලකණ්ණි
  - [OFF] after:  @USER එකනේ මොනා කරන්නද අමාරැ උනත් පොඩි උන් protect කරගන්න ඔනනේ..මුං අපේ නිදහසත් නැති කරානේ කාලකණ්ණි
  - [OFF] before: @USER එකනේ මොනා කරන්නද අමාරැ උනත් පොඩි උන් ආරක්ෂා කරගන්න ඔනනේ..මුං අපේ නිදහසත් නැති කරානේ කාලකණ්ණි
  - [OFF] after:  @USER එකනේ මොනා කරන්නද hard උනත් පොඩි උන් protect කරගන්න ඔනනේ..මුං අපේ නිදහසත් නැති කරානේ කාලකණ්ණි

### 3.369. `රස්නේ` -> `heat`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ඉවසන්න බෑ බොලව් මේ කරුම රස්නේ. !
  - [NOT] after:  ඉවසන්න බෑ බොලව් මේ කරුම heat. !
  - [NOT] before: ඉවසන්න බෑ බොලව් මේ කරුම රස්නේ. !
  - [NOT] after:  ඉවසන්න බෑ බොලව් මේ කරුම heat. !

### 3.370. `හොය` -> `search`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER හැමදාම තමුන්ගෙම රෙද්දස්ස හොය හොය උන්නොත් පයිය දෙකට නවල පුකේ ගහගන්නයි වෙන්නෙ..
  - [OFF] after:  @USER  @USER හැමදාම තමුන්ගෙම රෙද්දස්ස search search උන්නොත් පයිය දෙකට නවල පුකේ ගහගන්නයි වෙන්නෙ..
  - [OFF] before: @USER  @USER හැමදාම තමුන්ගෙම රෙද්දස්ස හොය හොය උන්නොත් පයිය දෙකට නවල පුකේ ගහගන්නයි වෙන්නෙ..
  - [OFF] after:  @USER  @USER හැමදාම තමුන්ගෙම රෙද්දස්ස search search උන්නොත් පයිය දෙකට නවල පුකේ ගහගන්නයි වෙන්නෙ..

### 3.371. `සූදු` -> `gambling`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මං සූදු කෙලියේ නෑ බලං හිටියා විතරයි
  - [NOT] after:  @USER මං gambling කෙලියේ නෑ බලං හිටියා විතරයි
  - [NOT] before: @USER මං සූදු කෙලියේ නෑ බලං හිටියා විතරයි
  - [NOT] after:  @USER මං gambling කෙලියේ නෑ බලං හිටියා විතරයි

### 3.372. `මේස` -> `table`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මේස රෙද්ද මෙහෙම ගන්න පුළුවන්ද? URL
  - [NOT] after:  table රෙද්ද මෙහෙම ගන්න පුළුවන්ද? URL
  - [NOT] before: මේස රෙද්ද මෙහෙම ගන්න පුළුවන්ද? URL
  - [NOT] after:  table රෙද්ද මෙහෙම ගන්න පුළුවන්ද? URL

### 3.373. `කැතයි` -> `ugly`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මම  කැතයි තමා..කැත උනත් ඉතින් මේ මමනෙ අයිසෙ
  - [NOT] after:  මම  ugly තමා..කැත උනත් ඉතින් මේ මමනෙ අයිසෙ
  - [NOT] before: මම  කැතයි තමා..කැත උනත් ඉතින් මේ මමනෙ අයිසෙ
  - [NOT] after:  මම  ugly තමා..කැත උනත් ඉතින් මේ මමනෙ අයිසෙ

### 3.374. `දෙයියො` -> `god`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අයිසෙ දෙයියො කෝප වෙයි
  - [NOT] after:  @USER අයිසෙ god කෝප වෙයි
  - [NOT] before: @USER අයිසෙ දෙයියො කෝප වෙයි
  - [NOT] after:  @USER අයිසෙ god කෝප වෙයි

### 3.375. `උපැස්` -> `spectacles`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: #පන්නරය යකෝ  Dulith Kasun (DK) @USER  · 4 Jul 2019 සිහින් උසැති උපැස් පළදින්නා....
  - [NOT] after:  #පන්නරය යකෝ  Dulith Kasun (DK) @USER  · 4 Jul 2019 සිහින් උසැති spectacles පළදින්නා....
  - [NOT] before: #පන්නරය යකෝ  Dulith Kasun (DK) @USER  · 4 Jul 2019 සිහින් උසැති උපැස් පළදින්නා....
  - [NOT] after:  #පන්නරය යකෝ  Dulith Kasun (DK) @USER  · 4 Jul 2019 සිහින් tall spectacles පළදින්නා....

### 3.376. `දුවලා` -> `daughters`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මම දැනුයි අර ත්‍රෙඩ් එක කියෙව්වේ, එතන රිලේ එකක් දුවලා වගේ පේන්නෙ නැද්ද, එක්කෙනෙක් ඇදගෙන ඇවිල්ලා තව එක්කෙනෙක්ට බැට්න් එක දෙනවා, එයාට අමාරු වෙද්දි තව එක්කෙනෙක්ට දීලා වගේ පේන්නෙ නැද්ද?
  - [NOT] after:  @USER මම දැනුයි අර ත්‍රෙඩ් එක කියෙව්වේ, එතන රිලේ එකක් daughters වගේ පේන්නෙ නැද්ද, එක්කෙනෙක් ඇදගෙන ඇවිල්ලා තව එක්කෙනෙක්ට බැට්න් එක දෙනවා, එයාට අමාරු වෙද්දි තව එක්කෙනෙක්ට දීලා වගේ පේන්නෙ නැද්ද?
  - [NOT] before: @USER මම දැනුයි අර ත්‍රෙඩ් එක කියෙව්වේ, එතන රිලේ එකක් දුවලා වගේ පේන්නෙ නැද්ද, එක්කෙනෙක් ඇදගෙන ඇවිල්ලා තව එක්කෙනෙක්ට බැට්න් එක දෙනවා, එයාට අමාරු වෙද්දි තව එක්කෙනෙක්ට දීලා වගේ පේන්නෙ නැද්ද?
  - [NOT] after:  @USER මම දැනුයි අර ත්‍රෙඩ් එක කියෙව්වේ, එතන රිලේ එකක් daughters වගේ පේන්නෙ නැද්ද, එක්කෙනෙක් ඇදගෙන ඇවිල්ලා තව එක්කෙනෙක්ට බැට්න් එක දෙනවා, එයාට අමාරු වෙද්දි තව එක්කෙනෙක්ට දීලා වගේ පේන්නෙ නැද්ද?

### 3.377. `ඔප්පු` -> `prove`
- impact: 2 posts (0 light, 2 heavy), 1 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER එහෙනම් ෆොන්සේකට අරක දෙන්න ඔයා කියන දේ ඔප්පු කරලම පෙන්නන්න.
  - [NOT] after:  @USER එහෙනම් ෆොන්සේකට අරක දෙන්න ඔයා කියන දේ prove කරලම show.
  - [OFF] before: උපයාගත්ත ආකාරය ඔප්පු කිරීමට නොහැකි බව කියන කාරනාව වෙනන ඕනෙ  මෝඩ යකා තුරුම්පුව කරගත්තෙ.
  - [OFF] after:  උපයාගත්ත ආකාරය prove කිරීමට නොහැකි බව කියන කාරනාව වෙනන ඕනෙ  මෝඩ devil තුරුම්පුව කරගත්තෙ.

### 3.378. `ඇතුළු` -> `including`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ජහමනයා පාරේ හිගාකෑවත්   අපේ ගොනා අපිට හොඳා   තියරිය අනුව යමින්   සාමූහික අහවල් එක   වෙනුවෙන් පෙනීසිටි   අතන මෙතන ගන රතන   තුනෙන් දෙකේ නානලා   කුඩ ඉල්ලපු අම්මණ්ඩිලා   ඇතුළු   දේශප්‍රේමී 152 ට   ජයෙන් ජය වේවා...!!!!
  - [NOT] after:  ජහමනයා පාරේ හිගාකෑවත්   අපේ ගොනා අපිට හොඳා   තියරිය අනුව යමින්   සාමූහික අහවල් එක   වෙනුවෙන් පෙනීසිටි   අතන මෙතන ගන රතන   තුනෙන් දෙකේ නානලා   කුඩ ඉල්ලපු අම්මණ්ඩිලා   including   දේශප්‍රේමී 152 ට   ජයෙන් ජය වේවා...!!!!
  - [NOT] before: ජහමනයා පාරේ හිගාකෑවත්   අපේ ගොනා අපිට හොඳා   තියරිය අනුව යමින්   සාමූහික අහවල් එක   වෙනුවෙන් පෙනීසිටි   අතන මෙතන ගන රතන   තුනෙන් දෙකේ නානලා   කුඩ ඉල්ලපු අම්මණ්ඩිලා   ඇතුළු   දේශප්‍රේමී 152 ට   ජයෙන් ජය වේවා...!!!!
  - [NOT] after:  ජහමනයා road එකේ හිගාකෑවත්   අපේ ගොනා අපිට හොඳා   තියරිය අනුව යමින්   සාමූහික අහවල් එක   වෙනුවෙන් පෙනීසිටි   අතන මෙතන ගන රතන   තුනෙන් දෙකේ නානලා   කුඩ ඉල්ලපු අම්මණ්ඩිලා   including   දේශප්‍රේමී 152 ට   ජයෙන් ජය වේවා...!!!!

### 3.379. `දැන්නම්` -> `now`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මෙන්න මූව වත් ගෙන්නල මොකක් හරි කරපල්ලකො... දැන්නම් ඇතිවෙලා රෙද්ද.  #Rain #SLvWI
  - [OFF] after:  මෙන්න මූව වත් ගෙන්නල මොකක් හරි කරපල්ලකො... now ඇතිවෙලා රෙද්ද.  #Rain #SLvWI
  - [OFF] before: මෙන්න මූව වත් ගෙන්නල මොකක් හරි කරපල්ලකො... දැන්නම් ඇතිවෙලා රෙද්ද.  #Rain #SLvWI
  - [OFF] after:  මෙන්න මූව වත් ගෙන්නල මොකක් හරි කරපල්ලකො... now ඇතිවෙලා රෙද්ද.  #Rain #SLvWI

### 3.380. `වික්කා` -> `sold`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER වෙස්සන්තර නෙවෙයි. ඒ ගොනා වික්කා.
  - [NOT] after:  @USER  @USER වෙස්සන්තර නෙවෙයි. ඒ ගොනා sold.
  - [NOT] before: @USER  @USER වෙස්සන්තර නෙවෙයි. ඒ ගොනා වික්කා.
  - [NOT] after:  @USER  @USER වෙස්සන්තර නෙවෙයි. ඒ ගොනා sold.

### 3.381. `හෙනකෲරයි` -> `cruel`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තමුසෙ හෙනකෲරයි අමිල
  - [OFF] after:  @USER  @USER තමුසෙ cruel අමිල
  - [OFF] before: @USER  @USER තමුසෙ හෙනකෲරයි අමිල
  - [OFF] after:  @USER  @USER තමුසෙ cruel අමිල

### 3.382. `හිනාවෙලා` -> `smiling`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  දැන්වත් හොඳට හිනාවෙලා ඉන්න අපේ මෝඩ නන්ගි
  - [NOT] after:  @USER @USER  දැන්වත් හොඳට smiling ඉන්න අපේ මෝඩ sister
  - [NOT] before: ඇත්ත ඒකි මගේ  පොඩි එකී හැම දුකම කඳුළම එක්ක  මගේ ළඟ හිනාවෙලා හුරතලෙන් ඉන්න මගේ පැංචී උඹ හරි හයියක් මට ඇත්තමයි උඹ මගෙම පොඩ්ඩි  @USER
  - [NOT] after:  ඇත්ත ඒකි මගේ  පොඩි එකී හැම දුකම කඳුළම එක්ක  මගේ near smiling හුරතලෙන් ඉන්න මගේ පැංචී උඹ හරි හයියක් මට ඇත්තමයි උඹ මගෙම පොඩ්ඩි  @USER

### 3.383. `නිවට` -> `coward`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අගමැතියා ඇමෙරිකා ගියා ලෙඩ්ඩු බිම බුදියනවා කියාගෙන කට අරින තොපි වාගෙ නිවට නියාලු බූරූ මොංගලයොම තමා මහ ඉස්පිරිතාලේ... URL
  - [OFF] after:  අගමැතියා ඇමෙරිකා ගියා ලෙඩ්ඩු බිම බුදියනවා කියාගෙන කට අරින තොපි වාගෙ coward නියාලු බූරූ මොංගලයොම තමා මහ ඉස්පිරිතාලේ... URL
  - [OFF] before: අගමැතියා ඇමෙරිකා ගියා ලෙඩ්ඩු බිම බුදියනවා කියාගෙන කට අරින තොපි වාගෙ නිවට නියාලු බූරූ මොංගලයොම තමා මහ ඉස්පිරිතාලේ... URL
  - [OFF] after:  අගමැතියා ඇමෙරිකා ගියා ලෙඩ්ඩු බිම බුදියනවා කියාගෙන කට අරින තොපි like coward නියාලු බූරූ මොංගලයොම තමා මහ ඉස්පිරිතාලේ... URL

### 3.384. `දෙරන` -> `Derana`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අද දෙරන මම අයින් කරනවා ,
  - [NOT] after:  @USER අද Derana මම අයින් කරනවා ,
  - [NOT] before: @USER අද දෙරන මම අයින් කරනවා ,
  - [NOT] after:  @USER අද Derana මම අයින් කරනවා ,

### 3.385. `මොකො` -> `why`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ආ.. බල්ලො මොකො බැල්ලි මොකෝ
  - [NOT] after:  @USER ආ.. බල්ලො why බැල්ලි මොකෝ
  - [NOT] before: @USER ආ.. බල්ලො මොකො බැල්ලි මොකෝ
  - [NOT] after:  @USER ආ.. බල්ලො why බැල්ලි මොකෝ

### 3.386. `වාසනාවන්` -> `lucky`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER වොක්ස්වැගන් එකටත් කිට්ටු නිසා නැගල යයි... අනේ වාසනාවන්...
  - [NOT] after:  @USER වොක්ස්වැගන් එකටත් කිට්ටු නිසා නැගල යයි... අනේ lucky...
  - [NOT] before: @USER වොක්ස්වැගන් එකටත් කිට්ටු නිසා නැගල යයි... අනේ වාසනාවන්...
  - [NOT] after:  @USER වොක්ස්වැගන් එකටත් close නිසා නැගල යයි... අනේ lucky...

### 3.387. `සමනළ` -> `butterfly`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER    මොකක්ද යකෝ මේ සමනළ මාවතක් ගැන කියල තියෙන්නේ? තෝ හිතුවද මමත් හසිය වගේ කියල
  - [OFF] after:  @USER  @USER    මොකක්ද යකෝ මේ butterfly මාවතක් ගැන කියල තියෙන්නේ? තෝ හිතුවද මමත් හසිය වගේ කියල
  - [OFF] before: @USER  @USER    මොකක්ද යකෝ මේ සමනළ මාවතක් ගැන කියල තියෙන්නේ? තෝ හිතුවද මමත් හසිය වගේ කියල
  - [OFF] after:  @USER  @USER    මොකක්ද යකෝ මේ butterfly මාවතක් ගැන කියල තියෙන්නේ? තෝ හිතුවද මමත් හසිය වගේ කියල

### 3.388. `අන්තිමනෙ` -> `last`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අපි ඉතින් හැම දෙකින්ම අන්තිමනෙ...
  - [NOT] after:  @USER අපි ඉතින් හැම දෙකින්ම last...
  - [NOT] before: @USER අපි ඉතින් හැම දෙකින්ම අන්තිමනෙ...
  - [NOT] after:  @USER අපි ඉතින් හැම දෙකින්ම last...

### 3.389. `සුනඛයන්` -> `dogs`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සිරිසේනගේ අවජාතක සුනඛයන් ජාතිය ඇමතිම..... URL
  - [OFF] after:  සිරිසේනගේ අවජාතක dogs ජාතිය ඇමතිම..... URL
  - [OFF] before: සිරිසේනගේ අවජාතක සුනඛයන් ජාතිය ඇමතිම..... URL
  - [OFF] after:  Sirisena's අවජාතක dogs ජාතිය ඇමතිම..... URL

### 3.390. `වෙනත්` -> `other`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අපේ බලශක්ති සුරක්ෂිතතාවය වෙනත් රටකට බාර දෙන්නේ අැයි?ඒය අප විසින්ම සුරක්ෂිත කළ යුතු නොවන්නේද?
  - [NOT] after:  @USER අපේ බලශක්ති සුරක්ෂිතතාවය other රටකට බාර දෙන්නේ අැයි?ඒය අප විසින්ම සුරක්ෂිත කළ යුතු නොවන්නේද?
  - [NOT] before: @USER අපේ බලශක්ති සුරක්ෂිතතාවය වෙනත් රටකට බාර දෙන්නේ අැයි?ඒය අප විසින්ම සුරක්ෂිත කළ යුතු නොවන්නේද?
  - [NOT] after:  @USER අපේ බලශක්ති සුරක්ෂිතතාවය other රටකට බාර දෙන්නේ why?ඒය අප විසින්ම සුරක්ෂිත කළ යුතු නොවන්නේද?

### 3.391. `ලඟදීම` -> `soon`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අනන්තයෙන් ආ  ගොන් හරකා  ලඟදීම
  - [OFF] after:  අනන්තයෙන් ආ  ගොන් හරකා  soon
  - [OFF] before: අනන්තයෙන් ආ  ගොන් හරකා  ලඟදීම
  - [OFF] after:  අනන්තයෙන් ආ  ගොන් හරකා  soon

### 3.392. `මයියොක්කා` -> `manioc`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER    මයියොක්කා වගෙමනෙ බලනවකො අයිසෙ
  - [NOT] after:  @USER  @USER    manioc වගෙමනෙ බලනවකො අයිසෙ
  - [NOT] before: @USER  @USER    මයියොක්කා වගෙමනෙ බලනවකො අයිසෙ
  - [NOT] after:  @USER  @USER    manioc වගෙමනෙ බලනවකො අයිසෙ

### 3.393. `වහාම` -> `immediately`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඥාණසාර හිටියනම්: "අපි මේ කැප කිරීම් කරලා මේ පන්සල් හැදුවේ තොපි වගේ හුත්තිගේ පුතාලට දුවන්න ද, වහාම පන්සලෙන් එලියට පල පර බල්ලා"
  - [OFF] after:  @USER ඥාණසාර හිටියනම්: "අපි මේ කැප කිරීම් කරලා මේ පන්සල් හැදුවේ තොපි වගේ හුත්තිගේ පුතාලට දුවන්න ද, immediately පන්සලෙන් එලියට පල පර බල්ලා"
  - [OFF] before: @USER ඥාණසාර හිටියනම්: "අපි මේ කැප කිරීම් කරලා මේ පන්සල් හැදුවේ තොපි වගේ හුත්තිගේ පුතාලට දුවන්න ද, වහාම පන්සලෙන් එලියට පල පර බල්ලා"
  - [OFF] after:  @USER ඥාණසාර හිටියනම්: "අපි මේ කැප කිරීම් කරලා මේ පන්සල් made තොපි වගේ හුත්තිගේ පුතාලට දුවන්න ද, immediately පන්සලෙන් එලියට පල පර බල්ලා"

### 3.394. `කඩ` -> `shop`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කඩ වල ලුණු දෙන්නේ නෑ.... Online බැලුවොත් limit එකක් එක්ක දෙන්නේ...
  - [NOT] after:  @USER shop වල ලුණු දෙන්නේ නෑ.... Online බැලුවොත් limit එකක් එක්ක දෙන්නේ...
  - [NOT] before: @USER කඩ වල ලුණු දෙන්නේ නෑ.... Online බැලුවොත් limit එකක් එක්ක දෙන්නේ...
  - [NOT] after:  @USER shop වල ලුණු දෙන්නේ නෑ.... Online බැලුවොත් limit එකක් එක්ක දෙන්නේ...

### 3.395. `දෙමලද` -> `Tamil`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER උඹෙ අප්පත් දෙමලද කියල හොයලා බලපන් පකෝ
  - [OFF] after:  @USER උඹෙ අප්පත් Tamil කියල හොයලා බලපන් පකෝ
  - [OFF] before: @USER උඹෙ අප්පත් දෙමලද කියල හොයලා බලපන් පකෝ
  - [OFF] after:  @USER උඹෙ අප්පත් Tamil කියල හොයලා බලපන් පකෝ

### 3.396. `මිටි` -> `short`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මිටි තැන් දැක පුප්පන්නේ උස් තැන් දැක හැකිලෙන්නේ.. #SLPolice
  - [OFF] after:  @USER short තැන් දැක පුප්පන්නේ උස් තැන් දැක හැකිලෙන්නේ.. #SLPolice
  - [OFF] before: @USER මිටි තැන් දැක පුප්පන්නේ උස් තැන් දැක හැකිලෙන්නේ.. #SLPolice
  - [OFF] after:  @USER short තැන් දැක පුප්පන්නේ loud තැන් දැක හැකිලෙන්නේ.. #SLPolice

### 3.397. `වදන්` -> `words`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මොනව නැතත් වදන් නං තියනව
  - [NOT] after:  @USER මොනව නැතත් words නං තියනව
  - [NOT] before: @USER මොනව නැතත් වදන් නං තියනව
  - [NOT] after:  @USER මොනව නැතත් words නං තියනව

### 3.398. `සිනාසුණා` -> `smiled`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ගොනා  RaNiYa @USER  · 7 Jun 2021 උපුල් නුවන් විදහා Ex සිනාසුණා මම ගොනාවුනා
  - [NOT] after:  ගොනා  RaNiYa @USER  · 7 Jun 2021 උපුල් නුවන් විදහා Ex smiled මම ගොනාවුනා
  - [NOT] before: ගොනා  RaNiYa @USER  · 7 Jun 2021 උපුල් නුවන් විදහා Ex සිනාසුණා මම ගොනාවුනා
  - [NOT] after:  ගොනා  RaNiYa @USER  · 7 Jun 2021 උපුල් eyes විදහා Ex smiled මම ගොනාවුනා

### 3.399. `උසයි` -> `tall`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: නාකි විසේ ගෙටත් වඩා උසයි කියනවනේ
  - [OFF] after:  නාකි විසේ ගෙටත් වඩා tall කියනවනේ
  - [OFF] before: නාකි විසේ ගෙටත් වඩා උසයි කියනවනේ
  - [OFF] after:  නාකි විසේ ගෙටත් වඩා tall කියනවනේ

### 3.400. `ගුවන්` -> `air`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ගුවන් යානයට නගිද්දි  වේක් වෙලා නැද්ද
  - [NOT] after:  @USER air යානයට නගිද්දි  වේක් වෙලා නැද්ද
  - [NOT] before: @USER ගුවන් යානයට නගිද්දි  වේක් වෙලා නැද්ද
  - [NOT] after:  @USER air යානයට නගිද්දි  වේක් වෙලා නැද්ද

### 3.401. `අන්තිමේ` -> `finally`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හරිනෙ දැන් මුන් ඔක්කොම උඞින් යාවි... අන්තිමේ ඒ බරත් අපිට ... යකෝ අපිට ගැලවිමක් ඇත්තෙම නැනෙ ...
  - [NOT] after:  @USER හරිනෙ දැන් මුන් ඔක්කොම උඞින් යාවි... finally ඒ බරත් අපිට ... යකෝ අපිට ගැලවිමක් ඇත්තෙම නැනෙ ...
  - [NOT] before: @USER හරිනෙ දැන් මුන් ඔක්කොම උඞින් යාවි... අන්තිමේ ඒ බරත් අපිට ... යකෝ අපිට ගැලවිමක් ඇත්තෙම නැනෙ ...
  - [NOT] after:  @USER හරිනෙ දැන් මුන් ඔක්කොම උඞින් යාවි... finally ඒ බරත් අපිට ... යකෝ අපිට ගැලවිමක් ඇත්තෙම නැනෙ ...

### 3.402. `කීවෙ` -> `said`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔයත් පලයන් බැල්ලි කීවෙ නැද්ද
  - [NOT] after:  @USER ඔයත් පලයන් බැල්ලි said නැද්ද
  - [NOT] before: @USER ඔයත් පලයන් බැල්ලි කීවෙ නැද්ද
  - [NOT] after:  @USER ඔයත් පලයන් බැල්ලි said නැද්ද

### 3.403. `ඔයගොල්ලෝ` -> `you all`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔයගොල්ලෝ කියන්නකෝ අපි අහන් ඉන්නම්
  - [NOT] after:  @USER you all කියන්නකෝ අපි අහන් ඉන්නම්
  - [NOT] before: @USER ඔයගොල්ලෝ කියන්නකෝ අපි අහන් ඉන්නම්
  - [NOT] after:  @USER you all කියන්නකෝ අපි අහන් ඉන්නම්

### 3.404. `කවදාද` -> `when`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කවදාද දන්නේ නැහැ සහනේ ජනතාවට ලැබෙන්නේ ?
  - [NOT] after:  @USER when දන්නේ නැහැ සහනේ ජනතාවට ලැබෙන්නේ ?
  - [NOT] before: @USER කවදාද දන්නේ නැහැ සහනේ ජනතාවට ලැබෙන්නේ ?
  - [NOT] after:  @USER when දන්නේ නැහැ සහනේ public එකට ලැබෙන්නේ ?

### 3.405. `යුද්ධෙට` -> `war`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: කට්ටිය යුද්ධෙට බස්සනකොටම call එකක් ආවනේ රෙද්ද
  - [NOT] after:  කට්ටිය war බස්සනකොටම call එකක් ආවනේ රෙද්ද
  - [NOT] before: කට්ටිය යුද්ධෙට බස්සනකොටම call එකක් ආවනේ රෙද්ද
  - [NOT] after:  කට්ටිය war බස්සනකොටම call එකක් ආවනේ රෙද්ද

### 3.406. `තවමත්` -> `still`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER #lka #SriLanka  ජී එල් පීරිස් මහත්තය ප්‍රොෆෙසර් කෙනෙක් වෙලත් තවමත් රැවටෙනවද..එහෙම නැත්නම් මේ අන්තවාදීන් මෙහෙට වද්දගත්ත අපේ මුතුන් මිත්තන්ට වගෙ මෝඩ අනුකම්පාවක්වත් ඇවිල්ලද..
  - [NOT] after:  @USER #lka #SriLanka  ජී එල් පීරිස් මහත්තය ප්‍රොෆෙසර් කෙනෙක් වෙලත් still රැවටෙනවද..එහෙම නැත්නම් මේ අන්තවාදීන් මෙහෙට වද්දගත්ත අපේ මුතුන් මිත්තන්ට වගෙ මෝඩ අනුකම්පාවක්වත් ඇවිල්ලද..
  - [NOT] before: @USER #lka #SriLanka  ජී එල් පීරිස් මහත්තය ප්‍රොෆෙසර් කෙනෙක් වෙලත් තවමත් රැවටෙනවද..එහෙම නැත්නම් මේ අන්තවාදීන් මෙහෙට වද්දගත්ත අපේ මුතුන් මිත්තන්ට වගෙ මෝඩ අනුකම්පාවක්වත් ඇවිල්ලද..
  - [NOT] after:  @USER #lka #SriLanka  ජී එල් පීරිස් මහත්තය ප්‍රොෆෙසර් කෙනෙක් වෙලත් still රැවටෙනවද..එහෙම නැත්නම් මේ අන්තවාදීන් මෙහෙට වද්දගත්ත අපේ මුතුන් මිත්තන්ට වගෙ මෝඩ අනුකම්පාවක්වත් ඇවිල්ලද..

### 3.407. `පිලිගත්තා` -> `accepted`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හරි සීයේ අපි පිලිගත්තා.
  - [NOT] after:  @USER හරි සීයේ අපි accepted.
  - [NOT] before: @USER හරි සීයේ අපි පිලිගත්තා.
  - [NOT] after:  @USER හරි සීයේ අපි accepted.

### 3.408. `හොයනවා` -> `searching`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මම දන්නවා තෝ චීත්තයක් වගේ මේකේ හැමෝගෙම ඕපේ හොයනවා කියලා... එක නිසා තොගේ මුනට කිව්වත් එකයි වටේ කිවත් එකයි... අනික මේ තෝ වගේ මෙකේ ගැනු පලල් කරල දෙයි කියලා හිතාගෙන ඔලු අත ගන්න යන්නේ නෑ.... එහෙම අහේනියක් නෑ යකෝ
  - [OFF] after:  @USER මම දන්නවා තෝ චීත්තයක් වගේ මේකේ හැමෝගෙම ඕපේ searching කියලා... එක නිසා තොගේ මුනට කිව්වත් එකයි වටේ කිවත් එකයි... අනික මේ තෝ වගේ මෙකේ ගැනු පලල් කරල දෙයි කියලා හිතාගෙන ඔලු අත ගන්න යන්නේ නෑ.... එහෙම අහේනියක් නෑ යකෝ
  - [OFF] before: @USER මම දන්නවා තෝ චීත්තයක් වගේ මේකේ හැමෝගෙම ඕපේ හොයනවා කියලා... එක නිසා තොගේ මුනට කිව්වත් එකයි වටේ කිවත් එකයි... අනික මේ තෝ වගේ මෙකේ ගැනු පලල් කරල දෙයි කියලා හිතාගෙන ඔලු අත ගන්න යන්නේ නෑ.... එහෙම අහේනියක් නෑ යකෝ
  - [OFF] after:  @USER මම know තෝ චීත්තයක් වගේ මේකේ හැමෝගෙම ඕපේ searching කියලා... එක නිසා තොගේ මුනට කිව්වත් එකයි වටේ කිවත් එකයි... අනික මේ තෝ වගේ මෙකේ ගැනු පලල් කරල දෙයි කියලා හිතාගෙන ඔලු අත ගන්න යන්නේ නෑ.... එහෙම අහේනියක් නෑ යකෝ

### 3.409. `අවුරුඩු` -> `years`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER තමුසෙ අවුරුඩු 25 වෙද්දි porn star කෙනෙක් වෙයි වගේ   @USER  @USER  @USER  @USER
  - [NOT] after:  @USER තමුසෙ years 25 වෙද්දි porn star කෙනෙක් වෙයි වගේ   @USER  @USER  @USER  @USER
  - [NOT] before: @USER තමුසෙ අවුරුඩු 25 වෙද්දි porn star කෙනෙක් වෙයි වගේ   @USER  @USER  @USER  @USER
  - [NOT] after:  @USER තමුසෙ years 25 වෙද්දි porn star කෙනෙක් වෙයි වගේ   @USER  @USER  @USER  @USER

### 3.410. `ජීවතුන්` -> `alive`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  ඒකි ජීවතුන් අතරලු
  - [NOT] after:  @USER @USER  ඒකි alive අතරලු
  - [NOT] before: @USER @USER  ඒකි ජීවතුන් අතරලු
  - [NOT] after:  @USER @USER  ඒකි alive අතරලු

### 3.411. `සැකයි` -> `doubt`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ගේල් කාරය නාකි බච්චන් කාරයව හම්බවෙන්න ගිය එක ගැනනම් මට සැකයි. #INDvWI #WT20
  - [NOT] after:  ගේල් කාරය නාකි බච්චන් කාරයව හම්බවෙන්න ගිය එක ගැනනම් මට doubt. #INDvWI #WT20
  - [NOT] before: ගේල් කාරය නාකි බච්චන් කාරයව හම්බවෙන්න ගිය එක ගැනනම් මට සැකයි. #INDvWI #WT20
  - [NOT] after:  ගේල් කාරය නාකි බච්චන් කාරයව හම්බවෙන්න ගිය එක ගැනනම් මට doubt. #INDvWI #WT20

### 3.412. `මාස` -> `months`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 6 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අමාරුවෙන් ලැබෙන දෙය හැම විටම ශ්‍රේෂ්ඨයි !  ඇතින්නියක් සහ බැල්ලියෙකු එකවර ගැබ් ගත්තේය. මාස තුනකට පසු බැල්ලි බලු පැටවුන් හය දෙනෙකු බිහි කළේය. මාස හයකට පසු, බැල්ලි නැවත ගැබ්ගෙන ඇති අතර, මාස නවයකදී එහි තවත් බලු පැටවුන් දුසිමක් බිහි කළේය. රටාව දිගටම පැවතුනි.
  - [NOT] after:  අමාරුවෙන් ලැබෙන දෙය හැම විටම ශ්‍රේෂ්ඨයි !  ඇතින්නියක් සහ බැල්ලියෙකු එකවර ගැබ් ගත්තේය. months තුනකට පසු බැල්ලි බලු පැටවුන් හය දෙනෙකු බිහි කළේය. months හයකට පසු, බැල්ලි නැවත ගැබ්ගෙන ඇති අතර, months නවයකදී එහි තවත් බලු පැටවුන් දුසිමක් බිහි කළේය. රටාව දිගටම පැවතුනි.
  - [NOT] before: අමාරුවෙන් ලැබෙන දෙය හැම විටම ශ්‍රේෂ්ඨයි !  ඇතින්නියක් සහ බැල්ලියෙකු එකවර ගැබ් ගත්තේය. මාස තුනකට පසු බැල්ලි බලු පැටවුන් හය දෙනෙකු බිහි කළේය. මාස හයකට පසු, බැල්ලි නැවත ගැබ්ගෙන ඇති අතර, මාස නවයකදී එහි තවත් බලු පැටවුන් දුසිමක් බිහි කළේය. රටාව දිගටම පැවතුනි.
  - [NOT] after:  අමාරුවෙන් ලැබෙන දෙය හැම විටම ශ්‍රේෂ්ඨයි !  ඇතින්නියක් සහ බැල්ලියෙකු එකවර ගැබ් ගත්තේය. months තුනකට පසු බැල්ලි බලු පැටවුන් හය දෙනෙකු born කළේය. months හයකට පසු, බැල්ලි නැවත ගැබ්ගෙන ඇති අතර, months නවයකදී එහි තවත් බලු පැටවුන් දුසිමක් born කළේය. රටාව දිගටම පැවතුනි.

### 3.413. `මහත්මයා` -> `gentleman`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඉතාමත් නිවැරදියි.මහත්මයෙක් හා ගොබ්බයෙක් අතර සටනකින් මහත්මයා දිනුවා.එච්චරයි.
  - [OFF] after:  @USER ඉතාමත් නිවැරදියි.මහත්මයෙක් හා ගොබ්බයෙක් අතර සටනකින් gentleman දිනුවා.එච්චරයි.
  - [OFF] before: @USER ඉතාමත් නිවැරදියි.මහත්මයෙක් හා ගොබ්බයෙක් අතර සටනකින් මහත්මයා දිනුවා.එච්චරයි.
  - [OFF] after:  @USER very නිවැරදියි.මහත්මයෙක් හා ගොබ්බයෙක් අතර සටනකින් gentleman දිනුවා.එච්චරයි.

### 3.414. `ගිනි` -> `fire`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අපේ ම්නිස්සුන්ට තියෙන්නෙත් India වල මානසිකත්වය. ම්නිහා මැරුනාහම ගෑණි ගිනි සෑයට  පනින්න ඕන වගේ.
  - [NOT] after:  @USER අපේ ම්නිස්සුන්ට තියෙන්නෙත් India වල මානසිකත්වය. ම්නිහා මැරුනාහම ගෑණි fire සෑයට  පනින්න ඕන වගේ.
  - [NOT] before: @USER අපේ ම්නිස්සුන්ට තියෙන්නෙත් India වල මානසිකත්වය. ම්නිහා මැරුනාහම ගෑණි ගිනි සෑයට  පනින්න ඕන වගේ.
  - [NOT] after:  @USER අපේ ම්නිස්සුන්ට තියෙන්නෙත් India වල මානසිකත්වය. ම්නිහා මැරුනාහම ගෑණි fire සෑයට  පනින්න ඕන වගේ.

### 3.415. `ජාති` -> `race`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: යකෝ තොට මෝල නැගලා නං පල වල් ගැහැණියක් පස්සේ...අසරණ ලමයින්ට ඉගෙන ගන්න දිපං සක්කිලියෝ...උබලා තමයි ජාති වාද පටං ගෙන... URL
  - [OFF] after:  යකෝ තොට මෝල නැගලා නං පල වල් ගැහැණියක් පස්සේ...අසරණ ලමයින්ට ඉගෙන ගන්න දිපං සක්කිලියෝ...උබලා තමයි race වාද පටං ගෙන... URL
  - [OFF] before: යකෝ තොට මෝල නැගලා නං පල වල් ගැහැණියක් පස්සේ...අසරණ ලමයින්ට ඉගෙන ගන්න දිපං සක්කිලියෝ...උබලා තමයි ජාති වාද පටං ගෙන... URL
  - [OFF] after:  යකෝ තොට මෝල නැගලා නං පල වල් ගැහැණියක් පස්සේ...helpless ලමයින්ට ඉගෙන ගන්න දිපං සක්කිලියෝ...උබලා තමයි race වාද පටං ගෙන... URL

### 3.416. `බල්ලන්` -> `dogs`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සෑම Campus එකකම ඉන්න බල්ලන් ලවා ජාතක උනු පොන්න හැත්ත... මේවගේ උන් ගන්න  නැතුව ඉන්න ඔනේ
  - [OFF] after:  සෑම Campus එකකම ඉන්න dogs ලවා ජාතක උනු පොන්න හැත්ත... මේවගේ උන් ගන්න  නැතුව ඉන්න ඔනේ
  - [OFF] before: සෑම Campus එකකම ඉන්න බල්ලන් ලවා ජාතක උනු පොන්න හැත්ත... මේවගේ උන් ගන්න  නැතුව ඉන්න ඔනේ
  - [OFF] after:  every Campus එකකම ඉන්න dogs ලවා ජාතක උනු පොන්න හැත්ත... මේවගේ උන් ගන්න  නැතුව ඉන්න ඔනේ

### 3.417. `ඇතුලට` -> `inside`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: රෙද්ද තමයි. ඔය දොර ඇරගෙන වෙන මොකෙක් හරි එකෙක් ඇතුලට ගිහිල්ල එළියටත් ඇවිල්ල ඉඳීවි
  - [NOT] after:  රෙද්ද තමයි. ඔය door ඇරගෙන වෙන මොකෙක් හරි එකෙක් inside ගිහිල්ල එළියටත් ඇවිල්ල ඉඳීවි
  - [NOT] before: @USER රෙද්ද උස්සගෙන ඇතුලට ගිහින් රෙද්ද හද හදා එලියට එන එවුන් ද..
  - [NOT] after:  @USER රෙද්ද උස්සගෙන inside ගිහින් රෙද්ද heart හදා එලියට එන එවුන් ද..

### 3.418. `ඇත්තද` -> `really`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ආනේ ඇත්තද! කොහෙද හිටියේ මෙච්චර වෙලා?
  - [NOT] after:  @USER ආනේ really! කොහෙද හිටියේ මෙච්චර වෙලා?
  - [NOT] before: @USER ආනේ ඇත්තද! කොහෙද හිටියේ මෙච්චර වෙලා?
  - [NOT] after:  @USER ආනේ really! කොහෙද හිටියේ මෙච්චර වෙලා?

### 3.419. `මසට` -> `meat`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හරකා මොකා උනත් අවසානෙ මසට යාලු
  - [NOT] after:  @USER හරකා මොකා උනත් අවසානෙ meat යාලු
  - [NOT] before: @USER හරකා මොකා උනත් අවසානෙ මසට යාලු
  - [NOT] after:  @USER හරකා මොකා උනත් finally meat යාලු

### 3.420. `කීයද` -> `how much`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER නිකන් අහන්නෙ 2015 කීයද තිබ්බෙ? 6 ගානක්ද?
  - [NOT] after:  @USER නිකන් අහන්නෙ 2015 how much තිබ්බෙ? 6 ගානක්ද?
  - [NOT] before: @USER නිකන් අහන්නෙ 2015 කීයද තිබ්බෙ? 6 ගානක්ද?
  - [NOT] after:  @USER නිකන් අහන්නෙ 2015 how much තිබ්බෙ? 6 ගානක්ද?

### 3.421. `සභ්‍ය` -> `decent`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: 'පුප' කියන්නෙත් 'පුක'ටම නම්, පුක අසභ්‍ය වෙලා පුප සභ්‍ය වෙන්නේ අහවල් හුත්තක් නිසා දැ?  #මටතියෙනපුරස්න #උණවිකාරේ — feeling amused
  - [OFF] after:  'පුප' කියන්නෙත් 'පුක'ටම නම්, පුක අසභ්‍ය වෙලා පුප decent වෙන්නේ අහවල් හුත්තක් නිසා දැ?  #මටතියෙනපුරස්න #උණවිකාරේ — feeling amused
  - [OFF] before: 'පුප' කියන්නෙත් 'පුක'ටම නම්, පුක අසභ්‍ය වෙලා පුප සභ්‍ය වෙන්නේ අහවල් හුත්තක් නිසා දැ?  #මටතියෙනපුරස්න #උණවිකාරේ — feeling amused
  - [OFF] after:  'පුප' කියන්නෙත් 'පුක'ටම නම්, පුක අසභ්‍ය වෙලා පුප decent වෙන්නේ අහවල් හුත්තක් නිසා දැ?  #මටතියෙනපුරස්න #උණවිකාරේ — feeling amused

### 3.422. `දරු` -> `child`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  දරු කමට උනත් බං...... උඹ පව්.   @USER  @USER
  - [NOT] after:  @USER  child කමට උනත් බං...... උඹ පව්.   @USER  @USER
  - [NOT] before: @USER  දරු කමට උනත් බං...... උඹ පව්.   @USER  @USER
  - [NOT] after:  @USER  child කමට උනත් බං...... උඹ පව්.   @USER  @USER

### 3.423. `මහින්දගේ` -> `Mahinda's`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: එදා මහින්දගේ කටවුට් ගැන කැ ගහපු පොන්න හරකුන්ගේ අවදානයට...   ඉරිසියාවේ පැලිච්ච බල්ලො දැන් නිදිද ? URL
  - [OFF] after:  එදා Mahinda's කටවුට් ගැන කැ ගහපු පොන්න හරකුන්ගේ අවදානයට...   ඉරිසියාවේ පැලිච්ච බල්ලො දැන් නිදිද ? URL
  - [OFF] before: එදා මහින්දගේ කටවුට් ගැන කැ ගහපු පොන්න හරකුන්ගේ අවදානයට...   ඉරිසියාවේ පැලිච්ච බල්ලො දැන් නිදිද ? URL
  - [OFF] after:  එදා Mahinda's කටවුට් ගැන කැ ගහපු පොන්න හරකුන්ගේ අවදානයට...   ඉරිසියාවේ පැලිච්ච බල්ලො දැන් නිදිද ? URL

### 3.424. `මානිසුන්` -> `people`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER සමහර මානිසුන්  ගේ නොබිනා  කතා
  - [NOT] after:  @USER සමහර people  ගේ නොබිනා  කතා
  - [NOT] before: @USER සමහර මානිසුන්  ගේ නොබිනා  කතා
  - [NOT] after:  @USER සමහර people  ගේ නොබිනා  talk

### 3.425. `හිරු` -> `sun`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හිරු එකේ කාටුන් තෝරන පර හැත්ත , පොඩි උන්ගේ රස වින්දනය කනවා!!
  - [OFF] after:  sun එකේ කාටුන් තෝරන පර හැත්ත , පොඩි උන්ගේ රස වින්දනය කනවා!!
  - [OFF] before: හිරු එකේ කාටුන් තෝරන පර හැත්ත , පොඩි උන්ගේ රස වින්දනය කනවා!!
  - [OFF] after:  sun එකේ කාටුන් තෝරන පර හැත්ත , පොඩි උන්ගේ රස වින්දනය කනවා!!

### 3.426. `අඩන්න` -> `cry`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  එල එල.. අඩො අනිත් අයට ඇඬෙන්න උඹ අඬපන් ඇහ්.. මගේ මරණෙට අඩන්න කවුරුත් නැති වෙයි මං හිතන්නේ..
  - [NOT] after:  @USER @USER  එල එල.. අඩො අනිත් අයට ඇඬෙන්න උඹ අඬපන් ඇහ්.. මගේ මරණෙට cry කවුරුත් නැති වෙයි මං හිතන්නේ..
  - [NOT] before: @USER @USER  එල එල.. අඩො අනිත් අයට ඇඬෙන්න උඹ අඬපන් ඇහ්.. මගේ මරණෙට අඩන්න කවුරුත් නැති වෙයි මං හිතන්නේ..
  - [NOT] after:  @USER @USER  එල එල.. අඩො other අයට ඇඬෙන්න උඹ අඬපන් ඇහ්.. මගේ මරණෙට cry කවුරුත් නැති වෙයි මං හිතන්නේ..

### 3.427. `යට` -> `under`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මේ වගේ පොන්න නායකයන්ට යට වෙලා අපිටත් ජිවත් වෙන්න උනානේ.
  - [OFF] after:  @USER මේ වගේ පොන්න නායකයන්ට under වෙලා අපිටත් ජිවත් වෙන්න උනානේ.
  - [OFF] before: @USER මේ වගේ පොන්න නායකයන්ට යට වෙලා අපිටත් ජිවත් වෙන්න උනානේ.
  - [OFF] after:  @USER මේ වගේ පොන්න නායකයන්ට under වෙලා අපිටත් live වෙන්න උනානේ.

### 3.428. `යලු` -> `friends`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ,  @USER  @USER අපි යලු වෙන්නේ ගණිකාවක් එක්කද  හුක#%_ දාලා
  - [OFF] after:  @USER ,  @USER  @USER අපි friends වෙන්නේ ගණිකාවක් එක්කද  හුක#%_ දාලා
  - [OFF] before: @USER ,  @USER  @USER අපි යලු වෙන්නේ ගණිකාවක් එක්කද  හුක#%_ දාලා
  - [OFF] after:  @USER ,  @USER  @USER අපි friends වෙන්නේ ගණිකාවක් එක්කද  හුක#%_ දාලා

### 3.429. `කවද්ද` -> `when`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: හෑහ් කවද්ද බොල මං ඔය මනුස්පයව නාක ලමේක් කලේ URL This Tweet is unavailable.
  - [NOT] after:  හෑහ් when බොල මං ඔය මනුස්පයව නාක ලමේක් කලේ URL This Tweet is unavailable.
  - [NOT] before: හෑහ් කවද්ද බොල මං ඔය මනුස්පයව නාක ලමේක් කලේ URL This Tweet is unavailable.
  - [NOT] after:  හෑහ් when බොල මං ඔය මනුස්පයව නාක ලමේක් කලේ URL This Tweet is unavailable.

### 3.430. `අත්` -> `hands`
- impact: 2 posts (0 light, 2 heavy), 1 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER එදා ඉඳලා මං ගොඩක් උන්ව අත් ඇරියා.   ඔනෑවට වඩා පුක දෙන්න ගියාම අගයක් නැති වෙන බව තේරුම් ගත්තා
  - [OFF] after:  @USER  @USER එදා ඉඳලා මං lot උන්ව hands ඇරියා.   ඔනෑවට වඩා පුක දෙන්න ගියාම අගයක් නැති වෙන බව තේරුම් ගත්තා
  - [NOT] before: @USER නිවන් සුව අත් වේවා
  - [NOT] after:  @USER nirvana සුව hands වේවා

### 3.431. `මැදියම්` -> `midnight`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මැදියම් නෙමේ දැන්ම පටන් ගෙන
  - [NOT] after:  @USER midnight නෙමේ දැන්ම පටන් ගෙන
  - [NOT] before: @USER මැදියම් නෙමේ දැන්ම පටන් ගෙන
  - [NOT] after:  @USER midnight නෙමේ දැන්ම start ගෙන

### 3.432. `රාජ්` -> `Raj`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER රාජ් නාම් තෝ සුනා හෝගා
  - [NOT] after:  @USER Raj නාම් තෝ සුනා හෝගා
  - [NOT] before: @USER රාජ් නාම් තෝ සුනා හෝගා
  - [NOT] after:  @USER Raj නාම් තෝ සුනා හෝගා

### 3.433. `බොහොම` -> `very`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මම බොහොම බයවුනා මගේ පණ එපා වුනා   තෝ බුදිය ගන්නෙ නැද්ද බොල
  - [NOT] after:  මම very බයවුනා මගේ පණ එපා වුනා   තෝ බුදිය ගන්නෙ නැද්ද බොල
  - [NOT] before: මම බොහොම බයවුනා මගේ පණ එපා වුනා   තෝ බුදිය ගන්නෙ නැද්ද බොල
  - [NOT] after:  මම very බයවුනා මගේ පණ එපා වුනා   තෝ බුදිය ගන්නෙ නැද්ද බොල

### 3.434. `බුදු` -> `Buddha`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මේ වගේ කාලකණ්ණි ඉන්න නිසා තමයි අපේ රත්තරං බුදු දහම
  - [OFF] after:  මේ වගේ කාලකණ්ණි ඉන්න නිසා තමයි අපේ රත්තරං Buddha දහම
  - [OFF] before: මේ වගේ කාලකණ්ණි ඉන්න නිසා තමයි අපේ රත්තරං බුදු දහම
  - [OFF] after:  මේ වගේ කාලකණ්ණි ඉන්න නිසා තමයි අපේ රත්තරං Buddha දහම

### 3.435. `නාකී` -> `old`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අඩො රමීස් රාජා නාකී කිවුවනේ.
  - [NOT] after:  අඩො රමීස් රාජා old කිවුවනේ.
  - [NOT] before: අඩො රමීස් රාජා නාකී කිවුවනේ.
  - [NOT] after:  අඩො රමීස් රාජා old කිවුවනේ.

### 3.436. `ක්‍රිෂ්මාල්` -> `Krishmal`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මා හිතන් හිටියේ රෙද්ද කඩා ගත්තා විතරක් කියාය. නමුත් ක්‍රිෂ්මාල් කියන්නේ ඇට දෙකක්ද නැති බවය. URL
  - [OFF] after:  මා හිතන් හිටියේ රෙද්ද කඩා ගත්තා විතරක් කියාය. නමුත් Krishmal කියන්නේ ඇට දෙකක්ද නැති බවය. URL
  - [OFF] before: මා හිතන් හිටියේ රෙද්ද කඩා ගත්තා විතරක් කියාය. නමුත් ක්‍රිෂ්මාල් කියන්නේ ඇට දෙකක්ද නැති බවය. URL
  - [OFF] after:  මා හිතන් හිටියේ රෙද්ද කඩා ගත්තා විතරක් කියාය. නමුත් Krishmal කියන්නේ ඇට දෙකක්ද නැති බවය. URL

### 3.437. `සෙප්‍රනෝ` -> `soprano`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: බල්ලා  #හිස්තැන්පුරවමු  සෙප්‍රනෝ ඔකියෝපියර්ස්  @USER  · 23 Nov 2019 _ ල්ලා  #හිස්තැන්පුරවමු
  - [NOT] after:  බල්ලා  #හිස්තැන්පුරවමු  soprano ඔකියෝපියර්ස්  @USER  · 23 Nov 2019 _ ල්ලා  #හිස්තැන්පුරවමු
  - [NOT] before: බල්ලා  #හිස්තැන්පුරවමු  සෙප්‍රනෝ ඔකියෝපියර්ස්  @USER  · 23 Nov 2019 _ ල්ලා  #හිස්තැන්පුරවමු
  - [NOT] after:  dog  #හිස්තැන්පුරවමු  soprano ඔකියෝපියර්ස්  @USER  · 23 Nov 2019 _ ල්ලා  #හිස්තැන්පුරවමු

### 3.438. `විනාස` -> `destroy`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මූ සිව්‍රක් පොරොගෙන ඉන්න පොන්න පකෙක් තො ඔක ගල්වපන් අපෙ ජාතිය විනාස කරන්නැතුව... URL
  - [OFF] after:  මූ සිව්‍රක් පොරොගෙන ඉන්න පොන්න පකෙක් තො ඔක ගල්වපන් අපෙ ජාතිය destroy කරන්නැතුව... URL
  - [OFF] before: මූ සිව්‍රක් පොරොගෙන ඉන්න පොන්න පකෙක් තො ඔක ගල්වපන් අපෙ ජාතිය විනාස කරන්නැතුව... URL
  - [OFF] after:  මූ සිව්‍රක් පොරොගෙන ඉන්න පොන්න පකෙක් තො ඔක ගල්වපන් අපෙ nation destroy කරන්නැතුව... URL

### 3.439. `දුන්` -> `gave`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පුටින් මෛත්‍රීට දුන් රජ බඩුව කටුගෙට #lka #SriLanka  @USER  @USER Srilankamirror @USER  · 30 Mar 2017 පුටින් මෛත්‍රීට දුන් රජ බඩුව කටුගෙට URL
  - [NOT] after:  පුටින් මෛත්‍රීට gave රජ බඩුව කටුගෙට #lka #SriLanka  @USER  @USER Srilankamirror @USER  · 30 Mar 2017 පුටින් මෛත්‍රීට gave රජ බඩුව කටුගෙට URL
  - [NOT] before: පුටින් මෛත්‍රීට දුන් රජ බඩුව කටුගෙට #lka #SriLanka  @USER  @USER Srilankamirror @USER  · 30 Mar 2017 පුටින් මෛත්‍රීට දුන් රජ බඩුව කටුගෙට URL
  - [NOT] after:  පුටින් මෛත්‍රීට gave රජ බඩුව කටුගෙට #lka #SriLanka  @USER  @USER Srilankamirror @USER  · 30 Mar 2017 පුටින් මෛත්‍රීට gave රජ බඩුව කටුගෙට URL

### 3.440. `මුන්ව` -> `them`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මුන්ව මොකට ජාතක කලාද මන්ද කරුමක්කාර හැත්ත
  - [OFF] after:  @USER them මොකට ජාතක කලාද මන්ද කරුමක්කාර හැත්ත
  - [OFF] before: @USER මුන්ව මොකට ජාතක කලාද මන්ද කරුමක්කාර හැත්ත
  - [OFF] after:  @USER them මොකට ජාතක කලාද මන්ද කරුමක්කාර හැත්ත

### 3.441. `ඉවසීම` -> `patience`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මිනිසුන් ගේ ඉවසීම පරික්ෂා කිරීමට තව කල් තීබේ
  - [NOT] after:  @USER මිනිසුන් ගේ patience පරික්ෂා කිරීමට තව කල් තීබේ
  - [NOT] before: @USER මිනිසුන් ගේ ඉවසීම පරික්ෂා කිරීමට තව කල් තීබේ
  - [NOT] after:  @USER people ගේ patience පරික්ෂා කිරීමට තව කල් තීබේ

### 3.442. `අච්චාරු` -> `pickle`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER පුක දැවිල්ල ඇති අච්චාරු ගෑවිලා ම්ම්ම්
  - [OFF] after:  @USER  @USER පුක දැවිල්ල ඇති pickle ගෑවිලා ම්ම්ම්
  - [OFF] before: @USER  @USER පුක දැවිල්ල ඇති අච්චාරු ගෑවිලා ම්ම්ම්
  - [OFF] after:  @USER  @USER පුක burning ඇති pickle ගෑවිලා ම්ම්ම්

### 3.443. `දෙකම` -> `both`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ශා ලසාන තන...ඇයි දන්නෑ තන් දෙකම අදින්නේ නැතුව එක තනක් ඇන්දේ
  - [OFF] after:  @USER ශා ලසාන තන...ඇයි දන්නෑ තන් both අදින්නේ නැතුව එක තනක් ඇන්දේ
  - [OFF] before: @USER ශා ලසාන තන...ඇයි දන්නෑ තන් දෙකම අදින්නේ නැතුව එක තනක් ඇන්දේ
  - [OFF] after:  @USER ශා ලසාන තන...ඇයි දන්නෑ තන් both අදින්නේ නැතුව එක තනක් ඇන්දේ

### 3.444. `නුඹෙ` -> `your`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කැරි රසගුලා රාධා මන  කරුපයියා බැරි මට කිමෑ  ඇර මාගේ හද  පයියා පිරි පෙම් බිජ්ජ උකවා මුළු ලෝ පයියා තිරි රිරි පකේ හිටුවමි නුඹෙ රසකයියා                                                        ( මකරකවි )
  - [OFF] after:  කැරි රසගුලා රාධා මන  කරුපයියා බැරි මට කිමෑ  ඇර මාගේ හද  පයියා පිරි පෙම් බිජ්ජ උකවා මුළු ලෝ පයියා තිරි රිරි පකේ හිටුවමි your රසකයියා                                                        ( මකරකවි )
  - [OFF] before: කැරි රසගුලා රාධා මන  කරුපයියා බැරි මට කිමෑ  ඇර මාගේ හද  පයියා පිරි පෙම් බිජ්ජ උකවා මුළු ලෝ පයියා තිරි රිරි පකේ හිටුවමි නුඹෙ රසකයියා                                                        ( මකරකවි )
  - [OFF] after:  කැරි රසගුලා රාධා මන  කරුපයියා බැරි මට කිමෑ  ඇර මාගේ heart  පයියා පිරි පෙම් බිජ්ජ උකවා මුළු ලෝ පයියා තිරි රිරි පකේ හිටුවමි your රසකයියා                                                        ( මකරකවි )

### 3.445. `කන්‍යා` -> `virgin`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER නාග කන්‍යා වේසි
  - [OFF] after:  @USER  @USER නාග virgin වේසි
  - [OFF] before: @USER  @USER නාග කන්‍යා වේසි
  - [OFF] after:  @USER  @USER නාග virgin වේසි

### 3.446. `ලාජ්ජා` -> `shame`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER තව ලාජ්ජා නෑ නේ මුන්ට
  - [NOT] after:  @USER තව shame නෑ නේ මුන්ට
  - [NOT] before: @USER තව ලාජ්ජා නෑ නේ මුන්ට
  - [NOT] after:  @USER තව shame නෑ නේ මුන්ට

### 3.447. `නැතිනම්` -> `otherwise`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ගොනා කන පැලේ ගොන් පැලේ නැතිනම් රජ පැලේද?
  - [NOT] after:  ගොනා කන පැලේ ගොන් පැලේ otherwise රජ පැලේද?
  - [NOT] before: ගොනා කන පැලේ ගොන් පැලේ නැතිනම් රජ පැලේද?
  - [NOT] after:  ගොනා කන පැලේ ගොන් පැලේ otherwise රජ පැලේද?

### 3.448. `ෆොන්සේකා` -> `Fonseka`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER සරත් ෆොන්සේකා 2010 එනකොට පැසිස්ට් කතා මතක් නොවිච්ච උදවියට 2019   @USER   එනකොට පැසිස්ට් කතා මතක්වීම පුදුමයට කරුණකි ! #SRILANKA #LKA  @USER @USER  #PressPoll2019
  - [NOT] after:  @USER සරත් Fonseka 2010 එනකොට පැසිස්ට් කතා මතක් නොවිච්ච උදවියට 2019   @USER   එනකොට පැසිස්ට් කතා මතක්වීම පුදුමයට කරුණකි ! #SRILANKA #LKA  @USER @USER  #PressPoll2019
  - [NOT] before: @USER සරත් ෆොන්සේකා 2010 එනකොට පැසිස්ට් කතා මතක් නොවිච්ච උදවියට 2019   @USER   එනකොට පැසිස්ට් කතා මතක්වීම පුදුමයට කරුණකි ! #SRILANKA #LKA  @USER @USER  #PressPoll2019
  - [NOT] after:  @USER සරත් Fonseka 2010 එනකොට පැසිස්ට් talk මතක් නොවිච්ච උදවියට 2019   @USER   එනකොට පැසිස්ට් talk මතක්වීම පුදුමයට කරුණකි ! #SRILANKA #LKA  @USER @USER  #PressPoll2019

### 3.449. `අරුන්දික` -> `Arundika`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: Mr අරුන්දික, මොනවද ඕයී තමුසෙ කියවන්නෙ ඔය   #වාදපිටිය
  - [OFF] after:  Mr Arundika, මොනවද ඕයී තමුසෙ කියවන්නෙ ඔය   #වාදපිටිය
  - [OFF] before: Mr අරුන්දික, මොනවද ඕයී තමුසෙ කියවන්නෙ ඔය   #වාදපිටිය
  - [OFF] after:  Mr Arundika, මොනවද ඕයී තමුසෙ කියවන්නෙ ඔය   #වාදපිටිය

### 3.450. `සුපුරුදු` -> `usual`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER බැන අහල ඉවරයි... දැං සුපුරුදු කරුම ජිඋවිතේට..
  - [NOT] after:  @USER බැන අහල ඉවරයි... දැං usual කරුම ජිඋවිතේට..
  - [NOT] before: @USER බැන අහල ඉවරයි... දැං සුපුරුදු කරුම ජිඋවිතේට..
  - [NOT] after:  @USER scold අහල ඉවරයි... දැං usual කරුම ජිඋවිතේට..

### 3.451. `මෙන්ඩිස්` -> `Mendis`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කුසල් මෙන්ඩිස්! මේ වේසි අපිව කෑවා!!
  - [OFF] after:  කුසල් Mendis! මේ වේසි අපිව කෑවා!!
  - [OFF] before: කුසල් මෙන්ඩිස්! මේ වේසි අපිව කෑවා!!
  - [OFF] after:  කුසල් Mendis! මේ වේසි us කෑවා!!

### 3.452. `හම්සා` -> `Hamsa`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ,  @USER  @USER උබ ඔය කිහන්නේ අපේ අමිතයට සනික මෝචනේ කියලාදා ? හම්සා තෝ අහුවෙන්න එපා අපේ අමියාට එවා මේවා කියලා
  - [OFF] after:  @USER ,  @USER  @USER උබ ඔය කිහන්නේ අපේ අමිතයට සනික මෝචනේ කියලාදා ? Hamsa තෝ අහුවෙන්න එපා අපේ අමියාට එවා මේවා කියලා
  - [OFF] before: @USER ,  @USER  @USER උබ ඔය කිහන්නේ අපේ අමිතයට සනික මෝචනේ කියලාදා ? හම්සා තෝ අහුවෙන්න එපා අපේ අමියාට එවා මේවා කියලා
  - [OFF] after:  @USER ,  @USER  @USER උබ ඔය කිහන්නේ අපේ අමිතයට සනික මෝචනේ කියලාදා ? Hamsa තෝ අහුවෙන්න එපා අපේ අමියාට එවා මේවා කියලා

### 3.453. `වෙනි` -> `th`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER බල්ලෙක් හදලම නෑ වගේ නේද? මන් හිතන්නේ මේ මගේ දහ වෙනි නැත්නම් එකොලොස් වෙනි බල්ලා පොඩිකාලේ ඉඳල හදපු.
  - [NOT] after:  @USER @USER බල්ලෙක් හදලම නෑ වගේ නේද? මන් හිතන්නේ මේ මගේ දහ th නැත්නම් එකොලොස් th බල්ලා පොඩිකාලේ ඉඳල හදපු.
  - [NOT] before: @USER @USER බල්ලෙක් හදලම නෑ වගේ නේද? මන් හිතන්නේ මේ මගේ දහ වෙනි නැත්නම් එකොලොස් වෙනි බල්ලා පොඩිකාලේ ඉඳල හදපු.
  - [NOT] after:  @USER @USER බල්ලෙක් හදලම නෑ වගේ නේද? මන් හිතන්නේ මේ මගේ ten th නැත්නම් එකොලොස් th බල්ලා පොඩිකාලේ ඉඳල හදපු.

### 3.454. `උංගෙ` -> `their`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER උංගෙ මර්ධනය කරගෙන ඉන්ට කියපිය ඉස්සෙල්ලා
  - [NOT] after:  @USER their මර්ධනය කරගෙන ඉන්ට කියපිය ඉස්සෙල්ලා
  - [NOT] before: @USER උංගෙ මර්ධනය කරගෙන ඉන්ට කියපිය ඉස්සෙල්ලා
  - [NOT] after:  @USER their මර්ධනය කරගෙන ඉන්ට කියපිය first

### 3.455. `ගැලපෙන` -> `matching`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER ම්ම් සෙස්.... මම හිතුවා තෝ ඕක කියයි කියලා.  Copyright free ගැලපෙන සවුන්ඩ් එකක් හොයා ගන්න තිබ්බෙ නෑ
  - [OFF] after:  @USER  @USER ම්ම් සෙස්.... මම හිතුවා තෝ ඕක කියයි කියලා.  Copyright free matching සවුන්ඩ් එකක් හොයා ගන්න තිබ්බෙ නෑ
  - [OFF] before: @USER  @USER ම්ම් සෙස්.... මම හිතුවා තෝ ඕක කියයි කියලා.  Copyright free ගැලපෙන සවුන්ඩ් එකක් හොයා ගන්න තිබ්බෙ නෑ
  - [OFF] after:  @USER  @USER ම්ම් සෙස්.... මම හිතුවා තෝ ඕක කියයි කියලා.  Copyright free matching සවුන්ඩ් එකක් හොයා ගන්න තිබ්බෙ නෑ

### 3.456. `කුරුල්ලා` -> `bird`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඒ ලබ්බ නෙමේ යකෝ කුරුල්ලා කුරුල්ලා
  - [NOT] after:  @USER ඒ ලබ්බ නෙමේ යකෝ bird bird
  - [NOT] before: @USER ඒ ලබ්බ නෙමේ යකෝ කුරුල්ලා කුරුල්ලා
  - [NOT] after:  @USER ඒ ලබ්බ නෙමේ යකෝ bird bird

### 3.457. `වමනේ` -> `vomit`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER නොදකින් අහන එකාට වමනේ යයි බං
  - [OFF] after:  @USER නොදකින් අහන එකාට vomit යයි බං
  - [OFF] before: @USER නොදකින් අහන එකාට වමනේ යයි බං
  - [OFF] after:  @USER නොදකින් අහන එකාට vomit යයි බං

### 3.458. `දේවාලේ` -> `temple`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: වදින්න ගිය දේවාලේ ගොනා ඇනලා ගහෙන් වැටිච්ච මිහිහට ඉහේ කඩා පාත් උනා වගේ  #lka
  - [NOT] after:  වදින්න ගිය temple ගොනා ඇනලා ගහෙන් වැටිච්ච මිහිහට ඉහේ කඩා down උනා වගේ  #lka
  - [NOT] before: මිනිස්සුන්ගේ සාප වලින් බේරෙන්න බෑ මොන දේවාලේ ගියත්.. NewsWire @USER  · 24 Dec 2021 Sri Lanka PM Rajapaksa worships at Lord Venkateswara temple - PTI URL
  - [NOT] after:  people සාප වලින් බේරෙන්න බෑ මොන temple ගියත්.. NewsWire @USER  · 24 Dec 2021 Sri Lanka PM Rajapaksa worships at Lord Venkateswara temple - PTI URL

### 3.459. `ඉරිසියාව` -> `jealousy`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER තොට ඉරිසියාව , පලයන් බන් වද නොදී
  - [OFF] after:  @USER තොට jealousy , පලයන් බන් වද නොදී
  - [OFF] before: @USER තොට ඉරිසියාව , පලයන් බන් වද නොදී
  - [OFF] after:  @USER තොට jealousy , පලයන් බන් trouble නොදී

### 3.460. `ඵකක්` -> `one`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER රස තේ ඵකක් මෙයාට හදලා දෙන්න
  - [NOT] after:  @USER රස තේ one මෙයාට හදලා දෙන්න
  - [NOT] before: @USER රස තේ ඵකක් මෙයාට හදලා දෙන්න
  - [NOT] after:  @USER රස tea one මෙයාට හදලා දෙන්න

### 3.461. `දෙයියන්ගේ` -> `gods`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER එකටත් 33 කොටියක් දෙයියන්ගේ පිහිටයි
  - [NOT] after:  @USER එකටත් 33 කොටියක් gods පිහිටයි
  - [NOT] before: @USER එකටත් 33 කොටියක් දෙයියන්ගේ පිහිටයි
  - [NOT] after:  @USER එකටත් 33 කොටියක් gods පිහිටයි

### 3.462. `එලියෙ` -> `outside`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අක්කෙ අක්කෙ අක්කෙ අක්කෙ අක්කියෝඕඕඕඕඕ.... මොකද ඕයි කෑගහන්නෙ? අනේ ටවල් එක එලියෙ තියල ඇවිත්නෙ ගෙනත් දෙනවකෝ තමුසෙ නම් මහ... ඉන්නව පොඩ්ඩක්
  - [NOT] after:  අක්කෙ අක්කෙ අක්කෙ අක්කෙ අක්කියෝඕඕඕඕඕ.... මොකද ඕයි කෑගහන්නෙ? අනේ ටවල් එක outside තියල ඇවිත්නෙ ගෙනත් දෙනවකෝ තමුසෙ නම් මහ... ඉන්නව පොඩ්ඩක්
  - [NOT] before: අක්කෙ අක්කෙ අක්කෙ අක්කෙ අක්කියෝඕඕඕඕඕ.... මොකද ඕයි කෑගහන්නෙ? අනේ ටවල් එක එලියෙ තියල ඇවිත්නෙ ගෙනත් දෙනවකෝ තමුසෙ නම් මහ... ඉන්නව පොඩ්ඩක්
  - [NOT] after:  sister sister sister sister අක්කියෝඕඕඕඕඕ.... මොකද ඕයි කෑගහන්නෙ? අනේ ටවල් එක outside තියල ඇවිත්නෙ ගෙනත් දෙනවකෝ තමුසෙ නම් මහ... ඉන්නව පොඩ්ඩක්

### 3.463. `හෙළි` -> `reveal`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER විපක්ෂයට යනකල්ද ඉන්නෙ හෙළි කරන්න? මීට වඩා සුදුසු කාලයක් තියේද?
  - [NOT] after:  @USER විපක්ෂයට යනකල්ද ඉන්නෙ reveal කරන්න? මීට වඩා සුදුසු කාලයක් තියේද?
  - [NOT] before: @USER විපක්ෂයට යනකල්ද ඉන්නෙ හෙළි කරන්න? මීට වඩා සුදුසු කාලයක් තියේද?
  - [NOT] after:  @USER විපක්ෂයට යනකල්ද ඉන්නෙ reveal කරන්න? මීට වඩා suitable කාලයක් තියේද?

### 3.464. `මල්ලිහ්` -> `brother`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඒ නංඟිට අනුව පුලාන් මල්ලිහ්.. ඒකට කියන්නෙ නලල් පයිය
  - [OFF] after:  @USER ඒ නංඟිට අනුව පුලාන් brother.. ඒකට කියන්නෙ නලල් පයිය
  - [OFF] before: @USER ඒ නංඟිට අනුව පුලාන් මල්ලිහ්.. ඒකට කියන්නෙ නලල් පයිය
  - [OFF] after:  @USER ඒ නංඟිට අනුව පුලාන් brother.. ඒකට කියන්නෙ නලල් පයිය

### 3.465. `අහිංසකයි` -> `innocent`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  නෑ බොල.pure මේකේ අහිංසකයි
  - [NOT] after:  @USER @USER  නෑ බොල.pure මේකේ innocent
  - [NOT] before: @USER @USER  නෑ බොල.pure මේකේ අහිංසකයි
  - [NOT] after:  @USER @USER  නෑ බොල.pure මේකේ innocent

### 3.466. `නිහඩයි` -> `silent`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පයිය හඩයි ලීසා නිහඩයි
  - [OFF] after:  @USER පයිය හඩයි ලීසා silent
  - [OFF] before: @USER පයිය හඩයි ලීසා නිහඩයි
  - [OFF] after:  @USER පයිය හඩයි Lisa silent

### 3.467. `හොයනව` -> `searching`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හම්බුනෙ නෑ,තාම හොයනව යකෝ  @USER
  - [NOT] after:  @USER හම්බුනෙ නෑ,තාම searching යකෝ  @USER
  - [NOT] before: @USER හම්බුනෙ නෑ,තාම හොයනව යකෝ  @USER
  - [NOT] after:  @USER හම්බුනෙ නෑ,still searching යකෝ  @USER

### 3.468. `නොහොත්` -> `or`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER නොහොත් අතීසාරයට අමුඩ ගැසීම #freedomofExpression
  - [NOT] after:  @USER or අතීසාරයට අමුඩ ගැසීම #freedomofExpression
  - [NOT] before: @USER නොහොත් අතීසාරයට අමුඩ ගැසීම #freedomofExpression
  - [NOT] after:  @USER or අතීසාරයට අමුඩ ගැසීම #freedomofExpression

### 3.469. `පුටු` -> `chairs`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER සැමදා උදෑසන බ්‍රහ්ම මුහුර්තයෙන් පිබිදී පක්ෂියා රජ කරන වේලාව බලා පුටු සෙටි කකුලකට හුජ්ජ කරන්න
  - [OFF] after:  @USER සැමදා උදෑසන බ්‍රහ්ම මුහුර්තයෙන් පිබිදී පක්ෂියා රජ කරන වේලාව බලා chairs සෙටි කකුලකට හුජ්ජ කරන්න
  - [OFF] before: @USER සැමදා උදෑසන බ්‍රහ්ම මුහුර්තයෙන් පිබිදී පක්ෂියා රජ කරන වේලාව බලා පුටු සෙටි කකුලකට හුජ්ජ කරන්න
  - [OFF] after:  @USER සැමදා morning බ්‍රහ්ම මුහුර්තයෙන් පිබිදී පක්ෂියා රජ කරන වේලාව බලා chairs සෙටි කකුලකට හුජ්ජ කරන්න

### 3.470. `කෙල්ලොනි` -> `girls`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පවු යකෝ .... කෙල්ලොනි 󾌴󾌴 URL
  - [NOT] after:  පවු යකෝ .... girls 󾌴󾌴 URL
  - [NOT] before: පවු යකෝ .... කෙල්ලොනි 󾌴󾌴 URL
  - [NOT] after:  පවු යකෝ .... girls 󾌴󾌴 URL

### 3.471. `හිල්` -> `hole`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඇයි ඒවගේ හිල් ද ?
  - [NOT] after:  @USER ඇයි ඒවගේ hole ද ?
  - [NOT] before: @USER ඇයි ඒවගේ හිල් ද ?
  - [NOT] after:  @USER ඇයි ඒවගේ hole ද ?

### 3.472. `කූඩුවෙ` -> `cage එකේ`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER බල්ලා ඉතින් කූඩුවෙ ඇත්තෙ
  - [NOT] after:  @USER @USER බල්ලා ඉතින් cage එකේ ඇත්තෙ
  - [NOT] before: @USER @USER බල්ලා ඉතින් කූඩුවෙ ඇත්තෙ
  - [NOT] after:  @USER @USER dog ඉතින් cage එකේ ඇත්තෙ

### 3.473. `නාකියා` -> `old man`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER අනේ බං මුට බැනලා තියන තරමක්..පවි යකෝ නාකියා
  - [OFF] after:  @USER  @USER අනේ බං මුට බැනලා තියන තරමක්..පවි යකෝ old man
  - [OFF] before: @USER  @USER අනේ බං මුට බැනලා තියන තරමක්..පවි යකෝ නාකියා
  - [OFF] after:  @USER  @USER අනේ බං මුට බැනලා තියන තරමක්..පවි යකෝ old man

### 3.474. `කටයුතු` -> `affairs`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER වැව් දසදහසක් ප්‍රතිසංස්කරණය කිරීමේ ව්‍යාපෘතියට මෙම වැවත් ඇතුලත් කර  ඉක්මනින් එය යථාතත්ත්වයට පත්කිරීමට කටයුතු කරන්න  @USER  #MahindaAmaraweera #වැව්දසදහසක් #lka
  - [NOT] after:  @USER වැව් දසදහසක් ප්‍රතිසංස්කරණය කිරීමේ ව්‍යාපෘතියට මෙම වැවත් ඇතුලත් කර  ඉක්මනින් එය යථාතත්ත්වයට පත්කිරීමට affairs කරන්න  @USER  #MahindaAmaraweera #වැව්දසදහසක් #lka
  - [NOT] before: @USER වැව් දසදහසක් ප්‍රතිසංස්කරණය කිරීමේ ව්‍යාපෘතියට මෙම වැවත් ඇතුලත් කර  ඉක්මනින් එය යථාතත්ත්වයට පත්කිරීමට කටයුතු කරන්න  @USER  #MahindaAmaraweera #වැව්දසදහසක් #lka
  - [NOT] after:  @USER වැව් දසදහසක් ප්‍රතිසංස්කරණය කිරීමේ ව්‍යාපෘතියට මෙම වැවත් ඇතුලත් කර  ඉක්මනින් it යථාතත්ත්වයට පත්කිරීමට affairs කරන්න  @USER  #MahindaAmaraweera #වැව්දසදහසක් #lka

### 3.475. `අං` -> `horn`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: Howzat ! අං පහේ පිං ගොනා #lka
  - [OFF] after:  Howzat ! horn පහේ පිං ගොනා #lka
  - [OFF] before: Howzat ! අං පහේ පිං ගොනා #lka
  - [OFF] after:  Howzat ! horn පහේ පිං ගොනා #lka

### 3.476. `නගර` -> `city`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අඩො අර බ්‍රැන්ඩික්ස් කොරොනා පොකුරද කොලඹ මහ නගර සබාවෙනුත් මතුවෙන්නෙ   මන් දැනන් හොරොයෙ නෑනෙ කොලඹ මහනගර සබාව කියන්නෙ ගාමන්ට් එකක් කීලා
  - [NOT] after:  අඩො අර බ්‍රැන්ඩික්ස් කොරොනා පොකුරද කොලඹ මහ city සබාවෙනුත් මතුවෙන්නෙ   මන් දැනන් හොරොයෙ නෑනෙ කොලඹ මහනගර සබාව කියන්නෙ ගාමන්ට් එකක් කීලා
  - [NOT] before: අඩො අර බ්‍රැන්ඩික්ස් කොරොනා පොකුරද කොලඹ මහ නගර සබාවෙනුත් මතුවෙන්නෙ   මන් දැනන් හොරොයෙ නෑනෙ කොලඹ මහනගර සබාව කියන්නෙ ගාමන්ට් එකක් කීලා
  - [NOT] after:  අඩො අර බ්‍රැන්ඩික්ස් කොරොනා පොකුරද කොලඹ මහ city සබාවෙනුත් මතුවෙන්නෙ   මන් දැනන් හොරොයෙ නෑනෙ කොලඹ මහනගර සබාව කියන්නෙ ගාමන්ට් එකක් කීලා

### 3.477. `සහජීවනය` -> `coexistence`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: කාත්තන් කුඩි එපා පලයන් අකුරණ, අම්පාරේ කල්මුණේ , අක්කරෛපත්තු තොපිට සහජීවනය උගන්වයි !!!
  - [NOT] after:  කාත්තන් කුඩි එපා පලයන් අකුරණ, අම්පාරේ කල්මුණේ , අක්කරෛපත්තු තොපිට coexistence උගන්වයි !!!
  - [NOT] before: කාත්තන් කුඩි එපා පලයන් අකුරණ, අම්පාරේ කල්මුණේ , අක්කරෛපත්තු තොපිට සහජීවනය උගන්වයි !!!
  - [NOT] after:  කාත්තන් කුඩි එපා පලයන් Akurana, අම්පාරේ කල්මුණේ , අක්කරෛපත්තු තොපිට coexistence උගන්වයි !!!

### 3.478. `කොන්ඩෙ` -> `hair`
- impact: 2 posts (0 light, 2 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER  ඔව් ඔව්.... DP එකෙ හිටපු කෙනා නෙමෙ නේ  කොන්ඩෙ ගොතලා සායක් ඇදලා... ගැමිකම වැක්කෙරෙනවා  @USER  නේ බොල
  - [NOT] after:  @USER @USER  ඔව් ඔව්.... DP එකෙ හිටපු person නෙමෙ නේ  hair ගොතලා සායක් ඇදලා... ගැමිකම වැක්කෙරෙනවා  @USER  නේ බොල
  - [NOT] before: මගෙ කොන්ඩෙ නැත්ත් ඉන ගාවට රෙද්ද හැට්ටෙ නොඇන්දාට හැදිච්චකම තාම තියනවා  එතකොට හැදිච්චකම තියන්නේ විනිවිද පේන රතුපාට මෙව්වා එකකද බන්
  - [NOT] after:  මගෙ hair නැත්ත් ඉන ගාවට රෙද්ද හැට්ටෙ නොඇන්දාට හැදිච්චකම still තියනවා  එතකොට හැදිච්චකම තියන්නේ විනිවිද පේන රතුපාට මෙව්වා එකකද බන්

### 3.479. `පරණයිනෙ` -> `old`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කොහොමද ඕයි තමුසෙ මේක දැක්කෙ. හෙණ පරණයිනෙ
  - [NOT] after:  @USER කොහොමද ඕයි තමුසෙ මේක දැක්කෙ. හෙණ old
  - [NOT] before: @USER කොහොමද ඕයි තමුසෙ මේක දැක්කෙ. හෙණ පරණයිනෙ
  - [NOT] after:  @USER කොහොමද ඕයි තමුසෙ මේක දැක්කෙ. හෙණ old

### 3.480. `පිපුණා` -> `bloomed`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔව් එය ඉහලින්ම පිපුණා
  - [NOT] after:  @USER ඔව් එය ඉහලින්ම bloomed
  - [NOT] before: @USER ඔව් එය ඉහලින්ම පිපුණා
  - [NOT] after:  @USER ඔව් it ඉහලින්ම bloomed

### 3.481. `පුතාලා` -> `sons`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මෝඩ ආතල් දෙන්න ආපු පොන්න පැටව් 2ක් BLOCK කරලා, blocking list එක start කරා     මොන්ටිසෝරි ආතල් දෙන වේසිගෙ පුතාලා හිතන්නෙ උන්ගේ සුරංගනා ආතල් වලට හැමොම කැමතියි කියලා
  - [OFF] after:  මෝඩ ආතල් දෙන්න ආපු පොන්න පැටව් 2ක් BLOCK කරලා, blocking list එක start කරා     මොන්ටිසෝරි ආතල් දෙන වේසිගෙ sons හිතන්නෙ උන්ගේ සුරංගනා ආතල් වලට හැමොම කැමතියි කියලා
  - [OFF] before: මෝඩ ආතල් දෙන්න ආපු පොන්න පැටව් 2ක් BLOCK කරලා, blocking list එක start කරා     මොන්ටිසෝරි ආතල් දෙන වේසිගෙ පුතාලා හිතන්නෙ උන්ගේ සුරංගනා ආතල් වලට හැමොම කැමතියි කියලා
  - [OFF] after:  මෝඩ ආතල් දෙන්න ආපු පොන්න පැටව් 2ක් BLOCK කරලා, blocking list එක start කරා     මොන්ටිසෝරි ආතල් දෙන වේසිගෙ sons හිතන්නෙ උන්ගේ සුරංගනා ආතල් වලට හැමොම කැමතියි කියලා

### 3.482. `කොටියා` -> `tiger`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කොටියා ද?? දිවියා ද??
  - [NOT] after:  @USER tiger ද?? දිවියා ද??
  - [NOT] before: @USER කොටියා ද?? දිවියා ද??
  - [NOT] after:  @USER tiger ද?? leopard ද??

### 3.483. `කිවුවා` -> `said`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER උබ පලයන් මල්ලීයේ මටනම් බෑ ඕන් කිවුවා
  - [NOT] after:  @USER උබ පලයන් මල්ලීයේ මටනම් බෑ ඕන් said
  - [NOT] before: @USER උබ පලයන් මල්ලීයේ මටනම් බෑ ඕන් කිවුවා
  - [NOT] after:  @USER උබ පලයන් මල්ලීයේ මටනම් බෑ ඕන් said

### 3.484. `බරයි` -> `heavy`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හුජ්ජ බරයි වැස්සයි අතරෙ  අමුතු පෙමක් ඇත මගෙ මිතුරෙ
  - [OFF] after:  හුජ්ජ heavy වැස්සයි අතරෙ  අමුතු පෙමක් ඇත මගෙ මිතුරෙ
  - [OFF] before: හුජ්ජ බරයි වැස්සයි අතරෙ  අමුතු පෙමක් ඇත මගෙ මිතුරෙ
  - [OFF] after:  හුජ්ජ heavy වැස්සයි අතරෙ  strange පෙමක් ඇත මගෙ මිතුරෙ

### 3.485. `වාගේ` -> `like`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ගොවි අරගලයට බේහේත් දේනවා වාගේ....
  - [NOT] after:  @USER ගොවි අරගලයට බේහේත් දේනවා like....
  - [NOT] before: @USER ගොවි අරගලයට බේහේත් දේනවා වාගේ....
  - [NOT] after:  @USER farmer අරගලයට බේහේත් දේනවා like....

### 3.486. `වයසයි` -> `old`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ෆල ෆල නාකියො තෝ මට වඩා වයසයි  @USER
  - [OFF] after:  @USER ෆල ෆල නාකියො තෝ මට වඩා old  @USER
  - [OFF] before: @USER ෆල ෆල නාකියො තෝ මට වඩා වයසයි  @USER
  - [OFF] after:  @USER ෆල ෆල old man තෝ මට වඩා old  @USER

### 3.487. `අනූ` -> `ninety`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තොපි දෙන්නම නාකියි. හූ හූ. . .  . . . . . .  . . . .  . . . . මම අනූ තුනේ ඕලෙවල්
  - [OFF] after:  @USER  @USER තොපි දෙන්නම නාකියි. හූ හූ. . .  . . . . . .  . . . .  . . . . මම ninety තුනේ ඕලෙවල්
  - [OFF] before: @USER  @USER තොපි දෙන්නම නාකියි. හූ හූ. . .  . . . . . .  . . . .  . . . . මම අනූ තුනේ ඕලෙවල්
  - [OFF] after:  @USER  @USER තොපි දෙන්නම old. හූ හූ. . .  . . . . . .  . . . .  . . . . මම ninety තුනේ ඕලෙවල්

### 3.488. `දැල්` -> `net`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER දැල් ගොනා දැල් ගොනා
  - [NOT] after:  @USER net ගොනා net ගොනා
  - [NOT] before: @USER දැල් ගොනා දැල් ගොනා
  - [NOT] after:  @USER net ගොනා net ගොනා

### 3.489. `ගොඩාක්` -> `a lot`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: රැට රැට පුතානොගෙන් ප්‍රවෙසම් උනත්   නම #රසික කියලා තියෙන උන්ගෙන් තමයි ගොඩාක් ප්‍රවෙසම් වෙන්ට ඔනේ  මොකද ඔය #රසික කියලා නම තියෙන උන් ඉන්නවා නේද අන්න උන්න පොන්න උල්පත්           වද්දගෙන රිද්දගෙන ලොල්ල සුප්පපන් විතරක් එන්ට එපො
  - [OFF] after:  රැට රැට පුතානොගෙන් ප්‍රවෙසම් උනත්   නම #රසික කියලා තියෙන උන්ගෙන් තමයි a lot ප්‍රවෙසම් වෙන්ට ඔනේ  මොකද ඔය #රසික කියලා නම තියෙන උන් ඉන්නවා නේද අන්න උන්න පොන්න උල්පත්           වද්දගෙන රිද්දගෙන ලොල්ල සුප්පපන් විතරක් එන්ට එපො
  - [OFF] before: රැට රැට පුතානොගෙන් ප්‍රවෙසම් උනත්   නම #රසික කියලා තියෙන උන්ගෙන් තමයි ගොඩාක් ප්‍රවෙසම් වෙන්ට ඔනේ  මොකද ඔය #රසික කියලා නම තියෙන උන් ඉන්නවා නේද අන්න උන්න පොන්න උල්පත්           වද්දගෙන රිද්දගෙන ලොල්ල සුප්පපන් විතරක් එන්ට එපො
  - [OFF] after:  රැට රැට පුතානොගෙන් ප්‍රවෙසම් උනත්   නම #රසික කියලා තියෙන උන්ගෙන් තමයි a lot ප්‍රවෙසම් වෙන්ට ඔනේ  මොකද ඔය #රසික කියලා නම තියෙන උන් ඉන්නවා නේද අන්න උන්න පොන්න උල්පත්           වද්දගෙන රිද්දගෙන ලොල්ල සුප්පපන් විතරක් එන්ට එපො

### 3.490. `බැටේ` -> `beating`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මේ පාරත් අපි දෙනව බැටේ
  - [NOT] after:  @USER මේ පාරත් අපි දෙනව beating
  - [NOT] before: @USER මේ පාරත් අපි දෙනව බැටේ
  - [NOT] after:  @USER මේ පාරත් අපි දෙනව beating

### 3.491. `කතිර` -> `cross`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: නේරුලා ගාන්ධිලා නොහිටින්න අපිත් තාම කතිර කොඩියට සැලියුට් ගහනවා. [දැන් ඉතිං රෙද්ද උස්සං එන්නෙපා. ඒක තමයි ඇත්ත]... URL
  - [NOT] after:  නේරුලා ගාන්ධිලා නොහිටින්න අපිත් තාම cross කොඩියට සැලියුට් ගහනවා. [දැන් ඉතිං රෙද්ද උස්සං එන්නෙපා. ඒක තමයි ඇත්ත]... URL
  - [NOT] before: නේරුලා ගාන්ධිලා නොහිටින්න අපිත් තාම කතිර කොඩියට සැලියුට් ගහනවා. [දැන් ඉතිං රෙද්ද උස්සං එන්නෙපා. ඒක තමයි ඇත්ත]... URL
  - [NOT] after:  නේරුලා ගාන්ධිලා නොහිටින්න අපිත් still cross කොඩියට සැලියුට් ගහනවා. [දැන් ඉතිං රෙද්ද උස්සං එන්නෙපා. ඒක තමයි ඇත්ත]... URL

### 3.492. `අංතිමට` -> `finally`
- impact: 2 posts (1 light, 1 heavy), 2 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER  43 others නෙදකු  මේකිට අංතිමට මාව මතක් වෙලානේ  සංසාර කරුම
  - [OFF] after:  @USER  @USER  43 others නෙදකු  මේකිට finally මාව මතක් වෙලානේ  සංසාර කරුම
  - [OFF] before: @USER  @USER  43 others නෙදකු  මේකිට අංතිමට මාව මතක් වෙලානේ  සංසාර කරුම
  - [OFF] after:  @USER  @USER  43 others නෙදකු  මේකිට finally මාව මතක් වෙලානේ  සංසාර කරුම

### 3.493. `නයෙක්` -> `snake`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: - අය්යේ ඉස්සරහා හුඹහා ගාවින් බස්සලා යන්න - තමුසෙ නයෙක් ද ඕයි හුඹහ ගාවින් බහින්න  - නෑ වේයෙක්. තමුසෙ බස්සනවකෝ...
  - [NOT] after:  - අය්යේ ඉස්සරහා හුඹහා ගාවින් බස්සලා යන්න - තමුසෙ snake ද ඕයි හුඹහ ගාවින් බහින්න  - නෑ වේයෙක්. තමුසෙ බස්සනවකෝ...
  - [NOT] before: - අය්යේ ඉස්සරහා හුඹහා ගාවින් බස්සලා යන්න - තමුසෙ නයෙක් ද ඕයි හුඹහ ගාවින් බහින්න  - නෑ වේයෙක්. තමුසෙ බස්සනවකෝ...
  - [NOT] after:  - අය්යේ front හුඹහා ගාවින් බස්සලා යන්න - තමුසෙ snake ද ඕයි හුඹහ ගාවින් බහින්න  - නෑ වේයෙක්. තමුසෙ බස්සනවකෝ...

### 3.494. `පොල්තෙල්` -> `coconut oil`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ටහුඩු   #teamපොල්තෙල් Embraer @USER  · 12 Apr 2021 We’re always working to improve the flight experience. Learn more about our latest conceptual project under study, the Sterile Lavatory: URL #EmbraerStories #WeAreEmbraer #ForADifferentWorld
  - [NOT] after:  ටහුඩු   #teamcoconut oil Embraer @USER  · 12 Apr 2021 We’re always working to improve the flight experience. Learn more about our latest conceptual project under study, the Sterile Lavatory: URL #EmbraerStories #WeAreEmbraer #ForADifferentWorld
  - [NOT] before: ටහුඩු   #teamපොල්තෙල් Embraer @USER  · 12 Apr 2021 We’re always working to improve the flight experience. Learn more about our latest conceptual project under study, the Sterile Lavatory: URL #EmbraerStories #WeAreEmbraer #ForADifferentWorld
  - [NOT] after:  ටහුඩු   #teamcoconut oil Embraer @USER  · 12 Apr 2021 We’re always working to improve the flight experience. Learn more about our latest conceptual project under study, the Sterile Lavatory: URL #EmbraerStories #WeAreEmbraer #ForADifferentWorld

### 3.495. `තාප්ප` -> `walls`
- impact: 2 posts (1 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER TV බලලා - Radio අහලා ඉවරයි , තාප්ප විනාසයි
  - [NOT] after:  @USER TV බලලා - Radio අහලා ඉවරයි , walls විනාසයි
  - [NOT] before: @USER TV බලලා - Radio අහලා ඉවරයි , තාප්ප විනාසයි
  - [NOT] after:  @USER TV බලලා - Radio අහලා ඉවරයි , walls විනාසයි

### 3.496. `උදෑසන` -> `morning`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER සැමදා උදෑසන බ්‍රහ්ම මුහුර්තයෙන් පිබිදී පක්ෂියා රජ කරන වේලාව බලා පුටු සෙටි කකුලකට හුජ්ජ කරන්න
  - [OFF] after:  @USER සැමදා morning බ්‍රහ්ම මුහුර්තයෙන් පිබිදී පක්ෂියා රජ කරන වේලාව බලා chairs සෙටි කකුලකට හුජ්ජ කරන්න

### 3.497. `මොළ` -> `brain`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: JVP  කියන්නේ මොළ කාරයෝ කියලා කවුරුහරි කිව්වොත් මෙන්න මේක පෙන්නපන් ගොන් හැත්ත.... URL
  - [OFF] after:  JVP  කියන්නේ brain කාරයෝ කියලා someone කිව්වොත් මෙන්න මේක පෙන්නපන් ගොන් හැත්ත.... URL

### 3.498. `ඇඳුම්` -> `clothes`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER උඩ කෑල්ල ඇඳුම් නැතුව ඉන්න එව්වාද ??
  - [NOT] after:  @USER උඩ girl clothes නැතුව ඉන්න එව්වාද ??

### 3.499. `මදි` -> `not enough`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මේ වේස හුකන්නොන්ට ඔහොම වෙලා මදි.. සේවකයො කියන්නෙ තොපේ අත පල්ලෙන් වැටිච්ච උන් නෙමෙයි කියල දැන්වත් තේරුම් ගනිව්..... URL
  - [OFF] after:  මේ වේස හුකන්නොන්ට ඔහොම වෙලා not enough.. සේවකයො කියන්නෙ තොපේ අත පල්ලෙන් වැටිච්ච උන් නෙමෙයි කියල දැන්වත් understand ගනිව්..... URL

### 3.500. `හිරගෙවල්` -> `prisons`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER හිරගෙවල් කීයක් කියල හදන්නද ඇල්ලුවනම්
  - [NOT] after:  @USER  @USER prisons how many කියල හදන්නද ඇල්ලුවනම්

### 3.501. `කන්ද` -> `mountain`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ගොන් බූරු තකතීරු ගොබ්බ හැත්ත. අජූත පජාත කුජීත අවලාත අවලස්සන නිකෘෂ්ඨ අධර්මිෂ්ඨ පාපචර කාලකණ්ණියා මෝඩ ගඳ ගහන කුණු කන්ද . කුණු ගොඩේ ලගින ඌරු රංචුව . බැටළු කොටුව. අලියාගේ තට්ටම . En TPWK @USER  · 2 Jan  @USER If Harry had a problem with being sexualised he wouldnt wear the outfits he does on tour.  This is a fake tweet.  He sexualises himself it sells his music. Such is life.
  - [OFF] after:  ගොන් බූරු තකතීරු ගොබ්බ හැත්ත. අජූත පජාත කුජීත අවලාත අවලස්සන නිකෘෂ්ඨ අධර්මිෂ්ඨ පාපචර කාලකණ්ණියා මෝඩ ගඳ ගහන කුණු mountain . කුණු ගොඩේ ලගින pig රංචුව . බැටළු කොටුව. අලියාගේ තට්ටම . En TPWK @USER  · 2 Jan  @USER If Harry had a problem with being sexualised he wouldnt wear the outfits he does on tour.  This is a fake tweet.  He sexualises himself it sells his music. Such is life.

### 3.502. `රුපියල්` -> `rupees`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කෙසෙල් ගෙඩියක් රුපියල් තිහයි
  - [NOT] after:  @USER කෙසෙල් ගෙඩියක් rupees thirty

### 3.503. `රතිඤ්ඤා` -> `crackers`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මේ වේස පකයො රැස්වීම් තියන්න රතිඤ්ඤා පත්තු කරනවා.සත්තු පණ බයෙ දුවනවා.නද්දකින් ගොන් පක්කු.!
  - [OFF] after:  මේ වේස පකයො රැස්වීම් තියන්න crackers පත්තු කරනවා.animals පණ බයෙ දුවනවා.නද්දකින් ගොන් පක්කු.!

### 3.504. `කුහක` -> `fake`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ,  @USER  @USER චික් බූරු ගොන් කාලකණ්ණි බේබදු කුහක නොසන්ඩාල අපත අමනයා
  - [OFF] after:  @USER ,  @USER  @USER චික් බූරු ගොන් කාලකණ්ණි බේබදු fake නොසන්ඩාල අපත idiot

### 3.505. `උල්` -> `sharp`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER කකුල් දෙක මැදින් බිජ්ජ උල් වෙලා වගෙ
  - [OFF] after:  @USER legs දෙක මැදින් බිජ්ජ sharp වෙලා වගෙ

### 3.506. `ලීසා` -> `Lisa`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පයිය හඩයි ලීසා නිහඩයි
  - [OFF] after:  @USER පයිය හඩයි Lisa silent

### 3.507. `යලි` -> `again`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: නන්නාඳුනන ලෙසේ මග තොට යලි හමුවෙලා, මහ මෙර හිසින් දරාගෙන අපි යමු දුරස් වෙලා... #SomethingsJustNeverMeantToHappen
  - [NOT] after:  නන්නාඳුනන ලෙසේ මග තොට again හමුවෙලා, මහ මෙර හිසින් දරාගෙන අපි let's go දුරස් වෙලා... #SomethingsJustNeverMeantToHappen

### 3.508. `කොල්ල` -> `boy`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  කොල්ල වගේද බල්ලා කියල හිතල
  - [NOT] after:  @USER  boy වගේද dog කියල හිතල

### 3.509. `ඉඳං` -> `from`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මිතුරෙක් - බලහං කඩවත ඉඳං මාතරට එනකං එක දංසලක් නෑනේ... 2මිතුරා - හයිවේ එකේ කොහෙ දන්සල්ද? පකෝ... #සිරාසිද්ධි
  - [OFF] after:  මිතුරෙක් - බලහං කඩවත from මාතරට එනකං එක දංසලක් නෑනේ... 2මිතුරා - හයිවේ එකේ where දන්සල්ද? පකෝ... #සිරාසිද්ධි

### 3.510. `අන්` -> `other`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: නුහුරු සෙනෙහසේ.. හුරු පුරුදු තනිකම හොයන... එකම එක අන් ගොනා... මන්   ඕයි.... :/
  - [NOT] after:  නුහුරු සෙනෙහසේ.. හුරු habit තනිකම හොයන... එකම එක other ගොනා... මන්   ඕයි.... :/

### 3.511. `අමුතු` -> `strange`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හුජ්ජ බරයි වැස්සයි අතරෙ  අමුතු පෙමක් ඇත මගෙ මිතුරෙ
  - [OFF] after:  හුජ්ජ heavy වැස්සයි අතරෙ  strange පෙමක් ඇත මගෙ මිතුරෙ

### 3.512. `උබෙ` -> `your`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අවජාතක උබෙ ගැනිගෙ ලෙඩ කිම්බට පන්න පන්න හුකපි උබෙ අප්පට ඔමද කතා කරන්නෙ කැරි වේසිගෙ පුතෝ ඇදලඅරන් උබෙ හුත්ත අස්සෙ ඔබලා මරන්නෙ ලෙඩ බැල්ලිගෙ එකාව
  - [OFF] after:  අවජාතක your ගැනිගෙ ලෙඩ කිම්බට පන්න පන්න හුකපි your අප්පට ඔමද talk කරන්නෙ කැරි වේසිගෙ පුතෝ ඇදලඅරන් your හුත්ත අස්සෙ ඔබලා මරන්නෙ ලෙඩ බැල්ලිගෙ එකාව

### 3.513. `දැවිල්ල` -> `burning`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER පුක දැවිල්ල ඇති අච්චාරු ගෑවිලා ම්ම්ම්
  - [OFF] after:  @USER  @USER පුක burning ඇති pickle ගෑවිලා ම්ම්ම්

### 3.514. `පුතී` -> `son`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පුතී අයින් වීලා පාරේ පලයන්
  - [NOT] after:  son අයින් වීලා road එකේ පලයන්

### 3.515. `සුදුසු` -> `suitable`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER විපක්ෂයට යනකල්ද ඉන්නෙ හෙළි කරන්න? මීට වඩා සුදුසු කාලයක් තියේද?
  - [NOT] after:  @USER විපක්ෂයට යනකල්ද ඉන්නෙ reveal කරන්න? මීට වඩා suitable කාලයක් තියේද?

### 3.516. `මඩ` -> `mud`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අම්මගේ රෙද්ද තමයි..... රටම පාවා දුන්න අවජාතකයාගේ මඩ හාේදන පාලම් කොක්කු ඉන්නවනේ.... URL
  - [OFF] after:  අම්මගේ රෙද්ද තමයි..... රටම පාවා දුන්න අවජාතකයාගේ mud හාේදන bridge කොක්කු ඉන්නවනේ.... URL

### 3.517. `මෙවන්` -> `such`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තු හ් නොදකින් මෙවන් දේවදත්තයො මතුවටවත්මේ හෙල දිවයිනෙ බිහි නොවෙවා
  - [OFF] after:  @USER  @USER තු හ් නොදකින් such දේවදත්තයො මතුවටවත්මේ හෙල දිවයිනෙ born නොවෙවා

### 3.518. `එරෙහිවත්` -> `against`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  සංශෝධනයට එරෙහිවත් හිටියෙ මේ අයම නේද...විජේදාස රාජපක්ෂ අඩුයි වගේ..!
  - [NOT] after:  @USER  සංශෝධනයට against හිටියෙ මේ අයම නේද...විජේදාස රාජපක්ෂ low වගේ..!

### 3.519. `බෙශියර්` -> `brassiere`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER වද කොත්තු, වද බෙශියර් මතක් උනාද?
  - [NOT] after:  @USER trouble කොත්තු, trouble brassiere මතක් උනාද?

### 3.520. `ගමන` -> `trip`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: උඹට මඩගහන්න.. උඹේ අඩුපාඩු දකින්නම ඔනේ තරම් කට්ටිය ඉදිවී එත් උඹේ ගමන උඹට ඔනේ විදිහට පලයන් උන්ට ඔනේ ෆුකක් කියන්න... URL
  - [OFF] after:  උඹට මඩගහන්න.. උඹේ අඩුපාඩු දකින්නම ඔනේ තරම් කට්ටිය ඉදිවී but උඹේ trip උඹට ඔනේ විදිහට පලයන් උන්ට ඔනේ ෆුකක් කියන්න... URL

### 3.521. `අපී` -> `we`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පොන්න පකෙක්.  අපී මෙහේ සීතලට අදින ඇදුම් .ගිනි ගහන රස්නේ මේ මීහරකා යටට ඇදලා බිජ්ජ halfboill වෙලා ඇතී
  - [OFF] after:  @USER පොන්න පකෙක්.  we මෙහේ සීතලට අදින ඇදුම් .ගිනි ගහන රස්නේ මේ මීහරකා under ඇදලා බිජ්ජ halfboill වෙලා ඇතී

### 3.522. `ශිෂ්ඨ` -> `civilized`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  ඔබ කියන ‘අවජාතක‘ බව ඔබේ හැදින්වීමෙන්ම පේනවා! ඉස්සල්ලා ශිෂ්ඨ වෙන්න! පසුව සංවාද කරමු  @USER  #lka
  - [OFF] after:  @USER @USER  ඔබ කියන ‘අවජාතක‘ බව ඔබේ හැදින්වීමෙන්ම පේනවා! ඉස්සල්ලා civilized වෙන්න! after සංවාද කරමු  @USER  #lka

### 3.523. `මීමා` -> `buffalo`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER තෝ පල පැණි සෙවෙල චමත් මීමා
  - [OFF] after:  @USER  @USER තෝ පල honey සෙවෙල චමත් buffalo

### 3.524. `අනුරාධපුරේ` -> `Anuradhapura`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අනුරාධපුරේ ට පෑව්වත් අප්පිරියයි වැස්සත් අප්පිරියයි . වැස්ස නං ඉතින් යලට එකයි මහට එකයි නේ...  #mosthatedcity #කරුම
  - [NOT] after:  Anuradhapura ට පෑව්වත් අප්පිරියයි වැස්සත් අප්පිරියයි . rain නං ඉතින් යලට එකයි මහට එකයි නේ...  #mosthatedcity #කරුම

### 3.525. `එහෙනන්` -> `then`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER Bro  @USER  , එහෙනන් ලබ්බටද යකෝ අවුරුදු 5ක් ඕව විසදුවේ නැත්තේ. -_-
  - [OFF] after:  @USER Bro  @USER  , then ලබ්බටද යකෝ years 5ක් ඕව විසදුවේ නැත්තේ. -_-

### 3.526. `හිත්` -> `heart`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හිත් පිත් නැති කාලකන්නි ටිකක් නිසා මුලු ටුවිටරයම එපා විය   මනුස්සකමක් නැති කාලකන්නි ,සක්කිලි , නොදකින් මෙහෙව් උන්
  - [OFF] after:  heart පිත් නැති කාලකන්නි ටිකක් නිසා whole ටුවිටරයම එපා විය   මනුස්සකමක් නැති කාලකන්නි ,සක්කිලි , නොදකින් මෙහෙව් උන්

### 3.527. `නිදාගත්තෙ` -> `slept`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER තෝ තාම නිදාගත්තෙ නැද්ද යකෝ
  - [NOT] after:  @USER තෝ still slept නැද්ද යකෝ

### 3.528. `උසැති` -> `tall`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: #පන්නරය යකෝ  Dulith Kasun (DK) @USER  · 4 Jul 2019 සිහින් උසැති උපැස් පළදින්නා....
  - [NOT] after:  #පන්නරය යකෝ  Dulith Kasun (DK) @USER  · 4 Jul 2019 සිහින් tall spectacles පළදින්නා....

### 3.529. `අක්කෙ` -> `sister`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 4 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: අක්කෙ අක්කෙ අක්කෙ අක්කෙ අක්කියෝඕඕඕඕඕ.... මොකද ඕයි කෑගහන්නෙ? අනේ ටවල් එක එලියෙ තියල ඇවිත්නෙ ගෙනත් දෙනවකෝ තමුසෙ නම් මහ... ඉන්නව පොඩ්ඩක්
  - [NOT] after:  sister sister sister sister අක්කියෝඕඕඕඕඕ.... මොකද ඕයි කෑගහන්නෙ? අනේ ටවල් එක outside තියල ඇවිත්නෙ ගෙනත් දෙනවකෝ තමුසෙ නම් මහ... ඉන්නව පොඩ්ඩක්

### 3.530. `පූසයි` -> `cat`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER    මම නම් එක පූසයි නේ තෝ පූසො ගොඩක් තියාගෙන ඉන්නවා නේ
  - [NOT] after:  @USER  @USER    මම නම් එක cat නේ තෝ cats ගොඩක් තියාගෙන ඉන්නවා නේ

### 3.531. `ළග` -> `near`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: පොන්නයෝ 3 දෙනාගේ පොන්න ජවනිකාව. චාමරට නෙවෙයි ළග පහතක හිටියනම් තොපි ගැන බලා ගන්න තිබ්බා ගොබ්බයෝ. තොපි පිරිමි... URL
  - [OFF] after:  පොන්නයෝ 3 දෙනාගේ පොන්න ජවනිකාව. චාමරට නෙවෙයි near පහතක හිටියනම් තොපි ගැන බලා ගන්න තිබ්බා ගොබ්බයෝ. තොපි men... URL

### 3.532. `අම්මලා` -> `mothers`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER උන්ගේ අම්මලා තාත්තලා මෝඩ නං අපි මෙහේ ඉතුරු වෙද්දී උන්ව එහෙ යවයිද
  - [NOT] after:  @USER උන්ගේ mothers තාත්තලා මෝඩ නං අපි මෙහේ remaining වෙද්දී උන්ව එහෙ යවයිද

### 3.533. `තනි` -> `single`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: තනි වුනු ඇයයි . අසරණ ඔබයි මට සාප කර යාවිදෝ  #sajje
  - [NOT] after:  single වුනු ඇයයි . helpless ඔබයි මට සාප කර යාවිදෝ  #sajje

### 3.534. `දැරිවි` -> `girl`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER උඹ දන්න රෙද්ද. ඒ රත්තරං දැරිවි එහෙම නෑ!  @USER  @USER  @USER  @USER  @USER @USER
  - [NOT] after:  @USER උඹ know රෙද්ද. ඒ රත්තරං girl එහෙම නෑ!  @USER  @USER  @USER  @USER  @USER @USER

### 3.535. `කොයිකවුරුත්` -> `everyone`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඔව් උඹ ගොනා කියල කොයිකවුරුත් දන්නව
  - [OFF] after:  @USER ඔව් උඹ ගොනා කියල everyone know

### 3.536. `ඇද` -> `bed`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: යන්න හදද්දි ඇද රෙද්ද මිරිකා ගන්නවා වගේ එව්වා තමා අපි නම් අහලා තියෙන්නේ LuckyGirlමලී @USER  · 24 Oct 2019 යන්න හදද්දි වහිනවා..
  - [NOT] after:  යන්න හදද්දි bed රෙද්ද මිරිකා ගන්නවා වගේ එව්වා තමා අපි නම් අහලා තියෙන්නේ LuckyGirlමලී @USER  · 24 Oct 2019 යන්න හදද්දි raining..

### 3.537. `මැරුණු` -> `dead`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: රිලාජ් පව් නේ. මිනිහ මැරුණු ගෑණි වගේ අඬන්නේ
  - [NOT] after:  රිලාජ් පව් නේ. guy dead ගෑණි වගේ අඬන්නේ

### 3.538. `ඔහුගේ` -> `his`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මක්නිසාද නපුරු ක්‍රියා කරන්නෝ සිඳිනු ලබන්නනෝය.   නුමුත් ස්වාමීන් කෙරෙහි බලා සිටින්නෝ දේශය උරුමකරගන්නෝය.   මද කලකින් දුෂ්ටයා නැතිවන්නේය. එසේය, නුඹ ඔහුගේ ස්ථානය පරීක්ෂාකර බලන්නෙහිය,  ඔහු සම්බනොවන්නේය.  ගීතාවලිය 37:9-10
  - [NOT] after:  @USER මක්නිසාද නපුරු ක්‍රියා කරන්නෝ සිඳිනු ලබන්නනෝය.   නුමුත් ස්වාමීන් කෙරෙහි බලා සිටින්නෝ දේශය උරුමකරගන්නෝය.   මද කලකින් දුෂ්ටයා නැතිවන්නේය. එසේය, you his ස්ථානය පරීක්ෂාකර බලන්නෙහිය,  ඔහු සම්බනොවන්නේය.  ගීතාවලිය 37:9-10

### 3.539. `පහක්` -> `five`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ඒකි :- "මගේ facebook account එකට අමතරව තව fake accounts පහක් හදාගන්න කිව්වා. මට තියෙන්නේ අයියේ, ස'ගේ page එකේ post වලට "ජය නියතයි", "ඌවේ පැතුම ඔබයි", "ඔබයි නියතව ජය ගන්නවා" වගේ comments දාලා post ටිකත් එයාලගේම group එකේ share කරන්න විතරයි තියෙන්නේ...  (2/4)
  - [NOT] after:  ඒකි :- "මගේ facebook account එකට අමතරව තව fake accounts five හදාගන්න කිව්වා. මට තියෙන්නේ අයියේ, ස'ගේ page එකේ post වලට "ජය නියතයි", "ඌවේ wish ඔබයි", "ඔබයි නියතව ජය ගන්නවා" වගේ comments දාලා post ටිකත් එයාලගේම group එකේ share කරන්න විතරයි තියෙන්නේ...  (2/4)

### 3.540. `අවසානෙ` -> `finally`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හරකා මොකා උනත් අවසානෙ මසට යාලු
  - [NOT] after:  @USER හරකා මොකා උනත් finally meat යාලු

### 3.541. `තරුණ` -> `young`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER නොදැකින් කාලකන්නි දෙන්නා මුංට සැර් නෙවෙ කියන්න ඕනැ. අවජාතක බල්ලෝ. තරුණ පරමුරම මුලා කරපු අවජාතක බල්ලෝ .
  - [OFF] after:  @USER නොදැකින් කාලකන්නි දෙන්නා මුංට සැර් නෙවෙ say ඕනැ. අවජාතක බල්ලෝ. young පරමුරම මුලා කරපු අවජාතක බල්ලෝ .

### 3.542. `කරත්තකාරයා` -> `cart man`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓  පුල්ලි ගොනා පුරුදුකාරයා මම ජෙමා කරත්තකාරයා  අහල තියෙනවනේ  මේකෙ මේ ජෙමා... URL
  - [NOT] after:  ░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓░▒▓  spotted ගොනා පුරුදුකාරයා මම ජෙමා cart man  අහල තියෙනවනේ  මේකෙ මේ ජෙමා... URL

### 3.543. `මාරයි` -> `awesome`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ශා ඔයාලගේ බල්ලා නම් මාරයි ආආආ
  - [NOT] after:  @USER ශා your බල්ලා නම් awesome ආආආ

### 3.544. `උදවිය` -> `people`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මැතිවරණයක් පවත්තන සෑම අවස්ථාවකම තාජිඩීන් ගොඩ දාපු උදවිය නාහින් අඩනවා සන්දීප්  සම්පත් විකුනන් දේසපාලන පලි ගන්නවලු.. මේවට කොහොම හිනාවෙන්නද මන්දා..
  - [NOT] after:  @USER මැතිවරණයක් පවත්තන every අවස්ථාවකම තාජිඩීන් ගොඩ දාපු people නාහින් අඩනවා සන්දීප්  සම්පත් විකුනන් දේසපාලන පලි ගන්නවලු.. මේවට කොහොම හිනාවෙන්නද මන්දා..

### 3.545. `විශාල` -> `big`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පයිය බිහි වීම.  පුරාණ රාවණ සෙල් ලිපි වලට අනුව රාවණ රජුගේ ලිංගය විශාල යන්ත්‍රයක් වැනිය.  පස් යොදුනක් දිග+ඉන්නක් වැනි+යන්ත්‍රය = පයිය  මේ සෙල්ලිපි අද්‍යනය කිරීමෙන් පසු අපට හැගී යන්නේ රාවණා රජුගේ ලිංගය අති විශාල වූවා පමණක් නොව එය සීතා වැනි ස්ත්‍රියකට කිසි සේත් දරා ගත නොහැකි බවයි.
  - [NOT] after:  පයිය බිහි වීම.  පුරාණ රාවණ සෙල් ලිපි වලට අනුව රාවණ රජුගේ ලිංගය big යන්ත්‍රයක් වැනිය.  පස් යොදුනක් දිග+ඉන්නක් වැනි+යන්ත්‍රය = පයිය  මේ සෙල්ලිපි අද්‍යනය කිරීමෙන් පසු අපට හැගී යන්නේ රාවණා රජුගේ ලිංගය අති big වූවා පමණක් නොව it සීතා වැනි ස්ත්‍රියකට කිසි සේත් දරා ගත නොහැකි බවයි.

### 3.546. `සජියට` -> `Sajee`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  @USER අඩො ගෙම්බා එක්ක සජියට බයින්න එපා හරිය
  - [OFF] after:  @USER  @USER අඩො frog එක්ක Sajee බයින්න එපා හරිය

### 3.547. `ඒකිගෙ` -> `her`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER උඹට තේරුනේ නැහැ. ඒකි කියන්න ඇත්‍තෙ photo එක ඒකිගෙ කියලා.
  - [NOT] after:  @USER  @USER උඹට තේරුනේ නැහැ. ඒකි say ඇත්‍තෙ photo එක her කියලා.

### 3.548. `නිකම්` -> `just`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: දවල්ටත් නිකම් මැරිච්ච වගේ නින්ද ගියානෙ බොල.මහ මුස්පේත්තු දවසක්..
  - [NOT] after:  දවල්ටත් just මැරිච්ච වගේ sleep ගියානෙ බොල.මහ මුස්පේත්තු දවසක්..

### 3.549. `උණුසුම්` -> `hot`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER  අද දිනෙන් ඇරඹෙන කාලකණ්ණි දිවියට උණුසුම් සුභ පැතුම්
  - [OFF] after:  @USER  අද දිනෙන් ඇරඹෙන කාලකණ්ණි දිවියට hot සුභ wishes

### 3.550. `මුල්` -> `first`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඔබ දුටු මුල් දා එදා. දැක්කේ අරකම තම. එය දැකලා, පක නැගලා. දුටුවා මුහුණත් එදා.
  - [OFF] after:  @USER ඔබ දුටු first දා එදා. දැක්කේ අරකම තම. it දැකලා, පක නැගලා. දුටුවා මුහුණත් එදා.

### 3.551. `කසාද` -> `marriage`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: යකෝ කසාද සහතිකේ විතරයි නැත්තේ, කාසාදෙන් පස්සේ  වෙන්න ඕන දේවල් උඹ දැන්ම කරලා ඉවරනේ
  - [NOT] after:  යකෝ marriage සහතිකේ විතරයි නැත්තේ, කාසාදෙන් පස්සේ  වෙන්න ඕන things උඹ දැන්ම කරලා ඉවරනේ

### 3.552. `ලොකුයි` -> `big`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඒකි බැන්ද නම් උඹව දරුකමට ගන්න තරම් උඹට වඩා ලොකුයි.
  - [NOT] after:  @USER ඒකි married නම් උඹව දරුකමට ගන්න තරම් උඹට වඩා big.

### 3.553. `කැට` -> `blocks`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මුලින්ම බලද්දි දැක්කෙ ගඩොල් කැට ටිකක් වගේපස්සෙ තමා #Caption එක දැක්කෙ
  - [NOT] after:  @USER මුලින්ම බලද්දි දැක්කෙ brick blocks ටිකක් වගේපස්සෙ තමා #Caption එක දැක්කෙ

### 3.554. `ඒතරං` -> `that much`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER නිල මැස්සො වගේ මුන්. ඒතරං අප්පිරියයි දැං..
  - [OFF] after:  @USER නිල flies වගේ මුන්. that much අප්පිරියයි දැං..

### 3.555. `පුත්‍රයා` -> `son`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: බලු සිරිසේනගේ අවජාතක පුත්‍රයා ගේ සවාරි යෑම් URL
  - [OFF] after:  බලු සිරිසේනගේ අවජාතක son ගේ ride යෑම් URL

### 3.556. `අරාබි` -> `arabi`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ඔව් ඇත්තටම කවුරැත් ඇහුවෙ නෑනෙ අරාබි පක්කො මෙහෙ ගෙන්නගෙන මොනවද කරන්න හැදුවෙ කියලා
  - [OFF] after:  @USER ඔව් ඇත්තටම කවුරැත් asked නෑනෙ arabi පක්කො මෙහෙ ගෙන්නගෙන මොනවද කරන්න හැදුවෙ කියලා

### 3.557. `කිලිටි` -> `dirty`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER ආයෙ බැල්ලි කියන්න එපා  අපේ හිත්මයි කිලිටි වෙන්නේ
  - [NOT] after:  @USER  @USER again බැල්ලි කියන්න එපා  අපේ හිත්මයි dirty වෙන්නේ

### 3.558. `විනාශ` -> `destroy`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER  @USER  @USER  @USER  @USER  @USER   කවුද මේ හූල් කියන්නේ ... දේශදොහියෙකි URL අප මාතෘ භුමිය විනාශ කිරිමට මාන බලන LTTE මහා මොලකරැය
  - [NOT] after:  @USER  @USER  @USER  @USER  @USER  @USER  @USER   කවුද මේ හූල් කියන්නේ ... දේශදොහියෙකි URL අප mother භුමිය destroy කිරිමට මාන බලන LTTE මහා මොලකරැය

### 3.559. `තැනත්` -> `place`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ,  @USER  @USER අද මන් ගත්ත තැනත් ඊයේ හවස ඇවිත් තියෙන්නේ කොට්ට පනහයී මන් යද්දී තිබ්බේ හයයී, සිමෙන්තී වැඩි දවසක් තියා ගන්නත් අමාරු නිසා හන්ගනවා කියන්න බෑ
  - [NOT] after:  @USER ,  @USER  @USER අද මන් ගත්ත place yesterday හවස ඇවිත් තියෙන්නේ කොට්ට පනහයී මන් යද්දී තිබ්බේ හයයී, සිමෙන්තී වැඩි දවසක් තියා ගන්නත් අමාරු නිසා හන්ගනවා කියන්න බෑ

### 3.560. `එලුවා` -> `goat`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER හරකා එලුවා කුකුලා ඔක්කොම එහෙම තමා දැන්
  - [NOT] after:  @USER හරකා goat chicken ඔක්කොම එහෙම තමා දැන්

### 3.561. `ඉර` -> `sun`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අපටත් දවසක ඉර පායනවා...  මල හුත්තයි... අවුරුදු  8කට පස්සේ  මේක  මන් කරේ  කියලා  මෙන්න  එකෙක්  කියලා... උඹ  කවුරු... URL
  - [OFF] after:  අපටත් දවසක sun පායනවා...  මල හුත්තයි... years  8කට පස්සේ  මේක  මන් කරේ  කියලා  මෙන්න  එකෙක්  කියලා... උඹ  කවුරු... URL

### 3.562. `මුහුණු` -> `masks`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER වෙස් මුහුණු බැදන් අාවට නැ අපි රැවටෙන්නෙ
  - [NOT] after:  @USER mask masks බැදන් අාවට නැ අපි රැවටෙන්නෙ

### 3.563. `මල්ලී` -> `brother`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ඇයි යකෝ මං විතරක් ඇහැරලා ඉද්දී අනිත් උං බුදිනේ.. @USER මල්ලී උඹ ඇහැරලාද?
  - [NOT] after:  ඇයි යකෝ මං විතරක් ඇහැරලා ඉද්දී other උං බුදිනේ.. @USER brother උඹ ඇහැරලාද?

### 3.564. `අැයි` -> `why`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අපේ බලශක්ති සුරක්ෂිතතාවය වෙනත් රටකට බාර දෙන්නේ අැයි?ඒය අප විසින්ම සුරක්ෂිත කළ යුතු නොවන්නේද?
  - [NOT] after:  @USER අපේ බලශක්ති සුරක්ෂිතතාවය other රටකට බාර දෙන්නේ why?ඒය අප විසින්ම සුරක්ෂිත කළ යුතු නොවන්නේද?

### 3.565. `අතරමං` -> `lost`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අතරමං වෙලාද මහත්තයො ?
  - [NOT] after:  @USER lost වෙලාද sir ?

### 3.566. `කටවල්` -> `mouths`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  යහපාලන මල්ලිලගේ කටවල්, පු*වල් වී ඇති බැවින් මොකුත් කතා නැත
  - [OFF] after:  @USER @USER  good governance මල්ලිලගේ mouths, පු*වල් වී ඇති බැවින් මොකුත් කතා නැත

### 3.567. `තිත්ත` -> `bitter`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔන්න ඔය තිත්ත ඇත්ත අපේ ගොන් වහන්සෙලට තේරෙන්නේ නෑනේ
  - [NOT] after:  @USER ඔන්න ඔය bitter ඇත්ත අපේ ගොන් වහන්සෙලට understand නෑනේ

### 3.568. `මිනිස්සුන්ව` -> `people`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මිනිස්සුන්ව තේරුම් ගන්නවා කියනව එක එක්සැම් කරනවට වඩා අමාරු වැඩක්..
  - [NOT] after:  people තේරුම් ගන්නවා කියනව එක එක්සැම් කරනවට වඩා අමාරු work..

### 3.569. `වර්ග` -> `types`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER @USER  මට අනුව ටුයිටරය වර්ග දෙකයි අෙප හාමුදුරුවනේ...එකක් පුක දෙන අය අනික් අය පුක නොදෙන අය..
  - [OFF] after:  @USER @USER  මට අනුව ටුයිටරය types two අෙප හාමුදුරුවනේ...එකක් පුක දෙන අය අනික් අය පුක නොදෙන අය..

### 3.570. `ප්‍රාර්ථනා` -> `wish`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER අනිත් අයටත් ඉක්මන් සුවය ප්‍රාර්ථනා කරනවා......
  - [NOT] after:  @USER other අයටත් ඉක්මන් සුවය wish කරනවා......

### 3.571. `රසල්` -> `Russell`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER බොරු දාන්න එපා ඕයි... රසල් ආනල්ඩ් දාලා තියෙනවා මුරලිට එහෙම මුකුත් අසනීපයක් නෑ කියලා
  - [NOT] after:  @USER lies දාන්න එපා ඕයි... Russell ආනල්ඩ් දාලා තියෙනවා මුරලිට එහෙම මුකුත් අසනීපයක් නෑ කියලා

### 3.572. `හොදායි` -> `good`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: අලියා- අර්ජුන් මහේන්ද්‍ර හොදායි අත- කිලී මහේන්ද්‍ර හොදායි පොහොට්ටුව-පර්සි මහේන්ද්‍ර හොදායි මම? නොදකින් විතරක් — feeling disappointed
  - [OFF] after:  අලියා- Arjun මහේන්ද්‍ර good අත- කිලී මහේන්ද්‍ර good පොහොට්ටුව-පර්සි මහේන්ද්‍ර good මම? නොදකින් විතරක් — feeling disappointed

### 3.573. `පුතයි` -> `son`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පක ලොකු පුතයි කට ලොකු දුවයි තමයි ඉතිං
  - [OFF] after:  @USER පක ලොකු son කට ලොකු daughter තමයි ඉතිං

### 3.574. `කාලගුණයෙන්` -> `weather`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER " @USER : අයහපත් කාලගුණයෙන් මිය ගිය ගණන 8 ක් දක්වා ඉහළට #lka #WeatherSL URL
  - [NOT] after:  @USER " @USER : bad weather මිය ගිය ගණන 8 ක් දක්වා ඉහළට #lka #WeatherSL URL

### 3.575. `බිත්තර` -> `egg`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 3 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: කිකිලියොත් උන් දාන බිත්තර විකිනෙන්නේ 8 කියලා දැනගෙන ද බං චූටි බිත්තර දාන්නේ. පුක ඉරන්න ඕනේ ඕකූන්ගේ.කතා වෙලාද මංදා බිත්තර දාන්නේ.
  - [OFF] after:  කිකිලියොත් උන් දාන egg විකිනෙන්නේ 8 කියලා දැනගෙන ද බං චූටි egg දාන්නේ. පුක ඉරන්න ඕනේ ඕකූන්ගේ.talk වෙලාද මංදා egg දාන්නේ.

### 3.576. `හලාවත` -> `Chilaw`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER ටහුඩු.. ඊයේ හලාවත ආවා. ඒකයි ඕක දැක්කේ..
  - [NOT] after:  @USER  @USER ටහුඩු.. yesterday Chilaw ආවා. ඒකයි ඕක දැක්කේ..

### 3.577. `මයෙ` -> `my`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER මයෙ මෙතූ... නැගිටහන් බොල @USER
  - [NOT] after:  @USER my මෙතූ... get up බොල @USER

### 3.578. `පලතුරු` -> `fruits`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: පලතුරු කෑවම හම පැහැපත් වෙනවලු...  ආච්චිගේ රෙද්ද  මීට, #වදුරෝ
  - [NOT] after:  fruits කෑවම skin පැහැපත් වෙනවලු...  ආච්චිගේ රෙද්ද  මීට, #වදුරෝ

### 3.579. `දහම්` -> `dhamma`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඉද ඉද ළුක ‌ව‌ෙහෙර -විද විද දහම් මනහර -සිද බිද දුක් සසර- අහෝ ‌දෙව්දත් ‌නෙ‌ාදිටිි ‌මොක්පුර.
  - [NOT] after:  @USER ඉද ඉද ළුක ‌ව‌ෙහෙර -විද විද dhamma මනහර -සිද බිද sad සසර- අහෝ ‌දෙව්දත් ‌නෙ‌ාදිටිි ‌මොක්පුර.

### 3.580. `සිවු` -> `four`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔය ඉන්න සිවු දෙනා ද...
  - [NOT] after:  @USER ඔය ඉන්න four people ද...

### 3.581. `නාකියො` -> `old man`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ෆල ෆල නාකියො තෝ මට වඩා වයසයි  @USER
  - [OFF] after:  @USER ෆල ෆල old man තෝ මට වඩා old  @USER

### 3.582. `කෙල්ලෙක්ව` -> `girl`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: චැන්ඩ්ලර් මරු බඩුව ඈ  කොම හරි ආයෙ සූටි කෙල්ලෙක්ව අල්ලගෙන... #lastship
  - [NOT] after:  චැන්ඩ්ලර් මරු බඩුව ඈ  කොම හරි again සූටි girl අල්ලගෙන... #lastship

### 3.583. `කොටි` -> `tiger`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER අශ්ව පඩ බැටලු පඩ අලි පඩ ඔටු පඩ ඩොල්ෆින් පඩ වඳුරු පඩ බැල්ලි පඩ පූස් පඩ කොටි පඩ කුකුල් පඩ බලු බඩ ඌරු පඩ මී පඩ මී හරක් පඩ පඩ පඩ
  - [OFF] after:  @USER අශ්ව පඩ බැටලු පඩ අලි පඩ ඔටු පඩ ඩොල්ෆින් පඩ වඳුරු පඩ බැල්ලි පඩ පූස් පඩ tiger පඩ කුකුල් පඩ බලු බඩ pig පඩ මී පඩ මී හරක් පඩ පඩ පඩ

### 3.584. `ඉපදුන` -> `born`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ඔකුන්ට ඔවා කිවුවට වැඩක් නෑ බං.. කරුමෙට ඉපදුන එවුන්... කාලකණ්ණි
  - [OFF] after:  ඔකුන්ට ඔවා කිවුවට work නෑ බං.. කරුමෙට born එවුන්... කාලකණ්ණි

### 3.585. `පහන්` -> `lamps`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: ලා දළු බෝපත් සෙමින් සැලෙන සේ යශෝදරා දේවී වාවනු බැරි තෑන රහසේ හැඩුවා පෙර සංසාරේ ඈසුර මතක් වී  ලේන කුලේ සිට ආ ගිය මග තොට සිටියා නොසැලෙන පහන් ටැඹක් වී නිවන් දකින තුරු මේ සංසාරේ පසුපස ආවා සෙවනැල්ලක් වී #රතුමකරාFM #ගීwithචාපා
  - [NOT] after:  ලා දළු බෝපත් සෙමින් සැලෙන සේ යශෝදරා දේවී වාවනු බැරි තෑන රහසේ හැඩුවා පෙර සංසාරේ ඈසුර මතක් වී  ලේන කුලේ සිට ආ ගිය මග තොට සිටියා නොසැලෙන lamps ටැඹක් වී nirvana දකින තුරු මේ සංසාරේ පසුපස ආවා සෙවනැල්ලක් වී #රතුමකරාFM #ගීwithචාපා

### 3.586. `යාලුවේ` -> `friend`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER උඹ පොන්නයෙක් නොවී privacy අයින් කරපන් rt කරන්න මගේ රත්තරන් යාලුවේ
  - [OFF] after:  @USER උඹ පොන්නයෙක් නොවී privacy අයින් කරපන් rt කරන්න මගේ gold friend

### 3.587. `කලුබොවිල` -> `Kalubowila`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  @USER අඩො උඹ අද සීනී 500 ක් අරන් කලුබොවිල හිටිය ද ?
  - [NOT] after:  @USER  @USER අඩො උඹ අද sugar 500 ක් අරන් Kalubowila හිටිය ද ?

### 3.588. `ඇයිද` -> `why`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER විසිල් විතරයි බල්ටි නැති රාජිත පනින්නට ඉණිමං නැති රාජිත දත් නොගලවන දත්දොස්තර රාජිත ඇයිද බය බොරු නොවේ නම් රාජිත
  - [NOT] after:  @USER විසිල් විතරයි බල්ටි නැති රාජිත පනින්නට ඉණිමං නැති රාජිත දත් නොගලවන දත්දොස්තර රාජිත why බය lies නොවේ නම් රාජිත

### 3.589. `උස්` -> `loud`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER මිටි තැන් දැක පුප්පන්නේ උස් තැන් දැක හැකිලෙන්නේ.. #SLPolice
  - [OFF] after:  @USER short තැන් දැක පුප්පන්නේ loud තැන් දැක හැකිලෙන්නේ.. #SLPolice

### 3.590. `අඟලේ` -> `inch`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER පොන්න රජා..පොන්සියා.  පක බුරියා...කැරි තඩියා .  අඟලේ පකා...
  - [OFF] after:  @USER පොන්න king..පොන්සියා.  පක බුරියා...කැරි තඩියා .  inch පකා...

### 3.591. `යුද්දෙ` -> `war`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER  රාජපක්ලා යුද්දෙ ඉවර කරෙ නැත්තම් ලන්කාවත් ඔය වගෙ තමා
  - [NOT] after:  @USER  රාජපක්ලා war ඉවර කරෙ නැත්තම් Lanka ඔය වගෙ තමා

### 3.592. `බලාපොරොත්තුවද` -> `expectation`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER Many are guessing " කාගේ බලාපොරොත්තුවද ඉටුවන්නේ කියලා"
  - [NOT] after:  @USER Many are guessing " whose expectation ඉටුවන්නේ කියලා"

### 3.593. `අකුරණ` -> `Akurana`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: කාත්තන් කුඩි එපා පලයන් අකුරණ, අම්පාරේ කල්මුණේ , අක්කරෛපත්තු තොපිට සහජීවනය උගන්වයි !!!
  - [NOT] after:  කාත්තන් කුඩි එපා පලයන් Akurana, අම්පාරේ කල්මුණේ , අක්කරෛපත්තු තොපිට coexistence උගන්වයි !!!

### 3.594. `දිවියා` -> `leopard`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER කොටියා ද?? දිවියා ද??
  - [NOT] after:  @USER tiger ද?? leopard ද??

### 3.595. `ආච්චියා` -> `granny`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER ඔව් කරුම පස්සෙන් එනවා ආච්චියා..
  - [NOT] after:  @USER ඔව් කරුම behind එනවා granny..

### 3.596. `සිරිසේනගේ` -> `Sirisena's`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: සිරිසේනගේ අවජාතක සුනඛයන් ජාතිය ඇමතිම..... URL
  - [OFF] after:  Sirisena's අවජාතක dogs ජාතිය ඇමතිම..... URL

### 3.597. `යකඩ` -> `iron`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: හෙ යකඩ පයිය මගේ නුඹ ලඟ හඬා වැලපුනා මල්ලේ   #විනී
  - [OFF] after:  හෙ iron පයිය මගේ නුඹ near හඬා වැලපුනා මල්ලේ   #විනී

### 3.598. `ලියනගේ` -> `Liyanage`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: ලියනගේ පයිය කපනවයි කියන්නේ?බයේ බෑ බං :3
  - [OFF] after:  Liyanage පයිය කපනවයි කියන්නේ?scared බෑ බං :3

### 3.599. `දෙහි` -> `lime`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: මහින්දගේ රෙද්ද අස්සේ දෙහි ගෙඩි 3 යි හොඬල අලයයි URL
  - [OFF] after:  මහින්දගේ රෙද්ද inside lime ගෙඩි 3 යි හොඬල අලයයි URL

### 3.600. `මාළු` -> `fish`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 2 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: කුළු මිමාගේ ගැහැණු සතා කුළු බඩුව වේ .. මාළුවාගේ ගැහැණු සතා මාළු කැල්ල වන අතර හාවාගේ ගැහැණු සතා හා හා ලදේ වේ ..... URL
  - [NOT] after:  කුළු මිමාගේ women සතා කුළු බඩුව වේ .. මාළුවාගේ women සතා fish කැල්ල වන අතර හාවාගේ women සතා හා හා ලදේ වේ ..... URL

### 3.601. `හයක්` -> `six`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: බෑ කියලා දැනගෙනත් ඇයි තොපි එල්ලෙන්නේ  වහක් උන හැටි මතක නැතුව ඇයි රගදෙන්නේ පහක් හයක් වට කරන් ඉන්න තොපි දැනගන්නේ... URL
  - [OFF] after:  බෑ කියලා දැනගෙනත් ඇයි තොපි එල්ලෙන්නේ  වහක් උන හැටි මතක නැතුව ඇයි රගදෙන්නේ පහක් six round කරන් ඉන්න තොපි දැනගන්නේ... URL

### 3.602. `සීතල` -> `cold`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: වැස්ස සීතල  මතක  උඹ.. #witch
  - [NOT] after:  rain cold  මතක  උඹ.. #witch

### 3.603. `කපුටා` -> `crow`
- impact: 1 posts (0 light, 1 heavy), 1 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [OFF] before: @USER ගොනා හරකා කැරපොත්තා හිකනලා බස්සා ඌරු මීයා ඌරා වල් ඌරා ගෙම්බා තලගොයා හැකරැල්ලා කපුටා මයිනා
  - [OFF] after:  @USER ගොනා හරකා cockroach හිකනලා බස්සා ඌරු මීයා ඌරා වල් ඌරා ගෙම්බා තලගොයා හැකරැල්ලා crow මයිනා

### 3.604. `දහ` -> `ten`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER @USER බල්ලෙක් හදලම නෑ වගේ නේද? මන් හිතන්නේ මේ මගේ දහ වෙනි නැත්නම් එකොලොස් වෙනි බල්ලා පොඩිකාලේ ඉඳල හදපු.
  - [NOT] after:  @USER @USER බල්ලෙක් හදලම නෑ වගේ නේද? මන් හිතන්නේ මේ මගේ ten th නැත්නම් එකොලොස් th බල්ලා පොඩිකාලේ ඉඳල හදපු.

### 3.605. `ඉතාම` -> `very`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: මතුපිටින් මෝඩ වැඩක් වගේ පෙනෙන සමහර දේවල් ඇතුලාන්තයෙන් අපිට ඉතාම ප්‍රයෝජනයක් ගෙනල්ලා දෙන ක්‍රියාවක් වෙන්න පුළුවන්.  ඒක නිසා කවුරු හිනා උනත්, මෝඩ වැඩක් කියලා කිව්වත්, ඒ කරන දෙයින් හොඳක් වෙනවා නම් ඒ ගැන විතරක් හිතන්න.
  - [NOT] after:  මතුපිටින් මෝඩ වැඩක් වගේ පෙනෙන සමහර දේවල් ඇතුලාන්තයෙන් අපිට very ප්‍රයෝජනයක් ගෙනල්ලා දෙන ක්‍රියාවක් වෙන්න පුළුවන්.  ඒක නිසා කවුරු laugh උනත්, මෝඩ වැඩක් කියලා කිව්වත්, ඒ කරන දෙයින් හොඳක් වෙනවා නම් ඒ ගැන විතරක් හිතන්න.

### 3.606. `කොළොන්නාව` -> `Kolonnawa`
- impact: 1 posts (0 light, 1 heavy), 0 of them labelled OFF, 1 total occurrences
- source: llm, codemix_plausible: False
  - [NOT] before: @USER නෑ නෑ කොළොන්නාව නෙවෙයි.. කිරිබත්ගොඩ
  - [NOT] after:  @USER නෑ නෑ Kolonnawa නෙවෙයි.. Kiribathgoda

## FLAGGED FOR REVIEW — likely mis-tagged, recommend KEEP

These matched the tier-2 bare-verb test but are Sinhala-script spellings of the English word itself (tagged `source=llm` instead of `loanword`). Switching them back to Latin is the most natural move available in the post. Held out of tier 2's removal set; listed here so the classification choice is visible, not silent.

- `බයිට්` -> `bite` (12 firings, source=llm)
- `ශෝ` -> `show` (4 firings, source=llm)
- `ලුක්` -> `look` (4 firings, source=llm)
- `ඕපන්` -> `open` (2 firings, source=llm)
- `ස්ටාර්ට්` -> `start` (2 firings, source=llm)
- `කැච්` -> `catch` (2 firings, source=llm)
- `ශො` -> `show` (1 firings, source=llm)
- `ටේක්` -> `take` (1 firings, source=llm)
