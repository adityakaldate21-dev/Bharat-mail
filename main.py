"""
Full attractive Tkinter Email App (single-file)
Features:
- Modern sidebar UI with Dark/Light theme toggle
- Login / Register (SQLite)
- Compose with attachments (base64 stored)
- Inbox / Sent / Spam tabs with search & sort
- Spam detection (keyword-based) and Mark Spam
- Delete emails
- Analytics with Matplotlib (Bar + Pie) embedded in Tkinter
- Export analytics CSV
Dependencies: Python standard library + matplotlib
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
import os
import base64
from datetime import datetime, timedelta

# ---------------- Database Setup ----------------
DB_FILE = "email_system.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
c.execute(
    "CREATE TABLE IF NOT EXISTS emails (id INTEGER PRIMARY KEY AUTOINCREMENT, recipient TEXT, sender TEXT, subject TEXT, body TEXT)"
)
# Optionally add columns if missing
for stmt in [
    "ALTER TABLE emails ADD COLUMN attachment TEXT",
    "ALTER TABLE emails ADD COLUMN timestamp TEXT",
    "ALTER TABLE emails ADD COLUMN is_spam INTEGER DEFAULT 0",
]:
    try:
        c.execute(stmt)
    except sqlite3.OperationalError:
        pass
conn.commit()

# ---------------- Theme & Styling ----------------
LIGHT_THEME = {
    "BG": "#f0f4f8",
    "SIDEBAR": "#ffffff",
    "HEADER": "#1f2937",
    "BTN": "#2563eb",
    "BTN_HOVER": "#1e40af",
    "CARD": "#ffffff",
    "CARD_HOVER": "#eef2ff",
    "TEXT": "#0f172a",
}
DARK_THEME = {
    "BG": "#0b1221",
    "SIDEBAR": "#0f1724",
    "HEADER": "#e6eef8",
    "BTN": "#4f46e5",
    "BTN_HOVER": "#3730a3",
    "CARD": "#0b1228",
    "CARD_HOVER": "#0f172a",
    "TEXT": "#e6eef8",
}

FONT_HEADER = ("Segoe UI", 18, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)

# ---------------- Application ----------------
class EmailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📧 Modern Email App")
        self.root.geometry("980x700")
        self.theme = LIGHT_THEME
        self.current_user = None
        self.apply_theme()
        self.login_screen()

    # ---------- Theme ----------
    def apply_theme(self):
        self.root.configure(bg=self.theme["BG"])
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=self.theme["BG"])
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(8, 6))
        # minimal ttk style changes so tabs blend

    def toggle_theme(self):
        self.theme = DARK_THEME if self.theme == LIGHT_THEME else LIGHT_THEME
        # Re-render current screen
        if self.current_user:
            self.main_menu()
        else:
            self.login_screen()

    # ---------- Utilities ----------
    def clear_screen(self):
        for w in self.root.winfo_children():
            w.destroy()

    def styled_button(self, parent, text, command, width=18, height=2, icon=""):
        btn = tk.Button(
            parent,
            text=(f"{icon} " if icon else "") + text,
            font=FONT_NORMAL,
            bg=self.theme["BTN"],
            fg="white",
            activebackground=self.theme["BTN_HOVER"],
            activeforeground="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            width=width,
            height=height,
            command=command,
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=self.theme["BTN_HOVER"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=self.theme["BTN"]))
        return btn

    def styled_entry(self, parent, show=None, width=32):
        entry = tk.Entry(parent, font=FONT_NORMAL, show=show, relief="solid", bd=1)
        entry.config(width=width)
        return entry

    def popup_window(self, title, fields, callback, width=420, height=320):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry(f"{width}x{height}")
        popup.configure(bg=self.theme["BG"])
        popup.grab_set()
        tk.Label(popup, text=title, font=FONT_HEADER, bg=self.theme["BG"], fg=self.theme["HEADER"]).pack(pady=12)
        entries = {}
        for field, opts in fields.items():
            frame = tk.Frame(popup, bg=self.theme["BG"])
            frame.pack(pady=6)
            tk.Label(frame, text=field + ":", bg=self.theme["BG"], font=FONT_NORMAL, fg=self.theme["TEXT"]).pack(side="left", padx=6)
            ent = self.styled_entry(frame, show=opts.get("show"), width=opts.get("width", 24))
            ent.pack(side="left")
            entries[field] = ent

        def submit():
            vals = {k: v.get() for k, v in entries.items()}
            popup.destroy()
            callback(vals)

        btn_frame = tk.Frame(popup, bg=self.theme["BG"])
        btn_frame.pack(pady=12)
        self.styled_button(btn_frame, "Submit", submit, icon="✅").pack(side="left", padx=8)
        self.styled_button(btn_frame, "Cancel", popup.destroy, icon="❌").pack(side="left", padx=8)

    # ---------- Login / Register ----------
    def login_screen(self):
        self.clear_screen()
        frame = tk.Frame(self.root, bg=self.theme["BG"])
        frame.pack(expand=True, fill="both")
        header = tk.Label(frame, text="📧 Multi-device Email App", font=("Segoe UI", 26, "bold"), bg=self.theme["BG"], fg=self.theme["HEADER"])
        header.pack(pady=28)
        card = tk.Frame(frame, bg=self.theme["SIDEBAR"], bd=0)
        card.pack(pady=10, ipadx=20, ipady=14)

        self.styled_button(card, "Register", self.register, width=26, icon="📝").pack(pady=10)
        self.styled_button(card, "Login", self.login, width=26, icon="🔑").pack(pady=6)
        self.styled_button(card, "Exit", self.root.quit, width=26, icon="🚪").pack(pady=6)

        tk.Button(frame, text="🌗 Toggle Theme", command=self.toggle_theme, bg=self.theme["CARD"], fg=self.theme["TEXT"], relief="flat", cursor="hand2").pack(pady=18)

    def register(self):
        def handle_reg(vals):
            username, password = vals["Username"], vals["Password"]
            if not username or not password:
                messagebox.showerror("Error", "Username and password required")
                return
            try:
                c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                conn.commit()
                messagebox.showinfo("Success", "Registration successful!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "User already exists!")

        self.popup_window("Register", {"Username": {}, "Password": {"show": "*"}}, handle_reg)

    def login(self):
        def handle_login(vals):
            username, password = vals["Username"], vals["Password"]
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            if c.fetchone():
                self.current_user = username
                messagebox.showinfo("Welcome", f"Welcome {username}!")
                self.main_menu()
            else:
                messagebox.showerror("Error", "Invalid credentials")
        self.popup_window("Login", {"Username": {}, "Password": {"show": "*"}}, handle_login)

    # ---------- Spam Detection ----------
    def detect_spam(self, subject, body):
        spam_keywords = [
            "lottery", "win money", "prize", "free offer", "urgent",
            "cash", "credit", "loan", "congratulations", "claim now", "click here",
        ]
        text = f"{subject} {body}".lower()
        for w in spam_keywords:
            if w in text:
                return True
        return False

    # ---------- Main UI / Menu ----------
    def main_menu(self):
        self.clear_screen()

        # Sidebar
        sidebar = tk.Frame(self.root, bg=self.theme["SIDEBAR"], width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = tk.Label(sidebar, text="📧 MailDesk", font=("Segoe UI", 18, "bold"), bg=self.theme["SIDEBAR"], fg=self.theme["HEADER"])
        logo.pack(pady=20)

        tk.Label(sidebar, text=f"Signed in as\n{self.current_user}", bg=self.theme["SIDEBAR"], fg=self.theme["TEXT"], font=FONT_SMALL, justify="center").pack(pady=8)

        self.styled_button(sidebar, "Compose", lambda: self.send_email(), icon="✉️", width=20).pack(pady=8)
        self.styled_button(sidebar, "Mailbox", lambda: self.open_mailbox_tabs(), icon="📂", width=20).pack(pady=6)
        self.styled_button(sidebar, "Analytics", lambda: self.open_analytics(), icon="📊", width=20).pack(pady=6)
        self.styled_button(sidebar, "Export All (CSV)", lambda: self.export_all_emails(), icon="📥", width=20).pack(pady=6)
        self.styled_button(sidebar, "Logout", self.logout, icon="🚪", width=20).pack(pady=14)

        tk.Button(sidebar, text="🌗 Toggle Theme", command=self.toggle_theme, bg=self.theme["CARD"], fg=self.theme["TEXT"], relief="flat", cursor="hand2").pack(side="bottom", pady=12)

        # Main content area
        content = tk.Frame(self.root, bg=self.theme["BG"])
        content.pack(side="right", fill="both", expand=True)

        header = tk.Label(content, text="Welcome to MailDesk", font=FONT_HEADER, bg=self.theme["BG"], fg=self.theme["HEADER"])
        header.pack(pady=28)

        summary_frame = tk.Frame(content, bg=self.theme["BG"])
        summary_frame.pack(padx=18, pady=6, fill="x")

        # Quick stats
        c.execute("SELECT COUNT(*) FROM emails WHERE sender=?", (self.current_user,))
        sent = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM emails WHERE recipient=?", (self.current_user,))
        received = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM emails WHERE (sender=? OR recipient=?) AND attachment IS NOT NULL", (self.current_user,self.current_user))
        attachments = c.fetchone()[0] or 0
        tk.Label(summary_frame, text=f"Sent: {sent}", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(side="left", padx=12)
        tk.Label(summary_frame, text=f"Received: {received}", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(side="left", padx=12)
        tk.Label(summary_frame, text=f"Attachments: {attachments}", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(side="left", padx=12)

    # ---------- Compose Email ----------
    def send_email(self, prefill=None):
        popup = tk.Toplevel(self.root)
        popup.title("Compose Email")
        popup.geometry("660x520")
        popup.configure(bg=self.theme["BG"])
        popup.grab_set()

        tk.Label(popup, text="Compose Email", font=FONT_HEADER, bg=self.theme["BG"], fg=self.theme["HEADER"]).pack(pady=10)

        # To
        frm_to = tk.Frame(popup, bg=self.theme["BG"])
        frm_to.pack(pady=6, fill="x", padx=12)
        tk.Label(frm_to, text="To:", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(side="left", padx=6)
        ent_to = self.styled_entry(frm_to, width=38)
        ent_to.pack(side="left")
        if prefill and prefill.get("To"):
            ent_to.insert(0, prefill["To"])

        # Subject
        frm_sub = tk.Frame(popup, bg=self.theme["BG"])
        frm_sub.pack(pady=6, fill="x", padx=12)
        tk.Label(frm_sub, text="Subject:", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(side="left", padx=6)
        ent_sub = self.styled_entry(frm_sub, width=38)
        ent_sub.pack(side="left")
        if prefill and prefill.get("Subject"):
            ent_sub.insert(0, prefill["Subject"])

        # Message
        frm_msg = tk.Frame(popup, bg=self.theme["BG"])
        frm_msg.pack(pady=6, fill="both", expand=True, padx=12)
        tk.Label(frm_msg, text="Message:", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(anchor="nw")
        txt_msg = tk.Text(frm_msg, font=FONT_NORMAL, height=14, wrap="word", bd=1, relief="solid")
        txt_msg.pack(fill="both", expand=True, pady=6)
        if prefill and prefill.get("Message"):
            txt_msg.insert("1.0", prefill["Message"])

        # Attachment
        attach_data = {"file": None, "name": None}
        def choose_file():
            path = filedialog.askopenfilename()
            if path:
                with open(path, "rb") as f:
                    data = f.read()
                attach_data["file"] = base64.b64encode(data).decode("utf-8")
                attach_data["name"] = os.path.basename(path)
                messagebox.showinfo("Attached", f"Attached {attach_data['name']}")

        btn_attach = tk.Button(popup, text="📎 Attach File", command=choose_file, bg=self.theme["BTN"], fg="white", relief="flat", cursor="hand2")
        btn_attach.pack(pady=6)

        # Send
        def handle_send():
            recipient = ent_to.get().strip()
            subject = ent_sub.get().strip()
            body = txt_msg.get("1.0", tk.END).strip()
            attachment = attach_data["file"]
            if not recipient or not subject or not body:
                messagebox.showerror("Error", "All fields are required!")
                return
            # recipient must exist as a user
            c.execute("SELECT * FROM users WHERE username=?", (recipient,))
            if not c.fetchone():
                messagebox.showerror("Error", "Recipient not found!")
                return
            timestamp = datetime.now().isoformat()
            is_spam = 1 if self.detect_spam(subject, body) else 0
            c.execute(
                "INSERT INTO emails (recipient, sender, subject, body, attachment, timestamp, is_spam) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (recipient, self.current_user, subject, body, attachment, timestamp, is_spam)
            )
            conn.commit()
            if is_spam:
                messagebox.showwarning("Spam", "This email was flagged as spam and delivered to Spam folder.")
            else:
                messagebox.showinfo("Sent", "Email sent successfully!")
            popup.destroy()

        btn_frame = tk.Frame(popup, bg=self.theme["BG"])
        btn_frame.pack(pady=10)
        self.styled_button(btn_frame, "Send", handle_send, icon="✈️").pack(side="left", padx=8)
        self.styled_button(btn_frame, "Cancel", popup.destroy, icon="❌").pack(side="left", padx=8)

    # ---------- Mailbox / Tabs ----------
    def open_mailbox_tabs(self):
        win = tk.Toplevel(self.root)
        win.title("Mailbox")
        win.geometry("900x650")
        win.configure(bg=self.theme["BG"])
        win.grab_set()

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        inbox_tab = tk.Frame(nb, bg=self.theme["BG"])
        sent_tab = tk.Frame(nb, bg=self.theme["BG"])
        spam_tab = tk.Frame(nb, bg=self.theme["BG"])
        nb.add(inbox_tab, text="Inbox 📥")
        nb.add(sent_tab, text="Sent 📤")
        nb.add(spam_tab, text="Spam 🚫")

        self.setup_mail_tab(inbox_tab, inbox=True, spam=False)
        self.setup_mail_tab(sent_tab, inbox=False, spam=False)
        self.setup_mail_tab(spam_tab, inbox=True, spam=True)

    def setup_mail_tab(self, tab, inbox=True, spam=False):
        # Top controls
        top = tk.Frame(tab, bg=self.theme["BG"])
        top.pack(fill="x", pady=6, padx=8)
        tk.Label(top, text="Search:", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(side="left", padx=6)
        search_var = tk.StringVar()
        search_entry = tk.Entry(top, textvariable=search_var, font=FONT_NORMAL, width=28)
        search_entry.pack(side="left", padx=6)
        tk.Label(top, text="Sort by:", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(side="left", padx=6)
        sort_var = tk.StringVar(value="Subject")
        sort_menu = ttk.Combobox(top, textvariable=sort_var, values=["Subject", "Sender/Recipient", "Date"], width=18)
        sort_menu.pack(side="left", padx=6)

        # Scroll area
        canvas = tk.Canvas(tab, bg=self.theme["BG"], highlightthickness=0)
        scrollbar = tk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.theme["BG"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def refresh():
            for w in scroll_frame.winfo_children():
                w.destroy()

            if spam:
                q = "SELECT id, sender, subject, body, attachment, timestamp FROM emails WHERE recipient=? AND is_spam=1"
                params = (self.current_user,)
            else:
                if inbox:
                    q = "SELECT id, sender, subject, body, attachment, timestamp FROM emails WHERE recipient=?"
                    params = (self.current_user,)
                else:
                    q = "SELECT id, recipient, subject, body, attachment, timestamp FROM emails WHERE sender=?"
                    params = (self.current_user,)
            c.execute(q, params)
            emails = c.fetchall()

            # Filter by search
            kw = search_var.get().lower()
            if kw:
                filtered = []
                for e in emails:
                    # person is at index 1 (sender or recipient depending)
                    person = e[1] or ""
                    subj = e[2] or ""
                    body = e[3] or ""
                    if kw in person.lower() or kw in subj.lower() or kw in body.lower():
                        filtered.append(e)
                emails = filtered

            # Sort
            if sort_var.get() == "Subject":
                emails.sort(key=lambda x: (x[2] or "").lower())
            elif sort_var.get() == "Sender/Recipient":
                emails.sort(key=lambda x: (x[1] or "").lower())
            else:  # Date
                def extract_date(e):
                    ts = e[5] or ""
                    try:
                        return ts
                    except:
                        return ""
                emails.sort(key=extract_date, reverse=True)

            if not emails:
                tk.Label(scroll_frame, text="No emails.", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(pady=24)
                return

            for row in emails:
                email_id = row[0]
                person = row[1]
                subject = row[2] or ""
                body = row[3] or ""
                attachment = row[4]
                timestamp = row[5] or ""
                # Card
                card = tk.Frame(scroll_frame, bg=self.theme["CARD"], bd=1, relief="flat")
                card.pack(fill="x", padx=12, pady=8)
                card.bind("<Enter>", lambda e, f=card: f.config(bg=self.theme["CARD_HOVER"]))
                card.bind("<Leave>", lambda e, f=card: f.config(bg=self.theme["CARD"]))

                # Header row
                hdr = tk.Frame(card, bg=self.theme["CARD"])
                hdr.pack(fill="x", padx=8, pady=6)
                name_label = tk.Label(hdr, text=(("From: " if inbox or spam else "To: ") + str(person)), font=("Segoe UI", 10, "bold"), fg=self.theme["TEXT"], bg=self.theme["CARD"], anchor="w")
                name_label.pack(side="left", fill="x", expand=True)
                time_label = tk.Label(hdr, text=(timestamp.split("T")[0] if timestamp else ""), bg=self.theme["CARD"], fg=self.theme["TEXT"], font=FONT_SMALL)
                time_label.pack(side="right")

                subj_label = tk.Label(card, text=f"Subject: {subject}", fg=self.theme["TEXT"], bg=self.theme["CARD"], font=("Segoe UI", 10, "italic"))
                subj_label.pack(fill="x", padx=8)
                body_label = tk.Label(card, text=(body[:250] + ("..." if len(body) > 250 else "")), fg=self.theme["TEXT"], bg=self.theme["CARD"], font=FONT_NORMAL, justify="left", wraplength=700)
                body_label.pack(fill="x", padx=8, pady=6)

                if attachment:
                    def save_attachment(data=attachment):
                        fdata = base64.b64decode(data)
                        save_path = filedialog.asksaveasfilename(defaultextension="", initialfile="attachment")
                        if save_path:
                            with open(save_path, "wb") as f:
                                f.write(fdata)
                            messagebox.showinfo("Saved", f"Attachment saved to {save_path}")
                    tk.Button(card, text="📎 Download Attachment", command=save_attachment, bg=self.theme["BTN"], fg="white", relief="flat", cursor="hand2").pack(padx=8, pady=6, anchor="w")

                # Buttons
                btns = tk.Frame(card, bg=self.theme["CARD"])
                btns.pack(padx=8, pady=6, anchor="e")
                if inbox and not spam:
                    self.styled_button(btns, "Reply", lambda s=person, sub=subject: self.send_email(prefill={"To": s, "Subject": f"Re: {sub}"}), width=10, icon="↩️").pack(side="left", padx=6)
                    self.styled_button(btns, "Mark Spam", lambda eid=email_id, f=card: self.mark_as_spam(eid, f), width=12, icon="🚫").pack(side="left", padx=6)
                    self.styled_button(btns, "Delete", lambda eid=email_id, f=card: self.delete_email(eid, f), width=10, icon="🗑️").pack(side="left", padx=6)
                else:
                    self.styled_button(btns, "Delete", lambda eid=email_id, f=card: self.delete_email(eid, f), width=10, icon="🗑️").pack(side="left", padx=6)

        # Traces
        search_var.trace_add("write", lambda *a: refresh())
        sort_var.trace_add("write", lambda *a: refresh())

        refresh()

    def mark_as_spam(self, email_id, card_frame=None):
        c.execute("UPDATE emails SET is_spam=1 WHERE id=?", (email_id,))
        conn.commit()
        if card_frame:
            card_frame.destroy()
        messagebox.showinfo("Marked", "Email moved to Spam folder")

    def delete_email(self, email_id, card_frame=None):
        if messagebox.askyesno("Delete", "Are you sure you want to delete this email?"):
            c.execute("DELETE FROM emails WHERE id=?", (email_id,))
            conn.commit()
            if card_frame:
                card_frame.destroy()

    def logout(self):
        self.current_user = None
        self.login_screen()

    # ---------- Analytics (Bar + Pie) ----------
    def open_analytics(self):
        popup = tk.Toplevel(self.root)
        popup.title("Analytics")
        popup.geometry("900x620")
        popup.configure(bg=self.theme["BG"])
        popup.grab_set()

        tk.Label(popup, text="📊 Email Analytics", font=FONT_HEADER, bg=self.theme["BG"], fg=self.theme["HEADER"]).pack(pady=12)
        content = tk.Frame(popup, bg=self.theme["BG"])
        content.pack(fill="both", expand=True, padx=12, pady=6)

        left = tk.Frame(content, bg=self.theme["BG"])
        left.pack(side="left", fill="y", padx=8, pady=6)
        right = tk.Frame(content, bg=self.theme["BG"])
        right.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        # Stats
        c.execute("SELECT COUNT(*) FROM emails WHERE sender=?", (self.current_user,))
        total_sent = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM emails WHERE recipient=?", (self.current_user,))
        total_received = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM emails WHERE (sender=? OR recipient=?) AND attachment IS NOT NULL",(self.current_user,self.current_user))
        attachment_count = c.fetchone()[0] or 0
        c.execute("SELECT AVG(LENGTH(subject)) FROM emails WHERE sender=? OR recipient=?", (self.current_user, self.current_user))
        avg_subject_len = c.fetchone()[0] or 0
        c.execute("SELECT AVG(LENGTH(body)) FROM emails WHERE sender=? OR recipient=?", (self.current_user, self.current_user))
        avg_body_len = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM emails WHERE (sender=? OR recipient=?) AND is_spam=1", (self.current_user,self.current_user))
        total_spam = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM emails WHERE recipient=? AND is_spam=1", (self.current_user,))
        spam_received = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM emails WHERE sender=? AND is_spam=1", (self.current_user,))
        spam_sent = c.fetchone()[0] or 0

        stats_text = (
            f"Total Sent: {total_sent}\n"
            f"Total Received: {total_received}\n"
            f"Attachments: {attachment_count}\n"
            f"Avg Subject Len: {avg_subject_len:.1f}\n"
            f"Avg Body Len: {avg_body_len:.1f}\n\n"
            f"Total Spam (sent/received): {total_spam}\n"
            f"Spam Received: {spam_received}\n"
            f"Spam Sent: {spam_sent}\n"
        )
        tk.Label(left, text="Summary", font=("Segoe UI", 13, "bold"), bg=self.theme["BG"], fg=self.theme["HEADER"]).pack(anchor="w")
        tk.Label(left, text=stats_text, font=FONT_NORMAL, bg=self.theme["BG"], fg=self.theme["TEXT"], justify="left").pack(anchor="w")

        # Top contacts
        tk.Label(left, text="Top Contacts", font=("Segoe UI", 13, "bold"), bg=self.theme["BG"], fg=self.theme["HEADER"]).pack(anchor="w", pady=(6,0))
        c.execute(
            """
            SELECT CASE WHEN sender=? THEN recipient ELSE sender END AS contact, COUNT(*) as cnt
            FROM emails
            WHERE sender=? OR recipient=?
            GROUP BY contact
            ORDER BY cnt DESC
            LIMIT 5
            """, (self.current_user, self.current_user, self.current_user)
        )
        top_contacts = c.fetchall()
        if top_contacts:
            for contact, cnt in top_contacts:
                tk.Label(left, text=f"{contact} — {cnt}", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(anchor="w")
        else:
            tk.Label(left, text="No contacts yet.", bg=self.theme["BG"], fg=self.theme["TEXT"], font=FONT_NORMAL).pack(anchor="w")

        # Emails per day (last 30 days)
        today = datetime.now().date()
        start_date = today - timedelta(days=29)
        c.execute(
            "SELECT SUBSTR(timestamp,1,10) as dt, COUNT(*) FROM emails WHERE (sender=? OR recipient=?) AND timestamp >= ? GROUP BY dt ORDER BY dt",
            (self.current_user, self.current_user, start_date.isoformat())
        )
        rows = c.fetchall()
        date_counts = { (start_date + timedelta(days=i)).isoformat(): 0 for i in range(30) }
        for dt, cnt in rows:
            if dt in date_counts:
                date_counts[dt] = cnt

        # Spam per month (last 6 months)
        months = []
        month_counts = {}
        for i in range(5, -1, -1):
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1
            key = f"{year:04d}-{month:02d}"
            months.append(key)
            month_counts[key] = 0
        six_months_ago = (today.replace(day=1) - timedelta(days=180)).isoformat()
        c.execute("SELECT SUBSTR(timestamp,1,7) as ym, COUNT(*) FROM emails WHERE (sender=? OR recipient=?) AND is_spam=1 AND timestamp >= ? GROUP BY ym ORDER BY ym", (self.current_user, self.current_user, six_months_ago))
        mrows = c.fetchall()
        for ym, cnt in mrows:
            if ym in month_counts:
                month_counts[ym] = cnt

        # Try to draw charts
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            # Bar: Emails per day (last 30)
            fig1, ax1 = plt.subplots(figsize=(6, 2.2))
            dates = list(date_counts.keys())
            counts = list(date_counts.values())
            ax1.bar(range(len(dates)), counts)
            ticks = list(range(0, len(dates), max(1, len(dates)//8)))
            ax1.set_xticks(ticks)
            ax1.set_xticklabels([dates[i] for i in ticks], rotation=45, ha="right", fontsize=8)
            ax1.set_title("Emails per day (last 30 days)")
            ax1.set_ylabel("Count")
            fig1.tight_layout()
            canvas1 = FigureCanvasTkAgg(fig1, master=right)
            widget1 = canvas1.get_tk_widget()
            widget1.pack(fill="x", pady=(0, 12))
            canvas1.draw()

            # Pie: Spam vs Non-spam (received)
            c.execute("SELECT COUNT(*) FROM emails WHERE recipient=? AND is_spam=1", (self.current_user,))
            spam_recv = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM emails WHERE recipient=? AND (is_spam=0 OR is_spam IS NULL)", (self.current_user,))
            normal_recv = c.fetchone()[0] or 0
            labels = ["Normal", "Spam"]
            sizes = [normal_recv, spam_recv]
            fig2, ax2 = plt.subplots(figsize=(4, 3))
            ax2.pie(sizes, labels=labels, autopct=lambda p: f"{p:.1f}% ({int(p*sum(sizes)/100)})", startangle=90)
            ax2.set_title("Inbox: Normal vs Spam")
            fig2.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, master=right)
            widget2 = canvas2.get_tk_widget()
            widget2.pack(fill="both", expand=True)
            canvas2.draw()
        except Exception as e:
            # fallback textual
            txt = tk.Text(right, height=20, width=60, wrap="none", font=("Courier", 10))
            txt.insert("1.0", "Date       | Count\n")
            txt.insert("2.0", "-" * 30 + "\n")
            for d, cnt in date_counts.items():
                txt.insert(tk.END, f"{d} | {cnt}\n")
            txt.insert(tk.END, "\nSpam per month:\n")
            for m in months:
                txt.insert(tk.END, f"{m} | {month_counts.get(m,0)}\n")
            txt.config(state="disabled")
            txt.pack(fill="both", expand=True)

        # Export & Close
        btn_frame = tk.Frame(popup, bg=self.theme["BG"])
        btn_frame.pack(pady=8)
        self.styled_button(btn_frame, "Export Stats (CSV)", lambda: self.export_stats(date_counts, top_contacts, month_counts), width=20, icon="💾").pack(side="left", padx=8)
        self.styled_button(btn_frame, "Close", popup.destroy, width=12, icon="❌").pack(side="left", padx=8)

    def export_stats(self, date_counts, top_contacts, month_counts):
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not save_path:
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("Metric,Value\n")
                c.execute("SELECT COUNT(*) FROM emails WHERE sender=?", (self.current_user,))
                total_sent = c.fetchone()[0] or 0
                c.execute("SELECT COUNT(*) FROM emails WHERE recipient=?", (self.current_user,))
                total_received = c.fetchone()[0] or 0
                c.execute("SELECT COUNT(*) FROM emails WHERE (sender=? OR recipient=?) AND attachment IS NOT NULL", (self.current_user, self.current_user))
                attachment_count = c.fetchone()[0] or 0
                f.write(f"Total Sent,{total_sent}\n")
                f.write(f"Total Received,{total_received}\n")
                f.write(f"Total (Sent+Received),{total_sent + total_received}\n")
                f.write(f"Emails with Attachments,{attachment_count}\n\n")
                f.write("Top Contacts,Count\n")
                for contact, cnt in top_contacts:
                    f.write(f"{contact},{cnt}\n")
                f.write("\nDate,Count\n")
                for d, cnt in date_counts.items():
                    f.write(f"{d},{cnt}\n")
                f.write("\nSpam Month,Count\n")
                for m, cnt in month_counts.items():
                    f.write(f"{m},{cnt}\n")
            messagebox.showinfo("Exported", f"Analytics exported to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def export_all_emails(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not save_path:
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("id,recipient,sender,subject,body,attachment_present,timestamp,is_spam\n")
                c.execute("SELECT id,recipient,sender,subject,body,attachment,timestamp,is_spam FROM emails")
                for row in c.fetchall():
                    aid, recip, snd, subj, body, att, ts, is_spam = row
                    f.write(f"{aid},{recip},{snd},{subj.replace(',', ' ')},{body.replace(',', ' ')},{1 if att else 0},{ts},{is_spam}\n")
            messagebox.showinfo("Exported", f"All emails exported to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = EmailApp(root)
    root.mainloop()
