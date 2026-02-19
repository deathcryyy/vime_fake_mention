<div align="center">

# 🎭 VimeMention

**Инструмент для отправки постов с изменённым упоминанием на [forum.vimeworld.com](https://forum.vimeworld.com)**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)]()

<br>

> Визуально отображает `@nastya`, но уведомление получает реальный пользователь `@okssi`

</div>

---

## ⚙️ Как это работает

Форум VimeWorld работает на движке **Invision Community (IPS)**. Упоминания устроены так:

```html
<a data-mentionid="USER_ID" href="/profile/USER_ID-username/">
  @ОтображаемоеИмя
</a>
```

Атрибут `data-mentionid` определяет **кому придёт уведомление**, а текст внутри тега — **что видят все**. Инструмент использует это, чтобы подставить любой отображаемый ник.

---

## 🚀 Быстрый старт

### Вариант 1 — Запуск через `run.bat` (рекомендуется)

> Требуется установленный [Python 3.8+](https://python.org) с галочкой **"Add Python to PATH"**

1. Скачай репозиторий (кнопка **Code → Download ZIP**)
2. Распакуй архив
3. Дважды кликни **`run.bat`**

Скрипт сам установит зависимости и запустит программу.

---

### Вариант 2 — Сборка в EXE

1. Дважды кликни **`build.bat`**
2. Подожди ~2 минуты
3. Готовый файл: `dist\VimeMention.exe`

После сборки `.exe` можно запускать на любом Windows без Python.

---

### Вариант 3 — Ручной запуск

```bash
git clone https://github.com/USERNAME/VimeMention.git
cd VimeMention
pip install -r requirements.txt
python src/gui.py
```

---

## 📖 Использование

| Шаг | Действие |
|:---:|----------|
| **①** | Введи логин и пароль → нажми **Войти** |
| **②** | Вставь URL темы или введи поисковый запрос → нажми **Найти** → кликни на тему |
| **③** | Введи ник пользователя → нажми **Найти** → кликни на него |
| **④** | Введи фейковое имя и текст поста |
| **⑤** | Нажми **ОТПРАВИТЬ ПОСТ** и подтверди |

---

## 📁 Структура проекта

```
VimeMention/
├── src/
│   └── gui.py          # Основной файл с GUI (tkinter)
├── run.bat             # ▶ Запуск одним кликом
├── build.bat           # 📦 Сборка EXE одним кликом
├── requirements.txt    # Зависимости Python
├── .gitignore
├── LICENSE
└── README.md
```

---

## 📦 Зависимости

| Пакет | Назначение |
|-------|------------|
| `requests` | HTTP запросы к форуму |
| `beautifulsoup4` | Парсинг HTML страниц |
| `pyinstaller` | Сборка в EXE *(только для `build.bat`)* |

---

## ⚠️ Дисклеймер

Инструмент создан в **образовательных целях** для изучения работы веб-форумов и HTML-структуры IPS. Используй ответственно и в соответствии с [правилами форума VimeWorld](https://vime.one/rules).

---

<div align="center">

Сделано для VimeWorld

</div>
