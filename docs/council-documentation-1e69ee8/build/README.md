# Сборка документации

Полные редактируемые источники находятся в [backend.md](../backend.md) и [user-guide.md](../user-guide.md). Каталоги API, таблиц и модулей уже включены в технический Markdown. Готовые SVG помещены рядом с редактируемыми DOT в [diagrams](../diagrams/).

## Собрать PDF из полных Markdown

Проверено с Python 3.12.14, Pandoc 3.1.11.1, WeasyPrint 66.0, pypdf 6.21.4, Graphviz 2.42.4 и шрифтами DejaVu Sans и DejaVu Sans Mono. WeasyPrint требует системных библиотек Pango, HarfBuzz и fontconfig. Для PDF не нужен запущенный бэкенд.

Из корня каталога комплекта выполните:

```bash
python -m venv /tmp/simple-tickets-doc-build
/tmp/simple-tickets-doc-build/bin/python -m pip install -r build/requirements.txt
/tmp/simple-tickets-doc-build/bin/python build/build_pdf.py
```

Будут собраны оба PDF с титулом, датой, оглавлением, номерами, Unicode-текстом и закладками. Можно передать имя одного документа, например `build/build_pdf.py user-guide`. Дата и рассмотренный снимок находятся в скрипте и титульном шаблоне. При смене редакции обновите их и шапки Markdown.

После правки исходника схемы можно перегенерировать SVG командой `dot -Tsvg diagrams/user-ticket-life.dot -o diagrams/user-ticket-life.svg`. `build/diagrams.py` восстанавливает текущие DOT и SVG из прописанных сценариев и каталога SQLite. Он сверяет нарисованные переходы с извлечённым графом.

## Обновить извлечённую часть

Для новой версии используйте отдельный экспорт исходников, содержащий только код, зависимости, схему и разрешённые документы. В нём не должно быть .env и рабочих баз. Для примера ниже путь в переменной `tickets_source` должен указывать на такой экспорт. Runtime скрипт создаёт свою синтетическую базу и генерирует временный ключ, а журналы пишет в отдельную временную директорию.

```bash
tickets_source=/tmp/frozen-simple-tickets
tickets_scratch=$(mktemp -d)
python -m venv "$tickets_scratch/venv"
"$tickets_scratch/venv/bin/pip" install -r "$tickets_source/requirements.txt" -r "$tickets_source/requirements-test.txt"
PYTHONDONTWRITEBYTECODE=1 "$tickets_scratch/venv/bin/python" build/runtime_snapshot.py "$tickets_source" "$tickets_scratch/runtime"
python build/catalogs.py "$tickets_source" 1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69 "$tickets_scratch/runtime" "$tickets_scratch/appendices" --summaries meta/api-summaries-ru.json
python build/diagrams.py "$tickets_scratch/runtime" diagrams
```

Из временного каталога перенесите полные приложения A, B, C в backend.md после сверки извлечённых связей. Переводы новых OpenAPI summary добавьте в словарь. Сверьте рисунки, правила и разделы обоих документов с новой схемой. Затем повторите сборку.

Для повторения HTTP-примеров см. [валидацию](../meta/validation.md). Формирование входных манифестов описано в [source-state.md](../meta/source-state.md).
