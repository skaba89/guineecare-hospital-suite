"""User profile module — preferences, feedback, recent items (v1.1.0).

Provides the "me" endpoints that power user-side adoption features:
- `GET/PUT /api/v1/me/preferences` — locale, theme, page size, dashboard refresh
- `POST /api/v1/feedback` + `GET /api/v1/feedback` — in-app feedback channel
- `GET/POST /api/v1/me/recent` — recent items (patients, lab orders, etc.)

These endpoints support the change-management loop opened by v1.1: users
can submit feedback from the UI, admins can collect it per facility, and
each user keeps a personalized workspace.
"""
