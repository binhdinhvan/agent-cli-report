// Shared offline acceptance for the native HTTP Client and embedded SDK.
export function matrixProvider(final: string) {
  let mode = "final"
  let requested!: () => void
  let ready = Promise.resolve()
  let release!: () => void
  let blocked = Promise.resolve()
  return {
    phase(value: string) {
      mode = value
      ready = new Promise<void>((resolve) => { requested = resolve })
      blocked = new Promise<void>((resolve) => { release = resolve })
    },
    ready: () => ready,
    release: () => release?.(),
    async response() {
      requested?.()
      if (mode === "error") return new Response(JSON.stringify({ error: { type: "invalid_request_error", code: "report_fixture_error", message: "REPORT_SCRIPTED_PROVIDER_ERROR" } }), {
        status: 400, headers: { "content-type": "application/json" },
      })
      if (mode === "pending") await blocked
      return new Response(final, { headers: { "content-type": "text/event-stream" } })
    },
  }
}

export async function failureMatrix(client: any, model: ReturnType<typeof matrixProvider>) {
  const result: any = { checks: {}, scenarios: [] }
  function check(name: string, condition: unknown) { result.checks[name] = Boolean(condition); if (!condition) throw new Error(name) }
  async function ready() {
    let timer: ReturnType<typeof setTimeout>
    await Promise.race([model.ready(), new Promise<void>((_resolve, reject) => {
      timer = setTimeout(() => reject(new Error("scripted model admission deadline")), 5000)
    })]).finally(() => clearTimeout(timer))
  }
  model.phase("error")
  const failed = await client.session.create({ title: "report-native-error", location: { directory: process.cwd() } })
  await client.session.prompt({ sessionID: failed.id, text: "Return the scripted provider error." })
  await client.experimental.session.wait({ sessionID: failed.id })
  const failedContext = await client.session.context({ sessionID: failed.id })
  const failedTerminal = failedContext.filter((e: any) => e.type === "idle").at(-1)
  result.scenarios.push({ kind: "provider_error", sessionID: failed.id, context: failedContext, terminal: failedTerminal })
  check("scripted_http400_native_terminal_failed", failedTerminal?.outcome === "failed")
  check("provider_error_marker_retained", JSON.stringify(failedContext).includes("REPORT_SCRIPTED_PROVIDER_ERROR"))

  model.phase("pending")
  const pending = await client.session.create({ title: "report-native-interrupt", location: { directory: process.cwd() } })
  await client.session.prompt({ sessionID: pending.id, text: "Hold the scripted inference until native interrupt." })
  await ready()
  let waitError = ""
  try { await client.experimental.session.wait({ sessionID: pending.id }, { signal: AbortSignal.timeout(50) }) }
  catch (error) { waitError = String(error) }
  check("wait_timeout_rejects_request", Boolean(waitError))
  const afterTimeout = await client.session.context({ sessionID: pending.id })
  check("wait_timeout_does_not_finish_execution", !afterTimeout.some((e: any) => e.type === "idle"))
  await client.session.interrupt({ sessionID: pending.id })
  model.release()
  await client.experimental.session.wait({ sessionID: pending.id })
  const interruptedContext = await client.session.context({ sessionID: pending.id })
  const interruptedTerminal = interruptedContext.filter((e: any) => e.type === "idle").at(-1)
  result.scenarios.push({ kind: "wait_timeout_then_session_interrupt", sessionID: pending.id, waitError, afterTimeout,
    context: interruptedContext, terminal: interruptedTerminal })
  check("native_interrupt_reaches_idle", Boolean(interruptedTerminal))
  check("native_interrupt_not_success", interruptedTerminal.outcome !== "success")
  return result
}
