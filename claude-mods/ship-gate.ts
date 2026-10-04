import type { Register, EngineInterface, PluginOptions } from 'claude-code';
import { classifyCommand } from './command.ts';
import type { Action } from './command.ts';
import { parseChecks, githubRepository, evaluatePublication, sameSnapshot } from './policy.ts';
import type { Snapshot, PullRequest } from './policy.ts';

async function configuration($: EngineInterface, options: PluginOptions) {
  const rows = await $.config.list();
  const value = (key: string) => rows.find(row => row.key === $.plugin.name + '.' + key)?.value ?? options[key];
  const mode = value('ship_gate_mode') ?? 'off';
  if (mode !== 'off' && mode !== 'enforce') throw new Error('Invalid Ship Gate mode.');
  return { mode, checks: value('ship_gate_checks') ?? '[]' };
}
async function run($: EngineInterface, argv: string[], cwd: string, optional = false) {
  const result = await $.process.run(argv, { cwd, timeoutMs: 30000 });
  if (result.isStdoutTruncated) throw new Error(argv[0] + ' evidence output was truncated.');
  if (optional && result.exitCode === 1) return '';
  if (result.exitCode !== 0) throw new Error(argv[0] + ' evidence collection failed (exit ' + result.exitCode + ').');
  return result.stdout;
}
async function collect($: EngineInterface, a: Action): Promise<Snapshot> {
  const session = await $.session.cwd();
  const prefix = a.directory ? ['git', '-C', a.directory] : ['git'];
  const repository = (await run($, [...prefix, 'rev-parse', '--show-toplevel'], session)).trim();
  const git = async (args: string[], optional = false) => run($, ['git', ...args], repository, optional);
  const branch = (await git(['branch', '--show-current'])).trim();
  const head = (await git(['rev-parse', '--verify', 'HEAD'])).trim();
  let baseBranch: string;
  const symbolic = await $.process.run(['git', 'symbolic-ref', 'refs/remotes/origin/HEAD'], { cwd: repository });
  if (symbolic.exitCode === 0 && symbolic.stdout.startsWith('refs/remotes/origin/')) {
    baseBranch = symbolic.stdout.trim().slice('refs/remotes/origin/'.length);
  } else {
    const conventional = await $.process.run(['git', 'rev-parse', '--verify', 'main'], { cwd: repository });
    baseBranch = conventional.exitCode === 0 ? 'main' : 'master';
  }
  let baseRef = baseBranch;
  let base = await $.process.run(['git', 'rev-parse', '--verify', baseRef], { cwd: repository });
  if (base.exitCode !== 0) {
    baseRef = 'origin/' + baseBranch;
    base = await $.process.run(['git', 'rev-parse', '--verify', baseRef], { cwd: repository });
  }
  if (base.exitCode !== 0 || !base.stdout.trim()) throw new Error('The default branch does not resolve locally or on origin.');
  const fetchUrl = (await git(['remote', 'get-url', 'origin'])).trim();
  const pushUrls = (await git(['remote', 'get-url', '--push', '--all', 'origin'])).trim().split('\n');
  const origin = fetchUrl;
  if (pushUrls.length !== 1 || pushUrls[0] !== origin) throw new Error('Origin has an ambiguous or different push destination.');
  if (a.operation === 'push') {
    const mirror = (await git(['config','--bool','--get','remote.origin.mirror'], true)).trim();
    const tags = (await git(['config','--bool','--get','push.followTags'], true)).trim();
    if (mirror === 'true' || tags === 'true') throw new Error('Push configuration would publish additional refs. Disable mirroring or follow-tags first.');
  }
  if (a.operation === 'push' && !a.branch) {
    const remote = (await git(['config','--get', 'branch.' + branch + '.pushRemote'], true)).trim()
      || (await git(['config','--get','remote.pushDefault'], true)).trim()
      || (await git(['config','--get','branch.' + branch + '.remote'], true)).trim() || 'origin';
    if ((a.remote ?? remote) !== 'origin') throw new Error('Use git push origin with the current branch explicitly.');
    const refspec = (await git(['config','--get-all','remote.origin.push'], true)).trim();
    const mode = (await git(['config','--get','push.default'], true)).trim() || 'simple';
    const upstream = (await git(['config','--get','branch.' + branch + '.merge'], true)).trim();
    if (refspec || !['simple','current','upstream'].includes(mode) || (mode !== 'current' && upstream && upstream !== 'refs/heads/' + branch)) {
      throw new Error('Implicit push destination is ambiguous. Use git push origin with the current branch explicitly.');
    }
  }
  const target = a.operation === 'delete' ? a.branch : branch;
  const remoteOutput = await git(['ls-remote','--heads','origin','refs/heads/' + target]);
  const remoteLines = remoteOutput.trim() ? remoteOutput.trim().split('\n') : [];
  if (remoteLines.length > 1) throw new Error('The remote feature branch is ambiguous.');
  const count = Number((await git(['rev-list','--count',baseRef + '..HEAD'])).trim());
  if (!Number.isSafeInteger(count) || count < 0) throw new Error('The feature commit count is invalid.');
  return {
    repository, branch, head, baseBranch, baseRef, baseCommit:base.stdout.trim(), origin,
    clean: (await git(['status','--porcelain=v1','--untracked-files=all'])).length === 0,
    commitsAhead:count,
    paths:[...new Set((await git(['log','--format=','--name-only','-z','--no-renames','--diff-merges=separate',baseRef + '..HEAD'])).split('\0').filter(Boolean))],
    remoteHead:remoteLines[0]?.split(/\s/)[0],
  };
}
async function inspectPR($: EngineInterface, a: Action, s: Snapshot): Promise<PullRequest | undefined> {
  if (a.operation !== 'create' && a.operation !== 'merge') return undefined;
  const origin = githubRepository(s.origin);
  if (a.operation === 'create' || a.operation === 'merge') {
    const argv = ['gh','repo','view'];
    if (a.repo) argv.push(a.repo);
    argv.push('--json','url,defaultBranchRef');
    const target = JSON.parse(await run($, argv, s.repository));
    if (githubRepository(target.url) !== origin || target.defaultBranchRef?.name !== s.baseBranch) throw new Error('GitHub inferred a different repository or default branch. Specify origin with --repo and its default branch with --base.');
    if (a.operation === 'create') {
      const configuredBase = (await run($, ['git','config','--get','branch.' + s.branch + '.gh-merge-base'], s.repository, true)).trim();
      const upstreamRemote = (await run($, ['git','config','--get','branch.' + s.branch + '.remote'], s.repository, true)).trim();
      const upstreamBranch = (await run($, ['git','config','--get','branch.' + s.branch + '.merge'], s.repository, true)).trim();
      if ((!a.base && configuredBase && configuredBase !== s.baseBranch) || (!a.head && (upstreamRemote && upstreamRemote !== 'origin' || upstreamBranch && upstreamBranch !== 'refs/heads/' + s.branch))) throw new Error('Specify the current branch with --head and the default branch with --base.');
    }
  }
  if (a.operation !== 'merge') return undefined;
  const fields = 'state,isDraft,baseRefName,headRefName,headRefOid,mergeStateStatus,reviewDecision,url,isCrossRepository';
  if (a.operation === 'merge') {
    const argv = ['gh','pr','view'];
    if (a.selector) argv.push(a.selector);
    argv.push('--repo',origin,'--json',fields);
    const raw = await run($, argv, s.repository);
    const pr = JSON.parse(raw) as PullRequest;
    const strategies = JSON.parse(await run($, ['gh','repo','view',origin,'--json','mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed'], s.repository));
    const field = ({merge:'mergeCommitAllowed',squash:'squashMergeAllowed',rebase:'rebaseMergeAllowed'} as Record<string,string>)[a.explicitStrategy ?? ''];
    if (!field || strategies[field] !== true) throw new Error('Specify a merge strategy allowed by origin.');
    return pr;
  }
  return undefined;
}

export const register: Register = (on, options) => {
  let last = 'No publication checked in this session.';
  on('session.start', async ($, e, next) => {
    await $.command.register({ name:'ship-gate', description:'Show Claude Ship Gate status' });
    return next(e);
  });
  on('command.run', { command:'ship-gate' }, async ($) => {
    const config = await configuration($, options);
    let checks: string;
    try { const count = parseChecks(config.checks).length; checks = count ? count + ' verification commands' : 'verification not configured'; }
    catch { checks = 'invalid verification configuration'; }
    return { text:'Ship Gate: ' + config.mode + ', ' + checks + '. Checks direct Git push and cleanup on any host, plus GitHub PR create/merge. Hosted merge confirmation for cleanup belongs to the workflow skill. ' + last };
  });
  on('tool.check', { tool:'Bash' }, async ($, e, next) => {
    const input = e.input as { command?: unknown };
    if (typeof input?.command !== 'string') return next(e);
    const action = classifyCommand(input.command);
    if (action.kind === 'pass') return next(e);
    const config = await configuration($, options);
    if (config.mode === 'off') return next(e);
    const native = await next(e);
    if (native.decision === 'deny') return native;
    const deny = (reason: string) => { last = 'Blocked: ' + reason; return { decision:'deny' as const, reason:'Ship Gate: ' + reason }; };
    if (action.kind === 'unsupported-publication') return deny('Use a separate direct publication command with literal arguments, no force/admin options or unsupported flags.');
    const checks = parseChecks(config.checks);
    const before = await collect($, action);
    const pr = await inspectPR($, action, before);
    const decision = evaluatePublication(before, action, pr);
    if (decision.kind === 'deny') return deny(decision.reason);
    if (action.operation !== 'delete') {
      for (const argv of checks) {
        const result = await $.process.run(argv, { cwd:before.repository, timeoutMs:600000 });
        if (result.exitCode !== 0) {
          const detail = (result.stderr || result.stdout).replace(/[\x00-\x08\x0b-\x1f\x7f]/g, '').trim().slice(0, 512);
          return deny('Verification command ' + argv[0] + ' failed (exit ' + result.exitCode + ').' + (detail ? '\n' + detail : ''));
        }
      }
    }
    if (decision.kind === 'confirm-paths') {
      const answer = await $.ui.ask('Publish these high-risk paths once: ' + decision.paths.map(path => JSON.stringify(path)).join(', ') + '?', ['Proceed once','Cancel']);
      if (answer !== 'Proceed once') return deny('High-risk paths were not approved.');
    }
    const after = await collect($, action);
    if (!sameSnapshot(before, after)) return deny('Repository or destination changed during checks. Retry with fresh evidence.');
    const finalConfig = await configuration($, options);
    if (finalConfig.mode !== config.mode || finalConfig.checks !== config.checks) return deny('Ship Gate configuration changed during checks. Retry with fresh settings.');
    const finalPR = await inspectPR($, action, after);
    const finalDecision = evaluatePublication(after, action, finalPR);
    if (finalDecision.kind === 'deny') return deny(finalDecision.reason);
    last = 'Passed: publication checks' + (checks.length ? ' and configured verification.' : ', verification not configured.');
    return native;
  }).catch(async (_$, e, next) => {
    const command = (e.input as { command?: unknown })?.command;
    if (typeof command === 'string' && classifyCommand(command).kind !== 'pass') {
      last = 'Blocked: evidence collection, verification, or confirmation failed.';
      return { decision:'deny', reason:'Ship Gate: evidence collection, verification, or confirmation failed. No publication was permitted.' };
    }
    if (!next.called) return next(e);
    throw new Error('The native permission check failed.');
  });
};
