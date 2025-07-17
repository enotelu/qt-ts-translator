import os
import tkinter as tk
from tkinter import filedialog
from ttkbootstrap import Window, Button, Text, Label, Scrollbar, Style
from ttkbootstrap.dialogs import Messagebox
import subprocess
import threading
import datetime
import sys

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
        self.root.geometry("800x600")
        self.setup_ui()
        self.current_process = None
        self.was_cancelled = False

    def setup_ui(self):
        style = Style("superhero")
        main_frame = tk.Frame(self.root, padx=20, pady=20, bg="#2b2b2b")
        main_frame.pack(fill="both", expand=True)

        title_label = Label(main_frame, text="DeltaQin Translator", font=("Segoe UI", 18, "bold"))
        title_label.pack(pady=(0, 15))

        file_frame = tk.Frame(main_frame)
        file_frame.pack(fill="x", pady=(0, 10))

        self.label = Label(file_frame, text="Fichier .ts à traduire :", font=("Segoe UI", 12))
        self.label.pack(side="left", padx=(0, 10))

        self.choose_btn = Button(file_frame, text="Sélectionner un fichier", command=self.choose_file)
        self.choose_btn.pack(side="left")

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


    def safe_quit(self):
        if self.current_process and self.current_process.poll() is None:
            confirm = custom_confirm(self.root, "Confirmation", "Une traduction est en cours.\nVoulez-vous vraiment quitter ?")
            if not confirm:
                return  # L'utilisateur a cliqué sur NON

            try:
                self.was_cancelled = True  # Pour éviter le popup erreur
                self.current_process.terminate()
            except Exception as e:
                print(f"Erreur lors de l'arrêt du processus : {e}")
            finally:
                self.root.after(200, self.root.quit)
        else:
            self.root.quit()



    def show_info(self):
        info_win = tk.Toplevel(self.root)
        info_win.title("À propos")
        info_win.geometry("400x500")
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
            "Ce programme permet de traduire du chinois au français automatiquement les fichiers .qm décompiler en .ts\n\n"
            "Fonctionnement :\n"
            "- Utilise `translate.py` et l'API GoogleTranslate pour traduire le fichier .ts\n"
            "- Utilise un dictionnaire custom (`dictionnaire.py`)\n"
            "- Génère un nouveau fichier .ts traduit, et un fichier .qm compilé\n\n"
            "Auteur : T. LAVAL / Lemtronic SA"
        )
        info_text.insert("1.0", content)
        info_text.config(state="disabled")

        btn_close = Button(info_win, text="Fermer", bootstyle="primary", command=info_win.destroy)
        btn_close.pack(pady=10)

    def choose_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("TS Files", "*.ts")])
        if file_path:
            confirm = custom_confirm(self.root, "Confirmation", f"Voulez-vous traduire ce fichier ?\n\n{file_path}")
            if confirm:
                self.console_text.delete("1.0", tk.END)
                thread = threading.Thread(target=self.run_translation, args=(file_path,))
                thread.start()
            else:
                self.status_var.set("Traduction annulée par l'utilisateur.")

    def run_translation(self, ts_path):
        try:
            self.status_var.set("Traduction en cours…")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_ts = f"deltaqin_traduit_{timestamp}.ts"
            output_qm = f"deltaqin_fr_{timestamp}.qm"
            script_path = get_resource_path("translate.py")

            python_path = os.path.join(os.environ.get('VIRTUAL_ENV', ''), 'Scripts', 'python.exe')
            if not os.path.exists(python_path):
                python_path = "python"

            command = [python_path, script_path, ts_path, output_ts, output_qm]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       bufsize=1, universal_newlines=True, encoding="utf-8",
                                       errors="replace", creationflags=subprocess.CREATE_NO_WINDOW)

            self.current_process = process

            for line in iter(process.stdout.readline, ''):
                if line:
                    self.console_text.insert(tk.END, line)
                    self.console_text.see(tk.END)
                    self.root.update()

            process.stdout.close()
            process.wait()
            self.current_process = None
            self.cancel_btn.config(state="disabled")

            if self.was_cancelled:
                self.was_cancelled = False
                return

            if process.returncode == 0:
                self.status_var.set("Traduction terminée avec succès.")
                self.open_output_folder()
            else:
                self.status_var.set("Erreur lors de la traduction.")
                self.root.after(0, lambda: Messagebox.show_error("Erreur", "Erreur durant la traduction."))

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