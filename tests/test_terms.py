"""Check approved wording, numbering, mirrors and immutable terms archives.

Run with: python -m unittest discover -s tests -v
Only Python's standard library is required.
"""

from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
APPROVED = json.loads(
    (ROOT / "tests/fixtures/terms-v1-1-approved.json").read_text(encoding="utf-8")
)


def normalize(text):
    return " ".join(text.split())


class Node:
    def __init__(self, tag, attrs=()):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []

    def text(self):
        if self.tag == "br":
            return " "
        return "".join(
            child if isinstance(child, str) else child.text()
            for child in self.children
        )

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()

    def by_class(self, name):
        return [node for node in self.walk() if node.has_class(name)]


class Document(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.feed(source)
        self.close()
        assert len(self.stack) == 1, "Unclosed HTML element"

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        assert self.stack[-1].tag == tag, f"Unexpected </{tag}>"
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def clauses(self):
        result = {}
        for node in self.root.by_class("clause"):
            numbers = node.by_class("clause-number")
            if numbers:
                number = normalize(numbers[0].text())
                text = node.text().strip()
                assert text.startswith(number), number
                text = text[len(number):]
            else:
                number = "11"  # The original force-majeure section is unnumbered.
                text = node.text()
            assert number not in result, f"Duplicate subsection {number}"
            result[number] = normalize(text)
        return result


def read_document(path):
    return Document((ROOT / path).read_text(encoding="utf-8"))


class TermsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = read_document("terms/index.html")
        cls.permanent = read_document("terms/v1-1/index.html")
        cls.original = read_document("terms/v1-0/source/terms/index.html")
        cls.clauses = cls.current.clauses()
        cls.old_clauses = cls.original.clauses()

    def test_exact_approved_replacements(self):
        for number, expected in APPROVED["clauses"].items():
            with self.subTest(number=number):
                self.assertEqual(self.clauses[number], normalize(expected))
        for number, appendix in APPROVED["appendices"].items():
            with self.subTest(number=number):
                self.assertEqual(
                    self.clauses[number],
                    normalize(self.old_clauses[number] + " " + appendix),
                )

    def test_unchanged_and_renumbered_original_wording(self):
        replaced = {"1.1", "5.2", "5.9", "5.14", "10.1", "12.4"}
        renumbered = {"1.2": "1.4", "1.3": "1.5", "10.2": "10.3", "10.3": "10.4"}
        for number, original in self.old_clauses.items():
            if number not in replaced:
                target = renumbered.get(number, number)
                with self.subTest(original=number, target=target):
                    self.assertEqual(self.clauses[target], original)

    def test_section_and_subsection_numbering(self):
        counts = {1: 6, 2: 2, 3: 3, 4: 3, 5: 15, 6: 2, 7: 5, 8: 5, 9: 4, 10: 4, 11: 0, 12: 5, 13: 4}
        expected = []
        for section, count in counts.items():
            expected.extend(f"{section}.{subsection}" for subsection in range(1, count + 1))
            if section == 11:
                expected.append("11")
        self.assertEqual(list(self.clauses), expected)
        headings = [normalize(node.text()) for node in self.current.root.walk() if node.tag == "h2"]
        self.assertEqual([int(heading.split(".")[0]) for heading in headings], list(range(1, 14)))
        self.assertEqual(headings[0], "1. ACCEPTANCE; ENTIRE AGREEMENT; WHO THE SELLER IS")
        self.assertEqual(headings[-1], "13. VERSIONS OF THESE TERMS")
        for node in self.current.root.by_class("legal-section"):
            self.assertTrue(node.attrs.get("id"))

    def test_internal_section_references_resolve(self):
        for text in self.clauses.values():
            for reference in re.findall(r"\b[Ss]ection\s+(\d+(?:\.\d+)?)(?:\([a-z]\))?", text):
                if int(reference.split(".")[0]) > 13:
                    continue  # Statutory tariff references, e.g. Section 232.
                with self.subTest(reference=reference):
                    if "." in reference:
                        self.assertIn(reference, self.clauses)
                    else:
                        self.assertTrue(any(n == reference or n.startswith(reference + ".") for n in self.clauses))
        self.assertIn("Section 10.3 applies to both.", self.clauses["5.15"])
        self.assertIn("10.3 and 12 survive", self.clauses["12.4"])
        self.assertIn("Section 5.14(b) survives without limitation.", self.clauses["12.4"])
        for key, letters in [("5.14", "abc"), ("5.15", "abcde")]:
            self.assertEqual(re.findall(r"\(([a-z])\) [A-Z]", self.clauses[key]), list(letters))

    def test_current_and_permanent_bodies_are_identical(self):
        current = (ROOT / "terms/index.html").read_text(encoding="utf-8")
        permanent = (ROOT / "terms/v1-1/index.html").read_text(encoding="utf-8")
        self.assertEqual(current[current.index("<body>"):], permanent[permanent.index("<body>"):])
        self.assertEqual(self.clauses, self.permanent.clauses())

    def test_visible_identity_version_dates_and_history(self):
        for document in [self.current, self.permanent]:
            nodes = list(document.root.walk())
            header = next(node for node in nodes if node.tag == "h1")
            self.assertEqual(normalize(header.text()), APPROVED["header"])
            self.assertEqual(normalize(document.root.by_class("lead")[0].text()), APPROVED["lead"])
            self.assertEqual(normalize(document.root.by_class("legal-contact")[0].text()), APPROVED["footer"])
            self.assertEqual(normalize(document.root.by_class("version-rule")[0].text()), APPROVED["version_rule"])
            self.assertIn("Version 1.1, effective September 30, 2026.", normalize(document.root.by_class("legal-sub")[0].text()))
            self.assertEqual(normalize(document.root.by_class("legal-footer-line")[0].text()), "Terms and Conditions of Sale - Effective September 30, 2026 - Version 1.1")
            self.assertNotIn("[EFFECTIVE DATE]", document.root.text())
            self.assertIn("Product scope clarified", document.clauses()["13.4"])
            self.assertIn("(1.6).", document.clauses()["13.4"])

    def test_version_metadata_and_frozen_stylesheet(self):
        for document, url, published in [
            (self.current, "https://levybrands.com/terms", "2026-08-25"),
            (self.permanent, "https://levybrands.com/terms/v1-1", "2026-09-30"),
        ]:
            nodes = list(document.root.walk())
            data = json.loads(next(node.text() for node in nodes if node.tag == "script" and node.attrs.get("type") == "application/ld+json"))
            self.assertEqual(data["url"], url)
            self.assertEqual(data["datePublished"], published)
            self.assertEqual(data["dateModified"], APPROVED["effective_date"])
            self.assertEqual(data["headline"], APPROVED["header"])
            self.assertEqual(next(node.attrs["href"] for node in nodes if node.tag == "link" and node.attrs.get("rel") == "canonical"), url)
            self.assertEqual(next(node.attrs["href"] for node in nodes if node.tag == "link" and node.attrs.get("rel") == "stylesheet"), "/terms/v1-1/terms.css")
        for css in [ROOT / "terms/v1-1/terms.css", ROOT / "terms/v1-1/public/dist/css/fonts.css"]:
            for reference in re.findall(r"url\([\"']?([^\)\"']+)[\"']?\)", css.read_text(encoding="utf-8")):
                url = urljoin("https://levybrands.com/" + css.relative_to(ROOT).as_posix(), reference)
                path = urlparse(url).path
                self.assertTrue(path.startswith("/terms/v1-1/"), path)
                self.assertTrue((ROOT / path.lstrip("/")).is_file(), path)

    def test_archive_checksums_and_version_1_0_remains_unchanged(self):
        for version in ["v1-0", "v1-1"]:
            directory = ROOT / "terms" / version
            manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], version[1:].replace("-", "."))
            for record in manifest["files"] + [manifest["pdf"]]:
                with self.subTest(version=version, file=record["path"]):
                    content = (directory / record["path"]).read_bytes()
                    self.assertEqual(len(content), record["bytes"])
                    self.assertEqual(sha256(content).hexdigest(), record["sha256"])
            self.assertTrue((directory / manifest["pdf"]["path"]).read_bytes().startswith(b"%PDF-"))
        original = ROOT / "terms/v1-0/source/terms/index.html"
        self.assertEqual(sha256(original.read_bytes()).hexdigest(), "b0afa9f60d6b6f94fa2624e0d3ae6ce9a3e7270a5d90d728128e08224f25e1cf")
        original_manifest = json.loads((ROOT / "terms/v1-0/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(original_manifest["pdf"]["sha256"], "2dcce48783b76dba767196dcb8a214e09dfe583111b1ebe386d2c3ae744ee283")
        self.assertEqual((ROOT / "terms/terms.css").read_bytes(), (ROOT / "terms/v1-0/source/terms/terms.css").read_bytes())
        self.assertEqual(read_document("terms/v1/index.html").clauses(), self.old_clauses)

    @unittest.skipUnless(shutil.which("pdftotext"), "Optional pdftotext utility is not installed")
    def test_pdf_contains_every_published_clause(self):
        directory = ROOT / "terms/v1-1"
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        text = subprocess.check_output([
            "pdftotext", "-enc", "UTF-8", str(directory / manifest["pdf"]["path"]), "-",
        ]).decode("utf-8")
        text = re.sub(r"^levybrands\.com/terms/v1-1.*Page \d+ of \d+\s*$", "", text, flags=re.MULTILINE)
        # PDF extraction can join line-end hyphens or insert soft hyphens.
        pdf_normalize = lambda value: re.sub(r"[\s\u00ad-]+", "", value)
        pdf_text = pdf_normalize(text)
        for number, wording in self.clauses.items():
            with self.subTest(number=number):
                self.assertIn(pdf_normalize(wording), pdf_text)
        self.assertIn("Version 1.1, effective September 30, 2026.", text)
        self.assertIn("Product scope clarified", text)

    def test_terms_links_have_local_targets(self):
        for document in [self.current, self.permanent]:
            for node in document.root.walk():
                if node.tag == "a" and node.attrs.get("href", "").startswith("/terms"):
                    target = ROOT / node.attrs["href"].lstrip("/")
                    self.assertTrue(target.is_file() or (target / "index.html").is_file(), str(target))


if __name__ == "__main__":
    unittest.main()
