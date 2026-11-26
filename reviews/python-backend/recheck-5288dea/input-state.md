# Входное состояние и границы нового прохода

Подключённый корень: `/workspace/simple_tickets`. Ветка: `api-new-client-scheme`. Начальный HEAD: **d497e75d4937e8edea98783a5af924c247622e06**.

Первый git status содержит 70 добавленных/неотслеживаемых файлов. Изменений Python-кода, DDL, корневого README или тестовых исходников нет. SHA256 полного `git diff --binary HEAD`: `fd54d271467c6ce607e76ba1b156bb3cc8cf8be23c591ae1b677c635a0abdc60`. Содержимое diff не включено в отчёт; сохранены пути и SHA256 файлов.

Удалённая api-new-client-scheme содержала новые изменения владельца. Для анализа создана связанная копия `/workspace/work/simple_tickets-5288dea` на **5288dea85d8f7e7e4c84d4801781d297e0e14475**. Начальная подключённая копия не переключалась, её index и пользовательские файлы сохраняются. Входные незакоммиченные материалы учтены в инвентаризации и последующем сравнении прежних отчётов, но не подмешивались в слепые экспертные пакеты. Новых backend-изменений из исходной копии для наложения на актуальный снимок не было.

## Общий вход

205 файлов исходников/DDL/документов перечислены в input-manifest.json: 204 файла из Git SHA и одна одинаковая служебная записка координатора INPUT-NOTES.md (её копия здесь — input-notes.md). SHA256 манифеста: `00c005b64c36f100382334212b0f71e2e7bc390a31cb0e08001f2e81672717bf`. Временный путь `/workspace/work/input-5288dea`. Финально все 204 содержимого отдельно сверены с Git blobs зафиксированного SHA; весь пакет205 и дополнение также сверены по хешам.

В Git файл `reviews/simple_tickets-decisions-2026-11-24.md` заканчивается заголовком5.3 без текста раздела. Уточнение счёта: `wc -l` даёт95 переводов строки; последний заголовок находится на логической строке96 без завершающего LF. Формулировка «95 строк» в первом вопросе и первичных материалах отражает первоначальный wc-подсчёт. На вопрос о полноте требований владелец ответил: **«Все последние договорённости уже обязательны»**. Всем четырём сессиям до сдачи какого-либо заключения передано одинаковое дополнение: полный ранее подготовленный документ и это подтверждение. SHA256 доп.манифеста: `ed4dd4e6ad341b1713b8bf404c9f19dba239425375793b1f973e0a9cd3b5d287`; сами материалы — decisions-full.md и owner-confirmation.md, версия дополнения — requirements-manifest.json. Основной пакет не менялся.

Корневой readme.md прочитан целиком. Его «Необходимо сделать» — TODO. Пометки FIXED в README прошлого аудита — заявления владельца об исправлении, а не доказательства. В слепой раунд не передавались прежние описания находок и патчи; полный старый отчёт сравнивается после первичных заключений. Датированные решения дополняют или заменяют более ранние предложения docs/notes.

Включены src, Python utils, db/schema.sql, требования зависимостей, pytest.ini, root launchers, backend Dockerfile/build-check и backend Markdown-документы. Исключены frontend/node_modules, архивы frontend, генерируемые результаты, рабочие DB и .env. Старые экспертные отчёты, REPORT_SIMPLE_TICKETS_3.md, TEST_MATRIX.md и прежние tests/patches не использовались как вход экспертов первого раунда.

## Начальный git status

| Статус | Путь | SHA256 файла |
|---|---|---|
| ` A` | `docs/notes/production_sessions_idempotency_observability.md` | `47e8e94c9b6d109d9d07afb388410fc1c0027790410506b1a61ccfdbf2fd229f` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/PROGRESS.md` | `4e0d2bcf0a40f7f99cf913aafe96ee2c2cfa4c41b5d2c90eaf801fa30a917849` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/README.md` | `e762ab9c00d54cefa6e7af6daa37a8b7bd5297e0218210fc71e2ef62dd970d43` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/arbiter-final.md` | `2134bd8df690b9468c0d78d18d97fa3ff40f21ae100aa01268c0c493575eb7de` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/arbiter-initial.md` | `c25d49dab41ed02bd86190d729f54e96472de5024e51ffbed3720ff698f990f1` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/coordinator-notes.md` | `8ed5391cd4a8aad7042a31607b4a2f9b5f97cdc4ac17a1989e9e55d786ca8674` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/initial-report-hashes.json` | `3e8c432da0e6e491f744d28402f5e7994b7b6ea716a7c18b10860fe08b302c3e` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/round-01/analyst.md` | `b96ae81d6f6701c432ae70bea6e500f84e06b3bf2c2537b3d1f6d0585644c1c4` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/round-01/python.md` | `aa47a3cad0f70f170e1d6ada117253edabf0fc93513b9c6b16bd8f7899bfe0c6` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/round-01/qa.md` | `a2998718bcadc9a3907f66b03c4db71f3ca03527affd3982199c217199f82868` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/round-02/analyst.md` | `3f06fd6fb930621891fea72322206d7c17e35469da29c25d844c260feef80ba9` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/round-02/python.md` | `b199fdda9d79d966111b573b13ef82c4a59c92bb41168ce2f85f87d483ab568f` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/round-02/qa.md` | `e88bb78deb01cf331515617acc3521e304974180d0f7ba1983579e40e7ef167d` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/round-03/analyst.md` | `9e1cc73fe14ec9e8d7ab5ac5b88b22660d2817011820e1c654a5193ae9037f5a` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/round-03/python.md` | `c1cdb6d65e80eea87984fb616df8de993b82812ed4592552d910186f041ef746` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/round-03/qa.md` | `005daab88cdde8bef08f8fdb0e1bf47e0f58455fa12ac657ed5353fffd9540d1` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/experts/support/previous-recheck-helper.md` | `6eeb07b38f9bb200baf99b39243f8beca27b9bdac318a2e0c4aa83667e182409` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/findings.md` | `29def9a14e3d8302df1a930a3fbae08e30922f72247a74362ad07b680ab3215d` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/git-verification.md` | `a17239cc12d670f45056415f616c422482f05995ac30c937914a75dbe0062513` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/input-manifest.json` | `8ad0911db59c2828a58f8e215d2ef0da291117ad20be52647d424573472e267d` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/01-user-role-permissions.patch` | `84b73edb78c9fa2f453609bd2ac0033ba59d00c0bf8bacae29236fa6463d8f30` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/02-expected-input-errors.patch` | `8a03a9b2a72f7fb66c7b66fb68cf81470aac88385605b345e96a322557975f2a` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/03-role-assignment-query.patch` | `44fbbc3c0f8d2fddab0836f8f56bc63cea85d1e22da6d2c56496b12bd82eaf69` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/04-staff-comment-author.patch` | `fb64dec4bc397ef5e706b6c5a48d0687dc450b56fcbb3afc7eac42cd3816864c` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/05-paired-contact-edit.patch` | `f2ca112b21700bb7d25143e930f1f3984c6899b3d8375b877308e79251f4a762` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/06-refresh-subject-identity.patch` | `2bb1fb6f795c058f48fe624f2676ec67db1bd3cea701a588d2d056dcdb0612fa` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/07-utc-dates.patch` | `0e85cc117057be711b4b9816dec7be7a3ebd1cec127b3f84d38437faaeeb412b` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/08-database-error-classification.patch` | `79d9fd785b6975b3109f31f3cdcb41fd00b54c6c70c024464df94dbe9955edde` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/09-admin-enable-department.patch` | `b691acb1e0dca7e90fc8aeb6def73193a0f3742cec4f6b1edf5addfa92c0d215` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/10-current-test-launchers.patch` | `8f80d758dca2d8bea1ca8afe00c57da466bd8c97cb3842adc4e2731d7aae35a5` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/patches/README.md` | `fb797c2773e860dac9c2f5d1ebff77e9793ecfa9b8de58d9c5758a2e57d546cf` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/previous-findings.md` | `1993a3e66abb78e6de0b72fbf35f088d5e50bb7b3f2192b50c32a19d21ecc9e5` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/requirements.md` | `856c0fb746c39f60dd228ae46b0c13a441f44f85d27b19d38326890e13c68445` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/snapshot.md` | `9d5fd5f975203c1271c5771a87967ef6d0b079de21b7ae475164c13f311622e7` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/README.md` | `86e97235db5d61787af287302010cb3192cfcc5e8a79d97338b4aabb921b4841` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/conftest.py` | `6aea27bbd1cfd13402e62266aa8ef4e5672adfcc3fa544bf421a226ab88da9d1` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/environment.json` | `1936afedfa2cb753d153e9b615d318044c1420a76cf8e71c202b4beb9d78b6c5` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/results.json` | `c31c8c52ebcd7087a99028e764f3a5857d6033e713da3ce39d63ce9a56b075b9` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/test_atomicity_and_contention.py` | `c85ed303c50b2595c0a3d67f472d9d023acdec5b17dd14244cb44e7e9fe07682` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/test_contact_and_department.py` | `64d2956463424b07b32eeca5cee3c080930ed62ca02358a03f3712f0863cae85` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/test_current_workflows.py` | `7dfed36b8063a30c2bd80da7f0534eb1638973124a92f7d97873d9893ca60bc4` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/test_database_error_classification.py` | `a298d8dcdc0df4e621c943ff1a2b78d26f653099f7a5616f167c2a2521d1c0e1` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/test_persistence_and_dates.py` | `55fea1cf081664a54d674d25c84d569001b3bf4619fe353c53c366a262d9b310` |
| ` A` | `reviews/python-backend/recheck-bbf7a39/tests/test_rbac_and_validation.py` | `199732dbfe794c1077b9b2484e1b742482fb21c45b2aacfaf10754ec270cb5a5` |
| `??` | `reviews/python-backend/recheck-d497e75/README.md` | `dde83c9f9590a620ad39c4000a1ed11fa839e20d88ccfcd5dfd4d43991bb9f77` |
| `??` | `reviews/python-backend/recheck-d497e75/TESTING.md` | `947104dbc7cb010cd79b62e0126aab42d8083d133d650bfc5367e712a66d44b7` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/arbiter-final.md` | `7358c70012c6588174c31c6f7a43a9f2f61586c5af7cee477365de5a04ee6f55` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/arbiter-initial.md` | `5bf376b4b57114a613220dc288a64073e71d2671f2bbecf6b429a86b38234911` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/round-01/analyst.md` | `c50fdfe725e6d39ddbb8cc98d72fdb08eb9523a6abbbd5eb1f3a3c95a5a0ec95` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/round-01/python.md` | `afc900d278f9bf2c34fe1056cae55b5e4a73b6fdfc9ace8918b75e3d4d08d0be` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/round-01/qa.md` | `f1cad6bb4da9ea61ee0818906a0f3572eb32097253ec4b514289dd277f7ab863` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/round-02/analyst.md` | `9e0416c86341e831dfc8647bf4ffcc35ffdc511c880f87d1049b7ea634e752cf` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/round-02/python.md` | `4c3d38ba9f09de8449d0e4b1c2bdcb68018773a1ec411afd3a758e49dd4899d2` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/round-02/qa.md` | `7c456ae158f57124e012b10ac4f7205e126cf0ff1de17b97b94dd9c517bb7d6a` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/round-03/analyst.md` | `76a6deeb59f211757d0910f584a017e1d5744d011b7d6e0242c4dbbf5f774221` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/round-03/python.md` | `63d1b8e2be9760ee3c18c6d7e6afe557cd748aee14ae11919d31136fb019f4b9` |
| `??` | `reviews/python-backend/recheck-d497e75/experts/round-03/qa.md` | `384a29addfee96b24be1e65f8e275614db16f0d1315682d5dbc5eeb7a3032fe0` |
| `??` | `reviews/python-backend/recheck-d497e75/findings.md` | `5dc8358a40019d940386f419d91f2c61c832d15d5593b931eb59b24d082bea42` |
| `??` | `reviews/python-backend/recheck-d497e75/git-snapshot.md` | `a94e2445b84746edcfdc9c523cc8095974d9fc1df32f0c23e9afb736c7a1bea4` |
| `??` | `reviews/python-backend/recheck-d497e75/idempotency.md` | `cf6ff7a628f2ff3b0d007f961f82d82ad61a89abd7a6a6f742cbb23e16b2e1c9` |
| `??` | `reviews/python-backend/recheck-d497e75/patches/01-disable-cascade.patch` | `94baf4b284d567c38ae679b323edc0ccfc9ecb47e3881f135441063d9e2e757d` |
| `??` | `reviews/python-backend/recheck-d497e75/patches/02-finish-work-documentation.patch` | `70213c5dd33fdf888dcd041ecfb5722fc5a821968bbed5c55c2400f655bd8264` |
| `??` | `reviews/python-backend/recheck-d497e75/patches/03-refresh-token-storage.patch` | `da84aa3fcc75dff5539e5ec63460f788cd2378485af87181de4ad519aec8bdae` |
| `??` | `reviews/python-backend/recheck-d497e75/patches/04-request-validation.patch` | `6f3ce8b97209fec79413632b86901e0f60a3f120e7128a292c810413818e1599` |
| `??` | `reviews/python-backend/recheck-d497e75/patches/05-workflow-error-details.patch` | `b0f565d65172797fd93d7fdc18bcf159e49fc5f75e17adee4282c5ac22da8d35` |
| `??` | `reviews/python-backend/recheck-d497e75/patches/06-sqlite-schema-compatibility.patch` | `6ece07837f9b9be7103cbaaf181db1317535bb1c3f4a13cbd97f86aa1dd6c3b3` |
| `??` | `reviews/python-backend/recheck-d497e75/patches/07-comment-author.patch` | `bb79e5617f83d0adf4243aadf338889f4f8a9d1272d60f0d2a3b73ffc09dfc03` |
| `??` | `reviews/python-backend/recheck-d497e75/tests/test_recheck_workflows.py` | `5ee48295a450831d30e70aff6e8c302eeadad9ccd52b0fe3f5e372fe65dc65cc` |
| `??` | `reviews/python-backend/recheck-d497e75/tests/test_refresh_storage.py` | `642255bc1074dc04b872e61110806d55fa77b1c6a6b3e690db5a8c2c40150be5` |
| `??` | `reviews/python-backend/recheck-d497e75/transactions-and-sessions.md` | `79adf3c92dbd641a4c130dae41e06c32b4ed266c3e9200b4aad09e165d0cc3c7` |
