# Development Trace Security

The development trace endpoint is additive to the stable `/v1/engine` API and must not become an accidental production data surface.

## Access policy

- Local loopback hosts (`127.0.0.1`, `localhost`, `::1`) may use `/v1/engine/trace` without a token for the existing developer workflow.
- When `REVISE_TRACE_TOKEN` is configured, the endpoint always requires the matching `X-Revise-Trace-Token` header, including on localhost.
- When no token is configured, a non-loopback `REVISE_HOST` denies trace access with HTTP 403.
- The stable `/v1/engine` endpoint is unchanged by this policy.

## Rationale

Trace metadata is deliberately payload-safe, but it still exposes execution stages, model/provider metadata, verification state, and decision details. Protecting the development endpoint prevents accidental exposure when the HTTP server is bound beyond loopback.

The token is compared with a constant-time comparison. This is an access-control boundary, not authentication for the main engine API.
