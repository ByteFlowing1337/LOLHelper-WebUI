// main.js - module entrypoint (ES Module)
import { showInlineMessage, isLCUConnected, setLCUStatus, qs } from './modules/ui.js';
import { fetchSummonerStats, fetchTFTMatches } from './modules/api.js';
import { setupSocket } from './modules/socketHandler.js';

document.addEventListener('DOMContentLoaded', () => {
    const detectBtn = qs('detect-btn');
    const fetchBtn = qs('fetch-btn');
    const fetchTftBtn = qs('fetch-tft-btn');
    const summonerNameInput = qs('summoner-name-input');
    const resultsDiv = qs('results-area');
    const autoAcceptBtn = qs('auto-accept-btn');
    const autoAnalyzeBtn = qs('auto-analyze-btn');
    const realtimeStatus = qs('realtime-status');
    const teammateResultsDiv = qs('teammate-results-area');
    const enemyResultsDiv = qs('enemy-results-area');

    // socket handlers
    const { socket, startAutoAccept, startAutoAnalyze, stopAutoAccept, stopAutoAnalyze } = setupSocket({
        onConnect() {
            console.log('成功连接到WebSocket服务器!');
        },
        onStatusUpdate(data) {
            // Expect structured payload: { type: 'lcu'|'biz', message: '...' }
            const type = data.type || (data.data ? 'lcu' : 'biz');
            const message = data.message || data.data || '';

            if (type === 'lcu') {
                // connection-related message -> update LCU status box
                if (message.includes('成功')) setLCUStatus(message, 'ok');
                else if (message.includes('失败') || message.includes('无法')) setLCUStatus(message, 'err');
                else setLCUStatus(message, 'neutral');
            } else {
                // business message -> realtime area
                showInlineMessage(message, { level: 'info', timeout: 5000 });
            }
        },
        onEnemiesFound: async (data) => {
            realtimeStatus.textContent = `💥 发现 ${data.enemies.length} 名敌人! 正在分析战绩...`;
            realtimeStatus.className = 'badge bg-danger';
            enemyResultsDiv.innerHTML = '<h5 class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>敌方目标分析:</h5>';
            const ul = document.createElement('ul');
            ul.className = 'list-unstyled';
            enemyResultsDiv.appendChild(ul);

            const promises = data.enemies.map(enemy => {
                const li = document.createElement('li');
                li.className = 'd-flex flex-column border-bottom py-2 mb-2';
                const headerDiv = document.createElement('div');
                headerDiv.className = 'd-flex justify-content-between align-items-center';
                const riotIdLink = document.createElement('a');
                riotIdLink.href = `/summoner/${encodeURIComponent(enemy.gameName + '#' + enemy.tagLine)}`;
                riotIdLink.target = '_blank';
                riotIdLink.rel = 'noopener noreferrer';
                riotIdLink.className = 'fw-bold text-danger text-decoration-none';
                riotIdLink.style.cursor = 'pointer';
                riotIdLink.innerHTML = `<i class="bi bi-person-x-fill me-1"></i>${enemy.gameName}#${enemy.tagLine}`;
                riotIdLink.title = '点击查看详细战绩';
                headerDiv.appendChild(riotIdLink);
                if (enemy.championId && enemy.championId !== 'Unknown') {
                    const championSpan = document.createElement('span');
                    championSpan.className = 'badge bg-dark';
                    championSpan.textContent = enemy.championId;
                    headerDiv.appendChild(championSpan);
                }
                li.appendChild(headerDiv);
                const statsDisplay = document.createElement('div');
                statsDisplay.textContent = '⏳ 查询中...';
                statsDisplay.className = 'text-muted small mt-1';
                li.appendChild(statsDisplay);
                ul.appendChild(li);
                return fetchSummonerStats(enemy.gameName, enemy.tagLine, statsDisplay);
            });

            await Promise.all(promises);
            realtimeStatus.textContent = `✅ 敌方战绩分析完成!`;
            realtimeStatus.className = 'badge bg-success';
        },
        onTeammatesFound: async (data) => {
            realtimeStatus.textContent = `👥 发现 ${data.teammates.length} 名队友! 正在分析战绩...`;
            realtimeStatus.className = 'badge bg-info';
            teammateResultsDiv.innerHTML = '<h5 class="text-primary"><i class="bi bi-people-fill me-2"></i>本局队友分析:</h5>';
            const ul = document.createElement('ul');
            ul.className = 'list-unstyled';
            teammateResultsDiv.appendChild(ul);

            const promises = data.teammates.map(tm => {
                const li = document.createElement('li');
                li.className = 'd-flex flex-column border-bottom py-2 mb-2';
                const headerDiv = document.createElement('div');
                headerDiv.className = 'd-flex justify-content-between align-items-center';
                const riotIdLink = document.createElement('a');
                riotIdLink.href = `/summoner/${encodeURIComponent(tm.gameName + '#' + tm.tagLine)}`;
                riotIdLink.target = '_blank';
                riotIdLink.rel = 'noopener noreferrer';
                riotIdLink.className = 'fw-bold text-primary text-decoration-none';
                riotIdLink.style.cursor = 'pointer';
                riotIdLink.innerHTML = `<i class="bi bi-person-check-fill me-1"></i>${tm.gameName}#${tm.tagLine}`;
                riotIdLink.title = '点击查看详细战绩';
                headerDiv.appendChild(riotIdLink);
                li.appendChild(headerDiv);
                const statsDisplay = document.createElement('div');
                statsDisplay.textContent = '⏳ 查询中...';
                statsDisplay.className = 'text-muted small mt-1';
                li.appendChild(statsDisplay);
                ul.appendChild(li);
                return fetchSummonerStats(tm.gameName, tm.tagLine, statsDisplay);
            });

            await Promise.all(promises);
            realtimeStatus.textContent = `✅ 队友分析完成! 等待游戏开始...`;
            realtimeStatus.className = 'badge bg-success';
            console.log('队友战绩分析全部完成');
        }
    });

    // --- UI actions ---
    fetchBtn.addEventListener('click', () => {
        const summonerName = summonerNameInput.value.trim();
        if (!summonerName) {
            showInlineMessage('请输入召唤师名称 (格式: 名称#Tag)', { level: 'warn' });
            return;
        }
        const encodedName = encodeURIComponent(summonerName);
        // Open summoner detail in a new tab instead of replacing current page
        window.open(`/summoner/${encodedName}`, '_blank', 'noopener');
    });

    if (fetchTftBtn) {
        fetchTftBtn.addEventListener('click', () => {
            const summonerName = summonerNameInput.value.trim();
            if (!summonerName) {
                showInlineMessage('请输入召唤师名称 (格式: 名称#Tag)', { level: 'warn' });
                return;
            }
            const encodedName = encodeURIComponent(summonerName);
            // open a dedicated TFT summoner page in a new tab
            window.open(`/tft_summoner/${encodedName}`, '_blank', 'noopener');
        });
    }

    let autoAcceptRunning = false;
    let autoAnalyzeRunning = false;

    autoAcceptBtn.addEventListener('click', () => {
        if (!isLCUConnected()) {
            showInlineMessage('无法启动自动接受：未检测到LCU连接，请先确保客户端已运行并且LCU已连接。', { level: 'error', timeout: 8000 });
            return;
        }
        
        if (!autoAcceptRunning) {
            // 启动
            startAutoAccept();
            autoAcceptRunning = true;
            autoAcceptBtn.innerHTML = '<i class="bi bi-stop-circle-fill me-1"></i> 停止接受';
            autoAcceptBtn.classList.remove('btn-success');
            autoAcceptBtn.classList.add('btn-danger');
            showInlineMessage('自动接受对局已启动', { level: 'info' });
        } else {
            // 停止
            stopAutoAccept();
            autoAcceptRunning = false;
            autoAcceptBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> 自动接受对局';
            autoAcceptBtn.classList.remove('btn-danger');
            autoAcceptBtn.classList.add('btn-success');
            showInlineMessage('自动接受对局已停止', { level: 'info' });
        }
    });

    autoAnalyzeBtn.addEventListener('click', () => {
        if (!isLCUConnected()) {
            showInlineMessage('无法启动敌我分析：未检测到LCU连接，请先确保客户端已运行并且LCU已连接。', { level: 'error', timeout: 8000 });
            return;
        }
        
        if (!autoAnalyzeRunning) {
            // 启动
            startAutoAnalyze();
            autoAnalyzeRunning = true;
            autoAnalyzeBtn.innerHTML = '<i class="bi bi-stop-circle-fill me-1"></i> 停止分析';
            autoAnalyzeBtn.classList.remove('btn-primary');
            autoAnalyzeBtn.classList.add('btn-danger');
            showInlineMessage('敌我分析已启动', { level: 'info' });
        } else {
            // 停止
            stopAutoAnalyze();
            autoAnalyzeRunning = false;
            autoAnalyzeBtn.innerHTML = '<i class="bi bi-bar-chart-fill me-1"></i> 敌我分析';
            autoAnalyzeBtn.classList.remove('btn-danger');
            autoAnalyzeBtn.classList.add('btn-primary');
            showInlineMessage('敌我分析已停止', { level: 'info' });
        }
    });
});
// (removed duplicate legacy module block)
