import { expect, test } from 'claude-code/testing';
import { classifyCommand } from '../command.ts';

test('read-only commands with publication words in arguments pass', () => {
  for (const command of ['git log --grep push', 'git show push', 'gh issue create --title "pr merge"']) {
    expect(classifyCommand(command).kind).toBe('pass');
  }
});
test('assignment-prefixed publication requires a separate direct command', () => {
  for (const command of ['FOO=bar git push --force', 'FOO="a b" BAR=x gh pr merge 2 --admin']) {
    expect(classifyCommand(command).kind).toBe('unsupported-publication');
  }
  expect(classifyCommand('FOO=bar git status').kind).toBe('pass');
});

for (const command of ['git push', 'git push -u origin feat/example', 'git -C "a b" push origin feat/example', 'gh pr create --body "A; B && C"', 'gh pr merge 12 --squash', 'git push origin --delete feat/old']) {
  test('recognizes ' + command, () => expect(classifyCommand(command).kind).not.toBe('pass'));
}
for (const command of ['git status', 'gh pr checks', 'echo "git push"', 'rg "git push" README.md', 'npm test && echo ok']) {
  test('passes ' + command, () => expect(classifyCommand(command).kind).toBe('pass'));
}
for (const command of ['npm test && git push', 'cd repo; git push', 'git push "$BRANCH"', 'git push --force', 'git push --force-with-lease', 'git push origin +HEAD:feat/x', 'git push --mirror', 'git -c push.default=matching push', 'gh pr merge --admin', 'gh pr create --unknown', '/usr/bin/git push', 'env git push', 'git push origin a b']) {
  test('rejects unsupported ' + command, () => expect(classifyCommand(command).kind).toBe('unsupported-publication'));
}
test('a quoted body preserves literal punctuation', () => {
  expect(classifyCommand('gh pr create --body "A; B"').argv).toEqual(['gh','pr','create','--body','A; B']);
});

for (const command of ['git \\'+ '\n' + 'push --force origin feat/x', 'g\\'+ '\n' + 'it push origin feat/x', 'gh pr \\'+ '\n' + 'merge 1 --admin', '"g\\'+ '\n' + 'it" push --force']) {
  test('shell continuations cannot hide publication ' + JSON.stringify(command), () => expect(classifyCommand(command).kind).toBe('unsupported-publication'));
}

const reportedCommand = 'gh auth status 2>&1 | head -3 && '
  + 'git push -u origin fix/ticket-system-config-recovery 2>&1 | tail -2 && '
  + 'gh pr view fix/ticket-system-config-recovery --repo AdamCaviness/agentic-toolkit --json number,state 2>&1';
test('the reported read-only chain extracts exactly the literal push', () => {
  const action = classifyCommand(reportedCommand);
  expect(action.kind).toBe('publish');
  expect(action.operation).toBe('push');
  expect(action.remote).toBe('origin');
  expect(action.branch).toBe('fix/ticket-system-config-recovery');
  expect(action.argv).toEqual(['git','push','-u','origin','fix/ticket-system-config-recovery']);
});

const wrappedCases: [string, string[]][] = [
  ['git push origin feat/x 2>&1', ['git','push','origin','feat/x']],
  ['2>&1 git push origin feat/x', ['git','push','origin','feat/x']],
  ['git push 2>&1 origin feat/x | tail -2', ['git','push','origin','feat/x']],
  ['git status --short --branch && git push origin feat/x 1>&2 | tail -n 2', ['git','push','origin','feat/x']],
  ['git push origin feat/x && gh pr view feat/x --repo=a/b --json=number,state', ['git','push','origin','feat/x']],
  ['gh pr create --body "A && B | C" 2>&1 | tail -2', ['gh','pr','create','--body','A && B | C']],
  ['gh pr merge 1 --squash 2>&1 | head -n 2', ['gh','pr','merge','1','--squash']],
  ['git push origin --delete feat/x | tail -2', ['git','push','origin','--delete','feat/x']],
  ['git -C "a b" push origin feat/x 2>& 1', ['git','-C','a b','push','origin','feat/x']],
];
for (const [command, argv] of wrappedCases) {
  test('extracts supported wrapper ' + command, () => {
    const action = classifyCommand(command);
    expect(['publish','delete'].includes(action.kind)).toBe(true);
    expect(action.argv).toEqual(argv);
  });
}

for (const command of [
  'git commit -am change && git push origin feat/x',
  'git status --help && git push origin feat/x',
  'git push origin feat/x && gh pr view --web',
  'gh auth login && git push origin feat/x',
  'git push origin feat/x && gh pr create --title title',
  'printf yes | gh pr merge 1 --squash',
  'gh auth status || git push origin feat/x',
  'git push origin feat/x &',
  'git push origin feat/x > output.txt',
  'git push origin feat/x 2>&1 > output.txt',
  'git push origin feat/x | tail -f',
  'git push origin feat/x | tail -2 file',
  'git push origin feat/x && gh pr view --repo=a/b --repo=c/d',
  'git push origin feat/x && gh pr view --json="number;state"',
  'git push origin feat/x && gh pr view --repo',
  'git push origin feat/x &&',
  'git push origin feat/x |',
  'git push origin feat/x 2>&1 && npm test',
  'git push --force origin feat/x 2>&1 | tail -2',
  'gh pr merge 1 --admin 2>&1 | tail -2',
  'FOO=bar git push origin feat/x 2>&1',
  'git push origin "$BRANCH" 2>&1',
  'git push origin feat/{a,b} 2>&1',
  'git push origin feat/x # comment',
  'git push origin feat/x 2>&1 && (git status)',
  'git push origin feat/x 2>&"',
]) {
  test('rejects unsupported publication context ' + command, () => {
    expect(classifyCommand(command).kind).toBe('unsupported-publication');
  });
}

test('quoted or escaped descriptor numbers remain branch arguments', () => {
  for (const command of ['git push origin "2" 1>&2', "git push origin ''2 1>&2", 'git push origin \\2 1>&2', 'git push origin 2 1>&2']) {
    expect(classifyCommand(command).argv).toEqual(['git','push','origin','2']);
    expect(classifyCommand(command).branch).toBe('2');
  }
});
test('a quoted operator in an argument does not introduce a pipeline', () => {
  expect(classifyCommand("gh pr create --body '2>&1 && git push --force' 2>&1").argv)
    .toEqual(['gh','pr','create','--body','2>&1 && git push --force']);
});

test('a leading cd names the repository a gh publication runs in', () => {
  const action = classifyCommand('cd /work/other && gh pr create --title t --body b');
  expect(action.kind).toBe('publish');
  expect(action.operation).toBe('create');
  expect(action.directory).toBe('/work/other');
  expect(action.argv).toEqual(['gh','pr','create','--title','t','--body','b']);
});
test('a leading cd names the repository a push runs in', () => {
  expect(classifyCommand('cd ../other && git push -u origin feat/x').directory).toBe('../other');
});
for (const command of [
  'cd a && cd b && git push origin feat/x',
  'cd a && git -C b push origin feat/x',
  'cd ~/x && git push origin feat/x',
  'cd a; git push origin feat/x',
  'cd a b && git push origin feat/x',
  'cd -P a && git push origin feat/x',
  'git push origin feat/x && cd a',
  'cd a | tail -2 && git push origin feat/x',
]) {
  test('rejects directory change ' + command, () => expect(classifyCommand(command).kind).toBe('unsupported-publication'));
}
