/**
 * Kimi Console — OpenClaw (MCP) Placeholder
 * Kimi Console — OpenClaw (MCP) local installation status.
 */
class OpenClawClient {
  constructor(isLocallyInstalled) {
    this.enabled = !!isLocallyInstalled;
  }

  async test() {
    if (!this.enabled) return { ok: false, msg: 'Mark OpenClaw as locally installed first.' };
    return { ok: true, msg: 'OpenClaw local installation enabled. Full MCP integration pending.' };
  }
}
