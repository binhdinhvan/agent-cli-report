import { mkdirSync, readFileSync, watch } from "node:fs"
const root = process.env.HOME!.replace(/\/home$/, "")
const result: any = { scope: "native packaged UI2.2.5/headless isolated service; not live user desktop", checks: {}, health: [], cdpAttempts: [] }
const password = crypto.randomUUID()
const authorization = "Basic " + btoa("opencode:" + password)
const state = root + "/xdg-state/opencode"
mkdirSync(state, { recursive: true })
await Bun.write(root + "/xdg-config/opencode/service.json", JSON.stringify({ password }))
const service = Bun.spawn([process.argv[2], "serve", "--service", "--hostname", "127.0.0.1", "--port", "0"], {
  stdin: "ignore", stdout: Bun.file(root + "/ui-server.log"), stderr: Bun.file(root + "/ui-server-error.log"), env: process.env,
})
let desktop: ReturnType<typeof Bun.spawn> | undefined
let socket: WebSocket | undefined
let url = ""
let cdpID = 0
const calls = new Map<number, { resolve: (value: any) => void, reject: (error: unknown) => void }>()
function check(name: string, condition: unknown) { result.checks[name] = Boolean(condition); if (!condition) throw new Error(name) }
async function api(method: string, path: string, body?: unknown) {
  const response = await fetch(url + path, { method, headers: { authorization, "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(5000) })
  if (!response.ok) throw new Error("UI API HTTP " + response.status)
  return response.json()
}
async function cdp(method: string, params: object = {}) {
  const id = ++cdpID
  return new Promise<any>((resolve, reject) => {
    const timeout = setTimeout(() => { calls.delete(id); reject(new Error("CDP deadline " + method)) }, 8000)
    calls.set(id, { resolve(value) { clearTimeout(timeout); resolve(value) }, reject(error) { clearTimeout(timeout); reject(error) } })
    socket!.send(JSON.stringify({ id, method, params }))
  })
}
try {
  url = await new Promise<string>((resolve, reject) => {
    const timeout = setTimeout(() => { observer.close(); reject(new Error("UI service registration deadline")) }, 10000)
    const inspect = () => {
      try {
        const registration = JSON.parse(readFileSync(state + "/service.json", "utf8"))
        if (registration.pid !== service.pid) return
        observer.close(); clearTimeout(timeout); resolve(registration.url)
      } catch {}
    }
    const observer = watch(state, inspect); inspect()
  })
  for (let index = 0; index < 15; index++) {
    const response = await fetch(url + "/api/info", { headers: { authorization }, signal: AbortSignal.timeout(3000) })
    result.health.push(response.status)
    if (response.ok) { result.server_info = await response.json(); break }
    if (response.status !== 503) throw new Error("UI service readiness HTTP " + response.status)
    await Bun.sleep(1000)
  }
  check("private_service_ready", result.server_info?.pid === service.pid)
  const session = await api("POST", "/api/session", { title: "REPORT_SHARED_UI_MARKER", location: { directory: process.cwd() } })
  result.session = session
  desktop = Bun.spawn(["/opt/research/desktop/ai.opencode", "--ozone-platform=headless", "--no-sandbox", "--disable-gpu", "--remote-debugging-port=9333"], {
    stdin: "ignore", stdout: Bun.file(root + "/desktop-stdout.txt"), stderr: Bun.file(root + "/desktop-stderr.txt"),
    env: { ...process.env, OPENCODE_DISABLE_AUTOUPDATE: "1" },
  })
  let targets: any[] = []
  for (let index = 0; index < 30; index++) {
    try {
      const response = await fetch("http://127.0.0.1:9333/json/list", { signal: AbortSignal.timeout(1000) })
      targets = await response.json() as any[]
      result.cdpAttempts.push({ status: response.status, targets: targets.map((t) => ({ type: t.type, url: t.url })) })
      if (targets.some((t) => t.type === "page")) break
    } catch (error) { result.cdpAttempts.push({ error: String(error) }) }
    if (desktop.exitCode !== null) throw new Error("packaged desktop exited " + desktop.exitCode)
    await Bun.sleep(250)
  }
  const target = targets.find((t) => t.type === "page")
  check("native_desktop_renderer_created", target)
  socket = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise<void>((resolve, reject) => { socket!.onopen = () => resolve(); socket!.onerror = reject })
  socket.onmessage = (event) => {
    const message = JSON.parse(String(event.data))
    if (!message.id) return
    const pending = calls.get(message.id); calls.delete(message.id)
    if (message.error) pending?.reject(new Error(JSON.stringify(message.error)))
    else pending?.resolve(message.result)
  }
  await cdp("Runtime.enable")
  result.desktop_document = await cdp("Runtime.evaluate", { expression: "JSON.stringify({url:location.href,title:document.title,text:document.body.innerText})", returnByValue: true })
  const screenshot = await cdp("Page.captureScreenshot", { format: "png" })
  await Bun.write(root + "/desktop.png", Buffer.from(screenshot.data, "base64"))
  result.service_after_desktop = await api("GET", "/api/info")
  check("desktop_did_not_replace_private_service", result.service_after_desktop.pid === service.pid)
  result.status = "observed_pending_review"
} catch (error) { result.status = "error"; result.error = String(error) }
finally {
  socket?.close()
  for (const owned of [desktop, service]) {
    if (!owned) continue
    owned.kill("SIGTERM")
    const timeout = setTimeout(() => owned.kill(9), 5000)
    await owned.exited; clearTimeout(timeout)
  }
  await Bun.write(root + "/ui-result.json", JSON.stringify(result, null, 2).replaceAll(password, "[PRIVATE-PASSWORD]"))
  console.log(JSON.stringify({ status: result.status, checks: result.checks, error: result.error }))
}
