type Word = { text: string; operator: boolean; start: number; end: number; raw: string };

function tokenize(command: string): { words: Word[]; unsafe: boolean } {
  const words: Word[] = [];
  let text = '', quote = '', start = -1, unsafe = false;
  const flush = (end: number) => {
    if (start >= 0) words.push({ text, operator:false, start, end, raw:command.slice(start, end) });
    text = ''; start = -1;
  };
  for (let i = 0; i < command.length; i++) {
    const c = command[i]!;
    if (quote) {
      if (c === quote) { quote = ''; continue; }
      if (quote === '"' && (c === '$' || c === '`')) unsafe = true;
      if (quote === '"' && c === '\\' && /["\\$`\n]/.test(command[i + 1] ?? '')) {
        if (command[i + 1] === '\n') { unsafe = true; i++; continue; }
        text += command[++i]!; continue;
      }
      text += c; continue;
    }
    if (c === '"' || c === "'") {
      if (start < 0) start = i;
      quote = c; continue;
    }
    if (c === '\\') {
      if (command[i + 1] === '\n') { unsafe = true; i++; continue; }
      if (start < 0) start = i;
      if (i + 1 === command.length) unsafe = true;
      else text += command[++i]!;
      continue;
    }
    if (';&|<>\n()'.includes(c)) {
      flush(i);
      const operator = ['&>>','<<<','&&','||','|&','>>','<<','>&','<&','&>','>|']
        .find(value => command.startsWith(value, i)) ?? c;
      words.push({ text:operator, operator:true, start:i, end:i + operator.length, raw:operator });
      i += operator.length - 1; continue;
    }
    if (c === ' ' || c === '\t') { flush(i); continue; }
    if ('$`*?[]{}~'.includes(c) || c === '#' && start < 0 || /[\x00-\x1f\x7f]/.test(c)) unsafe = true;
    if (start < 0) start = i;
    text += c;
  }
  flush(command.length);
  return { words, unsafe:unsafe || !!quote };
}

export function parseShell(command: string) {
  const { words, unsafe } = tokenize(command);
  const pipelines: Word[][][] = [[[]]];
  const recognition: string[][] = [[]];
  let reason: string | undefined;
  let stage = pipelines[0]![0]!;
  const reject = (message: string) => { reason ??= message; };
  for (const word of words) {
    if (word.operator) recognition.push([]);
    else recognition[recognition.length - 1]!.push(word.text);
  }
  for (let i = 0; i < words.length; i++) {
    const word = words[i]!;
    if (!word.operator) { stage.push(word); continue; }
    if (/[<>]/.test(word.text)) {
      const previous = stage[stage.length - 1];
      const source = previous && previous.end === word.start && /^\d+$/.test(previous.raw)
        ? stage.pop()!.text : undefined;
      const target = words[i + 1];
      if (word.text !== '>&' || !source || target?.operator !== false
        || !((source === '2' && target.raw === '1') || (source === '1' && target.raw === '2'))) {
        reject('Use only 2>&1 or 1>&2 output duplication; separate publication from other redirections.');
      }
      if (target && !target.operator) i++;
      continue;
    }
    if (word.text === '|') {
      stage = []; pipelines[pipelines.length - 1]!.push(stage);
    } else {
      if (word.text !== '&&') reject('Separate publication from unsupported shell operators; only && and output-filter pipelines are supported.');
      stage = []; pipelines.push([stage]);
    }
  }
  if (pipelines.some(pipeline => pipeline.some(command => !command.length))) {
    reject('Publication requires complete commands on both sides of each supported operator.');
  }
  if (unsafe) reject('Use literal arguments for publication; expansions, comments, and unsupported shell syntax require separate commands.');
  return { pipelines:pipelines.map(pipeline => pipeline.map(stage => stage.map(word => word.text))), recognition, reason };
}

export function isOutputFilter(argv: string[]): boolean {
  if (!['head','tail'].includes(argv[0] ?? '')) return false;
  return argv.length === 2 && /^-\d+$/.test(argv[1]!)
    || argv.length === 3 && argv[1] === '-n' && /^\d+$/.test(argv[2]!);
}

export function isReadOnly(argv: string[]): boolean {
  if (argv[0] === 'git' && argv[1] === 'status') {
    return argv.slice(2).every(flag => ['--short','--branch','--porcelain','--porcelain=v1','--untracked-files=all'].includes(flag));
  }
  if (argv[0] === 'gh' && argv[1] === 'auth' && argv[2] === 'status') return argv.length === 3;
  if (argv[0] !== 'gh' || argv[1] !== 'pr' || argv[2] !== 'view') return false;
  let selector = false;
  const seen = new Set<string>();
  for (let i = 3; i < argv.length; i++) {
    const argument = argv[i]!;
    if (!argument.startsWith('-')) {
      if (selector) return false;
      selector = true; continue;
    }
    const [flag, ...rest] = argument.split('=');
    const key = flag === '-R' || flag === '--repo' ? 'repo' : flag === '--json' ? 'json' : undefined;
    if (!key || seen.has(key) || flag === '-R' && rest.length) return false;
    seen.add(key);
    const value = rest.length ? rest.join('=') : argv[++i];
    if (!value || value.startsWith('-')) return false;
    if (key === 'json' && !/^[A-Za-z][A-Za-z0-9]*(,[A-Za-z][A-Za-z0-9]*)*$/.test(value)) return false;
  }
  return true;
}
