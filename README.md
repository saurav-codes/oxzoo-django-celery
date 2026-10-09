# oxzoo-django-celery

Deployed with [ox](https://deploywithox.com): deploy a repo to your own server with one command, no Docker. [Docs](https://deploywithox.com/docs) · [Guide for this stack](https://deploywithox.com/docs/guides/django)

An [ox](https://deploywithox.com) deploy example with many processes: Django 5.2 serves a JSON API behind gunicorn, a Celery worker runs tasks through Redis, Celery beat fires a heartbeat task every 60 seconds, data lives in PostgreSQL, and a React 18 SPA built by Vite shows both the build-time and the run-time greeting. ox deploys all of it to your own Ubuntu server from one `ox.toml`: systemd runs gunicorn, the worker and beat; Caddy serves the built SPA and sends the API paths to gunicorn; traffic moves to a new release only after its health check passes.

What it shows:

- **Services from one line each**: `[services]` gives the project a PostgreSQL database with the `pgcrypto` extension (`DATABASE_URL`) and a private Redis (`REDIS_URL`). Nothing to install or wire by hand.
- **A Celery round trip**: `GET /api/greeting/` enqueues a task, the worker runs it, and the result comes back through Redis. The worker also reads the `Visit` count from Postgres, so the response proves a second process sees the same database.
- **Workers and beat**: `[workers]` runs `worker` and `beat`. Beat keeps its schedule file in `$OX_DATA_DIR`, which survives releases. The worker's page in the ox console (and `ox celery oxzoo-django-celery worker`) shows its tasks and queues.
- **Zero-downtime deploys**: the app's port is not pinned, so ox starts the new release beside the old one and switches traffic once `/health` answers.
- **Tasks survive a deploy**: `long_job` sleeps up to 300 s, so a deploy restart lands in the middle of it. `task_acks_late` and `task_reject_on_worker_lost` redeliver a task the stopped worker never acknowledged, and the row is keyed by the Celery task id, so a redelivery finishes exactly one row.
- **A seeded table**: migration `0002` creates `Sample` with 50,000 rows, so a backup has real size and `/api/slow/` has a real aggregate to scan.
- **Migrations with a snapshot**: `[build] migrate` runs `manage.py migrate` before traffic switches, and ox snapshots the database first.
- **Scenario probes**: `MIGRATION_LOCK_SECONDS` makes migration `0004` hold an ACCESS EXCLUSIVE lock on the seeded table for that many seconds, and `DESTRUCTIVE_MIGRATION=drop` makes `0005` drop `greetings_visit.created_at` so a code rollback fails loudly. Both are no-ops when unset.

## Stack

| Component | Version | Purpose |
| --------- | ------- | ------- |
| Django | 5.2.17 | JSON API (`/api/greeting/`, `/health/`) |
| gunicorn | 26.2.0 | WSGI server for the app |
| Celery | 5.6.3 (`celery[redis]`) | `worker` and `beat` |
| psycopg | 3.3.5 (binary) | PostgreSQL driver |
| dj-database-url | 3.1.2 | parses `DATABASE_URL` |
| Python | 3.13 with uv (`uv.lock`, `.python-version`) | locked installs |
| React + Vite | react 18.3.1, vite 5.4.21 | SPA built to `dist/` |
| PostgreSQL 18, Redis 8 | provided by ox | `[services]` |

## ox.toml

```toml
# Django + Celery worker and beat, postgres (pgcrypto), redis, and a Vite SPA.

[app]
start  = "uv run gunicorn config.wsgi:application --bind 127.0.0.1:$PORT --workers 2"
health = "/health"

[static]
dir = "dist"
spa = true
api = ["/api", "/health"]

[build]
commands = ["uv sync --frozen --no-dev", "npm run build"]
migrate  = "uv run python manage.py migrate --noinput"

[workers]
worker = "uv run celery -A config worker --loglevel=INFO --concurrency=1"
beat   = "uv run celery -A config beat --loglevel=INFO --schedule=$OX_DATA_DIR/celerybeat-schedule"

[services]
postgres = { extensions = ["pgcrypto"] }
redis    = {}

[tools]
node = "24"
```

The repo has two lockfiles, so ox's detected install is `npm ci` and `[build] commands` adds `uv sync` before the SPA build.

## Environment flow

- **`GREETING_TAG`, run time:** `greetings/tasks.py` reads it inside the worker on every task, so `GET /api/greeting/` returns `hello world oxzoo-django-celery_<GREETING_TAG>`.
- **`GREETING_TAG`, build time:** `vite.config.js` sets `envPrefix: ["GREETING_", "VITE_"]`, so the value present during `npm run build` is baked into the bundle. ox sets your variables before the build, and changing one with `ox vars set` redeploys, which rebuilds the SPA.
- **`SECRET_KEY`:** Django's signing key. Generate it on the review screen (or with `--generate SECRET_KEY`).
- **`DATABASE_URL`, `REDIS_URL`:** provided by ox from `[services]`. `config/settings.py` uses `REDIS_URL` for both the Celery broker and the result backend.
- **`ALLOWED_HOSTS`:** `settings.py` allows `PUBLIC_HOST`, which ox provides, plus `127.0.0.1`. Set `ALLOWED_HOSTS` (comma-separated) only to override it. `DJANGO_DEBUG` defaults to `false`.

## Deploy with ox

```sh
curl -fsSL https://deploywithox.com/install.sh | sh
ox login
ox new https://github.com/saurav-codes/oxzoo-django-celery
printf 'GREETING_TAG=demo\n' | ox review oxzoo-django-celery --generate SECRET_KEY --from-file - --wait
```

The plan, offline:

```console
$ ox check .
ox check . (manifest: ox.toml)

  app.start                  uv run gunicorn config.wsgi:application --bind 127.0.0.1:$PORT --workers 2 declared
  app.health                 /health                                              declared
  static.dir                 dist                                                 declared
  static.spa                 true                                                 declared
  static.api                 /api, /health                                        declared
  build.install              npm ci                                               detected:package-lock.json
  build.commands[0]          uv sync --frozen --no-dev                            declared
  build.commands[1]          npm run build                                        declared
  build.migrate              uv run python manage.py migrate --noinput            declared
  workers.beat               uv run celery -A config beat --loglevel=INFO --schedule=$OX_DATA_DIR/celerybeat-schedule declared
  workers.worker             uv run celery -A config worker --loglevel=INFO --concurrency=1 declared
  tools.node                 24                                                   declared
  tools.python               3.13                                                 detected:.python-version
  tools.uv                   0.11                                                 default
  services.postgres          postgres 18 (shared)                                 default
  services.redis             redis 8 (only for this project)                      default

  Provided by ox: PORT, HOST, OX_ENV, OX_PROJECT, OX_RELEASE, OX_DATA_DIR, PUBLIC_URL, PUBLIC_HOST, DATABASE_URL, REDIS_URL
  Set on the dashboard before the first deploy: GREETING_TAG, SECRET_KEY (Django or Flask key: 64 random characters, Generate makes it)

Ready to deploy.
```

## Expected output

With `GREETING_TAG=demo`:

```
build-time: hello world oxzoo-django-celery_demo
api: {"greeting":"hello world oxzoo-django-celery_demo","celery":"ok","visits":3,"worker_visits":2}
slow: {"rows":50000,"total":1249975000}
```

- `build-time` is baked into the JS bundle; `api` is `GET /api/greeting/`. `worker_visits` is the count the worker read from Postgres before this request, so a healthy round trip shows `worker_visits == visits - 1`.
- `GET /api/slow/` aggregates the seeded `Sample` table.
- `GET /api/long/?seconds=45` enqueues a `long_job` and returns its task id; `GET /api/jobs/` lists the rows. `finished: true` after a deploy that restarted the worker proves the task was redelivered and finished once.
- `GET /health/` returns `{"ok": true}` (`/health` redirects to it).
- `ox logs oxzoo-django-celery --process worker` shows the beat heartbeat every 60 seconds.

## Local development

1. `uv sync`
2. Start Redis and PostgreSQL locally and export `DATABASE_URL` and `REDIS_URL`, or rely on the defaults (SQLite, and Redis on `127.0.0.1:6379`).
3. `uv run python manage.py migrate --noinput`
4. Web: `uv run python manage.py runserver`
5. Worker: `uv run celery -A config worker --loglevel=INFO --concurrency=1`
6. Beat: `uv run celery -A config beat --loglevel=INFO --schedule /tmp/oxzoo-django-celery-beat`
7. SPA: `npm install`, then `npm run dev` (or `npm run build`)
