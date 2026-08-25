/**
 * Kimi Console — Notes Manager
 */
const Notes = {
  async list() { return dbGetAll('notes'); },

  async add(n) {
    n.id = n.id || Date.now();
    n.updated = Date.now();
    await dbPut('notes', n);
    return n;
  },

  async remove(id) { await dbDelete('notes', id); },

  async get(id) { return dbGet('notes', id); }
};
