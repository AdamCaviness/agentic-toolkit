export type Action = {
  kind: 'pass' | 'unsupported-publication' | 'publish' | 'delete';
  argv: string[];
  operation?: 'push' | 'create' | 'merge' | 'delete';
  directory?: string; remote?: string; branch?: string;
  repo?: string; head?: string; base?: string; selector?: string;
  explicitStrategy?: string; matchHead?: string;
};

type Word = { text: string; quoted: boolean; operator: boolean };

function tokenize(command: string): { words: Word[]; unsafe: boolean } {
  const words: Word[] = [];
  let text = '', quote = '', quoted = false, started = false, unsafe = false;
  const flush = () => {
    if (started) words.push({ text, quoted, operator: false });
    text = ''; quoted = false; started = false;
  };
  for (let i = 0; i < command.length; i++) {
    const c = command[i]!;
    if (quote) {
      if (c === quote) { quote = ''; continue; }
      if (quote === '"' && (c === '$' || c === '`')) unsafe = true;
      if (quote === '"' && c === '\\' && /[\"\\$`\n]/.test(command[i + 1] ?? '')) {
        text += command[++i]!; continue;
      }
      text += c; continue;
    }
    if (c === '"' || c === "'") { quote = c; quoted = true; started = true; continue; }
    if (c === '\\') {
      if (i + 1 === command.length || command[i + 1] === '\n') unsafe = true;
      else { started = true; text += command[++i]!; }
      continue;
    }
    if (';&|<>\n'.includes(c)) {
      flush(); words.push({ text: c, quoted: false, operator: true }); continue;
    }
    if (/\s/.test(c)) { flush(); continue; }
    if ('$`*?[]()'.includes(c)) unsafe = true;
    started = true; text += c;
  }
  flush();
  return { words, unsafe: unsafe || !!quote };
}

function isPublication(words: Word[]): boolean {
  const exe = words[0]?.text.split('/').pop();
  if (exe === 'git' || exe === 'gh') {
    const valued = exe === 'git' ? ['-C','-c','--git-dir','--work-tree','--namespace','--config-env'] : ['-R','--repo','--hostname'];
    let i = 1;
    while (words[i]?.text.startsWith('-')) {
      i += valued.includes(words[i]!.text) ? 2 : 1;
    }
    return exe === 'git' ? words[i]?.text === 'push'
      : words[i]?.text === 'pr' && ['create', 'merge'].includes(words[i + 1]?.text ?? '');
  }
  if (['env', 'sudo', 'command', 'exec'].includes(exe ?? '')) {
    const i = words.findIndex(w => ['git', 'gh'].includes(w.text.split('/').pop() ?? ''));
    return i > 0 && isPublication(words.slice(i));
  }
  return false;
}

export function classifyCommand(command: string): Action {
  const { words, unsafe } = tokenize(command);
  const argv = words.map(w => w.text);
  const pass: Action = { kind: 'pass', argv };
  const deny: Action = { kind: 'unsupported-publication', argv };
  const segments: Word[][] = [[]];
  for (const w of words) {
    if (w.operator) segments.push([]); else segments[segments.length - 1]!.push(w);
  }
  if (!segments.some(isPublication)) return pass;
  if (unsafe || words.some(w => w.operator)) return deny;
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
