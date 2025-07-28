# DeltaQin Translator

**DeltaQin Translator** est un utilitaire graphique permettant de **traduire automatiquement les fichiers `.qm`** (fichiers de traduction Qt) depuis le chinois vers une langue cible, de manière rapide et intuitive.  
Il a été développé pour faciliter la compréhension d’interfaces logicielles industrielles non documentées.

---

## 🧠 Fonctionnement

L’outil réalise les étapes suivantes de façon transparente :

1. **Décompilation** du fichier `.qm` en `.ts` via `lconvert.exe`
2. **Traduction automatique** des chaînes via Google Translate
3. **Correction avec un dictionnaire local** (si fourni)
4. **Recompilation** du fichier `.ts` en `.qm` via `lrelease.exe`
5. **Sauvegarde** du fichier dans le dossier `translated_files`

---

## 🖥️ Interface

L'application est livrée sous forme d’un **exécutable Windows autonome** :

- Pas besoin d’installer Python ou de librairies
- Interface moderne grâce à **Tkinter + ttkbootstrap**
- Traduction **en temps réel**, avec console intégrée et estimation du temps restant
- Possibilité d’**annuler la traduction** proprement
- Gestion simple des erreurs et des fichiers temporaires

---

## ▶️ Utilisation

1. **Lancer l’application** via le fichier `DeltaQin_Translator.exe`
2. **Choisir un fichier `.qm`** à traduire
3. **Sélectionner la langue cible**
4. *(Optionnel)* **Ajouter un dictionnaire personnalisé** (`dictionnaire_fr.txt`, etc.)
5. Cliquer sur **Traduire**

Le fichier traduit sera enregistré dans le dossier `translated_files`.

---

## 📁 Dictionnaire personnalisé (optionnel)

Tu peux fournir un fichier texte avec des traductions spécifiques à appliquer après Google Translate.  
Format attendu (une ligne par paire) :

    "加料时长": "Durée d'alimentation: ",
    "温度": "Température: ",
    "速度": "Vitesse: ",
    "进料": "Chargement",
    "出料": "Déchargement",

L’outil remplacera automatiquement les chaînes correspondantes.

---

## 📦 Contenu fourni

DeltaQin_Translator.exe ← Exécutable prêt à l’emploi

translated_files/ ← Dossier de sortie des fichiers traduits

dictionnaire_fr.txt ← (Exemple de dictionnaire)

README.md


---

## 📌 Remarques

- Nécessite un accès à Internet pour utiliser Google Translate
- Fonctionne uniquement avec des fichiers `.qm` générés via Qt Linguist
- Compatible **Windows uniquement** (version `.exe`)

---

## 🧾 À propos

Projet réalisé par **T. LAVAL** durant un stage chez **Lemtronic SA** (Suisse), mai – juillet 2025.

Cet outil a été développé pour **traduire l’interface du logiciel DeltaQin** dans le cadre de projets industriels en robotique, où le logiciel d’origine est fourni uniquement en chinois.

