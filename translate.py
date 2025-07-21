from deep_translator import GoogleTranslator
import xml.etree.ElementTree as ET
import re
import html
import shutil
import subprocess
import os
import sys
from datetime import datetime
import io
import functools
import importlib
import time

start_time = time.time()

print = functools.partial(print, flush=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Force l'encodage en UTF-8 pour stdout et stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def normalize_text(text):
    return re.sub(r'[：:\s]', '', text)

# Arguments : fichier.ts et langue cible
if len(sys.argv) > 2:
    input_qm_file = sys.argv[1]
    target_lang = sys.argv[2]
else:
    input_qm_file = 'deltaqin_en.qm'
    target_lang = 'fr'

# Timestamp pour les noms de fichiers
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_ts_filename = f'deltaqin_{target_lang}_{timestamp}.ts'
output_qm_filename = f'deltaqin_{target_lang}_{timestamp}.qm'
base_name = os.path.splitext(os.path.basename(input_qm_file))[0]

# Dossiers
#qttools_dir = r"C:\Users\C.Udressy\Desktop\thibault\05 - qttools"
qttools_dir = os.path.join(BASE_DIR, "qttools")
#translated_dir = r"C:\Users\C.Udressy\Desktop\thibault\04 - VSC\translated_files"
translated_dir = os.path.join(BASE_DIR, "translated_files")
os.makedirs(translated_dir, exist_ok=True)

temp_dir = os.path.join(qttools_dir, "temp")
os.makedirs(temp_dir, exist_ok=True)


# Décompilation avec lconvert
decompiled_ts = os.path.join(temp_dir, f"{base_name}_source_{timestamp}.ts")
try:
    lconvert_path = os.path.join(qttools_dir, "lconvert.exe")
    subprocess.run([lconvert_path, input_qm_file, "-o", decompiled_ts], check=True)

    input_ts_file = decompiled_ts
    print(f"✅ Décompilation réussie : {decompiled_ts}")
except subprocess.CalledProcessError as e:
    print(f"❌ Erreur lors de la décompilation avec lconvert : {e}")
    sys.exit(1)


# Chemins complets
source_ts_temp = os.path.join(temp_dir, output_ts_filename)
source_qm_temp = os.path.join(temp_dir, output_qm_filename)
final_ts_path = os.path.join(translated_dir, output_ts_filename)
final_qm_path = os.path.join(translated_dir, output_qm_filename)

sys.path.insert(0, BASE_DIR)

# Chargement du dictionnaire de traduction s'il existe
manual_dict = {}
try:
    dict_module = importlib.import_module(f'dictionnaire_{target_lang}')
    manual_dict = getattr(dict_module, 'manual_dict', {})
    print(f"📘 Dictionnaire 'dictionnaire_{target_lang}.py' chargé ({len(manual_dict)} entrées)")
except ModuleNotFoundError:
    print(f"📙 Aucun dictionnaire spécifique trouvé pour la langue : {target_lang}")
except Exception as e:
    print(f"⚠️ Erreur lors du chargement du dictionnaire : {e}")

def count_total_messages(ts_path):
    try:
        with open(ts_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if "<message>" in line)
    except Exception as e:
        print(f"[ERREUR] Impossible de compter les messages : {e}")
        return 1  # Évite division par zéro

total_messages = count_total_messages(input_ts_file)


# Chargement du XML
tree = ET.parse(input_ts_file)
root = tree.getroot()

translator = GoogleTranslator(source='zh-CN', target=target_lang)

alpha = 0.2  # facteur de lissage (entre 0 et 1), plus petit = plus stable
ema_time_per_msg = None
start_time = time.time()
message_count = 0

for message in root.iter('message'):
    message_count += 1
    now = time.time()
    elapsed = now - start_time

    # Temps moyen actuel
    current_avg = elapsed / message_count

    # Calcul EMA
    if ema_time_per_msg is None:
        ema_time_per_msg = current_avg
    else:
        ema_time_per_msg = alpha * current_avg + (1 - alpha) * ema_time_per_msg

    progress = int((message_count / total_messages) * 100)
    print(f"[PROGRESS] {progress}", file=sys.stderr)

    if message_count % 10 == 0 and message_count > 0:
        remaining = total_messages - message_count
        eta_seconds = int(ema_time_per_msg * remaining)

        eta_min, eta_sec = divmod(eta_seconds, 60)
        print(f"[ETA_SECONDS] {eta_seconds}", file=sys.stderr)



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
    lrelease_path = os.path.join(qttools_dir, "lrelease.exe")
    output_qm_temp = os.path.join(temp_dir, output_qm_filename)
    subprocess.run([lrelease_path, source_ts_temp, "-qm", output_qm_temp], check=True)
    print(f"✅ Compilation terminée : {output_qm_filename} généré dans {qttools_dir}")
except subprocess.CalledProcessError as e:
    print(f"❌ Erreur lors de la compilation avec lrelease : {e}")

# Copie des fichiers finaux vers translated_files
try:
    shutil.copy(source_ts_temp, final_ts_path)
    shutil.copy(output_qm_temp, final_qm_path)
    print(f"✅ Fichiers finaux copiés dans : {translated_dir}")
except Exception as e:
    print(f"❌ Erreur lors de la copie des fichiers finaux : {e}")

# Suppression de tous les fichiers dans temp
try:
    for f in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
    print(f"🗑️ Tous les fichiers temporaires supprimés dans : {temp_dir}")
except Exception as e:
    print(f"⚠️ Erreur lors du nettoyage des fichiers temporaires : {e}")



# Résumé
print("\n✅ Traduction terminée.")
print(f"🔹 Fichier .ts généré : {final_ts_path}")
print(f"🔹 Fichier .qm généré : {final_qm_path}")
