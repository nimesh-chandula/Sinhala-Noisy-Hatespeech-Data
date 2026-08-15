# Misspelling confusion-set review

**Status: reviewed and approved as-is, 2026-08-15.** All 130 sets accepted
with no corrections — `data/lexicon/misspell_confusions.jsonl`
(sha256 `fff1e157...`) is the final, frozen artifact for Phase 4a. One
known cosmetic oddity (set #16 `ne` contains a malformed-encoding
duplicate-looking `නේ`, inherited from SOLD's raw text, freq=7) was
flagged during review and left in place as immaterial.

130 romanization-collision sets, impact-ordered by how many Sinhala word-tokens in SOLD contain >=1 member cluster (i.e. how much of the corpus this set could ever touch). Each set is a group of Sinhala grapheme clusters that a phonetic IME (type the roman spelling, get the Sinhala character) cannot distinguish between — see src/noisers/misspell.py and LOG.md's Phase 4a entry for why that's the misspelling mechanism modeled here.

For each set: reject the whole set (`reject_set`) if the confusion isn't something a real typist would actually produce, or list specific clusters to drop (`remove_members`) if only some members are implausible. Leave both blank to accept as-is. Record corrections in data/lexicon/misspell_review_corrections.jsonl (one JSON line per set: {"key": ..., "action": "reject_set"} or {"key": ..., "action": "remove_members", "remove": [...]}).

## 1. `na` (mixed) — න / නා / නැ / ණ / ණා
- impact: 30986 word-tokens in SOLD
- members by frequency: න (25409), නා (2733), නැ (2462), ණ (1185), ණා (142)
  - `නම්` -> `නාම්` (attested)
  - `කරන්න` -> `කරන්නා` (attested)
  - `ඉන්න` -> `ඉන්නා` (attested)

## 2. `n` (consonant_quality) — න් / ණ්
- impact: 29938 word-tokens in SOLD
- members by frequency: න් (30002), ණ් (499)
  - `කරන්න` -> `කරණ්න` (unattested)
  - `දැන්` -> `දැණ්` (unattested)
  - `ඉන්න` -> `ඉණ්න` (unattested)

## 3. `ka` (vowel_length) — ක / කා / කැ
- impact: 23397 word-tokens in SOLD
- members by frequency: ක (20360), කා (3001), කැ (811)
  - `එක` -> `එකා` (attested)
  - `කරන්න` -> `කාරන්න` (unattested)
  - `එකක්` -> `එකාක්` (unattested)

## 4. `wa` (vowel_length) — ව / වා / වැ
- impact: 23331 word-tokens in SOLD
- members by frequency: ව (17341), වා (4662), වැ (2093)
  - `වගේ` -> `වාගේ` (attested)
  - `වැඩ` -> `වඩ` (attested)
  - `නැතුව` -> `නැතුවා` (attested)

## 5. `ya` (vowel_length) — ය / යා / යැ
- impact: 20535 word-tokens in SOLD
- members by frequency: ය (17586), යා (3231), යැ (85)
  - `කියලා` -> `කියාලා` (attested)
  - `යකෝ` -> `යාකෝ` (attested)
  - `කියල` -> `කියාල` (attested)

## 6. `ma` (vowel_length) — ම / මා / මැ
- impact: 18594 word-tokens in SOLD
- members by frequency: ම (16290), මා (2516), මැ (886)
  - `මම` -> `මාම` (attested)
  - `මම` -> `මමා` (attested)
  - `මට` -> `මාට` (attested)

## 7. `la` (mixed) — ල / ලා / ළ / ලැ / ළා
- impact: 17885 word-tokens in SOLD
- members by frequency: ල (11106), ලා (6070), ළ (695), ලැ (291), ළා (59)
  - `කියලා` -> `කියල` (attested)
  - `කියල` -> `කියලා` (attested)
  - `වෙලා` -> `වෙල` (attested)

## 8. `da` (mixed) — ද / ඩ / දා / දැ / ඩා / ඩැ
- impact: 17160 word-tokens in SOLD
- members by frequency: ද (10242), ඩ (2750), දා (2180), දැ (1675), ඩා (569), ඩැ (13)
  - `දැන්` -> `දන්` (attested)
  - `රෙද්ද` -> `රෙද්ඩ` (unattested)
  - `වැඩ` -> `වැද` (attested)

## 9. `ra` (vowel_length) — ර / රා / රැ
- impact: 15949 word-tokens in SOLD
- members by frequency: ර (14639), රා (1186), රැ (455)
  - `කරන්න` -> `කරාන්න` (unattested)
  - `කරන` -> `කරාන` (attested)
  - `අර` -> `අරා` (attested)

## 10. `a` (consonant_quality) — අ / ඇ / ආ
- impact: 15388 word-tokens in SOLD
- members by frequency: අ (10648), ඇ (2871), ආ (1910)
  - `අපි` -> `ඇපි` (attested)
  - `අපේ` -> `ඇපේ` (attested)
  - `ඇති` -> `අති` (attested)

## 11. `ta` (vowel_length) — ට / ටා / ටැ
- impact: 15318 word-tokens in SOLD
- members by frequency: ට (15561), ටා (134), ටැ (43)
  - `මට` -> `මටා` (unattested)
  - `පට්ට` -> `පට්ටා` (attested)
  - `රට` -> `රටා` (attested)

## 12. `e` (consonant_quality) — එ / ඒ / ඈ / එ්
- impact: 11157 word-tokens in SOLD
- members by frequency: එ (8392), ඒ (2595), ඈ (136), එ් (43)
  - `එක` -> `ඒක` (attested)
  - `ඒ` -> `එ` (attested)
  - `එකක්` -> `ඒකක්` (attested)

## 13. `tha` (mixed) — ත / තා / තැ / ථා / ථ / ඨා / ඨ
- impact: 11125 word-tokens in SOLD
- members by frequency: ත (8779), තා (1893), තැ (338), ථා (150), ථ (74), ඨා (40), ඨ (28)
  - `තමයි` -> `තාමයි` (unattested)
  - `තමා` -> `තාමා` (attested)
  - `කතා` -> `කත` (attested)

## 14. `pa` (vowel_length) — ප / පා / පැ
- impact: 10069 word-tokens in SOLD
- members by frequency: ප (7003), පා (2367), පැ (784)
  - `එපා` -> `එප` (attested)
  - `පට්ට` -> `පාට්ට` (unattested)
  - `පලයන්` -> `පාලයන්` (attested)

## 15. `ha` (vowel_length) — හ / හැ / හා
- impact: 9932 word-tokens in SOLD
- members by frequency: හ (6945), හැ (2131), හා (899)
  - `හරි` -> `හැරි` (attested)
  - `හැත්ත` -> `හත්ත` (attested)
  - `මහ` -> `මහැ` (attested)

## 16. `ne` (mixed) — නේ / නෙ / නෑ / ණේ / ණෙ / ණෑ / නේ
- impact: 9735 word-tokens in SOLD
- members by frequency: නේ (4067), නෙ (3843), නෑ (1903), ණේ (69), ණෙ (29), ණෑ (11), නේ (7)
  - `නෑ` -> `නේ` (attested)
  - `අනේ` -> `අනෙ` (attested)
  - `කියන්නෙ` -> `කියන්නේ` (attested)

## 17. `ki` (vowel_length) — කි / කී
- impact: 7570 word-tokens in SOLD
- members by frequency: කි (7241), කී (343)
  - `කියලා` -> `කීයලා` (attested)
  - `කියල` -> `කීයල` (attested)
  - `කියන` -> `කීයන` (unattested)

## 18. `sa` (vowel_length) — ස / සා / සැ
- impact: 7507 word-tokens in SOLD
- members by frequency: ස (5781), සා (1437), සැ (350)
  - `නිසා` -> `නිස` (attested)
  - `සක්කිලි` -> `සාක්කිලි` (unattested)
  - `සල්ලි` -> `සාල්ලි` (attested)

## 19. `ga` (vowel_length) — ග / ගැ / ගා
- impact: 7218 word-tokens in SOLD
- members by frequency: ග (5780), ගැ (1024), ගා (511)
  - `ගැන` -> `ගන` (attested)
  - `ගන්න` -> `ගැන්න` (attested)
  - `ගහන්න` -> `ගැහන්න` (unattested)

## 20. `ge` (mixed) — ගෙ / ගේ / ගෑ / ගේ
- impact: 6863 word-tokens in SOLD
- members by frequency: ගෙ (3338), ගේ (3067), ගෑ (498), ගේ (6)
  - `වගේ` -> `වගෙ` (attested)
  - `මගේ` -> `මගෙ` (attested)
  - `ගෙදර` -> `ගේදර` (attested)

## 21. `ba` (vowel_length) — බ / බැ / බා
- impact: 6808 word-tokens in SOLD
- members by frequency: බ (5135), බැ (1265), බා (476)
  - `බන්` -> `බැන්` (attested)
  - `බල්ලා` -> `බැල්ලා` (unattested)
  - `බැරි` -> `බරි` (attested)

## 22. `yi` (vowel_length) — යි / යී
- impact: 6677 word-tokens in SOLD
- members by frequency: යි (6604), යී (96)
  - `තමයි` -> `තමයී` (attested)
  - `ඇයි` -> `ඇයී` (attested)
  - `පයිය` -> `පයීය` (unattested)

## 23. `we` (vowel_length) — වෙ / වේ / වෑ
- impact: 6071 word-tokens in SOLD
- members by frequency: වෙ (4730), වේ (1482), වෑ (27)
  - `වෙලා` -> `වේලා` (attested)
  - `වෙන්න` -> `වේන්න` (unattested)
  - `වෙන` -> `වේන` (attested)

## 24. `thi` (mixed) — ති / තී / ථි
- impact: 5752 word-tokens in SOLD
- members by frequency: ති (5487), තී (251), ථි (49)
  - `නැති` -> `නැතී` (attested)
  - `ඇති` -> `ඇතී` (attested)
  - `ඉතින්` -> `ඉතීන්` (unattested)

## 25. `ni` (mixed) — නි / ණි / නී / ණී
- impact: 5226 word-tokens in SOLD
- members by frequency: නි (4099), ණි (640), නී (465), ණී (48)
  - `නිසා` -> `ණිසා` (attested)
  - `මිනිස්සු` -> `මිණිස්සු` (attested)
  - `කාලකණ්ණි` -> `කාලකණ්නි` (attested)

## 26. `di` (mixed) — දි / ඩි / දී / ඩී
- impact: 4688 word-tokens in SOLD
- members by frequency: දි (2493), ඩි (1374), දී (802), ඩී (63)
  - `පොඩි` -> `පොදි` (attested)
  - `තඩි` -> `තදි` (unattested)
  - `වැඩි` -> `වැදි` (attested)

## 27. `me` (vowel_length) — මේ / මෙ / මෑ
- impact: 4501 word-tokens in SOLD
- members by frequency: මේ (2983), මෙ (1498), මෑ (22)
  - `මේ` -> `මෙ` (attested)
  - `මේක` -> `මෙක` (attested)
  - `මෙහෙම` -> `මේහෙම` (unattested)

## 28. `u` (consonant_quality) — උ / ඌ
- impact: 4323 word-tokens in SOLD
- members by frequency: උ (4011), ඌ (316)
  - `උන්` -> `ඌන්` (unattested)
  - `උඹ` -> `ඌඹ` (unattested)
  - `උන්ට` -> `ඌන්ට` (unattested)

## 29. `i` (consonant_quality) — ඉ / ඊ
- impact: 4220 word-tokens in SOLD
- members by frequency: ඉ (3913), ඊ (307)
  - `ඉන්න` -> `ඊන්න` (unattested)
  - `ඉතින්` -> `ඊතින්` (unattested)
  - `ඉන්නේ` -> `ඊන්නේ` (unattested)

## 30. `ko` (vowel_length) — කො / කෝ
- impact: 4193 word-tokens in SOLD
- members by frequency: කො (2710), කෝ (1486)
  - `යකෝ` -> `යකො` (attested)
  - `පකෝ` -> `පකො` (attested)
  - `එතකොට` -> `එතකෝට` (unattested)

## 31. `wi` (vowel_length) — වි / වී
- impact: 4014 word-tokens in SOLD
- members by frequency: වි (3422), වී (619)
  - `විතරයි` -> `වීතරයි` (unattested)
  - `ඇවිත්` -> `ඇවීත්` (unattested)
  - `විතරක්` -> `වීතරක්` (unattested)

## 32. `ri` (vowel_length) — රි / රී
- impact: 3972 word-tokens in SOLD
- members by frequency: රි (3396), රී (590)
  - `හරි` -> `හරී` (attested)
  - `බැරි` -> `බැරී` (attested)
  - `හරියට` -> `හරීයට` (attested)

## 33. `de` (mixed) — දෙ / දේ / ඩේ / ඩෙ / දෑ / ඩෑ
- impact: 3832 word-tokens in SOLD
- members by frequency: දෙ (2343), දේ (946), ඩේ (380), ඩෙ (106), දෑ (52), ඩෑ (14)
  - `දෙන්න` -> `දේන්න` (unattested)
  - `දෙයක්` -> `දේයක්` (unattested)
  - `දේවල්` -> `දෙවල්` (attested)

## 34. `o` (consonant_quality) — ඔ / ඕ / ඔ්
- impact: 3763 word-tokens in SOLD
- members by frequency: ඔ (2398), ඕ (1359), ඔ් (12)
  - `ඔය` -> `ඕය` (attested)
  - `ඕන` -> `ඔන` (attested)
  - `ඔයා` -> `ඕයා` (unattested)

## 35. `ke` (vowel_length) — කෙ / කේ / කෑ
- impact: 3470 word-tokens in SOLD
- members by frequency: කෙ (1970), කේ (965), කෑ (537)
  - `එකේ` -> `එකෙ` (attested)
  - `එකෙක්` -> `එකේක්` (unattested)
  - `කෑල්ල` -> `කෙල්ල` (attested)

## 36. `pi` (vowel_length) — පි / පී
- impact: 3335 word-tokens in SOLD
- members by frequency: පි (3254), පී (112)
  - `අපි` -> `අපී` (attested)
  - `පිස්සු` -> `පීස්සු` (unattested)
  - `තොපි` -> `තොපී` (unattested)

## 37. `li` (mixed) — ලි / ලී / ළි
- impact: 3277 word-tokens in SOLD
- members by frequency: ලි (2899), ලී (195), ළි (187)
  - `සක්කිලි` -> `සක්කිලී` (unattested)
  - `සල්ලි` -> `සල්ලී` (attested)
  - `කලින්` -> `කලීන්` (unattested)

## 38. `du` (mixed) — දු / ඩු / දූ / ඩූ
- impact: 3231 word-tokens in SOLD
- members by frequency: දු (2016), ඩු (1156), දූ (63), ඩූ (9)
  - `අවුරුදු` -> `අවුරුඩු` (attested)
  - `බඩුව` -> `බදුව` (attested)
  - `ටහුඩු` -> `ටහුදු` (unattested)

## 39. `hi` (vowel_length) — හි / හී
- impact: 3129 word-tokens in SOLD
- members by frequency: හි (3039), හී (101)
  - `ගිහින්` -> `ගිහීන්` (unattested)
  - `හිතන්` -> `හීතන්` (unattested)
  - `හිත` -> `හීත` (attested)

## 40. `ye` (vowel_length) — යෙ / යේ / යෑ
- impact: 3037 word-tokens in SOLD
- members by frequency: යෙ (2108), යේ (906), යෑ (23)
  - `තියෙන` -> `තියේන` (attested)
  - `තියෙන්නේ` -> `තියේන්නේ` (unattested)
  - `තියෙන්නෙ` -> `තියේන්නෙ` (unattested)

## 41. `ru` (vowel_length) — රු / රූ
- impact: 2871 word-tokens in SOLD
- members by frequency: රු (2809), රූ (84)
  - `අමාරු` -> `අමාරූ` (unattested)
  - `අවුරුදු` -> `අවුරූදු` (unattested)
  - `බොරු` -> `බොරූ` (unattested)

## 42. `pu` (vowel_length) — පු / පූ
- impact: 2812 word-tokens in SOLD
- members by frequency: පු (2683), පූ (147)
  - `පුක` -> `පූක` (unattested)
  - `කරපු` -> `කරපූ` (unattested)
  - `පුලුවන්` -> `පූලුවන්` (unattested)

## 43. `si` (vowel_length) — සි / සී
- impact: 2626 word-tokens in SOLD
- members by frequency: සි (2286), සී (353)
  - `වේසි` -> `වේසී` (attested)
  - `සීන්` -> `සින්` (attested)
  - `කිසිම` -> `කිසීම` (unattested)

## 44. `d` (consonant_quality) — ද් / ඩ්
- impact: 2367 word-tokens in SOLD
- members by frequency: ද් (1854), ඩ් (521)
  - `රෙද්ද` -> `රෙඩ්ද` (unattested)
  - `නැද්ද` -> `නැඩ්ද` (unattested)
  - `පොඩ්ඩක්` -> `පොද්ඩක්` (unattested)

## 45. `thu` (vowel_length) — තු / තූ
- impact: 2329 word-tokens in SOLD
- members by frequency: තු (2253), තූ (79)
  - `නැතුව` -> `නැතූව` (unattested)
  - `වතුර` -> `වතූර` (attested)
  - `යුතුයි` -> `යුතූයි` (attested)

## 46. `ja` (vowel_length) — ජ / ජා / ජැ
- impact: 2226 word-tokens in SOLD
- members by frequency: ජ (1529), ජා (696), ජැ (9)
  - `අවජාතක` -> `අවජතක` (attested)
  - `හුජ්ජ` -> `හුජ්ජා` (unattested)
  - `බිජ්ජ` -> `බිජ්ජා` (attested)

## 47. `re` (vowel_length) — රෙ / රේ / රෑ
- impact: 2217 word-tokens in SOLD
- members by frequency: රෙ (1414), රේ (705), රෑ (99)
  - `රෙද්ද` -> `රේද්ද` (unattested)
  - `ආදරේ` -> `ආදරෙ` (attested)
  - `කරේ` -> `කරෙ` (attested)

## 48. `mi` (vowel_length) — මි / මී
- impact: 2187 word-tokens in SOLD
- members by frequency: මි (1860), මී (330)
  - `මිනිස්සු` -> `මීනිස්සු` (unattested)
  - `මිනිස්සුන්ට` -> `මීනිස්සුන්ට` (unattested)
  - `මී` -> `මි` (attested)

## 49. `ti` (vowel_length) — ටි / ටී
- impact: 2155 word-tokens in SOLD
- members by frequency: ටි (2045), ටී (117)
  - `ටික` -> `ටීක` (unattested)
  - `ටිකක්` -> `ටීකක්` (unattested)
  - `හැටි` -> `හැටී` (attested)

## 50. `mu` (vowel_length) — මු / මූ
- impact: 2138 word-tokens in SOLD
- members by frequency: මු (1798), මූ (342)
  - `මුන්` -> `මූන්` (attested)
  - `මූ` -> `මු` (attested)
  - `තමුසෙ` -> `තමූසෙ` (unattested)

## 51. `he` (vowel_length) — හෙ / හේ / හෑ
- impact: 2061 word-tokens in SOLD
- members by frequency: හෙ (1781), හේ (248), හෑ (33)
  - `හෙන` -> `හේන` (attested)
  - `එහෙම` -> `එහේම` (unattested)
  - `මෙහෙම` -> `මෙහේම` (attested)

## 52. `lu` (mixed) — ලු / ළු / ලූ
- impact: 2002 word-tokens in SOLD
- members by frequency: ලු (1522), ළු (429), ලූ (51)
  - `පුලුවන්` -> `පුළුවන්` (attested)
  - `පුළුවන්` -> `පුලුවන්` (attested)
  - `අලුත්` -> `අළුත්` (attested)

## 53. `se` (vowel_length) — සෙ / සේ / සෑ
- impact: 2001 word-tokens in SOLD
- members by frequency: සෙ (1219), සේ (723), සෑ (62)
  - `සෙට්` -> `සේට්` (unattested)
  - `අයිසෙ` -> `අයිසේ` (attested)
  - `පස්සෙ` -> `පස්සේ` (attested)

## 54. `le` (mixed) — ලෙ / ලේ / ලෑ / ළේ / ළෙ
- impact: 1998 word-tokens in SOLD
- members by frequency: ලෙ (1091), ලේ (794), ලෑ (70), ළේ (36), ළෙ (10)
  - `කෙල්ලෙක්` -> `කෙල්ලේක්` (attested)
  - `කාලේ` -> `කාලෙ` (attested)
  - `කලේ` -> `කලෙ` (attested)

## 55. `wu` (vowel_length) — වු / වූ
- impact: 1877 word-tokens in SOLD
- members by frequency: වු (1765), වූ (113)
  - `අවුරුදු` -> `අවූරුදු` (attested)
  - `කවුද` -> `කවූද` (attested)
  - `එවුන්` -> `එවූන්` (attested)

## 56. `ho` (vowel_length) — හො / හෝ
- impact: 1863 word-tokens in SOLD
- members by frequency: හො (1620), හෝ (243)
  - `හොඳ` -> `හෝඳ` (attested)
  - `කොහොමද` -> `කොහෝමද` (unattested)
  - `හොද` -> `හෝද` (attested)

## 57. `ku` (vowel_length) — කු / කූ
- impact: 1844 word-tokens in SOLD
- members by frequency: කු (1772), කූ (92)
  - `ලොකු` -> `ලොකූ` (attested)
  - `කුණු` -> `කූණු` (attested)
  - `කුඩු` -> `කූඩු` (attested)

## 58. `su` (vowel_length) — සු / සූ
- impact: 1805 word-tokens in SOLD
- members by frequency: සු (1752), සූ (76)
  - `පිස්සු` -> `පිස්සූ` (attested)
  - `මිනිස්සු` -> `මිනිස්සූ` (attested)
  - `මිනිස්සුන්ට` -> `මිනිස්සූන්ට` (unattested)

## 59. `mo` (vowel_length) — මො / මෝ
- impact: 1764 word-tokens in SOLD
- members by frequency: මො (1193), මෝ (571)
  - `මෝඩ` -> `මොඩ` (attested)
  - `මොන` -> `මෝන` (attested)
  - `මොකද` -> `මෝකද` (unattested)

## 60. `nu` (mixed) — නු / ණු / නූ
- impact: 1697 word-tokens in SOLD
- members by frequency: නු (1274), ණු (395), නූ (37)
  - `වෙනුවෙන්` -> `වෙණුවෙන්` (unattested)
  - `ගෑනු` -> `ගෑණු` (attested)
  - `ගෑණු` -> `ගෑනු` (attested)

## 61. `po` (vowel_length) — පො / පෝ
- impact: 1682 word-tokens in SOLD
- members by frequency: පො (1462), පෝ (221)
  - `පොඩි` -> `පෝඩි` (unattested)
  - `පොන්න` -> `පෝන්න` (unattested)
  - `පොඩ්ඩක්` -> `පෝඩ්ඩක්` (unattested)

## 62. `tho` (vowel_length) — තො / තෝ
- impact: 1669 word-tokens in SOLD
- members by frequency: තො (883), තෝ (786)
  - `තෝ` -> `තො` (attested)
  - `තොපි` -> `තෝපි` (attested)
  - `තොට` -> `තෝට` (attested)

## 63. `pe` (vowel_length) — පේ / පෙ / පෑ
- impact: 1654 word-tokens in SOLD
- members by frequency: පේ (852), පෙ (747), පෑ (55)
  - `අපේ` -> `අපෙ` (attested)
  - `අපෙ` -> `අපේ` (attested)
  - `පෙන්නන්න` -> `පේන්නන්න` (unattested)

## 64. `hu` (vowel_length) — හු / හූ
- impact: 1615 word-tokens in SOLD
- members by frequency: හු (1574), හූ (42)
  - `හුජ්ජ` -> `හූජ්ජ` (unattested)
  - `ටහුඩු` -> `ටහූඩු` (unattested)
  - `හුත්ත` -> `හූත්ත` (unattested)

## 65. `gi` (vowel_length) — ගි / ගී
- impact: 1495 word-tokens in SOLD
- members by frequency: ගි (1395), ගී (101)
  - `ගිහින්` -> `ගීහින්` (unattested)
  - `ගියා` -> `ගීයා` (unattested)
  - `ගිය` -> `ගීය` (attested)

## 66. `no` (mixed) — නො / නෝ / ණො / ණෝ
- impact: 1442 word-tokens in SOLD
- members by frequency: නො (1205), නෝ (225), ණො (12), ණෝ (5)
  - `නොදකින්` -> `නෝදකින්` (unattested)
  - `නොකර` -> `නෝකර` (unattested)
  - `උනොත්` -> `උනෝත්` (unattested)

## 67. `sha` (mixed) — ශ / ෂ / ශා / ෂා / ශැ
- impact: 1373 word-tokens in SOLD
- members by frequency: ශ (694), ෂ (487), ශා (96), ෂා (91), ශැ (7)
  - `දේශපාලන` -> `දේෂපාලන` (unattested)
  - `විනාශ` -> `විනාෂ` (attested)
  - `රාජපක්ෂ` -> `රාජපක්ශ` (attested)

## 68. `the` (vowel_length) — තේ / තෙ / තෑ
- impact: 1297 word-tokens in SOLD
- members by frequency: තේ (690), තෙ (545), තෑ (63)
  - `හිතෙනවා` -> `හිතේනවා` (attested)
  - `තේරුම්` -> `තෙරුම්` (attested)
  - `ජීවිතේ` -> `ජීවිතෙ` (attested)

## 69. `lo` (mixed) — ලො / ලෝ / ළො
- impact: 1282 word-tokens in SOLD
- members by frequency: ලො (805), ලෝ (457), ළො (21)
  - `ලොකු` -> `ලෝකු` (attested)
  - `කෙල්ලො` -> `කෙල්ලෝ` (attested)
  - `කොල්ලො` -> `කොල්ලෝ` (attested)

## 70. `go` (vowel_length) — ගො / ගෝ
- impact: 1228 word-tokens in SOLD
- members by frequency: ගො (1092), ගෝ (136)
  - `ගොන්` -> `ගෝන්` (attested)
  - `ගොනා` -> `ගෝනා` (attested)
  - `ගොඩක්` -> `ගෝඩක්` (unattested)

## 71. `cha` (vowel_length) — ච / චා / චැ
- impact: 1048 word-tokens in SOLD
- members by frequency: ච (829), චා (182), චැ (39)
  - `කොච්චර` -> `කොච්චාර` (unattested)
  - `මෙච්චර` -> `මෙච්චාර` (unattested)
  - `වචන` -> `වචාන` (unattested)

## 72. `be` (vowel_length) — බෙ / බෑ / බේ
- impact: 1031 word-tokens in SOLD
- members by frequency: බෙ (379), බෑ (371), බේ (281)
  - `බෑ` -> `බෙ` (attested)
  - `උබේ` -> `උබෙ` (attested)
  - `ඔබේ` -> `ඔබෙ` (attested)

## 73. `yo` (vowel_length) — යෝ / යො
- impact: 1001 word-tokens in SOLD
- members by frequency: යෝ (629), යො (373)
  - `වීඩියෝ` -> `වීඩියො` (attested)
  - `ගියොත්` -> `ගියෝත්` (attested)
  - `පොන්නයෝ` -> `පොන්නයො` (attested)

## 74. `bo` (vowel_length) — බො / බෝ
- impact: 904 word-tokens in SOLD
- members by frequency: බො (666), බෝ (238)
  - `බොල` -> `බෝල` (attested)
  - `බොරු` -> `බෝරු` (unattested)
  - `බොන්න` -> `බෝන්න` (unattested)

## 75. `nda` (mixed) — ඳ / ඬ / ඳා / ඬා
- impact: 775 word-tokens in SOLD
- members by frequency: ඳ (705), ඬ (53), ඳා (11), ඬා (6)
  - `හොඳ` -> `හොඬ` (attested)
  - `හොඳයි` -> `හොඬයි` (unattested)
  - `ඉඳන්` -> `ඉඬන්` (unattested)

## 76. `bi` (vowel_length) — බි / බී
- impact: 752 word-tokens in SOLD
- members by frequency: බි (599), බී (161)
  - `බිජ්ජ` -> `බීජ්ජ` (unattested)
  - `බිම` -> `බීම` (attested)
  - `බීලා` -> `බිලා` (attested)

## 77. `bu` (vowel_length) — බු / බූ
- impact: 691 word-tokens in SOLD
- members by frequency: බු (562), බූ (130)
  - `තිබුනා` -> `තිබූනා` (unattested)
  - `බුදු` -> `බූදු` (unattested)
  - `බූරුවා` -> `බුරුවා` (attested)

## 78. `te` (vowel_length) — ටේ / ටෙ / ටෑ
- impact: 682 word-tokens in SOLD
- members by frequency: ටේ (471), ටෙ (199), ටෑ (12)
  - `රටේ` -> `රටෙ` (attested)
  - `වටේ` -> `වටෙ` (attested)
  - `කටේ` -> `කටෙ` (attested)

## 79. `tu` (vowel_length) — ටු / ටූ
- impact: 604 word-tokens in SOLD
- members by frequency: ටු (581), ටූ (24)
  - `සතුටු` -> `සතුටූ` (attested)
  - `ටුවිට්` -> `ටූවිට්` (unattested)
  - `සතුටුයි` -> `සතුටූයි` (unattested)

## 80. `ji` (vowel_length) — ජී / ජි
- impact: 565 word-tokens in SOLD
- members by frequency: ජී (292), ජි (273)
  - `ජීවත්` -> `ජිවත්` (attested)
  - `ජීවිතේ` -> `ජිවිතේ` (attested)
  - `ජීවිත` -> `ජිවිත` (attested)

## 81. `dha` (vowel_length) — ධ / ධා
- impact: 553 word-tokens in SOLD
- members by frequency: ධ (356), ධා (199)
  - `බෞද්ධ` -> `බෞද්ධා` (attested)
  - `සම්බන්ධ` -> `සම්බන්ධා` (attested)
  - `විරුද්ධ` -> `විරුද්ධා` (unattested)

## 82. `do` (mixed) — ඩො / ඩෝ / දො / දෝ
- impact: 541 word-tokens in SOLD
- members by frequency: ඩො (243), ඩෝ (118), දො (113), දෝ (68)
  - `අඩො` -> `අඩෝ` (attested)
  - `අඩෝ` -> `අඩො` (attested)
  - `ඩොලර්` -> `ඩෝලර්` (unattested)

## 83. `lam` (mixed) — ලං / ලාං / ළං
- impact: 525 word-tokens in SOLD
- members by frequency: ලං (492), ලාං (26), ළං (7)
  - `ලංකාවේ` -> `ලාංකාවේ` (attested)
  - `ලංකාවෙ` -> `ලාංකාවෙ` (unattested)
  - `ලංකාව` -> `ලාංකාව` (attested)

## 84. `yu` (vowel_length) — යු / යූ
- impact: 523 word-tokens in SOLD
- members by frequency: යු (480), යූ (51)
  - `යුතුයි` -> `යූතුයි` (attested)
  - `යුතුය` -> `යූතුය` (unattested)
  - `කටයුතු` -> `කටයූතු` (unattested)

## 85. `ro` (vowel_length) — රෝ / රො
- impact: 485 word-tokens in SOLD
- members by frequency: රෝ (303), රො (187)
  - `කොරෝනා` -> `කොරොනා` (attested)
  - `බලාපොරොත්තු` -> `බලාපොරෝත්තු` (attested)
  - `කරොත්` -> `කරෝත්` (unattested)

## 86. `wo` (vowel_length) — වො / වෝ
- impact: 404 word-tokens in SOLD
- members by frequency: වො (261), වෝ (143)
  - `කිව්වොත්` -> `කිව්වෝත්` (unattested)
  - `ආවොත්` -> `ආවෝත්` (attested)
  - `බැලුවොත්` -> `බැලුවෝත්` (unattested)

## 87. `gu` (vowel_length) — ගු / ගූ
- impact: 400 word-tokens in SOLD
- members by frequency: ගු (351), ගූ (50)
  - `ගූ` -> `ගු` (attested)
  - `මගුල්` -> `මගූල්` (attested)
  - `ගුටි` -> `ගූටි` (attested)

## 88. `sh` (consonant_quality) — ශ් / ෂ්
- impact: 365 word-tokens in SOLD
- members by frequency: ශ් (284), ෂ් (81)
  - `ප්‍රශ්න` -> `ප්‍රෂ්න` (attested)
  - `ප්‍රශ්නයක්` -> `ප්‍රෂ්නයක්` (unattested)
  - `විශ්වාස` -> `විෂ්වාස` (unattested)

## 89. `chi` (vowel_length) — චි / චී
- impact: 362 word-tokens in SOLD
- members by frequency: චි (250), චී (114)
  - `පුංචි` -> `පුංචී` (unattested)
  - `චීන` -> `චින` (attested)
  - `පාවිච්චි` -> `පාවිච්චී` (unattested)

## 90. `bam` (vowel_length) — බං / බැං
- impact: 309 word-tokens in SOLD
- members by frequency: බං (280), බැං (29)
  - `බං` -> `බැං` (unattested)
  - `බැංකු` -> `බංකු` (attested)
  - `බැංකුවට` -> `බංකුවට` (attested)

## 91. `bha` (vowel_length) — භා / භ
- impact: 309 word-tokens in SOLD
- members by frequency: භා (203), භ (106)
  - `සුභ` -> `සුභා` (attested)
  - `ගෝඨාභය` -> `ගෝඨාභාය` (attested)
  - `සභා` -> `සභ` (attested)

## 92. `dhi` (vowel_length) — ධි / ධී
- impact: 303 word-tokens in SOLD
- members by frequency: ධි (276), ධී (27)
  - `ජනාධිපති` -> `ජනාධීපති` (attested)
  - `බුද්ධිමත්` -> `බුද්ධීමත්` (unattested)
  - `ප්‍රසිද්ධියේ` -> `ප්‍රසිද්ධීයේ` (unattested)

## 93. `to` (vowel_length) — ටෝ / ටො
- impact: 291 word-tokens in SOLD
- members by frequency: ටෝ (210), ටො (81)
  - `ටෝක්` -> `ටොක්` (attested)
  - `ෆොටෝ` -> `ෆොටො` (attested)
  - `පොටෝ` -> `පොටො` (attested)

## 94. `nga` (vowel_length) — ඟ / ඟා
- impact: 282 word-tokens in SOLD
- members by frequency: ඟ (271), ඟා (11)
  - `ලඟ` -> `ලඟා` (attested)
  - `ඊළඟ` -> `ඊළඟා` (unattested)
  - `හිඟන` -> `හිඟාන` (unattested)

## 95. `nam` (consonant_quality) — නං / ණං
- impact: 270 word-tokens in SOLD
- members by frequency: නං (265), ණං (5)
  - `නං` -> `ණං` (attested)
  - `නංගි` -> `ණංගි` (unattested)
  - `එහෙනං` -> `එහෙණං` (unattested)

## 96. `so` (vowel_length) — සො / සෝ
- impact: 251 word-tokens in SOLD
- members by frequency: සො (150), සෝ (101)
  - `සොයා` -> `සෝයා` (attested)
  - `සොරි` -> `සෝරි` (unattested)
  - `පිස්සො` -> `පිස්සෝ` (attested)

## 97. `shi` (mixed) — ශි / ෂි / ශී / ෂී
- impact: 197 word-tokens in SOLD
- members by frequency: ශි (84), ෂි (68), ශී (39), ෂී (6)
  - `දේශීය` -> `දේශිය` (attested)
  - `සාක්ෂි` -> `සාක්ශි` (unattested)
  - `ශික්` -> `ෂික්` (attested)

## 98. `pam` (vowel_length) — පං / පාං
- impact: 191 word-tokens in SOLD
- members by frequency: පං (186), පාං (5)
  - `කරපං` -> `කරපාං` (unattested)
  - `බලපං` -> `බලපාං` (unattested)
  - `හිටපං` -> `හිටපාං` (unattested)

## 99. `ndu` (consonant_quality) — ඳු / ඬු
- impact: 186 word-tokens in SOLD
- members by frequency: ඳු (158), ඬු (28)
  - `ඇඳුම්` -> `ඇඬුම්` (attested)
  - `ඇඳුමක්` -> `ඇඬුමක්` (unattested)
  - `දඬුවම්` -> `දඳුවම්` (unattested)

## 100. `fo` (vowel_length) — ෆො / ෆෝ
- impact: 150 word-tokens in SOLD
- members by frequency: ෆො (86), ෆෝ (64)
  - `ෆොටෝ` -> `ෆෝටෝ` (unattested)
  - `ෆෝන්` -> `ෆොන්` (attested)
  - `ෆෝම්` -> `ෆොම්` (attested)

## 101. `je` (vowel_length) — ජෙ / ජේ
- impact: 147 word-tokens in SOLD
- members by frequency: ජෙ (113), ජේ (34)
  - `ජෙප්පෝ` -> `ජේප්පෝ` (unattested)
  - `සමාජෙට` -> `සමාජේට` (unattested)
  - `ජෙරී` -> `ජේරී` (attested)

## 102. `ndi` (mixed) — ඳි / ඳී / ඬි
- impact: 144 word-tokens in SOLD
- members by frequency: ඳි (117), ඳී (19), ඬි (8)
  - `අඳින` -> `අඳීන` (unattested)
  - `බඳින්න` -> `බඳීන්න` (unattested)
  - `විඳින` -> `විඳීන` (unattested)

## 103. `fa` (vowel_length) — ෆ / ෆා / ෆැ
- impact: 127 word-tokens in SOLD
- members by frequency: ෆ (102), ෆා (13), ෆැ (12)
  - `ෆලෝ` -> `ෆාලෝ` (unattested)
  - `ප්‍රොෆයිල්` -> `ප්‍රොෆායිල්` (unattested)
  - `අන්ෆලෝ` -> `අන්ෆාලෝ` (unattested)

## 104. `she` (mixed) — ශේ / ශෙ / ෂේ / ෂෙ
- impact: 125 word-tokens in SOLD
- members by frequency: ශේ (63), ශෙ (27), ෂේ (21), ෂෙ (14)
  - `විශේෂ` -> `විශෙෂ` (attested)
  - `ශේප්` -> `ශෙප්` (attested)
  - `ප්‍රතික්ෂේප` -> `ප්‍රතික්ශේප` (attested)

## 105. `chha` (vowel_length) — ඡ / ඡා
- impact: 120 word-tokens in SOLD
- members by frequency: ඡ (100), ඡා (20)
  - `ඡන්ද` -> `ඡාන්ද` (unattested)
  - `ඡන්දෙ` -> `ඡාන්දෙ` (unattested)
  - `ඡන්දේ` -> `ඡාන්දේ` (unattested)

## 106. `jo` (vowel_length) — ජෝ / ජො
- impact: 116 word-tokens in SOLD
- members by frequency: ජෝ (60), ජො (56)
  - `ජොබ්` -> `ජෝබ්` (attested)
  - `ජෝක්` -> `ජොක්` (attested)
  - `බිජ්ජො` -> `බිජ්ජෝ` (attested)

## 107. `fe` (vowel_length) — ෆේ / ෆෙ / ෆෑ
- impact: 111 word-tokens in SOLD
- members by frequency: ෆේ (78), ෆෙ (23), ෆෑ (10)
  - `ෆේස්බුක්` -> `ෆෙස්බුක්` (attested)
  - `ෆේල්` -> `ෆෙල්` (unattested)
  - `ෆේක්` -> `ෆෙක්` (unattested)

## 108. `chu` (vowel_length) — චූ / චු
- impact: 107 word-tokens in SOLD
- members by frequency: චූ (68), චු (39)
  - `චූටි` -> `චුටි` (attested)
  - `චූන්` -> `චුන්` (attested)
  - `චූ` -> `චු` (attested)

## 109. `mbe` (vowel_length) — ඹේ / ඹෙ
- impact: 107 word-tokens in SOLD
- members by frequency: ඹේ (77), ඹෙ (30)
  - `උඹේ` -> `උඹෙ` (attested)
  - `උඹෙ` -> `උඹේ` (attested)
  - `නුඹේ` -> `නුඹෙ` (attested)

## 110. `fi` (vowel_length) — ෆි / ෆී
- impact: 106 word-tokens in SOLD
- members by frequency: ෆි (94), ෆී (12)
  - `ෆිල්ම්` -> `ෆීල්ම්` (attested)
  - `ඔෆිස්` -> `ඔෆීස්` (attested)
  - `ෆිට්` -> `ෆීට්` (attested)

## 111. `aa` (vowel_length) — අැ / අා
- impact: 101 word-tokens in SOLD
- members by frequency: අැ (61), අා (40)
  - `අැයි` -> `අායි` (attested)
  - `අැති` -> `අාති` (unattested)
  - `අාතල්` -> `අැතල්` (unattested)

## 112. `dam` (mixed) — දැං / ඩං / දං
- impact: 99 word-tokens in SOLD
- members by frequency: දැං (50), ඩං (35), දං (14)
  - `දැං` -> `ඩං` (unattested)
  - `අත්අඩංගුවට` -> `අත්අදැංගුවට` (unattested)
  - `අඩංගුවට` -> `අදැංගුවට` (unattested)

## 113. `kam` (vowel_length) — කං / කාං
- impact: 92 word-tokens in SOLD
- members by frequency: කං (85), කාං (7)
  - `නිකං` -> `නිකාං` (unattested)
  - `වෙනකං` -> `වෙනකාං` (unattested)
  - `කං` -> `කාං` (unattested)

## 114. `yam` (vowel_length) — යං / යාං
- impact: 88 word-tokens in SOLD
- members by frequency: යං (75), යාං (13)
  - `පලයං` -> `පලයාං` (unattested)
  - `තියං` -> `තියාං` (attested)
  - `යං` -> `යාං` (unattested)

## 115. `ham` (vowel_length) — හං / හැං
- impact: 85 word-tokens in SOLD
- members by frequency: හං (69), හැං (16)
  - `බලහං` -> `බලහැං` (unattested)
  - `ගහං` -> `ගහැං` (unattested)
  - `හැංගි` -> `හංගි` (unattested)

## 116. `am` (consonant_quality) — අං / ආං
- impact: 84 word-tokens in SOLD
- members by frequency: අං (72), ආං (12)
  - `අංක` -> `ආංක` (unattested)
  - `ආං` -> `අං` (attested)
  - `අංකල්` -> `ආංකල්` (unattested)

## 117. `sho` (mixed) — ශෝ / ශො / ෂෝ / ෂො
- impact: 73 word-tokens in SOLD
- members by frequency: ශෝ (34), ශො (20), ෂෝ (14), ෂො (5)
  - `ශොට්` -> `ශෝට්` (attested)
  - `ෂෝ` -> `ශෝ` (attested)
  - `සංශෝධනය` -> `සංශොධනය` (attested)

## 118. `ju` (vowel_length) — ජු / ජූ
- impact: 65 word-tokens in SOLD
- members by frequency: ජු (50), ජූ (15)
  - `අර්ජුන` -> `අර්ජූන` (unattested)
  - `අර්ජුන්` -> `අර්ජූන්` (attested)
  - `ජූලි` -> `ජුලි` (attested)

## 119. `kri` (vowel_length) — කෘ / කෲ
- impact: 47 word-tokens in SOLD
- members by frequency: කෘ (42), කෲ (5)
  - `සංස්කෘතිය` -> `සංස්කෲතිය` (unattested)
  - `විකෘති` -> `විකෲති` (unattested)
  - `කෲර` -> `කෘර` (attested)

## 120. `shu` (consonant_quality) — ශු / ෂු
- impact: 47 word-tokens in SOLD
- members by frequency: ශු (29), ෂු (18)
  - `ෂුවර්` -> `ශුවර්` (attested)
  - `ශුද්ධ` -> `ෂුද්ධ` (unattested)
  - `ශුවර්` -> `ෂුවර්` (attested)

## 121. `jnya` (vowel_length) — ඥ / ඥා
- impact: 44 word-tokens in SOLD
- members by frequency: ඥ (24), ඥා (20)
  - `ඥාති` -> `ඥති` (attested)
  - `දේශපාලනඥයින්` -> `දේශපාලනඥායින්` (attested)
  - `ඥානසාර` -> `ඥනසාර` (unattested)

## 122. `gha` (vowel_length) — ඝ / ඝා
- impact: 43 word-tokens in SOLD
- members by frequency: ඝ (24), ඝා (19)
  - `ඝාතනය` -> `ඝතනය` (unattested)
  - `ඝනකම` -> `ඝානකම` (unattested)
  - `ජනඝාතන` -> `ජනඝතන` (unattested)

## 123. `bhi` (vowel_length) — භි / භී
- impact: 31 word-tokens in SOLD
- members by frequency: භි (26), භී (5)
  - `සෝභිත` -> `සෝභීත` (unattested)
  - `අභියෝග` -> `අභීයෝග` (attested)
  - `භික්ෂුන්` -> `භීක්ෂුන්` (attested)

## 124. `cho` (vowel_length) — චෝ / චො
- impact: 31 word-tokens in SOLD
- members by frequency: චෝ (16), චො (15)
  - `චෝදනා` -> `චොදනා` (attested)
  - `චොර` -> `චෝර` (attested)
  - `චොක්ලට්` -> `චෝක්ලට්` (unattested)

## 125. `nge` (vowel_length) — ඟේ / ඟෙ
- impact: 28 word-tokens in SOLD
- members by frequency: ඟේ (19), ඟෙ (9)
  - `ඇඟේ` -> `ඇඟෙ` (attested)
  - `වේසිඟේ` -> `වේසිඟෙ` (unattested)
  - `උන්ඟෙ` -> `උන්ඟේ` (unattested)

## 126. `bhu` (vowel_length) — භූ / භු
- impact: 25 word-tokens in SOLD
- members by frequency: භූ (17), භු (8)
  - `භූගත` -> `භුගත` (attested)
  - `භුක්ති` -> `භූක්ති` (attested)
  - `භුමිය` -> `භූමිය` (attested)

## 127. `che` (vowel_length) — චේ / චෙ
- impact: 25 word-tokens in SOLD
- members by frequency: චේ (13), චෙ (12)
  - `චෙක්` -> `චේක්` (unattested)
  - `චේතනාවෙන්` -> `චෙතනාවෙන්` (unattested)
  - `නේම්චේන්ජ්ඩ්` -> `නේම්චෙන්ජ්ඩ්` (unattested)

## 128. `nde` (vowel_length) — ඳේ / ඳෙ
- impact: 25 word-tokens in SOLD
- members by frequency: ඳේ (19), ඳෙ (6)
  - `හොඳේ` -> `හොඳෙ` (unattested)
  - `ඇඳේ` -> `ඇඳෙ` (attested)
  - `ළිඳේ` -> `ළිඳෙ` (unattested)

## 129. `dim` (consonant_quality) — ඩිං / දිං
- impact: 16 word-tokens in SOLD
- members by frequency: ඩිං (11), දිං (5)
  - `ඩිංගක්` -> `දිංගක්` (unattested)
  - `පදිංචියට` -> `පඩිංචියට` (unattested)
  - `ඩිංගිරි` -> `දිංගිරි` (unattested)

## 130. `dhu` (vowel_length) — ධු / ධූ
- impact: 13 word-tokens in SOLD
- members by frequency: ධු (8), ධූ (5)
  - `ආධුනික` -> `ආධූනික` (unattested)
  - `සාධු` -> `සාධූ` (unattested)
  - `මධුවා` -> `මධූවා` (unattested)
