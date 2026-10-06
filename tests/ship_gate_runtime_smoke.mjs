import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = dirname(dirname(fileURLToPath(import.meta.url)));

// agentic-toolkit declares prompt-marks as a dependency; a stub with only its
// manifest satisfies it, so this test stays offline and about Ship Gate alone.
function stubDependency(dir) {
  mkdirSync(join(dir, '.claude-plugin'), { recursive:true });
  writeFileSync(join(dir, '.claude-plugin', 'plugin.json'), JSON.stringify({ name:'prompt-marks', version:'0.0.0' }));
  return dir;
}

for (const disableAllHooks of [false, true]) {
  test(disableAllHooks ? 'Claude native hook disabling is respected'
    : 'Claude loads Ship Gate automatically without a custom command or model call', t => {
    const config = mkdtempSync(join(tmpdir(), 'ship-gate-runtime-'));
    t.after(() => rmSync(config, { recursive:true, force:true }));
    const dependency = stubDependency(join(config, 'prompt-marks'));
    const result = spawnSync('claude', ['-p','/cost','--plugin-dir',dependency,'--plugin-dir',root,
      '--setting-sources','','--settings',JSON.stringify({disableAllHooks}),'--no-session-persistence','--output-format','stream-json','--verbose'], {
      cwd:root, env:{...process.env, CLAUDE_CONFIG_DIR:config}, encoding:'utf8', timeout:30000,
    });
    assert.equal(result.error, undefined, result.error?.message);
    assert.equal(result.status, 0, result.stderr);
    const events = result.stdout.trim().split('\n').map(line => JSON.parse(line));
    const notices = events.filter(e => e.type === 'system' && e.subtype === 'ui_log' && e.plugin === 'agentic-toolkit');
    assert.deepEqual(notices.map(e => e.text), disableAllHooks ? [] : ['Ship Gate active: verification not configured.']);
    const init = events.find(e => e.type === 'system' && e.subtype === 'init');
    assert.ok(init?.plugins.some(p => p.name === 'agentic-toolkit'));
    assert.equal(init.slash_commands.some(c => c === 'ship-gate' || c.endsWith(':ship-gate')), false);
    const finished = events.find(e => e.type === 'result');
    assert.ok(finished);
    assert.equal(finished.is_error, false);
    assert.equal(finished.num_turns, 0);
    assert.equal(finished.duration_api_ms, 0);
    assert.deepEqual(finished.modelUsage, {});
  });
}
