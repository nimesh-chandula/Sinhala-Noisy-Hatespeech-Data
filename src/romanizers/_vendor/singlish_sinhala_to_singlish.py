"""
VENDORED, UNMODIFIED (except this header) from asanka9/singlish v0.0.3
(https://pypi.org/project/singlish/, https://github.com/asanka9/singlish),
retrieved 2026-07-31 from the PyPI sdist at
https://files.pythonhosted.org/packages/0d/3c/d8866c575772b17960fb610f5dab6a796c19fa6bdc2329cd28fbc3b02e12/singlish-0.0.3.tar.gz
(file singlish-0.0.3/singlish/sinhalaToSinglish.py).

Not installed via pip: the sdist's setup.py references a README.md the
tarball doesn't ship (build fails), and the tarball erroneously bundles the
author's entire local venv/ (3.5MB of unrelated packages) — the actual
package is just this one class. Vendored directly instead.

Copyright 2021 asanka9. MIT License (see below) — permits copying/vendoring
with attribution, which is what this file is.

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions: the above copyright notice and this
    permission notice shall be included in all copies or substantial
    portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT
    WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

Used AS-IS (mapping table untouched) by src/romanizers/indic.py, which wraps
it to fix a real bug: SinhalaToSinglish.convert() iterates per-codepoint and
silently drops (via a bare `except:`) any character not in its table —
spaces, digits, punctuation, English letters — which corrupts multi-word
text by concatenating all words together. That fix lives in the wrapper,
not here, so this file stays a faithful, verifiable copy of the original.
"""


class SinhalaToSinglish:

    def __init__(self):
        self.sinhalaDictValue = {

            '්': '-',
            'ා': '-aa',
            'ැ': '-ae',
            'ෑ': '-aee',
            'ි': '-i',
            'ී': '-ee',
            'ු': '-u',
            'ූ': '-uu',
            'ෘ': '-ru',
            'ෲ': '-ruu',
            'ෟ': '-aou',
            'ෙ': '-e',
            'ේ': '-ee',
            'ෛ': '-ai',
            'ො': '-o',
            'ෝ': '-oo',
            'ෞ': '-aou',

            'අ': 'a',
            'ආ': 'aa',
            'ඇ': 'A',
            'ඉ': 'i',
            'ඊ': 'ii',
            'උ': 'u',
            'ඌ': 'uu',
            'එ': 'e',
            'ඒ': 'ee',
            'ඓ': 'ai',
            'ඔ': 'o',
            'ඕ': 'oo',
            'ඖ': 'au',
            'ක': 'ka',
            'ඛ': 'Ka',
            'ග': 'ga',
            'ඝ': 'Ga',
            'ච': 'cha',
            'ජ': 'ja',
            'ඣ': 'Ja',
            'ට': 'ta',
            'ඨ': 'Ta',
            'ඩ': 'da',
            'ඪ': 'Da',
            'ණ': 'Na',
            'ත': 'tha',
            'ද': 'dha',
            'ධ': 'Dha',
            'න': 'na',
            'ප': 'pa',
            'ඵ': 'pha',
            'බ': 'ba',
            'භ': 'bha',
            'ම': 'ma',
            'ය': 'ya',
            'ර': 'ra',
            'ල': 'la',
            'ව': 'va',
            'ශ': 'sha',
            'ෂ': 'Sa',
            'ස': 'sa',
            'හ': 'ha',
            'ෆ': 'fa',
            'ළ': 'La',
            'ං': 'x',
            'ඟ': 'zga',
            'ඦ': 'zja',
            'ඵ': 'pha',
            'ථ': 'thha',
            'ඥ': 'zha',
            'ඦ': 'zja',
            'ඡ': 'chha',
            'ඬ': 'zda',
            'ඃ': 'H',
            'ඳ': 'zdha',
            'ඹ': 'Ba',
            'ʠ': 'unk',
            'ඈ': 'AA',
            "'ׂ": 'unk',
            'ඤ': 'zka',
            'ඍ': 'R',
            'ඎ': 'Ru'

        }

        self.badWords = []

    def convert(self,word):
        sinhala_word = ''
        for character in word:
            try:
                if character != '\n' and character != '‍':
                    if self.sinhalaDictValue[character][0] == '-':
                        sinhala_word = sinhala_word[:-1] + self.sinhalaDictValue[character][1:]
                    else:
                        sinhala_word += self.sinhalaDictValue[character]
            except:
                self.badWords.append(word)
        return sinhala_word
