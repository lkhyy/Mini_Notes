# mini-notes

最小笔记 Anna App：**bundle**（浏览器 UI）、**manifest**（权限与声明）、**executas**（本地 `tool-dev-mini-notes` 进程）。总结功能只通过 `anna.tools.invoke` 调 Executa，笔记数据通过 `anna.storage` 持久化。

---

## 如何安装依赖

### node22 安装

```bash
# 1. 下载官方 Node.js 22 (最新版) x86_64 二进制包
sudo wget https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz
# 2. 解压到系统全局目录
sudo tar -xJf node-v22.14.0-linux-x64.tar.xz -C /usr/local/
# 3. 创建软链接（让 node/npm 全局可用）
sudo ln -s /usr/local/node-v22.14.0-linux-x64/bin/node /usr/local/bin/
sudo ln -s /usr/local/node-v22.14.0-linux-x64/bin/npm /usr/local/bin/
sudo ln -s /usr/local/node-v22.14.0-linux-x64/bin/npx /usr/local/bin/
# 4. 验证安装（显示版本号即成功）
node -v
npm -v
```

### uv安装

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### anna-app/cli安装

```bash
sudo npm i -g @anna-ai/cli
anna-app --help
```

### uv设置国内镜像（推荐）

```bash
echo 'export UV_DEFAULT_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"' >> ~/.bashrc
source ~/.bashrc
```

### Executa 本地环境

```bash
cd executas/mini-notes
```

（说明：上述 `cd` 相对于本仓库根目录 `mini-notes/`。）

---

## 快速开始

```bash
cd mini-notes
anna-app validate
anna-app validate --strict
anna-app dev
```

## 手动测试 Executa（不经浏览器）

在 **仓库根目录 `mini-notes/`** 下执行（`python3` 的路径相对于根目录）：

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"describe"}' \
  '{"jsonrpc":"2.0","id":2,"method":"invoke","params":{"tool":"summarize","arguments":{"notes":[]}}}' \
  | python3 executas/mini-notes/mini_notes_plugin.py
```

或在 `**executas/mini-notes/**` 目录下执行：

```bash
cd executas/mini-notes
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"describe"}' \
  '{"jsonrpc":"2.0","id":2,"method":"invoke","params":{"tool":"summarize","arguments":{"notes":[]}}}' \
  | python3 mini_notes_plugin.py
```

---

## 解释 bundle / manifest / executas 的关系

三者是一套 Anna App 的固定分工：**bundle** 只通过 SDK 与宿主对话；**manifest** 声明宿主允许哪些 API、注册哪些工具；**executas** 实现工具进程（stdio JSON-RPC）。对应关系见下表。


| 部分                       | 作用                                                                                                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| **bundle/**              | 静态前端：`index.html` + `app.js`，只用 SDK 调 `storage` / `tools.invoke` / `window`。                                                         |
| **manifest.json**        | 声明权限（如 `tools.invoke`、`storage.`*）、`host_api` 白名单、`required_executas` 里挂上 `tool-dev-mini-notes`。                                     |
| **executas/mini-notes/** | `pyproject.toml` 定义入口脚本 `tool-dev-mini-notes` → `mini_notes_plugin:main`；**stdio JSON-RPC** 实现 `describe` / `invoke`（如 `summarize`）。 |


