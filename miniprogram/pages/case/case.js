const { checkHealth, generateAudio, generateVideo } = require("../../utils/api");
const { getApiBase } = require("../../utils/config");
const { getHealthSnapshot, normalizeAudioResult, normalizeVideoResult } = require("../../utils/media");

const SCRIPT_OPTIONS = [
  {
    label: "董事会摘要",
    text: "Medislim 项目当前建议聚焦中国高线城市体重管理人群，以循证定位、内容教育和医生背书建立信任，再通过分阶段渠道投放完成商业验证。",
  },
  {
    label: "渠道投放稿",
    text: "建议先以小红书和视频号作为前期种草阵地，建立品牌可信度，再逐步引入私域承接和转化链路，缩短首次触达至下单的决策周期。",
  },
  {
    label: "风险提示",
    text: "项目推进中需要重点关注合规表述、价格带匹配、供应稳定性和医生教育成本，避免在高曝光阶段出现信任折损。",
  },
];

const CASE_DATA = {
  name: "Medislim 产品上市案例",
  summary: "把市场空间、目标客群、渠道打法、风险项和管理层旁白整合到一个微信入口里，方便客户在会前、会中和会后统一查看。",
  highlights: [
    "围绕高线城市体重管理需求建立目标客群画像。",
    "用 McKinsey 风格结构输出市场空间、渠道优先级和执行节奏。",
    "把报告要点转成可直接播放的中文旁白，适合销售演示和管理层预览。",
  ],
  deliverables: [
    "DeepSeek V4 Pro 研究摘要",
    "渠道投放建议",
    "16 周执行路径",
    "风险清单与缓释策略",
    "Mimo 旁白音频预览",
    "ComfyUI 视频预览 URL",
  ],
};

Page({
  data: {
    caseData: CASE_DATA,
    scriptOptions: SCRIPT_OPTIONS,
    selectedScriptIndex: 0,
    selectedScriptLabel: SCRIPT_OPTIONS[0].label,
    scriptText: SCRIPT_OPTIONS[0].text,
    healthState: "checking",
    healthLabel: "检测中",
    healthNote: "正在检查音频和视频能力。",
    reportProviderLabel: "DeepSeek V4 Pro",
    audioProviderLabel: "Xiaomi Mimo",
    videoProviderLabel: "ComfyUI",
    isGeneratingAudio: false,
    isGeneratingVideo: false,
    audioUrl: "",
    audioMeta: null,
    remoteAudioUrl: "",
    videoUrl: "",
    posterUrl: "",
    videoMeta: null,
  },

  onLoad() {
    this.probeHealth();
  },

  async probeHealth() {
    try {
      const payload = await checkHealth(getApiBase());
      const snapshot = getHealthSnapshot(payload);
      const available = snapshot.audioAvailable || snapshot.videoAvailable;

      this.setData({
        healthState: available ? "available" : "unavailable",
        healthLabel: available ? "可用" : "不可用",
        reportProviderLabel: snapshot.llmModel,
        audioProviderLabel: `${snapshot.audioProvider} / ${snapshot.audioModel}`,
        videoProviderLabel: `${snapshot.videoProvider} / ${snapshot.videoModel}`,
        healthNote: available
          ? `文本模型 ${snapshot.llmModel} 已就绪，音频 ${snapshot.audioAvailable ? "可用" : "不可用"}，视频 ${snapshot.videoAvailable ? "可用" : "不可用"}`
          : snapshot.videoReason || snapshot.audioReason || "当前后端未提供媒体能力。",
      });
    } catch (error) {
      this.setData({
        healthState: "unavailable",
        healthLabel: "不可用",
        healthNote: error.message || "无法连接当前后端。",
      });
    }
  },

  onScriptChange(event) {
    const index = Number(event.detail.value);
    const selected = SCRIPT_OPTIONS[index];
    this.setData({
      selectedScriptIndex: index,
      selectedScriptLabel: selected.label,
      scriptText: selected.text,
    });
  },

  onScriptInput(event) {
    this.setData({ scriptText: event.detail.value });
  },

  async onGenerateAudio() {
    if (!this.data.scriptText.trim()) {
      wx.showToast({ title: "请输入旁白内容", icon: "none" });
      return;
    }

    this.setData({ isGeneratingAudio: true });

    try {
      const payload = normalizeAudioResult(await generateAudio({
        text: this.data.scriptText,
        voice: "default_zh",
        audio_format: "mp3",
      }));

      const audioUrl = payload.audioBase64
        ? await this.writeAudioFile(payload.audioBase64, payload.format || "mp3")
        : "";

      this.setData({
        audioUrl,
        remoteAudioUrl: payload.audioUrl || "",
        audioMeta: {
          voice: payload.voice || "default_zh",
          format: payload.format || "mp3",
        },
      });

      wx.showToast({ title: "旁白已生成", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "生成失败", icon: "none" });
    } finally {
      this.setData({ isGeneratingAudio: false });
    }
  },

  async onGenerateVideo() {
    if (!this.data.scriptText.trim()) {
      wx.showToast({ title: "请输入视频脚本", icon: "none" });
      return;
    }

    this.setData({ isGeneratingVideo: true });

    try {
      const payload = normalizeVideoResult(await generateVideo({
        prompt: this.data.scriptText,
        voice: "default_zh",
        audio_format: "mp3",
        video_provider: "comfyui",
        video_mode: "narrated-brief",
      }));

      this.setData({
        remoteAudioUrl: payload.audioUrl || "",
        videoUrl: payload.videoUrl || "",
        posterUrl: payload.posterUrl || "",
        videoMeta: {
          audioProvider: payload.audioProvider,
          videoProvider: payload.videoProvider,
          videoModel: payload.videoModel,
          voice: payload.voice,
        },
      });

      wx.showToast({
        title: payload.videoUrl ? "视频链接已返回" : "未返回视频链接",
        icon: payload.videoUrl ? "success" : "none",
      });
    } catch (error) {
      wx.showToast({ title: error.message || "视频生成失败", icon: "none" });
    } finally {
      this.setData({ isGeneratingVideo: false });
    }
  },

  writeAudioFile(audioBase64, extension) {
    return new Promise((resolve, reject) => {
      if (!audioBase64) {
        reject(new Error("接口未返回音频数据"));
        return;
      }

      const filePath = `${wx.env.USER_DATA_PATH}/tianyan-narration-${Date.now()}.${extension}`;
      const fs = wx.getFileSystemManager();

      fs.writeFile({
        filePath,
        data: audioBase64,
        encoding: "base64",
        success() {
          resolve(filePath);
        },
        fail(error) {
          reject(new Error(error.errMsg || "音频文件写入失败"));
        },
      });
    });
  },
});
