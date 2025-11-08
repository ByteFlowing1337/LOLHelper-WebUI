// socketHandler.js - wrap socket.io events into callbacks and emit helpers
export function setupSocket(handlers = {}) {
  const socket = io();

  if (handlers.onConnect) socket.on("connect", handlers.onConnect);
  if (handlers.onEnemiesFound)
    socket.on("enemies_found", handlers.onEnemiesFound);
  if (handlers.onTeammatesFound)
    socket.on("teammates_found", handlers.onTeammatesFound);
  if (handlers.onStatusUpdate)
    socket.on("status_update", handlers.onStatusUpdate);

  // 监听服务器关闭事件。当后端发出 "server_shutdown" 时，尝试关闭页面或提示用户手动关闭。
  socket.on("server_shutdown", (payload) => {
    console.warn("收到 server_shutdown 通知，尝试关闭页面...", payload);
    try {
      // 先尝试直接关闭（对由脚本打开的窗口有效）
      window.close();
    } catch (e) {
      // ignore
    }

    // 在某些浏览器中 window.close() 会被阻止，尝试替代方法后展示友好信息
    setTimeout(() => {
      try {
        // 尝试 self-close trick
        window.open("", "_self").close();
      } catch (e) {
        // 如果仍然失败，替换页面内容告知用户
        document.body.innerHTML = `\n                    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; padding: 30px; text-align: center;">\n                        <h2>应用已退出</h2>\n                        <p>后端服务已关闭。请关闭此标签页或窗口。</p>\n                    </div>`;
      }
    }, 150);
  });

  return {
    socket,
    startAutoAccept() {
      socket.emit("start_auto_accept");
    },
    startAutoAnalyze() {
      socket.emit("start_auto_analyze");
    },
    stopAutoAccept() {
      socket.emit("stop_auto_accept");
    },
    stopAutoAnalyze() {
      socket.emit("stop_auto_analyze");
    },
  };
}

export default { setupSocket };
