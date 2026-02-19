"""
VimeWorld Fake Mention Tool — GUI версия
Требования: pip install requests beautifulsoup4
Запуск:     python vime_fake_mention_gui.py
Сборка exe: pip install pyinstaller
            pyinstaller --onefile --windowed --name "VimeMention" vime_fake_mention_gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import re
from bs4 import BeautifulSoup

# ─────────────────────────────────────────
#  ЦВЕТА И СТИЛЬ
# ─────────────────────────────────────────
BG        = "#0d0d0f"
BG2       = "#141418"
BG3       = "#1c1c22"
ACCENT    = "#5865f2"
ACCENT2   = "#7983f5"
SUCCESS   = "#3ba55d"
ERROR     = "#ed4245"
TEXT      = "#e8e8f0"
TEXT_DIM  = "#6b6b80"
BORDER    = "#2a2a35"
INPUT_BG  = "#18181e"

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_LABEL  = ("Segoe UI", 9)
FONT_ENTRY  = ("Segoe UI", 10)
FONT_BTN    = ("Segoe UI", 10, "bold")
FONT_LOG    = ("Consolas", 9)
FONT_SMALL  = ("Segoe UI", 8)

BASE_URL = "https://forum.vimeworld.com"
session  = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Referer": BASE_URL,
})

# ─────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ВИДЖЕТЫ
# ─────────────────────────────────────────

class StyledEntry(tk.Frame):
    def __init__(self, master, placeholder="", show=None, **kw):
        super().__init__(master, bg=BORDER, padx=1, pady=1)
        self.placeholder = placeholder
        self._active = False

        inner = tk.Frame(self, bg=INPUT_BG)
        inner.pack(fill="both", expand=True)

        self.entry = tk.Entry(
            inner, bg=INPUT_BG, fg=TEXT_DIM,
            insertbackground=ACCENT, relief="flat",
            font=FONT_ENTRY, show=show,
            highlightthickness=0, bd=6,
            **kw
        )
        self.entry.pack(fill="both", expand=True)

        if placeholder:
            self.entry.insert(0, placeholder)

        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _=None):
        if not self._active and self.entry.get() == self.placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT)
            self._active = True
        self.config(bg=ACCENT)

    def _on_focus_out(self, _=None):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=TEXT_DIM)
            self._active = False
        self.config(bg=BORDER)

    def get(self):
        val = self.entry.get()
        return "" if val == self.placeholder else val

    def set(self, val):
        self.entry.delete(0, "end")
        self.entry.insert(0, val)
        self.entry.config(fg=TEXT)
        self._active = bool(val)

    def clear(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=TEXT_DIM)
        self._active = False


class StyledButton(tk.Button):
    def __init__(self, master, text, command=None, style="primary", **kw):
        colors = {
            "primary": (ACCENT, "#ffffff"),
            "success": (SUCCESS, "#ffffff"),
            "ghost":   (BG3,    TEXT_DIM),
            "danger":  (ERROR,  "#ffffff"),
        }
        bg, fg = colors.get(style, colors["primary"])

        super().__init__(
            master, text=text, command=command,
            bg=bg, fg=fg, activebackground=ACCENT2,
            activeforeground="#ffffff",
            relief="flat", cursor="hand2",
            font=FONT_BTN, bd=0,
            padx=18, pady=9,
            **kw
        )
        self._bg = bg
        self.bind("<Enter>", lambda _: self.config(bg=self._hover()))
        self.bind("<Leave>", lambda _: self.config(bg=self._bg))

    def _hover(self):
        def _lighten(hex_color):
            h = hex_color.lstrip("#")
            rgb = tuple(min(255, int(h[i:i+2], 16) + 20) for i in (0, 2, 4))
            return "#{:02x}{:02x}{:02x}".format(*rgb)
        return _lighten(self._bg)


class SectionCard(tk.Frame):
    def __init__(self, master, title, **kw):
        super().__init__(master, bg=BG2, bd=0, **kw)

        # Цветная полоска сверху
        accent_bar = tk.Frame(self, bg=ACCENT, height=2)
        accent_bar.pack(fill="x")

        inner = tk.Frame(self, bg=BG2, padx=20, pady=16)
        inner.pack(fill="both", expand=True)

        tk.Label(
            inner, text=title, bg=BG2, fg=ACCENT2,
            font=("Segoe UI", 9, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 12))

        self.inner = inner

    def body(self):
        return self.inner


# ─────────────────────────────────────────
#  ГЛАВНОЕ ОКНО
# ─────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VimeMention")
        self.geometry("720x820")
        self.minsize(680, 750)
        self.configure(bg=BG)
        self.resizable(True, True)

        # Состояние
        self._logged_in   = False
        self._user_data   = None   # {"id", "name", "url"}
        self._topic_id    = None

        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    # ── построение интерфейса ──────────────

    def _build_ui(self):
        # Скроллируемая область
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.main = tk.Frame(canvas, bg=BG)
        self.main_id = canvas.create_window((0, 0), window=self.main, anchor="nw")

        self.main.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            self.main_id, width=e.width
        ))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"
        ))

        self._build_header()
        self._build_login()
        self._build_topic()
        self._build_user()
        self._build_compose()
        self._build_send()
        self._build_log()

    def _build_header(self):
        hdr = tk.Frame(self.main, bg=BG, pady=0)
        hdr.pack(fill="x", padx=0)

        # Декоративная полоска
        tk.Frame(hdr, bg=ACCENT, height=3).pack(fill="x")

        inner = tk.Frame(hdr, bg=BG2, padx=28, pady=20)
        inner.pack(fill="x")

        tk.Label(
            inner, text="VIME  MENTION",
            bg=BG2, fg=TEXT, font=FONT_TITLE,
            anchor="w"
        ).pack(side="left")

        # Статус авторизации
        self.auth_badge = tk.Label(
            inner, text="● НЕ АВТОРИЗОВАН",
            bg=BG2, fg=ERROR,
            font=FONT_SMALL
        )
        self.auth_badge.pack(side="right", padx=4)

    def _row(self, parent, label):
        """Одна строка лейбл + виджет"""
        row = tk.Frame(parent, bg=BG2)
        row.pack(fill="x", pady=4)
        tk.Label(
            row, text=label, bg=BG2, fg=TEXT_DIM,
            font=FONT_LABEL, width=16, anchor="w"
        ).pack(side="left")
        return row

    def _build_login(self):
        card = SectionCard(self.main, "① АВТОРИЗАЦИЯ")
        card.pack(fill="x", padx=20, pady=(16, 6))
        body = card.body()

        r1 = self._row(body, "Логин")
        self.e_login = StyledEntry(r1, placeholder="Ваш логин")
        self.e_login.pack(side="left", fill="x", expand=True)

        r2 = self._row(body, "Пароль")
        self.e_pass = StyledEntry(r2, placeholder="Ваш пароль", show="●")
        self.e_pass.pack(side="left", fill="x", expand=True)

        btn_row = tk.Frame(body, bg=BG2)
        btn_row.pack(fill="x", pady=(10, 0))

        StyledButton(btn_row, "Войти", command=self._do_login).pack(side="left")

    def _build_topic(self):
        card = SectionCard(self.main, "② ТЕМА ДЛЯ ОТВЕТА")
        card.pack(fill="x", padx=20, pady=6)
        body = card.body()

        info = tk.Label(
            body,
            text="Вставь URL темы или введи поисковый запрос:",
            bg=BG2, fg=TEXT_DIM, font=FONT_SMALL, anchor="w"
        )
        info.pack(fill="x", pady=(0, 8))

        r1 = self._row(body, "URL / Поиск")
        self.e_topic = StyledEntry(r1, placeholder="https://forum.vimeworld.com/topic/... или название темы")
        self.e_topic.pack(side="left", fill="x", expand=True)
        StyledButton(r1, "Найти", command=self._do_search_topic, style="ghost").pack(side="left", padx=(8, 0))

        # Список результатов
        self.topic_frame = tk.Frame(body, bg=BG2)
        self.topic_frame.pack(fill="x", pady=(8, 0))

        self.topic_status = tk.Label(
            body, text="", bg=BG2, fg=TEXT_DIM, font=FONT_SMALL, anchor="w"
        )
        self.topic_status.pack(fill="x", pady=(4, 0))

    def _build_user(self):
        card = SectionCard(self.main, "③ КТО РЕАЛЬНО ПОЛУЧИТ УВЕДОМЛЕНИЕ")
        card.pack(fill="x", padx=20, pady=6)
        body = card.body()

        r1 = self._row(body, "Ник / URL")
        self.e_user = StyledEntry(r1, placeholder="Ник пользователя или URL профиля")
        self.e_user.pack(side="left", fill="x", expand=True)
        StyledButton(r1, "Найти", command=self._do_search_user, style="ghost").pack(side="left", padx=(8, 0))

        self.user_frame = tk.Frame(body, bg=BG2)
        self.user_frame.pack(fill="x", pady=(8, 0))

        self.user_status = tk.Label(
            body, text="", bg=BG2, fg=TEXT_DIM, font=FONT_SMALL, anchor="w"
        )
        self.user_status.pack(fill="x", pady=(4, 0))

    def _build_compose(self):
        card = SectionCard(self.main, "④ ТЕКСТ ПОСТА")
        card.pack(fill="x", padx=20, pady=6)
        body = card.body()

        r1 = self._row(body, "Фейк-имя (@...)")
        self.e_fake = StyledEntry(r1, placeholder="nastya")
        self.e_fake.pack(side="left", fill="x", expand=True)

        tk.Label(
            body, text="Текст сообщения:",
            bg=BG2, fg=TEXT_DIM, font=FONT_LABEL, anchor="w"
        ).pack(fill="x", pady=(10, 4))

        text_frame = tk.Frame(body, bg=BORDER, padx=1, pady=1)
        text_frame.pack(fill="x")

        inner = tk.Frame(text_frame, bg=INPUT_BG)
        inner.pack(fill="both")

        self.e_text = tk.Text(
            inner, bg=INPUT_BG, fg=TEXT,
            insertbackground=ACCENT, relief="flat",
            font=FONT_ENTRY, bd=8, height=4,
            wrap="word", highlightthickness=0
        )
        self.e_text.pack(fill="both", expand=True)
        self.e_text.insert("1.0", "Напиши текст своего сообщения здесь...")
        self.e_text.config(fg=TEXT_DIM)

        def on_focus_in(_):
            if self.e_text.get("1.0", "end-1c") == "Напиши текст своего сообщения здесь...":
                self.e_text.delete("1.0", "end")
                self.e_text.config(fg=TEXT)
            text_frame.config(bg=ACCENT)

        def on_focus_out(_):
            if not self.e_text.get("1.0", "end-1c").strip():
                self.e_text.insert("1.0", "Напиши текст своего сообщения здесь...")
                self.e_text.config(fg=TEXT_DIM)
            text_frame.config(bg=BORDER)

        self.e_text.bind("<FocusIn>",  on_focus_in)
        self.e_text.bind("<FocusOut>", on_focus_out)

    def _build_send(self):
        send_frame = tk.Frame(self.main, bg=BG, padx=20, pady=12)
        send_frame.pack(fill="x")

        self.btn_send = StyledButton(
            send_frame, "  ОТПРАВИТЬ ПОСТ  ",
            command=self._do_send, style="primary"
        )
        self.btn_send.pack(side="left")

        self.send_status = tk.Label(
            send_frame, text="", bg=BG, fg=TEXT_DIM, font=FONT_SMALL
        )
        self.send_status.pack(side="left", padx=16)

    def _build_log(self):
        card = SectionCard(self.main, "ЛОГ")
        card.pack(fill="x", padx=20, pady=(4, 20))
        body = card.body()

        log_frame = tk.Frame(body, bg=BORDER, padx=1, pady=1)
        log_frame.pack(fill="x")

        inner = tk.Frame(log_frame, bg="#0a0a0c")
        inner.pack(fill="both")

        self.log = tk.Text(
            inner, bg="#0a0a0c", fg="#5eff9e",
            relief="flat", font=FONT_LOG, bd=8, height=8,
            state="disabled", wrap="word", highlightthickness=0
        )
        self.log.pack(fill="both", expand=True)

        self._log("Добро пожаловать в VimeMention Tool")
        self._log("Заполни все поля и нажми «Отправить пост»")

    # ── логирование ───────────────────────

    def _log(self, msg, color=None):
        self.log.config(state="normal")
        tag = f"tag_{len(self.log.get('1.0','end'))}"
        self.log.insert("end", f"› {msg}\n", tag)
        if color:
            self.log.tag_config(tag, foreground=color)
        self.log.see("end")
        self.log.config(state="disabled")

    # ── авторизация ───────────────────────

    def _do_login(self):
        login_val = self.e_login.get()
        pass_val  = self.e_pass.get()
        if not login_val or not pass_val:
            messagebox.showwarning("Ошибка", "Введи логин и пароль!")
            return

        self._log(f"Авторизуюсь как {login_val}...")
        threading.Thread(target=self._login_thread,
                         args=(login_val, pass_val), daemon=True).start()

    def _login_thread(self, login_val, pass_val):
        try:
            resp = session.get(f"{BASE_URL}/login/")
            soup = BeautifulSoup(resp.text, "html.parser")
            csrf = soup.find("input", {"name": "csrfKey"})
            if not csrf:
                self.after(0, lambda: self._log("Ошибка: не найден CSRF токен", ERROR))
                return

            data = {
                "csrfKey": csrf["value"],
                "auth": login_val,
                "password": pass_val,
                "remember_me": "1",
                "_processLogin": "usernamepassword",
                "login__standard_submitted": "1",
            }
            resp = session.post(f"{BASE_URL}/login/", data=data, allow_redirects=True)

            if "sign_out" in resp.text or "logout" in resp.text.lower():
                self._logged_in = True
                self.after(0, lambda: [
                    self._log(f"Авторизация успешна! Привет, {login_val}", SUCCESS),
                    self.auth_badge.config(text=f"● {login_val.upper()}", fg=SUCCESS),
                ])
            else:
                self.after(0, lambda: self._log("Неверный логин или пароль", ERROR))
        except Exception as e:
            self.after(0, lambda: self._log(f"Ошибка подключения: {e}", ERROR))

    # ── поиск темы ────────────────────────

    def _do_search_topic(self):
        query = self.e_topic.get()
        if not query:
            messagebox.showwarning("Ошибка", "Введи поисковый запрос или URL темы!")
            return

        # Если это URL или ID — используем сразу
        match = re.search(r"/topic/(\d+)", query)
        if match:
            tid = match.group(1)
            self._topic_id = tid
            self.topic_status.config(
                text=f"✓ Тема выбрана: ID {tid}", fg=SUCCESS
            )
            self._log(f"Тема выбрана: ID {tid}", SUCCESS)
            return

        if query.isdigit():
            self._topic_id = query
            self.topic_status.config(
                text=f"✓ Тема выбрана: ID {query}", fg=SUCCESS
            )
            self._log(f"Тема выбрана: ID {query}", SUCCESS)
            return

        self._log(f"Ищу тему: {query}...")
        threading.Thread(target=self._search_topic_thread,
                         args=(query,), daemon=True).start()

    def _search_topic_thread(self, query):
        try:
            resp = session.get(f"{BASE_URL}/search/", params={
                "q": query, "type": "forums_topic",
                "search_and_or": "and", "sortby": "relevancy",
            })
            soup = BeautifulSoup(resp.text, "html.parser")

            results = []
            for item in soup.select("li[data-role='activityItem'], article.ipsStreamItem"):
                title_el = item.select_one("h2 a, h3 a, .ipsStreamItem_title a")
                if title_el and title_el.get("href"):
                    m = re.search(r"/topic/(\d+)-", title_el["href"])
                    if m:
                        results.append({
                            "id": m.group(1),
                            "title": title_el.get_text(strip=True),
                        })

            self.after(0, lambda: self._show_topic_results(results))
        except Exception as e:
            self.after(0, lambda: self._log(f"Ошибка поиска: {e}", ERROR))

    def _show_topic_results(self, results):
        # Очистка старых результатов
        for w in self.topic_frame.winfo_children():
            w.destroy()

        if not results:
            self._log("Тем не найдено", ERROR)
            return

        self._log(f"Найдено тем: {len(results)}")

        for t in results[:6]:
            row = tk.Frame(self.topic_frame, bg=BG3, cursor="hand2")
            row.pack(fill="x", pady=2)

            tk.Label(
                row, text=f"#{t['id']}", bg=BG3, fg=ACCENT,
                font=("Segoe UI", 8, "bold"), width=8
            ).pack(side="left", padx=(10, 4), pady=6)

            tk.Label(
                row, text=t["title"][:70], bg=BG3, fg=TEXT,
                font=FONT_SMALL, anchor="w"
            ).pack(side="left", fill="x", expand=True, pady=6)

            tid = t["id"]
            title = t["title"]

            def on_click(e, _id=tid, _title=title):
                self._topic_id = _id
                self.topic_status.config(
                    text=f"✓ Выбрана: {_title[:50]}", fg=SUCCESS
                )
                self._log(f"Тема выбрана: {_title[:40]} (ID {_id})", SUCCESS)

            row.bind("<Button-1>", on_click)
            for child in row.winfo_children():
                child.bind("<Button-1>", on_click)

            row.bind("<Enter>", lambda e, r=row: r.config(bg="#25252e"))
            row.bind("<Leave>", lambda e, r=row: r.config(bg=BG3))

    # ── поиск пользователя ────────────────

    def _do_search_user(self):
        query = self.e_user.get()
        if not query:
            messagebox.showwarning("Ошибка", "Введи ник или URL профиля!")
            return

        # Если URL профиля
        match = re.search(r"/profile/(\d+)-([^/]+)/", query)
        if match:
            uid, name = match.group(1), match.group(2)
            self._user_data = {
                "id": uid, "name": name,
                "url": f"{BASE_URL}/profile/{uid}-{name}/",
            }
            self.user_status.config(
                text=f"✓ Пользователь: {name} (ID {uid})", fg=SUCCESS
            )
            self._log(f"Пользователь выбран: {name} (ID {uid})", SUCCESS)
            return

        self._log(f"Ищу пользователя: {query}...")
        threading.Thread(target=self._search_user_thread,
                         args=(query,), daemon=True).start()

    def _search_user_thread(self, query):
        try:
            resp = session.get(f"{BASE_URL}/search/", params={
                "q": query, "type": "core_members",
            })
            soup = BeautifulSoup(resp.text, "html.parser")

            users, seen = [], set()
            for a in soup.select("a[href*='/profile/']"):
                m = re.search(r"/profile/(\d+)-([^/\"]+)/", a["href"])
                if m and m.group(1) not in seen:
                    seen.add(m.group(1))
                    users.append({
                        "id": m.group(1),
                        "name": m.group(2),
                        "display": a.get_text(strip=True) or m.group(2),
                        "url": f"{BASE_URL}/profile/{m.group(1)}-{m.group(2)}/",
                    })

            # Прямой запрос профиля
            if not users:
                resp2 = session.get(f"{BASE_URL}/profile/?name={query}")
                m = re.search(r"/profile/(\d+)-([^/\"]+)/", resp2.url)
                if m:
                    users.append({
                        "id": m.group(1), "name": m.group(2),
                        "display": query,
                        "url": resp2.url,
                    })

            self.after(0, lambda: self._show_user_results(users))
        except Exception as e:
            self.after(0, lambda: self._log(f"Ошибка поиска: {e}", ERROR))

    def _show_user_results(self, users):
        for w in self.user_frame.winfo_children():
            w.destroy()

        if not users:
            self._log("Пользователи не найдены", ERROR)
            return

        self._log(f"Найдено пользователей: {len(users)}")

        for u in users[:5]:
            row = tk.Frame(self.user_frame, bg=BG3, cursor="hand2")
            row.pack(fill="x", pady=2)

            avatar = tk.Label(
                row, text=u["display"][0].upper() if u["display"] else "?",
                bg=ACCENT, fg="#fff",
                font=("Segoe UI", 10, "bold"),
                width=3, height=1
            )
            avatar.pack(side="left", padx=(10, 8), pady=6)

            info_frame = tk.Frame(row, bg=BG3)
            info_frame.pack(side="left", fill="x", expand=True, pady=6)

            tk.Label(
                info_frame, text=u["display"], bg=BG3, fg=TEXT,
                font=("Segoe UI", 9, "bold"), anchor="w"
            ).pack(fill="x")

            tk.Label(
                info_frame, text=f"ID: {u['id']}", bg=BG3,
                fg=TEXT_DIM, font=FONT_SMALL, anchor="w"
            ).pack(fill="x")

            user_copy = dict(u)

            def on_click(e, _u=user_copy):
                self._user_data = _u
                self.user_status.config(
                    text=f"✓ Выбран: {_u['display']} (ID {_u['id']})", fg=SUCCESS
                )
                self._log(f"Пользователь выбран: {_u['display']} (ID {_u['id']})", SUCCESS)

            row.bind("<Button-1>", on_click)
            for child in row.winfo_children():
                child.bind("<Button-1>", on_click)
            for child in info_frame.winfo_children():
                child.bind("<Button-1>", on_click)

            row.bind("<Enter>", lambda e, r=row: r.config(bg="#25252e"))
            row.bind("<Leave>", lambda e, r=row: r.config(bg=BG3))

    # ── отправка поста ────────────────────

    def _do_send(self):
        if not self._logged_in:
            messagebox.showwarning("Ошибка", "Сначала авторизуйся!")
            return
        if not self._topic_id:
            messagebox.showwarning("Ошибка", "Выбери тему!")
            return
        if not self._user_data:
            messagebox.showwarning("Ошибка", "Выбери пользователя для тега!")
            return

        fake_name = self.e_fake.get()
        post_text = self.e_text.get("1.0", "end-1c").strip()

        if not fake_name:
            messagebox.showwarning("Ошибка", "Введи фейковое имя!")
            return
        if not post_text or post_text == "Напиши текст своего сообщения здесь...":
            messagebox.showwarning("Ошибка", "Введи текст поста!")
            return

        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Отправить пост?\n\n"
            f"Тема: {self._topic_id}\n"
            f"Тег: {self._user_data['display']} (ID {self._user_data['id']})\n"
            f"Отображается: @{fake_name}\n"
            f"Текст: {post_text[:80]}..."
        )
        if not confirm:
            return

        self.btn_send.config(state="disabled", text="Отправляю...")
        self._log("Отправляю пост...")

        threading.Thread(
            target=self._send_thread,
            args=(self._topic_id, self._user_data, fake_name, post_text),
            daemon=True
        ).start()

    def _send_thread(self, topic_id, user, fake_name, post_text):
        try:
            # CSRF
            resp = session.get(f"{BASE_URL}/topic/{topic_id}/")
            soup = BeautifulSoup(resp.text, "html.parser")

            csrf = None
            tag = soup.find("input", {"name": "csrfKey"})
            if tag:
                csrf = tag["value"]
            else:
                m = re.search(r'"csrfKey"\s*:\s*"([a-f0-9]+)"', resp.text)
                if m:
                    csrf = m.group(1)

            if not csrf:
                self.after(0, lambda: [
                    self._log("Не удалось получить CSRF токен", ERROR),
                    self.btn_send.config(state="normal", text="  ОТПРАВИТЬ ПОСТ  "),
                ])
                return

            # Собираем HTML упоминания
            mention = (
                f'<a contenteditable="false" '
                f'data-ipshover="" '
                f'data-ipshover-target="{user["url"]}?do=hovercard" '
                f'data-mentionid="{user["id"]}" '
                f'href="{user["url"]}" '
                f'rel="noopener noreferrer">'
                f'@{fake_name}'
                f'</a>'
            )
            content = f"{mention}&nbsp;{post_text}"

            data = {
                "csrfKey": csrf,
                "content": content,
                "_processReply": "1",
                "topicid": str(topic_id),
            }

            resp = session.post(
                f"{BASE_URL}/topic/{topic_id}/?do=reply",
                data=data,
                headers={"X-Requested-With": "XMLHttpRequest"},
                allow_redirects=True,
            )

            if resp.status_code in (200, 201, 302):
                self.after(0, lambda: [
                    self._log(f"Пост успешно отправлен! → {BASE_URL}/topic/{topic_id}/", SUCCESS),
                    self.send_status.config(text="✓ Отправлено!", fg=SUCCESS),
                    self.btn_send.config(state="normal", text="  ОТПРАВИТЬ ПОСТ  "),
                    messagebox.showinfo("Успех!", f"Пост отправлен!\n{BASE_URL}/topic/{topic_id}/"),
                ])
            else:
                self.after(0, lambda: [
                    self._log(f"Ошибка отправки. Статус: {resp.status_code}", ERROR),
                    self.btn_send.config(state="normal", text="  ОТПРАВИТЬ ПОСТ  "),
                ])

        except Exception as e:
            self.after(0, lambda: [
                self._log(f"Ошибка: {e}", ERROR),
                self.btn_send.config(state="normal", text="  ОТПРАВИТЬ ПОСТ  "),
            ])


# ─────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
