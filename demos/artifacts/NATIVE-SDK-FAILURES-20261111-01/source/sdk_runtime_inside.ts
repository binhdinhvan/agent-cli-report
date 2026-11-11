import { OpenCode } from "/opt/research/sdk/node_modules/@opencode/sdk/dist/index.js"
import { existsSync, readlinkSync } from "node:fs"
import { failureMatrix, matrixProvider } from "/opt/research/failure_matrix.ts"

const root = process.env.HOME!.replace(/\/home$/, "")
const result: any = { scope: "published embedded SDK2.2.5 with memory-scripted provider; no private service or real API", checks: {}, requests: [], events: [] }
const marker = "REPORT_SDK_ASSISTANT_MARKER"
const seed = "REPORT_SDK_USER_SEED"
const response = await Bun.file(root + "/sdk-response.sse").text()
const mode = process.argv[2]
const matrix = matrixProvider(response)
const provider = Bun.serve({ hostname: "127.0.0.1", port: 8765,
  async fetch(request) {
    if (request.method !== "POST" || new URL(request.url).pathname !== "/v1/responses") return new Response("forbidden", { status: 403 })
    result.requests.push(await request.json())
    if (result.requests.length > 12) return new Response("synthetic cap", { status: 429 })
    if (mode === "failure-matrix") return matrix.response()
    return new Response(response, { headers: { "content-type": "text/event-stream" } })
  },
})
let host: any
const controller = new AbortController()
function check(name: string, condition: unknown) {
  result.checks[name] = Boolean(condition)
  if (!condition) throw new Error(name)
}
try {
  check("real_home_hidden", !existsSync("/home/tts"))
  check("provider_key_absent", !process.env.OPENAI_API_KEY && !process.env.ANTHROPIC_API_KEY)
  result.net_namespace = readlinkSync("/proc/self/ns/net")
  host = await OpenCode.create()
  result.server_info = await host.server.info()
  result.host_pid = process.pid
  let ready!: () => void
  const connected = new Promise<void>((resolve) => { ready = resolve })
  void (async () => {
    for await (const event of host.events.subscribe({ signal: controller.signal })) {
      result.events.push(event)
      if (event.type === "server.connected") ready()
      if (result.events.length > 1000) throw new Error("event cap")
    }
  })().catch((error) => { if (!controller.signal.aborted) result.event_error = String(error) })
  let deadline: ReturnType<typeof setTimeout>
  await Promise.race([connected, new Promise<void>((_resolve, reject) => {
    deadline = setTimeout(() => reject(new Error("embedded event readiness deadline")), 5000)
  })]).finally(() => clearTimeout(deadline))
  result.event_subscribe_ready = result.events.some((e: any) => e.type === "server.connected")
  if (mode === "failure-matrix") {
    result.failure_matrix = await failureMatrix(host, matrix)
    for (const [name, value] of Object.entries(result.failure_matrix.checks)) check(name, value)
  } else {
  const session = await host.sessions.create({ title: "embedded-sdk-demo", location: { directory: process.cwd() } })
  result.sessionID = session.id
  await host.sessions.prompt({ sessionID: session.id, text: seed })
  await host.experimental.session.wait({ sessionID: session.id })
  result.context = await host.sessions.context({ sessionID: session.id })
  check("embedded_prompt_assistant_marker", JSON.stringify(result.context).includes(marker))
  check("embedded_prompt_user_seed", JSON.stringify(result.context).includes(seed))
  check("provider_request_observed", result.requests.length > 0)
  }
  controller.abort()
  await host.close(); host = undefined
  check("explicit_host_close_returned", true)
  result.status = "pass"
} catch (error) {
  result.status = "error"; result.error = String(error); result.stack = error instanceof Error ? error.stack : undefined
} finally {
  controller.abort()
  if (host) { try { await host.close() } catch {} }
  provider.stop(true)
  await Bun.write(root + "/sdk-result.json", JSON.stringify(result, null, 2))
  console.log(JSON.stringify({ status: result.status, checks: result.checks, error: result.error }))
}
