# Plugin Development Guide

## Обзор

RealEstatesAntiFraud использует модульную архитектуру на основе плагинов. Это руководство описывает, как создавать и интегрировать плагины различных типов.

> 📘 **Формальная спецификация**: См. [PLUGIN_SPEC.md](PLUGIN_SPEC.md) для полной спецификации манифеста плагина v1.0 с JSON Schema и примерами валидации.

## Типы плагинов

1. **Source Plugins** - Источники данных (скрейперы, API коннекторы)
2. **Processing Plugins** - Обработка и обогащение данных
3. **Detection Plugins** - Детекция мошенничества
4. **Search Plugins** - Поиск и индексация
5. **Display Plugins** - Отображение и форматирование

## Структура плагина

### Базовая структура директории

```
plugin-{type}-{name}/
├── plugin.yaml              # Манифест плагина (обязательно)
├── __init__.py             # Python package
├── main.py                 # Главный класс плагина
├── config.yaml             # Конфигурация по умолчанию
├── requirements.txt        # Python зависимости
├── README.md               # Документация плагина
├── CHANGELOG.md            # История изменений
├── LICENSE                 # Лицензия
├── tests/                  # Тесты
│   ├── __init__.py
│   ├── test_main.py
│   └── fixtures/
├── assets/                 # Статические файлы (иконки, etc)
│   └── icon.png
└── examples/               # Примеры использования
    └── example_usage.py
```

### Манифест плагина (plugin.yaml)

```yaml
# Базовая информация
id: plugin-source-example
name: Example Source Plugin
version: 1.0.0
type: source  # source | processing | detection | search | display
api_version: 1.0

# Метаданные
description: |
  Detailed description of what the plugin does
author:
  name: Your Name
  email: your.email@example.com
  url: https://yourwebsite.com

# Лицензия
license: MIT
repository: https://github.com/username/plugin-source-example

# Зависимости
dependencies:
  core_version: ">=1.0.0"
  python_version: ">=3.10"
  plugins:
    - plugin-processing-normalizer: ">=1.0.0"

# Конфигурация
config:
  schema: config.yaml
  required_keys:
    - api_key
    - base_url
