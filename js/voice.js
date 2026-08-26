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

/* ===== Groq Whisper STT ===== */
class GroqSTT {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.base = 'https://api.groq.com/openai/v1';
    this.mediaRecorder = null;
    this.chunks = [];
    this.stream = null;
    this.isListening = false;
    this.onResult = null;
    this.onEnd = null;
    this.onError = null;
  }

  async start(onResult, onEnd, onError) {
    if (!navigator.mediaDevices?.getUserMedia) {
      if (onError) onError('Microphone access is not available in this app runtime.');
      return false;
    }
    this.onResult = onResult;
    this.onEnd = onEnd;
    this.onError = onError;
    this.chunks = [];
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg';
      this.mediaRecorder = new MediaRecorder(this.stream, { mimeType });
      this.mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) this.chunks.push(e.data); };
      this.mediaRecorder.onstop = () => this._transcribe();
      this.mediaRecorder.onerror = (e) => { this._cleanup(); if (onError) onError('Recorder error: ' + e.message); };
      this.mediaRecorder.start(250);
      this.isListening = true;
      if (onResult) onResult('', 'Listening...');
      return true;
    } catch (e) {
      if (onError) onError('Microphone error: ' + e.message);
      return false;
    }
  }

  stop() {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    } else {
      this._cleanup();
    }
  }

  async _transcribe() {
    this.isListening = false;
    if (!this.chunks.length) { this._cleanup(); if (this.onEnd) this.onEnd(''); return; }
    const blob = new Blob(this.chunks, { type: this.mediaRecorder?.mimeType || 'audio/webm' });
    this._cleanup();
    try {
      const form = new FormData();
      form.append('file', blob, 'recording.webm');
      form.append('model', 'whisper-large-v3');
      form.append('response_format', 'json');
      const res = await fetch(this.base + '/audio/transcriptions', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + this.apiKey },
        body: form
      });
      if (!res.ok) throw new Error((await res.text().catch(() => res.statusText)));
      const data = await res.json();
      const text = data.text || '';
      if (this.onEnd) this.onEnd(text);
    } catch (e) {
      if (this.onError) this.onError('Groq transcription failed: ' + e.message);
    }
  }

  _cleanup() {
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    this.mediaRecorder = null;
    this.isListening = false;
  }
}

/* ===== Voice Manager ===== */
class VoiceManager {
  constructor() {
    this.tts = null;
    this.stt = new SpeechToText();
    this.groqStt = null;
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
    if (this.groqKey) {
      this.tts = new GroqTTS(this.groqKey);
      this.groqStt = new GroqSTT(this.groqKey);
    }
  }

  async saveSettings() {
    await Settings.set('voiceEnabled', this.enabled);
    await Settings.set('voiceAutoRead', this.autoRead);
    await Settings.set('voiceChoice', this.voice);
  }

  setKey(key) {
    this.groqKey = key;
    this.tts = key ? new GroqTTS(key) : null;
    this.groqStt = key ? new GroqSTT(key) : null;
  }

  async speak(text) {
    if (!this.enabled) throw new Error('Enable voice in Settings first.');
    if (this.tts) {
      try {
        await this.tts.speak(text, this.voice);
        return;
      } catch (e) {
        console.warn('Groq TTS failed:', e.message);
      }
    }
    if (!window.speechSynthesis) throw new Error('Voice output is not supported in this app runtime.');
    window.speechSynthesis.cancel();
    return new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1;
      utterance.onend = resolve;
      utterance.onerror = (e) => reject(new Error('System TTS failed: ' + e.error));
      window.speechSynthesis.speak(utterance);
    });
  }

  stop() {
    if (this.tts) this.tts.stop();
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  }

  startListening(onResult, onEnd, onError) {
    // Prefer Groq Whisper STT when a Groq key is available because it works
    // reliably inside the Electron flatpak. Fall back to browser-native
    // SpeechRecognition if Groq is not configured.
    if (this.groqStt) {
      return this.groqStt.start(onResult, onEnd, onError);
    }
    if (!this.stt.available) {
      const msg = 'Speech recognition is not available. Add a Groq key in Settings to use Groq Whisper, or use this app in a browser that supports SpeechRecognition.';
      if (onError) onError(msg);
      return false;
    }
    this.stt.onResult = onResult;
    this.stt.onEnd = onEnd;
    this.stt.onError = onError;
    return this.stt.start();
  }

  stopListening() {
    if (this.groqStt) this.groqStt.stop();
    this.stt.stop();
  }

  get isListening() { return this.groqStt?.isListening || this.stt.isListening; }
  get isSpeaking() { return this.tts?.isPlaying || window.speechSynthesis?.speaking || false; }
  get sttAvailable() { return !!this.groqStt || this.stt.available; }
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
