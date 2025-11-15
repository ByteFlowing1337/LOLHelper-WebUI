// main.js - module entrypoint (ES Module)
import {
  showInlineMessage,
  isLCUConnected,
  setLCUStatus,
  qs,
} from "./modules/ui.js";
import { fetchSummonerStats, fetchTFTMatches } from "./modules/api.js";
import { setupSocket } from "./modules/socketHandler.js";
import {
  loadChampionData,
  createChampionSelector,
} from "./modules/championSelector.js";

document.addEventListener("DOMContentLoaded", async () => {
  const detectBtn = qs("detect-btn");
  const fetchBtn = qs("fetch-btn");
  const fetchTftBtn = qs("fetch-tft-btn");
  const summonerNameInput = qs("summoner-name-input");
  const resultsDiv = qs("results-area");
  const autoAcceptBtn = qs("auto-accept-btn");
  const autoAnalyzeBtn = qs("auto-analyze-btn");
  const autoBanPickBtn = qs("auto-banpick-btn");
  const realtimeStatus = qs("realtime-status");
  const teammateResultsDiv = qs("teammate-results-area");
  const enemyResultsDiv = qs("enemy-results-area");

  // Initialize champion data and selectors
  await loadChampionData();

  // 创建 Ban 英雄优先队列选择器（最多3个）
  const banChampionSelectors = [
    createChampionSelector("ban-champion-selector-1"),
    createChampionSelector("ban-champion-selector-2"),
    createChampionSelector("ban-champion-selector-3"),
  ];

  // 创建 Pick 英雄优先队列选择器（最多3个）
  const pickChampionSelectors = [
    createChampionSelector("pick-champion-selector-1"),
    createChampionSelector("pick-champion-selector-2"),
    createChampionSelector("pick-champion-selector-3"),
  ];

  // Helper function to format rank badge
  function formatRankBadge(rank) {
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
  } // socket handlers
  const {
    socket,
    startAutoAccept,
    startAutoAnalyze,
    stopAutoAccept,
    stopAutoAnalyze,
    startAutoBanPick,
    stopAutoBanPick,
    configureBanPick,
  } = setupSocket({
    onConnect() {
      console.log("成功连接到WebSocket服务器!");
    },
    onStatusUpdate(data) {
      // Expect structured payload: { type: 'lcu'|'biz', message: '...' }
      const type = data.type || (data.data ? "lcu" : "biz");
      const message = data.message || data.data || "";

      if (type === "lcu") {
        // connection-related message -> update LCU status box
        if (message.includes("成功")) setLCUStatus(message, "ok");
        else if (message.includes("失败") || message.includes("无法"))
          setLCUStatus(message, "err");
        else setLCUStatus(message, "neutral");
      } else {
        // business message -> realtime area
        showInlineMessage(message, { level: "info", timeout: 5000 });
      }
    },
    onEnemiesFound: async (data) => {
      realtimeStatus.textContent = `💥 发现 ${data.enemies.length} 名敌人! 正在分析战绩...`;
      realtimeStatus.className = "badge bg-danger";
      enemyResultsDiv.innerHTML =
        '<h5 class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>敌方目标分析:</h5>';
      const ul = document.createElement("ul");
      ul.className = "list-unstyled";
      enemyResultsDiv.appendChild(ul);

      const promises = data.enemies.map((enemy) => {
        const li = document.createElement("li");
        li.className = "d-flex flex-column border-bottom py-2 mb-2";
        const headerDiv = document.createElement("div");
        headerDiv.className =
          "d-flex justify-content-between align-items-center flex-wrap";

        const nameDiv = document.createElement("div");
        nameDiv.className = "d-flex align-items-center gap-2";

        const riotIdLink = document.createElement("a");
        riotIdLink.href = `/summoner/${encodeURIComponent(
          enemy.gameName + "#" + enemy.tagLine
        )}`;
        riotIdLink.target = "_blank";
        riotIdLink.rel = "noopener noreferrer";
        riotIdLink.className = "fw-bold text-danger text-decoration-none";
        riotIdLink.style.cursor = "pointer";
        riotIdLink.innerHTML = `<i class="bi bi-person-x-fill me-1"></i>${enemy.gameName}#${enemy.tagLine}`;
        riotIdLink.title = "点击查看详细战绩";
        nameDiv.appendChild(riotIdLink);

        // 添加段位信息
        if (enemy.rank) {
          const rankBadge = document.createElement("span");
          rankBadge.innerHTML = formatRankBadge(enemy.rank);
          nameDiv.appendChild(rankBadge);
        }

        headerDiv.appendChild(nameDiv);

        if (enemy.championId && enemy.championId !== "Unknown") {
          const championSpan = document.createElement("span");
          championSpan.className = "badge bg-dark";
          championSpan.textContent = enemy.championId;
          headerDiv.appendChild(championSpan);
        }
        li.appendChild(headerDiv);
        const statsDisplay = document.createElement("div");
        statsDisplay.textContent = "⏳ 查询中...";
        statsDisplay.className = "text-muted small mt-1";
        li.appendChild(statsDisplay);
        ul.appendChild(li);
        return fetchSummonerStats(enemy.gameName, enemy.tagLine, statsDisplay);
      });

      await Promise.all(promises);
      realtimeStatus.textContent = `✅ 敌方战绩分析完成!`;
      realtimeStatus.className = "badge bg-success";
    },
    onTeammatesFound: async (data) => {
      realtimeStatus.textContent = `👥 发现 ${data.teammates.length} 名队友! 正在分析战绩...`;
      realtimeStatus.className = "badge bg-info";
      teammateResultsDiv.innerHTML =
        '<h5 class="text-primary"><i class="bi bi-people-fill me-2"></i>本局队友分析:</h5>';
      const ul = document.createElement("ul");
      ul.className = "list-unstyled";
      teammateResultsDiv.appendChild(ul);

      const promises = data.teammates.map((tm) => {
        const li = document.createElement("li");
        li.className = "d-flex flex-column border-bottom py-2 mb-2";
        const headerDiv = document.createElement("div");
        headerDiv.className =
          "d-flex justify-content-between align-items-center flex-wrap";

        const nameDiv = document.createElement("div");
        nameDiv.className = "d-flex align-items-center gap-2";

        const riotIdLink = document.createElement("a");
        riotIdLink.href = `/summoner/${encodeURIComponent(
          tm.gameName + "#" + tm.tagLine
        )}`;
        riotIdLink.target = "_blank";
        riotIdLink.rel = "noopener noreferrer";
        riotIdLink.className = "fw-bold text-primary text-decoration-none";
        riotIdLink.style.cursor = "pointer";
        riotIdLink.innerHTML = `<i class="bi bi-person-check-fill me-1"></i>${tm.gameName}#${tm.tagLine}`;
        riotIdLink.title = "点击查看详细战绩";
        nameDiv.appendChild(riotIdLink);

        // 添加段位信息
        if (tm.rank) {
          const rankBadge = document.createElement("span");
          rankBadge.innerHTML = formatRankBadge(tm.rank);
          nameDiv.appendChild(rankBadge);
        }

        headerDiv.appendChild(nameDiv);
        li.appendChild(headerDiv);
        const statsDisplay = document.createElement("div");
        statsDisplay.textContent = "⏳ 查询中...";
        statsDisplay.className = "text-muted small mt-1";
        li.appendChild(statsDisplay);
        ul.appendChild(li);
        return fetchSummonerStats(tm.gameName, tm.tagLine, statsDisplay);
      });

      await Promise.all(promises);
      realtimeStatus.textContent = `✅ 队友分析完成! 等待游戏开始...`;
      realtimeStatus.className = "badge bg-success";
      console.log("队友战绩分析全部完成");
    },
  });

  // --- UI actions ---
  fetchBtn.addEventListener("click", () => {
    const summonerName = summonerNameInput.value.trim();
    if (!summonerName) {
      showInlineMessage("请输入召唤师名称 (格式: 名称#Tag)", { level: "warn" });
      return;
    }
    const encodedName = encodeURIComponent(summonerName);
    // Open summoner detail in a new tab instead of replacing current page
    window.open(`/summoner/${encodedName}`, "_blank", "noopener");
  });

  if (fetchTftBtn) {
    fetchTftBtn.addEventListener("click", () => {
      const summonerName = summonerNameInput.value.trim();
      if (!summonerName) {
        showInlineMessage("请输入召唤师名称 (格式: 名称#Tag)", {
          level: "warn",
        });
        return;
      }
      const encodedName = encodeURIComponent(summonerName);
      // open a dedicated TFT summoner page in a new tab
      window.open(`/tft_summoner/${encodedName}`, "_blank", "noopener");
    });
  }

  let autoAcceptRunning = false;
  let autoAnalyzeRunning = false;
  let autoBanPickRunning = false;

  // localStorage 键名用于记忆自动化功能开关状态
  const STORAGE_KEY_AUTO_ACCEPT = "lcu_ui_auto_accept_enabled";
  const STORAGE_KEY_AUTO_ANALYZE = "lcu_ui_auto_analyze_enabled";
  const STORAGE_KEY_AUTO_BANPICK = "lcu_ui_auto_banpick_enabled";

  // 保存自动化功能开关状态
  function saveAutoFeatureStates() {
    try {
      localStorage.setItem(
        STORAGE_KEY_AUTO_ACCEPT,
        autoAcceptRunning.toString()
      );
      localStorage.setItem(
        STORAGE_KEY_AUTO_ANALYZE,
        autoAnalyzeRunning.toString()
      );
      localStorage.setItem(
        STORAGE_KEY_AUTO_BANPICK,
        autoBanPickRunning.toString()
      );
    } catch (e) {
      console.warn("保存自动化功能状态失败:", e);
    }
  }

  // 恢复自动化功能开关状态
  function restoreAutoFeatureStates() {
    try {
      const savedAutoAccept =
        localStorage.getItem(STORAGE_KEY_AUTO_ACCEPT) === "true";
      const savedAutoAnalyze =
        localStorage.getItem(STORAGE_KEY_AUTO_ANALYZE) === "true";
      const savedAutoBanPick =
        localStorage.getItem(STORAGE_KEY_AUTO_BANPICK) === "true";

      // 如果上次是开启状态，且 LCU 已连接，则自动启动
      if (savedAutoAccept && isLCUConnected()) {
        setTimeout(() => autoAcceptBtn.click(), 500);
      }
      if (savedAutoAnalyze && isLCUConnected()) {
        setTimeout(() => autoAnalyzeBtn.click(), 600);
      }
      if (savedAutoBanPick && isLCUConnected()) {
        setTimeout(() => autoBanPickBtn.click(), 700);
      }

      console.log("已恢复自动化功能状态:", {
        autoAccept: savedAutoAccept,
        autoAnalyze: savedAutoAnalyze,
        autoBanPick: savedAutoBanPick,
      });
    } catch (e) {
      console.warn("恢复自动化功能状态失败:", e);
    }
  }

  autoAcceptBtn.addEventListener("click", () => {
    if (!isLCUConnected()) {
      showInlineMessage(
        "无法启动自动接受：未检测到LCU连接，请先确保客户端已运行并且LCU已连接。",
        { level: "error", timeout: 8000 }
      );
      return;
    }

    if (!autoAcceptRunning) {
      // 启动
      startAutoAccept();
      autoAcceptRunning = true;
      autoAcceptBtn.innerHTML =
        '<i class="bi bi-stop-circle-fill me-1"></i> 停止接受';
      autoAcceptBtn.classList.remove("btn-success");
      autoAcceptBtn.classList.add("btn-danger");
      showInlineMessage("自动接受对局已启动", { level: "info" });
      saveAutoFeatureStates();
    } else {
      // 停止
      stopAutoAccept();
      autoAcceptRunning = false;
      autoAcceptBtn.innerHTML =
        '<i class="bi bi-check-circle-fill me-1"></i> 自动接受对局';
      autoAcceptBtn.classList.remove("btn-danger");
      autoAcceptBtn.classList.add("btn-success");
      showInlineMessage("自动接受对局已停止", { level: "info" });
      saveAutoFeatureStates();
    }
  });

  autoAnalyzeBtn.addEventListener("click", () => {
    if (!isLCUConnected()) {
      showInlineMessage(
        "无法启动敌我分析：未检测到LCU连接，请先确保客户端已运行并且LCU已连接。",
        { level: "error", timeout: 8000 }
      );
      return;
    }

    if (!autoAnalyzeRunning) {
      // 启动
      startAutoAnalyze();
      autoAnalyzeRunning = true;
      autoAnalyzeBtn.innerHTML =
        '<i class="bi bi-stop-circle-fill me-1"></i> 停止分析';
      autoAnalyzeBtn.classList.remove("btn-primary");
      autoAnalyzeBtn.classList.add("btn-danger");
      showInlineMessage("敌我分析已启动", { level: "info" });
      saveAutoFeatureStates();
    } else {
      // 停止
      stopAutoAnalyze();
      autoAnalyzeRunning = false;
      autoAnalyzeBtn.innerHTML =
        '<i class="bi bi-bar-chart-fill me-1"></i> 敌我分析';
      autoAnalyzeBtn.classList.remove("btn-danger");
      autoAnalyzeBtn.classList.add("btn-primary");
      showInlineMessage("敌我分析已停止", { level: "info" });
      saveAutoFeatureStates();
    }
  });

  // Auto Ban/Pick Button Handler
  if (
    autoBanPickBtn &&
    banChampionSelectors.length &&
    pickChampionSelectors.length
  ) {
    // Ban/Pick 英雄优先队列
    const banQueue = [];
    const pickQueue = [];

    const banFallbackListEl = document.getElementById("ban-fallback-list");
    const pickFallbackListEl = document.getElementById("pick-fallback-list");

    // localStorage 键名
    const STORAGE_KEY_BAN = "lcu_ui_ban_champions";
    const STORAGE_KEY_PICK = "lcu_ui_pick_champions";

    // 保存当前选择到 localStorage
    function saveSelectionsToStorage() {
      try {
        const banIds = banQueue.filter((id) => id);
        const pickIds = pickQueue.filter((id) => id);
        localStorage.setItem(STORAGE_KEY_BAN, JSON.stringify(banIds));
        localStorage.setItem(STORAGE_KEY_PICK, JSON.stringify(pickIds));
      } catch (e) {
        console.warn("保存 Ban/Pick 选择失败:", e);
      }
    }

    // 从 localStorage 恢复上次选择
    function loadSelectionsFromStorage() {
      try {
        const savedBanIds = JSON.parse(
          localStorage.getItem(STORAGE_KEY_BAN) || "[]"
        );
        const savedPickIds = JSON.parse(
          localStorage.getItem(STORAGE_KEY_PICK) || "[]"
        );

        // 恢复 Ban 选择器
        savedBanIds.forEach((id, index) => {
          if (
            index < banChampionSelectors.length &&
            banChampionSelectors[index]
          ) {
            banChampionSelectors[index].setSelectedChampion(id);
          }
        });

        // 恢复 Pick 选择器
        savedPickIds.forEach((id, index) => {
          if (
            index < pickChampionSelectors.length &&
            pickChampionSelectors[index]
          ) {
            pickChampionSelectors[index].setSelectedChampion(id);
          }
        });

        // 重建队列并渲染
        rebuildQueueFromSelectors();
        console.log("已恢复上次 Ban/Pick 选择:", {
          ban: savedBanIds,
          pick: savedPickIds,
        });
      } catch (e) {
        console.warn("加载 Ban/Pick 选择失败:", e);
      }
    }

    function rebuildQueueFromSelectors() {
      // 从所有选择器中读取已选英雄ID，按顺序构建队列
      banQueue.length = 0;
      pickQueue.length = 0;

      banChampionSelectors.forEach((selector) => {
        if (selector) {
          const id = selector.getSelectedChampionId();
          if (id) banQueue.push(id);
        }
      });

      pickChampionSelectors.forEach((selector) => {
        if (selector) {
          const id = selector.getSelectedChampionId();
          if (id) pickQueue.push(id);
        }
      });

      renderFallbackChips();
      saveSelectionsToStorage();
    }

    function renderFallbackChips() {
      // 渲染 Ban 英雄优先队列徽章
      if (banFallbackListEl) {
        banFallbackListEl.innerHTML = "";
        if (banQueue.length > 0) {
          const summary = document.createElement("div");
          summary.className = "d-flex flex-wrap gap-1 align-items-center";
          summary.innerHTML = '<small class="text-muted me-1">优先级:</small>';
          banQueue.forEach((id, index) => {
            const chip = document.createElement("span");
            chip.className =
              index === 0 ? "badge bg-primary" : "badge bg-secondary";
            chip.style.fontSize = "0.75rem";
            chip.textContent = `${index + 1}. ID ${id}`;
            summary.appendChild(chip);
          });
          banFallbackListEl.appendChild(summary);
        }
      }

      // 渲染 Pick 英雄优先队列徽章
      if (pickFallbackListEl) {
        pickFallbackListEl.innerHTML = "";
        if (pickQueue.length > 0) {
          const summary = document.createElement("div");
          summary.className = "d-flex flex-wrap gap-1 align-items-center";
          summary.innerHTML = '<small class="text-muted me-1">优先级:</small>';
          pickQueue.forEach((id, index) => {
            const chip = document.createElement("span");
            chip.className =
              index === 0 ? "badge bg-primary" : "badge bg-secondary";
            chip.style.fontSize = "0.75rem";
            chip.textContent = `${index + 1}. ID ${id}`;
            summary.appendChild(chip);
          });
          pickFallbackListEl.appendChild(summary);
        }
      }
    }
    autoBanPickBtn.addEventListener("click", () => {
      if (!isLCUConnected()) {
        showInlineMessage(
          "无法启动自动Ban/Pick：未检测到LCU连接，请先确保客户端已运行并且LCU已连接。",
          { level: "error", timeout: 8000 }
        );
        return;
      }

      if (!autoBanPickRunning) {
        // Get champion IDs from selectors
        rebuildQueueFromSelectors();
        const banId = banQueue[0] || null;
        const pickId = pickQueue[0] || null;

        const banCandidates = [...banQueue];
        const pickCandidates = [...pickQueue];

        // Start with configuration (包含备选队列)
        startAutoBanPick({
          ban_champion_id: banId,
          pick_champion_id: pickId,
          ban_candidates: banCandidates,
          pick_candidates: pickCandidates,
        });
        autoBanPickRunning = true;
        autoBanPickBtn.innerHTML =
          '<i class="bi bi-stop-circle-fill me-1"></i> 停止 Ban/Pick';
        autoBanPickBtn.classList.remove("btn-warning");
        autoBanPickBtn.classList.add("btn-danger");
        showInlineMessage(
          `自动Ban/Pick已启动 (Ban: ${banId || "未设置"}, Pick: ${
            pickId || "未设置"
          })`,
          { level: "info" }
        );
        saveAutoFeatureStates();
      } else {
        // Stop
        stopAutoBanPick();
        autoBanPickRunning = false;
        autoBanPickBtn.innerHTML =
          '<i class="bi bi-lightning-charge-fill me-1"></i> 启动自动 Ban/Pick';
        autoBanPickBtn.classList.remove("btn-danger");
        autoBanPickBtn.classList.add("btn-warning");
        showInlineMessage("自动Ban/Pick已停止", { level: "info" });
        saveAutoFeatureStates();
      }
    });

    // 监听所有 Ban 选择器的变更
    banChampionSelectors.forEach((selector, index) => {
      if (selector) {
        document
          .getElementById(`ban-champion-selector-${index + 1}`)
          .addEventListener("championChanged", (e) => {
            rebuildQueueFromSelectors();
            const banId = banQueue[0] || null;
            const pickId = pickQueue[0] || null;
            configureBanPick({
              ban_champion_id: banId,
              pick_champion_id: pickId,
              ban_candidates: [...banQueue],
              pick_candidates: [...pickQueue],
            });
          });
      }
    });

    // 监听所有 Pick 选择器的变更
    pickChampionSelectors.forEach((selector, index) => {
      if (selector) {
        document
          .getElementById(`pick-champion-selector-${index + 1}`)
          .addEventListener("championChanged", (e) => {
            rebuildQueueFromSelectors();
            const banId = banQueue[0] || null;
            const pickId = pickQueue[0] || null;
            configureBanPick({
              ban_champion_id: banId,
              pick_champion_id: pickId,
              ban_candidates: [...banQueue],
              pick_candidates: [...pickQueue],
            });
          });
      }
    });

    // 页面加载时恢复上次的选择
    loadSelectionsFromStorage();
  }

  // 在 socket 连接后恢复自动化功能状态
  socket.on("connect", () => {
    setTimeout(() => {
      restoreAutoFeatureStates();
    }, 1000); // 等待 LCU 连接状态稳定
  });
});
// (removed duplicate legacy module block)
