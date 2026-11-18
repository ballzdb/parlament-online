You are a senior full-stack developer. Build the web platform "Парламент.Online" from scratch in this folder and keep everything saved on GitHub as you go.

## Context
Student-parliament platform for Kharkiv University Lyceum. Students are scattered across Ukraine and abroad because of the war and study online. Information gets lost in chats and parliament results are invisible. The platform is one open place where students see what the parliament does, propose ideas, vote, send appeals, and track results. The core chain it must make visible: idea -> vote -> implementation -> report.
It must be simple to maintain and open-source later so other schools can reuse it.
Language: ALL user-facing text in Ukrainian. Code, comments, commit messages and README in English (plus a short Ukrainian section in the README).

## Tech stack (fixed)
- Python 3 + latest stable Django, SQLite, Django templates + HTMX (or minimal vanilla JS), plain CSS or Tailwind via CDN. No heavy frontend framework.
- Use Django's built-in auth, permissions and admin. Do NOT hand-roll password hashing or sessions.
- Config only via environment variables (python-dotenv): SECRET_KEY, DEBUG, ALLOWED_HOSTS, ANTHROPIC_API_KEY, ANTHROPIC_MODEL (default "claude-haiku-4-5"), email settings. Provide .env.example. Never hardcode or commit secrets.

## Git and GitHub rules (important)
1. First inspect the folder. If a Django project or git repo already exists, reuse it. Do not recreate it.
2. Make sure git is on branch main. Create .gitignore (.venv/, __pycache__/, *.pyc, db.sqlite3, .env, staticfiles/) BEFORE the first commit.
3. If there is no remote, create the repo with GitHub CLI: gh repo create parlament-online --private --source=. --remote=origin --push
   If gh is missing or not logged in, stop and tell me exactly which command to run. Keep the repo PRIVATE.
4. Commit small and often using Conventional Commits (feat:, fix:, test:, docs:, chore:). After every phase: run `python manage.py check` and the tests, commit, `git push`.
5. Never commit .env, db.sqlite3 or API keys.

## How to work
Work in phases. After each phase: tests pass, commit, push, give me a summary of max 5 lines, then STOP and wait until I say "continue".
If something is ambiguous, choose a sensible default and write it in docs/DECISIONS.md. Do not add features that are not listed here.

### Phase 1: Foundation
- Django project (settings module reading env vars), apps: accounts, kanban, ideas, appeals, support, moderation, analytics.
- Custom user model with unique case-insensitive email as login. Role field with 4 levels: student, member, commission_head, secretary. Enforce permissions on the BACKEND (mixins/decorators), never only in templates.
- Registration requires the configured school email domain, password, display name, and class. A six-digit email code must be confirmed before the account is activated; codes expire after 10 minutes and resend attempts are rate-limited. A secretary issues temporary passwords for resets.
- Commissions are a database model (admin can add more). Seed command creates: "Навчання", "Порядок", "Дозвілля". Also a command that creates demo data.
- Base layout, responsive navigation, home page explaining what the parliament does and showing latest public ideas and appeal statuses.

### Phase 2: Parliament workspace
- Kanban per commission: columns To do / In progress / Done. Cards have title, description, assignee (a member), deadline. Move cards between columns. Only members and above can edit. Students get a read-only view (transparency). Commission hub page per commission.
- Ideas incubator: students submit ideas (title, description, commission/category). List with sorting by votes and date. ONE vote per user per idea, enforced by a database unique constraint. Status lifecycle: submitted -> under review -> in progress -> done / rejected (with reason). Members change statuses. When done, a public completion report text is shown.

### Phase 3: Communication
- Appeals wall (complaints and proposals): author sends an appeal, statuses new / in progress / resolved, official response from parliament. The author sees and tracks their own appeals. Public wall entries do NOT show the author's name, but parliament always sees the author.
- Direct line: private message thread between a student and parliament leaders (commission_head, secretary). Only participants can read it.

### Phase 4: AI features (Anthropic Python SDK)
- Moderation: before publishing ideas, comments and appeals, send the text to the Claude API and request a structured JSON verdict (insults, spam, profanity in Ukrainian/Russian/English, inappropriate content). Flagged items go to a manual review queue for the secretary. If ANTHROPIC_API_KEY is missing, use a simple local keyword filter. If the API call fails, put the item in the manual review queue.
- Support chatbot: floating chat widget that answers ONLY questions about using the platform (register, submit an idea, check appeal status), based on a FAQ file in the repo. Refuse unrelated topics. Per-user rate limit (20 messages/hour) and max_tokens cap. Clearly label it as AI. Do not store sensitive data. Everything must still run without an API key (chatbot shows "unavailable").

### Phase 5: Analytics, quality, docs
- EventLog model (user, action type, related object, timestamp) recording registrations, logins, votes, ideas, appeals, card moves and status changes. I will use it for a before/after engagement study.
- Dashboard for members and above: counts of ideas, votes and appeals by status, active users per week, activity per commission, funnel idea -> voted -> in progress -> done. CSV export of event log and stats with anonymised user IDs (no emails).
- Tests: role access matrix, vote uniqueness, registration confirmation flow, moderation fallback (mock the API), appeal privacy.
- Security pass: CSRF, permission check in every view, output escaping, rate limit on login and registration, secure cookie settings when DEBUG=False.
- README (Windows and Linux setup, env vars, running tests, structure, roles), MIT LICENSE, short CONTRIBUTING, deployment notes (do not deploy).

## Out of scope
Gamification, lifehacks database, advanced analytics. These are a later phase.

Start with Phase 1 now.