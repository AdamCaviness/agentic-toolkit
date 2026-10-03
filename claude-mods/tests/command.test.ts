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
