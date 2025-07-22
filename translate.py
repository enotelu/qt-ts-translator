"""
DeltaQin Translator - Script de Traduction

Auteur : T. LAVAL / Lemtronic SA

Ce script est conçu pour traduire des fichiers .qm (format compilé Qt Linguist) en utilisant l'API Google Translate.
Il décompile d'abord le fichier .qm en .ts, traduit le contenu, puis recompile le fichier .ts traduit en .qm.
Il utilise également un dictionnaire personnalisé pour améliorer la qualité des traductions.
Les fichiers temporaires sont gérés dans un dossier 'temp' et les fichiers finaux sont enregistrés dans 'translated_files'.
"""

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
from typing import Optional
import queue


def normalize_text(text):
    return re.sub(r'[：:\s]', '', text)

def run_translation(input_qm_file: str, target_lang: str, dict_file_path: str = None, output_queue: queue.Queue = None):
    start_time = time.time()
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_ts_filename = f'deltaqin_{target_lang}_{timestamp}.ts'
    output_qm_filename = f'deltaqin_{target_lang}_{timestamp}.qm'
    base_name = os.path.splitext(os.path.basename(input_qm_file))[0]
    qttools_dir = os.path.join(BASE_DIR, "qttools")
    translated_dir = os.path.join(BASE_DIR, "translated_files")
    os.makedirs(translated_dir, exist_ok=True)
    temp_dir = os.path.join(qttools_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    decompiled_ts = os.path.join(temp_dir, f"{base_name}_source_{timestamp}.ts")

    was_cancelled = False  # Variable locale pour vérifier l'annulation

    try:
        lconvert_path = os.path.join(qttools_dir, "lconvert.exe")
        subprocess.run([lconvert_path, input_qm_file, "-o", decompiled_ts], check=True)
        input_ts_file = decompiled_ts
        if output_queue:
            output_queue.put(f"✅ Décompilation réussie : {decompiled_ts}\n")
    except subprocess.CalledProcessError as e:
        if output_queue:
            output_queue.put(f"❌ Erreur lors de la décompilation avec lconvert : {e}\n")
        raise RuntimeError("Erreur de décompilation avec lconvert")

    source_ts_temp = os.path.join(temp_dir, output_ts_filename)
    source_qm_temp = os.path.join(temp_dir, output_qm_filename)
    final_ts_path = os.path.join(translated_dir, output_ts_filename)
    final_qm_path = os.path.join(translated_dir, output_qm_filename)

    manual_dict = {}
    if dict_file_path:
        try:
            from importlib.machinery import SourceFileLoader
            module = SourceFileLoader("manual_dict_module", dict_file_path).load_module()
            if hasattr(module, "manual_dict"):
                manual_dict = module.manual_dict
                if output_queue:
                    output_queue.put(f"📘 Dictionnaire Python chargé depuis '{dict_file_path}' ({len(manual_dict)} entrées)\n")
            else:
                if output_queue:
                    output_queue.put(f"⚠️ Le fichier '{dict_file_path}' ne contient pas de variable 'manual_dict'\n")
        except Exception as e:
            if output_queue:
                output_queue.put(f"❌ Erreur de lecture du dictionnaire Python : {e}\n")

    def count_total_messages(ts_path):
        try:
            with open(ts_path, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if "<message>" in line)
        except Exception as e:
            if output_queue:
                output_queue.put(f"[ERREUR] Impossible de compter les messages : {e}\n")
            return 1

    total_messages = count_total_messages(input_ts_file)

    tree = ET.parse(input_ts_file)
    root = tree.getroot()

    translator = GoogleTranslator(source='zh-CN', target=target_lang)

    alpha = 0.2
    ema_time_per_msg = None
    start_time = time.time()
    message_count = 0

    for message in root.iter('message'):
        if was_cancelled:  # Utiliser la variable locale
            break

        message_count += 1
        now = time.time()
        elapsed = now - start_time
        current_avg = elapsed / message_count
        if ema_time_per_msg is None:
            ema_time_per_msg = current_avg
        else:
            ema_time_per_msg = alpha * current_avg + (1 - alpha) * ema_time_per_msg

        progress = int((message_count / total_messages) * 100)
        if output_queue:
            output_queue.put(f"[PROGRESS] {progress}\n")

        if message_count % 10 == 0 and message_count > 0:
            remaining = total_messages - message_count
            eta_seconds = int(ema_time_per_msg * remaining)
            if output_queue:
                output_queue.put(f"[ETA_SECONDS] {eta_seconds}\n")

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
                    if output_queue:
                        output_queue.put(f"[{message_count}] {chinese_text} → ({method}) → {translated_text}\n")
                except UnicodeEncodeError:
                    if output_queue:
                        output_queue.put(f"[{message_count}] Traduction (contenu illisible)\n")
            except Exception as e:
                if output_queue:
                    output_queue.put(f"[{message_count}] ❌ Erreur de traduction pour '{chinese_text}': {e}\n")

    try:
        tree.write(source_ts_temp, encoding='utf-8', xml_declaration=True)
        if output_queue:
            output_queue.put(f"✅ Fichier .ts copié vers : {source_ts_temp}\n")
    except Exception as e:
        if output_queue:
            output_queue.put(f"❌ Erreur d'écriture du .ts dans QtTools : {e}\n")

    try:
        lrelease_path = os.path.join(qttools_dir, "lrelease.exe")
        output_qm_temp = os.path.join(temp_dir, output_qm_filename)
        subprocess.run([lrelease_path, source_ts_temp, "-qm", output_qm_temp], check=True)
        if output_queue:
            output_queue.put(f"✅ Compilation terminée : {output_qm_filename} généré dans {qttools_dir}\n")
    except subprocess.CalledProcessError as e:
        if output_queue:
            output_queue.put(f"❌ Erreur lors de la compilation avec lrelease : {e}\n")

    try:
        shutil.copy(source_ts_temp, final_ts_path)
        shutil.copy(output_qm_temp, final_qm_path)
        if output_queue:
            output_queue.put(f"✅ Fichiers finaux copiés dans : {translated_dir}\n")
    except Exception as e:
        if output_queue:
            output_queue.put(f"❌ Erreur lors de la copie des fichiers finaux : {e}\n")

    try:
        for f in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        if output_queue:
            output_queue.put(f"🗑️ Tous les fichiers temporaires supprimés dans : {temp_dir}\n")
    except Exception as e:
        if output_queue:
            output_queue.put(f"⚠️ Erreur lors du nettoyage des fichiers temporaires : {e}\n")

    if output_queue:
        output_queue.put("\n✅ Traduction terminée.\n")
        output_queue.put(f"🔹 Fichier .ts généré : {final_ts_path}\n")
        output_queue.put(f"🔹 Fichier .qm généré : {final_qm_path}\n")
