<!-- Badges -->

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE) [![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/) [![CI](https://github.com/ByteFlowing1337/LOL/actions/workflows/ci.yml/badge.svg)](https://github.com/ByteFlowing1337/LOL/actions)

# 🎮 LCU-UI

> **League Client Update - User Interface**  
> 英雄联盟客户端辅助工具 - 现代化 Web 界面

中文 / Chinese

这是一个轻量级的 League of Legends 辅助 WebUI，提供：

- 自动接受对局（Auto Accept）
- 敌我分析（OP.GG 战绩查询辅助）
- 实时对局页面和 WebSocket 推送

English

A lightweight Web UI for League of Legends helper features:

- Auto-accept matches
- Teammate / enemy quick analysis (OP.GG lookups)
- Live-game view with WebSocket updates

---

## 快速开始 Quick Start (Windows PowerShell)

```powershell
# 在项目根目录
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
npm install
npm run build
uv run app.py
```

Then open the printed address (e.g. http://127.0.0.1:5000) in your browser.

## CI / 自动化示例 CI example

A minimal GitHub Actions workflow is included at `.github/workflows/ci.yml`. It currently:

- Installs the package in editable mode
- Runs a trivial import check (`import app`) to ensure the code imports cleanly

这是用于在 PR 或 push 时做基础检查的示例工作流，后续可以扩展为运行测试、 lint、打包等。

---

## 关于 LCU / LCU connection

- 自动接受或分析功能需要检测到 LCU（League Client）凭证才能启动。
- 如果页面显示 LCU 未连接，请确保客户端正在运行并且允许访问本地 API。

---

## 贡献 Contributing

欢迎提交 PR。建议流程：

1. Fork → 新分支
2. 修改与测试
3. 提交 PR 并描述修改意图

---

## License

MIT — see `LICENSE` for release notes.

If you'd like a localized Chinese-only README or a longer English README with screenshots and demos, I can expand this further.
