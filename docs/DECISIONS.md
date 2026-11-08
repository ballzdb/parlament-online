# Project decisions

- Used Django's built-in auth with a custom email-based user model to match the requirement for email login and role-based access.
- Kept the initial implementation focused on the Phase 1 foundation: custom user model, commissions, registration, auth flow, home page and core app skeletons.
- Defaulted all unspecified platform behavior to the simplest robust option and kept user-facing copy in Ukrainian while code and commands remain in English.
- Commission choices are seeded idempotently via `seed_default_commissions`, with hidden entries kept for historic records and visible entries used in new idea forms.
- Social links are stored in `site_settings`, validated as HTTPS-only links under 300 characters, and rendered as accessible SVG icon links in the site footer and homepage.
- The `set-role` CLI command updates the role and `is_staff` flag, writes an `AuditLog` record, and is designed to work without requiring a re-login because Django reloads the user from the database on the next request.
