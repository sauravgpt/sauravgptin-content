# sauravgpt-content

Headless content repository for the sauravgpt.in platform. It holds the Markdown,
media, and manifests that power:

- **Learn** — [learn.sauravgpt.in](https://learn.sauravgpt.in)
- **Blog** — [blog.sauravgpt.in](https://blog.sauravgpt.in)

The Next.js apps live in a separate repo and fetch this content at runtime over the
jsDelivr CDN. Pushing to `main` is enough to publish — no app rebuild or redeploy.

## Repository layout

```
/
├── course-manifest.json     # Learn: source of truth for tracks → modules → lessons
├── blog-manifest.json       # Blog: source of truth for posts
├── learn/                   # Learn Markdown, grouped by track
│   └── <track>/<module>/<lesson>.md
├── blogs/                   # Blog post Markdown
└── assets/                  # Media, referenced by absolute https CDN URLs
```

Content is served via:

```
https://cdn.jsdelivr.net/gh/sauravgpt/sauravgptin-content@main/<path>
```

## Courses (Learn tracks)

| Track | Slug | Modules |
|---|---|---|
| System Design | `system-design` | Foundations, Non-Functional Requirements, Core Building Blocks, Data Layer & Storage |
| Generative Artificial Intelligence | `generative-artificial-intelligence` | Foundations of GenAI, Prompt Engineering, Retrieval-Augmented Generation, Building GenAI Applications |

## How it works

- Navigation and curriculum are built entirely from the manifests. A `.md` file not
  listed in a manifest is invisible in the UI.
- URL slugs map directly to file paths: `/dsa/<module>/<lesson>` fetches
  `learn/dsa/<module>/<lesson>.md`, so folder and file names must match manifest slugs.
- Lessons support GitHub-flavored Markdown plus interactive blocks (`quiz`, `match`,
  `callout`, `mermaid`) authored as fenced code blocks with strict JSON payloads.
- Images and media must use absolute `https://` URLs; relative paths are blocked.

## Publishing workflow

1. Add or edit `.md` files under `learn/` or `blogs/`.
2. Update the matching manifest (`course-manifest.json` / `blog-manifest.json`).
3. Validate the JSON, commit, and push to `main`.
4. Purge the CDN cache to go live immediately:
   ```
   https://purge.jsdelivr.net/gh/sauravgpt/sauravgptin-content@main/course-manifest.json
   https://purge.jsdelivr.net/gh/sauravgpt/sauravgptin-content@main/learn/<track>/<module>/<lesson>.md
   ```

See [AGENTS.md](AGENTS.md) for the full authoring guide, manifest schema, and
validation rules.
