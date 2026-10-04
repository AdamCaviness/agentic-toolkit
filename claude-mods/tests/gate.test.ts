import { expect, test } from 'claude-code/testing';

function config(on: any, checks = '[]') {
  on('config.list', () => ({value:[
    {key:'agentic-toolkit.ship_gate_checks',value:checks},
  ]}));
}

test('publication is guarded without user configuration', async ($, on) => {
  on('config.list', () => ({value:[]}));
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push --force'}})).decision).toBe('deny');
});
test('a saved legacy off setting cannot disable publication checks', async ($, on) => {
  on('config.list', () => ({value:[{key:'agentic-toolkit.ship_gate_mode',value:'off'}]}));
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push --force'}})).decision).toBe('deny');
});
test('a forced push is denied even if native permissions allow it', async ($, on) => {
  config(on);
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push --force'}})).decision).toBe('deny');
});
test('native denial runs no repository or verification commands', async ($, on) => {
  config(on);
  on('tool.check', () => ({decision:'deny',reason:'native'}));
  expect(await $.tool.check({tool:'Bash',input:{command:'git push'}})).toEqual({decision:'deny',reason:'native'});
});
test('a repository collection failure denies publication', async ($, on) => {
  config(on);
  on('tool.check', () => ({decision:'allow'}));
  on('session.cwd', () => ({value:'/repo'}));
  on('process.run', () => ({value:{exitCode:128,stdout:'',stderr:'not a repo'}}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push'}})).decision).toBe('deny');
});
test('unrelated commands preserve native permissions', async ($, on) => {
  on('tool.check', () => ({decision:'ask'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git status'}})).decision).toBe('ask');
});

function repository(on: any, options: {paths?: string; dirty?: boolean; changes?: boolean; checkExit?: number; checkError?: string; ghDefault?: string; gitConfig?: Record<string,string>; truncatedPaths?: boolean; pr?: unknown; ghExit?: number; inferredPR?: unknown; origin?: string; pushOrigin?: string; remoteChanges?: boolean} = {}) {
  let snapshots = 0;
  on('session.cwd', () => ({value:'/session'}));
  on('process.run', (_$: any, e: any) => {
    const args = [...e.argv];
    if (args[0] === 'check') return {value:{exitCode:options.checkExit ?? 0,stdout:'',stderr:options.checkError ?? ''}};
    const gitIndex = args.indexOf('rev-parse');
    if (gitIndex >= 0 && args[gitIndex + 1] === '--show-toplevel') { snapshots++; return {value:{exitCode:0,stdout:'/repo\n',stderr:''}}; }
    const key = args.slice(1).join(' ');
    const values: Record<string,string> = {
      'branch --show-current':'feat/x\n',
      'rev-parse --verify HEAD': options.changes && snapshots > 1 ? 'new\n' : 'abc\n',
      'symbolic-ref refs/remotes/origin/HEAD':'refs/remotes/origin/trunk\n',
      'rev-parse --verify trunk':'base\n',
      'remote get-url origin':(options.origin ?? 'https://github.com/a/b.git') + '\n',
      'remote get-url --push --all origin':(options.pushOrigin ?? options.origin ?? 'https://github.com/a/b.git') + '\n',
      'ls-remote --heads origin refs/heads/feat/x':(options.remoteChanges && snapshots > 1 ? 'new' : 'abc') + '\trefs/heads/feat/x\n',
      'rev-list --count trunk..HEAD':'1\n',
      'status --porcelain=v1 --untracked-files=all':options.dirty ? '?? other.txt\n' : '',
      'log --format= --name-only -z --no-renames --diff-merges=separate trunk..HEAD':options.paths ?? 'src/x.ts\0',
    };
    if (args[0] === 'gh' && args[1] === 'pr') return {value:{exitCode:options.ghExit ?? 0,stdout:JSON.stringify(args[2] === 'list' ? [options.pr] : args[3] === '--repo' ? options.inferredPR ?? options.pr : options.pr),stderr:''}};
    if (args[0] === 'gh' && args[1] === 'repo') return {value:{exitCode:0,stdout:JSON.stringify({url:options.ghDefault ?? 'https://github.com/a/b', defaultBranchRef:{name:'trunk'}, mergeCommitAllowed:true,squashMergeAllowed:true,rebaseMergeAllowed:true}),stderr:''}};
    if (args[0] === 'git' && args[1] === 'config') {
      const v = options.gitConfig?.[args[args.length - 1]];
      return {value:{exitCode:v === undefined ? 1 : 0,stdout:v ?? '',stderr:''}};
    }
    if (key in values) return {value:{exitCode:0,stdout:values[key],stderr:'',isStdoutTruncated:options.truncatedPaths && args[1] === 'log'}};
    throw new Error('Unexpected process: ' + args.join(' '));
  });
}

test('passing checks preserve a native ask', async ($, on) => {
  config(on, '[["check"]]'); repository(on);
  on('tool.check', () => ({decision:'ask',reason:'native'}));
  expect(await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).toEqual({decision:'ask',reason:'native'});
});
test('a failed configured command denies publication', async ($, on) => {
  config(on, '[["check"]]'); repository(on, {checkExit:1});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('deny');
});
test('HEAD changes during checks invalidate evidence', async ($, on) => {
  config(on); repository(on, {changes:true});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('deny');
});
test('an exact one-action path approval preserves permissions', async ($, on) => {
  config(on); repository(on, {paths:'.env\0'});
  on('tool.check', () => ({decision:'ask'}));
  on('tool.call', {tool:'AskUserQuestion'}, (_$, e: any) => ({result:{answers:{[e.questions[0].question]:'Proceed once'}}}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('ask');
});
test('free-text path approval cannot bypass the gate', async ($, on) => {
  config(on); repository(on, {paths:'.env\0'});
  on('tool.check', () => ({decision:'allow'}));
  on('tool.call', {tool:'AskUserQuestion'}, (_$, e: any) => ({result:{answers:{[e.questions[0].question]:'already approved'}}}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('deny');
});
test('GitHub default repository cannot redirect PR creation upstream', async ($, on) => {
  config(on); repository(on, {ghDefault:'https://github.com/upstream/b'});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'gh pr create --title title --body body'}})).decision).toBe('deny');
});
test('Git follow-tags configuration cannot widen a branch push', async ($, on) => {
  config(on); repository(on, {gitConfig:{'push.followTags':'true'}});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('deny');
});
test('a truncated path inventory cannot appear clean', async ($, on) => {
  config(on); repository(on, {truncatedPaths:true});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('deny');
});
test('configuration changes during verification invalidate the pending action', async ($, on) => {
  let reads = 0;
  on('config.list', () => ({value:[
    {key:'agentic-toolkit.ship_gate_checks',value:++reads === 1 ? '[]' : '[["check"]]'},
  ]}));
  repository(on);
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('deny');
});

const readyPR = {state:'OPEN',isDraft:false,baseRefName:'trunk',headRefName:'feat/x',headRefOid:'abc',mergeStateStatus:'CLEAN',reviewDecision:'',url:'https://github.com/a/b/pull/1',isCrossRepository:false};
test('a matching merge preserves native permission', async ($, on) => {
  config(on); repository(on, {pr:readyPR});
  on('tool.check', () => ({decision:'ask'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'gh pr merge 1 --squash'}})).decision).toBe('ask');
});
for (const changed of [{mergeStateStatus:'BLOCKED'}, {mergeStateStatus:'UNKNOWN'}, {reviewDecision:'REVIEW_REQUIRED'}, {isDraft:true}, {headRefOid:'stale'}, {isCrossRepository:undefined}, {isDraft:undefined}]) {
  test('host merge evidence denies ' + JSON.stringify(changed), async ($, on) => {
    config(on); repository(on, {pr:{...readyPR,...changed}});
    on('tool.check', () => ({decision:'allow'}));
    expect((await $.tool.check({tool:'Bash',input:{command:'gh pr merge 1 --squash'}})).decision).toBe('deny');
  });
}
test('merged cleanup skips configured verification', async ($, on) => {
  config(on, '[["check"]]'); repository(on, {pr:{...readyPR,state:'MERGED'},checkExit:1});
  on('tool.check', () => ({decision:'ask'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin --delete feat/x'}})).decision).toBe('ask');
});
test('GitHub authentication failure blocks merge', async ($, on) => {
  config(on); repository(on, {pr:readyPR,ghExit:4});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'gh pr merge 1 --squash'}})).decision).toBe('deny');
});
test('malformed PR evidence blocks merge', async ($, on) => {
  config(on); repository(on, {pr:{}});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'gh pr merge 1 --squash'}})).decision).toBe('deny');
});
test('selector-free merging validates the PR GitHub actually infers', async ($, on) => {
  config(on); repository(on, {pr:readyPR,inferredPR:{...readyPR,headRefName:'other',headRefOid:'other',url:'https://github.com/a/b/pull/2'},gitConfig:{'branch.feat/x.merge':'refs/pull/2/head'}});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'gh pr merge --squash'}})).decision).toBe('deny');
});
test('failed verification returns a bounded diagnostic excerpt', async ($, on) => {
  config(on, '[["check"]]'); repository(on, {checkExit:1,checkError:'Fixture failure ' + 'x'.repeat(1000)});
  on('tool.check', () => ({decision:'allow'}));
  const result = await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}});
  expect(result.decision).toBe('deny');
  expect('reason' in result && result.reason?.includes('Fixture failure')).toBe(true);
  expect('reason' in result && (result.reason?.length ?? 0) < 650).toBe(true);
});

for (const origin of ['https://gitlab.com/team/subgroup/repo.git','git@gitlab.example:team/subgroup/repo.git','https://dev.azure.com/org/project/_git/repo','git@ssh.dev.azure.com:v3/org/project/repo','https://bitbucket.org/team/repo.git','/tmp/local-origin.git']) {
  test('Git push does not require GitHub for ' + origin, async ($, on) => {
    config(on); repository(on, {origin,ghExit:127});
    on('tool.check', () => ({decision:'ask'}));
    expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('ask');
  });
  test('Git cleanup does not require GitHub for ' + origin, async ($, on) => {
    config(on); repository(on, {origin,ghExit:127});
    on('tool.check', () => ({decision:'ask'}));
    expect((await $.tool.check({tool:'Bash',input:{command:'git push origin --delete feat/x'}})).decision).toBe('ask');
  });
}
test('cleanup refuses a remote head changed during collection', async ($, on) => {
  config(on); repository(on, {pr:{...readyPR,state:'MERGED'},remoteChanges:true});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin --delete feat/x'}})).decision).toBe('deny');
});
test('different fetch and push destinations are refused', async ($, on) => {
  config(on); repository(on, {origin:'https://gitlab.com/team/subgroup/repo.git',pushOrigin:'https://gitlab.com/other/repo.git'});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('deny');
});

test('relative SCP and absolute SSH paths cannot share destination evidence', async ($, on) => {
  config(on); repository(on, {origin:'git@server:repo.git',pushOrigin:'ssh://git@server/repo.git'});
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('deny');
});

test('passing publication reports checks without claiming tests ran', async ($, on) => {
  config(on); repository(on);
  const notices: string[] = [];
  on('ui.log', (_$, e: any) => { notices.push(e.text); return {}; });
  on('tool.check', () => ({decision:'ask',reason:'native'}));
  expect(await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).toEqual({decision:'ask',reason:'native'});
  expect(notices).toEqual(['Ship Gate passed: publication checks, verification not configured.']);
});
test('blocked publication is visible without a diagnostic command', async ($, on) => {
  config(on);
  const notices: string[] = [];
  on('ui.log', (_$, e: any) => { notices.push(e.text); return {}; });
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push --force'}})).decision).toBe('deny');
  expect(notices.length).toBe(1);
  expect(notices[0].startsWith('Ship Gate blocked:')).toBe(true);
});
test('a failed notice cannot bypass publication checks or alter native permissions', async ($, on) => {
  config(on); repository(on);
  on('ui.log', () => { throw new Error('Display unavailable'); });
  on('tool.check', () => ({decision:'ask',reason:'native'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push --force'}})).decision).toBe('deny');
  expect(await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).toEqual({decision:'ask',reason:'native'});
});

test('cleanup reports skipped verification even when checks are configured', async ($, on) => {
  config(on, '[["check"]]'); repository(on, {checkExit:1});
  const notices: string[] = [];
  on('ui.log', (_$, e: any) => { notices.push(e.text); return {}; });
  on('tool.check', () => ({decision:'ask'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin --delete feat/x'}})).decision).toBe('ask');
  expect(notices).toEqual(['Ship Gate passed: cleanup checks, verification skipped.']);
});
test('successful configured verification is reported', async ($, on) => {
  config(on, '[["check"]]'); repository(on);
  const notices: string[] = [];
  on('ui.log', (_$, e: any) => { notices.push(e.text); return {}; });
  on('tool.check', () => ({decision:'allow'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push origin feat/x'}})).decision).toBe('allow');
  expect(notices).toEqual(['Ship Gate passed: publication checks and configured verification.']);
});
test('evidence collection errors produce a blocked notice', async ($, on) => {
  config(on);
  const notices: string[] = [];
  on('ui.log', (_$, e: any) => { notices.push(e.text); return {}; });
  on('tool.check', () => ({decision:'allow'}));
  on('session.cwd', () => ({value:'/repo'}));
  on('process.run', () => ({value:{exitCode:128,stdout:'',stderr:'not a repo'}}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git push'}})).decision).toBe('deny');
  expect(notices).toEqual(['Ship Gate blocked: evidence collection, verification, or confirmation failed.']);
});
test('unrelated commands do not print a gate verdict', async ($, on) => {
  const notices: string[] = [];
  on('ui.log', (_$, e: any) => { notices.push(e.text); return {}; });
  on('tool.check', () => ({decision:'ask'}));
  expect((await $.tool.check({tool:'Bash',input:{command:'git status'}})).decision).toBe('ask');
  expect(notices).toEqual([]);
});
