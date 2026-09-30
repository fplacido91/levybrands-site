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

## Version 1.1

Version 1.1 is effective September 30, 2026. `terms/index.html` mirrors the legal
body of the permanent `terms/v1-1/index.html`. The permanent page has its own
frozen stylesheet and font assets, a dated PDF and a checksum manifest. The
Version 1.0 archive was published and its public PDF checksum verified before
these amendments were applied; that verification is recorded in the Version
1.1 manifest.

The approved replacement text and product-scope addition are checked against
`tests/fixtures/terms-v1-1-approved.json`. Run the wording, renumbering,
references, mirror and archive-integrity checks with:

```sh
python -m unittest discover -s tests -v
```

The tests use only Python's standard library. If `pdftotext` is available, they
also check that the PDF contains every clause.

Credit-agreement companion edits, invoice templates and the separate cabinet
terms page are outside this repository. Copy each dated PDF to the dealer-credit
archive in Dropbox and record which version each dealer received; website
publication alone does not perform those operational steps.

## Required publication sequence

1. Deploy the Version 1.0 archive **before editing the current terms**.
2. Verify that `/terms/v1-0`, its dated PDF and its source snapshot are publicly
   accessible, and that the downloaded PDF's SHA-256 matches `manifest.json`.
3. Obtain the approved memo. Copy its replacement wording and apply its exact
   renumbering and cross-reference changes; do not infer legal language.
4. Publish the new version at both the current URL and a new permanent version
   URL, with its effective date visible in both the header and footer. Freeze its
   CSS and assets at that version URL as well. Update the page's structured
   modification date and relevant descriptive metadata consistently.
5. Save and publish the new version's dated PDF and checksum manifest. Verify
   the published wording and references against the memo, and recheck that all
   prior archives and their checksums remain unchanged.

A local archive is not completion of step 1: the stable public URL and PDF must
be deployed and verified before changes to `terms/index.html`.
