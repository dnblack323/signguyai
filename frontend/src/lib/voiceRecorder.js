/**
 * voiceRecorder — shared MediaRecorder + Voice Activity Detection helper.
 *
 * Solves two real bugs:
 *   E) Browser-detected audio format sent to Whisper. We were always uploading
 *      as audio/webm even on Safari (which records audio/mp4) — Whisper would
 *      sometimes silently transcribe garbage. Now we pick the best mimeType
 *      with isTypeSupported() and upload with the matching extension.
 *   F) Auto-stop on silence. A WebAudio AnalyserNode watches the mic level;
 *      when the speaker has been quiet for ~1.2s, recording stops on its own.
 *      Avoids dead air at the end of every recording.
 *
 * Usage:
 *   const rec = await startRecording({ onSilence: () => { ... } });
 *   // ... user talks ...
 *   const { blob, filename, mimeType } = await rec.stop();
 *   formData.append('audio', blob, filename);
 */

// Pick the first MIME type the browser supports — order matters.
// Whisper-1 supports webm, mp4, m4a, mp3, ogg, wav, flac.
const MIME_CANDIDATES = [
  { mime: 'audio/webm;codecs=opus', ext: 'webm' },
  { mime: 'audio/webm',             ext: 'webm' },
  { mime: 'audio/mp4',              ext: 'mp4' },  // Safari
  { mime: 'audio/ogg;codecs=opus',  ext: 'ogg' },
  { mime: 'audio/wav',              ext: 'wav' },
];

function pickSupportedMime() {
  if (typeof MediaRecorder === 'undefined') {
    return { mime: undefined, ext: 'webm' };
  }
  for (const c of MIME_CANDIDATES) {
    try {
      if (MediaRecorder.isTypeSupported(c.mime)) return c;
    } catch {
      /* some browsers throw on isTypeSupported() — try the next one */
    }
  }
  return { mime: undefined, ext: 'webm' }; // let browser default; we'll re-detect from recorder.mimeType
}

function extFromMimeType(mime) {
  if (!mime) return 'webm';
  const m = mime.toLowerCase();
  if (m.includes('mp4'))  return 'mp4';
  if (m.includes('m4a'))  return 'm4a';
  if (m.includes('mpeg')) return 'mp3';
  if (m.includes('ogg'))  return 'ogg';
  if (m.includes('wav'))  return 'wav';
  if (m.includes('flac')) return 'flac';
  return 'webm';
}

export async function startRecording({
  onSilence,                    // optional auto-stop callback
  silenceThreshold = 0.012,     // RMS below this counts as silence (0–1 scale)
  silenceDuration = 1200,       // ms of continuous silence before auto-stop
  minRecordingMs = 800,         // never auto-stop in the first ~0.8s (lets the user start speaking)
  maxRecordingMs = 60000,       // hard ceiling — auto-stop at 60s no matter what
} = {}) {
  // 1) Mic stream with browser noise suppression / echo cancellation on.
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });

  // 2) MediaRecorder with the best supported mime.
  const picked = pickSupportedMime();
  const recorder = picked.mime
    ? new MediaRecorder(stream, { mimeType: picked.mime })
    : new MediaRecorder(stream); // browser picks default

  const chunks = [];
  recorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };
  recorder.start(250); // emit chunks every 250ms

  const startedAt = Date.now();

  // 3) Voice Activity Detection. Optional — only set up if onSilence given.
  let audioCtx = null;
  let vadTimer = null;
  let hardStopTimer = null;
  let stopped = false;

  const cleanup = () => {
    if (vadTimer)      { cancelAnimationFrame(vadTimer); vadTimer = null; }
    if (hardStopTimer) { clearTimeout(hardStopTimer); hardStopTimer = null; }
    if (audioCtx && audioCtx.state !== 'closed') {
      audioCtx.close().catch(() => {});
    }
    audioCtx = null;
  };

  if (onSilence) {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioCtx();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 1024;
      source.connect(analyser);
      const buf = new Uint8Array(analyser.fftSize);

      let silentSince = null;
      const tick = () => {
        if (stopped) return;
        analyser.getByteTimeDomainData(buf);

        // RMS of [-1, 1] signal (buf is 0..255 with 128 = silence).
        let sum = 0;
        for (let i = 0; i < buf.length; i++) {
          const v = (buf[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / buf.length);

        const elapsed = Date.now() - startedAt;
        if (rms < silenceThreshold) {
          if (silentSince === null) silentSince = Date.now();
          if (
            elapsed >= minRecordingMs &&
            Date.now() - silentSince >= silenceDuration
          ) {
            stopped = true;
            cleanup();
            try { onSilence(); } catch (e) { console.warn('VAD onSilence threw', e); }
            return;
          }
        } else {
          silentSince = null;
        }
        vadTimer = requestAnimationFrame(tick);
      };
      vadTimer = requestAnimationFrame(tick);
    } catch (vadErr) {
      // VAD setup failed — that's fine, recording still works manually.
      console.warn('VAD setup failed; manual stop only', vadErr);
      cleanup();
    }
  }

  // Hard ceiling — Whisper bills per second; don't let a forgotten mic run
  // forever.
  hardStopTimer = setTimeout(() => {
    if (stopped) return;
    stopped = true;
    cleanup();
    if (onSilence) { try { onSilence(); } catch { /* noop */ } }
  }, maxRecordingMs);

  // 4) stop() returns the final Blob with correct mime + extension.
  const stop = () => new Promise((resolve) => {
    cleanup();
    if (recorder.state === 'inactive') {
      // Already stopped (autostop via onSilence triggered cleanup). Wait one
      // tick then resolve from chunks.
      const detectedMime = recorder.mimeType || picked.mime || 'audio/webm';
      const ext = extFromMimeType(detectedMime);
      resolve({
        blob: new Blob(chunks, { type: detectedMime }),
        mimeType: detectedMime,
        filename: `assistant-input.${ext}`,
      });
      stream.getTracks().forEach((t) => t.stop());
      return;
    }
    recorder.onstop = () => {
      const detectedMime = recorder.mimeType || picked.mime || 'audio/webm';
      const ext = extFromMimeType(detectedMime);
      resolve({
        blob: new Blob(chunks, { type: detectedMime }),
        mimeType: detectedMime,
        filename: `assistant-input.${ext}`,
      });
      stream.getTracks().forEach((t) => t.stop());
    };
    try { recorder.stop(); } catch { /* already stopped — onstop fires anyway */ }
  });

  return { stop, stream, recorder };
}
