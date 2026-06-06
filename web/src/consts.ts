export const LANGS = [
  { code: "en", locale: "en-GB", name: "English" },
  { code: "es", locale: "es-ES", name: "Español" },
  { code: "it", locale: "it-IT", name: "Italiano" },
  { code: "pt", locale: "pt-PT", name: "Português" },
] as const;

export type LangCode = (typeof LANGS)[number]["code"];

export const DEFAULT_LANG: LangCode = "en";
export const SITE_URL = "https://www.wanderandtales.com";
export const REPO = "https://github.com/agigante80/wander-and-tales";
export const CREATE_URL = REPO + "#create-your-own-story";

// Cloudflare Web Analytics (manual snippet). Cookieless, so no consent banner is
// required. Leave empty to disable the beacon.
export const CF_ANALYTICS_TOKEN = "56fc568a95f043f08d532a9ecd317322";

export const localeOf = (code: string) =>
  (LANGS.find((l) => l.code === code) ?? LANGS[0]).locale;
export const codeOfLocale = (locale: string) =>
  (LANGS.find((l) => l.locale === locale) ?? LANGS[0]).code;
