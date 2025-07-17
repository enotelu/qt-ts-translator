from deep_translator import GoogleTranslator
import xml.etree.ElementTree as ET
from dictionnaire import manual_dict
import re
import html
import shutil
import subprocess
import os
import sys
from datetime import datetime
import io
import functools

print = functools.partial(print, flush=True)

# Force l'encodage en UTF-8 pour stdout et stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def normalize_text(text):
    return re.sub(r'[：:\s]', '', text)

# Timestamp pour fichiers
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Fichiers d'entrée
if len(sys.argv) > 1:
    input_ts_file = sys.argv[1]
else:
    input_ts_file = 'deltaqin_fr_test.ts'  # fallback

output_ts_filename = f'deltaqin_traduit_{timestamp}.ts'
output_qm_filename = f'deltaqin_fr_{timestamp}.qm'

# Dossiers
qttools_dir = r"C:\Users\C.Udressy\Desktop\thibault\05 - qttools"
translated_dir = r"C:\Users\C.Udressy\Desktop\thibault\04 - VSC\translated_files"
os.makedirs(translated_dir, exist_ok=True)

# Chemins complets
source_ts_temp = os.path.join(qttools_dir, output_ts_filename)
source_qm_temp = os.path.join(qttools_dir, output_qm_filename)
final_ts_path = os.path.join(translated_dir, output_ts_filename)
final_qm_path = os.path.join(translated_dir, output_qm_filename)

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
                translation.text = html.unescape(translated_text)

            try:
                print(f"[{message_count}] {chinese_text} → ({method}) → {translated_text}")
            except UnicodeEncodeError:
                print(f"[{message_count}] Traduction (contenu illisible)")


        except Exception as e:
            print(f"[{message_count}] ❌ Erreur de traduction pour '{chinese_text}': {e}")

# Sauvegarde temporaire du .ts dans qttools
try:
    tree.write(source_ts_temp, encoding='utf-8', xml_declaration=True)
    print(f"✅ Fichier .ts copié vers : {source_ts_temp}")
except Exception as e:
    print(f"❌ Erreur d'écriture du .ts dans QtTools : {e}")

# Compilation avec lrelease
try:
    os.chdir(qttools_dir)
    subprocess.run(["lrelease.exe", source_ts_temp, "-qm", output_qm_filename], check=True)
    print(f"✅ Compilation terminée : {output_qm_filename} généré dans {qttools_dir}")
except subprocess.CalledProcessError as e:
    print(f"❌ Erreur lors de la compilation avec lrelease : {e}")

# Copie des fichiers finaux vers translated_files
try:
    shutil.copy(source_ts_temp, final_ts_path)
    shutil.copy(source_qm_temp, final_qm_path)
    print(f"✅ Fichiers finaux copiés dans : {translated_dir}")
except Exception as e:
    print(f"❌ Erreur lors de la copie des fichiers finaux : {e}")

# Suppression des fichiers temporaires
try:
    os.remove(source_ts_temp)
    os.remove(source_qm_temp)
    print(f"🗑️ Fichiers temporaires supprimés dans {qttools_dir}")
except Exception as e:
    print(f"⚠️ Impossible de supprimer les fichiers temporaires : {e}")


# Résumé
print("\n✅ Traduction terminée.")
print(f"🔹 Fichier .ts généré : {final_ts_path}")
print(f"🔹 Fichier .qm généré : {final_qm_path}")
