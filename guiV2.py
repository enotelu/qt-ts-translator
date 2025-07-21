from deep_translator import GoogleTranslator
import xml.etree.ElementTree as ET
import re
import html
import shutil
import subprocess
import os
import sys
import threading
import datetime
import io
import functools
import importlib
import time
import tkinter as tk
from tkinter import filedialog
from ttkbootstrap import Window, Button, Text, Label, Scrollbar, Style
from ttkbootstrap.dialogs import Messagebox
from tkinter import ttk

# Langues supportées : nom affiché → code Google Translate
LANGUAGES = {
    "Français": "fr",
    "Anglais": "en",
    "Allemand": "de",
    "Italien": "it",
    "Espagnol": "es",
    "Japonais": "ja",
    "Coréen": "ko",
    "Vietnamien": "vi",
    "Russe": "ru",
    "Arabe": "ar"
}

start_time = time.time()
print = functools.partial(print, flush=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Vérifiez si sys.stdout et sys.stderr sont valides avant de les rediriger
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
else:
    print("Erreur: Impossible de rediriger stdout")

if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
else:
    print("Erreur: Impossible de rediriger stderr")


def normalize_text(text):
    return re.sub(r'[：:\s]', '', text)

def count_total_messages(ts_path):
    try:
        with open(ts_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if "<message>" in line)
    except Exception as e:
        print(f"[ERREUR] Impossible de compter les messages : {e}")
        return 1  # Évite division par zéro

def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(__file__), filename)

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(__file__)

def custom_confirm(root, title, message):
    confirm_window = tk.Toplevel(root)
    confirm_window.title(title)
    confirm_window.geometry("400x150")
    confirm_window.iconbitmap(get_resource_path("logo_lemtronic.ico"))
    confirm_window.resizable(False, False)
    confirm_window.grab_set()
    confirm_window.transient(root)
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    confirm_width = 400
    confirm_height = 150
    x = root_x + (root_width // 2) - (confirm_width // 2)
    y = root_y + (root_height // 2) - (confirm_height // 2)
    confirm_window.geometry(f"{confirm_width}x{confirm_height}+{x}+{y}")
    label = tk.Label(confirm_window, text=message, wraplength=380, padx=10, pady=10)
    label.pack(pady=10)
    result = {'response': False}

    def on_ok():
        result['response'] = True
        confirm_window.destroy()

    def on_cancel():
        confirm_window.destroy()

    button_frame = tk.Frame(confirm_window)
    button_frame.pack(pady=5)
    Button(button_frame, text="OUI", command=on_ok, bootstyle="success-outline").pack(side="right", padx=10)
    Button(button_frame, text="NON", command=on_cancel, bootstyle="danger-outline").pack(side="left", padx=10)
    root.wait_window(confirm_window)
    return result['response']

class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        if self.text_widget.winfo_exists():
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)

    def flush(self):
        pass  # Nécessaire pour compatibilité avec sys.stdout


class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeltaQin Translate")
        self.root.geometry("1000x700")
        self.setup_ui()
        sys.stdout = ConsoleRedirector(self.console_text)
        sys.stderr = ConsoleRedirector(self.console_text)
        self.current_process = None
        self.was_cancelled = False
        self.dictionnaire_path = None

    def setup_ui(self):
        style = Style("superhero")
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        title_label = Label(main_frame, text="DeltaQin Translator", font=("Segoe UI", 18, "bold"))
        title_label.pack(pady=(0, 15))

        # Frame pour les boutons de sélection de fichier et de dictionnaire
        selection_frame = tk.Frame(main_frame)
        selection_frame.pack(fill="x", pady=(0, 10))

        # Bouton pour sélectionner un fichier
        self.label = Label(selection_frame, text="Fichier .qm à traduire :", font=("Segoe UI", 12))
        self.label.pack(side="left", padx=(0, 10))
        self.choose_btn = Button(selection_frame, text="Sélectionner un fichier", command=self.choose_file)
        self.choose_btn.pack(side="left")

        # Liste déroulante pour la langue (initialement cachée)
        self.lang_frame = tk.Frame(selection_frame)
        self.lang_label = Label(self.lang_frame, text="Langue cible :", font=("Segoe UI", 12))
        self.lang_label.pack(side="left", padx=(10, 5))
        self.lang_var = tk.StringVar()
        self.lang_dropdown = ttk.Combobox(self.lang_frame, textvariable=self.lang_var, state="readonly", width=15)
        self.lang_dropdown['values'] = list(LANGUAGES.keys())
        self.lang_dropdown.pack(side="left")
        self.lang_dropdown.bind("<<ComboboxSelected>>", self.on_language_selected)

        # Bouton pour sélectionner un dictionnaire (initialement caché)
        self.dict_frame = tk.Frame(selection_frame)
        dict_button = Button(self.dict_frame, text="Sélectionner un dictionnaire", command=self.select_dictionnaire)
        dict_button.pack(side="left")
        self.dict_label = Label(self.dict_frame, text="Aucun fichier sélectionné", font=("Segoe UI", 10))
        self.dict_label.pack(side="left", padx=(10, 0))
        self.dict_frame.pack_forget()
        self.lang_frame.pack_forget()

        self.confirm_btn = Button(main_frame, text="Confirmer et traduire", command=self.confirm_translation, state="disabled")
        self.confirm_btn.pack(pady=(10, 0))

        console_frame = tk.Frame(main_frame)
        console_frame.pack(fill="both", expand=True, pady=10)
        self.console_text = Text(console_frame, height=20, wrap='word', font=("Segoe UI Emoji", 10))
        self.console_text.pack(side="left", fill="both", expand=True)
        scroll = Scrollbar(console_frame, command=self.console_text.yview)
        scroll.pack(side='right', fill='y')
        self.console_text.config(yscrollcommand=scroll.set)

        self.status_var = tk.StringVar()
        self.status_var.set("Prêt")
        self.status_label = Label(main_frame, textvariable=self.status_var, anchor="w", font=("Segoe UI", 10), bootstyle="info")
        self.status_label.pack(fill="x", pady=(10, 5))

        progress_frame = tk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=(0, 10))
        progress_bar_frame = tk.Frame(progress_frame)
        progress_bar_frame.pack(expand=True, fill="both")
        self.eta_label = Label(progress_bar_frame, text="Temps restant : --:--", font=("Segoe UI", 10))
        self.eta_label.pack(anchor="center")
        self.progress = ttk.Progressbar(progress_bar_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0, 10))
        progress_label_frame = tk.Frame(progress_bar_frame)
        progress_label_frame.pack(fill="x")
        self.progress_label = tk.Label(progress_label_frame, text="", font=("Segoe UI", 10))
        self.progress_label.pack(side="right", padx=10)

        action_frame = tk.Frame(main_frame)
        action_frame.pack(pady=(5, 0))
        self.cancel_btn = Button(action_frame, text="Annuler", bootstyle="warning", command=self.cancel_translation)
        self.cancel_btn.pack(side="left", padx=5)
        self.quit_btn = Button(action_frame, text="Quitter", bootstyle="danger", command=self.safe_quit)
        self.quit_btn.pack(side="right", padx=5)
        self.info_btn = Button(action_frame, text="À propos", bootstyle="secondary", command=self.show_info)
        self.info_btn.pack(side="right", padx=5)
        self.open_folder_btn = Button(action_frame, text="Ouvrir dossier", bootstyle="success", command=self.open_output_folder)
        self.open_folder_btn.pack(side="right", padx=5)

        logo_path = get_resource_path("logo_lemtronic2.png")
        logo_image = tk.PhotoImage(file=logo_path)
        subsample_factor = 18
        logo_image = logo_image.subsample(subsample_factor, subsample_factor)
        logo_label = tk.Label(main_frame, image=logo_image)
        logo_label.image = logo_image
        logo_label.place(relx=1.0, x=15, y=-15, anchor="ne")
        logo_label.lift()

    def cancel_translation(self):
        self.was_cancelled = True
        self.status_var.set("Annulation demandée…")
        self.console_text.insert(tk.END, "\n[INFO] Annulation demandée par l'utilisateur.\n")
        self.console_text.see(tk.END)
        self.cancel_btn.config(state="disabled")


    def safe_quit(self):
        if hasattr(self, 'thread') and self.thread.is_alive():
            confirm = custom_confirm(self.root, "Confirmation", "Une traduction est en cours.\nVoulez-vous vraiment quitter ?")
            if not confirm:
                return
            self.was_cancelled = True
            self.root.after(1000, self.root.quit)  # Laisse le thread terminer proprement
        else:
            self.root.quit()


    def flash_status_label(self, times=6, interval=500, flash_color="#4BB543", default_color="#FFFFFF"):
        def toggle(count, is_on):
            if count <= 0:
                self.status_label.config(foreground=default_color)
                return
            self.status_label.config(foreground=flash_color if is_on else default_color)
            self.root.after(interval, toggle, count - 1, not is_on)
        toggle(times, True)

    def show_info(self):
        info_win = tk.Toplevel(self.root)
        info_win.title("À propos")
        info_win.geometry("500x800")
        info_win.transient(self.root)
        info_win.grab_set()
        info_win.iconbitmap("logo_lemtronic.ico")
        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        win_w = 400
        win_h = 500
        pos_x = root_x + (root_w // 2) - (win_w // 2)
        pos_y = root_y + (root_h // 2) - (win_h // 2)
        info_win.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        text_frame = tk.Frame(info_win)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        info_text = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Segoe UI", 10))
        info_text.pack(fill="both", expand=True)
        scrollbar.config(command=info_text.yview)
        content = (
            "DeltaQin Translator\n\n"
            "Ce programme permet de traduire automatiquement les fichiers .qm (format compilé Qt Linguist) depuis le chinois vers une langue cible (par défaut : le français).\n\n"
            "Fonctionnement :\n"
            "1. Décompilation du fichier .qm en .ts avec `lconvert.exe`\n"
            "2. Traduction automatique du fichier .ts avec l'API Google Translate\n"
            "3. Utilisation d'un dictionnaire local personnalisé (`dictionnaire_xx.py`) pour corriger ou améliorer certaines traductions\n"
            "4. Compilation du fichier .ts traduit en .qm avec `lrelease.exe`\n\n"
            "Les fichiers temporaires sont gérés automatiquement dans un dossier 'temp'.\n"
            "Les fichiers finaux sont enregistrés dans le dossier 'translated_files'.\n\n"
            "Auteur : T. LAVAL / Lemtronic SA\n"
            "Date : Stage mai / juillet 2025"
        )
        info_text.insert("1.0", content)
        info_text.config(state="disabled")
        btn_close = Button(info_win, text="Fermer", bootstyle="primary", command=info_win.destroy)
        btn_close.pack(pady=10)

    def choose_file(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = filedialog.askopenfilename(
            initialdir=base_dir,
            filetypes=[("QM Files", "*.qm")],
            title="Sélectionnez un fichier .qm"
        )
        if file_path:
            self.selected_file = file_path
            self.lang_frame.pack(side="left", padx=(10, 0))
            self.status_var.set("Sélectionnez la langue cible.")
            self.confirm_btn.config(state="normal")

    def on_language_selected(self, event=None):
        if hasattr(self, 'selected_file') and self.lang_var.get():
            self.dict_frame.pack(side="left", padx=(10, 0))

    def select_dictionnaire(self):
        dico_dir = get_resource_path("dico")
        file_path = filedialog.askopenfilename(
            initialdir=dico_dir,
            filetypes=[("Fichier Python", "*.py")],
            title="Sélectionnez un dictionnaire"
        )
        if file_path:
            self.dictionnaire_path = file_path
            self.dict_label.config(text=os.path.basename(file_path))
        else:
            self.dictionnaire_path = None
            self.dict_label.config(text="Aucun fichier sélectionné")

    def confirm_translation(self):
        if hasattr(self, 'selected_file') and self.lang_var.get():
            selected_name = self.lang_var.get()
            lang = LANGUAGES.get(selected_name)
            if not lang:
                self.console_text.insert(tk.END, "❌ Veuillez sélectionner une langue valide.\n")
                return
            confirm = custom_confirm(self.root, "Confirmation",
                                    f"Voulez-vous traduire le fichier en {lang.upper()} ?\n\n{self.selected_file}")
            if confirm:
                self.console_text.delete("1.0", tk.END)
                thread = threading.Thread(target=self.run_translation, args=(self.selected_file, lang))
                thread.start()
            else:
                self.status_var.set("Traduction annulée par l'utilisateur.")
        else:
            self.status_var.set("Veuillez sélectionner un fichier et une langue.")
    
    def update_progress_gui(self, progress, eta_seconds, message_count, total_messages):
        self.progress["value"] = progress
        self.progress_label.config(text=f"{progress}%")
        if eta_seconds is not None:
            eta_min, eta_sec = divmod(eta_seconds, 60)
            self.eta_label.config(text=f"Temps restant : {eta_min:02}:{eta_sec:02}")
        else:
            self.eta_label.config(text="Temps restant : --:--")


    def run_translation(self, input_qm_file, target_lang):
        try:
            self.cancel_btn.config(state="normal")
            self.was_cancelled = False
            self.status_var.set("Traduction en cours…")

            # Timestamp pour les noms de fichiers
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_ts_filename = f'deltaqin_{target_lang}_{timestamp}.ts'
            output_qm_filename = f'deltaqin_{target_lang}_{timestamp}.qm'
            base_name = os.path.splitext(os.path.basename(input_qm_file))[0]

            # Dossiers
            qttools_dir = os.path.join(BASE_DIR, "qttools")
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

            # Chargement du dictionnaire depuis un fichier .txt si fourni
            if self.dictionnaire_path:
                try:
                    spec = importlib.util.spec_from_file_location("manual_dict_module", self.dictionnaire_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    # On attend un attribut 'manual_dict' dans le fichier
                    if hasattr(module, "manual_dict"):
                        manual_dict = module.manual_dict
                        print(f"📘 Dictionnaire Python chargé depuis '{self.dictionnaire_path}' ({len(manual_dict)} entrées)")
                    else:
                        print(f"⚠️ Le fichier '{self.dictionnaire_path}' ne contient pas de variable 'manual_dict'")
                except Exception as e:
                    print(f"❌ Erreur de lecture du dictionnaire Python : {e}")
            else:
                print(f"📙 Aucun dictionnaire fourni, traduction automatique uniquement")

            total_messages = count_total_messages(input_ts_file)

            tree = ET.parse(input_ts_file)
            root = tree.getroot()
            translator = GoogleTranslator(source='zh-CN', target=target_lang)
            alpha = 0.2
            ema_time_per_msg = None
            start_time = time.time()
            message_count = 0

            for message in root.iter('message'):
                if self.was_cancelled:
                    print("\n[INFO] Traduction interrompue par l'utilisateur.")
                    self.status_var.set("Traduction annulée.")
                    self.progress["value"] = 0
                    self.progress_label.config(text="")
                    self.eta_label.config(text="Temps restant : --:--")
                    return

                message_count += 1
                now = time.time()
                elapsed = now - start_time

                current_avg = elapsed / message_count
                if ema_time_per_msg is None:
                    ema_time_per_msg = current_avg
                else:
                    ema_time_per_msg = alpha * current_avg + (1 - alpha) * ema_time_per_msg

                eta_seconds = int(ema_time_per_msg * (total_messages - message_count))

                progress = int((message_count / total_messages) * 100)
                self.root.after(0, self.update_progress_gui, progress, eta_seconds, message_count, total_messages)

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

            if self.was_cancelled:
                self.was_cancelled = False
                return

            self.status_var.set("Traduction terminée avec succès.")
            self.flash_status_label(times=15, interval=800, flash_color="#00FF00", default_color="#FFFFFF")
            self.progress_label.config(text="")
            self.progress["value"] = 0
            self.eta_label.config(text="Temps restant : --:--")
            self.open_output_folder()

        except Exception as e:
            self.status_var.set("Erreur d'exécution.")
            self.root.after(0, functools.partial(
                Messagebox.show_error,
                "Erreur",
                f"Erreur d'exécution du script :\n{e}"
            ))

    def open_output_folder(self):
        base_path = get_base_path()
        output_dir = os.path.join(base_path, "translated_files")
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            self.root.after(0, lambda: Messagebox.show_error("Erreur", f"Dossier non trouvé :\n{output_dir}"))

if __name__ == "__main__":
    root = Window(themename="superhero")
    root.iconbitmap(get_resource_path("logo_lemtronic.ico"))
    app = TranslatorApp(root)
    root.mainloop()
