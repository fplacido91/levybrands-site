# Terms versioning

## Version 1.0 archive

Deploy `terms/v1-0/` unchanged through the site's hosting process. The stable
archive page is `https://levybrands.com/terms/v1-0`; it displays and links to the
PDF dated with both its original effective date (2026-08-25) and capture date
(2026-09-30).

- `source/` preserves the original HTML, CSS and self-hosted font files without
  changing their wording or depending on the current terms stylesheet.
- `published-response.html` preserves the raw HTML received from the live site.
  Cloudflare's email protection is the only transformation relative to the
  original source, aside from line endings.
- `manifest.json` records the source commit, UTC capture time, HTTP response
  dates, file sizes and SHA-256 checksums, including the PDF checksum.
- The PDF preserves the original print layout and wording, including the
  original seller definition and section 5.14. Its additional footer identifies
  the archive URL, version, capture date and page count.

The capture date records when this snapshot was saved; it does not change the
original effective date or establish an independently certified timestamp.
Never overwrite this archive, regenerate its PDF in place, or redirect its URL
to the current terms. Leave the existing `/terms/v1` route intact as well.

## Required publication sequence

1. Deploy the Version 1.0 archive **before editing the current terms**.
2. Verify that `/terms/v1-0`, its dated PDF and its source snapshot are publicly
   accessible, and that the downloaded PDF's SHA-256 matches `manifest.json`.
3. Obtain the approved memo. Copy its replacement wording and apply its exact
   renumbering and cross-reference changes; do not infer legal language.
4. Publish the current terms as Version 1.1 with the approved new effective
   date visible in both the header and footer. Update the page's structured
   modification date and relevant descriptive metadata consistently.
5. Verify the published wording and references against the memo, and recheck
   that the Version 1.0 archive and its checksums remain unchanged.

A local archive is not completion of step 1: the stable public URL and PDF must
be deployed and verified before changes to `terms/index.html`.
