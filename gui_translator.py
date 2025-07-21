import os
import tkinter as tk
from tkinter import filedialog
from ttkbootstrap import Window, Button, Text, Label, Scrollbar, Style
from ttkbootstrap.dialogs import Messagebox
import subprocess
import threading
import datetime
import sys
from tkinter import ttk

# Langues supportées : nom affiché → code Google Translate
LANGUAGES = {
    "Français": "fr",
    "Anglais": "en",
    "Allemand": "de",
    "Italien": "it",
    "Espagnol": "es",
    "Japonais": "ja"
}

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

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeltaQin Translate")
        self.root.geometry("1000x700")
        self.setup_ui()
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
        self.dict_button = Button(self.dict_frame, text="Sélectionner un dictionnaire", command=self.select_dictionnaire)
        self.dict_button.pack(side="left")

        self.dict_label = Label(self.dict_frame, text="Aucun fichier sélectionné", font=("Segoe UI", 10))
        self.dict_label.pack(side="left", padx=(10, 0))
        self.dict_frame.pack_forget()


        self.lang_frame.pack_forget()

        self.confirm_btn = Button(main_frame, text="Confirmer et traduire", bootstyle="success", command=self.confirm_translation, state="disabled")
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


    def reset_ui_to_initial_state(self):
        # Réinitialisation des éléments visuels
        self.status_var.set("Prêt")

        # Boutons et champs
        self.choose_btn.config(state='normal')
        self.confirm_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')

        # Masquer les éléments
        self.lang_frame.pack_forget()
        self.dict_frame.pack_forget()


    def cancel_translation(self):
        if self.current_process and self.current_process.poll() is None:
            try:
                self.was_cancelled = True
                self.current_process.terminate()
                self.status_var.set("Traduction annulée par l'utilisateur.")
                self.console_text.insert(tk.END, "\n[INFO] Traduction annulée par l'utilisateur.\n")
                self.console_text.see(tk.END)
            except Exception as e:
                self.console_text.insert(tk.END, f"\n[ERREUR] Impossible d'annuler : {e}\n")
            finally:
                self.cancel_btn.config(state="disabled")
                self.reset_ui_to_initial_state()

    def safe_quit(self):
        if self.current_process and self.current_process.poll() is None:
            confirm = custom_confirm(self.root, "Confirmation", "Une traduction est en cours.\nVoulez-vous vraiment quitter ?")
            if not confirm:
                return
            try:
                self.was_cancelled = True
                self.current_process.terminate()
            except Exception as e:
                print(f"Erreur lors de l'arrêt du processus : {e}")
            finally:
                self.root.after(200, self.root.quit)
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
        info_win.geometry("900x800")
        info_win.transient(self.root)
        info_win.grab_set()
        info_win.iconbitmap("logo_lemtronic.ico")
        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        win_w = 520
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
            self.status_var.set("Sélectionnez un dictionnaire.")

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
            self.status_var.set("Confirmer pour démarrer la traduction.")
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
                                    f"Voulez-vous traduire le fichier en {selected_name} ?\n\n{self.selected_file}")
            if confirm:
                self.console_text.delete("1.0", tk.END)
                thread = threading.Thread(target=self.run_translation, args=(self.selected_file, lang))
                thread.start()
            else:
                self.status_var.set("Traduction annulée par l'utilisateur.")
        else:
            self.status_var.set("Veuillez sélectionner un fichier et une langue.")

    def run_translation(self, ts_path, lang="fr"):
        try:
            self.cancel_btn.config(state="normal")
            self.was_cancelled = False
            self.status_var.set("Traduction en cours…")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_ts = f"deltaqin_{lang}_{timestamp}.ts"
            output_qm = f"deltaqin_{lang}_{timestamp}.qm"
            script_path = get_resource_path("translate.py")
            python_path = os.path.join(os.environ.get('VIRTUAL_ENV', ''), 'Scripts', 'python.exe')
            if not os.path.exists(python_path):
                python_path = sys.executable
            command = [python_path, script_path, ts_path, lang]
            if self.dictionnaire_path:
                command.append(self.dictionnaire_path)
            else:
                base_path = get_base_path()
                dict_path = os.path.join(base_path, f"dictionnaire_{lang}.py")
                if os.path.isfile(dict_path):
                    command.append(dict_path)

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.current_process = process

            def read_stdout():
                self.progress_label.config(text="0 %")
                for line in iter(process.stdout.readline, ''):
                    if line:
                        self.console_text.insert(tk.END, line)
                        self.console_text.see(tk.END)
                        self.root.update()
                process.stdout.close()

            def read_stderr():
                for line in iter(process.stderr.readline, ''):
                    if "[PROGRESS]" in line:
                        try:
                            percent = int(line.strip().split()[1])
                            self.progress["value"] = percent
                            self.progress_label.config(text=f"{percent} %")
                        except:
                            pass
                    elif "[ETA_SECONDS]" in line:
                        try:
                            seconds = int(line.strip().split()[1])
                            minutes, sec = divmod(seconds, 60)
                            self.eta_label.config(text=f"Temps restant : {minutes} min {sec} s")
                        except:
                            pass
                    self.root.update()

            t_out = threading.Thread(target=read_stdout, daemon=True)
            t_err = threading.Thread(target=read_stderr, daemon=True)
            t_out.start()
            t_err.start()

            process.wait()
            t_out.join()
            t_err.join()

            self.current_process = None
            self.cancel_btn.config(state="disabled")

            if self.was_cancelled:
                self.was_cancelled = False
                return

            if process.returncode == 0:
                self.status_var.set("Traduction terminée avec succès.")
                self.flash_status_label(times=15, interval=800, flash_color="#00FF00", default_color="#FFFFFF")
                self.progress_label.config(text="")
                self.progress["value"] = 0
                self.open_output_folder()
                self.reset_ui_to_initial_state()
            else:
                self.status_var.set("Erreur lors de la traduction.")
                self.root.after(0, lambda: Messagebox.show_error("Erreur", "Erreur durant la traduction."))
                self.reset_ui_to_initial_state()
        except Exception as e:
            self.status_var.set("Erreur d'exécution.")
            self.root.after(0, lambda: Messagebox.show_error("Erreur", f"Erreur d'exécution du script :\n{e}"))

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
