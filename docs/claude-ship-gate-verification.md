# Claude Ship Gate verification

Ship Gate is a Claude module in the existing agentic-toolkit plugin.
The Claude manifest names `./claude-mods/hooks.json`, resolved from the plugin
root. Other manifests do not register it. All harnesses discover the same 13 shared
skills, with a host-neutral cleanup instruction in `ship`.

## Configuration and coverage

Use Claude Code 2.1.287 or later. Ship Gate runs automatically when the plugin
is enabled and hooks are allowed. There is no separate activation setting or
`/ship-gate` command. Saved `ship_gate_mode` values are ignored, including `off`.
Native plugin and hook controls, including `disableAllHooks` and safe mode,
remain authoritative. Startup prints **Ship Gate active** with verification
configuration; supported publication attempts print **passed** or **blocked**.
These transcript notices use `$.ui.log` without a model turn. A passing notice
means the pending action passed the gate, not that publication completed.

**Ship Gate verification commands** is JSON, for example
`[["npm","test"],["npm","run","lint"]]`. Up to eight nonempty argv arrays are
accepted, with at most 64 arguments each. Commands run without shell expansion
in the repository being published. This plugin configuration applies across
projects. Empty `[]` means **verification not configured**, never tests passed.

The gate checks supported Bash calls for direct `git push`, `gh pr create`,
`gh pr merge`, and `git push origin --delete <branch>`. Publication requires a
clean feature branch and a verified default branch and origin. The default branch
comes from `origin/HEAD`, or else `main` then `master`, locally or on origin. Generic Git
operations accept GitLab subgroup, Azure DevOps, Bitbucket, self-hosted, and
local remote layouts without a GitHub CLI or login. Origin must have one push
URL identical to its fetch URL. Different transport or path spellings are
rejected instead of assuming equivalent destinations. GitHub PR operations
verify the host repository, base, head branch, and head commit. Merge requires
one explicit allowed strategy and host evidence that checks and reviews permit
it. Cleanup checks the target branch and an unchanged remote branch head, and
skips verification commands. The `ship` skill must separately confirm through
the repository host that the matching PR or MR is merged and its recorded head
matches the current remote branch. The runtime does not prove merged state for
cleanup. Non-GitHub PR and MR commands rely on skill instructions and host
protections; they have no runtime merge-policy check. Cross-provider workflow
adaptation is provided by the shared workflow skills. Implicit pushes are
accepted only when Git configuration identifies a single current-branch destination on origin.

The canonical filename screen is shared with the publishing skills. Inventory
comes from every feature commit, including paths removed by later commits,
with NUL-delimited names and merge diffs. Matching
paths need exact **Proceed once** confirmation. Native permission decisions,
including **ask**, remain in force. Failed checks, failed evidence collection,
truncated inventories, missing confirmation, and changed repository snapshots
or settings deny the pending action, and the denial carries the specific
reason. Confirmation never overrides another
failed rule. The module collects evidence but never launches publication itself.

Publication uses literal arguments. A supported compound call contains exactly
one publication invocation, at the start of its pipeline. One leading
`cd <path> &&` names the repository the publication runs in, and evidence is
collected there; it cannot be combined with `git -C`. `&&` may join it to
known read-only commands; subsequent pipeline stages are only `head -N`,
`tail -N`, `head -n N`, or `tail -n N`, with a literal nonnegative decimal count
and no files or other flags. Literal `2>&1` and `1>&2` duplicate output descriptors
without opening files. Quoted operators remain argument content; descriptor
numbers are distinguished from quoted, escaped, or whitespace-separated words.

Supported read-only neighbors are `gh auth status` without options, `git status`
with `--short`, `--branch`, `--porcelain`, `--porcelain=v1`, or
`--untracked-files=all`, and `gh pr view` with an optional literal selector,
`--repo`/`-R`, and `--json` fields. Long valued flags accept separate or equals
forms; duplicate selectors/options and other flags are rejected. JSON fields
are comma-separated identifier names. Every neighboring command is validated
by subcommand and arguments, not merely its executable name.

State changes, unknown neighbors, multiple publication invocations, commands
feeding publication input, file redirection, expansion, grouping, background
execution, `||`, semicolons, command-separating newlines, and unsupported syntax
require separate publication calls. Force options, administrator merges,
additional refs, and ambiguous destinations retain their existing rejection.
Diagnostics identify the unsupported context without echoing arbitrary bodies
or arguments. The gate does not rewrite the Bash input, run its neighbors,
or publish on the model's behalf. Native permissions check the full original
input. Output filters can mask publication failure in Bash's exit status; the
gate's pre-execution pass never certifies completion. Workflow skills and later
publication checks use actual remote and host evidence. Scripts, aliases, MCP
tools, other modules, and publication outside supported Claude Bash calls are
outside coverage. Hooks
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
node --test tests/ship_gate_integration.mjs tests/ship_gate_shell_integration.mjs
node --test tests/ship_gate_runtime_smoke.mjs
npx --yes --package typescript@5.9.3 tsc -p tsconfig.json --allowImportingTsExtensions
```

The runtime smoke test loads the real plugin using Claude’s built-in `/cost`
with temporary settings storage. It verifies the automatic startup notice, the
absence of `/ship-gate`, respect for native hook disabling, and zero model
turns or API usage. Loading generates
ignored declarations and `tsconfig.json`; static validation and native tests do
not. Type checking uses these runtime declarations. CI pins Claude Code
2.1.288 and TypeScript 5.9.3, with Node 24. Native tests need no model or sign-in. Required
test jobs do not silently skip an unavailable runtime.

Native tests exercise command parsing, the complete canonical path corpus,
policy decisions, activation without settings, ignored legacy off settings,
verdict notices, permission preservation, verification failure, approval,
GitHub target inference and merge evidence, host-neutral Git cleanup, shell
line continuations, intermediate commit paths, and configuration changes.
Process calls and human answers are stubbed through Claude's own test runner.
Local Git integration tests use disposable repositories and bare origins,
including newline-containing filenames and remote-only default refs. Bash
integration tests use disposable recording executables to compare actual
publication argv and cwd with the extracted action, including descriptor and
quoting boundaries. They also demonstrate that a passing output-filter pipeline
can mask a failed publication executable. These tests do
not push, merge, or delete anything on a hosted repository.

## Compatibility evidence

These checks were performed on macOS on 2026-10-03. A loader or validator check
establishes component discovery, not an end-to-end model session.

| Route | Version | Evidence |
| --- | --- | --- |
| Claude module registration | 2.1.288 and 2.1.289 | Manifest and module validation pass with no warnings; only `session.start` and Bash `tool.check` are registered. Native behavioral tests cover automatic activation and ignored legacy off settings. |
| Claude automatic startup | 2.1.288 and 2.1.289 | `--plugin-dir` loads the real module with temporary settings, emits the startup notice, and exposes no Ship Gate command, with zero model turns or API usage. |
| Minimum Claude runtime | 2.1.287 | Native manifest and custom-path module validation pass. |
| Earlier Claude runtime | 2.1.286 | Native manifest and module validation also pass; the documented minimum remains 2.1.287. |
| Codex native plugin | 0.160.0 | Real app-server `plugin/read` discovers 13 skills and an empty hooks list in a temporary marketplace. |
| Codex Claude-manifest fallback | 0.160.0 | Removing the Codex and Cursor manifests from the temporary copy still discovers 13 skills and an empty hooks list. |
| Codex manual skills | 0.160.0 | Real app-server extra-root skill discovery finds the 13 shared skills with no errors. |
| Gemini extension | 0.62.0 | Native `extensions validate` accepts the full plugin tree without modifying the installed extension. |
| Cursor native and Claude import | 3.23.12 | Real desktop component discovery loads all 13 skills from temporary native and Claude-manifest-only local copies. Only skills appear in plugin details. The Claude-import hook inventory contains no Ship Gate hook, and its commands inventory is empty, with the original test Claude default set to enforce. |
| Manual skill-only copies | Shared files | No skill file changes or module references; only copying `skills/` cannot install the module. |

To reproduce Cursor component discovery, test temporary copies in
`~/.cursor/plugins/local/`, first with `.cursor-plugin/plugin.json`, then with
only `.claude-plugin/plugin.json`. Verify all 13 skills, no Ship Gate hook or
command, and no loader errors. The verification used unique test plugin names and removed
only the temporary copies afterward; it did not run a model or publication. Remove
only your temporary copies afterward. Do not change the operator's installed
marketplace plugin or test publication against unrelated hosted branches.

References: [Claude automatic mod activation](https://code.claude.com/docs/en/plugins/mods/overview#turn-mods-on-or-off),
[Claude transcript notices](https://code.claude.com/docs/en/plugins/mods/api#show-something-without-starting-a-turn),
[Claude mod testing](https://code.claude.com/docs/en/plugins/mods/test),
[Claude manifest paths](https://code.claude.com/docs/en/plugins/manifest-reference),
[Codex packaging](https://developers.openai.com/plugins/build/plugins), and
[Cursor plugin loading](https://cursor.com/docs/reference/plugins).
