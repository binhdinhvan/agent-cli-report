// Runs only inside a fresh network/PID/filesystem namespace. No provider credentials.
import { OpenCode } from "/opt/research/client/promise/index.ts"
import { mkdirSync, readFileSync, watch } from "node:fs"
import { failureMatrix, matrixProvider } from "/opt/research/failure_matrix.ts"

const root = process.env.HOME!.replace(/\/home$/, "")
const result: any = { scope: "native TypeScript Client/private server with scripted SSE, not embedded SDK or model quality", checks: {}, events: [], requests: [], cycles: [] }
const marker = "REPORT_CLIENT_ASSISTANT_MARKER"
const seed = "REPORT_CLIENT_USER_SEED"
const received = new Map<string, any>()
const receivedAt = new Map<string, number>()
const listeners = new Map<string, (event: any) => void>()
function eventKey(event: any) { return event.type + ":" + (event.data?.id ?? "") }
function waitEvent(type: string, id: string) {
  const key = type + ":" + id
  if (received.has(key)) return Promise.resolve(received.get(key))
  return new Promise<any>((resolve, reject) => {
    const timeout = setTimeout(() => { listeners.delete(key); reject(new Error("event deadline " + key)) }, 10000)
    listeners.set(key, (event) => { clearTimeout(timeout); resolve(event) })
  })
}
const fixture = await Bun.file(root + "/response.sse").text()
const pluginFixture = await Bun.file(root + "/plugin-call.sse").text()
const pluginExecuteFixture = await Bun.file(root + "/plugin-execute.sse").text()
const backgroundFixture = await Bun.file(root + "/background-call.sse").text()
const compactionFixture = await Bun.file(root + "/compaction.sse").text()
const subagentCallFixture = await Bun.file(root + "/subagent-call.sse").text()
const subagentResponseFixture = await Bun.file(root + "/subagent-response.sse").text()
const mode = process.argv[3]
const matrix = matrixProvider(fixture)
let injectedPlugin = false
let injectedBackground = false
let injectedSubagent = false
let childRequestReady!: () => void
const childRequestStarted = new Promise<void>((resolve) => { childRequestReady = resolve })
let childRequests = 0
const budgetPending: Array<() => void> = []
const budgetRequests: Array<() => void> = []
function waitBudgetRequest(index: number) {
  if (budgetPending.length > index) return Promise.resolve()
  return new Promise<void>((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("budget recovery request deadline " + index)), 8000)
    budgetRequests[index] = () => { clearTimeout(timeout); resolve() }
  })
}
const provider = Bun.serve({
  hostname: "127.0.0.1", port: 8765,
  async fetch(request) {
    if (request.method !== "POST" || new URL(request.url).pathname !== "/v1/responses") return new Response("forbidden", { status: 403 })
    const payload: any = await request.json()
    result.requests.push(payload)
    if (result.requests.length > 12) return new Response("synthetic request cap", { status: 429 })
    if (mode === "failure-matrix") return matrix.response()
    if (mode === "budget-service-restart") {
      await new Promise<void>((resolve) => {
        budgetPending.push(resolve)
        budgetRequests[budgetPending.length - 1]?.()
      })
      return new Response(fixture, { headers: { "content-type": "text/event-stream" } })
    }
    if (mode.startsWith("subagent")) {
      if (String(payload.instructions).includes("Return the fixed research child marker; do not use tools.") && JSON.stringify(payload.input).includes("REPORT_SUBAGENT_CHILD_SEED")) {
        result.child_request_started_at = performance.now()
        childRequests++
        childRequestReady()
        await Bun.sleep(mode === "subagent-service-restart" && childRequests === 1 ? 4000 : 1000)
        result.child_response_at = performance.now()
        return new Response(subagentResponseFixture, { headers: { "content-type": "text/event-stream" } })
      }
      if (!injectedSubagent && payload.tools?.some((t: any) => t.name === "subagent")) {
        injectedSubagent = true
        return new Response(subagentCallFixture, { headers: { "content-type": "text/event-stream" } })
      }
    }
    if (mode.startsWith("background-") && !injectedBackground && payload.tools?.some((t: any) => t.name === "shell")) {
      injectedBackground = true
      return new Response(backgroundFixture, { headers: { "content-type": "text/event-stream" } })
    }
    if (mode === "compaction" && /You MUST summarize the conversation above|Update the existing checkpoint/.test(JSON.stringify(payload.input))) {
      result.compaction_fixture_used = true
      return new Response(compactionFixture, { headers: { "content-type": "text/event-stream" } })
    }
    if (!injectedPlugin && payload.tools?.some((t: any) => t.name === "report_marker")) {
      injectedPlugin = true
      return new Response(pluginFixture, { headers: { "content-type": "text/event-stream" } })
    }
    if (!injectedPlugin && payload.tools?.some((t: any) => t.name === "execute") && JSON.stringify(payload).includes("tools.report_marker()")) {
      injectedPlugin = true
      return new Response(pluginExecuteFixture, { headers: { "content-type": "text/event-stream" } })
    }
    return new Response(fixture, { headers: { "content-type": "text/event-stream" } })
  },
})
const password = crypto.randomUUID()
let child: ReturnType<typeof Bun.spawn> | undefined
let controller: AbortController | undefined
async function progress(stage: string, extra: object = {}) {
  if (mode.endsWith("service-restart")) await Bun.write(root + "/demo-progress.json", JSON.stringify({ stage, ...extra }))
}
async function start() {
  const service = mode.endsWith("service-restart")
  const stateDirectory = root + "/xdg-state/opencode"
  if (service) {
    mkdirSync(stateDirectory, { recursive: true })
    await Bun.write(root + "/xdg-config/opencode/service.json", JSON.stringify({ password }))
  }
  child = Bun.spawn([process.argv[2], "serve", service ? "--service" : "--stdio", "--hostname", "127.0.0.1", "--port", "0"], {
    stdin: "pipe", stdout: "pipe", stderr: Bun.file(root + "/client-server.log"),
    env: { ...process.env, OPENCODE_PASSWORD: password },
  })
  await progress("private_child_spawned", { pid: child.pid })
  const reader = (child.stdout as ReadableStream<Uint8Array>).getReader()
  let text = ""
  let url = ""
  if (service) {
    const ownedPID = child.pid
    url = await new Promise<string>((resolve, reject) => {
      const timer = setTimeout(() => { observer.close(); reject(new Error("private service readiness deadline")) }, 15000)
      const inspectRegistration = () => {
        try {
          const registration = JSON.parse(readFileSync(stateDirectory + "/service.json", "utf8"))
          if (registration.pid !== ownedPID) return
          if (typeof registration.url !== "string") throw new Error("private service registration URL missing")
          observer.close(); clearTimeout(timer); resolve(registration.url)
        } catch {}
      }
      const observer = watch(stateDirectory, inspectRegistration)
      inspectRegistration() // one immediate race check, not repeated polling
    })
  }
  await progress("private_endpoint_ready", { url })
  while (!url) {
    const chunk = await reader.read()
    if (chunk.done) throw new Error("private server ended before readiness")
    text += new TextDecoder().decode(chunk.value)
    for (const line of text.split("\n")) {
      try { const value = JSON.parse(line); if (value.url) url = value.url } catch {}
    }
  }
  const parsed = new URL(url)
  if (parsed.hostname !== "127.0.0.1") throw new Error("nonloopback server")
  void (async () => { while (!(await reader.read()).done) {} })().catch(() => {})
  result.cycles.push({ pid: child.pid, url })
  if (service) {
    result.service_health_attempts ??= []
    for (let attempt = 0; attempt < 15; attempt++) {
      const info = await fetch(url + "/api/info", {
        headers: { authorization: "Basic " + btoa("opencode:" + password) }, signal: AbortSignal.timeout(3000),
      })
      const health = { status: info.status, body: await info.text() }
      result.service_health_attempts.push(health)
      if (info.ok) break
      if (info.status !== 503) throw new Error("private service boot HTTP " + info.status)
      // Bounded service boot readiness, not agent/background-job status polling.
      await Bun.sleep(1000)
    }
    check("managed_service_authenticated_info", result.service_health_attempts.at(-1).status === 200)
  }
  return OpenCode.make({ baseUrl: url, headers: { authorization: "Basic " + btoa("opencode:" + password) } })
}
async function stop() {
  controller?.abort()
  if (!child) return
  const owned = child
  if (mode.endsWith("service-restart")) owned.kill("SIGTERM")
  else owned.stdin.end()
  const watchdog = setTimeout(() => owned.kill(), 8000)
  const exit = await owned.exited
  clearTimeout(watchdog)
  result.cycles.at(-1).exit = exit
  child = undefined
}
function check(name: string, condition: unknown) {
  result.checks[name] = Boolean(condition)
  if (!condition) throw new Error(name)
}
try {
  let client = await start()
  await progress("client_created")
  controller = new AbortController()
  let ready!: () => void
  let readinessFailed!: (error: unknown) => void
  const connected = new Promise<void>((resolve, reject) => { ready = resolve; readinessFailed = reject })
  const readinessDeadline = setTimeout(() => {
    controller?.abort()
    readinessFailed(new Error("native event readiness deadline after 8000ms"))
  }, 8000)
  const signal = controller.signal
  void (async () => {
    for await (const event of client.event.subscribe({ signal })) {
      result.events.push(event)
      if (JSON.stringify(event).includes(marker) && !result.parent_marker_received_at) result.parent_marker_received_at = performance.now()
      const key = eventKey(event)
      received.set(key, event)
      receivedAt.set(key, performance.now())
      if (listeners.has(key)) { listeners.get(key)!(event); listeners.delete(key) }
      if (event.type === "server.connected") ready()
      if (result.events.length > 1000) throw new Error("event cap")
    }
    if (!signal.aborted) throw new Error("event stream ended before cancellation")
  })().catch((error) => {
    result.event_error = String(error)
    readinessFailed(error)
  })
  await connected.finally(() => clearTimeout(readinessDeadline))
  await progress("event_stream_ready")
  check("subscribed_before_prompt", true)
  const created = await client.session.create({ title: "native-client-demo", location: { directory: process.cwd() } })
  result.sessionID = created.id
  result.plugin_list = await client.plugin.list({ location: { directory: process.cwd() } })
  const configEntries = await client.config.get({ location: { directory: process.cwd() } })
  result.config_plugins = configEntries.filter((e: any) => e.type === "document").map((e: any) => ({ path: e.path, plugins: e.info?.plugins }))
  if (result.config_plugins.some((e: any) => e.plugins?.length) && result.plugin_list.data.length === 0) {
    try { result.plugin_inventory_event = await waitEvent("plugin.updated", "") }
    catch (error) { result.plugin_inventory_wait_error = String(error) }
    result.plugin_list_after_wait = await client.plugin.list({ location: { directory: process.cwd() } })
  }
  if (mode === "permission-unmatched") {
    const effective = await client.agent.get({ agentID: "build", location: { directory: process.cwd() } })
    result.unmatched_effective_agent = effective
    check("test_action_has_no_configured_match", effective.data.permissions.every((rule: any) => rule.action !== "*" && rule.action !== "report_no_matching_rule"))
    const request = await client.permission.create({ sessionID: created.id, action: "report_no_matching_rule", resources: ["fixture"] })
    result.unmatched_request = request
    check("unmatched_fallback_ask", request.effect === "ask")
    await client.permission.reply({ sessionID: created.id, requestID: request.id, decision: "once" })
    const second = await client.permission.create({ sessionID: created.id, action: "report_no_matching_rule", resources: ["fixture"] })
    check("once_does_not_persist", second.effect === "ask")
    await client.permission.reply({ sessionID: created.id, requestID: second.id, decision: "reject" })
    check("unmatched_pending_settled", (await client.permission.list({ sessionID: created.id })).length === 0)
  } else if (mode === "failure-matrix") {
    result.failure_matrix = await failureMatrix(client, matrix)
    for (const [name, value] of Object.entries(result.failure_matrix.checks)) check(name, value)
    const unauthenticated = await fetch(result.cycles[0].url + "/api/session", { signal: AbortSignal.timeout(3000) })
    check("client_missing_auth_rejected", unauthenticated.status === 401)
  } else if (mode === "budget-service-restart") {
    await client.session.prompt({ sessionID: created.id, text: "REPORT_RESUME_BUDGET_FIXTURE; keep the scripted inference pending." })
    result.budget_crashes = []
    for (let index = 0; index < 11; index++) {
      await waitBudgetRequest(index)
      controller.abort()
      const owned = child!
      owned.kill(9)
      const exit = await owned.exited
      result.cycles.at(-1).exit = exit
      result.cycles.at(-1).stop = "SIGKILL_exact_private_child"
      child = undefined
      budgetPending[index]()
      result.budget_crashes.push({ index: index + 1, pid: owned.pid, exit })
      client = await start()
    }
    await client.experimental.session.wait({ sessionID: created.id })
    result.budget_context = await client.session.context({ sessionID: created.id })
    result.budget_session = await client.session.get({ sessionID: created.id })
    check("eleven_private_crashes_recorded", result.budget_crashes.length === 11)
    check("exhaustion_prevents_twelfth_model_request", result.requests.length === 11)
    check("native_resume_budget_failure", result.budget_context.some((entry: any) => entry.type === "idle" && entry.outcome === "failed" && entry.error?.message === "Execution was interrupted repeatedly and will not be resumed automatically."))
  } else if (mode === "permission") {
    result.permission_cases = []
    const action = "report_permission"
    for (const [name, effects] of Object.entries({ allow: ["allow"], deny: ["deny"], "overlap-allow": ["deny", "allow"], "overlap-deny": ["allow", "deny"] })) {
      await client.session.update({ sessionID: created.id, permissions: effects.map((effect) => ({ action, resource: "*", effect })) } as any)
      const evaluated = await client.permission.create({ sessionID: created.id, action, resources: ["fixture"] })
      result.permission_cases.push({ name, effects, evaluated })
      check("permission_" + name, evaluated.effect === effects.at(-1))
    }
    await client.session.update({ sessionID: created.id, permissions: [{ action, resource: "*", effect: "ask" }] })
    for (const decision of ["once", "reject", "always"] as const) {
      const request = await client.permission.create({ sessionID: created.id, action, resources: ["fixture"], save: ["fixture"] })
      check("permission_ask_" + decision, request.effect === "ask")
      const pending = await client.permission.list({ sessionID: created.id })
      check("permission_pending_" + decision, pending.some((p) => p.id === request.id))
      await client.permission.reply({ sessionID: created.id, requestID: request.id, decision })
      const after = await client.permission.list({ sessionID: created.id })
      check("permission_reply_" + decision, !after.some((p) => p.id === request.id))
      result.permission_cases.push({ name: "ask-" + decision, request, decision, pending_before: pending.length, pending_after: after.length })
    }
    const saved = await client.permission.create({ sessionID: created.id, action, resources: ["fixture"] })
    check("saved_approval_same_resource", saved.effect === "allow")
    const other = await client.permission.create({ sessionID: created.id, action, resources: ["different-fixture"] })
    check("saved_approval_not_other_resource", other.effect === "ask")
    await client.permission.reply({ sessionID: created.id, requestID: other.id, decision: "reject" })
    await client.session.update({ sessionID: created.id, permissions: [{ action, resource: "fixture", effect: "deny" }] })
    const denied = await client.permission.create({ sessionID: created.id, action, resources: ["fixture"] })
    check("configured_deny_beats_saved_allow", denied.effect === "deny")
    result.permission_saved_scope = { saved, other, denied }
  } else if (mode.startsWith("subagent")) {
    await client.session.prompt({ sessionID: created.id, text: "Launch one independent scripted child in the background and continue immediately." })
    await client.experimental.session.wait({ sessionID: created.id })
    result.subagent_parent_before = await client.session.context({ sessionID: created.id })
    const ids = [...new Set(JSON.stringify(result.subagent_parent_before).match(/ses_[A-Za-z0-9]+/g) ?? [])].filter((id) => id !== created.id)
    check("background_subagent_session_returned", ids.length === 1)
    result.child_sessionID = ids[0]
    const childInfo = await client.session.get({ sessionID: ids[0] })
    result.child_info = childInfo
    check("subagent_parent_lineage", childInfo.parentID === created.id)
    if (mode === "subagent-service-restart") {
      await childRequestStarted
      controller.abort()
      const owned = child!
      owned.kill(9)
      result.cycles.at(-1).exit = await owned.exited
      result.cycles.at(-1).stop = "SIGKILL_exact_private_child"
      child = undefined
      client = await start()
      check("subagent_private_service_pid_changed", result.cycles[0].pid !== result.cycles[1].pid)
      const restored = await client.session.get({ sessionID: ids[0] })
      result.child_info_restored = restored
      check("subagent_lineage_survives_restart", restored.parentID === created.id)
    }
    await client.experimental.session.wait({ sessionID: ids[0] })
    result.child_context = await client.session.context({ sessionID: ids[0] })
    check("child_marker_returned", JSON.stringify(result.child_context).includes("REPORT_SUBAGENT_CHILD_MARKER"))
    if (mode === "subagent") check("parent_continues_before_child_complete", result.parent_marker_received_at < result.child_response_at)
    else check("child_inference_requested_again_after_crash", childRequests >= 2)
    await client.experimental.session.wait({ sessionID: created.id })
    result.subagent_parent_after = await client.session.context({ sessionID: created.id })
    check("child_completion_delivered_to_parent", JSON.stringify(result.subagent_parent_after).includes("REPORT_SUBAGENT_CHILD_MARKER"))
  } else if (mode.startsWith("background-")) {
    await progress("admitting_background_prompt")
    await client.session.prompt({ sessionID: created.id, text: "Start the scripted bounded background worker, continue immediately and return the fixed marker." })
    await client.experimental.session.wait({ sessionID: created.id })
    result.background_context_before = await client.session.context({ sessionID: created.id })
    const started = await waitEvent("shell.created", "")
    await progress("background_tool_admitted")
    const job = started.data.info
    result.background_job = job
    check("native_background_tool_returned", JSON.stringify(result.background_context_before).includes("Command moved to the background"))
    check("parent_marker_before_wait", JSON.stringify(result.background_context_before).includes(marker))
    if (mode === "background-restart" || mode === "background-service-restart") {
      // Abruptly kill only the private test child, leaving running durable rows for recovery.
      controller.abort()
      const owned = child!
      owned.kill(9)
      result.cycles.at(-1).exit = await owned.exited
      result.cycles.at(-1).stop = "SIGKILL_exact_private_child"
      child = undefined
      await progress("private_child_crashed")
      client = await start()
      await progress("private_child_restarted")
      await client.session.prompt({ sessionID: created.id, text: "Continue after the private server restart." })
      await client.experimental.session.wait({ sessionID: created.id })
      result.background_context_after_restart = await client.session.context({ sessionID: created.id })
      check("background_private_server_pid_changed", result.cycles[0].pid !== result.cycles[1].pid)
      const serialized = JSON.stringify(result.background_context_after_restart)
      check("native_cancelled_notice_after_restart", serialized.includes(job.id) && /cancelled|canceled/i.test(serialized))
    } else {
      const terminal = await waitEvent("shell.exited", job.id)
      result.background_terminal = terminal
      result.background_output = await client.shell.output({ id: job.id })
      check("background_parent_continues_before_worker_end", result.parent_marker_received_at && result.parent_marker_received_at < receivedAt.get("shell.exited:" + job.id)!)
      check("native_worker_terminal", terminal.data.exit === (mode === "background-error" ? 7 : 0))
      await client.experimental.session.wait({ sessionID: created.id })
      result.background_context_after = await client.session.context({ sessionID: created.id })
    }
  } else if (mode === "compaction") {
    await client.session.prompt({ sessionID: created.id, text: seed + "; invariant=REPORT_RETAIN_ME" })
    await client.experimental.session.wait({ sessionID: created.id })
    result.compaction_before = await client.session.context({ sessionID: created.id })
    result.compaction_admission = await client.session.compact({ sessionID: created.id })
    await client.experimental.session.wait({ sessionID: created.id })
    result.compaction_after = await client.session.context({ sessionID: created.id })
    const before = result.requests.length
    await client.session.prompt({ sessionID: created.id, text: "Continue with the retained invariant." })
    await client.experimental.session.wait({ sessionID: created.id })
    check("native_compaction_requested_fixture_summary", result.compaction_fixture_used)
    check("post_compaction_input_uses_summary", result.requests.slice(before).some((p: any) => JSON.stringify(p.input).includes("REPORT_COMPACT_SUMMARY")))
  } else {
  await client.session.prompt({ sessionID: created.id, text: seed })
  await client.experimental.session.wait({ sessionID: created.id })
  const context = await client.session.context({ sessionID: created.id })
  result.context_before_restart = context
  check("assistant_marker", JSON.stringify(context).includes(marker))
  check("user_message", JSON.stringify(context).includes(seed))
  check("native_model_requests_observed", result.requests.length > 0)
  const inventory = result.plugin_list_after_wait?.data ?? result.plugin_list.data
  const ported = inventory.find((p: any) => p.id === "report.marker")
  if (ported) {
    check("ported_plugin_active", ported.state.status === "active")
    check("ported_plugin_tool_invoked", injectedPlugin && JSON.stringify(context).includes("REPORT_PLUGIN_MARKER"))
  }
  // These are native location-shell API cases, not agent-owned background job recovery.
  const worker = "python3 -u " + root + "/background_worker.py"
  const shellStarted = performance.now()
  const job = (await client.shell.create({ command: worker + " --steps 12", location: { directory: process.cwd() } })).data
  const returnedAt = performance.now()
  result.shell_start = job
  check("shell_start_returns_running", job.status === "running")
  const parentAt = performance.now()
  const exited = await waitEvent("shell.exited", job.id)
  const completedAt = performance.now()
  result.shell_success = { event: exited, return_ms: returnedAt - shellStarted, parent_ms: parentAt - shellStarted, complete_ms: completedAt - shellStarted,
    info: await client.shell.get({ id: job.id }), output: await client.shell.output({ id: job.id }) }
  check("parent_continues_before_shell_end", parentAt < completedAt && exited.data.exit === 0)
  const failed = (await client.shell.create({ command: worker + " --mode error --steps 2" })).data
  const failedEvent = await waitEvent("shell.exited", failed.id)
  result.shell_error = { event: failedEvent, output: await client.shell.output({ id: failed.id }) }
  check("shell_exit7_observed", failedEvent.data.exit === 7)
  const sibling = (await client.shell.create({ command: worker + " --steps 20" })).data
  const cancelled = (await client.shell.create({ command: worker + " --steps 30" })).data
  await client.shell.remove({ id: cancelled.id })
  const siblingEnd = await waitEvent("shell.exited", sibling.id)
  result.shell_cancel = { cancelledID: cancelled.id, siblingID: sibling.id, sibling: siblingEnd }
  check("cancel_does_not_kill_sibling", siblingEnd.data.exit === 0)
  // Disconnect only this client's event stream while a command continues in the private server.
  const disconnected = (await client.shell.create({ command: worker + " --steps 6" })).data
  controller.abort()
  const observer = OpenCode.make({ baseUrl: result.cycles.at(-1).url, headers: { authorization: "Basic " + btoa("opencode:" + password) } })
  controller = new AbortController()
  let reconnected!: () => void
  const observed = new Promise<void>((resolve) => { reconnected = resolve })
  const observerSignal = controller.signal
  void (async () => {
    for await (const event of observer.event.subscribe({ signal: observerSignal })) {
      result.events.push(event)
      if (event.type === "server.connected") reconnected()
      const key = eventKey(event); received.set(key, event)
      if (listeners.has(key)) { listeners.get(key)!(event); listeners.delete(key) }
    }
  })().catch((error) => { if (!observerSignal.aborted) result.observer_error = String(error) })
  await observed
  const afterDisconnect = await waitEvent("shell.exited", disconnected.id)
  result.shell_disconnect = { event: afterDisconnect, output: await observer.shell.output({ id: disconnected.id }) }
  check("shell_survives_client_disconnect", afterDisconnect.data.exit === 0)
  await stop()
  client = await start()
  check("private_server_pid_changed", result.cycles[0].pid !== result.cycles[1].pid)
  const persisted = await client.session.context({ sessionID: created.id })
  result.context_after_restart = persisted
  check("transcript_after_restart", JSON.stringify(persisted).includes(seed) && JSON.stringify(persisted).includes(marker))
  const before = result.requests.length
  await client.session.prompt({ sessionID: created.id, text: "Continue the existing session and return the fixed marker." })
  await client.experimental.session.wait({ sessionID: created.id })
  check("resume_request_contains_prior_context", result.requests.slice(before).some((r: any) => JSON.stringify(r.input).includes(seed) && JSON.stringify(r.input).includes(marker)))
  }
  result.status = "pass"
} catch (error) {
  result.status = "error"
  result.error = String(error)
} finally {
  await stop()
  provider.stop(true)
  const text = JSON.stringify(result, null, 2).replaceAll(password, "[PRIVATE-SERVER-PASSWORD]")
  await Bun.write(root + "/client-result.json", text)
  console.log(JSON.stringify({ status: result.status, checks: result.checks, error: result.error }))
}
