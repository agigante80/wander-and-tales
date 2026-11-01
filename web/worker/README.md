# Contact form Worker

`index.js` serves the static site and handles `POST /api/contact`, the only
contact route the site has. wanderandtales.com takes no email (null MX, SPF
`-all`, DMARC `p=reject`), so the site never shows an address and never sends
From its own domain. Each message is:

1. checked with Cloudflare Turnstile (plus a hidden honeypot field),
2. stored in the D1 database `wander-and-tales-contact` (deleted after 365
   days by the daily cron in `wrangler.jsonc`, as the privacy notice says),
3. forwarded through Resend's shared sender `onboarding@resend.dev` to the
   `CONTACT_TO` secret, with the visitor's address only in `Reply-To`.

The visitor sees success only when the forward worked. If it fails, they are
told to try again later, and the D1 copy is kept with `sent = 0`.

Resend's shared sender only delivers to the address the Resend account was
registered with, so `CONTACT_TO` must be that address. It is a secret: never
put it in the site, the repo, or a commit message.

## One-time setup (needs `npx wrangler login`)

```bash
cd web
# 1. D1: create, then add the printed binding to wrangler.jsonc as
#    "d1_databases": [{ "binding": "DB", "database_name": "wander-and-tales-contact", "database_id": "..." }]
npx wrangler d1 create wander-and-tales-contact
npx wrangler d1 execute wander-and-tales-contact --remote --file worker/schema.sql

# 2. Turnstile: create a widget for www.wanderandtales.com in the Cloudflare
#    dashboard; put the site key in src/consts.ts (TURNSTILE_SITE_KEY), then:
npx wrangler secret put TURNSTILE_SECRET

# 3. Resend: create an API key (sending access) in the Resend account, then:
npx wrangler secret put RESEND_API_KEY
npx wrangler secret put CONTACT_TO
```

## Reading stored messages

```bash
npx wrangler d1 execute wander-and-tales-contact --remote \
  --command "SELECT id, created_at, topic, name, email, message FROM messages ORDER BY id DESC LIMIT 20"
```

Messages whose forward failed (check these after any Resend or secret change):

```bash
npx wrangler d1 execute wander-and-tales-contact --remote \
  --command "SELECT id, created_at, topic, email, message FROM messages WHERE sent = 0 ORDER BY id DESC"
```

## Local test

Turnstile's test keys always pass: site key `1x00000000000000000000AA`,
secret `1x0000000000000000000000000000000AA`. Put the secret in
`web/.dev.vars` (gitignored) as `TURNSTILE_SECRET=...` and run
`npm run build && npx wrangler dev`.
