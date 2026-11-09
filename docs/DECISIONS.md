# Project decisions

- Used Django's built-in auth with a custom email-based user model to match the requirement for email login and role-based access.
- Kept the initial implementation focused on the Phase 1 foundation: custom user model, commissions, registration, auth flow, home page and core app skeletons.
- Defaulted all unspecified platform behavior to the simplest robust option and kept user-facing copy in Ukrainian while code and commands remain in English.
- Commission choices are seeded idempotently via `seed_default_commissions`, with hidden entries kept for historic records and visible entries used in new idea forms.
- Social links are stored in `site_settings`, validated as HTTPS-only links under 300 characters, and rendered as accessible SVG icon links in the site footer and homepage.
- The `set-role` CLI command updates the role and `is_staff` flag, writes an `AuditLog` record, and is designed to work without requiring a re-login because Django reloads the user from the database on the next request.
- Registration immediately activates the account and requires only the school-domain email, password, display name, and one class field (grades 5–11 with an optional letter, e.g. `9-А`). No email confirmation, allowlist, verification-code, or email-outbox tables are used; a secretary can issue a one-time temporary password that must be changed on next login.
- Appeal submissions require sign-in so Parliament can privately identify and respond to the author; public appeal listings always hide the author's name and email. Students can see public appeals and their own private appeals, while Parliament roles can see the author and all submissions.
