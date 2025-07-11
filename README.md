# qt-ts-translator

A semi-automatic translator for Qt `.ts` files (Chinese → French) using a manual dictionary and Google Translate as fallback.

## Features

- ✔ Manual translation dictionary
- ✔ Normalized key matching (ignores spaces/punctuation)
- ✔ Automatic translation via Google Translate
- ✔ Preserves formatting and HTML entities
- ✔ Outputs clean `.ts` files ready for Qt Linguist

## Usage

1. Place your source `.ts` file in the root folder (e.g., `deltaqin_fr.ts`)
2. Edit `dictionnaire.py` with your manual mappings:
   ```python
   manual_dict = {
       "复位(&amp;R)": "&amp;Reset",
       "清\n空": "R\nA\nZ",
       ...
   }
