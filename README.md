# מראה מקומות לתרי״ג מצוות — Sources for the 613 Mitzvot

A single self-contained page (`public/index.html`), deployed as a Cloudflare Worker with static assets (`wrangler.jsonc`). All 613 mitzvot are embedded in it, so you need no server code or build step, and it works even when you open the file straight from your disk.

## Deploying
It is deployed as a Cloudflare Worker (Workers Builds, connected to this repository). Every push to `main` redeploys it. To deploy by hand, run `npx wrangler deploy`.

## Other places to host it

- **Netlify Drop:** go to app.netlify.com/drop and drag this folder onto the page. You get a link right away, and you can connect your own domain later.
- **GitHub Pages:** create a repository, upload `index.html`, then go to Settings → Pages → Deploy from branch `main` / root. The site appears at `https://<username>.github.io/<repository>/`.
- **Cloudflare Pages:** Workers & Pages → Create → Pages → Upload assets → upload this folder.

To use a custom domain (for example tryag.example.org), add it in the host's domain settings and point a CNAME record at the address the host gives you.

## Credits
Texts and links come from Sefaria (sefaria.org). The Hebrew list of mitzvot is from Wikisource (CC-BY-SA). The English list is the translation by Eliyahu Touger (Moznaim), used under CC-BY-NC, so keep the site non-commercial.
