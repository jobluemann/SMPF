/**
 * Kimi Console — Voice Layer (Phase 4)
 * Groq Orpheus TTS (free tier) + Browser-native Speech-to-Text
 */

/* ===== Groq TTS ===== */
class GroqTTS {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.base = 'https://api.groq.com/openai/v1';
    this.model = 'playai-tts';  // Groq TTS model (Orpheus-based)
    this.voice = 'Arista-PlayAI';
    this.audio = null;
    this.onPlay = null;
    this.onEnd = null;
  }

  async speak(text, voice) {
    if (!this.apiKey) throw new Error('Groq API key not set');
    this.stop();

    const res = await fetch(this.base + '/audio/speech', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + this.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: this.model,
        voice: voice || this.voice,
        input: text,
        response_format: 'mp3'
      })
    });

    if (!res.ok) {
      const err = await res.text().catch(() => res.statusText);
      throw new Error('TTS error: ' + err);
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    this.audio = new Audio(url);
    this.audio.onended = () => {
      URL.revokeObjectURL(url);
      if (this.onEnd) this.onEnd();
    };
    this.audio.onplay = () => { if (this.onPlay) this.onPlay(); };
    await this.audio.play();
    return this.audio;
  }

  stop() {
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
      this.audio = null;
    }
  }

  get isPlaying() {
    return this.audio && !this.audio.paused && !this.audio.ended;
  }
}

/* ===== Browser Speech-to-Text ===== */
class SpeechToText {
  constructor() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.available = !!SR;
    this.recognizer = this.available ? new SR() : null;
    this.isListening = false;
    this.onResult = null;
    this.onError = null;
    this.onEnd = null;
    this._finalTranscript = '';

    if (this.recognizer) {
      this.recognizer.continuous = true;
      this.recognizer.interimResults = true;
      this.recognizer.lang = 'en-US';

      this.recognizer.onresult = (e) => {
        let interim = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const transcript = e.results[i][0].transcript;
          if (e.results[i].isFinal) this._finalTranscript += transcript;
          else interim += transcript;
        }
        if (this.onResult) this.onResult(this._finalTranscript, interim);
      };

      this.recognizer.onerror = (e) => {
        if (this.onError) this.onError(e.error);
      };

      this.recognizer.onend = () => {
        this.isListening = false;
        if (this.onEnd) this.onEnd(this._finalTranscript);
      };
    }
  }

  start() {
    if (!this.recognizer) return false;
    this._finalTranscript = '';
    this.isListening = true;
    try { this.recognizer.start(); } catch (e) { return false; }
    return true;
  }

  stop() {
    if (!this.recognizer) return;
    this.recognizer.stop();
    this.isListening = false;
  }
}

/* ===== Voice Manager ===== */
class VoiceManager {
  constructor() {
    this.tts = null;
    this.stt = new SpeechToText();
    this.enabled = false;
    this.autoRead = false;
    this.voice = 'Arista-PlayAI';
    this.groqKey = '';
  }

  async init() {
    this.groqKey = await Settings.get('groqKey', '');
    this.enabled = await Settings.get('voiceEnabled', false);
    this.autoRead = await Settings.get('voiceAutoRead', false);
    this.voice = await Settings.get('voiceChoice', 'Arista-PlayAI');
    if (this.groqKey) this.tts = new GroqTTS(this.groqKey);
  }

  async saveSettings() {
    await Settings.set('voiceEnabled', this.enabled);
    await Settings.set('voiceAutoRead', this.autoRead);
    await Settings.set('voiceChoice', this.voice);
  }

  setKey(key) {
    this.groqKey = key;
    this.tts = key ? new GroqTTS(key) : null;
  }

  async speak(text) {
    if (!this.enabled || !this.tts) return;
    try { await this.tts.speak(text, this.voice); }
    catch (e) { console.warn('TTS failed:', e.message); }
  }

  stop() {
    if (this.tts) this.tts.stop();
  }

  startListening(onResult, onEnd, onError) {
    if (!this.stt.available) { if (onError) onError('Speech recognition not supported in this browser'); return false; }
    this.stt.onResult = onResult;
    this.stt.onEnd = onEnd;
    this.stt.onError = onError;
    return this.stt.start();
  }

  stopListening() {
    this.stt.stop();
  }

  get isListening() { return this.stt.isListening; }
  get isSpeaking() { return this.tts?.isPlaying || false; }
  get sttAvailable() { return this.stt.available; }
}

const VOICES = [
  { id: 'Arista-PlayAI', name: 'Arista (Female)' },
  { id: 'Atlas-PlayAI', name: 'Atlas (Male)' },
  { id: 'Basil-PlayAI', name: 'Basil (Male)' },
  { id: 'Cora-PlayAI', name: 'Cora (Female)' },
  { id: 'Jasper-PlayAI', name: 'Jasper (Male)' },
  { id: 'Luna-PlayAI', name: 'Luna (Female)' },
  { id: 'Miles-PlayAI', name: 'Miles (Male)' },
  { id: 'Orion-PlayAI', name: 'Orion (Male)' }
];
