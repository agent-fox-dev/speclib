# PRD

## Intent

Enable the first external users to self-onboard to af-hub and authenticate AF instances against it via time-bound API keys.

## Background

af-hub is a service to collect telemetry and audit data from running agent-fox instances. Over time, it will also serve as a "gateway" to control individual agent-fox (AF) instances running on, e.g. VPSs or in Kubernetes pods.

For this, it must maintain an inventory of:

- GitHub repos (or other Git-forges) "under management" i.e. which are implemented or maintained by AF.
- Users accessing the "hub". We keep a minimal record only: username/email, GitHub/GitLab ID, which repo they have access to.
- API keys for users & repos that can be used to a) access the hub API and b) by AF instances to report data.

## Goals

- All API endpoints for user management, API key management, and multi-tenant (repo-scoped) access are implemented and validated through end-to-end tests.
- A new external user can self-onboard via OAuth and receive a working API key without admin intervention.
- All API endpoints return HTTP 401 for expired or invalid tokens within a single request cycle.

## Non-Goals

The following are explicitly out of scope for Phase 1:

- Billing and subscription management.
- Advanced RBAC roles beyond the `editor` role (e.g. `viewer`, `admin`, `read-only`).
- AF instance gateway / control-plane features (remote control of AF instances).
- Audit log querying UI or any frontend beyond the CLI.
- Organisation or workspace-level tenant grouping (multiple repos under a shared tenant entity).

## Multi-Tenancy Model

**Repo is the tenant boundary.** Every database table is keyed by a `repo_id`. All API calls are scoped to a single repo, derived from the bearer token presented with the request. There is no higher-level organisation or workspace concept in Phase 1.

A user may have access to multiple repos, but each access grant is stored as a discrete record associating `(user_id, repo_id)`.

## Requirements

### Bootstrap / Initialization

- On first initialization, af-hub creates an admin user and a long-lived bootstrap API key. This key acts as the "root" credential for initial setup.
- The bootstrap token is printed to stdout **once** at initialization time and never stored in plaintext; subsequent retrieval is not possible without generating a new token.
- The bootstrap token has a configurable expiry (default: 90 days) and can be rotated by the admin via the API.

### User Management

- User records are minimal: `username`, `email`, `oauth_provider`, `provider_account_id`, `created_at`, `created_by`.
- **Identity federation:** Email is the canonical identity. If a user authenticates via a second OAuth provider using the same email address, the new provider is automatically linked to the existing account (auto-merge). No duplicate accounts are created.
- Users can be created or modified via the API (admin-only for direct manipulation).
- All database entries carry provenance fields: `repo_id`, `created_by` (user ID), `created_at`.

### Authentication & OAuth Onboarding

- User self-signup and login are strictly via OAuth through external identity providers. Supported providers in Phase 1: **GitHub, GitLab, Google, Keycloak**.
- On first login (new email), an account is automatically provisioned.
- On subsequent logins, the session is resumed and any new OAuth provider for the same email is linked to the existing account.
- OAuth scopes required: at minimum `email` and `profile` (or provider equivalent) to obtain a verified email address.

### API Key Management

- API keys are **time-bound** and carry an explicit expiration date.
- Keys are stored as **bcrypt or argon2 hashes only**; the plaintext key is shown to the user **once** at creation time and is never retrievable afterwards.
- On renewal, a **new key is issued** and the **old key is immediately invalidated** — there is no grace period.
- Keys can be created, updated (e.g. extend expiry), and expired (revoked) via the API.
- Possessing an API key for a repo grants `editor` role: full read/write access to that repo's resources.

### RBAC

- Phase 1 defines a single role: **`editor`** — full read/write access scoped to a repo.
- The role model is designed to be extensible; additional roles and permission policies will be added in future phases without requiring a schema migration.

### API Design

- All API calls must be **user- and repo-aware**: the bearer token presented with each request determines both the user identity and the repo scope.
- Endpoints required in Phase 1:
  - **Users:** create user, modify user.
  - **API Keys:** create key, update key (e.g. extend expiry), expire/revoke key.
- All endpoints return HTTP 401 for expired, revoked, or malformed tokens.

### CLI

The af-hub CLI is in scope for Phase 1 with the following commands only:

| Command | Description |
|---|---|
| `signup` | Initiate OAuth-based user self-signup flow |
| `login` | Authenticate an existing user via OAuth and store a local session token |
| `logout` | Invalidate the local session token |

Additional CLI commands (e.g. repo management, key rotation helpers) are deferred to future phases.

## Non-Functional Requirements

### Security

- API keys are stored exclusively as **bcrypt or argon2** hashes. Plaintext is displayed once at creation and never persisted.
- The API **must** enforce TLS for all endpoints in production deployments.
- API keys must have sufficient entropy (minimum 256 bits / 32 random bytes before encoding).

### Extensibility

- The RBAC model and database schema must be designed to accommodate additional roles and tenant-hierarchy levels without breaking changes.
