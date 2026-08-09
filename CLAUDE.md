# CLAUDE.md: IHS-Website

Public site for the Iroko Historical Society. Static HTML on GitHub Pages, served at **irokosociety.org** (CNAME in repo root). No build step, no framework, no package manager. What is committed is what is served.

---

## Layout

Every page is a hand-written HTML file in the repo root. There is no template engine, so shared chrome (nav, footer, meta tags) is duplicated across files. **A change to navigation or footer has to be applied to every page.** Check the full list before declaring a nav change done.

| Group | Pages |
|---|---|
| Core | `index.html`, `about.html`, `mission.html`, `founder.html`, `contact.html`, `cv.html` |
| Position and policy | `our-stance.html`, `access-policy.html`, `contributor-guidelines.html` |
| Research and collections | `research.html`, `collections.html`, `visual-ethnography.html`, `capturing-iroko.html` |
| Commentary program | `iroko-commentaries.html`, `propose-commentary.html`, `contribute-commentary.html`, `guest-commentary-template.html`, `contact-form.html` |
| Essays | `the-scholar-is-not-the-custodian.html`, `the-bones-fall-prophecy-or-verdict.html`, `wont-they-do-it.html`, `iroko-spirituality.html`, `bread-before-the-end.html` |

Other directories: `assets/` (38 files: styles, fonts, images, Open Graph cards), `foundation-day/` (13 files), `docs/`, `archive/`.

`generate-og.py` builds Open Graph cards. `generate-og okd.py` is a variant copy; confirm which is current before running either.

---

## Before committing

- **`__pycache__` is currently tracked in this repo.** It should not be. Add it to `.gitignore` and `git rm -r --cached` it.
- `_bash_write_test.txt` and similar scratch artifacts have appeared in the working tree. Do not commit them.
- New pages need: the shared nav and footer, a matching Open Graph card in `assets/`, correct canonical URL, and an entry anywhere the page should be linked from. Nothing does this automatically.

---

## Foundation Day

`foundation-day/` here holds 13 tracked files. There is also a **separate, untracked `foundation-day` folder** sitting beside the repos in `github active/`, containing `2025.html`, `2026.html`, `2027.html`, `find-your-tree.html`, and several patch zips. Those two are not synchronized and one of them is stale.

Determine which is authoritative before editing Foundation Day content. Do not assume this repo's copy is current.

---

## Working conventions

- Never use em dashes in any prose on this site.
- Do not use "diaspora" or "diasporic" in any copy. Use Afro-Atlantic, Atlantic world, Atlantic crossing, or the specific geographic framing. This is a principled terminological position, not a style preference.
- Iroko terminology is exact: postcustodial, Iroko module, access tier, RefusalEvent, StewardshipMandate. Do not substitute generalist synonyms.
- `access-policy.html` and `our-stance.html` state the institutional position that restricted access is the correct default for sacred Afro-Atlantic material. Any new page touching collections or access has to be consistent with them. Read them first.
- Register is scholarly but readable, with a voice. Not corporate, not stiff.
- Author name on this site is Délé Fágbèmí Ọ̀. The finance alias Ayodele Odiduro does not appear here.

---

## Related

- **IAO-Website** (ileanaolofi.org) is the parent 501(c)(3). IHS is its program, not a peer organization. Keep the relationship accurate in any copy that names both.
- **Per-Medjat** (medjat.irokosociety.org) is the digital archive.
- **iroko-framework** (ontology.irokosociety.org) is the ontology.

Cross-site links are hand-maintained. There is no link checker in this repo.
