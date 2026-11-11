export default {
  id: "report.marker",
  async setup(ctx) {
    console.error("REPORT_PLUGIN_V2_LOADED")
    await ctx.tool.transform((editor) => {
      editor.add({
        name: "report_marker",
        description: "Return the fixed research marker; no file, environment, credential or network access.",
        input: { type: "object", properties: {}, additionalProperties: false },
        async execute() {
          return { content: "REPORT_PLUGIN_MARKER" }
        },
      })
    })
    return () => console.error("REPORT_PLUGIN_V2_CLEANUP")
  },
}
