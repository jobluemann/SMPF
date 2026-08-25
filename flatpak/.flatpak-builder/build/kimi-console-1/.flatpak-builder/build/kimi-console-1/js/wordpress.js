/**
 * Kimi Console — WordPress Integration
 * Uses WordPress REST API with Application Passwords (WP 5.6+).
 */
class WordPressClient {
  constructor(baseUrl, username, appPassword) {
    this.base = baseUrl.replace(/\/$/, '');
    this.username = username;
    this.password = appPassword;
    this.auth = 'Basic ' + btoa(unescape(encodeURIComponent(username + ':' + appPassword)));
  }

  async req(path, opts = {}) {
    const res = await fetch(this.base + '/wp-json/wp/v2' + path, {
      ...opts,
      headers: {
        'Authorization': this.auth,
        'Content-Type': 'application/json',
        ...(opts.headers || {})
      }
    });
    if (!res.ok) {
      const txt = await res.text().catch(() => res.statusText);
      throw new Error('WP ' + res.status + ': ' + txt);
    }
    return res.json();
  }

  async getPosts(per_page = 10) {
    return this.req(`/posts?per_page=${per_page}&_embed=1`);
  }

  async getPost(id) {
    return this.req(`/posts/${id}?_embed=1`);
  }

  async createPost(title, content, status = 'draft') {
    return this.req('/posts', {
      method: 'POST',
      body: JSON.stringify({ title, content, status })
    });
  }

  async updatePost(id, data) {
    return this.req(`/posts/${id}`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async test() {
    return this.req('/users/me');
  }
}
