import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, mkdirSync, rmSync, realpathSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { classifyCommand } from '../claude-mods/command.ts';

const cases = [
  'gh auth status 2>&1 | head -3 && git push -u origin fix/ticket-system-config-recovery 2>&1 | tail -2 && gh pr view fix/ticket-system-config-recovery --repo AdamCaviness/agentic-toolkit --json number,state 2>&1',
  'git push origin feat/x 2>&1',
  '2>&1 git push origin feat/x',
  'git push 2>&1 origin feat/x | tail -2',
  'git status --short --branch && git push origin feat/x 1>&2 | tail -n 2',
  'git push origin feat/x && gh pr view feat/x --repo=a/b --json=number,state',
  'gh pr create --body "A && B | C" 2>&1 | tail -2',
  'gh pr merge 1 --squash 2>&1 | head -n 2',
  'git push origin --delete feat/x | tail -2',
  'git -C "a b" push origin feat/x 2>& 1',
  'git push origin "2" 1>&2',
  "git push origin ''2 1>&2",
  'git push origin \\2 1>&2',
  'git push origin 2 1>&2',
  "gh pr create --body '2>&1 && git push --force' 2>&1",
];

function fixture(t) {
  const root = realpathSync(mkdtempSync(join(tmpdir(), 'ship-gate-shell-')));
  t.after(() => rmSync(root, { recursive:true, force:true }));
  const bin = join(root, 'bin'); mkdirSync(bin);
  const record = join(root, 'calls.jsonl');
  const stub = join(root, 'stub.mjs');
  writeFileSync(stub, `import {appendFileSync} from 'node:fs';
appendFileSync(process.env.RECORD, JSON.stringify({argv:process.argv.slice(2),cwd:process.cwd()})+'\\n');
console.log('fixture output');
process.exit(Number(process.env.STUB_EXIT ?? 0));
`);
  for (const executable of ['git','gh']) {
    writeFileSync(join(bin, executable), '#!/bin/sh\nexec "$NODE" "$STUB" ' + executable + ' "$@"\n', {mode:0o755});
  }
  function execute(command, exitCode = 0) {
    return spawnSync('bash', ['--noprofile','--norc','-c',command], {
      cwd:root, encoding:'utf8', timeout:10000,
      env:{PATH:bin + ':/usr/bin:/bin',NODE:process.execPath,STUB:stub,RECORD:record,STUB_EXIT:String(exitCode)},
    });
  }
  function calls() { return readFileSync(record, 'utf8').trim().split('\n').map(line => JSON.parse(line)); }
  return {root, execute, calls};
}

for (const command of cases) {
  test('Bash receives exactly the extracted publication argv: ' + command, t => {
    const f = fixture(t);
    const action = classifyCommand(command);
    assert.ok(['publish','delete'].includes(action.kind));
    const result = f.execute(command);
    assert.equal(result.error, undefined);
    assert.equal(result.status, 0, result.stderr);
    const publication = f.calls().filter(({argv}) => argv[0] === 'git' && argv.includes('push')
      || argv[0] === 'gh' && argv[1] === 'pr' && ['create','merge'].includes(argv[2]));
    assert.equal(publication.length, 1);
    assert.deepEqual(publication[0].argv, action.argv);
    assert.equal(publication[0].cwd, f.root);
  });
}

test('a supported output filter does not certify successful publication', t => {
  const f = fixture(t);
  const command = 'git push origin feat/x 2>&1 | tail -2';
  assert.equal(classifyCommand(command).kind, 'publish');
  assert.equal(f.execute(command, 17).status, 0);
  assert.deepEqual(f.calls()[0].argv, ['git','push','origin','feat/x']);
});
