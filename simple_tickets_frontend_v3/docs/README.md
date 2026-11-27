# Документация Simple Tickets Frontend v3

Актуальное направление — рабочее место Admin в ветке `frontend_new`. Для запуска I1–I4 используйте [README frontend v3](../README.md). Итоги и условия продолжения приведены в [статусе проекта](PROJECT_STATUS.md). [План реализации](IMPLEMENTATION_PLAN.md) · [AGENTS.md](../../AGENTS.md).

| Документ | Содержание |
|---|---|
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Состояние проекта, границы этапа и условия запуска разработки |
| [ITERATION_1_REPORT.md](ITERATION_1_REPORT.md) | Реализация I1, состав изменений, проверки и ограничения |
| [ITERATION_2_REPORT.md](ITERATION_2_REPORT.md) | Рабочие вкладки, команды записи, результаты приёмки I2 и условия перехода к I3 |
| [ITERATION_3_REPORT.md](ITERATION_3_REPORT.md) | Рабочие переходы, горячая линия, сверка истории и результаты приёмки I3 |
| [ITERATION_4_REPORT.md](ITERATION_4_REPORT.md) | Административные справочники, аккаунты, роли, отмена и удаление |
| [RUNTIME_CONFIGURATION.md](RUNTIME_CONFIGURATION.md) | Публикация тем, языков и подписей интерфейса без пересборки |
| [APPEARANCE_REPORT.md](APPEARANCE_REPORT.md) | Реализация и результаты проверок BK-013/014 |
| [RELEASE_ACCEPTANCE_REPORT.md](RELEASE_ACCEPTANCE_REPORT.md) | Кандидат I5, профиль стенда, измерения и условия эксплуатационного допуска |
| [DECISIONS.md](DECISIONS.md) | Ответы владельца, статусы DEC, альтернативы и открытые вопросы |
| [CONSILIUM_LOG.md](CONSILIUM_LOG.md) | Консилиумы, разногласия и результаты рецензирования |
| [INITIAL_RESEARCH_REPORT.md](INITIAL_RESEARCH_REPORT.md) | Историческое заключение этапа 1. Поправка по query приведена в API_CONTRACT |
| [BACKEND_ANALYSIS.md](BACKEND_ANALYSIS.md) | Архитектура, модели, правила и ограничения неизменяемого backend |
| [API_CONTRACT.md](API_CONTRACT.md) | 107 операций с методами, URL, схемами, правами и ошибками |
| [AUTHENTICATION.md](AUTHENTICATION.md) | Login, refresh, logout, права, состояния и риски хранения |
| [PERMISSIONS_MATRIX.md](PERMISSIONS_MATRIX.md) | Право, роль, состояние, актёр и ограничения доступа |
| [FRONTEND_V2_ANALYSIS.md](FRONTEND_V2_ANALYSIS.md) | Существующие страницы, стек и технические проблемы |
| [COMPATIBILITY_MATRIX.md](COMPATIBILITY_MATRIX.md) | Расхождения v2/backend и решения для v3 с трассировкой |
| [CODE_REUSE_PLAN.md](CODE_REUSE_PLAN.md) | Пофайловый перенос, адаптация, замены и проверки |
| [FUNCTIONAL_REQUIREMENTS.md](FUNCTIONAL_REQUIREMENTS.md) | FR, приоритеты MoSCoW, сценарии, API и критерии AC |
| [NON_FUNCTIONAL_REQUIREMENTS.md](NON_FUNCTIONAL_REQUIREMENTS.md) | NFR, метрики, безопасность, доступность и доказательства |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Стек, модули, маршрутизация, API и состояния |
| [USABILITY_ANALYSIS.md](USABILITY_ANALYSIS.md) | Проблемы v2, критичность и гипотезы о работе Admin |
| [USER_JOURNEYS.md](USER_JOURNEYS.md) | Шаги Admin, разрешения, ошибки и критерии результата |
| [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) | Разделы, контекст, структура страниц и навигация |
| [UI_GUIDELINES.md](UI_GUIDELINES.md) | Поля, таблицы, действия, нагрузка и единообразие |
| [WIREFRAMES.md](WIREFRAMES.md) | Текстовые схемы ключевых страниц и состояний |
| [ACCESSIBILITY.md](ACCESSIBILITY.md) | WCAG 2.2 AA, фокус, клавиатура и ручная проверка |
| [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | TC, mock и реальные проверки, критерии эксплуатации |
| [RISKS.md](RISKS.md) | Вероятность, критичность, ответственность и смягчение |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Backlog, объём I1–I4, зависимости и критерии готовности |

Трасса для реализации: DEC → FR/NFR → J/API/permission → AC/TC → BK. Только явно утверждённые решения в `DECISIONS.md` имеют статус Approved. Документы этапа 2 описывают проверку по исходникам, а работающую реализацию и эксплуатационную готовность подтверждают тесты последующих этапов.
