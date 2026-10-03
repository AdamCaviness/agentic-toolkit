# Claude Ship Gate verification

Ship Gate is an optional Claude module in the existing agentic-toolkit plugin.
The Claude manifest names `./claude-mods/hooks.json`, resolved from the plugin
root. Other
manifests do not register it. The shared 13 skills are unchanged.

## Configuration and coverage

Use Claude Code 2.1.287 or later. In `/config`, set **Ship Gate** to **enforce**.
The default is **off**. `/ship-gate` reports mode, configured verification, and
the last session verdict. Restoring **off** keeps every skill available.

**Ship Gate verification commands** is JSON, for example
`[["npm","test"],["npm","run","lint"]]`. Up to eight nonempty argv arrays are
accepted, with at most 64 arguments each. Commands run without shell expansion
in the repository being published. This plugin configuration applies across
projects. Empty `[]` means **verification not configured**, never tests passed.

The gate checks supported Bash calls for direct `git push`, `gh pr create`,
`gh pr merge`, and `git push origin --delete <branch>`. Publication requires a
clean feature branch and a verified default branch and origin. PR operations
verify the host repository, base, head branch, and head commit. Merge requires
one explicit allowed strategy and host evidence that checks and reviews permit
it. Cleanup requires a matching merged PR and an unchanged remote branch head;
cleanup skips verification commands. Implicit pushes are accepted only when
Git configuration identifies a single current-branch destination on origin.

The canonical filename screen is shared with the publishing skills. Matching
paths need exact **Proceed once** confirmation. Native permission decisions,
including **ask**, remain in force. Failed checks, failed evidence collection,
truncated inventories, missing confirmation, and changed repository snapshots
or settings deny the pending action. Confirmation never overrides another
failed rule. The module collects evidence but never launches publication itself.

Run publication separately with literal arguments. Compound shell programs,
force options, administrator merges, additional refs, and ambiguous destinations
are rejected when recognized. Scripts, aliases, MCP tools, other modules, and
publication outside supported Claude Bash calls are outside coverage. Hooks
must be enabled and loaded. A process can change state after the final check;
this is not an atomic host transaction. Filenames are screened, not contents.
Keep host protections and content secret scanning in place.

There is no default `hooks/hooks.json`, classic-hook fallback, second plugin,
module reference in another harness manifest, duplicated skill tree, model
call, HTTP client, telemetry, or persistent transcript storage.

## Automated verification

From the repository root:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -t tests
ruff check .
claude plugin validate . --json
claude plugin test .
node --test tests/ship_gate_integration.mjs
claude -p /ship-gate --plugin-dir . --no-session-persistence
npx --yes --package typescript@5.9.3 tsc -p tsconfig.json --allowImportingTsExtensions
```

Loading `/ship-gate` generates ignored declarations and `tsconfig.json`; static
validation and native tests do not. Type checking uses these runtime declarations.
CI runs the diagnostic with temporary settings storage and verifies no model
turn occurred before checking types. CI pins Claude Code 2.1.288 and
TypeScript 5.9.3, with Node 24. Native tests need no model or sign-in. Required
test jobs do not silently skip an unavailable runtime.

Native tests exercise command parsing, the complete canonical path corpus,
policy decisions, permission preservation, verification failure, approval,
GitHub target inference, merge evidence, cleanup, and configuration changes.
Process calls and human answers are stubbed through Claude's own test runner.
Local Git integration tests use disposable repositories and bare origins,
including newline-containing filenames and remote-only default refs. They do
not push, merge, or delete anything on a hosted repository.

## Compatibility evidence

These checks were performed on macOS on 2026-10-03. A loader or validator check
establishes component discovery, not an end-to-end model session.

| Route | Version | Evidence |
| --- | --- | --- |
| Claude module registration | 2.1.288 | Manifest and module validation pass with no warnings; only `session.start`, `command.run`, and Bash `tool.check` are registered. Native behavioral tests cover off and enforce. |
| Claude diagnostic command | 2.1.288 | `--plugin-dir` loads the real module and `/ship-gate` returns off and enforce status with temporary settings, without a model call. |
| Minimum Claude runtime | 2.1.287 | Native manifest and custom-path module validation pass. |
| Earlier Claude runtime | 2.1.286 | Native manifest and module validation also pass; the documented minimum remains 2.1.287. |
| Codex native plugin | 0.160.0 | Real app-server `plugin/read` discovers 13 skills and an empty hooks list in a temporary marketplace. |
| Codex Claude-manifest fallback | 0.160.0 | Removing the Codex and Cursor manifests from the temporary copy still discovers 13 skills and an empty hooks list. |
| Codex manual skills | 0.160.0 | Real app-server extra-root skill discovery finds the 13 shared skills with no errors. |
| Gemini extension | 0.62.0 | Native `extensions validate` accepts the full plugin tree without modifying the installed extension. |
| Cursor native and Claude import | 3.23.12 | Manifest isolation is covered by automated validators. Desktop loading remains unverified because the Mac was locked during the check. |
| Manual skill-only copies | Shared files | No skill file changes or module references; only copying `skills/` cannot install the module. |

Before claiming full Cursor runtime compatibility, test temporary copies in
`~/.cursor/plugins/local/`, first with `.cursor-plugin/plugin.json`, then with
only `.claude-plugin/plugin.json`. Verify all 13 skills, no Ship Gate hook or
command, and no loader errors with Claude configuration set to enforce. Remove
only the temporary copies afterward. Do not change the operator's installed
marketplace plugin or test publication against unrelated hosted branches.

References: [Claude mod testing](https://code.claude.com/docs/en/plugins/mods/test),
[Claude manifest paths](https://code.claude.com/docs/en/plugins/manifest-reference),
[Codex packaging](https://developers.openai.com/plugins/build/plugins), and
[Cursor plugin loading](https://cursor.com/docs/reference/plugins).
