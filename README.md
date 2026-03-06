# Iroko Historical Society — Static Site

Static site for irokosociety.org, deploying to GitHub Pages.

## File Structure

```
ihs-site/
├── index.html          # Homepage
├── about.html          # About the Society / Founder
├── collections.html    # Collections overview
├── access-policy.html  # Six-tier access framework
├── mission.html        # Mission & Stewardship
├── contact.html        # Contact page
├── style.css           # Shared stylesheet (brand colors, typography)
├── CNAME               # Custom domain (irokosociety.org)
└── assets/
    └── IHS-Logo.jpg    # Logo — download from Squarespace media library
```

## Setup

### 1. Copy your logo

Download `Square Logo-TM.png` or the JPG version from your Squarespace Media Library.
Save it as `assets/IHS-Logo.jpg` in this folder.

### 2. Push to GitHub

```bash
git init
git add .
git commit -m "Initial site"
git remote add origin git@github.com:iroko-framework/ihs-website.git
git push -u origin main
```

### 3. Enable GitHub Pages

GitHub repo > Settings > Pages > Source: main branch, / (root) > Save

### 4. DNS Cutover (in Squarespace DNS settings)

Replace existing A records with GitHub Pages IPs:

```
Type  Host  Value
A     @     185.199.108.153
A     @     185.199.109.153
A     @     185.199.110.153
A     @     185.199.111.153
CNAME www   iroko-framework.github.io
```

Remove the Squarespace-generated A records and CNAME first.
GitHub Pages will auto-provision HTTPS once DNS propagates (24-48 hours).

## Brand Colors

| Token         | Hex       | Use                        |
|---------------|-----------|----------------------------|
| --cream       | #EDEAD0   | Page background            |
| --green-deep  | #1E4A27   | Nav, hero, headings        |
| --green-mid   | #2D6035   | Hover states, links        |
| --green-light | #3A7A44   | Accents, card borders      |
| --text-muted  | #4A6350   | Body text, labels          |
