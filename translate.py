from deep_translator import GoogleTranslator
import xml.etree.ElementTree as ET
from dictionnaire import manual_dict 
import re
import html

def normalize_text(text):
    return re.sub(r'[：:\s]', '', text)

# Fichier d'entrée et sortie
input_ts_file = 'deltaqin_fr.ts'
output_ts_file = 'deltaqin_traduit_V3.ts'

# Chargement du XML
tree = ET.parse(input_ts_file)
root = tree.getroot()

translator = GoogleTranslator(source='zh-CN', target='fr')

message_count = 0
for message in root.iter('message'):
    message_count += 1
    source = message.find('source')
    translation = message.find('translation')

    if source is not None and source.text:
        chinese_text = source.text.strip()
        escaped_text = html.escape(chinese_text)
        normalized_text = normalize_text(escaped_text)

        try:
            if escaped_text in manual_dict:
                translated_text = manual_dict[escaped_text]
                method = "manuel"
            elif normalized_text in manual_dict:
                translated_text = manual_dict[normalized_text]
                method = "manuel*"
            else:
                translated_text = translator.translate(chinese_text)
                method = "automatique"

            if translation is not None:
                translation.text = translated_text  # laissé tel quel

            print(f"[{message_count}] {chinese_text} → ({method}) → {translated_text}")

        except Exception as e:
            print(f"[{message_count}] Erreur de traduction pour '{chinese_text}': {e}")

# Sauvegarde dans un nouveau fichier .ts
tree.write(output_ts_file, encoding='utf-8', xml_declaration=True)
print(f"\nTraduction terminée. Nouveau fichier : {output_ts_file}")
