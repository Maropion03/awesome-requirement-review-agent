# Permissions and data handling

| Actor | Can access | Cannot access by design |
| --- | --- | --- |
| Browser page | Selected local file bytes, Key entered on page, in-memory report/chat | Other local files, saved browser secrets, another user's data |
| Vercel Function | Current request body and provider response for the request lifetime | Durable user state, database, arbitrary outbound base URL |
| Selected provider | Prompt content required for the current review/chat and the provider account Key | Browser state outside the submitted request |
| Repository/deployer | Source and deployment configuration | A built-in production model Key, because none is configured |

## Key controls

- Password input with opt-in visibility toggle.
- `autocomplete="off"`; no persistence API is called.
- Maximum length and control-character validation.
- Fixed HTTPS provider hosts prevent user-controlled forwarding.
- API responses and provider catalog omit Key and base URLs.
- Upstream response bodies are not forwarded to the browser.

Each review sends the PRD to the selected provider once per dimension, for six concurrent model calls. The connection test, JSON repair, and report chat can add calls and therefore consume the user's provider quota.

## CORS

Production is same-origin. CORS is enabled only for the configurable local Vite origins in `LOCAL_DEV_ORIGINS`; credentials/cookies are disabled.

## Missing identity layer

There is intentionally no user identity, authorization role, or share token. The app is a stateless BYOK tool, so adding server persistence later requires a separate authentication and authorization design.
