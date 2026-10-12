# 🐋 大胖鱼 AI 聊天 (BigFatFish)

Windows 桌面 AI 聊天客户端，tkinter 原生，零第三方依赖。

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
