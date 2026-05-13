function getHealthSnapshot(payload) {
  const llm = payload && payload.llm ? payload.llm : {};
  const media = payload && payload.media ? payload.media : {};
  const audio = media.audio || {};
  const video = media.video || {};

  return {
    llmProvider: llm.provider || "deepseek",
    llmModel: llm.model || "deepseek-v4-pro",
    audioAvailable: Boolean(audio.available),
    audioProvider: audio.provider || "mimo",
    audioModel: audio.model || "mimo-v2-tts",
    audioReason: audio.reason || "",
    videoAvailable: Boolean(video.available),
    videoProvider: video.provider || "comfyui",
    videoModel: video.model || "comfyui-video",
    videoReason: video.reason || "",
  };
}

function normalizeAudioResult(payload) {
  return {
    audioBase64: payload && payload.audio_base64 ? payload.audio_base64 : "",
    audioUrl: payload && payload.audio_url ? payload.audio_url : "",
    format: (payload && payload.format) || "mp3",
    voice: (payload && payload.voice) || "default_zh",
  };
}

function normalizeVideoResult(payload) {
  return {
    success: Boolean(payload && payload.success),
    script: (payload && payload.script) || "",
    audioUrl: (payload && payload.audio_url) || "",
    videoUrl: (payload && payload.video_url) || "",
    posterUrl: (payload && payload.poster_url) || "",
    voice: (payload && payload.voice) || "default_zh",
    videoProvider: (payload && payload.video_provider) || "comfyui",
    videoModel: (payload && payload.video_model) || "comfyui-video",
    audioProvider: (payload && payload.audio_provider) || "mimo",
  };
}

module.exports = {
  getHealthSnapshot,
  normalizeAudioResult,
  normalizeVideoResult,
};
