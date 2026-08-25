/**
 * Kimi Console — Google Apps Integration
 * Uses Google Identity Services (GIS) OAuth2 + Gmail/Calendar/Drive APIs.
 */
class GoogleClient {
  constructor(clientId) {
    this.clientId = clientId;
    this.token = null;
    this.scopes = 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/drive.readonly';
  }

  loadGIS() {
    return new Promise((resolve, reject) => {
      if (window.google?.accounts) return resolve();
      const s = document.createElement('script');
      s.src = 'https://accounts.google.com/gsi/client';
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  async init() {
    await this.loadGIS();
    this.client = google.accounts.oauth2.initTokenClient({
      client_id: this.clientId,
      scope: this.scopes,
      callback: (resp) => {
        if (resp.error) return;
        this.token = resp.access_token;
        localStorage.setItem('google_token', this.token);
        document.dispatchEvent(new CustomEvent('google-authed'));
      }
    });
  }

  async auth() {
    if (!this.client) await this.init();
    this.client.requestAccessToken();
  }

  async revoke() {
    if (!this.token) return;
    if (window.google?.accounts?.oauth2) {
      google.accounts.oauth2.revoke(this.token, () => {});
    }
    this.token = null;
    localStorage.removeItem('google_token');
  }

  async api(url) {
    if (!this.token) this.token = localStorage.getItem('google_token');
    if (!this.token) throw new Error('Not authenticated');
    const res = await fetch(url, {
      headers: { 'Authorization': 'Bearer ' + this.token }
    });
    if (!res.ok) throw new Error('Google API ' + res.status);
    return res.json();
  }

  async getEmails(max = 5) {
    const list = await this.api(`https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=${max}`);
    if (!list.messages) return [];
    return Promise.all(list.messages.map(m =>
      this.api(`https://gmail.googleapis.com/gmail/v1/users/me/messages/${m.id}?format=metadata&metadataHeaders=Subject&metadataHeaders=From`)
    ));
  }

  async getEvents(max = 5) {
    const timeMin = new Date().toISOString();
    const data = await this.api(`https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin=${encodeURIComponent(timeMin)}&maxResults=${max}&orderBy=startTime&singleEvents=true`);
    return data.items || [];
  }

  async getDriveFiles(max = 5) {
    const data = await this.api(`https://www.googleapis.com/drive/v3/files?pageSize=${max}&fields=files(id,name,webViewLink)`);
    return data.files || [];
  }
}
