// Native v1 HTTP runtime, isolated by v1_runtime.py; no real provider/key.
import { existsSync } from "node:fs"
const root = process.env.HOME!.replace(/\/home$/, "")
const mode = process.argv[3]
const password = crypto.randomUUID()
const authorization = "Basic " + btoa("opencode:" + password)
const result: any = { mode, requests: [], events: [], turns: [], checks: {} }
let turn = -1
let injected = false
let childDone!: () => void
const completion = new Promise<void>((resolve) => { childDone = resolve })
const final = await Bun.file(root + "/final.sse").text()
const childFixture = await Bun.file(root + "/child.sse").text()
const provider = Bun.serve({ hostname: "127.0.0.1", port: 8765, async fetch(request) {
  if (request.method !== "POST" || new URL(request.url).pathname !== "/v1/responses") return new Response("forbidden", { status: 403 })
  const payload: any = await request.json()
  result.requests.push(payload)
  if (result.requests.length > 24) return new Response("synthetic cap", { status: 429 })
  const child = String(payload.instructions).includes("REPORT_V1_CHILD_SYSTEM") || JSON.stringify(payload.input).includes('You are a subagent') && !payload.tools?.some((t: any) => t.name === "task")
  if (mode === "subagent" && child) {
    await Bun.sleep(1000)
    result.child_response_at = performance.now()
    return new Response(childFixture, { headers: { "content-type": "text/event-stream" } })
  }
  const target = mode === "permission" ? "bash" : "task"
  if (!injected && payload.tools?.some((t: any) => t.name === target)) {
    injected = true
    const file = mode === "permission" ? `/call-${turn}.sse` : "/task.sse"
    return new Response(await Bun.file(root + file).text(), { headers: { "content-type": "text/event-stream" } })
  }
  return new Response(final, { headers: { "content-type": "text/event-stream" } })
} })
const server = Bun.spawn([process.argv[2], "serve", "--hostname", "127.0.0.1", "--port", "0"], {
  stdin: "ignore", stdout: "pipe", stderr: Bun.file(root + "/v1-server.log"),
  env: { ...process.env, OPENCODE_SERVER_PASSWORD: password },
})
const abort = new AbortController()
let url = ""
let decision = "once"
function check(name: string, value: unknown) { result.checks[name] = Boolean(value); if (!value) throw new Error(name) }
async function api(method: string, path: string, body?: unknown) {
  const response = await fetch(url + path, { method, headers: { authorization, "content-type": "application/json", "x-opencode-directory": process.cwd() },
    body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(12000) })
  const text = await response.text()
  if (!response.ok) throw new Error(method + " " + path + " HTTP " + response.status + " " + text.slice(0, 500))
  return text ? JSON.parse(text) : undefined
}
try {
  const reader = server.stdout.getReader()
  let text = ""
  while (!url) {
    const chunk = await reader.read()
    if (chunk.done) throw new Error("server ended before readiness")
    text += new TextDecoder().decode(chunk.value)
    url = text.match(/opencode server listening on (http:\/\/\S+)/)?.[1] ?? ""
  }
  void (async () => { while (!(await reader.read()).done) {} })()
  let ready!: () => void
  let fail!: (error: unknown) => void
  const connected = new Promise<void>((resolve, reject) => { ready = resolve; fail = reject })
  const timer = setTimeout(() => fail(new Error("v1 event readiness deadline")), 8000)
  void (async () => {
    const stream = await fetch(url + "/event", { headers: { authorization, "x-opencode-directory": process.cwd() }, signal: abort.signal })
    if (!stream.ok || !stream.body) throw new Error("v1 SSE HTTP " + stream.status)
    const source = stream.body.getReader(); let pending = ""
    while (true) {
      const chunk = await source.read(); if (chunk.done) break
      pending += new TextDecoder().decode(chunk.value)
      let boundary: number
      while ((boundary = pending.indexOf("\n\n")) >= 0) {
        const record = pending.slice(0, boundary); pending = pending.slice(boundary + 2)
        const data = record.split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trim()).join("\n")
        if (!data) continue
        const event = JSON.parse(data); result.events.push(event)
        if (event.type === "server.connected") ready()
        if (event.type === "permission.asked") {
          const asked = event.properties
          const pending = await api("GET", "/permission")
          result.turns[turn].asked = asked
          result.turns[turn].pending_before = pending
          await api("POST", "/permission/" + asked.id + "/reply", { reply: decision })
          result.turns[turn].pending_after = await api("GET", "/permission")
        }
        if (JSON.stringify(event).includes("REPORT_V1_PARENT_MARKER") && !result.parent_marker_at) result.parent_marker_at = performance.now()
        if (event.type === "message.part.updated" && JSON.stringify(event).includes("REPORT_V1_CHILD_MARKER") && JSON.stringify(event).includes("task")) childDone()
      }
    }
  })().catch((error) => { if (!abort.signal.aborted) { result.event_error = String(error); fail(error) } })
  await connected.finally(() => clearTimeout(timer))
  check("subscribed_before_prompt", true)
  const session = await api("POST", "/session", { title: "report-v1-native-" + mode })
  result.sessionID = session.id
  if (mode === "permission") {
    for (const [index, reply] of ["once", "reject", "always", "once", "once", "reject"].entries()) {
      turn = index; decision = reply; injected = false
      result.turns.push({ index, reply })
      const response = await api("POST", `/session/${session.id}/message`, { parts: [{ type: "text", text: "REPORT_V1_PERMISSION_TURN_" + index }] })
      result.turns[index].response = response
      const witness = existsSync(process.cwd() + `/v1-witness-${index}.txt`)
      result.turns[index].witness = witness
      check("turn_" + index + "_witness", witness === ![1, 5].includes(index))
      check("turn_" + index + "_ask_scope", Boolean(result.turns[index].asked) === [0, 1, 2, 5].includes(index))
    }
    check("all_pending_settled", (await api("GET", "/permission")).length === 0)
  } else {
    injected = false
    result.parent_response = await api("POST", `/session/${session.id}/message`, { parts: [{ type: "text", text: "Launch scripted child in background then return parent marker." }] })
    check("native_background_task_returned", JSON.stringify(result.parent_response).includes('state=\\"running\\"') || JSON.stringify(result.parent_response).includes("working in the background"))
    const deadline = setTimeout(childDone, 8000)
    await completion; clearTimeout(deadline)
    result.messages = await api("GET", `/session/${session.id}/message`)
    check("child_completion_in_parent", JSON.stringify(result.messages).includes("REPORT_V1_CHILD_MARKER"))
    check("parent_continues_before_child", result.parent_marker_at < result.child_response_at)
  }
  result.status = "pass"
} catch (error) { result.status = "error"; result.error = String(error) }
finally {
  abort.abort(); server.kill("SIGTERM")
  const watchdog = setTimeout(() => server.kill(9), 5000)
  result.server_exit = await server.exited; clearTimeout(watchdog)
  provider.stop(true)
  await Bun.write(root + "/v1-result.json", JSON.stringify(result, null, 2).replaceAll(password, "[PRIVATE-PASSWORD]"))
  console.log(JSON.stringify({ status: result.status, checks: result.checks, error: result.error }))
}
