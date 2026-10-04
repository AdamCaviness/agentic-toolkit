import { parseShell, isReadOnly, isOutputFilter } from './shell.ts';

export type Action = {
  kind: 'pass' | 'unsupported-publication' | 'publish' | 'delete';
  argv: string[];
  operation?: 'push' | 'create' | 'merge' | 'delete';
  directory?: string; remote?: string; branch?: string;
  repo?: string; head?: string; base?: string; selector?: string;
  explicitStrategy?: string; matchHead?: string; reason?: string;
};

function isPublication(words: string[]): boolean {
  let assignmentCount = 0;
  while (/^[A-Za-z_][A-Za-z0-9_]*=/.test(words[assignmentCount] ?? '')) assignmentCount++;
  if (assignmentCount) return isPublication(words.slice(assignmentCount));
  const exe = words[0]?.split('/').pop();
  if (exe === 'git' || exe === 'gh') {
    const valued = exe === 'git' ? ['-C','-c','--git-dir','--work-tree','--namespace','--config-env'] : ['-R','--repo','--hostname'];
    let i = 1;
    while (words[i]?.startsWith('-')) {
      i += valued.includes(words[i]!) ? 2 : 1;
    }
    return exe === 'git' ? words[i] === 'push'
      : words[i] === 'pr' && ['create', 'merge'].includes(words[i + 1] ?? '');
  }
  if (['env', 'sudo', 'command', 'exec'].includes(exe ?? '')) {
    const i = words.findIndex(w => ['git', 'gh'].includes(w.split('/').pop() ?? ''));
    return i > 0 && isPublication(words.slice(i));
  }
  return false;
}

export function classifyCommand(command: string): Action {
  const shell = parseShell(command);
  const stages = shell.pipelines.flat();
  const candidates = stages.filter(isPublication);
  const argv = stages.flat();
  const deny = (reason: string): Action => ({kind:'unsupported-publication',argv,reason});
  if (!candidates.length && !shell.recognition.some(isPublication)) return {kind:'pass',argv};
  if (shell.reason) return deny(shell.reason);
  if (candidates.length !== 1) return deny('Run each publication operation separately so it receives fresh repository and host checks.');
  const publication = candidates[0]!;
  for (const pipeline of shell.pipelines) {
    if (pipeline.slice(1).some(isPublication)) return deny('Run publication at the start of its pipeline without commands feeding its input.');
    if (pipeline[0] !== publication && !isReadOnly(pipeline[0]!)) return deny('Separate publication from neighboring commands whose effects cannot be verified.');
    if (!pipeline.slice(1).every(isOutputFilter)) return deny('Publication pipelines support only head/tail filters with a literal line count and no files or other flags.');
  }
  return classifyPublication(publication);
}

function classifyPublication(argv: string[]): Action {
  const pass: Action = {kind:'pass',argv};
  const deny: Action = {kind:'unsupported-publication',argv,reason:'Use a direct publication command with supported literal arguments, no force/admin options or unsupported flags.'};
  let i = 1;
  const action: Action = { kind: 'publish', argv };
  if (argv[0] === 'git') {
    if (argv[i] === '-C') { action.directory = argv[i + 1]; i += 2; }
    if (argv[i++] !== 'push') return deny;
    let deletion = false;
    const positional: string[] = [];
    for (; i < argv.length; i++) {
      const arg = argv[i]!;
      if (arg === '-u' || arg === '--set-upstream') continue;
      if (arg === '--delete' || arg === '-d') { deletion = true; continue; }
      if (arg === '--dry-run' || arg === '-n') {
        return argv.slice(i + 1).some(a => a.startsWith('-') && !['--porcelain','--verbose'].includes(a)) ? deny : pass;
      }
      if (arg.startsWith('-') || /[+:]/.test(arg)) return deny;
      positional.push(arg);
    }
    if (positional.length > 2 || (deletion && positional.length !== 2)) return deny;
    action.operation = deletion ? 'delete' : 'push';
    action.kind = deletion ? 'delete' : 'publish';
    [action.remote, action.branch] = positional;
    return action;
  }
  if (argv[0] !== 'gh' || argv[1] !== 'pr' || !['create', 'merge'].includes(argv[2] ?? '')) return deny;
  action.operation = argv[2] as 'create' | 'merge';
  const valued = action.operation === 'create'
    ? ['--title','-t','--body','-b','--body-file','-F','--base','-B','--head','-H','--repo','-R','--assignee','-a','--reviewer','-r','--label','-l','--milestone','-m','--project','-p','--template','-T']
    : ['--repo','-R','--match-head-commit'];
  const plain = action.operation === 'create'
    ? ['--draft','-d','--fill','-f','--fill-first','--fill-verbose']
    : ['--merge','-m','--squash','-s','--rebase','-r','--delete-branch','-d'];
  const seen = new Set<string>();
  for (i = 3; i < argv.length; i++) {
    const [flag, ...rest] = argv[i]!.split('=');
    if (plain.includes(flag!) && !rest.length) {
      const strategy = ({ '--merge':'merge', '-m':'merge', '--squash':'squash', '-s':'squash', '--rebase':'rebase', '-r':'rebase' } as Record<string,string>)[flag!];
      if (strategy) { if (action.explicitStrategy) return deny; action.explicitStrategy = strategy; }
      continue;
    }
    if (valued.includes(flag!)) {
      const value = rest.length ? rest.join('=') : argv[++i];
      if (value === undefined || !value.length || value.startsWith('-')) return deny;
      const key = ({ '--repo':'repo','-R':'repo','--head':'head','-H':'head','--base':'base','-B':'base','--match-head-commit':'matchHead' } as Record<string,string>)[flag!];
      if (key) {
        if (seen.has(key)) return deny;
        seen.add(key); (action as unknown as Record<string,unknown>)[key] = value;
      }
      continue;
    }
    if (action.operation === 'merge' && !argv[i]!.startsWith('-') && !action.selector) { action.selector = argv[i]; continue; }
    return deny;
  }
  return action;
}
