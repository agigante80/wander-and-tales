// Per-page audit with Google Lighthouse (SEO, Best Practices, Accessibility,
// Performance). Usage:
//   1) npm run preview   (serves the built site on http://localhost:4321)
//   2) npm run audit     (opens the report; scans every page)
export default {
  site: "http://localhost:4321",
  scanner: {
    // Pages carry hreflang / x-default pointing at the production domain, so
    // without this Unlighthouse treats the local pages as i18n duplicates and
    // skips them all. Disable that dedup for local auditing.
    ignoreI18nPages: false,
  },
};
