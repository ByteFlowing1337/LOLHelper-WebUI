import { showInlineMessage, setLCUStatus } from "./modules/ui.js";
import { setupSocket } from "./modules/socketHandler.js";

function handleStatusUpdate(payload = {}) {
  const message = payload.message || payload.data || "";
  const type = payload.type || (payload.data ? "lcu" : "biz");

  if (!message) {
    return;
  }

  if (type === "lcu") {
    const normalized = message.toLowerCase();
    if (normalized.includes("成功") || normalized.includes("已连接")) {
      setLCUStatus(message, "ok");
    } else if (
      normalized.includes("失败") ||
      normalized.includes("未连接") ||
      normalized.includes("无法")
    ) {
      setLCUStatus(message, "err");
    } else {
      setLCUStatus(message, "neutral");
    }
  } else {
    showInlineMessage(message, { level: "info", timeout: 5000 });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const { socket } = setupSocket({
    onStatusUpdate: handleStatusUpdate,
  });

  socket.on("connect_error", () => {
    showInlineMessage("❌ 无法连接到后台服务", {
      level: "error",
      timeout: 6000,
    });
    setLCUStatus("❌ 无法连接到后台服务", "err");
  });
});
