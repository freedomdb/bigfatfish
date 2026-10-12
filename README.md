# 🐋 大胖鱼 AI 聊天 (BigFatFish)

Windows 桌面 AI 聊天客户端，tkinter 原生，零第三方依赖。

## 开发故事

这个项目是 2026 年 10 月 12 日一个下午手搓出来的。

起因是大兄弟（用户）在 B 站看到 OpenRouter 免费模型的教程，想整个 Windows 桌面客户端。小老弟（我是 Muse，Meta 的 AI 助手）负责写代码，大兄弟负责实测——他测、我改，来回折腾了 20 来版：

- v1-v5：搭架子，浏览器版改桌面版，bat 中文乱码、emoji 按钮空白，逐个踩坑
- v6-v10：深色主题被嫌"太深了"，换浅色；历史记录选中态看不清，改蓝底白字
- v11-v14：加联网搜索，从 DuckDuckGo 爬虫换到 Bing，最后发现 OpenRouter 自带 web 插件，让 DeepSeek 自己搜——搜创业板涨幅前十直接出表格，成了
- v15-v19：链接可点击、联网按钮挪顶栏、文件按钮改"+",代理设置进设置页，发送按钮被输入框挤没又修回来

每个版本都是大兄弟截图反馈、小老弟当场改，名字"大胖鱼"是因为 DeepSeek 的鲸鱼标。

## 功能

- **458 个模型**：OpenRouter 全量模型，一键切换（DeepSeek 置顶）
- **流式输出**：打字机效果实时显示
- **联网搜索**：OpenRouter web 插件，AI 自己联网查资料（默认开启）
- **文件上传**：图片转 base64 走 vision 模型，文本直接内联
- **历史记录**：本地 JSON 存储，左侧列表切换
- **代理设置**：系统代理 / 直连 / 自定义
- **深浅主题**：一键切换
- **Token 统计**：顶栏实时显示消耗
- **可点击链接**：聊天中的 URL 蓝色下划线，点击浏览器打开
- **断线重试**：自动重试 3 次，指数退避
- **导出 Markdown**：一键导出对话

## 运行

需要 Python 3.8+（Windows 自带 tkinter，无需 pip 装任何东西）。

双击 `start-desktop.bat` 即可，或：

```bash
python app.py
```

首次运行点右上角 **设置** 填入 OpenRouter API Key（https://openrouter.ai/keys 免费获取）。

## 配置

`data/config.json`（首次运行自动创建）：
- `api_key`：OpenRouter API Key
- `default_model`：默认模型
- `temperature` / `max_tokens` / `system_prompt`
- `proxy_mode`：system / direct / custom
- `proxy_url`：自定义代理地址

## License

MIT
