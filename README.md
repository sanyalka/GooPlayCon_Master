# GooPlayCon Master

Инструмент для работы со страницей приложения в **Google Play Console**:

- массовое копирование текстов листинга (название, короткое и полное описание) между локализациями;
- массовая загрузка скриншотов из мастер-папки со структурой `язык/1n.jpg, 2n.jpg`;
- массовое удаление изображений выбранного типа;
- экспорт всех заполненных локалей в один JSON-файл для редактирования;
- импорт этого JSON обратно в Google Play Console;
- загрузка списка целевых локалей прямо из Google Play (кнопка в UI).

## Где хранятся данные приложения?

- Само приложение **не ведет базу данных** и не сохраняет ваши листинги локально.
- Тексты и изображения хранятся в Google Play Console (на стороне Google).
- Локально сохраняются только файлы, которые вы сами выбираете:
  - JSON экспорт/импорт,
  - мастер-папка со скриншотами,
  - JSON-ключ service account.

## Что такое Service Account JSON?

Это JSON-файл с ключом сервисного аккаунта Google Cloud. Через него приложение получает API-доступ к Google Play Console от имени этого аккаунта.

Как получить:
1. Создайте Service Account в Google Cloud.
2. В Google Play Console откройте `Setup -> API access`.
3. Свяжите сервисный аккаунт с Play Console и выдайте ему права на нужное приложение.
4. Скачайте JSON-ключ и укажите его в приложении.

## Структура проекта

- `app.py` — GUI-приложение.
- `gpc_tool.py` — слой работы с Google Play Developer API.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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

## Формат JSON экспорта/импорта

```json
{
  "packageName": "com.example.app",
  "listings": {
    "en-US": {
      "title": "App title",
      "short_description": "Short description",
      "full_description": "Full description"
    }
  }
}
```

Допускается импорт как `short_description/full_description`, так и API-формат `shortDescription/fullDescription`.

## Важно

Приложение использует Android Publisher API (`edits`). Перед массовыми изменениями рекомендуется протестировать на тестовом приложении.
