const STORAGE_KEY = "tianyan_api_base";
const DEFAULT_API_BASE = "https://tianyan-api.mokangmedical-dev.workers.dev";

function normalizeBaseUrl(value) {
  const source = (value || "").trim();
  if (!source) {
    return DEFAULT_API_BASE;
  }

  return source.replace(/\/+$/, "");
}

function getApiBase() {
  try {
    const saved = wx.getStorageSync(STORAGE_KEY);
    return normalizeBaseUrl(saved || DEFAULT_API_BASE);
  } catch (error) {
    return DEFAULT_API_BASE;
  }
}

function setApiBase(value) {
  const normalized = normalizeBaseUrl(value);
  wx.setStorageSync(STORAGE_KEY, normalized);
  return normalized;
}

module.exports = {
  DEFAULT_API_BASE,
  STORAGE_KEY,
  getApiBase,
  normalizeBaseUrl,
  setApiBase,
};
