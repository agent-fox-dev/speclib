---
spec_id: '01'
spec_name: phase1
title: Phase1
status: draft
created_at: '2026-06-10T08:16:54.736583+00:00'
updated_at: '2026-06-10T08:16:54.736583+00:00'
owner: ''
source: interactive
schema_version: 1
---
# PRD

Let's add proper user management, API key management and multi-tennant support.

## Background

af-hub is a service to collect telemetry and audit data from running agent-fox instances. Over time, it will also 
serve as a "gateway" to controll individual agent-fox (AF) instances running on, e.g. VPSs or in Kubernetes pods.

For this, it must maintain an inventory of:

- GitHub repos (or other Git-forges) "under management" i.e. which are implemented or maintained by AF.
- User accessing the "hub". We keep a minimal record only: username/email, github/gitlab ID, which repo they have access to
- API keys for users & repos that can be used to a) access the hub API and b) by AF instances to report data

## Requirements

- af-hub creates ana dmin user and token on first initialization. This user/token is used to access the af-hub API as "root".
- af-hub CLI for user self-signup and basic API key management. Other functionallity will be added later.
- user sign-up / onboarding is strictly OAuth and via external identity providers: GitHub,GitLab,Google,Keycloak for now.
- all API calls must be "user and repo aware". Based on the provided access/bearer token, af-hub will know which repo and user the call is associated with.
- Basic RBAC is a must-have. For now having an API key for a repo allows full read/write access (editor role) but we will add more roles with different access policies in the future.
- All database tables mut be keyed with a "repo ID" and have provenance of who (which user) created the entry.
- API keys must be time-bound, i.e. have an expiration date after wich they are either invalid or must be renewed.
- Add endpoints needed for user management: create / modify a user via the API, create, update, expire API keys.
- User self-signup via configurable (1 or more) OAuth apps.


