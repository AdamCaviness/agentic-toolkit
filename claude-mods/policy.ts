import type { Action } from './command.ts';
export type Snapshot = {
  repository: string; branch: string; head: string; baseBranch: string;
  baseRef: string; baseCommit: string; origin: string; clean: boolean;
  commitsAhead: number; paths: string[]; remoteHead?: string;
};
export type PullRequest = {
  state: string; isDraft: boolean; baseRefName: string; headRefName: string;
  headRefOid: string; mergeStateStatus: string; reviewDecision: string;
  url: string; isCrossRepository: boolean;
};
export type Decision = { kind: 'pass' } | { kind: 'deny'; reason: string } | { kind: 'confirm-paths'; paths: string[] };
export const HIGH_RISK_SCREEN = String.raw`(^|/)(\.env|\.npmrc|\.pypirc)(\.|/|$)|(^|/)id_(rsa|dsa|ecdsa|ed25519)([-_. 0-9][^/]*)?(\.|/|$)|(^|/)([^/]*[-_. ])?(credentials?|secrets?)([-_ ][^/.]*)?(/|$|\.(json|ya?ml|env|txt|ini|cfg|conf|toml|properties|xml|csv|tsv|pem|key|p12|enc)$)|\.(pem|p12|pfx|key|crt|sqlite3?|db3?|dump|env)(-(wal|shm|journal))?$`;

export function parseChecks(value: unknown): string[][] {
  if (typeof value !== 'string') throw new Error('Verification commands must be JSON argv arrays.');
  const result: unknown = JSON.parse(value);
  if (!Array.isArray(result) || result.length > 8 || result.some(command =>
    !Array.isArray(command) || !command.length || command.length > 64 || command.some(arg =>
      typeof arg !== 'string' || !arg.trim() || /[\x00-\x1f\x7f]/.test(arg)))) {
    throw new Error('Use up to eight nonempty argv arrays without control characters.');
  }
  return result as string[][];
}
export function screenPaths(paths: string[]): string[] {
  const screen = new RegExp(HIGH_RISK_SCREEN, 'i');
  return paths.filter(path => screen.test(path));
}
export function githubRepository(url: string): string {
  const match = /^(?:https:\/\/|ssh:\/\/git@|git@)([^/:@]+)(?:\/|:)([\w.-]+)\/([\w.-]+?)(?:\.git)?\/?$/.exec(url);
  if (!match) throw new Error('Origin must have an unambiguous HTTPS or SSH repository URL.');
  return [match[1]!.toLowerCase(), match[2]!.toLowerCase(), match[3]!.toLowerCase()].join('/');
}
export function prRepository(url: string): string {
  const match = /^https:\/\/([^/]+)\/([^/]+)\/([^/]+)\/pull\/[0-9]+$/.exec(url);
  if (!match) throw new Error('The selected pull request has an invalid URL.');
  return match.slice(1).join('/').toLowerCase();
}
export function sameSnapshot(a: Snapshot, b: Snapshot): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}
export function evaluatePublication(s: Snapshot, a: Action, pr?: PullRequest): Decision {
  const deny = (reason: string): Decision => ({ kind: 'deny', reason });
  if (!s.repository || !s.head || !s.baseCommit || !s.baseBranch) return deny('Repository or default branch could not be verified.');
  if (a.remote && a.remote !== 'origin') return deny('Use origin as the publication destination.');
  if (a.operation === 'delete') {
    if (!a.branch || a.branch === s.baseBranch) return deny('The default branch cannot be deleted.');
    if (!s.remoteHead) return deny('Cleanup requires an existing remote feature branch.');
    return { kind: 'pass' };
  }
  if (!s.branch || s.branch === s.baseBranch) return deny('Ship Gate publishes feature branches, and ' + (s.branch || 'a detached HEAD') + ' is not one. Create a feature branch for these commits first.');
  if (!s.clean) return deny('Commit or exclude remaining staged, unstaged, and untracked changes first.');
  if (a.branch && a.branch === s.baseBranch) return deny('Ship Gate never pushes the default branch ' + s.baseBranch + '. Push it yourself if that is intended.');
  if (a.branch && a.branch !== s.branch) return deny('Only the checked-out branch ' + s.branch + ' can be pushed; this command names ' + a.branch + '. Check out ' + a.branch + ' first, or push ' + s.branch + '.');
  if (a.head && a.head !== s.branch) return deny('The PR head must be the current branch.');
  if (a.base && a.base !== s.baseBranch) return deny('The PR base must be the default branch.');
  if (a.operation !== 'merge' && s.commitsAhead === 0) return deny('There are no feature commits to publish.');
  const github = a.operation === 'create' || a.operation === 'merge' ? githubRepository(s.origin) : undefined;
  if (a.repo && a.repo.toLowerCase() !== github && a.repo.toLowerCase() !== github?.split('/').slice(1).join('/')) return deny('The PR must target origin.');
  if ((a.operation === 'create' || a.operation === 'merge') && s.remoteHead !== s.head) return deny('Push the current HEAD to origin before continuing.');
  if (a.operation === 'merge') {
    if (!pr || pr.state !== 'OPEN' || pr.isDraft !== false || pr.isCrossRepository !== false || pr.baseRefName !== s.baseBranch || pr.headRefName !== s.branch || pr.headRefOid !== s.head || prRepository(pr.url) !== github) return deny('The selected PR does not match this feature branch and origin.');
    if (pr.mergeStateStatus !== 'CLEAN' || !['', 'APPROVED'].includes(pr.reviewDecision ?? 'unknown')) return deny('Required checks and review must permit merging.');
    if (a.matchHead && a.matchHead !== s.head) return deny('The requested merge head does not match local HEAD.');
    if (!a.explicitStrategy) return deny('Specify one allowed merge strategy.');
  }
  const paths = screenPaths(s.paths);
  return paths.length ? { kind: 'confirm-paths', paths } : { kind: 'pass' };
}
