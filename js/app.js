const APP_BUILD = '2026.08.23.1';

/**
 * Kimi Console — Main Application Controller
 * Phase 1: Core chat, projects, prompts, notes, context
 * Phase 2: GitHub sync
 * Phase 3: WordPress, Google Apps, Accounting, OpenClaw integrations
 */

class App {
  constructor() {
    this.currentView = 'chat';
    this.currentProject = null;
    this.provider = 'groq';
    this.providerModels = { kimi: PROVIDERS.kimi.model, groq: PROVIDERS.groq.model, openrouter: PROVIDERS.openrouter.model, openclaw: PROVIDERS.openclaw.model };
    this.chatMode = 'normal';
    this.developmentProvider = 'openrouter';
    this.developmentModel = PROVIDERS.openrouter.model;
    this.github = null;
    this.wpClient = null;
    this.googleClient = null;
    this.accounting = null;
    this.openclaw = null;
    this.voice = new VoiceManager();
    this.pendingFiles = [];
    this.messageHistory = [];
    this.activeContextIds = [];
    this.lastUsedModel = null;
    this.newChatRequested = false;
    this.init();
  }

  /* ===== Boot ===== */
  async init() {
    this.bindNav();
    this.bindChat();
    this.bindProjects();
    this.bindPrompts();
    this.bindNotes();
    this.bindContext();
    this.bindSync();
    this.bindIntegrations();
    this.bindSettings();
    await this.voice.init();
    await this.loadSettings();
    this.loadMessages();
    await this.refreshProjects();
    await this.refreshPrompts();
    await this.refreshNotes();
    await this.refreshContext();
    this.initIntegrations();
    this.registerSW();
  }

  registerSW() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('sw.js').catch(() => {});
    }
  }

  /* ===== Navigation ===== */
  bindNav() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        this.switchView(view);
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  }

  switchView(view) {
    this.currentView = view;
    if (view === 'chat') this.chatMode = 'normal';
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById('view-' + view)?.classList.remove('hidden');
    if (view === 'integrations' || view === 'openclaw') this.refreshIntegrations();
  }

  /* ===== Chat ===== */
  bindChat() {
    const input = document.getElementById('chatInput');
    const send = document.getElementById('sendBtn');
    const attach = document.getElementById('attachBtn');
    const fileIn = document.getElementById('fileInput');
    const sel = document.getElementById('providerSelect');
    const activeModel = document.getElementById('activeModel');
    const updateActiveModel = () => {
      if (activeModel) activeModel.textContent = `${this.provider}: ${this.providerModels[this.provider]}`;
    };

    document.getElementById('useDevelopmentBtn')?.addEventListener('click', () => this.openDevelopmentChat());
    document.getElementById('testGroqModelBtn')?.addEventListener('click', () => this.testDevelopmentModel('groq'));
    document.getElementById('testOpenRouterModelBtn')?.addEventListener('click', () => this.testDevelopmentModel('openrouter'));
    document.getElementById('testKimiModelBtn')?.addEventListener('click', () => this.testDevelopmentModel('kimi'));
    document.getElementById('refreshGroqModelsBtn')?.addEventListener('click', () => this.refreshAvailableModels('groq'));
    document.getElementById('refreshOpenRouterModelsBtn')?.addEventListener('click', () => this.refreshAvailableModels('openrouter'));
    document.getElementById('refreshKimiModelsBtn')?.addEventListener('click', () => this.refreshAvailableModels('kimi'));
    document.getElementById('refreshKimiDevModelsBtn')?.addEventListener('click', () => this.refreshAvailableModels('kimi'));
    document.getElementById('testVoiceBtn')?.addEventListener('click', () => this.testVoice());
    sel?.addEventListener('change', e => { this.provider = e.target.value; this.chatMode = 'normal'; updateActiveModel(); Settings.set('chatProvider', e.target.value); });
    updateActiveModel();
    document.getElementById('newChatBtn')?.addEventListener('click', () => this.startNewChat());

    attach?.addEventListener('click', () => fileIn?.click());
    fileIn?.addEventListener('change', e => {
      this.pendingFiles = Array.from(e.target.files);
      this.appendSystemMsg(`Attached ${this.pendingFiles.length} file(s).`);
    });

    const doSend = () => this.sendChat(input.value.trim());
    send?.addEventListener('click', doSend);
    input?.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); doSend(); }
    });

    const mic = document.getElementById('micBtn');
    mic?.addEventListener('click', () => this.toggleMic(mic, input));
  }

  async openDevelopmentChat() {
    const provider = document.getElementById('developmentProvider')?.value || 'openrouter';
    const modelId = this.modelSelectId(provider);
    const model = document.getElementById(modelId)?.value || PROVIDERS[provider].model;
    await Settings.set('developmentProvider', provider);
    await Settings.set('developmentModel', model);
    this.provider = provider;
    this.developmentProvider = provider;
    this.developmentModel = model;
    document.getElementById('providerSelect').value = provider;
    const activeModel = document.getElementById('activeModel');
    if (activeModel) activeModel.textContent = `${provider}: ${model}`;
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.view === 'chat'));
    this.switchView('chat');
    this.chatMode = 'development';
    await this.startNewChat(false);
  }

  async startNewChat(showMessage = true) {
    await dbClear('messages');
    this.messageHistory = [];
    const box = document.getElementById('chatBox');
    if (box) box.innerHTML = '';
    this.pendingFiles = [];
    if (showMessage) this.appendSystemMsg('New chat started with ' + this.provider + '.');
  }

  async testDevelopmentModel(providerId) {
    const modelId = this.modelSelectId(providerId);
    const resultId = providerId + 'ModelTestResult';
    const result = document.getElementById(resultId);
    const model = document.getElementById(modelId)?.value;
    if (!result || !model) return;
    result.textContent = 'Testing...';
    result.className = 'status-msg';
    const apiKey = await Settings.get(PROVIDERS[providerId].keyEnv, '');
    if (!apiKey) { result.textContent = 'API key missing.'; result.className = 'status-msg err'; return; }
    try {
      await chatCompletion(providerId, [{ role: 'user', content: 'Reply with OK.' }], apiKey, { model });
      result.textContent = `${model}: available`;
      result.className = 'status-msg ok';
    } catch (error) {
      result.textContent = `${model}: ${error.message}`;
      result.className = 'status-msg err';
    }
  }

  async testKimi() {
    const status = document.getElementById('kimiStatus');
    if (!status) return;
    const apiKey = await Settings.get('kimiKey', '');
    const model = this.providerModels.kimi;
    if (!apiKey) { status.textContent = 'Kimi API key missing.'; status.className = 'status-msg err'; return; }
    status.textContent = 'Testing Kimi...';
    status.className = 'status-msg';
    try {
      await chatCompletion('kimi', [{ role: 'user', content: 'Reply with OK.' }], apiKey, { model });
      status.textContent = `${model}: connection OK`;
      status.className = 'status-msg ok';
    } catch (error) {
      status.textContent = `${model}: ${error.message}`;
      status.className = 'status-msg err';
    }
  }

  modelSelectId(providerId) {
    const map = { groq: 'groqDevelopmentModel', openrouter: 'openrouterDevelopmentModel', kimi: 'kimiDevelopmentModel' };
    return map[providerId];
  }

  async refreshAvailableModels(providerId) {
    const selectId = this.modelSelectId(providerId);
    const select = document.getElementById(selectId);
    if (!select) return;
    const apiKey = await Settings.get(PROVIDERS[providerId].keyEnv, '');
    if (!apiKey) { select.innerHTML = '<option>API key missing</option>'; return; }
    try {
      const models = await listModels(providerId, apiKey);
      let available = models;
      if (providerId === 'openrouter') available = models.filter(model => model.id?.endsWith(':free'));
      if (!available.length) { select.innerHTML = '<option>No models available</option>'; return; }
      select.innerHTML = available.map(model => `<option value="${model.id}">${model.name || model.id}</option>`).join('');
      this.providerModels[providerId] = select.value;
    } catch (error) {
      select.innerHTML = `<option>Error: ${error.message}</option>`;
    }
  }

  async testVoice() {
    const status = document.getElementById('voiceStatus');
    if (!status) return;
    status.textContent = 'Testing voice...';
    try {
      await this.voice.speak('Voice is working.');
      status.textContent = this.voice.sttAvailable ? 'Voice output and speech input are available.' : 'Voice output is available; speech input is not supported in this app runtime.';
      status.className = 'status-msg ok';
    } catch (error) {
      status.textContent = error.message;
      status.className = 'status-msg err';
    }
  }

  appendMsg(role, text, files = []) {
    const box = document.getElementById('chatBox');
    if (!box) return;
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.textContent = text;
    if (files.length) {
      files.forEach(f => {
        const tag = document.createElement('span');
        tag.className = 'file-tag';
        tag.textContent = '📎 ' + f.name;
        div.appendChild(tag);
      });
    }
    if (role === 'assistant' && text && !text.startsWith('[System]')) {
      const actions = document.createElement('div');
      actions.className = 'msg-actions';
      const speakBtn = document.createElement('button');
      speakBtn.textContent = '🔊 Speak';
      speakBtn.addEventListener('click', () => this.voice.speak(text));
      actions.appendChild(speakBtn);
      const saveBtn = document.createElement('button');
      saveBtn.textContent = 'Save Response';
      saveBtn.addEventListener('click', () => this.saveResponse(text));
      actions.appendChild(saveBtn);
      if (this.extractCodeFiles(text).length > 1) {
        const zipBtn = document.createElement('button');
        zipBtn.textContent = 'Download ZIP';
        zipBtn.addEventListener('click', () => this.downloadResponseZip(text));
        actions.appendChild(zipBtn);
      }
      div.appendChild(actions);
    }
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  appendSystemMsg(text) {
    this.appendMsg('assistant', '[System] ' + text);
  }

  saveResponse(text) {
    const codeMatch = text.match(/```([\w-]*)\n([\s\S]*?)```/);
    const content = codeMatch ? codeMatch[2] : text;
    const extensionMap = { javascript: 'js', js: 'js', typescript: 'ts', ts: 'ts', python: 'py', html: 'html', css: 'css', json: 'json', bash: 'sh', sh: 'sh', sql: 'sql' };
    const extension = extensionMap[codeMatch?.[1]?.toLowerCase()] || 'txt';
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    this.download(blob, `kimi-response.${extension}`);
  }

  extractCodeFiles(text) {
    const files = [];
    const blocks = /```([^\n]*)\n([\s\S]*?)```/g;
    let match;
    while ((match = blocks.exec(text))) {
      const info = match[1].trim();
      const content = match[2].replace(/^\s*(?:\/\/|#|<!--)\s*(?:file|filename|path)\s*:\s*(\S+)\s*-->?\s*\n/i, '');
      const filenameMatch = info.match(/(?:file|filename|path)\s*=\s*["']?([^\s"']+)/i);
      const filename = filenameMatch?.[1] || (info.includes('/') || /\.[a-z0-9]+$/i.test(info) ? info.split(/\s+/).pop() : '');
      if (filename) files.push({ filename, content });
    }
    return files;
  }

  async downloadResponseZip(text) {
    const files = this.extractCodeFiles(text);
    if (!files.length) return;
    if (!window.JSZip) { alert('ZIP support is unavailable. Check your network connection and reload the app.'); return; }
    const zip = new JSZip();
    files.forEach(file => zip.file(file.filename, file.content));
    const blob = await zip.generateAsync({ type: 'blob' });
    this.download(blob, 'kimi-generated-files.zip');
  }

  toggleMic(micBtn, input) {
    if (this.voice.isListening) {
      this.voice.stopListening();
      micBtn.classList.remove('listening');
      return;
    }
    micBtn.classList.add('listening');
    const started = this.voice.startListening(
      (final, interim) => { input.value = final + interim; input.scrollTop = input.scrollHeight; },
      (final) => { micBtn.classList.remove('listening'); if (final.trim()) this.sendChat(final.trim()); },
      (err) => { micBtn.classList.remove('listening'); this.appendSystemMsg('Mic error: ' + err); }
    );
    if (!started) { micBtn.classList.remove('listening'); this.appendSystemMsg('Speech recognition not available'); }
  }

  async loadMessages() {
    const msgs = await dbGetAll('messages');
    this.messageHistory = msgs;
    msgs.forEach(m => this.appendMsg(m.role, m.content));
  }

  async saveMessage(role, content) {
    const msg = { id: Date.now(), role, content, ts: Date.now() };
    await dbPut('messages', msg);
    this.messageHistory.push(msg);
  }

  async sendChat(text) {
    const input = document.getElementById('chatInput');
    if (!text) return;
    input.value = '';
    this.appendMsg('user', text, this.pendingFiles);
    await this.saveMessage('user', text);

    const sysPrompt = await ContextLib.buildSystemPrompt(this.activeContextIds);
    const messages = [];
    const normalChatInstruction = this.chatMode === 'normal'
      ? 'Answer clearly and concisely. Lead with the direct answer, use short paragraphs or bullets, and avoid unnecessary background or repetition.'
      : '';
    const combinedSystemPrompt = [normalChatInstruction, sysPrompt].filter(Boolean).join('\n\n');
    if (combinedSystemPrompt) messages.push({ role: 'system', content: combinedSystemPrompt });
    const recentMessages = this.messageHistory.slice(-20).map(m => ({ role: m.role, content: m.content }));
    let contextSize = sysPrompt?.length || 0;
    const boundedMessages = [];
    for (let i = recentMessages.length - 1; i >= 0 && contextSize < 12000; i--) {
      const message = recentMessages[i];
      const remaining = 12000 - contextSize;
      const content = message.content.length > remaining ? message.content.slice(-remaining) : message.content;
      boundedMessages.unshift({ role: message.role, content });
      contextSize += content.length;
    }
    messages.push(...boundedMessages);

    const keyMap = { kimi: 'kimiKey', groq: 'groqKey', openrouter: 'openrouterKey' };
    const key = await Settings.get(keyMap[this.provider], '');

    if (!key && this.provider !== 'kimi') {
      this.appendMsg('assistant', 'No API key set for ' + this.provider + '. Add it in Settings.');
      return;
    }

    try {
      const model = this.chatMode === 'development' ? this.developmentModel : this.providerModels[this.provider];
      const resp = await chatCompletion(this.provider, messages, key, { model });
      this.lastUsedModel = `${this.provider}: ${model}`;
      await Settings.set('lastUsedModel', this.lastUsedModel);
      const lastUsedModel = document.getElementById('lastUsedModel');
      if (lastUsedModel) lastUsedModel.textContent = 'Last used: ' + this.lastUsedModel;
      this.appendMsg('assistant', resp);
      await this.saveMessage('assistant', resp);
      if (this.voice.autoRead) this.voice.speak(resp);
    } catch (e) {
      this.appendMsg('assistant', 'Error: ' + e.message);
    }
    this.pendingFiles = [];
  }

  /* ===== Projects ===== */
  bindProjects() {
    document.getElementById('newProjectBtn')?.addEventListener('click', () => this.createProject());
    document.getElementById('importProjectBtn')?.addEventListener('click', () => this.importProjects());
    document.getElementById('exportAllBtn')?.addEventListener('click', () => this.exportProjects());
  }

  async refreshProjects() {
    const list = document.getElementById('projectList');
    if (!list) return;
    list.innerHTML = '';
    const projects = await dbGetAll('projects');
    projects.forEach(p => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `<h4>${p.title || 'Untitled'}</h4><p>${p.description || ''}</p>
        <div class="actions">
          <button class="btn" data-id="${p.id}" data-action="open">Open</button>
          <button class="btn" data-id="${p.id}" data-action="export">Export</button>
          <button class="btn" data-id="${p.id}" data-action="delete">Delete</button>
        </div>`;
      card.querySelectorAll('button').forEach(b => {
        b.addEventListener('click', e => {
          e.stopPropagation();
          const id = Number(b.dataset.id);
          const action = b.dataset.action;
          if (action === 'open') this.openProject(id);
          else if (action === 'export') this.exportProject(id);
          else if (action === 'delete') this.deleteProject(id);
        });
      });
      list.appendChild(card);
    });
  }

  async createProject() {
    const title = prompt('Project title:');
    if (!title) return;
    const desc = prompt('Description (optional):') || '';
    await dbPut('projects', { id: Date.now(), title, description: desc, created: Date.now() });
    await this.refreshProjects();
  }

  async openProject(id) {
    const p = await dbGet('projects', id);
    if (!p) return;
    this.currentProject = p;
    this.appendSystemMsg(`Switched to project: ${p.title}`);
    this.switchView('chat');
  }

  async deleteProject(id) {
    if (!confirm('Delete this project?')) return;
    await dbDelete('projects', id);
    await this.refreshProjects();
  }

  async exportProject(id) {
    const p = await dbGet('projects', id);
    if (!p) return;
    const blob = new Blob([JSON.stringify(p, null, 2)], { type: 'application/json' });
    this.download(blob, `project-${p.id}.json`);
  }

  async exportProjects() {
    const all = await dbGetAll('projects');
    const blob = new Blob([JSON.stringify(all, null, 2)], { type: 'application/json' });
    this.download(blob, 'projects.json');
  }

  async importProjects() {
    const file = await this.pickFile('application/json');
    if (!file) return;
    const text = await file.text();
    const data = JSON.parse(text);
    const items = Array.isArray(data) ? data : [data];
    for (const item of items) {
      item.id = item.id || Date.now() + Math.floor(Math.random() * 1000);
      await dbPut('projects', item);
    }
    await this.refreshProjects();
  }

  /* ===== Prompts ===== */
  bindPrompts() {
    document.getElementById('newPromptBtn')?.addEventListener('click', () => this.createPrompt());
    document.getElementById('exportPromptsBtn')?.addEventListener('click', () => this.exportPrompts());
    document.getElementById('importPromptsBtn')?.addEventListener('click', () => this.importPrompts());
  }

  async refreshPrompts() {
    const list = document.getElementById('promptList');
    if (!list) return;
    list.innerHTML = '';
    const items = await Prompts.list();
    items.forEach(p => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `<h4>${p.title || 'Untitled'}</h4><p>${p.content?.slice(0, 80) || ''}...</p>
        <div class="actions">
          <button class="btn" data-id="${p.id}" data-action="use">Use</button>
          <button class="btn" data-id="${p.id}" data-action="delete">Delete</button>
        </div>`;
      card.querySelectorAll('button').forEach(b => {
        b.addEventListener('click', e => {
          e.stopPropagation();
          const id = Number(b.dataset.id);
          if (b.dataset.action === 'use') this.usePrompt(id);
          else if (b.dataset.action === 'delete') this.deletePrompt(id);
        });
      });
      list.appendChild(card);
    });
  }

  async createPrompt() {
    const title = prompt('Prompt title:');
    if (!title) return;
    const content = prompt('Prompt text:') || '';
    await Prompts.add({ title, content });
    await this.refreshPrompts();
  }

  async usePrompt(id) {
    const p = await Prompts.get(id);
    if (!p) return;
    const input = document.getElementById('chatInput');
    if (input) input.value = p.content;
    this.switchView('chat');
  }

  async deletePrompt(id) {
    if (!confirm('Delete prompt?')) return;
    await Prompts.remove(id);
    await this.refreshPrompts();
  }

  async exportPrompts() {
    const all = await Prompts.list();
    const blob = new Blob([JSON.stringify(all, null, 2)], { type: 'application/json' });
    this.download(blob, 'prompts.json');
  }

  async importPrompts() {
    const file = await this.pickFile('application/json');
    if (!file) return;
    const text = await file.text();
    const data = JSON.parse(text);
    const items = Array.isArray(data) ? data : [data];
    for (const item of items) await Prompts.add(item);
    await this.refreshPrompts();
  }

  /* ===== Notes ===== */
  bindNotes() {
    document.getElementById('newNoteBtn')?.addEventListener('click', () => this.createNote());
    document.getElementById('exportNotesBtn')?.addEventListener('click', () => this.exportNotes());
    document.getElementById('importNotesBtn')?.addEventListener('click', () => this.importNotes());
  }

  async refreshNotes() {
    const list = document.getElementById('noteList');
    if (!list) return;
    list.innerHTML = '';
    const items = await Notes.list();
    items.forEach(n => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `<h4>${n.title || 'Untitled'}</h4><p>${n.content?.slice(0, 80) || ''}...</p>
        <div class="actions">
          <button class="btn" data-id="${n.id}" data-action="view">View</button>
          <button class="btn" data-id="${n.id}" data-action="delete">Delete</button>
        </div>`;
      card.querySelectorAll('button').forEach(b => {
        b.addEventListener('click', e => {
          e.stopPropagation();
          const id = Number(b.dataset.id);
          if (b.dataset.action === 'view') this.viewNote(id);
          else if (b.dataset.action === 'delete') this.deleteNote(id);
        });
      });
      list.appendChild(card);
    });
  }

  async createNote() {
    const title = prompt('Note title:');
    if (!title) return;
    const content = prompt('Note content:') || '';
    await Notes.add({ title, content });
    await this.refreshNotes();
  }

  viewNote(id) {
    Notes.get(id).then(n => alert(n?.content || 'Not found'));
  }

  async deleteNote(id) {
    if (!confirm('Delete note?')) return;
    await Notes.remove(id);
    await this.refreshNotes();
  }

  async exportNotes() {
    const all = await Notes.list();
    const blob = new Blob([JSON.stringify(all, null, 2)], { type: 'application/json' });
    this.download(blob, 'notes.json');
  }

  async importNotes() {
    const file = await this.pickFile('application/json');
    if (!file) return;
    const text = await file.text();
    const data = JSON.parse(text);
    const items = Array.isArray(data) ? data : [data];
    for (const item of items) await Notes.add(item);
    await this.refreshNotes();
  }

  /* ===== Context Library ===== */
  bindContext() {
    document.getElementById('addContextBtn')?.addEventListener('click', () => this.addContext());
    document.getElementById('exportContextBtn')?.addEventListener('click', () => this.exportContext());
    document.getElementById('importContextBtn')?.addEventListener('click', () => this.importContext());
  }

  async refreshContext() {
    const list = document.getElementById('contextList');
    if (!list) return;
    list.innerHTML = '';
    const items = await ContextLib.list();
    items.forEach(c => {
      const card = document.createElement('div');
      card.className = 'card';
      const active = this.activeContextIds.includes(c.id);
      card.innerHTML = `<h4>${c.title || 'Untitled'}</h4><p>${c.content?.slice(0, 80) || ''}...</p>
        <div class="actions">
          <button class="btn" data-id="${c.id}" data-action="toggle">${active ? 'Deactivate' : 'Activate'}</button>
          <button class="btn" data-id="${c.id}" data-action="delete">Delete</button>
        </div>`;
      card.querySelectorAll('button').forEach(b => {
        b.addEventListener('click', e => {
          e.stopPropagation();
          const id = Number(b.dataset.id);
          if (b.dataset.action === 'toggle') this.toggleContext(id);
          else if (b.dataset.action === 'delete') this.deleteContext(id);
        });
      });
      list.appendChild(card);
    });
  }

  async addContext() {
    const title = prompt('Context title:');
    if (!title) return;
    const content = prompt('Context content:') || '';
    await ContextLib.add({ title, content });
    await this.refreshContext();
  }

  toggleContext(id) {
    const idx = this.activeContextIds.indexOf(id);
    if (idx >= 0) this.activeContextIds.splice(idx, 1);
    else this.activeContextIds.push(id);
    this.refreshContext();
  }

  async deleteContext(id) {
    if (!confirm('Delete context?')) return;
    await ContextLib.remove(id);
    const idx = this.activeContextIds.indexOf(id);
    if (idx >= 0) this.activeContextIds.splice(idx, 1);
    await this.refreshContext();
  }

  async exportContext() {
    const all = await ContextLib.list();
    const blob = new Blob([JSON.stringify(all, null, 2)], { type: 'application/json' });
    this.download(blob, 'context.json');
  }

  async importContext() {
    const file = await this.pickFile('application/json');
    if (!file) return;
    const text = await file.text();
    const data = JSON.parse(text);
    const items = Array.isArray(data) ? data : [data];
    for (const item of items) await ContextLib.add(item);
    await this.refreshContext();
  }

  /* ===== Sync ===== */
  bindSync() {
    document.getElementById('saveGitHubBtn')?.addEventListener('click', () => this.saveGitHub());
    document.getElementById('pushToGitHubBtn')?.addEventListener('click', () => this.pushGitHub());
    document.getElementById('pullFromGitHubBtn')?.addEventListener('click', () => this.pullGitHub());
  }

  async saveGitHub() {
    const token = document.getElementById('githubToken')?.value.trim() || '';
    const repo = document.getElementById('githubRepo')?.value.trim() || '';
    const branch = document.getElementById('githubBranch')?.value.trim() || 'main';
    await Settings.set('githubToken', token);
    await Settings.set('githubRepo', repo);
    await Settings.set('githubBranch', branch);
    this.github = token && repo ? new GitHubSync(token, repo, branch) : null;
    this.logSync('GitHub credentials saved.');
  }

  async pushGitHub() {
    if (!this.github) { this.logSync('Configure GitHub first.', true); return; }
    try {
      const ts = await this.github.pushSnapshot();
      this.logSync('Pushed snapshot at ' + ts);
    } catch (e) { this.logSync('Push failed: ' + e.message, true); }
  }

  async pullGitHub() {
    if (!this.github) { this.logSync('Configure GitHub first.', true); return; }
    try {
      await this.github.pullSnapshot();
      this.logSync('Pulled snapshot. Reloading...');
      setTimeout(() => location.reload(), 800);
    } catch (e) { this.logSync('Pull failed: ' + e.message, true); }
  }

  logSync(msg, isError = false) {
    const box = document.getElementById('syncLog');
    if (!box) return;
    const line = document.createElement('div');
    line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    line.style.color = isError ? 'var(--danger)' : 'inherit';
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
  }

  /* ===== Integrations ===== */
  bindIntegrations() {
    document.querySelectorAll('.integration-tabs .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.integration-tabs .tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab)?.classList.add('active');
      });
    });

    document.getElementById('saveWpBtn')?.addEventListener('click', () => this.saveWordPress());
    document.getElementById('testWpBtn')?.addEventListener('click', () => this.testWordPress());

    document.getElementById('saveGoogleBtn')?.addEventListener('click', () => this.saveGoogle());
    document.getElementById('authGoogleBtn')?.addEventListener('click', () => this.authGoogle());
    document.getElementById('revokeGoogleBtn')?.addEventListener('click', () => this.revokeGoogle());

    document.getElementById('saveAccountingBtn')?.addEventListener('click', () => this.saveAccounting());

    document.getElementById('saveOpenclawBtn')?.addEventListener('click', () => this.saveOpenclaw());
    document.getElementById('enableOpenclawBtn')?.addEventListener('click', () => this.enableOpenclaw());
  }

  initIntegrations() {
    this.loadWordPress();
    this.loadGoogle();
    this.loadAccounting();
    this.loadOpenclaw();
  }

  refreshIntegrations() {
    this.refreshWordPressUI();
    this.refreshGoogleUI();
    this.refreshAccountingUI();
    this.refreshOpenclawUI();
  }

  /* WordPress */
  async saveWordPress() {
    const url = document.getElementById('wpUrl')?.value.trim() || '';
    const user = document.getElementById('wpUser')?.value.trim() || '';
    const pass = document.getElementById('wpPass')?.value || '';
    await Settings.set('wpUrl', url);
    await Settings.set('wpUser', user);
    await Settings.set('wpPass', pass);
    this.wpClient = url && user && pass ? new WordPressClient(url, user, pass) : null;
    this.refreshWordPressUI();
  }

  async loadWordPress() {
    const url = await Settings.get('wpUrl', '');
    const user = await Settings.get('wpUser', '');
    const pass = await Settings.get('wpPass', '');
    if (url) document.getElementById('wpUrl').value = url;
    if (user) document.getElementById('wpUser').value = user;
    if (pass) document.getElementById('wpPass').value = pass;
    this.wpClient = url && user && pass ? new WordPressClient(url, user, pass) : null;
  }

  async testWordPress() {
    const status = document.getElementById('wpStatus');
    if (!this.wpClient) { status.textContent = 'Configure WordPress first.'; status.className = 'status-msg err'; return; }
    try {
      const me = await this.wpClient.test();
      status.textContent = 'Connected as ' + (me.name || me.slug || me.username || 'user');
      status.className = 'status-msg ok';
      const posts = await this.wpClient.getPosts(5);
      const list = document.getElementById('wpPosts');
      list.innerHTML = '';
      posts.forEach(post => {
        const div = document.createElement('div');
        div.className = 'card';
        div.innerHTML = `<h4>${post.title?.rendered || 'Untitled'}</h4><p>${post.excerpt?.rendered?.replace(/<[^>]+>/g, '').slice(0, 100) || ''}...</p>`;
        list.appendChild(div);
      });
    } catch (e) {
      status.textContent = 'Error: ' + e.message;
      status.className = 'status-msg err';
    }
  }

  refreshWordPressUI() {
    const status = document.getElementById('wpStatus');
    if (!status) return;
    if (this.wpClient) { status.textContent = 'WordPress configured.'; status.className = 'status-msg ok'; }
    else { status.textContent = 'WordPress not configured.'; status.className = 'status-msg'; }
  }

  /* Google */
  async saveGoogle() {
    const clientId = document.getElementById('googleClientId')?.value.trim() || '';
    await Settings.set('googleClientId', clientId);
    this.googleClient = clientId ? new GoogleClient(clientId) : null;
    this.refreshGoogleUI();
  }

  async loadGoogle() {
    const clientId = await Settings.get('googleClientId', '');
    if (clientId) document.getElementById('googleClientId').value = clientId;
    this.googleClient = clientId ? new GoogleClient(clientId) : null;
  }

  async authGoogle() {
    if (!this.googleClient) { alert('Save Client ID first.'); return; }
    await this.googleClient.auth();
  }

  async revokeGoogle() {
    if (this.googleClient) await this.googleClient.revoke();
    this.refreshGoogleUI();
  }

  async loadGoogleData() {
    if (!this.googleClient) return;
    const panel = document.getElementById('googleData');
    if (!panel) return;
    panel.innerHTML = '<p>Loading...</p>';
    try {
      const [emails, events, files] = await Promise.all([
        this.googleClient.getEmails(3).catch(() => []),
        this.googleClient.getEvents(3).catch(() => []),
        this.googleClient.getDriveFiles(3).catch(() => [])
      ]);
      let html = '';
      if (emails.length) {
        html += '<div class="card"><h4>Recent Emails</h4>';
        emails.forEach(m => {
          const subj = m.payload?.headers?.find(h => h.name === 'Subject')?.value || 'No subject';
          html += `<p>• ${subj}</p>`;
        });
        html += '</div>';
      }
      if (events.length) {
        html += '<div class="card"><h4>Upcoming Events</h4>';
        events.forEach(ev => html += `<p>• ${ev.summary || 'Event'} — ${ev.start?.dateTime?.slice(0, 16) || ev.start?.date || ''}</p>`);
        html += '</div>';
      }
      if (files.length) {
        html += '<div class="card"><h4>Drive Files</h4>';
        files.forEach(f => html += `<p>• ${f.name}</p>`);
        html += '</div>';
      }
      panel.innerHTML = html || '<p class="hint">No data found.</p>';
    } catch (e) {
      panel.innerHTML = '<p class="err">' + e.message + '</p>';
    }
  }

  refreshGoogleUI() {
    const status = document.getElementById('googleStatus');
    const token = localStorage.getItem('google_token');
    if (!this.googleClient) { status.textContent = 'Google not configured.'; status.className = 'status-msg'; }
    else if (token) { status.textContent = 'Google authorized.'; status.className = 'status-msg ok'; this.loadGoogleData(); }
    else { status.textContent = 'Google configured but not authorized.'; status.className = 'status-msg'; }
  }

  /* Accounting */
  async saveAccounting() {
    const provider = document.getElementById('accountingProvider')?.value || '';
    await Settings.set('accountingProvider', provider);
    this.accounting = provider ? new AccountingClient(provider) : null;
    this.refreshAccountingUI();
  }

  async loadAccounting() {
    const provider = await Settings.get('accountingProvider', '');
    const sel = document.getElementById('accountingProvider');
    if (sel && provider) sel.value = provider;
    this.accounting = provider ? new AccountingClient(provider) : null;
  }

  refreshAccountingUI() {
    const status = document.getElementById('accountingStatus');
    const config = document.getElementById('accountingConfig');
    if (!status) return;
    if (this.accounting) {
      const info = this.accounting.getInfo();
      status.textContent = `Selected: ${info?.name || this.accounting.provider}`;
      status.className = 'status-msg ok';
      if (config) config.innerHTML = `<p class="hint">API: ${info?.api || 'N/A'} — <a href="${info?.url || '#'}"" target="_blank">Docs</a></p>`;
    } else {
      status.textContent = 'No accounting provider selected.';
      status.className = 'status-msg';
      if (config) config.innerHTML = '';
    }
  }

  /* OpenClaw */
  async testOpenclaw() {
    const status = document.getElementById('openclawStatus');
    if (!status) return;
    const url = (document.getElementById('openclawUrl')?.value || PROVIDERS.openclaw.base).replace(/\/$/, '');
    const token = document.getElementById('openclawKey')?.value || '';
    status.textContent = 'Connecting to OpenClaw gateway...';
    status.className = 'status-msg';
    try {
      const res = await fetch(url + '/models', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      if (!res.ok) throw new Error((await res.text().catch(() => res.statusText)));
      const data = await res.json();
      const models = (data.data || []).map(m => m.id).join(', ');
      status.textContent = 'Connected. Models: ' + (models || 'none');
      status.className = 'status-msg ok';
    } catch (e) {
      status.textContent = 'Connection failed: ' + e.message;
      status.className = 'status-msg err';
    }
  }

  async loadOpenclaw() {
    const url = await Settings.get('openclawUrl', PROVIDERS.openclaw.base);
    document.getElementById('openclawUrl').value = url;
    PROVIDERS.openclaw.base = url;
  }

  /* ===== Settings ===== */
  bindSettings() {
    document.getElementById('saveSettingsBtn')?.addEventListener('click', () => this.saveSettings());
    document.getElementById('clearDataBtn')?.addEventListener('click', () => this.clearAllData());
    document.getElementById('exportDataBtn')?.addEventListener('click', () => this.exportAllData());
    document.getElementById('themeSelect')?.addEventListener('change', e => this.setTheme(e.target.value));
    document.getElementById('voiceEnabled')?.addEventListener('change', e => { this.voice.enabled = e.target.checked; });
    document.getElementById('voiceAutoRead')?.addEventListener('change', e => { this.voice.autoRead = e.target.checked; });
    document.getElementById('voiceSelect')?.addEventListener('change', e => { this.voice.voice = e.target.value; });
    document.getElementById('kimiModel')?.addEventListener('change', e => { this.providerModels.kimi = e.target.value; });
    document.getElementById('testKimiBtn')?.addEventListener('click', () => this.testKimi());
    document.getElementById('refreshKimiModelsBtn')?.addEventListener('click', () => this.refreshAvailableModels('kimi'));
    document.getElementById('openKimiDashboardBtn')?.addEventListener('click', () => window.open('https://platform.moonshot.cn/', '_blank'));
    document.getElementById('groqModel')?.addEventListener('change', e => { this.providerModels.groq = e.target.value; });
    document.getElementById('openrouterModel')?.addEventListener('change', e => { this.providerModels.openrouter = e.target.value; });
    document.getElementById('openclawModel')?.addEventListener('change', e => { this.providerModels.openclaw = e.target.value; });
    document.getElementById('openclawViewModel')?.addEventListener('change', e => { this.providerModels.openclaw = e.target.value; document.getElementById('openclawModel').value = e.target.value; });
    document.getElementById('testOpenclawBtn')?.addEventListener('click', () => this.testOpenclaw());
    document.getElementById('refreshOpenclawModelsBtn')?.addEventListener('click', () => this.refreshAvailableModels('openclaw'));
    this.bindColorControls();
  }

  bindColorControls() {
    document.querySelectorAll('.color-control').forEach(control => {
      const picker = control.querySelector('input[type="color"]');
      const hex = control.querySelector('input[type="text"]');
      const slider = control.querySelector('input[type="range"]');
      const setBaseColor = value => {
        if (!/^#[0-9a-f]{6}$/i.test(value)) return;
        control.dataset.baseColor = value.toLowerCase();
        picker.value = control.dataset.baseColor;
        hex.value = control.dataset.baseColor;
        slider.value = 50;
        this.applyColor(control, 50);
      };
      picker?.addEventListener('input', e => setBaseColor(e.target.value));
      hex?.addEventListener('change', e => setBaseColor(e.target.value.trim()));
      slider?.addEventListener('input', e => this.applyColor(control, Number(e.target.value)));
    });
  }

  applyColor(control, lightness) {
    const base = control.dataset.baseColor || '#000000';
    const color = this.adjustColor(base, lightness);
    control.dataset.currentColor = color;
    document.documentElement.style.setProperty(control.dataset.colorVar, color);
    const hex = control.querySelector('input[type="text"]');
    if (hex) hex.value = color;
  }

  adjustColor(hex, lightness) {
    const value = hex.slice(1);
    const rgb = [0, 2, 4].map(index => parseInt(value.slice(index, index + 2), 16));
    const amount = (lightness - 50) / 50;
    const target = amount >= 0 ? 255 : 0;
    const factor = Math.abs(amount);
    return '#' + rgb.map(channel => Math.round(channel + (target - channel) * factor).toString(16).padStart(2, '0')).join('');
  }

  async loadSettings() {
    const buildInfo = document.getElementById('buildInfo');
    if (buildInfo) buildInfo.textContent = 'Build ' + APP_BUILD;
    this.lastUsedModel = await Settings.get('lastUsedModel', 'None yet');
    const lastUsedModel = document.getElementById('lastUsedModel');
    if (lastUsedModel) lastUsedModel.textContent = 'Last used: ' + this.lastUsedModel;
    const savedProvider = await Settings.get('chatProvider', 'groq');
    this.provider = PROVIDERS[savedProvider] ? savedProvider : 'groq';
    const providerSelect = document.getElementById('providerSelect');
    if (providerSelect) providerSelect.value = this.provider;
    document.getElementById('kimiKey').value = await Settings.get('kimiKey', '');
    document.getElementById('groqKey').value = await Settings.get('groqKey', '');
    document.getElementById('openrouterKey').value = await Settings.get('openrouterKey', '');
    document.getElementById('openclawKey').value = await Settings.get('openclawKey', '');
    document.getElementById('openclawUrl').value = await Settings.get('openclawUrl', PROVIDERS.openclaw.base);
    PROVIDERS.openclaw.base = document.getElementById('openclawUrl').value || PROVIDERS.openclaw.base;
    const savedKimiModel = await Settings.get('kimiModel', PROVIDERS.kimi.model);
    const savedGroqModel = await Settings.get('groqModel', PROVIDERS.groq.model);
    const savedOpenRouterModel = await Settings.get('openrouterModel', PROVIDERS.openrouter.model);
    const savedOpenclawModel = await Settings.get('openclawModel', PROVIDERS.openclaw.model);
    this.providerModels.kimi = PROVIDERS.kimi.models.includes(savedKimiModel) ? savedKimiModel : PROVIDERS.kimi.model;
    this.providerModels.groq = PROVIDERS.groq.models.includes(savedGroqModel) ? savedGroqModel : PROVIDERS.groq.model;
    this.providerModels.openrouter = PROVIDERS.openrouter.models.includes(savedOpenRouterModel) ? savedOpenRouterModel : PROVIDERS.openrouter.model;
    this.providerModels.openclaw = PROVIDERS.openclaw.models.includes(savedOpenclawModel) ? savedOpenclawModel : PROVIDERS.openclaw.model;
    document.getElementById('kimiModel').value = this.providerModels.kimi;
    document.getElementById('groqModel').value = this.providerModels.groq;
    document.getElementById('openrouterModel').value = this.providerModels.openrouter;
    document.getElementById('openclawModel').value = this.providerModels.openclaw;
    document.getElementById('openclawViewModel').value = this.providerModels.openclaw;
    const activeModel = document.getElementById('activeModel');
    if (activeModel) activeModel.textContent = `${this.provider}: ${this.providerModels[this.provider]}`;
    const savedDevelopmentProvider = await Settings.get('developmentProvider', 'openrouter');
    this.developmentProvider = PROVIDERS[savedDevelopmentProvider] ? savedDevelopmentProvider : 'openrouter';
    const savedDevelopmentModel = await Settings.get('developmentModel', PROVIDERS[this.developmentProvider].model);
    this.developmentModel = PROVIDERS[this.developmentProvider].models.includes(savedDevelopmentModel) ? savedDevelopmentModel : PROVIDERS[this.developmentProvider].model;
    document.getElementById('developmentProvider').value = this.developmentProvider;
    document.getElementById('groqDevelopmentModel').value = PROVIDERS.groq.models.includes(this.developmentModel) ? this.developmentModel : PROVIDERS.groq.model;
    document.getElementById('openrouterDevelopmentModel').value = PROVIDERS.openrouter.models.includes(this.developmentModel) ? this.developmentModel : PROVIDERS.openrouter.model;
    document.getElementById('kimiDevelopmentModel').value = PROVIDERS.kimi.models.includes(this.developmentModel) ? this.developmentModel : PROVIDERS.kimi.model;
    document.getElementById('githubToken').value = await Settings.get('githubToken', '');
    document.getElementById('githubRepo').value = await Settings.get('githubRepo', '');
    document.getElementById('githubBranch').value = await Settings.get('githubBranch', 'main');
    const theme = await Settings.get('theme', 'dark');
    document.getElementById('themeSelect').value = theme;
    this.setTheme(theme);
    const customColors = { '--bg': '#081426', '--surface': '#10233d', '--accent': '#4ea8de', '--text': '#e8e8e8', '--muted': '#9aa7b8' };
    for (const control of document.querySelectorAll('.color-control')) {
      const color = await Settings.get(control.dataset.colorKey, customColors[control.dataset.colorVar]);
      control.dataset.baseColor = color;
      control.querySelector('input[type="color"]').value = color;
      control.querySelector('input[type="text"]').value = color;
      this.applyColor(control, 50);
    }
    const autoSync = await Settings.get('autoSync', false);
    document.getElementById('autoSync').checked = autoSync;

    const vEnabled = await Settings.get('voiceEnabled', false);
    document.getElementById('voiceEnabled').checked = vEnabled;
    this.voice.enabled = vEnabled;

    const vAuto = await Settings.get('voiceAutoRead', false);
    document.getElementById('voiceAutoRead').checked = vAuto;
    this.voice.autoRead = vAuto;

    const vChoice = await Settings.get('voiceChoice', 'Arista-PlayAI');
    document.getElementById('voiceSelect').value = vChoice;
    this.voice.voice = vChoice;

    const groqKey = await Settings.get('groqKey', '');
    this.voice.setKey(groqKey);

    const ght = await Settings.get('githubToken', '');
    const ghr = await Settings.get('githubRepo', '');
    const ghb = await Settings.get('githubBranch', 'main');
    this.github = ght && ghr ? new GitHubSync(ght, ghr, ghb) : null;
  }

  async saveSettings() {
    await Settings.set('kimiKey', document.getElementById('kimiKey')?.value || '');
    await Settings.set('groqKey', document.getElementById('groqKey')?.value || '');
    await Settings.set('openrouterKey', document.getElementById('openrouterKey')?.value || '');
    await Settings.set('openclawKey', document.getElementById('openclawKey')?.value || '');
    const openclawUrl = document.getElementById('openclawUrl')?.value || PROVIDERS.openclaw.base;
    await Settings.set('openclawUrl', openclawUrl);
    PROVIDERS.openclaw.base = openclawUrl;
    await Promise.all(Array.from(document.querySelectorAll('.color-control'), control => Settings.set(control.dataset.colorKey, control.dataset.currentColor || control.dataset.baseColor || control.querySelector('input[type="color"]').value)));
    await Settings.set('kimiModel', document.getElementById('kimiModel')?.value || PROVIDERS.kimi.model);
    await Settings.set('groqModel', document.getElementById('groqModel')?.value || PROVIDERS.groq.model);
    await Settings.set('openrouterModel', document.getElementById('openrouterModel')?.value || PROVIDERS.openrouter.model);
    await Settings.set('openclawModel', document.getElementById('openclawModel')?.value || PROVIDERS.openclaw.model);
    await Settings.set('theme', document.getElementById('themeSelect')?.value || 'dark');
    await Settings.set('autoSync', document.getElementById('autoSync')?.checked || false);
    await Settings.set('voiceEnabled', document.getElementById('voiceEnabled')?.checked || false);
    await Settings.set('voiceAutoRead', document.getElementById('voiceAutoRead')?.checked || false);
    await Settings.set('voiceChoice', document.getElementById('voiceSelect')?.value || 'Arista-PlayAI');
    await this.voice.saveSettings();
    this.voice.setKey(document.getElementById('groqKey')?.value || '');
    await this.saveGitHub();
    alert('Settings saved.');
  }

  setTheme(theme) {
    document.body.classList.toggle('light', theme === 'light');
  }

  async clearAllData() {
    if (!confirm('WARNING: This deletes ALL local data. Continue?')) return;
    for (const s of ['projects', 'prompts', 'notes', 'context', 'settings', 'messages']) await dbClear(s);
    localStorage.clear();
    alert('All data cleared. Reloading...');
    location.reload();
  }

  async exportAllData() {
    const all = {};
    for (const s of ['projects', 'prompts', 'notes', 'context', 'settings', 'messages']) all[s] = await dbGetAll(s);
    const blob = new Blob([JSON.stringify(all, null, 2)], { type: 'application/json' });
    this.download(blob, 'kimi-console-backup.json');
  }

  /* ===== Utilities ===== */
  download(blob, filename) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  pickFile(accept) {
    return new Promise(resolve => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = accept;
      input.onchange = () => resolve(input.files[0] || null);
      input.click();
    });
  }
}

/* ===== Boot ===== */
document.addEventListener('DOMContentLoaded', () => { window.app = new App(); });
