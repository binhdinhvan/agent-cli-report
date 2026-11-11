import { expect, test } from "bun:test"
import { matrixProvider } from "./failure_matrix"

test("scripted error has explicit local marker and HTTP400", async () => {
  const model = matrixProvider("fixed-sse")
  model.phase("error")
  const response = await model.response()
  await model.ready()
  expect(response.status).toBe(400)
  expect(await response.text()).toContain("REPORT_SCRIPTED_PROVIDER_ERROR")
})

test("scripted pending inference waits for explicit release", async () => {
  const model = matrixProvider("fixed-sse")
  model.phase("pending")
  let completed = false
  const response = model.response().then((value) => { completed = true; return value })
  await model.ready()
  expect(completed).toBe(false)
  model.release()
  expect(await (await response).text()).toBe("fixed-sse")
})

test("new phases reset readiness and use no provider credentials", async () => {
  const model = matrixProvider("fixed-sse")
  for (const phase of ["final", "error", "final"]) {
    model.phase(phase)
    const response = await model.response()
    await model.ready()
    expect(response.status).toBe(phase === "error" ? 400 : 200)
  }
})
