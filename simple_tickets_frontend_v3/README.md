# Simple Tickets Frontend v3

Рабочее место Admin для Simple Tickets. I1 добавила вход, очередь и чтение карточки. I2 добавила вкладки с черновиками, связанные карточки, создание, редактирование и комментарии. I3 добавила обработку заявок и горячую линию. I4 добавила справочники, аккаунты, роли, отмену и удаление. [Документация проекта](docs/README.md).

## Локальный запуск

Используйте ветку `frontend_new`. Проверены Node.js 24.22.3, npm 11.19.1 и Python 3.14.10. Для запуска на тестовых данных достаточно двух терминалов.

В первом терминале запустите FastAPI из корня репозитория. Для установки зависимостей используйте активированное виртуальное окружение Python.

```bash
cd simple_tickets_frontend_v3
python -m pip install -r ../requirements.txt
python -B tests/backend_contract.py --serve
```

FastAPI слушает `127.0.0.1:18080` и создаёт отдельную временную SQLite. Путь к `credentials.json` появится в терминале. Для просмотра заявок используйте поля `username` и `password` из профиля `reader`.

Во втором терминале запустите frontend из корня репозитория.

```bash
cd simple_tickets_frontend_v3
npm ci --cache .npm-cache --no-audit --no-fund
npm run dev
```

Оставьте оба терминала открытыми и перейдите на [http://127.0.0.1:5173/](http://127.0.0.1:5173/). Для завершения остановите оба процесса клавишами Ctrl+C. При штатной остановке FastAPI удаляет временную базу и файл учётных данных.

По умолчанию Vite пересылает `/api/*` на `http://127.0.0.1:18080` с удалением префикса `/api`. Для другого адреса задайте `BACKEND_BASE_URL` в окружении процесса или в локальном `.env` внутри v3. Параметр применяется на стороне Vite. [Образец конфигурации](.env.example).

## Проверки и сборка

```bash
npm test
npm run build
npm run preview
```

Preview слушает `127.0.0.1:5174` и использует тот же прокси. Для размещения `dist/` настройте статический хост с SPA fallback для страниц и отдельное перенаправление `/api/*` к FastAPI на том же origin. В документации размещения нужно зафиксировать HTTPS и маршрут API. Preview служит для проверок сборки.

### Изолированный FastAPI и Chromium

Скрипт контракта использует Python 3.12 или новее, зависимости FastAPI из репозитория и `httpx` из `requirements-test.txt` для TestClient. Для автоматического браузерного прогона дополнительно нужны Python Playwright и Chromium по пути `/usr/bin/chromium`. Релизная проверка использовала закреплённые зависимости FastAPI. [Отчёт I5](docs/RELEASE_ACCEPTANCE_REPORT.md).

```bash
python -m pip install -r ../requirements-test.txt
python -B tests/backend_contract.py
python -B tests/backend_contract.py --serve
```

Команда с `--serve` держит тестовый FastAPI на `127.0.0.1:18080` и выводит путь к временному файлу учётных данных. В других терминалах запустите preview из предыдущего раздела и передайте выведенный путь браузерному тесту.

```bash
python -B tests/browser_smoke.py '<путь к credentials.json>' --screenshots
python -B tests/browser_i2.py '<путь к credentials.json>'
```

Для общего прогона сначала запустите I1 на свежей базе. Сценарии I2 создают и меняют синтетические записи. Снимки синтетических экранов сохраняются в игнорируемом каталоге `.qa-visual/`. Остановите процесс изолированного API клавишами Ctrl+C, чтобы удалить временную БД и учётные данные.

Для браузерных сценариев I3 запустите новый стенд на том же порту с отдельными профилями рабочих ролей.

```bash
python -B tests/backend_contract.py --serve-i3
python -B tests/browser_i3.py '<путь к credentials.json>'
```

Для I4 используйте отдельный запуск с административными ролями. API и браузерный тест запускаются в разных терминалах.

```bash
python -B tests/backend_contract.py --serve-i4
python -B tests/browser_i4.py '<путь к credentials.json>'
```

## Граница итерации

Карточка открывает связанные данные по правам чтения. Черновики живут до обновления страницы или выхода. I4 добавляет административные списки и операции с учётом прав действующего API. Темы, языки и тексты интерфейса публикуются как JSON в `/config/`. [Инструкция по настройке](docs/RUNTIME_CONFIGURATION.md) · [План](docs/IMPLEMENTATION_PLAN.md).

После сборки браузерную проверку тем и переводов можно повторить на тестовой SQLite в режиме `--serve`. Тест меняет JSON только в собственной временной копии `dist/`.

```bash
python -B tests/browser_appearance.py '<путь к credentials.json>'
```

Браузерный замер очереди использует production-сборку и отдельные синтетические ответы. Он показывает время обработки списка, локального поиска и переключения карточек. [Результаты I5](docs/RELEASE_ACCEPTANCE_REPORT.md).

```bash
python -B tests/browser_performance.py --dist dist
```
