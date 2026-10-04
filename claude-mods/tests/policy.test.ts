import { expect, test } from 'claude-code/testing';
import { parseChecks, screenPaths, githubRepository, evaluatePublication, sameSnapshot } from '../policy.ts';
import type { Snapshot, PullRequest } from '../policy.ts';

const clean: Snapshot = { repository: '/repo', branch: 'feat/x', head: 'abc', baseBranch: 'trunk', baseRef: 'origin/trunk', baseCommit: 'base', origin: 'https://github.com/a/b.git', clean: true, commitsAhead: 1, paths: ['src/x.ts'], remoteHead: 'abc' };
const pr: PullRequest = { state:'OPEN', isDraft:false, isCrossRepository:false, baseRefName:'trunk', headRefName:'feat/x', headRefOid:'abc', mergeStateStatus:'CLEAN', reviewDecision:'APPROVED', url:'https://github.com/a/b/pull/1' };
test('ordinary publication passes', () => expect(evaluatePublication(clean, {kind:'publish',argv:[],operation:'push'}).kind).toBe('pass'));
for (const change of [{branch:'trunk'}, {branch:''}, {clean:false}, {baseCommit:''}, {commitsAhead:0}]) {
  test('rejects snapshot ' + JSON.stringify(change), () => expect(evaluatePublication({...clean,...change}, {kind:'publish',argv:[],operation:'push'}).kind).toBe('deny'));
}
for (const command of [{remote:'upstream'}, {branch:'trunk'}, {head:'other'}, {base:'production'}, {repo:'elsewhere/repo'}]) {
  test('rejects destination ' + JSON.stringify(command), () => expect(evaluatePublication(clean, {kind:'publish',argv:[],operation:'create',...command}).kind).toBe('deny'));
}
test('paths need confirmation', () => expect(evaluatePublication({...clean,paths:['.env']}, {kind:'publish',argv:[],operation:'push'}).kind).toBe('confirm-paths'));
test('merge uses PR evidence rather than ahead count', () => expect(evaluatePublication({...clean,commitsAhead:0}, {kind:'publish',argv:[],operation:'merge',explicitStrategy:'squash'}, pr).kind).toBe('pass'));
for (const change of [{state:'CLOSED'}, {isDraft:true}, {headRefOid:'old'}, {mergeStateStatus:'BLOCKED'}, {reviewDecision:'REVIEW_REQUIRED'}, {url:'https://github.com/other/repo/pull/1'}, {isCrossRepository:true}, {baseRefName:'production'}]) {
  test('rejects PR ' + JSON.stringify(change), () => expect(evaluatePublication(clean, {kind:'publish',argv:[],operation:'merge',explicitStrategy:'squash'}, {...pr,...change}).kind).toBe('deny'));
}
test('merged feature cleanup works from default checkout', () => expect(evaluatePublication({...clean,branch:'trunk'}, {kind:'delete',argv:[],operation:'delete',remote:'origin',branch:'feat/x'}, {...pr,state:'MERGED'}).kind).toBe('pass'));
test('missing remote branch cannot be deleted', () => expect(evaluatePublication({...clean,remoteHead:undefined}, {kind:'delete',argv:[],operation:'delete',branch:'feat/x'}).kind).toBe('deny'));
test('remote branch reuse during checks changes the snapshot', () => expect(sameSnapshot(clean, {...clean,remoteHead:'new'})).toBe(false));
test('never deletes default branch', () => expect(evaluatePublication(clean, {kind:'delete',argv:[],operation:'delete',branch:'trunk'}, {...pr,state:'MERGED'}).kind).toBe('deny'));
test('state change invalidates confirmation', () => expect(sameSnapshot(clean, {...clean,head:'new'})).toBe(false));
test('JSON argv commands do not undergo shell expansion', () => expect(parseChecks('[["npm","test"],["echo","$HOME"]]')).toEqual([['npm','test'],['echo','$HOME']]));
for (const value of ['{}','[[]]','[[1]]','[[" "]]','[["x\\n"]]']) test('invalid checks ' + value, () => expect(() => parseChecks(value)).toThrow());
test('empty checks remain empty', () => expect(parseChecks('[]')).toEqual([]));
test('SSH and HTTPS identities agree', () => expect(githubRepository('git@github.com:A/B.git')).toBe(githubRepository('https://github.com/a/b')));
test('credential URLs are rejected', () => expect(() => githubRepository('https://token@github.com/a/b.git')).toThrow());
test('decorated data paths are screened and source paths are not', () => expect(screenPaths(['client_secrets_v2.json','id_rsa2','data.db-shm','src/secrets.ts'])).toEqual(['client_secrets_v2.json','id_rsa2','data.db-shm']));
