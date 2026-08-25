/**
 * Kimi Console — GitHub Sync Module
 * Push / pull JSON snapshots of IndexedDB data to a GitHub repo.
 */
class GitHubSync {
  constructor(token, repo, branch = 'main') {
    this.token = token;
    this.repo = repo;
    this.branch = branch;
    this.apiBase = 'https://api.github.com';
  }

  async request(path, opts = {}) {
    const url = this.apiBase + path;
    const res = await fetch(url, {
      ...opts,
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + this.token,
        'X-GitHub-Api-Version': '2022-11-28',
        ...(opts.headers || {})
      }
    });
    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`GitHub ${res.status}: ${text}`);
    }
    return res.json().catch(() => ({}));
  }

  async getFile(path) {
    try {
      return await this.request(`/repos/${this.repo}/contents/${path}?ref=${this.branch}`);
    } catch (e) { return null; }
  }

  async push(path, content, message) {
    const existing = await this.getFile(path);
    const payload = {
      message,
      content: btoa(unescape(encodeURIComponent(content))),
      branch: this.branch
    };
    if (existing && existing.sha) payload.sha = existing.sha;
    return this.request(`/repos/${this.repo}/contents/${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }

  async pull(path) {
    const file = await this.getFile(path);
    if (!file || !file.content) return null;
    const json = decodeURIComponent(escape(atob(file.content.replace(/\s/g, ''))));
    return JSON.parse(json);
  }

  async exportAll() {
    const stores = ['projects', 'prompts', 'notes', 'context', 'settings'];
    const snapshot = {};
    for (const s of stores) snapshot[s] = await dbGetAll(s);
    return snapshot;
  }

  async pushSnapshot() {
    const snap = await this.exportAll();
    const ts = new Date().toISOString();
    await this.push('kimi-console/snapshot.json', JSON.stringify(snap, null, 2), `Sync snapshot ${ts}`);
    return ts;
  }

  async pullSnapshot() {
    const data = await this.pull('kimi-console/snapshot.json');
    if (!data) return null;
    for (const [store, items] of Object.entries(data)) {
      if (!Array.isArray(items)) continue;
      await dbClear(store);
      for (const item of items) await dbPut(store, item);
    }
    return data;
  }
}
