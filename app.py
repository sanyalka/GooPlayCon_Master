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
        self.title("GooPlayCon Master")
        self.geometry("1080x780")
        self.minsize(980, 700)

        self.service_json = tk.StringVar()
        self.package_name = tk.StringVar()
        self.source_locale = tk.StringVar(value="en-US")
        self.master_folder = tk.StringVar()
        self.image_type = tk.StringVar(value=IMAGE_TYPES[1])
        self.status_text = tk.StringVar(value="Готов к работе")

        self._action_buttons: list[ttk.Button] = []
        self._locales: list[str] = []

        self._init_style()
        self._build_ui()

    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#4b5563")
        style.configure("Card.TLabelframe", padding=12)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Action.TButton", padding=8)

    def _build_ui(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="GooPlayCon Master", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Массовое управление листингами и изображениями Google Play Console",
            style="SubHeader.TLabel",
        ).pack(anchor="w")

        top = ttk.Frame(root)
        top.pack(fill="x", pady=(0, 10))

        auth_card = ttk.LabelFrame(top, text="Подключение", style="Card.TLabelframe")
        auth_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        listing_card = ttk.LabelFrame(top, text="Локализации", style="Card.TLabelframe")
        listing_card.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._entry_row(auth_card, "Service account JSON", self.service_json, pick_file=True)
        self._entry_row(auth_card, "Package name", self.package_name)
        ttk.Label(
            auth_card,
            text="Данные не хранятся в приложении: настройки берутся из полей UI,\nа JSON экспорт/импорт сохраняется только в выбранный вами файл.",
            style="SubHeader.TLabel",
        ).pack(anchor="w", pady=(8, 0))

        self._entry_row(listing_card, "Исходная локаль", self.source_locale)
        tools = ttk.Frame(listing_card)
        tools.pack(fill="x", pady=(4, 6))
        ttk.Button(tools, text="Загрузить локали с Google Play", command=self.load_locales_from_play).pack(side="left")
        ttk.Button(tools, text="Выбрать все", command=self.select_all_locales).pack(side="left", padx=6)
        ttk.Button(tools, text="Снять выбор", command=self.clear_locales_selection).pack(side="left")

        self.locale_list = tk.Listbox(listing_card, selectmode=tk.MULTIPLE, height=8)
        self.locale_list.pack(fill="both", expand=True)

        media_card = ttk.LabelFrame(root, text="Изображения", style="Card.TLabelframe")
        media_card.pack(fill="x", pady=(0, 10))

        row = ttk.Frame(media_card)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Тип изображений", width=32).pack(side="left")
        ttk.Combobox(row, textvariable=self.image_type, values=IMAGE_TYPES, state="readonly").pack(
            side="left", fill="x", expand=True
        )

        row2 = ttk.Frame(media_card)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Мастер-папка скриншотов", width=32).pack(side="left")
        ttk.Entry(row2, textvariable=self.master_folder).pack(side="left", fill="x", expand=True)
        ttk.Button(row2, text="Выбрать", command=self._pick_folder).pack(side="left", padx=(8, 0))

        actions_card = ttk.LabelFrame(root, text="Операции", style="Card.TLabelframe")
        actions_card.pack(fill="x", pady=(0, 10))
        grid = ttk.Frame(actions_card)
        grid.pack(fill="x")

        self._add_action_button(grid, "Копировать тексты", self.copy_texts, 0, 0)
        self._add_action_button(grid, "Загрузить изображения", self.upload_images, 0, 1)
        self._add_action_button(grid, "Удалить изображения", self.delete_images, 0, 2)
        self._add_action_button(grid, "Экспорт локализаций в JSON", self.export_json, 1, 0)
        self._add_action_button(grid, "Импорт локализаций из JSON", self.import_json, 1, 1)

        for i in range(3):
            grid.columnconfigure(i, weight=1)

        progress_card = ttk.LabelFrame(root, text="Прогресс загрузки изображений", style="Card.TLabelframe")
        progress_card.pack(fill="x", pady=(0, 10))
        self.upload_progress = ttk.Progressbar(progress_card, orient="horizontal", mode="determinate", maximum=100)
        self.upload_progress.pack(fill="x")
        self.upload_progress_label = ttk.Label(progress_card, text="Пока нет активной загрузки")
        self.upload_progress_label.pack(anchor="w", pady=(6, 0))

        log_card = ttk.LabelFrame(root, text="Журнал", style="Card.TLabelframe")
        log_card.pack(fill="both", expand=True)
        self.log = tk.Text(log_card, height=14, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0", relief="flat")
        self.log.pack(fill="both", expand=True)

        status = ttk.Frame(root)
        status.pack(fill="x", pady=(10, 0))
        ttk.Label(status, textvariable=self.status_text).pack(anchor="w")

    def _entry_row(self, parent, label, var, pick_file=False):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, width=32).pack(side="left")
        ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
        if pick_file:
            ttk.Button(row, text="Выбрать", command=self._pick_file).pack(side="left", padx=(8, 0))

    def _add_action_button(self, parent, text, command, r, c):
        b = ttk.Button(parent, text=text, command=command, style="Action.TButton")
        b.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
        self._action_buttons.append(b)

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

    def _selected_locales(self):
        idx = self.locale_list.curselection()
        return [self.locale_list.get(i) for i in idx]

    def _set_busy(self, busy: bool, text: str):
        self.status_text.set(text)
        state = "disabled" if busy else "normal"
        for b in self._action_buttons:
            b.config(state=state)

    def _run_bg(self, fn, action_title: str):
        def worker():
            self.after(0, lambda: self._set_busy(True, f"Выполняется: {action_title}..."))
            try:
                fn()
                self.after(0, lambda: self._set_busy(False, f"Готово: {action_title}"))
            except Exception as e:
                self.after(0, lambda: self._set_busy(False, "Ошибка операции"))
                self._log(f"Ошибка: {e}")
                self.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _log(self, text: str):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def _reset_upload_progress(self):
        self.upload_progress["value"] = 0
        self.upload_progress_label.configure(text="Пока нет активной загрузки")

    def _update_upload_progress(self, done: int, total: int, locale: str, filename: str):
        percent = (done / total * 100) if total else 100
        self.upload_progress["value"] = percent
        self.upload_progress_label.configure(text=f"{done}/{total} • {locale} • {filename}")

    def load_locales_from_play(self):
        def task():
            c = self._client()
            locales_data = c.list_filled_locales()
            locales = sorted(locales_data.keys())
            self._locales = locales

            def fill_listbox():
                self.locale_list.delete(0, "end")
                for loc in locales:
                    self.locale_list.insert("end", loc)
                self._log(f"Загружены локали из Google Play: {locales}")

            self.after(0, fill_listbox)

        self._run_bg(task, "Загрузка локалей")

    def select_all_locales(self):
        self.locale_list.select_set(0, "end")

    def clear_locales_selection(self):
        self.locale_list.selection_clear(0, "end")

    def copy_texts(self):
        def task():
            c = self._client()
            locales = self._selected_locales()
            self._log(f"Копирование текстов {self.source_locale.get()} -> {locales}")
            result = c.copy_listing_text(self.source_locale.get().strip(), locales)
            self._log(f"Готово: {result}")

        self._run_bg(task, "Копирование текстов")

    def upload_images(self):
        def task():
            c = self._client()
            locales = self._selected_locales()
            self.after(0, self._reset_upload_progress)
            self._log(f"Загрузка изображений ({self.image_type.get()}) из {self.master_folder.get()}")

            def progress(done: int, total: int, locale: str, filename: str):
                self.after(0, lambda: self._update_upload_progress(done, total, locale, filename))

            result = c.upload_images_from_master_folder(
                image_type=self.image_type.get(),
                master_folder=self.master_folder.get().strip(),
                target_locales=locales,
                progress_callback=progress,
            )
            self._log(f"Готово: {result}")

        self._run_bg(task, "Загрузка изображений")

    def delete_images(self):
        if not messagebox.askyesno("Подтверждение", "Удалить все изображения выбранного типа в выбранных локалях?"):
            return

        def task():
            c = self._client()
            locales = self._selected_locales()
            self._log(f"Удаление изображений ({self.image_type.get()}) в {locales}")
            result = c.delete_all_images(self.image_type.get(), locales)
            self._log(f"Готово: {result}")

        self._run_bg(task, "Удаление изображений")

    def export_json(self):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            title="Сохранить локализации в JSON",
        )
        if not save_path:
            return

        def task():
            c = self._client()
            count = c.export_listings_to_json(save_path)
            self._log(f"Экспортировано локалей: {count}. Файл: {save_path}")

        self._run_bg(task, "Экспорт в JSON")

    def import_json(self):
        json_path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            title="Выберите JSON для импорта",
        )
        if not json_path:
            return
        if not messagebox.askyesno("Подтверждение", "Обновить локализации в Google Play из выбранного JSON?"):
            return

        def task():
            c = self._client()
            result = c.import_listings_from_json(json_path)
            self._log(f"Обновлено локалей: {len(result)}. Детали: {result}")

        self._run_bg(task, "Импорт из JSON")


if __name__ == "__main__":
    App().mainloop()
