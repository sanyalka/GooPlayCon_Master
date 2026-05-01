import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gpc_tool import GooglePlayConsoleTool

IMAGE_TYPES = [
    "featureGraphic",
    "phoneScreenshots",
    "sevenInchScreenshots",
    "tenInchScreenshots",
    "tvScreenshots",
    "wearScreenshots",
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Google Play Console Master")
        self.geometry("900x700")

        self.service_json = tk.StringVar()
        self.package_name = tk.StringVar()
        self.source_locale = tk.StringVar(value="en-US")
        self.target_locales = tk.StringVar(value="ru-RU,uk-UA")
        self.master_folder = tk.StringVar()
        self.image_type = tk.StringVar(value=IMAGE_TYPES[1])

        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        def row(label, var, browse=False):
            r = ttk.Frame(frm)
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=label, width=36).pack(side="left")
            ttk.Entry(r, textvariable=var).pack(side="left", fill="x", expand=True)
            if browse:
                ttk.Button(r, text="Выбрать", command=self._pick_file).pack(side="left", padx=4)

        row("Service account JSON", self.service_json, browse=True)
        row("Package name (например: com.example.app)", self.package_name)
        row("Исходная локаль (пример: en-US)", self.source_locale)
        row("Целевые локали через запятую", self.target_locales)

        r = ttk.Frame(frm)
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Тип изображений", width=36).pack(side="left")
        ttk.Combobox(r, textvariable=self.image_type, values=IMAGE_TYPES).pack(side="left", fill="x", expand=True)

        r2 = ttk.Frame(frm)
        r2.pack(fill="x", pady=4)
        ttk.Label(r2, text="Мастер-папка изображений", width=36).pack(side="left")
        ttk.Entry(r2, textvariable=self.master_folder).pack(side="left", fill="x", expand=True)
        ttk.Button(r2, text="Выбрать папку", command=self._pick_folder).pack(side="left", padx=4)

        actions = ttk.Frame(frm)
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="Копировать тексты в локали", command=self.copy_texts).pack(fill="x", pady=4)
        ttk.Button(actions, text="Загрузить изображения из мастер-папки", command=self.upload_images).pack(fill="x", pady=4)
        ttk.Button(actions, text="Удалить ВСЕ изображения выбранного типа", command=self.delete_images).pack(fill="x", pady=4)

        ttk.Label(frm, text="Лог выполнения").pack(anchor="w")
        self.log = tk.Text(frm, height=20)
        self.log.pack(fill="both", expand=True)

    def _pick_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if path:
            self.service_json.set(path)

    def _pick_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.master_folder.set(path)

    def _client(self):
        return GooglePlayConsoleTool(self.service_json.get().strip(), self.package_name.get().strip())

    def _locales(self):
        return [x.strip() for x in self.target_locales.get().split(",") if x.strip()]

    def _run_bg(self, fn):
        def worker():
            try:
                fn()
            except Exception as e:
                self._log(f"Ошибка: {e}")
                messagebox.showerror("Ошибка", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _log(self, text: str):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def copy_texts(self):
        def task():
            c = self._client()
            locales = self._locales()
            self._log(f"Копирование текстов {self.source_locale.get()} -> {locales}")
            result = c.copy_listing_text(self.source_locale.get().strip(), locales)
            self._log(f"Готово: {result}")

        self._run_bg(task)

    def upload_images(self):
        def task():
            c = self._client()
            locales = self._locales()
            self._log(f"Загрузка изображений ({self.image_type.get()}) из {self.master_folder.get()}")
            result = c.upload_images_from_master_folder(
                image_type=self.image_type.get(),
                master_folder=self.master_folder.get().strip(),
                target_locales=locales,
            )
            self._log(f"Готово: {result}")

        self._run_bg(task)

    def delete_images(self):
        if not messagebox.askyesno("Подтверждение", "Удалить все изображения выбранного типа в целевых локалях?"):
            return

        def task():
            c = self._client()
            locales = self._locales()
            self._log(f"Удаление изображений ({self.image_type.get()}) в {locales}")
            result = c.delete_all_images(self.image_type.get(), locales)
            self._log(f"Готово: {result}")

        self._run_bg(task)


if __name__ == "__main__":
    App().mainloop()
