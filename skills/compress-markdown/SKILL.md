---
name: compress-markdown
model: sonnet
description: >
  Compress markdown files into concise prose to save input tokens. Default mode reduces
  verbosity without losing information. With --deep, verifies each section against the
  codebase first, removing stale or incorrect content before compressing.
  Trigger: /compress-markdown <filepath> [--deep]
---

# Compress Markdown

## Trigger

`/compress-markdown <filepath>` — reduce verbosity, preserve all content.

`/compress-markdown <filepath> --deep` — verify against codebase first, then compress.

## Modes

**Default (lossless):** Reduce verbosity of prose without consulting the codebase. Every distinct idea survives, just stated more concisely. Safe for any markdown file.

**Deep (lossy):** Read the file section by section and verify each claim against the actual codebase. Remove content that is demonstrably stale or incorrect. Flag ambiguous cases to the user. Then apply the same verbosity reduction as default mode. Only meaningful for files that reference a codebase (CLAUDE.md, architecture docs, onboarding guides).

## Process

### Default mode

1. **Guard.** Check the file extension. Only compress `.md`, `.txt`, `.markdown`, `.rst`, or extensionless files. Refuse anything else. Skip files ending in `.original.md`.
2. **Backup.** If `<stem>.original.md` already exists, stop and tell the user (prevents overwriting a previous backup). Otherwise copy the original file to `<stem>.original.md`.
3. **Compress.** Read the file and rewrite it following the Compression Rules below. Write the compressed content back to the original path.
4. **Validate.** Run `python3 validate.py <backup_path> <compressed_path>` using the `validate.py` in the same directory as this SKILL.md. Read the output.
5. **Fix if needed.** If validation reports errors, read the backup to see what was lost, then fix only the specific issues in the compressed file (do not recompress from scratch). Re-run validation. After 2 failed fix attempts, restore the backup to the original path, remove the backup file, and report the failure.
6. **Report.** Tell the user what was compressed and where the backup lives.

### Deep mode

1. **Guard and Backup.** Same as default mode.
2. **Audit.** Read the file and split it by top-level headings into sections. For each section:
   - Extract file paths, function/class names, command examples, and architectural claims.
   - Verify each reference against the codebase:
     - **File paths:** Do they exist? Use glob/find to check.
     - **Symbols in inline code:** Grep for function names, class names, variable names. Are they still defined?
     - **Commands:** Are the referenced tools/scripts still present?
     - **Conventions/patterns described:** Spot-check a few files to see if the described pattern holds.
   - Classify each finding:
     - **Auto-remove:** The referenced thing no longer exists at all (deleted file, removed function). Remove the content silently.
     - **Flag to user:** The reference is ambiguous (renamed, moved, partially changed). Present the finding and ask whether to keep, update, or remove.
     - **Keep:** The reference checks out. Leave it for compression.
3. **Apply removals.** Delete auto-remove content. Wait for user decisions on flagged items. Write the audited file.
4. **Compress.** Apply the same verbosity reduction as default mode to the surviving content.
5. **Validate, Fix, Report.** Same as default mode.

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
- Directive keywords: NEVER, MUST, ALWAYS, CRITICAL, DO NOT, REQUIRED, IMPORTANT, FORBIDDEN, MANDATORY. These carry imperative force that must survive compression. The validator checks for their presence.

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
> Run tests before push to main. Important: catch bugs early, prevent broken prod deploys.

Before:
> The application uses a microservices architecture with the following components. The API gateway handles all incoming requests and routes them to the appropriate service. The authentication service is responsible for managing user sessions and JWT tokens.

After:
> Microservices architecture. API gateway route all requests to services. Auth service manage user sessions + JWT tokens.
