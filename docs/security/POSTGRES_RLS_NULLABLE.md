# PostgreSQL RLS — `facility_id` nullable

`NULL` is never interpreted as "globally visible" by default.

## Protected tables

- `data_breaches`: facility rows are visible only in that facility; `facility_id=NULL` is national and SUPER_ADMIN-only.
- `user_feedback`: users can read their own feedback; ADMIN can triage feedback in their facility; only ADMIN/SUPER_ADMIN can update/delete.
- `notifications`: read/update/delete are recipient-scoped; insert is restricted to a trusted authenticated context and same-facility/self scope.

## Explicit control-plane exemptions

- `users`: authentication must resolve a user before tenant context exists. Application auth/RBAC remains authoritative; a future hardening can use a dedicated auth DB role or SECURITY DEFINER lookup.
- `refresh_tokens`: token rotation/refresh happens before normal authenticated tenant context.
- `audit_logs`: login/security events can be emitted before tenant context and global security events legitimately have no facility. API read access remains RBAC/facility-scoped; the table stays append-only at application level.

Migration `0032_nullable_facility_rls` fails if any other nullable `facility_id` table exists without an explicit classification. This makes future schema changes fail closed at migration time.
