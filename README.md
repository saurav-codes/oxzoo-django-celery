# oxzoo-django-celery

Official ox deploy example: the multi-process kitchen sink. Django 5.2 serves a JSON API behind gunicorn, a Celery worker executes tasks through a local Redis broker, Celery beat fires a heartbeat task every 60 seconds, data lives in a local PostgreSQL database, and a React 18 SPA built by Vite shows both the build-time and the runtime greeting. ox deploys all of it to one Ubuntu VPS from a single `ox.toml` at the repo root: three systemd processes ordered by `depends_on`, nginx serving the built frontend and proxying the API paths, and every install/build/migrate hook running as the unprivileged project user. Traffic switches only after the health check passes.

What this example demonstrates beyond the single-process [oxzoo-react-django](https://github.com/saurav-codes/oxzoo-react-django):

- **Multi-process ordering**: `web`, `worker`, and `beat` systemd units with `depends_on` gates so workers start after the web process is ready.
- **Infra autowiring**: the `DATABASE_URL` placeholder makes ox provision local PostgreSQL (role + database named by `DATABASE_NAME`) and inject the full DSN; a local Redis is started and injected as `REDIS_URL`. The `[[postgres_databases]]` block then enables `pgcrypto` on that database, whose name must match `DATABASE_NAME`. No manual host setup.
- **Celery roundtrip**: `GET /api/greeting` enqueues a task, a worker executes it, and the result comes back through Redis.
- **Beat timers**: `CELERYBEAT_SCHEDULE` repeats `heartbeat()` every 60 seconds, printed into the worker's journald log.
- **Migrations**: the `migrate` deploy hook runs `manage.py migrate --noinput` against the autowired database.

## Architecture

| Component | Version | Purpose |
| ----------------- | -------------------------- | ---------------------------------------------- |
| Django | 5.2.17 | JSON API (`/api/greeting/`, `/health/`) |
| gunicorn | 26.2.0 | WSGI server for the `web` process |
| Celery | 5.6.3 (`celery[redis]`) | `worker` and `beat` processes |
| redis-py | 6.4.0 | broker + result backend transport |
| psycopg | 3.3.5 (binary) | PostgreSQL driver for the `Visit` model |
| dj-database-url | 3.1.2 | parses `DATABASE_URL` into `DATABASES` |
| Python tooling | uv (`uv.lock`, `.python-version`), Python 3.13 | locked installs |
| React + Vite | react/react-dom 18.3.1, vite 5.4.21 | SPA built to `dist/` |
| PostgreSQL + Redis | provisioned by ox | local role/db + local broker, both on the VPS |
| Serving | nginx + systemd | provisioned by ox |

## Environment flow

- **`GREETING_TAG` is runtime env for Django and the worker**: `greetings/tasks.py` reads it from `os.environ` inside the worker process on every task, so `GET /api/greeting` returns `hello world oxzoo-django-celery_{GREETING_TAG}` with whatever the ox Environment editor currently holds. Change it in the editor and the API line follows without a redeploy.
- **`GREETING_TAG` is build-time env for the SPA**: `vite.config.js` sets `envPrefix: ["GREETING_", "VITE_"]`, so `GREETING_TAG` present during `npm run build` is baked into the bundle via `import.meta.env.GREETING_TAG` (one contiguous template literal in `src/App.jsx`, on purpose). Changing the tag means rebuilding the SPA.
- **`SECRET_KEY`**: Django signing key. Placeholder in `.env.example`; set a real value in the ox Environment editor.
- **`DATABASE_URL`** (`postgres://change-me` in `.env.example`): autowired by ox — the placeholder triggers local PostgreSQL provisioning and ox injects the full DSN into every process. `DATABASE_NAME` (`oxzoo-celery`) names the database ox creates; it must equal the `[[postgres_databases]]` name in `ox.toml` so the `pgcrypto` extension step targets the same database. Unset locally, `settings.py` falls back to `db.sqlite3` for convenience; ox always sets the real one.
- **`REDIS_URL`** (`redis://change-me` in `.env.example`): autowired by ox. ox starts a local Redis and injects the DSN; `config/settings.py` uses it for both `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` (a `CELERY_BROKER_URL` env var overrides if you ever split them).
- **`ALLOWED_HOSTS`**: ox injects the deploy domain (comma-separated); `settings.py` reads it directly. `DJANGO_DEBUG` defaults to `false`.

## Deploy with ox

1. In the ox dashboard, create a project from the clone URL: `https://github.com/saurav-codes/oxzoo-django-celery`
2. **Before the first deploy**, set `GREETING_TAG=w3-03` (and `SECRET_KEY`) in the project's Environment editor. The build hook bakes `GREETING_TAG` into the SPA, so it must exist before the first deploy.
3. Press **Deploy**. ox:
   - creates the local postgres role + `oxzoo-celery` database with the `pgcrypto` extension and starts the local Redis,
   - runs `uv sync --frozen` and `npm install` (release-local installs),
   - runs `npm run build` and `uv run python manage.py migrate --noinput`,
   - starts the `worker` and `beat` processes (Redis broker) and the `web` process (`uv run gunicorn config.wsgi:application` on `127.0.0.1:9117`), gated by `depends_on` and the `http://127.0.0.1:9117/health` readiness check,
   - points nginx at `dist/` (`spa = true`) and proxies `/api` + `/health` to gunicorn.

Expected domain: `https://celery.oxzoo.sorv.dev` (TLS provisioned by ox).

## Expected output

Visiting the domain with `GREETING_TAG=w3-03`:

```
build-time: hello world oxzoo-django-celery_w3-03
api: {"greeting":"hello world oxzoo-django-celery_w3-03","celery":"ok","visits":3}
```

- The `build-time` line is baked into the JS bundle at build time.
- The `api` line is `GET /api/greeting` (JSON shape: `{"greeting": string, "celery": "ok", "visits": number}`); `greeting` reflects the worker's live environment and `visits` counts the `Visit` rows created by each request.
- `GET /health` returns `{"ok": true}` (plain `/health` 301-redirects to `/health/`, which ox's readiness gate accepts).
- The worker journal shows the heartbeat line every 60 seconds:

```
hello world oxzoo-django-celery_w3-03
```

## Local development

1. Install deps: `uv sync`
2. Start local Redis and PostgreSQL (`redis-server` and `postgres`), or edit `.env` to point elsewhere; with neither `DATABASE_URL` nor Redis set you still get sqlite + a broker error only on `/api/greeting`
3. Migrate: `uv run python manage.py migrate --noinput`
4. Web: `uv run python manage.py runserver` (Django reads `GREETING_TAG` from the shell env)
5. Worker: `uv run celery -A config worker --loglevel=INFO --concurrency=1`
6. Beat: `uv run celery -A config beat --loglevel=INFO --schedule /tmp/oxzoo-django-celery-beat`
7. SPA: `npm install` then `npm run dev` (build with `npm run build`)

Copy `.env.example` to `.env` and fill in values if you do not want to rely on the sqlite/localhost defaults.
