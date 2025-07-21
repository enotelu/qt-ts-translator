import ast
import re

# 📄 Chemin vers ton fichier dictionnaire Python
py_dict_file = "dictionnaire_fr.py"
# 📄 Fichier texte de sortie
txt_output_file = "dictionnaire_fr_export.txt"

# 🔁 Lecture du fichier
with open(py_dict_file, "r", encoding="utf-8") as f:
    content = f.read()

# 🔍 Extraction du bloc contenant le dictionnaire (manuel_dict = {...})
match = re.search(r'manual_dict\s*=\s*({.*})', content, re.DOTALL)
if not match:
    print("❌ Impossible de trouver 'manual_dict = {...}' dans le fichier.")
    exit(1)

dict_str = match.group(1)

# ✅ Évaluation sécurisée du dictionnaire
try:
    data = ast.literal_eval(dict_str)
except Exception as e:
    print(f"❌ Erreur d'évaluation du dictionnaire Python : {e}")
    exit(1)

# 📝 Conversion et écriture dans le fichier .txt
with open(txt_output_file, "w", encoding="utf-8") as f:
    for key, value in data.items():
        key_escaped = key.replace("\n", "\\n")
        value_escaped = value.replace("\n", "\\n")
        f.write(f"{key_escaped} ; {value_escaped}\n")

print(f"✅ Fichier exporté avec succès : {txt_output_file}")
