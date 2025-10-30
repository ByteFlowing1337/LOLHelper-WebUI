// socketHandler.js - wrap socket.io events into callbacks and emit helpers
export function setupSocket(handlers = {}) {
    const socket = io();

    if (handlers.onConnect) socket.on('connect', handlers.onConnect);
    if (handlers.onEnemiesFound) socket.on('enemies_found', handlers.onEnemiesFound);
    if (handlers.onTeammatesFound) socket.on('teammates_found', handlers.onTeammatesFound);
    if (handlers.onStatusUpdate) socket.on('status_update', handlers.onStatusUpdate);

    return {
        socket,
        startAutoAccept() { socket.emit('start_auto_accept'); },
        startAutoAnalyze() { socket.emit('start_auto_analyze'); },
        stopAutoAccept() { socket.emit('stop_auto_accept'); },
        stopAutoAnalyze() { socket.emit('stop_auto_analyze'); }
    };
}

export default { setupSocket };
