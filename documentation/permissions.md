# Permissions and data handling

| Actor | Can access | Cannot access by design |
| --- | --- | --- |
| Browser page | Selected local file bytes, locally persisted model configuration, in-memory report/chat | Other local files, secrets from other origins, another user's data |
| Vercel Function | Current request body and provider response for the request lifetime | Durable user state, database, arbitrary outbound base URL |
| Selected provider | Prompt content required for the current review/chat and the provider account Key | Browser state outside the submitted request |
| Repository/deployer | Source and deployment configuration | A built-in production model Key, because none is configured |

## Key controls

- Password input with opt-in visibility toggle.
- `autocomplete="off"`; provider, model, preset, and Key are stored as plaintext in origin-scoped `localStorage`.
- A visible clear action removes the persisted configuration; shared devices should not retain it.
- Maximum length and control-character validation.
- Fixed HTTPS provider hosts prevent user-controlled forwarding.
- API responses and provider catalog omit Key and base URLs.
- Upstream response bodies are not forwarded to the browser.

Each review sends the PRD to the selected provider once per dimension, for six concurrent model calls. The connection test, JSON repair, and report chat can add calls and therefore consume the user's provider quota.

## CORS

Production is same-origin. CORS is enabled only for the configurable local Vite origins in `LOCAL_DEV_ORIGINS`; credentials/cookies are disabled.

## Missing identity layer

There is intentionally no user identity, authorization role, or share token. The app is stateless on the server; browser-local configuration persistence does not add cross-device sync or an authorization boundary. Adding server persistence later requires a separate authentication and authorization design.
