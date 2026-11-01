-- D1 schema for contact-form messages (see worker/index.js).
-- Apply with: npx wrangler d1 execute wander-and-tales-contact --remote --file worker/schema.sql
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  lang TEXT NOT NULL,
  topic TEXT NOT NULL,
  name TEXT,
  email TEXT NOT NULL,
  message TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS messages_created_at ON messages (created_at);
