# API Format Configuration Design

## Goal

Replace vendor-specific model selection with three transport formats:

1. OpenAI Chat Completions
2. OpenAI Responses
3. Anthropic Messages

Users configure an API format, public HTTPS Base URL, API Key, model name, and review preset. The Vercel backend remains stateless.

## User experience

- The API settings page shows three format choices instead of six vendor choices.
- Each format supplies an editable default Base URL and a format-specific endpoint hint.
- Connection validation requires all four connection fields.
- Sidebar, workbench, and assistant identify the selected format rather than a vendor.
- Existing browser configuration is migrated from the previous vendor ID to the equivalent format and official Base URL.

## Request contracts

### OpenAI Chat Completions

- Endpoint: `<base_url>/chat/completions`
- Authentication: `Authorization: Bearer <key>`
- Body: `model`, `messages`, `max_completion_tokens`
- Output: `choices[0].message.content`

### OpenAI Responses

- Endpoint: `<base_url>/responses`
- Authentication: `Authorization: Bearer <key>`
- Body: `model`, `instructions`, `input`, `max_output_tokens`, `store: false`
- Output: top-level `output_text`, falling back to text blocks in `output[].content[]`

### Anthropic Messages

- Endpoint: `<base_url>/v1/messages`
- Authentication: `x-api-key` plus `anthropic-version: 2023-06-01`
- Body: `model`, top-level `system`, `messages`, `max_tokens`
- Output: concatenated text blocks in `content[]`

## Base URL security

- Require HTTPS.
- Reject credentials, query strings, fragments, control characters, non-443 ports, localhost, and IP literals that are not globally routable.
- Resolve hostnames before each outbound request and reject any private, loopback, link-local, reserved, multicast, or unspecified address.
- Do not follow redirects and do not include upstream bodies in user-visible errors.
- Keep the Base URL out of server logs and API error messages.

DNS validation reduces SSRF risk but cannot provide a complete DNS-rebinding guarantee without a pinned resolver/transport. This limitation is documented explicitly.

## API and persistence migration

- Replace `/api/providers` with `/api/formats` and `/api/providers/validate` with `/api/formats/validate`.
- Review and chat requests use `api_format` and `base_url` instead of `provider`.
- Keep the existing localStorage key and migrate legacy provider fields on read.
- The next save writes only `apiFormat`, `baseUrl`, `apiKey`, `model`, and `preset`.

## Error handling

- Invalid Base URLs fail before any outbound call.
- Redirects fail explicitly instead of being followed.
- Authentication, balance, model, throttling, timeout, and provider availability errors remain sanitized Chinese messages.
- Unknown API formats return a client error.

## Testing and release

- Contract tests cover all three request/response formats.
- Security tests cover HTTPS enforcement, private IPs, DNS resolution, redirects, and sanitized errors.
- Frontend tests cover the three-format UI and legacy localStorage migration.
- Update runtime docs and production smoke checks.
- Run backend, skill, frontend, audit, and Vercel builds before pushing `main`, then deploy production and run external smoke checks.
