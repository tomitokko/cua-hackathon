import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Workflow Chat")

        self._apply_theme()
        self._configure_window()
        self._build_layout()

    def _apply_theme(self) -> None:
        """Set up colors, fonts, and ttk styling for a modern look."""
        self.bg_color = "#e7edf5"  # light grey-blue background
        self.card_color = "#f8fbff"  # white-ish cards
        self.accent_color = "#4b84d7"  # medium blue accent
        self.text_color = "#1f2933"  # dark grey text

        self.configure(background=self.bg_color)

        # Configure default fonts for a modern feel
        base_font = "Segoe UI"
        fallback_font = "Helvetica"
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family=base_font, size=11)
        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family=base_font, size=11)
        fixed_font = tkfont.nametofont("TkFixedFont")
        fixed_font.configure(family=fallback_font, size=11)
        heading_font = tkfont.nametofont("TkHeadingFont")
        heading_font.configure(family=base_font, size=14, weight="bold")

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "App.TFrame",
            background=self.bg_color,
        )
        style.configure(
            "Card.TFrame",
            background=self.card_color,
        )
        style.configure(
            "ChatHeader.TLabel",
            background=self.card_color,
            foreground=self.text_color,
            font=(base_font, 13, "bold"),
        )
        style.configure(
            "Placeholder.TLabel",
            background=self.bg_color,
            foreground=self.text_color,
            font=(base_font, 16, "bold"),
        )
        style.configure(
            "Accent.TButton",
            background=self.accent_color,
            foreground="white",
            borderwidth=0,
            focusthickness=3,
            focuscolor=self.bg_color,
            padding=(18, 8),
            font=(base_font, 11, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#3a6bb2"), ("pressed", "#335f9f")],
        )

    def _configure_window(self) -> None:
        """Initialize window size and center on screen."""
        width, height = 1200, 750
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _build_layout(self) -> None:
        container = ttk.Frame(self, style="App.TFrame")
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self._build_chat_panel(container)
        self._build_placeholder_panel(container)

    def _build_chat_panel(self, parent: ttk.Frame) -> None:
        chat_frame = ttk.Frame(parent, style="Card.TFrame", padding=20)
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        chat_frame.grid_rowconfigure(1, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        header = ttk.Label(chat_frame, text="Agent chat", style="ChatHeader.TLabel")
        header.grid(row=0, column=0, sticky="ew")

        messages_container = ttk.Frame(chat_frame, style="Card.TFrame")
        messages_container.grid(row=1, column=0, sticky="nsew", pady=15)
        messages_container.grid_rowconfigure(0, weight=1)
        messages_container.grid_columnconfigure(0, weight=1)

        self.chat_text = tk.Text(
            messages_container,
            wrap="word",
            relief="flat",
            background=self.card_color,
            foreground=self.text_color,
            font=("Segoe UI", 11),
            height=10,
            spacing3=6,
            padx=4,
            pady=4,
        )
        self.chat_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(messages_container, orient="vertical", command=self.chat_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        self.chat_text.configure(state="disabled")

        self.chat_text.tag_configure("sender", foreground="#2f5d9f", font=("Segoe UI", 11, "bold"))
        self.chat_text.tag_configure("message", foreground=self.text_color, font=("Segoe UI", 10))

        self._insert_initial_messages()

        entry_row = ttk.Frame(chat_frame, style="Card.TFrame")
        entry_row.grid(row=2, column=0, sticky="ew")
        entry_row.grid_columnconfigure(0, weight=1)
        entry_row.grid_columnconfigure(1, weight=0)

        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(entry_row, textvariable=self.message_var, font=("Segoe UI", 11))
        self.message_entry.grid(row=0, column=0, sticky="ew", pady=(10, 0))
        self.message_entry.bind("<Return>", self._on_send)

        send_button = ttk.Button(entry_row, text="Send", style="Accent.TButton", command=self._on_send)
        send_button.grid(row=0, column=1, padx=(12, 0), pady=(10, 0))

    def _build_placeholder_panel(self, parent: ttk.Frame) -> None:
        placeholder_frame = ttk.Frame(parent, style="Card.TFrame", padding=20)
        placeholder_frame.grid(row=0, column=1, sticky="nsew")

        parent.grid_columnconfigure(1, weight=1)

        placeholder_frame.grid_rowconfigure(0, weight=1)
        placeholder_frame.grid_columnconfigure(0, weight=1)

        label = ttk.Label(placeholder_frame, text="Future workflow view goes here", style="Placeholder.TLabel")
        label.grid(row=0, column=0, sticky="nsew")

    def _insert_initial_messages(self) -> None:
        sample_messages = [
            ("You", "Here is the latest process update."),
            ("Agent", "Thanks! I'll keep learning this workflow."),
            ("You", "Let me know when you're ready for the next step."),
        ]
        for sender, message in sample_messages:
            self._append_message(sender, message)
            self.chat_text.insert("end", "\n")
        self.chat_text.see("end")

    def _append_message(self, sender: str, message: str) -> None:
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", f"{sender}: ", "sender")
        self.chat_text.insert("end", f"{message}\n", "message")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def _on_send(self, event: tk.Event | None = None) -> None:
        message = self.message_var.get().strip()
        if not message:
            return

        print(f"User sent: {message}")
        self._append_message("You", message)
        self.message_var.set("")

        fake_reply = "Got it, I will learn this workflow later."
        self.after(200, lambda: self._append_message("Agent", fake_reply))


if __name__ == "__main__":
    app = App()
    app.mainloop()
