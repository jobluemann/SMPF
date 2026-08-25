/**
 * Kimi Console — AI Provider Router
 * Supports Kimi (Moonshot), Groq (free tier), and OpenRouter (free tier).
 */
const PROVIDERS = {
  kimi: {
    name: 'Kimi',
    base: 'https://api.moonshot.cn/v1',
    model: 'moonshot-v1-8k',
    keyEnv: 'kimiKey'
  },
  groq: {
    name: 'Groq',
    base: 'https://api.groq.com/openai/v1',
    model: 'qwen/qwen3-32b',
    models: ['qwen/qwen3-32b', 'moonshotai/kimi-k2-instruct'],
    keyEnv: 'groqKey'
  },
  openrouter: {
    name: 'OpenRouter',
    base: 'https://openrouter.ai/api/v1',
    model: 'qwen/qwen3-235b-a22b:free',
    models: ['qwen/qwen3-235b-a22b:free', 'deepseek/deepseek-r1-0528:free'],
    keyEnv: 'openrouterKey'
  }
};

const GROQ_TTS = {
  base: 'https://api.groq.com/openai/v1',
  model: 'playai-tts',
  defaultVoice: 'Arista-PlayAI'
};

async function chatCompletion(providerId, messages, apiKey, opts = {}) {
  const p = PROVIDERS[providerId];
  if (!p) throw new Error('Unknown provider: ' + providerId);
  if (!apiKey) throw new Error('API key required for ' + p.name);

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + apiKey
  };
  if (providerId === 'openrouter') {
    headers['HTTP-Referer'] = location.href;
    headers['X-Title'] = 'Kimi Console';
  }

  const body = {
    model: opts.model || p.model,
    messages: messages.map(m => ({ role: m.role, content: m.content })),
    stream: !!opts.stream,
    temperature: opts.temperature ?? 0.7
  };

  const res = await fetch(p.base + '/chat/completions', {
    method: 'POST',
    headers,
    body: JSON.stringify(body)
  });

  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText);
    throw new Error(p.name + ' error: ' + err);
  }

  if (opts.stream) return res.body;
  const data = await res.json();
  return data.choices?.[0]?.message?.content ?? '';
}

async function listModels(providerId, apiKey) {
  const p = PROVIDERS[providerId];
  if (!p) return [];
  const res = await fetch(p.base + '/models', {
    headers: { 'Authorization': 'Bearer ' + apiKey }
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.data || [];
}
