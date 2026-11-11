// Test-only empty ruleset: exposes evaluator fallback, not normal base-agent defaults.
export default {
  id: "report.unmatched",
  async setup(ctx) {
    await ctx.agent.transform((editor) => {
      editor.update("build", (agent) => { agent.permissions = [] })
    })
  },
}
