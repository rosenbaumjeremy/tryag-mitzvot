# Daily routine: three new "in depth" (בירור) write-ups

Each day the site gets full write-ups for the **next three mitzvot** that don't have one yet, in Rambam's
order (P1…P248, then N1…N365). A write-up is the bilingual `<div class="dd" data-dd="KEY">` block inside
`<div id="dd" hidden>` in `public/index.html`: the same block the page already shows for P1–P20, N183,
N320, P161, P212 and P215. Pushing to `main` redeploys the site (Cloudflare Workers Builds).

The rule above everything else: **use only sources on Sefaria, link every source you use, and quote only
words that are actually in the linked text.** Don't add opinions, rulings or explanations of your own.
Publish only what `scripts/dd.py check` verified.

## Step 0: once a day
`TZ=Asia/Jerusalem date +%F` gives TODAY. If `git log --oneline -20` already has a commit
`In depth: … (TODAY)`, stop: today's write-ups are done.

## Step 1: which three
`python3 scripts/dd.py due 3` prints the three keys (e.g. `P21 P22 P23`). If it prints FINISHED, stop and
say all 613 are done.

## Step 2: read the model
Read one finished write-up in full before writing, e.g. P20:
`awk '/data-dd="P20"/,/DEEP DIVE: NEGATIVE 320/' public/index.html`. Also skim N183 (a negative
mitzva). Copy the markup exactly: class names, the order of sections, the table columns and the
`nmx` boxes.

## Step 3: gather the sources, one mitzva at a time
1. `python3 scripts/dd.py info KEY`: the heading, the Rambam's text, and every Sefaria link the site
   already has for it (`g`: Torah, Mishneh Torah, Chinuch, SMaG, SMaK, Tur, Gemara, Sefer HaMitzvot
   cross-references, commentaries), plus R' Perla's passages from `perla.json`.
2. Read the texts themselves from Sefaria's API, e.g.
   `curl -s "https://www.sefaria.org/api/v3/texts/Sefer_HaChinukh.95?version=hebrew&return_format=text_only"`.
   At least: Rambam's Sefer HaMitzvot and his Mishneh Torah halacha, Chinuch, SMaG, SMaK, Rasag
   (`Sefer_Hamitzvot_of_Rasag,…`) and R' Perla's commentary on it
   (`Commentary_on_Sefer_Hamitzvot_of_Rasag,…`), Minchat Chinuch on the Chinuch's number
   (`Minchat_Chinukh.N`), the Ramban's Hasagot where he discusses it, and the Gemara/Mishna the
   sources cite. Use the Sefaria search or links API (`/api/related/REF`) to find more.
3. Work out where the counters really disagree: what act is commanded, its object, its scope,
   one mitzva or several, Torah or rabbinic, today or only in Temple times, who is obligated.

## Step 4: write the draft
Write `/tmp/dd/KEY.html` with exactly one block:

```html
<div class="dd" data-dd="KEY">
<div class="en">
  <h3>How each counter phrases the mitzva</h3>
  <p class="lead">…what the disagreement really is…</p>
  <table class="ft">
    <thead><tr><th>Source</th><th>Wording</th><th>What the wording commits him to</th></tr></thead>
    <tbody>
      <tr><td><a href="https://www.sefaria.org/REF">Name</a></td><td lang="he">exact words… exact words</td><td>…</td></tr>
      … (at least 4 rows; Rambam SHM, Mishneh Torah, Chinuch, SMaG, SMaK, Rasag, Behag as R' Perla reports him…)
    </tbody>
  </table>
  <h3>Axes of the disagreement</h3>
  <ul class="axes"><li><b>Axis:</b> …</li> …</ul>
  <h3>R' Yerucham Fishel Perla</h3>
  <p><b>Point.</b> … (<a href="https://www.sefaria.org/Commentary_on_Sefer_Hamitzvot_of_Rasag,…">seg. N</a>) …</p>
  <h3>Minchat Chinuch</h3>
  <p><b>Point.</b> … (<a href="https://www.sefaria.org/Minchat_Chinukh.N.M.K">MC N:M:K</a>)</p>
  <h3>Nafka minas that come from the wording</h3>
  <ol class="nm">
    <li><b>Case</b> One-line answer per view.<div class="nmx"><p>The source: <span lang="he">"exact words"</span> …</p></div></li>
    … (at least 3)
  </ol>
</div>
<div class="he">
  <h3>לשון כל מונה במצוה</h3> … the same content in Hebrew, same order and same rows …
  <h3>צירים למחלוקת</h3> … <h3>הגרי״פ פערלא</h3> … <h3>מנחת חינוך</h3> … <h3>נפקא מינות היוצאות מן הלשון</h3> …
</div>
</div>
```

Rules for the content:
- Every quotation (in `"…"`, `“…”` or `״…״`, and every Hebrew cell in the Wording column) must be words
  copied from a Sefaria text that is **linked in the same paragraph, list item or table row**. Use `…`
  to skip words. Niqqud and spelling differences are fine; changed words are not.
- Only sefaria.org links, with real refs that load.
- If R' Perla's comment on this mitzva isn't on Sefaria (`info` shows `"has": false` or nothing), write
  under his heading one `<p class="empty">` line saying so (see N183). Do the same for the Minchat Chinuch
  if he has nothing on it.
- No views of your own. "The Rambam holds X (link)", never "it seems to me".
- The English is plain, short sentences, like the existing write-ups. The Hebrew is a faithful parallel,
  not a word-for-word translation.

## Step 5: check, then add
`python3 scripts/dd.py check /tmp/dd/KEY.html` for each draft. Fix every ERROR by correcting the quote
against the source, linking the source, or removing the quote. Never edit `scripts/dd.py`. Repeat
until it prints OK. Then add all three at once:
`python3 scripts/dd.py add /tmp/dd/K1.html /tmp/dd/K2.html /tmp/dd/K3.html`
(it checks again and inserts them at the end of `<div id="dd">`). Change nothing else in
`public/index.html`, `mitzvot.json` or `perla.json`.

## Step 6: publish
`git add public/index.html && git commit -m "In depth: K1, K2, K3 (TODAY)"` and
`git -c push.negotiate=true push origin HEAD:main`. If the push is rejected because main moved,
`git pull --rebase origin main` and push again.

## Step 7: the Ask page
The "Ask Claude" page for this site must learn the new write-ups the same day. Follow the scheduled
task's instructions for this step (it updates the tryag Ask page from this repo with append_notes.py).

## Step 8: report
One line: `In depth added: K1 (name), K2 (name), K3 (name). Ask page: updated / nothing new.`
