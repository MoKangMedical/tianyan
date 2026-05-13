const { getApiBase, normalizeBaseUrl } = require("./config");

function request(path, options = {}) {
  const apiBase = normalizeBaseUrl(options.apiBase || getApiBase());

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${apiBase}${path}`,
      method: options.method || "GET",
      data: options.data || null,
      timeout: options.timeout || 15000,
      header: {
        "content-type": "application/json",
        ...(options.header || {}),
      },
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data);
          return;
        }

        reject(
          new Error(
            (response.data && (response.data.detail || response.data.message)) ||
            `Request failed with status ${response.statusCode}`
          )
        );
      },
      fail(error) {
        reject(new Error(error.errMsg || "Network request failed"));
      },
    });
  });
}

function checkHealth(apiBase) {
  return request("/api/health", { apiBase });
}

function generateAudio(payload, apiBase) {
  return request("/api/v1/media/audio", {
    method: "POST",
    data: payload,
    apiBase,
    timeout: 30000,
  });
}

function generateReport(payload, apiBase) {
  return request("/api/v1/report/generate", {
    method: "POST",
    data: payload,
    apiBase,
    timeout: 45000,
  });
}

function generateVideo(payload, apiBase) {
  return request("/api/v1/media/video", {
    method: "POST",
    data: payload,
    apiBase,
    timeout: 90000,
  });
}

module.exports = {
  checkHealth,
  generateAudio,
  generateReport,
  generateVideo,
  request,
};
