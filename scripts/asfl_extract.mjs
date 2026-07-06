#!/usr/bin/env node
/**
 * Extract structured JSON from Agile-SOFL specifications for the research pipeline.
 * Usage: node scripts/asfl_extract.mjs <path.asfl> [--tasks]
 */
import { readFileSync } from 'node:fs'
import { check, printPredicate, printType, textOf, walk } from '../vendor/agile-sofl-toolchain/packages/parser/dist/index.js'

function paramGroups(groups) {
  return groups.flatMap((g) =>
    g.names.map((name) => ({
      name,
      type: printType(g.typeExpr)
    }))
  )
}

function extractModule(mod) {
  return {
    name: mod.name,
    isSystem: mod.isSystem,
    parent: mod.parent ? (mod.parent.module ? `${mod.parent.module}.${mod.parent.name}` : mod.parent.name) : null,
    constants: mod.consts.map((c) => ({
      name: c.name,
      value: c.value.type === 'number_literal' ? c.value.value : null
    })),
    types: mod.types.map((t) => ({ name: t.name, expr: printType(t.typeExpr) })),
    variables: mod.vars.map((v) => ({
      name: v.variable.name,
      kind: v.variable.kind,
      type: printType(v.typeExpr)
    })),
    invariants: mod.invariants.map((inv) => printPredicate(inv.condition)),
    processes: mod.processes
      .filter((p) => !p.alias)
      .map((p) => extractProcess(mod.name, p)),
    functions: mod.functions.map((f) => extractFunction(mod.name, f))
  }
}

function extractProcess(moduleName, p) {
  const inputs = paramGroups(p.inputs)
  const outputs = paramGroups(p.outputs)
  const body = p.body
  const fsf = body?.fsf
  // Treat readable/writable ext vars as implicit state interface
  const ext = body?.ext ?? []
  for (const e of ext) {
    const asParam = { name: e.name, type: e.typeExpr ? printType(e.typeExpr) : 'nat' }
    if (e.access === 'rd' && !inputs.find((x) => x.name === e.name)) {
      inputs.push(asParam)
    }
    if (e.access === 'wr' && !outputs.find((x) => x.name === e.name)) {
      outputs.push(asParam)
      if (!inputs.find((x) => x.name === e.name)) {
        inputs.push(asParam)
      }
    }
  }
  const scenarios = fsf
    ? [
        ...fsf.scenarios.map((s, i) => ({
          index: i + 1,
          kind: 'scenario',
          test: printPredicate(s.test),
          def: printPredicate(s.def)
        })),
        ...(fsf.others
          ? [{ index: fsf.scenarios.length + 1, kind: 'others', test: 'others', def: printPredicate(fsf.others) }]
          : [])
      ]
    : []

  if (!outputs.length && scenarios.length) {
    const outNames = new Set()
    for (const sc of scenarios) {
      for (const m of sc.def.matchAll(/(\w+)\s*(?:=|eq)\s*/g)) {
        outNames.add(m[1])
      }
    }
    for (const name of outNames) {
      if (!outputs.find((x) => x.name === name)) {
        outputs.push({ name, type: 'nat' })
      }
    }
  }

  if (!outputs.length && scenarios.length) {
    const outNames = new Set()
    for (const sc of scenarios) {
      for (const m of sc.def.matchAll(/(\w+)\s*(?:=|eq)\s*/g)) {
        outNames.add(m[1])
      }
    }
    for (const name of outNames) {
      if (!outputs.find((x) => x.name === name)) {
        outputs.push({ name, type: 'nat' })
      }
    }
  }

  return {
    id: `${moduleName}.${p.name}`,
    module: moduleName,
    name: p.name,
    isInit: p.isInit,
    inputs,
    outputs,
    ext: (body?.ext ?? []).map((e) => ({
      access: e.access,
      name: e.name,
      type: e.typeExpr ? printType(e.typeExpr) : null
    })),
    fsfScenarios: scenarios,
    decomposition: textOf(body?.decomposition) ?? null,
    comment: textOf(body?.comment) ?? null
  }
}

function extractFunction(moduleName, f) {
  const fsf = f.fsf
  const scenarios = fsf
    ? [
        ...fsf.scenarios.map((s, i) => ({
          index: i + 1,
          kind: 'scenario',
          test: printPredicate(s.test),
          def: printPredicate(s.def)
        })),
        ...(fsf.others
          ? [{ index: fsf.scenarios.length + 1, kind: 'others', test: 'others', def: printPredicate(fsf.others) }]
          : [])
      ]
    : []

  return {
    id: `${moduleName}.${f.name}`,
    module: moduleName,
    name: f.name,
    params: paramGroups(f.params),
    returnType: printType(f.returnType),
    body: f.body ? 'defined' : 'undefined',
    fsfScenarios: scenarios
  }
}

function buildTasks(modules, sourcePath) {
  const tasks = []
  for (const mod of modules) {
    for (const proc of mod.processes) {
      if (!proc.fsfScenarios.length) continue
      tasks.push({
        taskId: proc.id,
        kind: 'process',
        sourceFile: sourcePath,
        module: proc.module,
        name: proc.name,
        signature: {
          inputs: proc.inputs,
          outputs: proc.outputs
        },
        fsfScenarios: proc.fsfScenarios,
        ext: proc.ext,
        promptSpec: formatPromptSpec(proc)
      })
    }
    for (const fn of mod.functions) {
      if (!fn.fsfScenarios.length && fn.body === 'undefined') continue
      tasks.push({
        taskId: fn.id,
        kind: 'function',
        sourceFile: sourcePath,
        module: fn.module,
        name: fn.name,
        signature: {
          params: fn.params,
          returnType: fn.returnType
        },
        fsfScenarios: fn.fsfScenarios,
        promptSpec: formatFunctionPrompt(fn)
      })
    }
  }
  return tasks
}

function formatPromptSpec(proc) {
  const inParams = proc.inputs.map((p) => `${p.name}: ${p.type}`).join(', ')
  const outParams = proc.outputs.map((p) => `${p.name}: ${p.type}`).join(', ')
  const fsfLines = proc.fsfScenarios
    .map((s) => (s.kind === 'others' ? `others => ${s.def}` : `if (${s.test}) => ${s.def}`))
    .join('\n')
  const extLines = proc.ext.map((e) => `${e.access} ${e.name}`).join('\n')
  return [
    `Process ${proc.name}(${inParams}) -> (${outParams})`,
    extLines ? `External variables:\n${extLines}` : '',
    `FSF specification:\n${fsfLines}`,
    proc.comment ? `Informal: ${proc.comment}` : ''
  ]
    .filter(Boolean)
    .join('\n\n')
}

function formatFunctionPrompt(fn) {
  const params = fn.params.map((p) => `${p.name}: ${p.type}`).join(', ')
  const fsfLines = fn.fsfScenarios
    .map((s) => (s.kind === 'others' ? `others => ${s.def}` : `if (${s.test}) => ${s.def}`))
    .join('\n')
  return [`Function ${fn.name}(${params}) -> ${fn.returnType}`, fsfLines ? `FSF:\n${fsfLines}` : ''].filter(Boolean).join('\n\n')
}

const args = process.argv.slice(2)
const tasksFlag = args.includes('--tasks')
const file = args.find((a) => !a.startsWith('--'))

if (!file) {
  console.error('Usage: node scripts/asfl_extract.mjs <file.asfl> [--tasks]')
  process.exit(1)
}

const source = readFileSync(file, 'utf8')
const { ast, diagnostics } = check(source)

if (!ast) {
  console.log(JSON.stringify({ ok: false, diagnostics, modules: [], tasks: [] }, null, 2))
  process.exit(1)
}

const modules = ast.modules.map(extractModule)
const payload = {
  ok: true,
  file,
  diagnostics: diagnostics.map((d) => ({
    severity: d.severity,
    code: d.code,
    message: d.message
  })),
  modules,
  ...(tasksFlag ? { tasks: buildTasks(modules, file) } : {})
}

console.log(JSON.stringify(payload, null, 2))
