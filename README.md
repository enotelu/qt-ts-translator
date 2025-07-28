DeltaQin Translator
DeltaQin Translator est un utilitaire graphique permettant de traduire automatiquement les fichiers .qm (fichiers de traduction Qt) depuis le chinois vers une langue cible, de manière rapide et intuitive.
Il a été développé pour faciliter la compréhension d’interfaces logicielles industrielles non documentées.

🧠 Fonctionnement
L’outil réalise les étapes suivantes de façon transparente :

Décompilation du fichier .qm en .ts via lconvert.exe

Traduction automatique des chaînes via Google Translate

Correction avec un dictionnaire local (si fourni)

Recompilation du fichier .ts en .qm via lrelease.exe

Sauvegarde du fichier dans le dossier translated_files

🖥️ Interface
L'application est livrée sous forme d’un exécutable Windows autonome :

Pas besoin d’installer Python ou de librairies

Interface moderne grâce à Tkinter + ttkbootstrap

Traduction en temps réel, avec console intégrée et estimation du temps restant

Possibilité d’annuler la traduction proprement

Gestion simple des erreurs et des fichiers temporaires

▶️ Utilisation
Lancer l’application via le fichier DeltaQin_Translator.exe

Choisir un fichier .qm à traduire

Sélectionner la langue cible

(Optionnel) Ajouter un dictionnaire personnalisé (dictionnaire_fr.txt, etc.)

Cliquer sur Traduire

Le fichier traduit sera enregistré dans le dossier translated_files.

📁 Dictionnaire personnalisé (optionnel)
Tu peux fournir un fichier texte avec des traductions spécifiques à appliquer après Google Translate. 
Format :
原文 | Traduction souhaitée
启动 | Démarrer
停止 | Arrêter
L’outil remplacera automatiquement les chaînes correspondantes.

📦 Contenu fourni
DeltaQin_Translator.exe      ← Exécutable prêt à l’emploi
translated_files/            ← Dossier de sortie des fichiers traduits
dictionnaire_fr.txt          ← (Exemple de dictionnaire)
README.md

📌 Remarques
Nécessite un accès à Internet pour utiliser Google Translate

Fonctionne uniquement avec des fichiers .qm générés via Qt Linguist

Compatible Windows uniquement (version .exe)

🧾 À propos
Projet réalisé par T. LAVAL durant un stage chez Lemtronic SA (Suisse), mai – juillet 2025.

Cet outil a été développé pour traduire l’interface du logiciel DeltaQin dans le cadre de projets industriels en robotique, où le logiciel d’origine est fourni uniquement en chinois.
