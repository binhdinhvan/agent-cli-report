export default async () => {
  console.error("REPORT_PLUGIN_V1_LOADED")
  return {
    tool: {
      report_marker: {
        description: "Return the fixed research marker; no file, environment, credential or network access.",
        args: {},
        async execute() {
          return "REPORT_PLUGIN_MARKER"
        },
      },
    },
  }
}
