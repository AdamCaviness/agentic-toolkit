---
name: compress-markdown
model: sonnet
description: >
  Compress markdown files into concise prose to save input tokens. Default mode reduces
  verbosity without losing information. With deep, verifies each section against the
  codebase first, removing stale or incorrect content before compressing.
  Trigger: /compress-markdown <filepath> [deep]
---

# Compress Markdown

## Trigger

`/compress-markdown <filepath>`, reduce verbosity, preserve all content.

`/compress-markdown <filepath> deep`, verify against codebase first, then compress.

## Modes

**Default (lossless):** Reduce verbosity of prose without consulting the codebase. Every distinct idea survives, just stated more concisely. Safe for any markdown file.

**Deep (lossy):** Read the file section by section and verify each claim against the actual codebase. Remove content that is stale or incorrect. Update content that is partially right. Then apply the same verbosity reduction as default mode. Only meaningful for files that reference a codebase (CLAUDE.md, architecture docs, onboarding guides).

## Process

### Default mode

1. **Guard.** Check the file extension. Only compress `.md`, `.txt`, `.markdown`, `.rst`, or extensionless files. Refuse anything else. Skip files ending in `.original.md`.
2. **Backup.** If `<stem>.original.md` already exists, stop and tell the user (prevents overwriting a previous backup). Otherwise copy the original file to `<stem>.original.md`.
3. **Compress.** Read the file and rewrite it following the Compression Rules below. Write the compressed content back to the original path.
4. **Validate.** Run `python3 validate.py <backup_path> <compressed_path>` using the `validate.py` in the same directory as this SKILL.md. Read the output.
5. **Fix if needed.** If validation reports errors, read the backup to see what was lost, then fix only the specific issues in the compressed file (do not recompress from scratch). Re-run validation. After 2 failed fix attempts, restore the backup to the original path, remove the backup file, and report the failure.
6. **Report.** Tell the user what was compressed and where the backup lives.

### Deep mode

Deep mode trusts you to read the codebase and make intelligent editorial decisions, the same way you would if a user asked you to "update my CLAUDE.md to reflect the current codebase." The difference is structure: you work section by section, verify before changing, and the backup provides a safety net.

1. **Guard and Backup.** Same as default mode.

2. **Read the whole file first.** Understand the document's purpose, scope, and how its sections relate to each other before making changes.

3. **Audit section by section.** Split by headings. For each section, read what it claims and verify against the codebase:

   - **File paths and imports:** Do they exist? Check with glob. If a path moved, find where it went.
   - **Function, class, and variable names:** Grep for them. Are they still defined? Still used the way the section describes?
   - **Commands and scripts:** Are the referenced tools present? Do the flags and arguments described still work?
   - **Behavioral descriptions:** If the section says "the auth middleware validates JWT tokens," read the actual auth middleware and confirm. If the behavior changed, the description is stale.
   - **Conventions and patterns:** If the section says "we use tabs" or "components follow the container pattern," spot-check 3-5 representative files. If the codebase contradicts the claim, the claim is stale.
   - **Architecture and data flow:** If the section describes how services communicate or how data moves through the system, verify against the actual code structure.

4. **Make decisions.** For each finding, act:

   - **Accurate:** Keep it. Move on.
   - **Stale (the thing no longer exists or the description is wrong):** Remove the content. If an entire section is stale, remove the section including its heading.
   - **Partially correct (moved, renamed, behavior changed):** Update the content to reflect reality. Don't just delete, fix it.
   - **Genuinely uncertain (can't determine from the codebase alone):** Keep it and add a note in the report. Don't remove what you can't disprove.

5. **Write the audited file.** Apply all removals and updates. Save a copy of this audited content as the validation baseline (e.g., `<stem>.audited.md`).

6. **Compress.** Apply the same verbosity reduction as default mode to the surviving content. Write the compressed result to the original path.

7. **Validate, Fix.** Run `validate.py` comparing the **audited file** (step 5) against the **compressed file** (step 6), not the original backup. The audit intentionally changed content, so the original is the wrong baseline. After validation passes or the fix loop completes, remove the audited file.

8. **Report.** In addition to the standard compression stats, include:
   - Sections or content removed and why (one line each)
   - Content updated and what changed
   - Anything kept despite uncertainty

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

**Note:** In deep mode, the "Preserve EXACTLY" rules apply to the compression step only. During the audit step, stale paths, commands, and inline code references are updated or removed, that is the point of deep mode.

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

**Note:** In deep mode, code blocks containing stale examples (referencing deleted files, removed APIs) are removed along with their surrounding context during the audit step. The "read-only" rule applies during compression, not during auditing.

## Examples

### Default mode

Before:
> You should always make sure to run the test suite before pushing any changes to the main branch. This is important because it helps catch bugs early and prevents broken builds from being deployed to production.

After:
> Run tests before push to main. Important: catch bugs early, prevent broken prod deploys.

### Deep mode

Before (CLAUDE.md section):
> ## Database
> The application uses `src/db/legacy-connector.js` to connect to MongoDB. Always call `initPool()` before running queries. The pool size is configured in `config/database.yaml`.

After auditing the codebase, the agent finds `src/db/legacy-connector.js` no longer exists, the app now uses `src/db/prisma.ts` with PostgreSQL, and `config/database.yaml` was replaced by environment variables:

After:
> ## Database
> Uses `src/db/prisma.ts` with PostgreSQL. Connection configured via `DATABASE_URL` env var.

Report includes:
> - Removed: reference to `src/db/legacy-connector.js` (file deleted, replaced by `src/db/prisma.ts`)
> - Removed: `initPool()` guidance (no longer applicable with Prisma)
> - Updated: database config from `config/database.yaml` to `DATABASE_URL` env var
