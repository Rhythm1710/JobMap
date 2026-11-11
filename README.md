# JobMap

JobMap tracks job applications for one person (the repo owner). The Next.js app is the product: add, edit, filter, and review applications. A Python service reads Gmail and writes the same Postgres database, so application emails show up as jobs instead of being typed in by hand.

Phase 2 (a browser agent that applies with approval, and a LinkedIn referral workflow) is not built. The Python package `backend/app/agents` only reserves the interfaces those flows will plug into.

## Architecture

- **Next.js app** (`frontend/`) — UI, Clerk auth, Prisma. Deploy on Vercel.
- **Ingestion service** (`backend/`) — FastAPI. Gmail OAuth, sync, classification. Deploy on Railway.
- **Postgres** — one database. Prisma owns the schema and migrations. The Python service maps the same tables and does not create them.

Clerk is the only user identity. Rows are keyed by `clerkId`. The browser never calls the Python service. Server actions send `Authorization: Bearer $SERVICE_SECRET` plus the Clerk user id.

Gmail uses the web OAuth authorization-code flow with the `gmail.readonly` scope. Refresh tokens are encrypted with Fernet before they are stored. The Next.js app never reads token columns.

## Status values

Existing rows are migrated by `frontend/prisma/migrations/20261110120000_gmail_tracking`:

| Old value | New value |
| --- | --- |
| `pending` | `applied` |
| `declined` / `decline` | `rejected` |
| `interview` | `interview` |

Current statuses: `applied`, `assessment`, `interview`, `offer`, `rejected`, `ghosted`, `withdrawn`.

`source` is `manual`, `gmail`, or `agent` (`agent` is reserved). A Gmail message id is stored once per user. Separate threads for the same company and role update that job instead of inserting another row. Sync does not move a status backward. An offer is left in place if a later email looks like a rejection. Editing the company, role, location, mode, or job URL marks the row so later syncs do not overwrite those fields. Status can still advance.

## Local setup

### 1. Database and Clerk

Create a Postgres database and a Clerk application. Copy `frontend/.env.example` to `frontend/.env` and fill it in.

```bash
cd frontend
npm install
npx prisma migrate deploy
npm run dev
```

The app runs at http://localhost:3000. Sign in with Clerk, then use Add job.

### 2. Ingestion service

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env`. Generate the two secrets:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the first value in `SERVICE_SECRET` on both apps. Put the Fernet key in `TOKEN_ENCRYPTION_KEY`.

```bash
uvicorn app.main:app --reload --port 8000
```

`GET /health` returns `{"ok": true}`.

### 3. Google OAuth client

1. In Google Cloud, create a project and enable the **Gmail API**.
2. Configure the OAuth consent screen. For a single personal account, External + Testing, and add the Gmail address as a test user, is enough to start. See the caveat below about refresh-token lifetime.
3. Create an OAuth client of type **Web application**.
4. Authorized redirect URI. Google must send the browser back to the Next.js app, which is where the connect cookie lives:
   - Local: `http://localhost:3000/api/gmail/callback`
   - Vercel: `https://<your-app>/api/gmail/callback`
5. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` on the Python service. `GOOGLE_REDIRECT_URI` is the Next.js callback above, not a Railway URL.
6. Set `APP_URL` to the Next.js origin (`http://localhost:3000` or the Vercel URL) with no path and no trailing slash.

In the app, open Jobs and choose **Connect Gmail**. After Google redirects back, choose **Sync now**. The same import runs on a schedule (below).

Classification uses rules first (application received, online assessment / HackerRank / CodeSignal, interview, rejection, offer). Set `LLM_API_KEY` to also call an OpenAI-compatible chat API for mail the rules are unsure about. `LLM_BASE_URL` and `LLM_MODEL` select the provider. With no key, sync still imports the mail the rules recognize.

## Deploy

### Vercel (Next.js)

- Root directory: `frontend` (or set the install/build commands to run there).
- Build command: `prisma generate && next build` (already the `build` script).
- Environment: `DATABASE_URL`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `PYTHON_SERVICE_URL` (the Railway URL), `SERVICE_SECRET`.
- Apply migrations from a machine that can reach the database:

```bash
cd frontend
DATABASE_URL="postgresql://..." npx prisma migrate deploy
```

If Vercel uses a pooled connection string, run the migration with the direct URL. The Python service should use the direct URL as well. Prisma query parameters such as `pgbouncer` and `schema` are stripped before SQLAlchemy connects.

### Railway (Python)

- Root directory: `backend`. `railway.toml` starts uvicorn and checks `/health`.
- Set every variable in `backend/.env.example`. `DATABASE_URL` and `SERVICE_SECRET` must match the database and the Vercel app. `APP_URL` is the Vercel origin. `GOOGLE_REDIRECT_URI` is `https://<your-app>/api/gmail/callback`, and that exact URI must be on the Google client.

Scheduled sync, pick one:

- **Railway cron** (preferred when you do not want a second copy running): schedule `0 */6 * * *` and run

```bash
curl -fsS -X POST -H "Authorization: Bearer $SERVICE_SECRET" "$PYTHON_SERVICE_URL/internal/cron/sync"
```

Leave `SYNC_INTERVAL_MINUTES` at `0`.

- **In-process scheduler**: set `SYNC_INTERVAL_MINUTES` (for example `360`) and do not also add the cron, or each account will sync twice.

`POST /gmail/sync` is what **Sync now** calls for the signed-in user. Both paths are safe to re-run.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

The tests cover fixture emails (confirmation, assessment, interview, rejection, offer, newsletter), status merging, same-thread and same company/role dedup, manual-edit locking, a second sync that does not insert duplicates, and the Gmail OAuth browser-cookie binding (matching cookie, missing cookie, and mismatched cookie).

```bash
cd frontend
npm test
npm run lint
npm run build
```

GitHub Actions (`.github/workflows/ci.yml`) runs the Python tests, and the frontend cookie tests, lint, and build, on pull requests and on pushes to `main`.

## Phase 2

Not in this change. `backend/app/agents/base.py` describes an approval queue, a Playwright apply agent that must stop before submit, and a LinkedIn referral flow with a low daily cap and per-message approval. Those types are not mounted on the API and have no tables yet.

## License

[MIT](https://choosealicense.com/licenses/mit/)
