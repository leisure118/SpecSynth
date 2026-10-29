const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { compile } = require('@vue/compiler-dom');
const root = path.resolve(__dirname, '../apps/web/src');
for (const file of ['App.js','views/HomeView.js','views/ProjectsView.js','views/WorkspaceView.js','views/RustWorkspaceView.js','views/CWorkspaceView.js','components/VerusEditor.js','components/CodeCompare.js','components/ExampleCatalog.js','components/AgentConfig.js','views/DatasetView.js','views/SkillsView.js','views/BenchmarkView.js','views/SpectoolView.js']) {
  const source = fs.readFileSync(path.join(root, file), 'utf8');
  const start = source.indexOf('template:') + 'template:'.length;
  const template = Function('return ' + source.slice(start, source.lastIndexOf('`') + 1))();
  // Evaluate JS escapes before compiling, exactly as a browser importing this component does.
  const render = compile(template, { mode: 'function' });
  assert.doesNotThrow(() => new Function('Vue', render.code), file);
}
(async () => {
  const source = fs.readFileSync(path.join(root, 'workspaceState.js'), 'utf8');
  const { matchingRuns, isRunning } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
  const runs = [{task_id:'a',entry_path:'src/main.c',mode:'single'}, {task_id:'b',entry_path:'lib/main.c',mode:'single'}, {task_id:'project',entry_path:'src/main.c',mode:'inter-modular'}, {task_id:'termination',entry_path:'src/main.c',mode:'termination'}, {task_id:'retry',entry_path:'src/main.c',mode:'single'}];
  assert.deepEqual(matchingRuns(runs,'src/main.c','single').map(r=>r.task_id), ['retry','a']);
  assert.deepEqual(matchingRuns(runs,'lib/main.c','single').map(r=>r.task_id), ['b']);
  assert.deepEqual(matchingRuns(runs,'src/main.c','termination').map(r=>r.task_id), ['termination']);
  assert.deepEqual(matchingRuns(runs,'lib/main.c','inter-modular').map(r=>r.task_id), ['project']);
  assert.deepEqual(matchingRuns(runs,'new.c','single'), []);
  assert.equal(isRunning('running'), true);
  assert.equal(isRunning('pass'), false);
  console.log('Runtime templates and per-file task isolation passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
