// ui.js - DOM helpers and inline messaging
export function qs(id) {
  return document.getElementById(id);
}

export function showInlineMessage(
  message,
  { targetId = "realtime-status", level = "info", timeout = 5000 } = {}
) {
  const el = qs(targetId);
  if (!el) return;
  el.textContent = message;
  // map levels to bootstrap badge classes
  const cls =
    {
      info: "badge bg-info",
      success: "badge bg-success",
      warn: "badge bg-warning text-dark",
      error: "badge bg-danger",
      neutral: "badge bg-secondary",
    }[level] || "badge bg-secondary";
  el.className = cls;

  if (timeout && timeout > 0) {
    clearTimeout(el._messageTimeout);
    el._messageTimeout = setTimeout(() => {
      // revert to neutral state
      el.textContent = "等待指令...";
      el.className = "badge bg-secondary";
    }, timeout);
  }
}

export function isLCUConnected() {
  const statusEl = qs("lcu-status");
  if (!statusEl) return false;
  const txt = (statusEl.textContent || "").toLowerCase();
  return (
    txt.includes("成功") || txt.includes("已连接") || txt.includes("连接成功")
  );
}

export function setLCUStatus(message, style = "neutral") {
  const statusEl = qs("lcu-status");
  const statusBox = qs("connection-status-box");
  if (!statusEl || !statusBox) return;
  statusEl.textContent = message;
  if (style === "ok") {
    statusBox.style.backgroundColor = "#d4edda";
    statusBox.style.color = "#155724";
    statusBox.style.borderColor = "#c3e6cb";
  } else if (style === "err") {
    statusBox.style.backgroundColor = "#f8d7da";
    statusBox.style.color = "#721c24";
    statusBox.style.borderColor = "#f5c6cb";
  } else {
    statusBox.style.backgroundColor = "#cce5ff";
    statusBox.style.color = "#004085";
    statusBox.style.borderColor = "#b8daff";
  }
}

export function formatRankBadge(rank) {
  if (!rank || rank.tier === "UNRANKED") {
    return '<span class="badge bg-secondary" style="font-size: 0.7rem;">未定级</span>';
  }

  const tierColors = {
    IRON: "#6B5D57",
    BRONZE: "#CD7F32",
    SILVER: "#C0C0C0",
    GOLD: "#FFD700",
    PLATINUM: "#4EC9B0",
    EMERALD: "#00C896",
    DIAMOND: "#B9F2FF",
    MASTER: "#9B4F96",
    GRANDMASTER: "#E74856",
    CHALLENGER: "#F1C40F",
  };

  const tierNames = {
    IRON: "黑铁",
    BRONZE: "青铜",
    SILVER: "白银",
    GOLD: "黄金",
    PLATINUM: "铂金",
    EMERALD: "翡翠",
    DIAMOND: "钻石",
    MASTER: "大师",
    GRANDMASTER: "宗师",
    CHALLENGER: "王者",
  };

  const divisionNames = {
    I: "I",
    II: "II",
    III: "III",
    IV: "IV",
  };

  const tier = rank.tier.toUpperCase();
  const color = tierColors[tier] || "#6C757D";
  const tierName = tierNames[tier] || tier;
  const division = rank.division
    ? divisionNames[rank.division] || rank.division
    : "";
  const lp = rank.lp || 0;

  let rankText = tierName;
  if (division) {
    rankText += ` ${division}`;
  }
  if (["MASTER", "GRANDMASTER", "CHALLENGER"].includes(tier)) {
    rankText += ` ${lp}点`;
  }

  return `<span class="badge" style="background-color: ${color}; font-size: 0.7rem;">${rankText}</span>`;
}
