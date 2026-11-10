# Data dictionary

## users
- email: unique user login, stored in lowercase.
- display_name: visible name in the UI.
- role: one of student, member, commission_head, secretary.
- grade: school grade 5–11.
- class_letter: optional class letter.

## commissions
- name: commission name.
- slug: stable URL slug.
- description: summary text.
- sort_order: display ordering.

## ideas
- title: short title up to 120 characters.
- body: description up to 2000 characters.
- status: submitted, under_review, in_progress, done, rejected.
- commission: optional linked commission.
- author: user who submitted the idea.
- vote_count: cached count of votes.

## appeals
- kind: review or proposal.
- visibility: public or private.
- status: new, in_progress, resolved, declined.
- subject: short summary.
- body: full message content.

## anonymous_metrics
- date: local calendar date of the aggregate.
- section: allowlisted site section, never a URL or query string.
- page_views: total consented page views for that date and section.
- No IP address, account, email, session, referrer, or per-visitor identifier is stored.
