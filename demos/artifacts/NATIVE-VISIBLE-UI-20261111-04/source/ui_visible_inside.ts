// Owned Xvfb display, packaged Desktop, standalone Chrome and native TUI. No inference.
import { mkdirSync, readFileSync, watch } from "node:fs"

const root = process.env.HOME!.replace(/\/home$/, "")
const result: any = { scope: "fresh isolated Xvfb; real Desktop window, standalone Chrome toolbar and xterm TUI; no prompt", checks: {}, screenshots: {}, timeline: [] }
const owned: ReturnType<typeof Bun.spawn>[] = []
const sockets: WebSocket[] = []
const password = crypto.randomUUID()
const authorization = "Basic " + btoa("opencode:" + password)
const tools = "/opt/research/ui-tools/usr/bin/"
function check(name: string, value: unknown) { result.checks[name] = Boolean(value); if (!value) throw new Error(name) }
function spawn(args: string[], name: string, env = process.env) {
  const process = Bun.spawn(args, { stdin: "ignore", stdout: Bun.file(root + "/" + name + "-stdout.txt"), stderr: Bun.file(root + "/" + name + "-stderr.txt"), env })
  owned.push(process)
  result.timeline.push({ stage: "spawn", name, pid: process.pid, args, at: new Date().toISOString() })
  return process
}
async function waitFile(path: string, timeout = 12000): Promise<any> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { observer.close(); reject(new Error("file readiness deadline: " + path)) }, timeout)
    const inspect = () => {
      try { const data = JSON.parse(readFileSync(path, "utf8")); observer.close(); clearTimeout(timer); resolve(data) } catch {}
    }
    const observer = watch(path.slice(0, path.lastIndexOf("/")), inspect)
    inspect()
  })
}
let url = ""
async function api(method: string, path: string, data?: unknown) {
  const response = await fetch(url + path, { method, headers: { authorization, "content-type": "application/json" },
    body: data === undefined ? undefined : JSON.stringify(data), signal: AbortSignal.timeout(5000) })
  if (!response.ok) throw new Error("API HTTP " + response.status)
  return response.json()
}
async function connect(port: number) {
  let targets: any[] = []
  for (let attempt = 0; attempt < 50; attempt++) {
    try { targets = await (await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(600) })).json() as any[] } catch {}
    if (targets.some(t => t.type === "page")) break
    await Bun.sleep(200) // bounded native browser boot readiness, not agent polling
  }
  const target = targets.find(t => t.type === "page")
  if (!target) throw new Error("no page target on private port " + port)
  const socket = new WebSocket(target.webSocketDebuggerUrl)
  sockets.push(socket)
  await new Promise<void>((resolve, reject) => { socket.onopen = () => resolve(); socket.onerror = reject })
  let sequence = 0
  const pending = new Map<number, { resolve: (x: any) => void, reject: (e: unknown) => void }>()
  socket.onmessage = event => {
    const message = JSON.parse(String(event.data))
    if (message.method === "Runtime.exceptionThrown" || message.method === "Network.loadingFailed") {
      result.browser_errors ??= []; result.browser_errors.push({ port, method: message.method, params: message.params })
    }
    if (!message.id) return
    const p = pending.get(message.id); pending.delete(message.id)
    if (message.error) p?.reject(new Error(JSON.stringify(message.error)))
    else p?.resolve(message.result)
  }
  const call = (method: string, params: object = {}): Promise<any> => new Promise((resolve, reject) => {
    const id = ++sequence
    result.last_cdp = { port, method, at: new Date().toISOString() }
    const timer = setTimeout(() => { pending.delete(id); reject(new Error("CDP deadline " + method)) }, 12000)
    pending.set(id, { resolve(x) { clearTimeout(timer); resolve(x) }, reject(e) { clearTimeout(timer); reject(e) } })
    socket.send(JSON.stringify({ id, method, params }))
  })
  return call
}
async function titleReady(cdp: Awaited<ReturnType<typeof connect>>) {
  return cdp("Runtime.evaluate", { expression: `new Promise(resolve => {
    const inspect = () => { if(document.body?.innerText.includes("REPORT_SHARED_UI_MARKER")) { observer.disconnect(); clearTimeout(timer); resolve({url:location.href,title:document.title,text:document.body.innerText}) } };
    const observer = new MutationObserver(inspect); observer.observe(document,{childList:true,subtree:true,characterData:true});
    const timer = setTimeout(()=>{observer.disconnect();resolve({error:"TITLE_TIMEOUT",url:location.href,text:document.body?.innerText})},10000); inspect();
  })`, awaitPromise: true, returnByValue: true })
}
async function capture(name: string) {
  const p = Bun.spawn(["/usr/bin/python3", "-B", "-c", "from PIL import ImageGrab; import sys; ImageGrab.grab(xdisplay=':91').save(sys.argv[1])", root + "/" + name + ".png"], { stdout: "pipe", stderr: "pipe", env: process.env })
  const error = await new Response(p.stderr).text()
  check(name + "_screen_capture", await p.exited === 0)
  if (error) result.screenshot_warning = error
  result.screenshots[name] = { method: "Pillow ImageGrab / XCB root screen, not CDP viewport or fabricated chrome", display: ":91", at: new Date().toISOString() }
}
try {
  mkdirSync(root + "/xdg-state/opencode", { recursive: true })
  await Bun.write(root + "/xdg-config/opencode/service.json", JSON.stringify({ password }))
  await Bun.write(root + "/twmrc", 'RandomPlacement\nNoGrabServer\nDontMoveOff\nDecorateTransients\nTitleFont "fixed"\nResizeFont "fixed"\nMenuFont "fixed"\nIconFont "fixed"\nIconManagerFont "fixed"\nColor {\n BorderColor "#406482"\n TitleBackground "#d9e9ef"\n TitleForeground "#182b3a"\n}\n')
  const x = spawn([tools + "Xvfb", ":91", "-screen", "0", "1600x1050x24", "-nolisten", "tcp", "-ac"], "xvfb")
  const ready = Bun.spawn(["/usr/bin/python3", "-B", "-c", "import socket,time; s=socket.socket(socket.AF_UNIX); end=time.monotonic()+8\nwhile time.monotonic()<end:\n try:s.connect('/tmp/.X11-unix/X91');break\n except OSError:time.sleep(.1)\nelse:raise SystemExit('private X server readiness failed')"], { stdout: "pipe", stderr: "pipe", env: process.env })
  check("private_xvfb_ready", await ready.exited === 0 && x.exitCode === null)
  spawn([tools + "twm", "-f", root + "/twmrc"], "twm")
  const service = spawn([process.argv[2], "serve", "--service", "--hostname", "127.0.0.1", "--port", "0"], "service")
  const registration = await waitFile(root + "/xdg-state/opencode/service.json")
  check("owned_service_registration", registration.pid === service.pid)
  url = registration.url
  result.health = []
  for (let i = 0; i < 15; i++) {
    const response = await fetch(url + "/api/info", { headers: { authorization }, signal: AbortSignal.timeout(2000) })
    result.health.push(response.status)
    if (response.ok) { result.service_before = await response.json(); break }
    if (response.status !== 503) throw new Error("private service health " + response.status)
    await Bun.sleep(500)
  }
  check("private_service_ready", result.service_before?.pid === service.pid)
  const session = await api("POST", "/api/session", { title: "REPORT_SHARED_UI_MARKER", location: { directory: process.cwd() } })
  result.session = session
  const sessionID = session.data.id
  const desktop = spawn(["/opt/research/desktop/ai.opencode", "--ozone-platform=x11", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--password-store=basic", "--remote-debugging-port=9333"], "desktop")
  const d = await connect(9333)
  await d("Runtime.enable")
  await d("Network.enable")
  await capture("desktop-boot-diagnostic")
  result.desktop_boot_document = await d("Runtime.evaluate", { expression: "JSON.stringify({url:location.href,ready:document.readyState,windowID:window.electron?.windowID})", returnByValue: true })
  const route = "/server/" + btoa("sidecar").replace(/=+$/, "") + "/session/" + sessionID
  await d("Runtime.evaluate", { expression: `localStorage.setItem("opencode.desktop.window."+window.electron.windowID+".last-active-url",${JSON.stringify(route)});true`, returnByValue: true })
  await d("Page.reload")
  await Bun.sleep(500)
  result.desktop_document = await titleReady(d)
  check("desktop_shared_session", !result.desktop_document.result?.value?.error && result.desktop_document.result.value.text.includes("REPORT_SHARED_UI_MARKER"))
  // Electron's page CDP does not expose Browser.getWindowForTarget at this pin.
  // Keep its actual native window size; do not fabricate a frame around a viewport.
  result.desktop_route = route
  await Bun.sleep(650)
  await capture("desktop-window")
  result.service_after_desktop = await api("GET", "/api/info")
  check("desktop_keeps_service_pid", result.service_after_desktop.pid === service.pid && desktop.exitCode === null)
  const chrome = spawn(["/opt/google/chrome/chrome", "--ozone-platform=x11", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-sync", "--disable-extensions", "--no-first-run", "--no-default-browser-check", "--password-store=basic", "--user-data-dir=" + root + "/chrome-profile", "--remote-debugging-port=9444", "--window-position=35,30", "--window-size=1500,950", "about:blank"], "chrome")
  const c = await connect(9444)
  await c("Network.enable")
  await c("Network.setExtraHTTPHeaders", { headers: { Authorization: authorization } })
  const webRoute = "/server/" + btoa(url).replace(/=+$/, "") + "/session/" + sessionID
  await c("Page.navigate", { url: url + webRoute })
  await Bun.sleep(500)
  result.web_document = await titleReady(c)
  check("standalone_browser_shared_session", !result.web_document.result?.value?.error && result.web_document.result.value.text.includes("REPORT_SHARED_UI_MARKER") && chrome.exitCode === null)
  result.web_route = url + webRoute
  await c("Page.bringToFront")
  await Bun.sleep(650)
  await capture("web-browser")
  const terminal = spawn([tools + "xterm", "-geometry", "148x42+35+30", "-fa", "DejaVu Sans Mono", "-fs", "12", "-bg", "#0d1b2a", "-fg", "#e6edf3", "-title", "OpenCode TUI - isolated capture", "-e", "/usr/bin/python3", "-B", "/opt/research/tui_visible_inside.py", process.argv[2], sessionID], "terminal")
  result.tui_ready = await waitFile(root + "/tui-visible-ready.json", 18000)
  check("tui_shared_session", result.tui_ready.sessionID === sessionID && result.tui_ready.session_title_observed && terminal.exitCode === null)
  await Bun.sleep(750)
  await capture("tui-terminal")
  await Bun.write(root + "/stop-tui", "stop only owned TUI")
  await terminal.exited
  result.tui = await Bun.file(root + "/tui-result.json").json()
  result.service_after_all = await api("GET", "/api/info")
  check("all_clients_keep_service_pid", result.service_after_all.pid === result.service_before.pid)
  check("same_endpoint", JSON.stringify(result.service_after_all.urls) === JSON.stringify(result.service_before.urls))
  result.no_prompt_submitted = true
  result.status = "checks_passed_pending_review"
} catch (error) {
  result.status = "error"; result.error = String(error)
  try { await capture("failure-screen") } catch (captureError) { result.failure_capture_error = String(captureError) }
} finally {
  for (const s of sockets) s.close()
  result.cleanup = []
  for (const p of owned.toReversed()) {
    if (p.exitCode === null) p.kill("SIGTERM")
    const timeout = setTimeout(() => { if (p.exitCode === null) p.kill(9) }, 4000)
    const exit = await p.exited; clearTimeout(timeout)
    result.cleanup.push({ pid: p.pid, exit })
  }
  await Bun.write(root + "/ui-visible-result.json", JSON.stringify(result, null, 2).replaceAll(password, "[PRIVATE-PASSWORD]"))
  console.log(JSON.stringify({ status: result.status, checks: result.checks, error: result.error }))
}
