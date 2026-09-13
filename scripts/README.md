# AIModelCalc — pricing build system

All model pricing lives in **one file**: [`models.json`](../models.json).
To change prices or models, edit that file, then run the generator. You never
hand-edit prices in the HTML pages again.

## How to update pricing (the whole routine)

1. Open `models.json` in the repo root.
2. Change the numbers (`input` / `output`), add or remove models, or flip a
   model to `"legacy": true`. Also bump `site.last_checked` (and `next_check`).
3. From the repo root, run:

   ```
   python3 scripts/generate.py
   ```

4. Commit and push. If the site is behind Cloudflare, purge the cache
   (Cloudflare dashboard → Caching → Purge Everything) so the new pages serve.

That's it. No frameworks, no installs — just Python 3 (already on macOS).

## What the generator writes (and what it doesn't)

`generate.py` only rewrites the regions marked with `GEN:` comment markers.
Everything else on every page — the prose, worked examples, headings — is left
exactly as written. The auto-generated regions are:

| File | Region |
|------|--------|
| `index.html` | calculator `MODELS` data, the model dropdown, the "models tracked / providers" counts |
| `guides/ai-api-pricing-2026.html` | the full comparison table |
| `guides/openai-api-pricing.html` | the OpenAI lineup table |
| `guides/claude-api-pricing.html` | the Anthropic lineup table |
| `guides/cheapest-ai-api.html` | the ranked "cheapest" table |

**Do not hand-edit anything between `<!--GEN:...-->` / `<!--/GEN:...-->`
(or `/*GEN:...*/`) markers** — the next generate run will overwrite it. Change
`models.json` instead.

### Still hand-written (update these yourself when a flagship changes)

The generator handles all the pricing **tables and the calculator**. A few
places use prices inside sentences / worked examples and stay manual:

- Homepage editorial paragraphs and info cards (`index.html`)
- Worked-dollar examples inside the guides (e.g. the RAG cost example in the
  Claude guide, the savings tables in `cheapest` / `gemini-vs`)
- `about.html` and `faq.html` model lists (short, rarely change)

These don't change on a routine price tweak — only when a headline model is
added/renamed. When that happens, search the repo for the old model name.

## Fields in models.json

Each model: `id`, `name`, `provider` (`openai`/`anthropic`/`google`),
`input`, `output` (USD per 1M tokens), `context`, `speed` (1–5), `best`
(short label), `tier`, `legacy` (bool), `in_calculator` (bool),
`in_cheapest` (bool), and for the cheapest table `cheapest_badge` /
`cheapest_color` (`green` or `amber`).

`site.default_calc_model` = the model pre-selected in the calculator dropdown.

## Safety notes

- The generator is **idempotent** — running it twice in a row changes nothing.
- On first run it auto-installs the `GEN:` markers around the current regions,
  then fills them; later runs just refill.
- It uses only the Python standard library and works offline.
