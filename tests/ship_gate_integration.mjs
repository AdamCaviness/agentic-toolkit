import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { register } from '../claude-mods/ship-gate.ts';

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'ship-gate-git-'));
  t.after(() => rmSync(root, { recursive:true, force:true }));
  const cwd = join(root, 'work');
  const bare = join(root, 'origin.git');
  function command(argv, directory = cwd) {
    const result = spawnSync(argv[0], argv.slice(1), {cwd:directory, encoding:'utf8'});
    return {exitCode:result.status ?? 1,stdout:result.stdout ?? '',stderr:result.stderr ?? ''};
  }
  function git(...args) {
    const result = command(['git',...args]);
    assert.equal(result.exitCode,0,result.stderr);
    return result.stdout;
  }
  assert.equal(command(['git','init','--bare',bare], root).exitCode,0);
  assert.equal(command(['git','init','-b','trunk',cwd], root).exitCode,0);
  git('config','user.name','Fixture'); git('config','user.email','fixture@example.invalid');
  writeFileSync(join(cwd,'base.txt'),'base'); git('add','base.txt'); git('commit','-m','base');
  git('remote','add','origin',bare); git('push','origin','trunk');
  git('symbolic-ref','refs/remotes/origin/HEAD','refs/remotes/origin/trunk');
  git('checkout','-b','feat/x');
  writeFileSync(join(cwd,'file with\na newline.txt'),'feature');
  git('add','.'); git('commit','-m','feature'); git('push','origin','feat/x');
  git('remote','set-url','origin','https://github.com/fixture/repo.git');
  let handler, recover, mutate;
  const processCalls = [];
  const api = {
    plugin:{name:'agentic-toolkit'},
    config:{list:async () => [
      {key:'agentic-toolkit.ship_gate_mode',value:'enforce'},
      {key:'agentic-toolkit.ship_gate_checks',value:'[]'},
    ]},
    session:{cwd:async () => cwd},
    process:{run:async (argv, init) => {
      processCalls.push(argv);
      const actual = [...argv];
      if (argv[0] === 'git' && argv[1] === 'ls-remote') actual[3] = bare;
      if (mutate && argv[1] === 'log') { mutate(); mutate = undefined; }
      return command(actual, init?.cwd ?? cwd);
    }},
    ui:{ask:async () => 'Cancel'},
  };
  register((event, matcher, callback) => {
    if (event === 'tool.check') handler = callback;
    return {catch(fn) { if (event === 'tool.check') recover = fn; }};
  }, {});
  async function check(commandText, native = 'ask') {
    const event = {tool:'Bash',input:{command:commandText}};
    const next = async () => ({decision:native});
    try { return await handler(api,event,next); }
    catch (error) { next.error = {kind:'throw',message:error.message}; next.called = true; return recover(api,event,next); }
  }
  return {cwd, git, api, check, processCalls, setMutation(fn) {mutate = fn;}};
}

test('actual Git state permits a feature push and preserves native ask', async t => {
  const f = fixture(t);
  const result = await f.check('git push origin feat/x');
  assert.equal(result.decision,'ask');
  assert.equal(f.processCalls.some(a => a[1] === 'push'),false);
});
test('a remote-only default ref resolves in a single-branch checkout', async t => {
  const f = fixture(t); f.git('branch','-D','trunk');
  assert.equal((await f.check('git push origin feat/x')).decision,'ask');
});
test('actual untracked work prevents publication', async t => {
  const f = fixture(t); writeFileSync(join(f.cwd,'untracked.txt'),'untracked');
  assert.equal((await f.check('git push origin feat/x')).decision,'deny');
});
test('actual commit path inventory detects a secret-shaped filename', async t => {
  const f = fixture(t); writeFileSync(join(f.cwd,'client_secrets_v2.json'),'fixture');
  f.git('add','client_secrets_v2.json'); f.git('commit','-m','fixture secret path');
  let asked = false;
  f.api.ui.ask = async () => {asked=true; return 'Cancel';};
  assert.equal((await f.check('git push origin feat/x')).decision,'deny');
  assert.equal(asked,true);
});
test('a repository mutation between snapshots denies publication', async t => {
  const f = fixture(t);
  f.setMutation(() => writeFileSync(join(f.cwd,'changed.txt'),'changed'));
  assert.equal((await f.check('git push origin feat/x')).decision,'deny');
});
test('actual push configuration cannot redirect to upstream', async t => {
  const f = fixture(t); f.git('config','remote.pushDefault','upstream');
  assert.equal((await f.check('git push')).decision,'deny');
});
test('git -C resolves the publication repository explicitly', async t => {
  const f = fixture(t);
  assert.equal((await f.check('git -C ' + JSON.stringify(f.cwd) + ' push origin feat/x')).decision,'ask');
});
test('an actual linked worktree resolves branch and default-ref evidence', async t => {
  const f = fixture(t); const linked = join(f.cwd,'..','linked');
  f.git('worktree','add','-b','feat/linked',linked);
  f.api.session.cwd = async () => linked;
  assert.equal((await f.check('git push origin feat/linked')).decision,'ask');
});
test('an actual detached checkout cannot publish', async t => {
  const f = fixture(t); f.git('checkout','--detach');
  assert.equal((await f.check('git push origin feat/x')).decision,'deny');
});
test('an actual unborn branch fails closed', async t => {
  const f = fixture(t); f.git('checkout','--orphan','feat/unborn');
  assert.equal((await f.check('git push origin feat/unborn')).decision,'deny');
});
test('missing local and remote default refs cannot appear clean', async t => {
  const f = fixture(t); f.git('branch','-D','trunk'); f.git('update-ref','-d','refs/remotes/origin/trunk');
  assert.equal((await f.check('git push origin feat/x')).decision,'deny');
});
test('missing origin cannot appear as a valid destination', async t => {
  const f = fixture(t); f.git('remote','remove','origin');
  assert.equal((await f.check('git push origin feat/x')).decision,'deny');
});

test('a high-risk file removed in a later commit still requires approval', async t => {
  const f = fixture(t);
  writeFileSync(join(f.cwd,'.env'),'fixture, not a real secret');
  f.git('add','.env'); f.git('commit','-m','temporary high-risk path');
  f.git('rm','.env'); f.git('commit','-m','remove temporary path');
  let asked = false;
  f.api.ui.ask = async () => {asked=true; return 'Cancel';};
  assert.equal((await f.check('git push origin feat/x')).decision,'deny');
  assert.equal(asked,true);
});

test('a local Git remote works without a hosted repository identity', async t => {
  const f = fixture(t);
  f.git('remote','set-url','origin',join(f.cwd,'..','origin.git'));
  assert.equal((await f.check('git push origin feat/x')).decision,'ask');
  assert.equal(f.processCalls.some(a => a[0] === 'gh'),false);
});

test('cleanup checks Git state without a provider CLI', async t => {
  const f = fixture(t);
  f.git('remote','set-url','origin',join(f.cwd,'..','origin.git'));
  assert.equal((await f.check('git push origin --delete feat/x')).decision,'ask');
  assert.equal(f.processCalls.some(a => a[0] === 'gh'),false);
  assert.equal((await f.check('git push origin --delete trunk')).decision,'deny');
});
