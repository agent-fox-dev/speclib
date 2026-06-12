# af-hub creation example

## Init

spec init hub_example --description "create the af-hub"

spec -C hub_example new --name "phase1" prd.md

spec -C hub_example status

---

## PRD refinement

spec -C hub_example assess 01_phase1

Quality: needs_refinement
Summary: The PRD for "phase1" covers user management, API key management, and multi-tenant support for af-hub. It provides a solid background section and a reasonable list of requirements, but it lacks a dedicated **Intent** statement (the goal is implied rather than explicitly stated), has no formal **Goals** section with measurable outcomes, and has no **Non-Goals** section to bound scope. The requirements themselves also contain several ambiguities that need resolution before artifact generation can proceed safely.

Gaps:
  1. Missing dedicated 'Intent' section — the purpose of Phase 1 is implied across the background and requirements but never concisely stated as a single authoritative statement.
  2. No 'Goals' section with measurable, verifiable outcomes (e.g., success metrics, acceptance criteria, SLOs).
  3. No 'Non-Goals' section — scope boundaries are entirely absent, making it unclear what is deliberately excluded from Phase 1.
  4. Multi-tenancy model is underspecified: 'repo' appears to be the tenant boundary, but the relationship between users, repos, and tenants is not formally defined.
  5. RBAC is mentioned as a must-have but only one role ('editor') is defined; the role model and permission matrix are missing.
  6. API key renewal/rotation flow is unspecified — it is unclear whether renewal is automatic, user-initiated, or admin-initiated, and whether the old key is immediately invalidated.
  7. OAuth onboarding flow details are missing: which OAuth scopes are required, how identity federation works across providers (e.g., same email on GitHub and Google = one user?), and what happens on first login vs. subsequent logins.
  8. The 'admin user and token on first initialization' (bootstrap) mechanism lacks detail: how is the token delivered, what is its expiry, and can it be rotated?
  9. CLI scope is vague — 'user self-signup and basic API key management' does not enumerate which specific CLI commands are in scope for Phase 1.
  10. No non-functional requirements are stated: security standards (e.g., token hashing algorithm, TLS requirements), performance targets, or availability expectations.
  11. Owner field is empty — accountability for this PRD is unassigned.

Questions:
  q1: Can you provide a concise Intent statement for Phase 1? What is the single most important outcome this phase must deliver?
  q2: What are the measurable success criteria / goals for Phase 1? For example: 'An admin can onboard a new user end-to-end in < 5 minutes', 'All API endpoints return 401 for expired tokens within 1 request cycle', etc.
  q3: What is explicitly OUT of scope for Phase 1? For example: billing, advanced RBAC roles beyond 'editor', AF instance gateway/control-plane features, audit log querying UI, etc.
  q4: What is the tenant boundary in the multi-tenant model? Is a 'repo' the tenant, or is there a higher-level concept (e.g., 'organisation' or 'workspace') that owns multiple repos?
  q5: How should identity federation across OAuth providers be handled? If a user signs up with GitHub and later logs in with Google using the same email, should they be treated as the same user?
  q6: What is the API key renewal/rotation model? When a key expires, what must happen?
  q7: Which specific CLI commands are in scope for Phase 1?
  q8: What are the security requirements for API key storage and transport? For example: must keys be stored as hashes only (never in plaintext), must the API enforce TLS, what is the minimum key entropy?

---

spec -C examples/hub_example refine 01_phase1 > examples/hub_example/qa1.json

spec -C examples/hub_example refine 01_phase1 --answers examples/hub_example/qa1.json

--- 
same as above for qa2.json, qa3.json

---

## Finaize the spec

spec -C examples/hub_example accept 01_phase1

spec -C examples/hub_example generate 01_phase1