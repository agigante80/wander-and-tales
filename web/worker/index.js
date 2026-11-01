// Wander & Tales Worker: serves the static site (env.ASSETS) and handles the
// contact form at POST /api/contact.
//
// Why this shape: wanderandtales.com takes no email at all (null MX, SPF -all,
// DMARC reject), so the site can neither receive mail nor send From its own
// domain. A message is therefore (1) kept in Cloudflare D1 so nothing is lost,
// and (2) forwarded to the maintainer's inbox through Resend's shared sender
// (onboarding@resend.dev), with the visitor's address only in Reply-To. The
// destination address is the CONTACT_TO secret and never appears in the site
// or the repo. Messages older than RETENTION_DAYS are deleted by the cron
// trigger declared in wrangler.jsonc (and stated in the privacy notice).
//
// Bindings and secrets (see web/worker/README.md):
//   DB               D1 database (optional until created; storage is skipped)
//   TURNSTILE_SECRET Turnstile secret key (required)
//   RESEND_API_KEY   Resend API key (required: success means forwarded)
//   CONTACT_TO       destination inbox, the Resend account's own address (required)

const RETENTION_DAYS = 365;
const LIMITS = { name: 100, email: 200, topic: 20, message: 5000 };
const TOPICS = ["privacy", "content", "other"];
const LANGS = ["en", "es", "it", "pt"];
const EMAIL_RE = /^[^\s@<>"]+@[^\s@<>"]+\.[^\s@<>"]+$/;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/contact" || url.pathname === "/api/contact/") {
      if (request.method !== "POST") {
        return new Response("Method not allowed", { status: 405, headers: { Allow: "POST" } });
      }
      return handleContact(request, env);
    }
    return env.ASSETS.fetch(request);
  },

  async scheduled(_event, env) {
    if (!env.DB) return;
    await env.DB.prepare("DELETE FROM messages WHERE created_at < datetime('now', ?1)")
      .bind(`-${RETENTION_DAYS} days`)
      .run();
  },
};

async function handleContact(request, env) {
  const wantsJson = (request.headers.get("Accept") || "").includes("application/json");
  let form;
  try {
    form = await request.formData();
  } catch {
    return reply(wantsJson, "en", 400, "invalid");
  }
  const field = (k) => String(form.get(k) ?? "").trim();
  const lang = LANGS.includes(field("lang")) ? field("lang") : "en";

  // Honeypot: bots fill the hidden "website" field. Pretend success.
  if (field("website")) return reply(wantsJson, lang, 200, "ok");

  const name = field("name");
  const email = field("email");
  const topic = TOPICS.includes(field("topic")) ? field("topic") : "other";
  const message = field("message");
  if (
    !email || !EMAIL_RE.test(email) || !message ||
    name.length > LIMITS.name || email.length > LIMITS.email || message.length > LIMITS.message
  ) {
    return reply(wantsJson, lang, 400, "invalid");
  }

  if (!env.TURNSTILE_SECRET || !(await turnstileOk(env, form.get("cf-turnstile-response"), request))) {
    return reply(wantsJson, lang, 403, "challenge");
  }

  // The forward is what reaches the maintainer, so it alone decides success:
  // a message only stored in D1 would never be read. The D1 row is the backup
  // copy, flagged sent=0 when the forward failed so it can be listed (README).
  const safeName = name.replace(/[\r\n]+/g, " ");
  let sent = false;
  if (env.RESEND_API_KEY && env.CONTACT_TO) {
    try {
      const res = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          from: "Wander & Tales contact <onboarding@resend.dev>",
          to: [env.CONTACT_TO],
          reply_to: email,
          subject: `[Wander & Tales] ${topic}: message from ${safeName || email}`,
          text: `Topic: ${topic}\nLanguage: ${lang}\nName: ${safeName || "(not given)"}\nEmail: ${email}\n\n${message}\n`,
        }),
      });
      sent = res.ok;
      if (!res.ok) console.error("contact: Resend failed", res.status, await res.text());
    } catch (err) {
      console.error("contact: Resend error", err);
    }
  } else {
    console.error("contact: RESEND_API_KEY or CONTACT_TO not set");
  }

  if (env.DB) {
    try {
      await env.DB.prepare(
        "INSERT INTO messages (created_at, lang, topic, name, email, message, sent) VALUES (datetime('now'), ?1, ?2, ?3, ?4, ?5, ?6)",
      )
        .bind(lang, topic, name, email, message, sent ? 1 : 0)
        .run();
    } catch (err) {
      console.error("contact: D1 insert failed", err);
    }
  }

  return sent ? reply(wantsJson, lang, 200, "ok") : reply(wantsJson, lang, 502, "failed");
}

async function turnstileOk(env, token, request) {
  if (!token) return false;
  const body = new FormData();
  body.append("secret", env.TURNSTILE_SECRET);
  body.append("response", String(token));
  const ip = request.headers.get("CF-Connecting-IP");
  if (ip) body.append("remoteip", ip);
  try {
    const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body });
    const data = await res.json();
    return data.success === true;
  } catch {
    return false;
  }
}

// JSON for the enhanced form; a 303 back to the page for a plain form post.
function reply(wantsJson, lang, status, result) {
  if (wantsJson) {
    return new Response(JSON.stringify({ ok: status === 200, result }), {
      status,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }
  return new Response(null, {
    status: 303,
    headers: { Location: `/${lang}/contact/?result=${result}`, "Cache-Control": "no-store" },
  });
}
