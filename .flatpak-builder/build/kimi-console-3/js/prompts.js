/**
 * Kimi Console — Prompt Manager
 */
const Prompts = {
  async list() { return dbGetAll('prompts'); },

  async add(p) {
    p.id = p.id || Date.now();
    p.updated = Date.now();
    await dbPut('prompts', p);
    return p;
  },

  async remove(id) { await dbDelete('prompts', id); },

  async get(id) { return dbGet('prompts', id); }
};
