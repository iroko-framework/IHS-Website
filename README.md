# Iroko Historical Society - Static Website

Static HTML site for [irokosociety.org](https://www.irokosociety.org), hosted on GitHub Pages.

## Deployment

1. Create a new GitHub repository (e.g., `iroko-framework/irokosociety.org` or `iroko-framework/ihs-website`)
2. Push all files in this directory to the `main` branch
3. In repository Settings > Pages, set Source to "Deploy from a branch" and select `main` / `/ (root)`
4. The `CNAME` file will configure the custom domain automatically

### DNS Configuration (Squarespace to GitHub Pages)

In your domain registrar (or Squarespace Domains if that's where the domain is registered):

1. Remove any existing A records or CNAME records pointing to Squarespace
2. Add these A records pointing to GitHub Pages:
   - `185.199.108.153`
   - `185.199.109.153`
   - `185.199.110.153`
   - `185.199.111.153`
3. Add a CNAME record: `www` -> `iroko-framework.github.io`
4. In GitHub repo Settings > Pages, enter `www.irokosociety.org` as the custom domain
5. Check "Enforce HTTPS" once DNS propagates (may take up to 24 hours)

### Before You Go Live

- [ ] Replace `assets/IHS-Logo.svg` with your actual logo (download from your current Squarespace site's media library, save as `assets/IHS-Logo.svg` or update the filename references in all HTML files)
- [ ] Migrate content for placeholder pages: `iroko-spirituality.html`, `capturing-iroko.html`, `foundation-day-2025.html`
- [ ] Add any gallery images to an `assets/gallery/` directory
- [ ] Review and adjust the `CNAME` file if using a different domain configuration
- [ ] Cancel your Squarespace subscription once the GitHub Pages site is confirmed working

## Structure

```
index.html              Homepage
about.html              Our Vision
founder.html            The Founder (bio)
collections.html        Collections Overview
access-policy.html      Access & Use Policy
mission.html            Mission & Stewardship
contact.html            Contact
iroko-spirituality.html Iroko Spirituality (placeholder)
capturing-iroko.html    Visual Ethnography (placeholder)
foundation-day-2025.html Foundation Day 2025 (placeholder)
assets/
  style.css             Main stylesheet
  nav.js                Mobile navigation
  IHS-Logo.svg          Logo (placeholder, replace with actual)
CNAME                   GitHub Pages custom domain
.nojekyll               Tells GitHub Pages to skip Jekyll processing
```

## Design

The site matches the design language of [ontology.irokosociety.org](https://ontology.irokosociety.org/): dark background, Source Sans 3 / Source Serif 4 typography, card-based layouts, and metric strips. All CSS is in a single file with custom properties for easy theme adjustment.

## Adding a Contact Form

The current contact page lists the email address directly. If you want a working form without a backend, consider:

- [Formspree](https://formspree.io/) (free tier: 50 submissions/month)
- [Netlify Forms](https://www.netlify.com/products/forms/) (if you switch hosting)
- [Google Forms](https://forms.google.com/) embedded via iframe
