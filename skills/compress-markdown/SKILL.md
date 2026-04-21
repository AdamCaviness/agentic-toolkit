---
name: compress-markdown
model: sonnet
description: >
  Compress markdown files (CLAUDE.md, docs, specs) into concise prose to save input tokens.
  Preserves all technical substance, code, URLs, and structure.
  Trigger: /compress-markdown <filepath>
---

# Compress Markdown

## Trigger

`/compress-markdown <filepath>` or when user asks to compress a markdown file.

## Process

1. **Guard.** Check the file extension. Only compress `.md`, `.txt`, `.markdown`, `.rst`, or extensionless files. Refuse anything else. Skip files ending in `.original.md`.
2. **Backup.** If `<stem>.original.md` already exists, stop and tell the user (prevents overwriting a previous backup). Otherwise copy the original file to `<stem>.original.md`.
3. **Compress.** Read the file and rewrite it following the Compression Rules below. Write the compressed content back to the original path.
4. **Validate.** Run `python3 validate.py <backup_path> <compressed_path>` using the `validate.py` in the same directory as this SKILL.md. Read the output.
5. **Fix if needed.** If validation reports errors, read the backup to see what was lost, then fix only the specific issues in the compressed file (do not recompress from scratch). Re-run validation. After 2 failed fix attempts, restore the backup to the original path, remove the backup file, and report the failure.
6. **Report.** Tell the user what was compressed and where the backup lives.

## Compression Rules

### Remove
- Articles: a, an, the
- Filler: just, really, basically, actually, simply, essentially, generally
- Pleasantries: "sure", "certainly", "of course", "happy to", "I'd recommend"
- Hedging: "it might be worth", "you could consider", "it would be good to"
- Redundant phrasing: "in order to" → "to", "make sure to" → "ensure", "the reason is because" → "because"
- Connective fluff: "however", "furthermore", "additionally", "in addition"

### Preserve EXACTLY (never modify)
- Code blocks (fenced ``` and indented)
- Inline code (`backtick content`)
- URLs and links (full URLs, markdown links)
- File paths (`/src/components/...`, `./config.yaml`)
- Commands (`npm install`, `git commit`, `docker build`)
- Technical terms (library names, API names, protocols, algorithms)
- Proper nouns (project names, people, companies)
- Dates, version numbers, numeric values
- Environment variables (`$HOME`, `NODE_ENV`)
- Frontmatter/YAML headers

### Preserve Structure
- All markdown headings (keep exact heading text, compress body below)
- Bullet point hierarchy (keep nesting level)
- Numbered lists (keep numbering)
- Tables (compress cell text, keep structure)

### Compress
- Use short synonyms: "big" not "extensive", "fix" not "implement a solution for", "use" not "utilize"
- Fragments OK: "Run tests before commit" not "You should always run tests before committing"
- Drop "you should", "make sure to", "remember to", just state the action
- Merge redundant bullets that say the same thing differently
- Keep one example where multiple examples show the same pattern

### Code blocks are read-only
Anything inside ``` ... ``` or inline backticks must be copied character-for-character. Do not remove comments, spacing, or reorder lines inside code. If a file mixes prose and code, only compress the prose around the code blocks. Do not merge sections across code block boundaries.

## Examples

Before:
> You should always make sure to run the test suite before pushing any changes to the main branch. This is important because it helps catch bugs early and prevents broken builds from being deployed to production.

After:
> Run tests before push to main. Catch bugs early, prevent broken prod deploys.

Before:
> The application uses a microservices architecture with the following components. The API gateway handles all incoming requests and routes them to the appropriate service. The authentication service is responsible for managing user sessions and JWT tokens.

After:
> Microservices architecture. API gateway route all requests to services. Auth service manage user sessions + JWT tokens.
