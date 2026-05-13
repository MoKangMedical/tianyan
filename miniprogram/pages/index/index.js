const { checkHealth } = require("../../utils/api");
const { getApiBase, setApiBase } = require("../../utils/config");

Page({
  data: {
    version: "1.0.0",
    textProviderLabel: "DeepSeek V4 Pro",
    audioProviderLabel: "Xiaomi Mimo",
    apiBaseInput: "",
    healthState: "checking",
    healthLabel: "检测中",
    healthNote: "正在检查当前 API 地址是否可用。",
  },

  onLoad() {
    const apiBase = getApiBase();
    this.setData({ apiBaseInput: apiBase });
    this.probeHealth(apiBase);
  },

  onShow() {
    const apiBase = getApiBase();
    if (apiBase !== this.data.apiBaseInput) {
      this.setData({ apiBaseInput: apiBase });
      this.probeHealth(apiBase);
    }
  },

  onApiBaseInput(event) {
    this.setData({ apiBaseInput: event.detail.value });
  },

  onSaveApiBase() {
    const apiBase = setApiBase(this.data.apiBaseInput);
    this.setData({ apiBaseInput: apiBase });
    this.probeHealth(apiBase);
  },

  onProbeHealth() {
    this.probeHealth(this.data.apiBaseInput);
  },

  async probeHealth(apiBase) {
    this.setData({
      healthState: "checking",
      healthLabel: "检测中",
      healthNote: "正在检查 /api/health 和媒体能力状态。",
    });

    try {
      const payload = await checkHealth(apiBase);
      const audio = payload && payload.media ? payload.media.audio : null;
      const llm = payload && payload.llm ? payload.llm : null;
      const available = Boolean(audio && audio.available);
      const textModel = llm && llm.model ? llm.model : "deepseek-v4-pro";

      this.setData({
        healthState: available ? "available" : "unavailable",
        healthLabel: available ? "可用" : "不可用",
        textProviderLabel: `DeepSeek V4 Pro / ${textModel}`,
        healthNote: available
          ? `当前后端可用，音频模型：${audio.model || "unknown"}`
          : (audio && audio.reason) || "后端在线，但音频能力不可用。",
      });
    } catch (error) {
      this.setData({
        healthState: "unavailable",
        healthLabel: "不可用",
        healthNote: error.message || "无法访问当前 API 地址。",
      });
    }
  },

  goCase() {
    wx.navigateTo({ url: "/pages/case/case" });
  },
});
