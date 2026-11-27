# JobMap

JobMap tracks job applications for one person (the repo owner). The Next.js app is the product: add, edit, filter, and review applications. A Python service reads Gmail and writes the same Postgres database, so application emails show up as jobs instead of being typed in by hand.

Phase 2 (a browser agent that applies with approval, and a LinkedIn referral workflow) is not built. The Python package `backend/app/agents` only reserves the interfaces those flows will plug into.

## Architecture

- **Next.js app** (`frontend/`) — UI, Auth.js (Google) sign-in, Prisma. Deploy on Vercel.
- **Ingestion service** (`backend/`) — FastAPI. Gmail OAuth, sync, classification. Deploy on Railway.
- **Postgres** — one database. Prisma owns the schema and migrations. The Python service maps the same tables and does not create them.

Sign-in is Auth.js with the Google provider. The session is a JWT, and the user id is the Google account subject (`sub`). That id is stored in the existing `clerkId` column, and the Python service still receives it as `clerkId`, so the schema and the API do not change. The browser never calls the Python service. Server actions send `Authorization: Bearer $SERVICE_SECRET` plus that id.

Rows that already use a Clerk user id are kept. On sign-in, if exactly one `GmailConnection.email` matches the Google account email and that row's `clerkId` is still a Clerk id (`user_…`), `Job`, `GmailMessage`, and `GmailConnection` rows for that id are updated to the Google `sub`. Nothing is deleted. If two connections share the email, or Gmail was never connected, the rows are left as they are. In that case set the id once (after sign-in, `session.user.id` is the `sub`):

```sql
UPDATE "Job" SET "clerkId" = '<google-sub>' WHERE "clerkId" = '<clerk-user-id>';
UPDATE "GmailMessage" SET "clerkId" = '<google-sub>' WHERE "clerkId" = '<clerk-user-id>';
UPDATE "GmailConnection" SET "clerkId" = '<google-sub>' WHERE "clerkId" = '<clerk-user-id>';
```

Signing in and connecting Gmail are separate OAuth flows. Sign-in requests `openid`, `email`, and `profile`. Gmail connect requests `https://www.googleapis.com/auth/gmail.readonly` only. They can share one Google Cloud client or use two. A shared client needs both redirect URIs registered. Gmail refresh tokens are encrypted with Fernet before they are stored. The Next.js app never reads token columns.

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

### 1. Database and Google sign-in

Create a Postgres database and a Google OAuth client (below). Copy `frontend/.env.example` to `frontend/.env` and fill in `DATABASE_URL`, `AUTH_SECRET`, `AUTH_GOOGLE_ID`, and `AUTH_GOOGLE_SECRET`. `AUTH_TRUST_HOST` is optional: Vercel sets `VERCEL=1`, and the app sets `trustHost`, so production on Vercel does not need it. The Next.js build does not require the `AUTH_*` variables.

```bash
cd frontend
npm install
npx prisma migrate deploy
npm run dev
```

The app runs at http://localhost:3000. Sign in with Google, then use Add job.

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
4. Authorized JavaScript origins: `http://localhost:3000` and the deployed origin (for this app, `https://jobmap.rhythmarora.dev`).
5. Authorized redirect URIs. Sign-in and Gmail connect return to different paths on the Next.js app:
   - Sign-in (Auth.js), scopes `openid email profile`: `http://localhost:3000/api/auth/callback/google` and `https://jobmap.rhythmarora.dev/api/auth/callback/google`
   - Gmail connect, scope `https://www.googleapis.com/auth/gmail.readonly`: `http://localhost:3000/api/gmail/callback` and `https://jobmap.rhythmarora.dev/api/gmail/callback`
6. Put the client id and secret in `AUTH_GOOGLE_ID` and `AUTH_GOOGLE_SECRET` on the Next.js app. Put the same pair, or a second client's pair, in `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` on the Python service. `GOOGLE_REDIRECT_URI` is the Gmail callback above, not a Railway URL.
7. Set `APP_URL` to the Next.js origin (`http://localhost:3000` or `https://jobmap.rhythmarora.dev`) with no path and no trailing slash.

In the app, open Jobs and choose **Connect Gmail**. After Google redirects back, choose **Sync now**. The same import runs on a schedule (below).

Classification uses rules first (application received, online assessment / HackerRank / CodeSignal, interview, rejection, offer). For mail the rules are unsure about, set `LLM_API_KEY`. The client speaks the OpenAI chat API and is aimed at free tiers. The documented default is **Groq** with Llama 3.3 70B (`https://api.groq.com/openai/v1`, model `llama-3.3-70b-versatile`): create a key at https://console.groq.com/keys. Groq needs no extra headers, and that model is accurate enough for short recruiting mail. A personal sync stays inside the free rate limit because only uncertain messages are sent, bodies are truncated, calls are capped (`LLM_MAX_CALLS_PER_RUN`), and HTTP 429s are retried with backoff. If the model returns junk or the cap is hit, the rules result is kept.

Other free presets are commented in `backend/.env.example`:

- OpenRouter: `https://openrouter.ai/api/v1` and a `:free` model such as `meta-llama/llama-3.3-70b-instruct:free` (key at https://openrouter.ai/keys).
- Gemini's OpenAI-compatible endpoint: `https://generativelanguage.googleapis.com/v1beta/openai` and `gemini-2.5-flash` (key at https://aistudio.google.com/apikey).

With no key, sync still imports the mail the rules recognize.

Each sync also marks `applied` and `assessment` rows `ghosted` when the latest related email (or the applied date, if there is no email) is older than `GHOST_AFTER_DAYS` (default 30, `0` disables it). A later email on that application replaces `ghosted` with the new status. Rows whose status was chosen in the app (`statusManual`) are not auto-ghosted. A hand-added job is protected only when the chosen status is not the default `applied`; leaving it on `applied` keeps `statusManual` false, so it can still be auto-ghosted. Statuses set before this column existed are only protected when `source` is `manual`; a Gmail row whose status you corrected before the migration can still be auto-ghosted once.

## Deploy

### Vercel (Next.js)

- Root directory: `frontend` (or set the install/build commands to run there).
- Build command: `prisma generate && next build` (already the `build` script).
- Environment: `DATABASE_URL`, `AUTH_SECRET`, `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`, `PYTHON_SERVICE_URL` (the Railway URL), `SERVICE_SECRET`. `AUTH_TRUST_HOST` is not required on Vercel.
- Apply migrations from a machine that can reach the database:

```bash
cd frontend
DATABASE_URL="postgresql://..." npx prisma migrate deploy
```

That applies the Gmail tables and `20261111120000_status_manual`, which records owner-chosen statuses so they are not auto-ghosted.

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
