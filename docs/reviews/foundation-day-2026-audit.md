# Foundation Day 2026 / State of the Society — Audit Memo

Internal repository document. Not for publication. Prepared in advance of editing `foundation-day/2026.html` to add the State of the Society, 2025–2026, per the Foundation Day 2026 Review and State of the Society Integration Plan.

Date of review: July 2026 (Year Two, prior to close).
Reviewer: Claude, Cowork session, working from the live repo clones (`IHS-Website`, `iroko-framework`, `Per-Medjat`, `medjat-tools`) and the IHS-Vault, cross-checked against the live deployed sites where noted.

---

## 1. Current Page Architecture

`foundation-day/2026.html` currently contains, in order: top bar, primary nav (identical structure across all inner pages, dropdown-based), hero (`fd-hero`, eyebrow "Annual Observance · Year Two"), observance block (date-pair, private-observance note, mini-conference deferral note), "Find Your Tree" pilgrimage block, "What the Society Built" lead paragraph, "IHS Infrastructure" bulleted block, "Founder's Contributions to the IHS Research Program" bulleted block, community photography call, sidebar archive (2026 current entry, 2025 entry with links), footer.

There is no existing "State of the Society" address block on this page. The only page with the address pattern built out is `foundation-day/2025.html`.

## 2. Style Dependencies

Shared: `style.css` (site-wide, brand tokens: `--cream`, `--green-deep`, `--green-mid`, `--green-light`, `--text-muted`), `assets/nav.js` (mobile nav toggle and dropdown behavior only; no other functions defined in this file).

Page-local `<style>` blocks duplicate nav/top-bar CSS on every page (this is the site's existing convention, not something introduced by this task). `2026.html`'s local style block does **not** contain `.address-paper-wrap`, `.address-share`, `.address-full`, `.address-date`, or `.address-signature`. These exist only in `2025.html`'s local style block. Porting the minimum required declarations into `2026.html` is necessary, not optional.

## 3. Existing Foundation Day Conventions

- Hero pattern: eyebrow line, `<h1>Foundation Day</h1>`, year line, rule, italic lead paragraph. Large translucent roman numeral watermark in the hero background (`I` for 2025, `II` for 2026).
- Observance block: single `date-block` with label/date/note, note text reading "Private observance. Sacred date. Not a public event."
- Sidebar: `archive-entry` per year, most recent marked `archive-current-badge`, each with `archive-theme` and `archive-meta`, optional `archive-links`.
- 2025's address block precedent: `.address-paper-wrap` wraps a placeholder summary (`.address-placeholder`), a share button (`.address-share` / `onclick="shareAddress()"`), and the full address (`.address-full`, with `.address-date` and `.address-signature`). The `id="state-of-the-society"` anchor sits on the outer wrap, not on the `<h2>`.
- 2025's sidebar already links to `2025.html#state-of-the-society`, and 2026's sidebar already links to that same anchor from the "This Page" entry's counterpart. Both directions of the archive link already exist and resolve correctly.

## 4. Verified Year Two Accomplishments

Confirmed independently, not merely asserted by site copy:

- **Ewé Sacred Plant Database**: 50 records built and viewable. Verified directly by counting built output files in `Per-Medjat/ewe/output/plant/` (Plant0001.html through Plant0050.html, exactly fifty). Founder clarification, important and not otherwise knowable from the repo alone: this fifty-record set is test material, not operational or actionable research data. Its function was to prove the Iroko Framework's field-level access control and the public interface actually work, not to publish a usable research resource. The live site's "Live" badge on this feature (`collections.html`, `index.html`) does not currently make that distinction and reads as though the fifty records are a finished, citable dataset. That overstatement is out of scope for this task (only `foundation-day/2026.html` is authorized for edits) but is flagged here since it affects more than one page. The Foundation Day address itself has been written to describe this accurately as a pilot proving the mechanism, not a research resource. Collections.html separately and correctly states a 750+ record full corpus, built on operational data, is "in development."
- **Medjat Library**: grew from a previously stated 69+ items to approximately 600+ records this year. `Per-Medjat/library/data/library.index.json` contains 618 entries; `library/data/library.facets.json` (a separately generated build artifact per its own README) totals 613. The five-record gap is most likely a facets-rebuild lag, not a data error, per founder confirmation that an autorun keeps these in sync but the exact sync direction wasn't certain at review time. Breakdown: 280 theses/dissertations, 213 journal articles, ~77–82 books, 40 book chapters. Access: overwhelmingly Public tier (607–612 of the total), 6 at Community tier, none yet populated at higher tiers. Tradition/theme tagging coverage is still early (only ~35–37 of ~618 records carry tradition tags), which is a function of the Medjat Steward human-review workflow, not neglect. Founder direction: state this as "600+" rather than pinning 613 vs. 618.
- **Iroko Framework**: sixteen modules confirmed live, structured as one Foundation module (Core) plus five Governance modules (Agency, Authority, Epistemic, Narrative, Manifestation) plus ten Domain modules (Ewé, Nkisi, Travay, Ilé, Marca, Ékpè, Vèvè, Ngoma, Sankofa, Qal). A separate file, `iroko-align-prov.ttl` (PROV-O alignment), exists as a reference-only interoperability file and is explicitly not counted among the sixteen module cards on the live framework site. The live deployed framework site (`ontology.irokosociety.org`) is labeled v1.3.0 and matches the Zenodo deposit, founder-confirmed. Git-level check (`git log`, `git diff -w`, `git branch -a` in the local `iroko-framework` clone) confirms: `main` is already committed and pushed to `origin/main` with a "Version v1.4.0" commit and a later v1.4.1-tagged module commit, well ahead of what's live. This is not an uncommitted-work problem; it is a promotion/deploy-branch problem. The repo also carries separate `v1.3.0` and `dev/v1.1.0` branches, and `scripts/deploy.sh` deploys by pushing to `main` and asserts the live site tracks `main` directly. Since `main` already has v1.4.0/1.4.1 pushed but the live site still shows v1.3.0, the most likely cause is that the GitHub Pages source branch for this repo is still pointed at `v1.3.0` rather than `main`. Founder should check Settings → Pages → Source on `github.com/iroko-framework/iroko-framework` before assuming a rebuild alone will fix it. Founder confirmed a new Zenodo version deposit for v1.4.0 will be completed before July 13.
- **TAA submission**: "Havana to the Sabine" was submitted to *The American Archivist* for peer review on June 1, 2026. This directly supersedes the "active revision" / "Forthcoming Submission" language still live on both `foundation-day/2026.html` and `research.html`.
- **ASA presentation**: "Sealed from the Inside" is accepted for presentation at the African Studies Association's 69th Annual Meeting, New Orleans, December 2026. This is accepted and scheduled, not yet delivered as of Foundation Day (July 14, 2026, precedes the December meeting). Founder direction: make this explicit in the address rather than leaving it ambiguous.
- **Internal tooling**: five distinct tools were built or substantially used this year to support the public infrastructure: Medjat Acquire (external catalog search and export with provenance), Medjat Steward (Zotero record review, Iroko tag proposals, approval gating, deletion quarantine), Medjat Enrich (retroactive authority URI, abstract, and OpenAlex enrichment), the Featured Work Selector (public catalog feature rotation), and the Iroko Framework Manager (local TTL editor and build tool, explains how the framework went from two documented modules in the framework repo's root README to sixteen deployed modules). Founder direction: name these specifically in the address as evidence of real infrastructure, not just policy language.
- **Mini-conference deferral**: confirmed accurate and current. The live `2026.html` and the live fetched copy both already state the postponement to 2027. The vault's contrary information (a still-scheduled July 18 virtual restricted-access panel) is stale; founder confirmed Foundation Day programming was scaled back after the vault was last updated.

## 5. Projects Still in Development

- Ewé Sacred Plant Database: 750+ record full corpus (50 live now).
- Framework v1.4.0/1.4.1: committed and pushed to `main` on GitHub, not yet promoted to whatever branch the live `ontology.irokosociety.org` deploy actually tracks, and not yet given its own Zenodo version deposit. Founder will complete the new Zenodo deposit before July 13; the GitHub Pages source-branch question (see Section 4) should be checked at the same time so the live site and the new deposit go out together.
- Medjat Library: tagging/enrichment coverage (tradition, theme, domain) across the ~600+ record catalog is still early-stage; volume has scaled ahead of governance metadata.
- 2027 mini-conference / public convening: explicitly deferred, not cancelled.

**Note on the IHS-Website repo specifically**: `git status` initially showed nearly every page as "modified." `git diff -w` (ignoring whitespace/line-endings) returns empty for all of them, confirming this is line-ending normalization noise (Windows/VS Code CRLF vs. the repo's stored line endings), not real content drift. The one real, minor timing gap found: the live fetch of `2026.html` during this review still showed a reference to "the Fulbright application" in the deferral note that the current committed `main` branch does not contain (today's "Minor Update to Foundation Day 2026 page" commit, already pushed). This is almost certainly GitHub Pages/CDN propagation lag following a same-day push, not a structural problem, and should resolve on its own shortly if it hasn't already.

## 6. Claims Requiring Confirmation Before Publication — Resolved This Session

- UA Outstanding Student Paper Award 2026 attribution: `2026.html` and the homepage metrics area both, in different places, risk conflating this with the Verger Ewé Dataset. Three independent sources (`research.html`, `index.html`'s own Fieldwork & Scholarship section, and the vault's `02_PHASE3_TAA.md`) agree the award belongs to "Havana to the Sabine," awarded under an earlier working title. Founder confirmed: Havana to the Sabine. `2026.html`'s current attribution to the Verger Ewé Dataset is incorrect and will be corrected.
- Zenodo version state: v1.3.0 deposited (founder-confirmed), v1.4.0 built locally but undeployed and undeposited. Recommendation in Section 8.

## 7. Cross-Site Inconsistencies

These are presented as findings, not resolved by guessing, per the brief's own instruction.

- **Framework quantitative counts, four disagreeing sets found on four different pages**: `index.html` homepage metrics states 650 concepts (no class/property figures given). `founder.html` states "94 classes, 389 properties, and 589 concepts." `research.html`'s Zenodo abstract states "ninety-one classes, three hundred seventy-nine properties, sixty-nine concept schemes, and six hundred two concepts." The live `ontology.irokosociety.org` site, fetched directly during this review, currently shows 95 classes, 393 properties, 70 schemes, 593 concepts. None of these four match. This means the live framework site has itself drifted from its own Zenodo deposit's stated snapshot without a version bump, on top of the separate, larger drift represented by the undeployed local v1.4.0. **Recommendation carried into the draft: do not state any specific class/property/concept count on the Foundation Day page.** "Sixteen modules" is the one figure confirmed stable everywhere (repo, live site, Zenodo description, homepage) and is safe to use.
- **Initiatory tenure**: `about.html` states "Over 20 years of fully initiated practice." `founder.html` states "over 30 years." These do not agree. Not corrected here; flagged for the founder's own site maintenance, unrelated to Foundation Day.
- **Framework credential list**: `about.html` omits the BS in Psychology (Tennessee State) that `founder.html` includes, and phrases the JD without the "International Law" qualifier `founder.html` uses. Likely just differing levels of detail rather than a factual conflict, but noted.
- **Homepage Foundation Day teaser is stale**: `index.html`'s own Foundation Day section still reads "a private observance followed by a public weekend of scholarship, community gathering, and living practice," with no mention of the 2027 deferral, and "In 2026 we enter Year Two" (a framing that was accurate for the July 2025 Foundation Day, not July 2026, since Year Two began in 2025 and closes this July). This will become more visibly wrong once Year Three opens July 14, 2026. Out of scope for this task (only `foundation-day/2026.html` is authorized for edits), flagged for a follow-up pass.
- **Access-tier notation is inconsistent across three layers**: `access-policy.html` uses plain numbered, named tiers (1 Public, 2 Registered Scholar, 3 Community Member, 4 Initiated Practitioner, 5 Elder/Lineage Authority, 6 Sacred/Restricted). `collections.html` and `visual-ethnography.html` use an "L-number" shorthand ("L2–L5," "Tiers 3–6"). The underlying library data schema uses yet another form (`L0-public`, `L1-community`). Founder direction: leave this alone for now.
- **TAA status is stale in two places, not one**: both `foundation-day/2026.html` and `research.html` describe the paper as "in active revision" / "Forthcoming Submission." Founder direction: patch both, `research.html` as a separate, clearly labeled commit outside the primary scope of this task.
- **DOI assignment is internally consistent** across `2026.html`, `research.html`, `collections.html`, `mission.html`, and `founder.html`: 10.5281/zenodo.19157679 is the vocabulary, 10.5281/zenodo.18826673 is the white paper. The only place this pairing is blurred is a course-project README (`Per-Medjat/README.md`, the LS563 Verger Ewé Dataset documentation), which cites 18826673 without the vocabulary/white-paper distinction. Not a live public claim; low priority.

## 8. Recommended Wording for Uncertain Items

- Framework vocabulary: *"The Iroko Framework continued to develop as a published, versioned semantic vocabulary, deposited to Zenodo under a persistent DOI and structured across sixteen modules spanning foundation, governance, and domain layers."* No class/property/concept counts.
- Framework version: describe the deposited state (v1.3.0) as the citable record; note continued development without claiming a v1.4.0 deposit that does not yet exist. Recommend the founder complete a proper Zenodo **new version** deposit (under the existing concept DOI, which Zenodo's versioning system is built for) once v1.4.0 is finalized and pushed live, rather than editing the existing v1.3.0 record's metadata text. Editing an archived deposit's description to describe different content breaks the citation record Zenodo exists to preserve; a new version deposit preserves the citation lineage from 1.3.0 forward. If this is completed before July 14, the address can cite v1.4.0 directly; if not, the address should describe the current, honest split (deposited at 1.3.0, continuing to develop toward the next release).
- Medjat Library: *"more than 600 cataloged records"* per founder direction, not a pinned figure, until `library.index.json` and `library.facets.json` are reconciled.
- ASA presentation: state explicitly as accepted and scheduled for December 2026, not yet delivered as of Foundation Day, per founder direction.
- TAA: *"submitted to The American Archivist (vol. 90.1) for peer review, June 2026."*
- UA Outstanding Student Paper Award: attribute to "Havana to the Sabine," per founder confirmation and three-source agreement.

## 9. Broken Links, Missing Scripts, or Accessibility Issues

- `shareAddress()` is called via `onclick` on `foundation-day/2025.html` and does not exist anywhere in `assets/nav.js` or elsewhere in that page. Confirmed broken since the page's original publication. Founder direction: fix, as an isolated, low-risk, separately labeled commit.
- No canonical tags exist on any page reviewed (`2025.html`, `2026.html`, or the inner pages). No canonical tag will be introduced on `2026.html`, consistent with the site's existing pattern.
- No other broken internal links, empty anchors, or missing alt text found on the pages reviewed (`2025.html`, `2026.html`, `about.html`, `mission.html`, `access-policy.html`, `collections.html`, `research.html`, `founder.html`, `visual-ethnography.html`, `iroko-commentaries.html`, `contact.html`, `our-stance.html`, `index.html`). All external links carry `target="_blank"`; most but not all also carry `rel="noopener noreferrer"` (some external links on `2026.html` and elsewhere use `target="_blank"` without a `rel` attribute, e.g. the Zenodo DOI links). Recommend adding `rel="noopener noreferrer"` to any new external links introduced in this task and to existing ones directly touched.

## 10. Files Changed or Proposed for Change

**In scope for this task:**
- `foundation-day/2026.html` — primary edit: hero framing, deferral note tense, State of the Society section insertion, content reorder, Year Three Outlook, sidebar update, metadata update.
- `foundation-day/2025.html` — isolated fix: define and wire `shareAddress()`.
- `research.html` — isolated fix: update the "Havana to the Sabine" entry from "Forthcoming Submission" / active-revision framing to submitted-for-peer-review, per founder direction.
- `docs/reviews/foundation-day-2026-audit.md` — this document.
- `docs/drafts/state-of-society-2025-2026.md` — draft address text, to follow.

**Out of scope, flagged only:**
- `index.html` homepage metrics banner and Foundation Day teaser section (stale figures and stale framing).
- `founder.html` and `about.html` (initiatory-tenure and credential-detail mismatches).
- `iroko-framework` root `README.md` (still describes only two modules).
- Access-tier notation inconsistency across `collections.html`, `visual-ethnography.html`, and the library data schema.
