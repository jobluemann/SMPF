/**
 * Kimi Console — Context Library Manager
 */
const ContextLib = {
  async list() { return dbGetAll('context'); },

  async add(item) {
    item.id = item.id || Date.now();
    item.updated = Date.now();
    await dbPut('context', item);
    return item;
  },

  async remove(id) { await dbDelete('context', id); },

  async getById(id) { return dbGet('context', id); },

  buildSystemPrompt(activeIds = []) {
    return activeIds.map(id => this.getById(id)).filter(Boolean).map(c => c.content).join('\n\n');
  }
};
