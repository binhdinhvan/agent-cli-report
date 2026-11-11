// Runs only inside a fresh network/PID/filesystem namespace. No provider credentials.
import { OpenCode } from "/opt/research/client/promise/index.ts"

const root = process.env.HOME!.replace(/\/home$/, "")
const result: any = { scope: "native TypeScript Client/private server with scripted SSE, not embedded SDK or model quality", checks: {}, events: [], requests: [], cycles: [] }
const marker = "REPORT_CLIENT_ASSISTANT_MARKER"
const seed = "REPORT_CLIENT_USER_SEED"
const fixture = await Bun.file(root + "/response.sse").text()
const provider = Bun.serve({
  hostname: "127.0.0.1", port: 8765,
  async fetch(request) {
    if (request.method !== "POST" || new URL(request.url).pathname !== "/v1/responses") return new Response("forbidden", { status: 403 })
    result.requests.push(await request.json())
    if (result.requests.length > 12) return new Response("synthetic request cap", { status: 429 })
    return new Response(fixture, { headers: { "content-type": "text/event-stream" } })
  },
})
const password = crypto.randomUUID()
let child: ReturnType<typeof Bun.spawn> | undefined
let controller: AbortController | undefined
async function start() {
  child = Bun.spawn([process.argv[2], "serve", "--stdio", "--hostname", "127.0.0.1", "--port", "0"], {
    stdin: "pipe", stdout: "pipe", stderr: Bun.file(root + "/client-server.log"),
    env: { ...process.env, OPENCODE_PASSWORD: password },
  })
  const reader = (child.stdout as ReadableStream<Uint8Array>).getReader()
  let text = ""
  let url = ""
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
  return OpenCode.make({ baseUrl: url, headers: { authorization: "Basic " + btoa("opencode:" + password) } })
}
async function stop() {
  controller?.abort()
  if (!child) return
  const owned = child
  owned.stdin.end()
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
  controller = new AbortController()
  let ready!: () => void
  const connected = new Promise<void>((resolve) => { ready = resolve })
  const signal = controller.signal
  void (async () => {
    for await (const event of client.event.subscribe({ signal })) {
      result.events.push(event)
      if (event.type === "server.connected") ready()
      if (result.events.length > 1000) throw new Error("event cap")
    }
  })().catch((error) => { if (!signal.aborted) result.event_error = String(error) })
  await connected
  check("subscribed_before_prompt", true)
  const created = await client.session.create({ title: "native-client-demo", location: { directory: process.cwd() } })
  result.sessionID = created.id
  result.plugin_list = await client.plugin.list({ location: { directory: process.cwd() } })
  await client.session.prompt({ sessionID: created.id, text: seed })
  await client.session.wait({ sessionID: created.id })
  const context = await client.session.context({ sessionID: created.id })
  result.context_before_restart = context
  check("assistant_marker", JSON.stringify(context).includes(marker))
  check("user_message", JSON.stringify(context).includes(seed))
  check("native_model_requests_observed", result.requests.length > 0)
  await stop()
  client = await start()
  check("private_server_pid_changed", result.cycles[0].pid !== result.cycles[1].pid)
  const persisted = await client.session.context({ sessionID: created.id })
  result.context_after_restart = persisted
  check("transcript_after_restart", JSON.stringify(persisted).includes(seed) && JSON.stringify(persisted).includes(marker))
  const before = result.requests.length
  await client.session.prompt({ sessionID: created.id, text: "Continue the existing session and return the fixed marker." })
  await client.session.wait({ sessionID: created.id })
  check("resume_request_contains_prior_context", result.requests.slice(before).some((r: any) => JSON.stringify(r.input).includes(seed) && JSON.stringify(r.input).includes(marker)))
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
