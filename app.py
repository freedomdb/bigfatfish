#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大胖鱼 AI 聊天客户端 - 桌面版
tkinter 原生窗口，无需浏览器，Python 标准库零依赖
"""
import json
import os
import sys
import threading
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog, filedialog
import base64
import mimetypes

# 文件类型
IMG_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
TEXT_EXT = {'.txt', '.md', '.py', '.json', '.csv', '.log', '.html', '.xml', '.yaml', '.yml', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.go', '.rs', '.sql'}
MAX_TEXT_CHARS = 100000

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
HISTORY_DIR = os.path.join(DATA_DIR, 'history')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

OPENROUTER_BASE = 'https://openrouter.ai/api/v1'

# 配色主题
THEMES = {
    'light': {
        'BG': '#ffffff', 'BG2': '#f0f2f5', 'BG3': '#e2e6eb',
        'FG': '#000000', 'MUTED': '#4a5568', 'ACCENT': '#0969da',
        'ACCENT_HOVER': '#0550ae', 'USER_BG': '#cce5ff', 'AI_BG': '#f0f2f5',
        'BORDER': '#c0c8d0', 'CURSOR': '#000000', 'SELECT_BG': '#b6e3ff',
    },
    'dark': {
        'BG': '#0d1117', 'BG2': '#161b22', 'BG3': '#21262d',
        'FG': '#e6edf3', 'MUTED': '#7d8590', 'ACCENT': '#2f81f7',
        'ACCENT_HOVER': '#1f6feb', 'USER_BG': '#1c2a3a', 'AI_BG': '#161b22',
        'BORDER': '#30363d', 'CURSOR': '#ffffff', 'SELECT_BG': '#264f78',
    },
}

def get_theme(name='light'):
    return THEMES.get(name, THEMES['light'])

def apply_theme(name='light'):
    """应用主题到模块全局变量"""
    global BG, BG2, BG3, FG, MUTED, ACCENT, ACCENT_HOVER, USER_BG, AI_BG, BORDER
    t = get_theme(name)
    BG = t['BG']; BG2 = t['BG2']; BG3 = t['BG3']
    FG = t['FG']; MUTED = t['MUTED']; ACCENT = t['ACCENT']
    ACCENT_HOVER = t['ACCENT_HOVER']
    USER_BG = t['USER_BG']; AI_BG = t['AI_BG']
    BORDER = t['BORDER']

# 默认浅色（启动时根据配置覆盖）
_current = get_theme('light')
BG = _current['BG']; BG2 = _current['BG2']; BG3 = _current['BG3']
FG = _current['FG']; MUTED = _current['MUTED']; ACCENT = _current['ACCENT']
ACCENT_HOVER = _current['ACCENT_HOVER']
USER_BG = _current['USER_BG']; AI_BG = _current['AI_BG']
BORDER = _current['BORDER']

DEFAULT_CONFIG = {
    'api_key': '', 'default_model': 'deepseek/deepseek-v4.1-flash',
    'temperature': 0.7, 'max_tokens': 4096, 'system_prompt': '',
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items(): cfg.setdefault(k, v)
                return cfg
        except: pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def make_hover(btn, normal_bg, hover_bg):
    """按钮悬停效果"""
    btn.bind('<Enter>', lambda e: btn.config(bg=hover_bg))
    btn.bind('<Leave>', lambda e: btn.config(bg=normal_bg))

def process_file(path):
    """处理上传的文件，返回 (描述文本, openai格式content块列表)"""
    ext = os.path.splitext(path)[1].lower()
    name = os.path.basename(path)
    if ext in IMG_EXT:
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        mime = mimetypes.guess_type(path)[0] or 'image/png'
        return f'[图片: {name}]', [{'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{b64}'}}]
    elif ext in TEXT_EXT:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read(MAX_TEXT_CHARS)
        return f'[文件: {name}]\n{text}', [{'type': 'text', 'text': f'[文件 {name} 内容如下]\n{text}'}]
    else:
        return f'[文件: {name} (不支持预览)]', [{'type': 'text', 'text': f'[用户上传了文件: {name}]'}]

def api_call(path, api_key, method='GET', data=None, stream_cb=None, usage_cb=None, retries=3, proxy_cfg=None):
    url = OPENROUTER_BASE + path
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json',
               'HTTP-Referer': 'https://localhost', 'X-Title': 'BigFatFish Desktop'}
    body = json.dumps(data).encode('utf-8') if data else None
    # 代理配置
    opener = None
    if proxy_cfg:
        mode = proxy_cfg.get('proxy_mode', 'system')
        if mode == 'direct':
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        elif mode == 'custom' and proxy_cfg.get('proxy_url'):
            purl = proxy_cfg['proxy_url']
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({'http': purl, 'https': purl}))
        # system 模式：urllib 默认走系统代理，不用特殊处理
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            if opener:
                resp = opener.open(req, timeout=180)
            else:
                resp = urllib.request.urlopen(req, timeout=180)
            if stream_cb:
                buf = ''
                for chunk in resp:
                    buf += chunk.decode('utf-8', errors='ignore')
                    while '\n' in buf:
                        line, buf = buf.split('\n', 1)
                        line = line.strip()
                        if line.startswith('data:'):
                            p = line[5:].strip()
                            if p == '[DONE]': continue
                            try:
                                j = json.loads(p)
                                delta = j.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if delta: stream_cb(delta)
                                u = j.get('usage')
                                if u and usage_cb:
                                    usage_cb(u.get('prompt_tokens', 0), u.get('completion_tokens', 0))
                            except: pass
                return
            else:
                return json.loads(resp.read().decode('utf-8'))
        except (urllib.error.URLError, ConnectionResetError, TimeoutError) as e:
            last_err = e
            if attempt < retries - 1:
                import time
                time.sleep(2 ** attempt)  # 指数退避：2s, 4s
                continue
            raise
        except Exception:
            raise
    if last_err:
        raise last_err

class BigFatFishApp:
    def __init__(self, root):
        self.root = root
        self.root.title('🐋 大胖鱼 AI 聊天')
        self.root.geometry('1050x720')
        self.root.minsize(800, 550)
        self.cfg = load_config()
        # 应用主题
        self.theme = self.cfg.get('theme', 'light')
        apply_theme(self.theme)
        self.root.configure(bg=BG)
        # 设置 ttk 主题让下拉框好看
        try:
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('TCombobox', fieldbackground=BG3, background=BG3,
                            foreground=FG, arrowcolor=MUTED, borderwidth=0)
        except: pass
        # 设置 ttk 主题让下拉框好看
        try:
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('TCombobox', fieldbackground=BG3, background=BG3,
                            foreground=FG, arrowcolor=MUTED, borderwidth=0)
        except: pass
        self.cfg = load_config()
        self.messages = []
        self.current_id = None
        self.models = []
        self.sending = False
        self.stop_event = threading.Event()
        self.token_stats = {'prompt': 0, 'completion': 0}
        self.web_search_enabled = True  # 联网默认开启
        self.build_ui()
        self.render_all()  # 显示欢迎页
        self.load_models_thread()
        self.load_history_list()
        self.input_text.focus_set()
        if not self.cfg.get('api_key'):
            self.root.after(500, lambda: messagebox.showinfo('提示', '请先点右上角"设置"填入 OpenRouter API Key'))

    def build_ui(self):
        # 初始化附件列表
        self.attachments = []  # [(path, 描述, content块)]

        # 顶栏 - Codex 风格简洁
        top = tk.Frame(self.root, bg=BG2, height=48)
        top.pack(fill='x')
        top.pack_propagate(False)
        tk.Label(top, text='🐋 大胖鱼', font=('Microsoft YaHei', 13, 'bold'), bg=BG2, fg=FG).pack(side='left', padx=14, pady=10)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(top, textvariable=self.model_var, width=42, state='readonly', font=('Microsoft YaHei', 10))
        self.model_combo.pack(side='left', padx=8, pady=10)
        btn_export = tk.Button(top, text='导出', command=self.export_chat, bg=BG3, fg=FG, relief='flat',
                               font=('Microsoft YaHei', 10), padx=14, pady=4, cursor='hand2')
        btn_export.pack(side='right', padx=4, pady=10)
        make_hover(btn_export, BG3, '#30363d')
        btn_theme = tk.Button(top, text='🌙 深色' if self.theme == 'light' else '☀️ 浅色', command=self.toggle_theme,
                               bg=BG3, fg=FG, relief='flat',
                               font=('Microsoft YaHei', 10), padx=14, pady=4, cursor='hand2')
        btn_theme.pack(side='right', padx=4, pady=10)
        make_hover(btn_theme, BG3, '#30363d')
        self.theme_btn = btn_theme
        btn_regen = tk.Button(top, text='🔄 重来', command=self.regenerate, bg=BG3, fg=FG, relief='flat',
                               font=('Microsoft YaHei', 10), padx=14, pady=4, cursor='hand2')
        btn_regen.pack(side='right', padx=4, pady=10)
        make_hover(btn_regen, BG3, '#30363d')
        # Token 统计
        self.token_var = tk.StringVar(value='')
        tk.Label(top, textvariable=self.token_var, bg=BG2, fg=MUTED,
                 font=('Microsoft YaHei', 9)).pack(side='right', padx=8)
        btn_settings = tk.Button(top, text='⚙ 设置', command=self.open_settings, bg=BG3, fg=FG, relief='flat',
                                  font=('Microsoft YaHei', 10), padx=14, pady=4, cursor='hand2')
        btn_settings.pack(side='right', padx=8, pady=10)
        make_hover(btn_settings, BG3, '#30363d')

        # 联网开关（顶栏，设置旁边，默认开启）
        self.web_btn = tk.Button(top, text='🌐 联网:开', command=self.toggle_web,
                                bg=BG3, fg=ACCENT, relief='flat', font=('Microsoft YaHei', 10),
                                cursor='hand2', padx=10, pady=4)
        self.web_btn.pack(side='right', padx=2, pady=10)
        make_hover(self.web_btn, BG3, '#30363d')

        # 主体
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill='both', expand=True)

        # 左侧历史
        left = tk.Frame(body, bg=BG2, width=210)
        left.pack(side='left', fill='y')
        left.pack_propagate(False)
        btn_new = tk.Button(left, text='+ 新对话', command=self.new_chat, bg=ACCENT, fg='white',
                  font=('Microsoft YaHei', 10, 'bold'), relief='flat', pady=8, cursor='hand2')
        btn_new.pack(fill='x', padx=10, pady=10)
        make_hover(btn_new, ACCENT, ACCENT_HOVER)
        self.history_box = tk.Listbox(left, bg=BG2, fg=FG, relief='flat', highlightthickness=0,
                                       font=('Microsoft YaHei', 10), selectbackground=ACCENT,
                                       selectforeground='white', activestyle='none')
        self.history_box.pack(fill='both', expand=True, padx=10, pady=4)
        self.history_box.bind('<<ListboxSelect>>', self.on_history_select)
        self.history_box.bind('<Delete>', lambda e: self.delete_history())
        btn_del = tk.Button(left, text='删除选中', command=self.delete_history, bg=BG3, fg=MUTED,
                            relief='flat', font=('Microsoft YaHei', 9), cursor='hand2')
        btn_del.pack(fill='x', padx=10, pady=8)
        make_hover(btn_del, BG3, '#30363d')

        # 右侧聊天 - 先放底部输入区，再放聊天区
        right = tk.Frame(body, bg=BG)
        right.pack(side='right', fill='both', expand=True)

        # 状态栏（最底部）
        self.status_var = tk.StringVar()
        tk.Label(right, textvariable=self.status_var, bg=BG, fg=MUTED,
                 font=('Microsoft YaHei', 9), anchor='w').pack(side='bottom', fill='x', padx=16, pady=(0,6))

        # 输入区（底部固定）
        bottom = tk.Frame(right, bg=BG2, height=80)
        bottom.pack(side='bottom', fill='x', padx=12, pady=(0,8))
        bottom.pack_propagate(False)
        input_inner = tk.Frame(bottom, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        input_inner.pack(fill='both', expand=True, padx=2, pady=2)

        # 文件上传按钮
        btn_upload = tk.Button(input_inner, text='+', command=self.upload_file,
                                bg=BG3, fg=FG, relief='flat', font=('Microsoft YaHei', 12, 'bold'),
                                cursor='hand2', padx=10, pady=4)
        btn_upload.pack(side='left', padx=6, pady=8)
        make_hover(btn_upload, BG3, '#30363d')

        self.input_text = tk.Text(input_inner, bg=BG, fg=FG, font=('Microsoft YaHei', 11),
                                   height=3, relief='flat', padx=8, pady=8,
                                   insertbackground='#1f2328', insertwidth=3,
                                   selectbackground='#b6e3ff', cursor='xterm',
                                   highlightthickness=0, bd=0)
        self.input_text.bind('<Return>', self.on_enter)
        self.send_btn = tk.Button(input_inner, text='发送', command=self.send, bg=ACCENT, fg='white',
                                   font=('Microsoft YaHei', 11, 'bold'), relief='flat', padx=24, cursor='hand2')
        # 先 pack 固定按钮，最后 pack 输入框（expand 会吃掉剩余空间）
        self.send_btn.pack(side='right', padx=8, pady=8)
        self.input_text.pack(side='left', fill='both', expand=True, pady=4)
        make_hover(self.send_btn, ACCENT, ACCENT_HOVER)
        # 停止按钮（发送时显示）
        self.stop_btn = tk.Button(input_inner, text='⏹ 停止', command=self.stop_gen, bg='#da3633', fg='white',
                                   font=('Microsoft YaHei', 11, 'bold'), relief='flat', padx=16, cursor='hand2')

        # 附件显示条（输入区上方）
        self.attach_frame = tk.Frame(right, bg=BG2)
        self.attach_label = tk.Label(self.attach_frame, bg=BG2, fg=ACCENT,
                                      font=('Microsoft YaHei', 10), anchor='w')
        self.attach_label.pack(side='left', padx=10, pady=4)
        btn_clear = tk.Button(self.attach_frame, text='✕ 清除', command=self.clear_attachments,
                               bg=BG2, fg=MUTED, relief='flat', font=('Microsoft YaHei', 9), cursor='hand2')
        btn_clear.pack(side='right', padx=8)

        # 聊天区（填充剩余空间）
        self.chat_text = scrolledtext.ScrolledText(right, bg=BG, fg=FG, wrap='word',
            font=('Microsoft YaHei', 11), relief='flat', padx=16, pady=12, state='disabled',
            spacing1=4, spacing3=4, cursor='arrow', highlightthickness=0, bd=0,
            selectbackground=BG3, selectforeground=FG)
        self.chat_text.pack(fill='both', expand=True, padx=4, pady=4)
        # 美化滚动条
        try:
            sb = self.chat_text.vbar
            sb.config(bg=BG2, troughcolor=BG, relief='flat', width=10,
                      activebackground=BG3, highlightthickness=0, bd=0)
        except: pass
        self.chat_text.tag_config('user', background=USER_BG, lmargin1=60, rmargin=12,
                                   spacing1=8, spacing3=8, borderwidth=12, relief='flat')
        self.chat_text.tag_config('ai', background=BG2, lmargin1=12, rmargin=60,
                                   spacing1=8, spacing3=8, borderwidth=12, relief='flat')
        self.chat_text.tag_config('meta', foreground=MUTED, font=('Microsoft YaHei', 9))
        self.chat_text.tag_config('attach', foreground=ACCENT, font=('Microsoft YaHei', 10))
        self.chat_text.tag_config('welcome', foreground=MUTED, font=('Microsoft YaHei', 12),
                                   justify='center', spacing1=20)
        # Markdown 样式
        self.chat_text.tag_config('md_bold', font=('Microsoft YaHei', 11, 'bold'))
        self.chat_text.tag_config('md_code', font=('Consolas', 10), background='#f6f8fa',
                                   foreground='#24292f')
        self.chat_text.tag_config('md_h', font=('Microsoft YaHei', 13, 'bold'),
                                   foreground='#1f2328', spacing1=6)

    def upload_file(self):
        """选择文件上传"""
        path = filedialog.askopenfilename(
            title='选择文件',
            filetypes=[
                ('支持的文件', '*.png *.jpg *.jpeg *.gif *.webp *.bmp *.txt *.md *.py *.json *.csv *.log'),
                ('图片', '*.png *.jpg *.jpeg *.gif *.webp *.bmp'),
                ('文本', '*.txt *.md *.py *.json *.csv *.log'),
                ('所有文件', '*.*'),
            ])
        if not path:
            return
        try:
            desc, blocks = process_file(path)
            self.attachments.append((path, desc, blocks))
            self.update_attach_display()
            self.set_status(f'已添加附件: {os.path.basename(path)}')
        except Exception as e:
            messagebox.showerror('错误', f'文件处理失败: {e}')

    def update_attach_display(self):
        if self.attachments:
            names = [os.path.basename(a[0]) for a in self.attachments]
            self.attach_label.config(text='[附件] ' + ', '.join(names))
            self.attach_frame.pack(fill='x', padx=12, pady=(0,4), before=self.chat_text.master.winfo_children()[-2])
        else:
            self.attach_frame.pack_forget()

    def toggle_web(self):
        """切换联网搜索开关"""
        self.web_search_enabled = not self.web_search_enabled
        if self.web_search_enabled:
            self.web_btn.config(text='🌐 联网:开', fg=ACCENT)
            self.set_status('联网搜索已开启')
        else:
            self.web_btn.config(text='🌐 联网:关', fg=MUTED)
            self.set_status('联网搜索已关闭')

    def clear_attachments(self):
        self.attachments = []
        self.update_attach_display()

    def stop_gen(self):
        """停止生成"""
        self.stop_event.set()
        self.set_status('已停止')

    def regenerate(self):
        """重新生成最后一条 AI 回复"""
        if self.sending:
            messagebox.showinfo('提示', '正在生成中，请先停止')
            return
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i]['role'] == 'assistant':
                del self.messages[i]
                break
        else:
            messagebox.showinfo('提示', '没有可重新生成的回复')
            return
        self.render_all()
        model = self.model_var.get()
        if not model:
            return
        self.sending = True
        self.stop_event.clear()
        self.send_btn.pack_forget()
        self.stop_btn.pack(side='right', padx=8, pady=8)
        self.set_status('🐋 重新生成中...')
        threading.Thread(target=self._do_send, args=(model,), daemon=True).start()

    def toggle_theme(self):
        """切换深浅色主题"""
        self.theme = 'dark' if self.theme == 'light' else 'light'
        self.cfg['theme'] = self.theme
        save_config(self.cfg)
        self.theme_btn.config(text='🌙 深色' if self.theme == 'light' else '☀️ 浅色')
        messagebox.showinfo('提示', f'已切换为{"深色" if self.theme == "dark" else "浅色"}主题，重启生效')

    def update_token_display(self):
        p = self.token_stats['prompt']
        c = self.token_stats['completion']
        if p or c:
            self.token_var.set(f'📊 {p + c} tokens')

    def on_enter(self, e):
        if not e.state & 0x1:  # 非 Shift+Enter
            self.send()
            return 'break'

    def set_status(self, s):
        self.status_var.set(s)

    def load_models_thread(self):
        threading.Thread(target=self._load_models, daemon=True).start()

    def _load_models(self):
        if not self.cfg.get('api_key'):
            self.root.after(0, lambda: self.set_status('未配置 API Key'))
            return
        try:
            data = api_call('/models', self.cfg['api_key'], proxy_cfg=self.cfg)
            self.models = data.get('data', [])
            ds = [m['id'] for m in self.models if m['id'].startswith('deepseek/')]
            free = [m['id'] for m in self.models if m['id'].endswith(':free') and not m['id'].startswith('deepseek/')]
            rest = [m['id'] for m in self.models if not m['id'].startswith('deepseek/') and not m['id'].endswith(':free')]
            ordered = ds + free + rest[:200]
            def update():
                self.model_combo['values'] = ordered
                dm = self.cfg.get('default_model')
                self.model_var.set(dm if dm in ordered else (ordered[0] if ordered else ''))
                self.set_status(f'已加载 {len(self.models)} 个模型')
            self.root.after(0, update)
        except Exception as e:
            self.root.after(0, lambda: self.set_status(f'模型加载失败: {e}'))

    def append_msg(self, role, content, model=''):
        import re
        import webbrowser
        self.chat_text.config(state='normal')
        tag = 'user' if role == 'user' else 'ai'
        prefix = '👤 你\n' if role == 'user' else '🐋 AI\n'
        self.chat_text.insert('end', prefix, 'meta')
        # 插入内容（带 Markdown 解析）
        start_idx = self.chat_text.index('end-1c')
        if role == 'assistant':
            self._insert_markdown(content + '\n', tag)
        else:
            self.chat_text.insert('end', content + '\n', tag)
        # 查找 URL 并设为可点击
        url_pattern = r'https?://[^\s\)\]]+'
        text_start = start_idx
        for m in re.finditer(url_pattern, content):
            s = f"{text_start}+{m.start()}c"
            e = f"{text_start}+{m.end()}c"
            url = m.group(0)
            link_tag = f'link_{hash(url) % 100000}'
            self.chat_text.tag_config(link_tag, foreground='#0969da', underline=True)
            self.chat_text.tag_add(link_tag, s, e)
            self.chat_text.tag_bind(link_tag, '<Button-1>', lambda ev, u=url: webbrowser.open(u))
            self.chat_text.tag_bind(link_tag, '<Enter>', lambda ev: self.chat_text.config(cursor='hand2'))
            self.chat_text.tag_bind(link_tag, '<Leave>', lambda ev: self.chat_text.config(cursor='arrow'))
        if model:
            self.chat_text.insert('end', model + '\n', 'meta')
        self.chat_text.insert('end', '\n')
        self.chat_text.config(state='disabled')
        self.chat_text.see('end')

    def _insert_markdown(self, text, base_tag):
        """简单 Markdown 渲染：加粗、行内代码、标题、链接"""
        import re
        import webbrowser
        # 按行处理标题
        for line in text.split('\n'):
            # 标题行
            hm = re.match(r'^(#{1,3})\s+(.*)', line)
            if hm:
                self.chat_text.insert('end', hm.group(2) + '\n', (base_tag, 'md_h'))
                continue
            # 行内：加粗、代码、链接
            pos = 0
            for m in re.finditer(r'(\*\*(.+?)\*\*)|(`(.+?)`)|(\[([^\]]+)\]\((https?://[^\)]+)\))', line):
                # 普通文本
                if m.start() > pos:
                    self.chat_text.insert('end', line[pos:m.start()], base_tag)
                if m.group(2):  # 加粗
                    self.chat_text.insert('end', m.group(2), (base_tag, 'md_bold'))
                elif m.group(4):  # 代码
                    self.chat_text.insert('end', m.group(4), (base_tag, 'md_code'))
                elif m.group(6):  # Markdown 链接 [文字](url)
                    link_text, url = m.group(6), m.group(7)
                    link_tag = f'mdlink_{hash(url) % 100000}'
                    self.chat_text.tag_config(link_tag, foreground='#0969da', underline=True)
                    self.chat_text.insert('end', link_text, (base_tag, link_tag))
                    self.chat_text.tag_bind(link_tag, '<Button-1>', lambda ev, u=url: webbrowser.open(u))
                    self.chat_text.tag_bind(link_tag, '<Enter>', lambda ev: self.chat_text.config(cursor='hand2'))
                    self.chat_text.tag_bind(link_tag, '<Leave>', lambda ev: self.chat_text.config(cursor='arrow'))
                pos = m.end()
            if pos < len(line):
                self.chat_text.insert('end', line[pos:], base_tag)
            self.chat_text.insert('end', '\n', base_tag)

    def render_all(self):
        self.chat_text.config(state='normal')
        self.chat_text.delete('1.0', 'end')
        self.chat_text.config(state='disabled')
        if not self.messages:
            self.chat_text.config(state='normal')
            self.chat_text.insert('end', '\n\n🐋\n', 'welcome')
            self.chat_text.insert('end', '大胖鱼 AI 聊天\n', 'welcome')
            self.chat_text.insert('end', '选择模型，输入消息开始对话\n点 + 上传图片和文件', 'welcome')
            self.chat_text.config(state='disabled')
            return
        for m in self.messages:
            self.append_msg(m['role'], m['content'], m.get('model', ''))

    def send(self):
        text = self.input_text.get('1.0', 'end').strip()
        if (not text and not self.attachments) or self.sending: return
        model = self.model_var.get()
        if not model:
            messagebox.showwarning('提示', '请先选择模型')
            return
        if not self.cfg.get('api_key'):
            messagebox.showwarning('提示', '请先在设置里填入 API Key')
            return

        # 构建消息内容（含附件）
        display_text = text
        api_content = text
        if self.attachments:
            # 显示用
            attach_descs = [a[1] for a in self.attachments]
            display_text = text + '\n' + '\n'.join(attach_descs) if text else '\n'.join(attach_descs)
            # API 用：多部分格式
            blocks = [{'type': 'text', 'text': text}] if text else []
            for _, _, b in self.attachments:
                blocks.extend(b)
            api_content = blocks

        self.messages.append({'role': 'user', 'content': display_text, '_api_content': api_content})
        self.append_msg('user', display_text)
        self.input_text.delete('1.0', 'end')
        self.clear_attachments()
        self.sending = True
        self.stop_event.clear()
        self.send_btn.pack_forget()
        self.stop_btn.pack(side='right', padx=8, pady=8)
        self.set_status('🐋 思考中...')
        threading.Thread(target=self._do_send, args=(model,), daemon=True).start()

    def _do_send(self, model):
        ai_content = ['']
        class Stopped(Exception): pass
        def on_delta(d):
            if self.stop_event.is_set():
                raise Stopped()
            ai_content[0] += d
            self.root.after(0, lambda: self._update_streaming(ai_content[0], model))
        def on_usage(p, c):
            self.token_stats['prompt'] += p
            self.token_stats['completion'] += c
            self.root.after(0, self.update_token_display)
        # 先显示占位
        self.root.after(0, lambda: self.append_msg('assistant', '', model))
        try:
            msgs = []
            for m in self.messages:
                c = m.get('_api_content', m['content'])
                msgs.append({'role': m['role'], 'content': c})
            # 联网搜索：用 OpenRouter web 插件让模型自己搜
            payload = {
                'model': model, 'messages': msgs,
                'temperature': self.cfg['temperature'],
                'max_tokens': self.cfg['max_tokens'],
                'stream': True,
                'usage': {'include': True},
            }
            if self.web_search_enabled:
                payload['plugins'] = [{'id': 'web'}]
                self.root.after(0, lambda: self.set_status('🌐 DeepSeek 联网搜索中...'))
            if self.cfg.get('system_prompt'):
                msgs = [{'role': 'system', 'content': self.cfg['system_prompt']}] + msgs
            api_call('/chat/completions', self.cfg['api_key'], 'POST', payload,
                     stream_cb=on_delta, usage_cb=on_usage, proxy_cfg=self.cfg)
            self.messages.append({'role': 'assistant', 'content': ai_content[0], 'model': model})
            self.root.after(0, lambda: self.set_status('✓ 完成'))
        except Stopped:
            self.messages.append({'role': 'assistant', 'content': ai_content[0] + '\n\n[已停止]', 'model': model})
            self.root.after(0, lambda: self.set_status('已停止'))
        except Exception as e:
            err = f'❌ 出错: {e}'
            ai_content[0] = err
            self.messages.append({'role': 'assistant', 'content': err, 'model': model})
            self.root.after(0, lambda: self.set_status(err[:80]))
        self.root.after(0, self._finish_send)
        self.auto_save()

    def _update_streaming(self, content, model):
        # 更新最后一条 AI 消息的显示
        self.chat_text.config(state='normal')
        # 删除最后一条消息重绘（简单方案）
        self.render_all()
        # 把正在流式的内容追加显示
        if self.messages and self.messages[-1]['role'] == 'assistant' and not self.messages[-1]['content']:
            pass
        self.chat_text.config(state='disabled')

    def _finish_send(self):
        self.render_all()
        self.sending = False
        self.stop_event.clear()
        self.stop_btn.pack_forget()
        self.send_btn.pack(side='right', padx=8, pady=8)

    def auto_save(self):
        if not self.messages: return
        if not self.current_id:
            self.current_id = str(int(__import__('time').time() * 1000))
        title = next((m['content'][:20] for m in self.messages if m['role'] == 'user'), '未命名')
        fp = os.path.join(HISTORY_DIR, self.current_id + '.json')
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump({'title': title, 'messages': self.messages}, f, ensure_ascii=False)
        self.root.after(0, self.load_history_list)

    def load_history_list(self):
        self.history_box.delete(0, 'end')
        self.history_ids = []
        try:
            files = sorted([f[:-5] for f in os.listdir(HISTORY_DIR) if f.endswith('.json')], reverse=True)
            for fid in files:
                try:
                    with open(os.path.join(HISTORY_DIR, fid + '.json'), 'r', encoding='utf-8') as f:
                        d = json.load(f)
                        self.history_box.insert('end', d.get('title', '未命名'))
                        self.history_ids.append(fid)
                except: pass
        except: pass

    def on_history_select(self, e):
        sel = self.history_box.curselection()
        if not sel: return
        fid = self.history_ids[sel[0]]
        try:
            with open(os.path.join(HISTORY_DIR, fid + '.json'), 'r', encoding='utf-8') as f:
                d = json.load(f)
                self.current_id = fid
                self.messages = d.get('messages', [])
                self.render_all()
                self.set_status('')
        except: pass

    def delete_history(self):
        sel = self.history_box.curselection()
        if not sel: return
        if not messagebox.askyesno('确认', '确定删除这条历史记录吗？'):
            return
        fid = self.history_ids[sel[0]]
        fp = os.path.join(HISTORY_DIR, fid + '.json')
        if os.path.exists(fp): os.remove(fp)
        if fid == self.current_id:
            self.current_id = None; self.messages = []; self.render_all()
        self.load_history_list()

    def new_chat(self):
        self.current_id = None
        self.messages = []
        self.render_all()
        self.set_status('')
        self.input_text.focus()

    def export_chat(self):
        if not self.messages:
            messagebox.showinfo('提示', '没有可导出的内容')
            return
        t = '# 聊天记录\n\n'
        for m in self.messages:
            t += '## 👤 你\n' if m['role'] == 'user' else '## 🐋 AI\n'
            t += m['content'] + '\n\n'
        fp = os.path.join(BASE_DIR, f'chat-{self.current_id or "new"}.md')
        with open(fp, 'w', encoding='utf-8') as f: f.write(t)
        messagebox.showinfo('导出成功', f'已保存到:\n{fp}')

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title('设置')
        win.geometry('450x520')
        win.configure(bg=BG2)
        win.transient(self.root)
        win.grab_set()

        fields = {}
        def add_row(label, key, show=None, height=1):
            tk.Label(win, text=label, bg=BG2, fg=MUTED, font=('Microsoft YaHei', 10)).pack(anchor='w', padx=16, pady=(10, 2))
            if height > 1:
                w = tk.Text(win, bg=BG, fg=FG, font=('Microsoft YaHei', 10), height=height, relief='flat')
            else:
                w = tk.Entry(win, bg=BG, fg=FG, font=('Microsoft YaHei', 10), relief='flat', show=show or '')
            w.pack(fill='x', padx=16)
            val = self.cfg.get(key, '')
            if key == 'api_key':
                w.insert(0, '' if val else '')
                if val: w.insert(0, '********')
            else:
                if height > 1: w.insert('1.0', str(val))
                else: w.insert(0, str(val))
            fields[key] = w

        add_row('OpenRouter API Key', 'api_key', show='*')
        add_row('默认模型', 'default_model')
        add_row('Temperature (0-2)', 'temperature')
        add_row('Max Tokens', 'max_tokens')
        add_row('System Prompt', 'system_prompt', height=3)

        # 代理设置
        tk.Label(win, text='代理模式', bg=BG2, fg=MUTED, font=('Microsoft YaHei', 10)).pack(anchor='w', padx=16, pady=(10, 2))
        proxy_var = tk.StringVar(value=self.cfg.get('proxy_mode', 'system'))
        proxy_frame = tk.Frame(win, bg=BG2)
        proxy_frame.pack(fill='x', padx=16)
        for mode, label in [('system', '系统代理'), ('direct', '直连'), ('custom', '自定义')]:
            tk.Radiobutton(proxy_frame, text=label, variable=proxy_var, value=mode,
                          bg=BG2, fg=FG, selectcolor=BG3, font=('Microsoft YaHei', 10)).pack(side='left', padx=8)
        tk.Label(win, text='自定义代理 (如 http://127.0.0.1:7890)', bg=BG2, fg=MUTED, font=('Microsoft YaHei', 10)).pack(anchor='w', padx=16, pady=(10, 2))
        proxy_url_entry = tk.Entry(win, bg=BG, fg=FG, font=('Microsoft YaHei', 10), relief='flat')
        proxy_url_entry.pack(fill='x', padx=16)
        proxy_url_entry.insert(0, self.cfg.get('proxy_url', ''))

        def save():
            for k, w in fields.items():
                v = w.get('1.0', 'end').strip() if isinstance(w, tk.Text) else w.get().strip()
                if k == 'api_key':
                    if v and v != '********': self.cfg[k] = v
                elif v:
                    if k in ('temperature',): self.cfg[k] = float(v)
                    elif k in ('max_tokens',): self.cfg[k] = int(v)
                    else: self.cfg[k] = v
            self.cfg['proxy_mode'] = proxy_var.get()
            self.cfg['proxy_url'] = proxy_url_entry.get().strip()
            save_config(self.cfg)
            win.destroy()
            messagebox.showinfo('提示', '设置已保存')
            self.load_models_thread()

        tk.Button(win, text='保存', command=save, bg=ACCENT, fg='black',
                  font=('Microsoft YaHei', 11, 'bold'), relief='flat', pady=8).pack(fill='x', padx=16, pady=16)

def main():
    root = tk.Tk()
    app = BigFatFishApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
