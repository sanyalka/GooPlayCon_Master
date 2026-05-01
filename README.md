# GooPlayCon Master

Инструмент для работы со страницей приложения в **Google Play Console**:

- массовое копирование текстов листинга (название, короткое и полное описание) между локализациями;
- массовая загрузка скриншотов из мастер-папки со структурой `язык/1n.jpg, 2n.jpg`;
- массовое удаление изображений выбранного типа;
- простой графический интерфейс на Tkinter.

## Структура проекта

- `app.py` — GUI-приложение.
- `gpc_tool.py` — слой работы с Google Play Developer API.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Подготовка доступа к Google Play API

1. Создайте Service Account в Google Cloud.
2. Выдайте ему доступ в Google Play Console (Setup → API access).
3. Скачайте JSON-ключ.

## Запуск

```bash
python app.py
```

## Формат мастер-папки со скриншотами

```text
master_screenshots/
  en-US/
    1n.jpg
    2n.jpg
  ru-RU/
    1n.jpg
    2n.jpg
```

Поддерживаются расширения: `jpg`, `jpeg`, `png`, `webp`.

## Важно

Приложение использует Android Publisher API (`edits`). Перед массовыми изменениями рекомендуется протестировать на тестовом приложении.
