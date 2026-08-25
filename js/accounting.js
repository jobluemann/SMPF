/**
 * Kimi Console — Accounting Software Placeholder
 * Supports Wave, Manager.io, GnuCash, and Akaunting.
 * This is a stub awaiting user selection of provider.
 */
class AccountingClient {
  constructor(provider) {
    this.provider = provider;
  }

  static providers = {
    wave: { name: 'Wave', url: 'https://developer.waveapps.com/hc/en-us', api: 'GraphQL' },
    manager: { name: 'Manager.io', url: 'https://www.manager.io/guides/9458', api: 'Desktop / Cloud' },
    gnucash: { name: 'GnuCash', url: 'https://wiki.gnucash.org/wiki/Python_Bindings', api: 'Python bindings (local)' },
    akaunting: { name: 'Akaunting', url: 'https://akaunting.com/docs/developer-manual', api: 'REST' }
  };

  getInfo() {
    return AccountingClient.providers[this.provider] || null;
  }

  async test() {
    return { ok: true, msg: `${this.provider} integration not yet implemented. Select a provider in Settings > Integrations.` };
  }
}
