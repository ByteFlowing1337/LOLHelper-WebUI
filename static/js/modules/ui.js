// ui.js - DOM helpers and inline messaging
export function qs(id) {
    return document.getElementById(id);
}

export function showInlineMessage(message, { targetId = 'realtime-status', level = 'info', timeout = 5000 } = {}) {
    const el = qs(targetId);
    if (!el) return;
    el.textContent = message;
    // map levels to bootstrap badge classes
    const cls = {
        info: 'badge bg-info',
        success: 'badge bg-success',
        warn: 'badge bg-warning text-dark',
        error: 'badge bg-danger',
        neutral: 'badge bg-secondary'
    }[level] || 'badge bg-secondary';
    el.className = cls;

    if (timeout && timeout > 0) {
        clearTimeout(el._messageTimeout);
        el._messageTimeout = setTimeout(() => {
            // revert to neutral state
            el.textContent = '等待指令...';
            el.className = 'badge bg-secondary';
        }, timeout);
    }
}

export function isLCUConnected() {
    const statusEl = qs('lcu-status');
    if (!statusEl) return false;
    const txt = (statusEl.textContent || '').toLowerCase();
    return txt.includes('成功') || txt.includes('已连接') || txt.includes('连接成功');
}

export function setLCUStatus(message, style = 'neutral') {
    const statusEl = qs('lcu-status');
    const statusBox = qs('connection-status-box');
    if (!statusEl || !statusBox) return;
    statusEl.textContent = message;
    if (style === 'ok') {
        statusBox.style.backgroundColor = '#d4edda';
        statusBox.style.color = '#155724';
        statusBox.style.borderColor = '#c3e6cb';
    } else if (style === 'err') {
        statusBox.style.backgroundColor = '#f8d7da';
        statusBox.style.color = '#721c24';
        statusBox.style.borderColor = '#f5c6cb';
    } else {
        statusBox.style.backgroundColor = '#cce5ff';
        statusBox.style.color = '#004085';
        statusBox.style.borderColor = '#b8daff';
    }
}
