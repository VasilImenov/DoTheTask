# Скелет на проект

Основа за уеб приложение с Flask и PostgreSQL, което се стартира с Docker Compose. Приложението има една страница: пишете SQL заявка, изпълнявате я и виждате резултата. Базата съдържа примерните данни dvdrental, за да има с какво да работите.

## Изисквания

Docker Desktop (Windows, macOS) или Docker Engine с Docker Compose (Linux).

На Linux, ако `docker` работи само със `sudo`, изпълнете стъпките от раздела „Manage Docker as a non-root user“: https://docs.docker.com/engine/install/linux-postinstall/

## Стартиране и спиране

1. Стартирайте Docker Desktop и изчакайте да зареди. На Linux с Docker Engine тази стъпка не е нужна.
2. Разархивирайте `project-skeleton.zip` и отворете терминал в папката `project-skeleton`, в която е файлът `compose.yaml`.

   - Windows: отворете папката във File Explorer, напишете `powershell` в адресната лента и натиснете Enter.
   - macOS: отворете Terminal, напишете `cd ` (с интервал след `cd`), плъзнете папката от Finder в прозореца на Terminal и натиснете Enter.
   - Linux: щракнете с десния бутон в папката и изберете Open in Terminal.

   Друг начин за всички системи: отворете папката във VS Code (или алтернативно IDE) (File > Open Folder) и отворете терминал от Terminal > New Terminal.

3. Стартирайте услугите:

   ```bash
   docker compose up -d --build
   ```

   Първото стартиране отнема повече време: Docker изтегля образите, а базата dvdrental се възстановява в празния том. Ако командата съобщи, че не може да се свърже с Docker, Docker Desktop не е стартиран или още зарежда.

4. Проверете състоянието:

   ```bash
   docker compose ps
   ```

   Услугата `db` трябва да е `healthy`, а `web` да е `Up`.

5. Отворете http://localhost:8000.

Спиране:

```bash
docker compose down
```

Данните остават в тома `pgdata` и са налице при следващото стартиране. `docker compose down -v` изтрива и тома, затова при следващото стартиране базата се създава наново.

Логове: `docker compose logs web` и `docker compose logs db`.

Ако порт 8000 е зает, `docker compose up` завършва с грешка, в която има `port is already allocated` или `ports are not available`. Сменете `WEB_PORT` в `.env` (например `WEB_PORT=8001`), изпълнете `docker compose up -d` и отворете http://localhost:8001.

Редактирайте `.env` във VS Code или друг текстов редактор. Името му започва с точка, затова macOS и Linux не го показват: във Finder го покажете с Cmd+Shift+. (точка), а във файловия мениджър на Linux с Ctrl+H.

## Услуги

- `db` - PostgreSQL 18. При първо стартиране с празен том изпълнява скриптовете от `db/init`. Портът на базата не е публикуван навън. Приложението се свързва с нея по името `db` във вътрешната мрежа на Compose.
- `web` - приложението на Flask (сървър за разработка) на порт 8000. Потребителя, паролата и името на базата взема от `.env`, а `PGHOST` и `PGPORT` за контейнера са зададени в `compose.yaml`. Ако процесът спре с грешка, Docker го стартира отново (`restart: unless-stopped`).

## Страницата

- Напишете SQL заявка в полето и натиснете „Изпълни“ (или Ctrl+Enter, на macOS и Cmd+Enter).
- `SELECT` показва таблица с резултата (до 1000 реда) и общия брой редове.
- `INSERT`, `UPDATE` и `DELETE` показват колко реда са засегнати, а `CREATE TABLE` и другите команди - какво е изпълнено.
- При грешка се показва съобщението на PostgreSQL.
- Вляво са таблиците в базата. Щракнете върху име, за да видите първите 100 реда.

Всяка команда се записва в базата веднага и не може да се отмени. Ако в полето има няколко команди, разделени с `;`, се показва резултатът само от последната, а ако една от тях е с грешка, не се изпълнява нито една. Не използвайте `BEGIN`: промените след него се губят, ако в същото поле няма `COMMIT`. Началните данни се връщат с `docker compose down -v` и `docker compose up -d`.

Заявка, която свързва таблици без условие (например `SELECT * FROM rental, customer`), връща милиони редове и може да изразходва паметта на `web`. Тогава Docker рестартира `web` и след няколко секунди страницата отново работи. Ако страницата не отговаря или показва грешка за връзка с базата, изпълнете `docker compose up -d`.

Примери:

```sql
SELECT title, length FROM film ORDER BY length DESC LIMIT 10;
```

```sql
SELECT c.name AS category, count(*) AS films
FROM film_category fc JOIN category c USING (category_id)
GROUP BY c.name
ORDER BY films DESC;
```

```sql
INSERT INTO note (title) VALUES ('Втора бележка');
```

Базата е достъпна и с `psql` в контейнера (`\dt` показва таблиците, `\q` излиза). Ако сте сменили `PGUSER` или `PGDATABASE` в `.env`, сменете и стойностите след `-U` и `-d`.

```bash
docker compose exec db psql -U postgres -d dvdrental
```

## Промени в кода

Папката `app` е монтирана в контейнера `web`, а Flask е стартиран с `--debug`. Запишете промяната и презаредете страницата: сървърът се рестартира сам. При грешка в кода браузърът показва описание на грешката. Вижте и `docker compose logs web`.

`app/db.py` съдържа `get_db()`, която връща връзката с базата за текущата заявка, и `query()`, която изпълнява SQL с параметри и връща редовете като речници, например `query("SELECT * FROM actor WHERE actor_id = %s", (1,), one=True)`. Промени в базата от вашите страници се записват след `get_db().commit()`. Само страницата за SQL записва всяка команда веднага.

След промяна в `requirements.txt` или в `Dockerfile` изпълнете отново `docker compose up -d --build`.

## Собствени таблици

Скриптовете в `db/init` се изпълняват по реда на имената си и само когато томът с данните е празен:

- `01-dvdrental.sh` възстановява `db/dvdrental.tar` (данните dvdrental);
- `02-schema.sql` е мястото за вашите таблици. В него има примерна таблица `note`.

1. Заменете съдържанието на `db/init/02-schema.sql` с вашите заявки `CREATE TABLE` и `INSERT`. Можете първо да ги изпробвате на страницата.
2. Ако не искате данните dvdrental, изтрийте `db/init/01-dvdrental.sh`. По желание сменете и името на базата в `.env`, например `PGDATABASE=shop`.
3. Спрете услугите и изтрийте тома с всички данни:

   ```bash
   docker compose down -v
   ```

4. По желание сменете `name: project-skeleton` в `compose.yaml` с името на вашия проект (малки латински букви, цифри и тирета).
5. Стартирайте отново:

   ```bash
   docker compose up -d --build
   ```

6. Проверете дали вляво на страницата се виждат вашите таблици.

Ако в `02-schema.sql` има грешка, услугата `db` спира. Вижте грешката с `docker compose logs db`, поправете файла и повторете стъпки 3 и 5.

`PGUSER`, `PGPASSWORD` и `PGDATABASE` от `.env` се използват при създаването на базата. Ако ги смените по-късно, също повторете стъпки 3 и 5.

## Развитие на проекта

1. За всяка ваша таблица добавете страници със списък и бутони за добавяне, редактиране и изтриване (функции в `app/pages.py`, шаблони в `app/templates`), както в част 2 „Уеб приложение с Flask“ и част 3 „Добавяне, редактиране и изтриване“.
2. Стартирайте приложението с gunicorn вместо със сървъра за разработка, както в част 4 „Приложението в контейнер“.
3. Добавете nginx като балансьор на натоварването пред две реплики на `web`, HTTPS със самоподписан сертификат и наблюдение с Dozzle, както в част 5 „Балансьор, HTTPS и наблюдение“.

Как изглеждат тези части в завършено приложение, вижте в примерния проект `dvdrental-app`.

Страницата за SQL позволява всякакви промени в базата. Преди да покажете проекта, премахнете я или я оставете достъпна само за администратор.

## Без Docker (по желание)

Приложението може да работи и с локално инсталиран PostgreSQL. Нужен е Python 3.10 или по-нов, например от https://www.python.org/downloads/. Проверете версията с `python3 --version` (на Windows `py --version`). Вграденият `python3` на macOS е по-стар и не е подходящ. Пакетът `psycopg2-binary` няма готова версия за Windows на ARM процесор (ARM64).

1. Създайте база в локалния PostgreSQL. За данните dvdrental създайте база `dvdrental` и възстановете в нея `db/dvdrental.tar`: в pgAdmin с десен бутон върху базата и Restore или в терминал. Командите питат за паролата на потребителя `postgres`.

   Windows (PowerShell; сменете 17 с вашата версия на PostgreSQL):

   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -h localhost -U postgres dvdrental
   & "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -h localhost -U postgres -d dvdrental --no-owner db\dvdrental.tar
   ```

   На Linux (Ubuntu, Debian) потребителят `postgres` първоначално няма парола. Първо му задайте паролата от `.env`:

   ```bash
   sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'secret'"
   ```

   macOS и Linux:

   ```bash
   createdb -h localhost -U postgres dvdrental
   pg_restore -h localhost -U postgres -d dvdrental --no-owner db/dvdrental.tar
   ```

   На macOS, ако терминалът не намира `createdb`, използвайте пълния път, например `/Library/PostgreSQL/17/bin/createdb`.

2. В `.env` запишете паролата на вашия PostgreSQL в `PGPASSWORD` и порта му в `PGPORT`, ако не е 5432.
3. Създайте виртуална среда и инсталирайте пакетите.

   Windows (PowerShell):

   ```powershell
   py -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```

   macOS и Linux:

   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   ```

   На Ubuntu и Debian, ако `python3 -m venv` съобщи, че `ensurepip` не е наличен, първо изпълнете `sudo apt install python3-venv`.

4. Стартирайте сървъра за разработка.

   Windows (PowerShell):

   ```powershell
   .venv\Scripts\python -m flask --app app run --debug --port 8000
   ```

   macOS и Linux:

   ```bash
   .venv/bin/python -m flask --app app run --debug --port 8000
   ```

5. Отворете http://localhost:8000. Спрете сървъра с Ctrl+C.

Таблиците от `db/init/02-schema.sql` създайте, като поставите съдържанието на файла на страницата и го изпълните.

Двата начина използват порт 8000, затова не ги стартирайте едновременно.

## Структура на проекта

```text
project-skeleton/
├── app/
│   ├── __init__.py       create_app(): създава приложението
│   ├── db.py             връзка с базата: get_db(), query()
│   ├── pages.py          страницата за SQL
│   ├── templates/        HTML шаблони
│   └── static/style.css  стилове
├── db/
│   ├── Dockerfile        образ на PostgreSQL 18 с данните
│   ├── dvdrental.tar     архив на базата dvdrental
│   └── init/             скриптове при създаване на базата
├── compose.yaml          услугите db и web
├── Dockerfile            образ на приложението
├── requirements.txt      пакети на Python
├── .env                  настройки и пароли
└── .env.example          образец на .env
```

`.env` съдържа демонстрационни стойности. В реален проект `.env` не се споделя и не се качва в Git (вижте `.gitignore`). Споделя се само `.env.example`.

## Документация

- Flask: https://flask.palletsprojects.com/en/stable/
- psycopg2: https://www.psycopg.org/docs/
- PostgreSQL 18: https://www.postgresql.org/docs/18/
- Образът postgres (раздел Initialization scripts): https://hub.docker.com/_/postgres
- Docker Compose: https://docs.docker.com/compose/
