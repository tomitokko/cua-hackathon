import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from datetime import datetime
import threading

# Optional speech recognition (install: pip install SpeechRecognition pyaudio)
try:
    import speech_recognition as sr  # type: ignore
except Exception:  # pragma: no cover
    sr = None


class WorkflowHistoryWindow(tk.Toplevel):
    """Popup window to view recorded workflow history."""
    
    def __init__(self, parent: tk.Tk, theme_colors: dict):
        """
        Initialize the workflow history viewer.
        
        Args:
            parent: The main application window
            theme_colors: Dictionary of theme colors from parent
        """
        super().__init__(parent)
        
        self.parent = parent
        self.theme_colors = theme_colors
        
        self.title("Workflow History")
        self.configure(background=theme_colors['bg_color'])
        
        # Size and center the window
        width, height = 700, 500
        self.geometry(f"{width}x{height}")
        self._center_window(width, height)
        
        # Prevent multiple instances
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        # Build UI
        self._setup_styles()
        self._build_ui()
        
        # Focus this window
        self.lift()
        self.focus_force()
    
    def _center_window(self, width: int, height: int) -> None:
        """Center the window relative to the parent."""
        self.update_idletasks()
        
        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _setup_styles(self) -> None:
        """Configure ttk styles for the history window."""
        style = ttk.Style(self)
        
        # Treeview styling
        style.configure(
            "History.Treeview",
            background="#ffffff",
            foreground=self.theme_colors['text_color'],
            fieldbackground="#ffffff",
            borderwidth=0,
            font=("Segoe UI", 10),
            rowheight=28,
        )
        style.configure(
            "History.Treeview.Heading",
            background=self.theme_colors['header_bg'],
            foreground=self.theme_colors['text_color'],
            borderwidth=1,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "History.Treeview",
            background=[("selected", self.theme_colors['accent_color'])],
            foreground=[("selected", "white")],
        )
        
        # Alternating row colors
        self.tag_configure_colors = {
            'evenrow': '#f7f9fc',
            'oddrow': '#ffffff'
        }
    
    def _build_ui(self) -> None:
        """Build the history window UI."""
        # Main container with padding
        container = tk.Frame(
            self,
            background=self.theme_colors['card_color'],
            padx=20,
            pady=20
        )
        container.pack(fill="both", expand=True)
        
        # Header
        header_label = tk.Label(
            container,
            text="Recorded Workflows",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_colors['text_color'],
            background=self.theme_colors['card_color']
        )
        header_label.pack(anchor="w", pady=(0, 15))
        
        # Treeview container with border
        tree_container = tk.Frame(
            container,
            background=self.theme_colors['border_color'],
            highlightthickness=0
        )
        tree_container.pack(fill="both", expand=True, pady=(0, 15))
        
        # Treeview with scrollbar
        tree_frame = tk.Frame(tree_container, background="#ffffff")
        tree_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Create Treeview
        columns = ("name", "date", "steps")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="History.Treeview",
            selectmode="browse"
        )
        
        # Configure columns
        self.tree.heading("name", text="Workflow Name")
        self.tree.heading("date", text="Date Recorded")
        self.tree.heading("steps", text="Steps")
        
        self.tree.column("name", width=300, anchor="w")
        self.tree.column("date", width=200, anchor="w")
        self.tree.column("steps", width=100, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # Populate with placeholder data
        self._populate_placeholder_data()
        
        # Close button
        close_button = ttk.Button(
            container,
            text="Close",
            style="Accent.TButton",
            command=self.destroy
        )
        close_button.pack(anchor="e")
        try:
            close_button.configure(cursor="hand2")
        except Exception:
            pass
    
    def _populate_placeholder_data(self) -> None:
        """Add placeholder workflow data to the tree."""
        placeholder_workflows = [
            ("Email Check Workflow", "2025-11-15 09:30 AM", "5"),
            ("Daily Report Generation", "2025-11-14 02:15 PM", "8"),
            ("File Backup Routine", "2025-11-13 11:45 AM", "3"),
            ("Database Cleanup", "2025-11-12 04:20 PM", "12"),
            ("Screenshot Organizer", "2025-11-11 10:00 AM", "6"),
        ]
        
        for idx, (name, date, steps) in enumerate(placeholder_workflows):
            # Alternate row colors
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            self.tree.insert(
                "",
                "end",
                values=(name, date, steps),
                tags=(tag,)
            )
        
        # Configure row colors
        self.tree.tag_configure('evenrow', background='#f7f9fc')
        self.tree.tag_configure('oddrow', background='#ffffff')
    
    def _on_tree_select(self, event) -> None:
        """Handle workflow selection from tree."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if values:
                workflow_name = values[0]
                # Call stub method
                self.on_select_workflow(workflow_name)
    
    def on_select_workflow(self, workflow_id: str) -> None:
        """
        Stub method for workflow selection.
        
        Args:
            workflow_id: The selected workflow identifier
        """
        print(f"[Stub] Selected workflow: {workflow_id}")
        # Future: Load workflow details and display


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Workflow Chat")
        
        # Agent state tracking
        self.agent_state = "idle"  # idle, recording, executing
        
        # Track history window instance
        self.history_window = None

        # Ensure key theme attributes exist before building UI (defensive)
        self.bg_color = getattr(self, "bg_color", "#e7edf5")
        self.card_color = getattr(self, "card_color", "#fbfcfd")
        self.header_bg = getattr(self, "header_bg", "#d4dde8")
        self.accent_color = getattr(self, "accent_color", "#4a81ff")
        self.text_color = getattr(self, "text_color", "#1f2933")
        self.border_color = getattr(self, "border_color", "#d3dae3")
        self.user_bubble_bg = getattr(self, "user_bubble_bg", "#eef4ff")
        self.agent_bubble_bg = getattr(self, "agent_bubble_bg", "#f7f7f7")

        self._apply_theme()
        self._configure_window()
        self._build_layout()
        
        # Update send button state initially
        self._update_send_button_state()

    def _apply_theme(self) -> None:
        """Set up colors, fonts, and ttk styling for a modern look."""
        self.bg_color = "#e7edf5"  # light grey-blue background
        self.card_color = "#fbfcfd"  # soft off-white cards
        self.header_bg = "#d4dde8"  # slightly darker grey-blue for header
        self.accent_color = "#4a81ff"  # bright blue accent
        self.text_color = "#1f2933"  # dark grey text
        self.border_color = "#d3dae3"  # soft border color
        self.agent_bubble_bg = "#f7f7f7"  # light grey tint for agent messages

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
            "Custom.TPanedwindow",
            background=self.bg_color,
        )
        style.configure(
            "Card.TFrame",
            background=self.card_color,
            relief="flat",
        )
        style.configure(
            "Header.TFrame",
            background=self.header_bg,
        )
        style.configure(
            "ChatTitle.TLabel",
            background=self.header_bg,
            foreground=self.text_color,
            font=(base_font, 14, "bold"),
        )
        style.configure(
            "ChatSubtitle.TLabel",
            background=self.header_bg,
            foreground="#52606d",
            font=(base_font, 10),
        )
        style.configure(
            "StatusBadge.TLabel",
            background=self.header_bg,
            foreground="#52606d",
            font=(base_font, 9, "bold"),
            relief="flat",
        )
        style.configure(
            "Placeholder.TLabel",
            background=self.card_color,
            foreground="#7c8a99",
            font=(base_font, 14),
        )
        style.configure(
            "Accent.TButton",
            background=self.accent_color,
            foreground="white",
            borderwidth=0,
            relief="flat",
            focusthickness=0,
            padding=(22, 11),
            font=(base_font, 11, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#3a6bd9"), ("pressed", "#2f5bb8")],
        )
        # Subtle icon/ghost button for mic
        style.configure(
            "Ghost.TButton",
            background=self.card_color,
            foreground=self.text_color,
            relief="flat",
            borderwidth=0,
            padding=(10, 8),
            font=(base_font, 11)
        )
        style.map(
            "Ghost.TButton",
            background=[("active", "#eef2f7")]
        )
        # Modernized scrollbar tone
        style.configure(
            "Modern.Vertical.TScrollbar",
            gripcount=0,
            background="#cdd5e1",
            darkcolor="#c3cad6",
            lightcolor="#e5eaf2",
            troughcolor="#e9eef6",
            bordercolor="#e5eaf2",
            arrowcolor="#6b7280"
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
        # Use a resizable paned window for modern split view
        paned = ttk.Panedwindow(self, orient="horizontal", style="Custom.TPanedwindow")
        paned.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        left_container = ttk.Frame(paned, style="App.TFrame")
        right_container = ttk.Frame(paned, style="App.TFrame")

        paned.add(left_container, weight=1)
        paned.add(right_container, weight=1)

        # Build panes
        self._build_chat_panel(left_container)
        self._build_placeholder_panel(right_container)

    def _build_chat_panel(self, parent: ttk.Frame) -> None:
        # Outer card frame with subtle border effect
        chat_card = tk.Frame(
            parent,
            background=self.border_color,
            highlightthickness=0,
        )
        chat_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Inner content frame (creates border effect with padding)
        chat_frame = ttk.Frame(chat_card, style="Card.TFrame")
        chat_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        chat_frame.grid_rowconfigure(1, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        # Header section with darker background
        header_frame = ttk.Frame(chat_frame, style="Header.TFrame")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Header content with padding
        header_content = ttk.Frame(header_frame, style="Header.TFrame")
        header_content.pack(fill="x", padx=20, pady=18)
        
        # Title and status on same row
        title_row = ttk.Frame(header_content, style="Header.TFrame")
        title_row.pack(fill="x", anchor="w")
        
        title_label = ttk.Label(title_row, text="Agent chat", style="ChatTitle.TLabel")
        title_label.pack(side="left")
        
        # Status indicator badge
        self.status_badge = tk.Label(
            title_row,
            text="● Idle",
            font=("Segoe UI", 9, "bold"),
            foreground="#7c8a99",
            background=self.header_bg,
            padx=10,
            pady=2,
        )
        self.status_badge.pack(side="left", padx=(15, 0))
        
        subtitle_label = ttk.Label(
            header_content,
            text="Describe a workflow and I will learn it.",
            style="ChatSubtitle.TLabel"
        )
        subtitle_label.pack(anchor="w", pady=(4, 0))
        
        # Subtle bottom border for header
        header_border = tk.Frame(header_frame, height=1, background="#c5cdd6")
        header_border.pack(fill="x")

        # Messages container with improved styling
        messages_outer = ttk.Frame(chat_frame, style="Card.TFrame")
        messages_outer.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        messages_outer.grid_rowconfigure(0, weight=1)
        messages_outer.grid_columnconfigure(0, weight=1)

        self.chat_text = tk.Text(
            messages_outer,
            wrap="word",
            relief="flat",
            background=self.card_color,
            foreground=self.text_color,
            font=("Segoe UI", 11),
            borderwidth=0,
            highlightthickness=0,
            spacing1=3,
            spacing3=10,
            padx=14,
            pady=14,
        )
        self.chat_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            messages_outer,
            orient="vertical",
            command=self.chat_text.yview,
            style="Modern.Vertical.TScrollbar",
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        try:
            scrollbar["width"] = 10
        except Exception:
            pass
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        self.chat_text.configure(state="disabled")

        # Improved tag styling for different message types
        self.chat_text.tag_configure(
            "user_sender",
            foreground="#2f5d9f",
            font=("Segoe UI", 11, "bold"),
            lmargin1=20,
            lmargin2=20,
        )
        self.chat_text.tag_configure(
            "agent_sender",
            foreground="#1f2933",
            font=("Segoe UI", 11, "bold"),
            lmargin1=40,
            lmargin2=40,
        )
        self.chat_text.tag_configure(
            "system_sender",
            foreground="#52606d",
            font=("Segoe UI", 10, "italic")
        )
        self.chat_text.tag_configure(
            "user_message",
            foreground=self.text_color,
            font=("Segoe UI", 11),
            background=self.user_bubble_bg,
            lmargin1=20,
            lmargin2=20,
            rmargin=60,
            spacing1=6,
            spacing3=12,
        )
        self.chat_text.tag_configure(
            "agent_message",
            foreground="#3e4c59",
            font=("Segoe UI", 11),
            background=self.agent_bubble_bg,
            lmargin1=40,
            lmargin2=40,
            rmargin=20,
            spacing1=6,
            spacing3=12,
        )
        self.chat_text.tag_configure(
            "system_message",
            foreground="#616e7c",
            font=("Segoe UI", 10, "italic")
        )
        self.chat_text.tag_configure(
            "timestamp",
            foreground="#a7b0ba",
            font=("Segoe UI", 8)
        )
        self.chat_text.tag_configure(
            "success_icon",
            foreground="#10b981",
            font=("Segoe UI", 11, "bold")
        )
        self.chat_text.tag_configure(
            "warning_icon",
            foreground="#f59e0b",
            font=("Segoe UI", 11, "bold")
        )

        self._insert_initial_messages()

        # Input row with improved styling
        entry_row = ttk.Frame(chat_frame, style="Card.TFrame")
        entry_row.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        entry_row.grid_columnconfigure(0, weight=1)  # entry expands
        entry_row.grid_columnconfigure(1, weight=0)  # mic
        entry_row.grid_columnconfigure(2, weight=0)  # send

        self.message_var = tk.StringVar()
        
        # Track message var changes to update button state
        self.message_var.trace_add("write", lambda *args: self._update_send_button_state())
        
        # Custom styled entry with more height
        entry_style = ttk.Style()
        entry_style.configure("Custom.TEntry", padding=(10, 8))
        
        self.message_entry = ttk.Entry(
            entry_row,
            textvariable=self.message_var,
            font=("Segoe UI", 11),
            style="Custom.TEntry"
        )
        self.message_entry.grid(row=0, column=0, sticky="ew", ipady=4)
        self.message_entry.bind("<Return>", self._on_send)
        
        # Insert placeholder text
        self.message_entry.insert(0, "Type a command or describe a workflow...")
        self.message_entry.config(foreground="#9aa5b1")
        
        # Bind focus events for placeholder
        self.message_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.message_entry.bind("<FocusOut>", self._on_entry_focus_out)

        # Mic button with animation state tracking
        self.mic_listening = False
        self.mic_button = ttk.Button(
            entry_row,
            text="🎤",
            style="Ghost.TButton",
            command=self._on_mic_click,
            width=2,
        )
        self.mic_button.grid(row=0, column=1, padx=(10, 10))
        try:
            self.mic_button.configure(cursor="hand2")
        except Exception:
            pass

        send_button = ttk.Button(
            entry_row,
            text="Send",
            style="Accent.TButton",
            command=self._on_send
        )
        send_button.grid(row=0, column=2, padx=(0, 0))
        try:
            send_button.configure(cursor="hand2")
        except Exception:
            pass
        self.send_button = send_button

    def _build_placeholder_panel(self, parent: ttk.Frame) -> None:
        # Outer card frame with subtle border
        placeholder_card = tk.Frame(
            parent,
            background=self.border_color,
            highlightthickness=0,
        )
        placeholder_card.grid(row=0, column=0, sticky="nsew")

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Inner frame with tinted background
        placeholder_frame = ttk.Frame(placeholder_card, style="Card.TFrame")
        placeholder_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Configure grid for three sections
        placeholder_frame.grid_rowconfigure(0, weight=0)  # Controls (fixed)
        placeholder_frame.grid_rowconfigure(1, weight=1)  # Timeline (expands)
        placeholder_frame.grid_rowconfigure(2, weight=0)  # Status (fixed)
        placeholder_frame.grid_columnconfigure(0, weight=1)
        
        # Build three sections
        self._build_workflow_controls(placeholder_frame)
        self._build_workflow_timeline(placeholder_frame)
        self._build_workflow_status(placeholder_frame)
    
    def _build_workflow_controls(self, parent: ttk.Frame) -> None:
        """Build the top controls section with buttons."""
        controls_container = tk.Frame(parent, background="#fafcfe")
        controls_container.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        # Header
        header_label = tk.Label(
            controls_container,
            text="Workflow View",
            font=("Segoe UI", 14, "bold"),
            foreground=self.text_color,
            background="#fafcfe"
        )
        header_label.pack(anchor="w", pady=(0, 12))
        
        # Button row
        button_row = tk.Frame(controls_container, background="#fafcfe")
        button_row.pack(fill="x")
        
        self.record_btn = ttk.Button(
            button_row,
            text="🔴 Record Workflow",
            style="Accent.TButton",
            command=lambda: self._set_agent_state("recording")
        )
        self.record_btn.pack(side="left", padx=(0, 8))
        try:
            self.record_btn.configure(cursor="hand2")
        except Exception:
            pass
        
        self.stop_btn = ttk.Button(
            button_row,
            text="⏹ Stop Recording",
            style="Accent.TButton",
            command=lambda: self._set_agent_state("idle")
        )
        self.stop_btn.pack(side="left", padx=(0, 8))
        self.stop_btn.state(["disabled"])  # Disabled by default
        try:
            self.stop_btn.configure(cursor="hand2")
        except Exception:
            pass
        
        history_btn = ttk.Button(
            button_row,
            text="📋 View History",
            style="Accent.TButton",
            command=self._open_history_window
        )
        history_btn.pack(side="left")
        try:
            history_btn.configure(cursor="hand2")
        except Exception:
            pass
    
    def _build_workflow_timeline(self, parent: ttk.Frame) -> None:
        """Build the middle timeline section showing workflow steps."""
        # Outer card container
        timeline_outer = tk.Frame(
            parent,
            background=self.border_color,
            highlightthickness=0,
        )
        timeline_outer.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        # Inner card
        timeline_card = tk.Frame(timeline_outer, background="#fafcfe")
        timeline_card.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Card header
        timeline_header = tk.Frame(timeline_card, background="#e9ecf1", height=40)
        timeline_header.pack(fill="x", padx=12, pady=12)
        timeline_header.pack_propagate(False)
        
        timeline_title = tk.Label(
            timeline_header,
            text="Workflow Steps",
            font=("Segoe UI", 12, "bold"),
            foreground=self.text_color,
            background="#e9ecf1",
            anchor="w"
        )
        timeline_title.pack(fill="both", padx=12, pady=8)
        
        # Timeline content area
        timeline_content = tk.Frame(timeline_card, background="#fafcfe")
        timeline_content.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # Placeholder text
        self.timeline_label = tk.Label(
            timeline_content,
            text="No workflow selected or recorded yet.",
            font=("Segoe UI", 11),
            foreground="#7c8a99",
            background="#fafcfe",
            justify="center"
        )
        self.timeline_label.pack(expand=True)
    
    def _build_workflow_status(self, parent: ttk.Frame) -> None:
        """Build the bottom status section."""
        # Outer card container
        status_outer = tk.Frame(
            parent,
            background=self.border_color,
            highlightthickness=0,
        )
        status_outer.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        
        # Inner card
        status_card = tk.Frame(status_outer, background="#fafcfe")
        status_card.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Card header
        status_header = tk.Frame(status_card, background="#e9ecf1", height=35)
        status_header.pack(fill="x", padx=12, pady=12)
        status_header.pack_propagate(False)
        
        status_title = tk.Label(
            status_header,
            text="Status",
            font=("Segoe UI", 11, "bold"),
            foreground=self.text_color,
            background="#e9ecf1",
            anchor="w"
        )
        status_title.pack(fill="both", padx=12, pady=6)
        
        # Status content
        status_content = tk.Frame(status_card, background="#fafcfe")
        status_content.pack(fill="both", padx=12, pady=(0, 12))
        
        # Status fields
        status_info = tk.Frame(status_content, background="#fafcfe")
        status_info.pack(fill="x", pady=4)
        
        # Current workflow
        workflow_row = tk.Frame(status_info, background="#fafcfe")
        workflow_row.pack(fill="x", pady=3)
        
        tk.Label(
            workflow_row,
            text="Workflow:",
            font=("Segoe UI", 10, "bold"),
            foreground="#52606d",
            background="#fafcfe",
            width=12,
            anchor="w"
        ).pack(side="left")
        
        self.workflow_name_label = tk.Label(
            workflow_row,
            text="None",
            font=("Segoe UI", 10),
            foreground="#7c8a99",
            background="#fafcfe",
            anchor="w"
        )
        self.workflow_name_label.pack(side="left", fill="x")
        
        # Steps count
        steps_row = tk.Frame(status_info, background="#fafcfe")
        steps_row.pack(fill="x", pady=3)
        
        tk.Label(
            steps_row,
            text="Steps:",
            font=("Segoe UI", 10, "bold"),
            foreground="#52606d",
            background="#fafcfe",
            width=12,
            anchor="w"
        ).pack(side="left")
        
        self.steps_count_label = tk.Label(
            steps_row,
            text="0",
            font=("Segoe UI", 10),
            foreground="#7c8a99",
            background="#fafcfe",
            anchor="w"
        )
        self.steps_count_label.pack(side="left", fill="x")
        
        # Recording state
        state_row = tk.Frame(status_info, background="#fafcfe")
        state_row.pack(fill="x", pady=3)
        
        tk.Label(
            state_row,
            text="State:",
            font=("Segoe UI", 10, "bold"),
            foreground="#52606d",
            background="#fafcfe",
            width=12,
            anchor="w"
        ).pack(side="left")
        
        self.recording_state_label = tk.Label(
            state_row,
            text="Idle",
            font=("Segoe UI", 10),
            foreground="#7c8a99",
            background="#fafcfe",
            anchor="w"
        )
        self.recording_state_label.pack(side="left", fill="x")

    def _on_mic_click(self) -> None:
        """UI hook: delegate to start_voice_input without changing UI wiring."""
        self.start_voice_input()

    def start_voice_input(self) -> None:
        """Begin basic voice input: show listening, start non-blocking capture."""
        if sr is None:
            self._append_message("System", "Voice input not available. Install PyAudio.", "system")
            return
        # Start listening animation
        self._start_mic_animation()
        # Listening system message
        self._append_message("System", "🎤 Listening…", "system")
        # Spawn worker thread
        threading.Thread(target=self._run_voice_thread, daemon=True).start()
    
    def _start_mic_animation(self) -> None:
        """Animate mic button to show listening state."""
        self.mic_listening = True
        try:
            self.mic_button.state(["disabled"])
            # Store original style
            if not hasattr(self, '_mic_animation_count'):
                self._mic_animation_count = 0
            self._animate_mic_pulse()
        except Exception:
            pass
    
    def _animate_mic_pulse(self) -> None:
        """Pulse animation for mic button while listening."""
        if not self.mic_listening:
            return
        
        # Alternate between normal and active mic emoji
        emojis = ["🎤", "🔴"]
        self._mic_animation_count = getattr(self, '_mic_animation_count', 0)
        current_emoji = emojis[self._mic_animation_count % 2]
        
        try:
            self.mic_button.configure(text=current_emoji)
        except Exception:
            pass
        
        self._mic_animation_count += 1
        
        # Continue animation if still listening
        if self.mic_listening:
            self.after(400, self._animate_mic_pulse)
    
    def _stop_mic_animation(self) -> None:
        """Stop mic animation and restore button state."""
        self.mic_listening = False
        try:
            self.mic_button.configure(text="🎤")
            self.mic_button.state(["!disabled"])
        except Exception:
            pass

    def _run_voice_thread(self) -> None:
        """Capture ~5s of audio and transcribe (no auto-send)."""
        if sr is None:
            return
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, phrase_time_limit=5)
            # Try transcription
            try:
                text = recognizer.recognize_google(audio)
                # Populate entry, do not auto-send
                def _apply_text():
                    self.message_entry.config(foreground=self.text_color)
                    self.message_var.set(text)
                    # Stop animation and re-enable mic
                    self._stop_mic_animation()
                self.after(0, _apply_text)
            except Exception:
                # UnknownValueError / RequestError / others: generic user-friendly message
                def _err():
                    self._append_message("System", "Sorry, I couldn't transcribe the audio.", "system")
                    self._stop_mic_animation()
                self.after(0, _err)
        except Exception:
            def _fail():
                self._append_message("System", "Voice input not available. Install PyAudio.", "system")
                self._stop_mic_animation()
            self.after(0, _fail)

    def _insert_initial_messages(self) -> None:
        sample_messages = [
            ("System", "Welcome to the workflow agent. Ready to learn!", "system"),
            ("You", "Here is the latest process update.", "user"),
            ("Agent", "Thanks! I'll keep learning this workflow.", "agent"),
            ("You", "Let me know when you're ready for the next step.", "user"),
        ]
        for sender, message, msg_type in sample_messages:
            self._append_message(sender, message, msg_type)

    def _append_message(self, sender: str, message: str, msg_type: str = "user") -> None:
        """Append a message to the chat with proper styling.
        
        Args:
            sender: The sender label (e.g., 'You', 'Agent', 'System')
            message: The message text
            msg_type: Type of message ('user', 'agent', or 'system')
        """
        self.chat_text.configure(state="normal")
        
        # Add icon for system messages
        icon = ""
        if msg_type == "system":
            if "success" in message.lower() or "ready" in message.lower():
                icon = "✓ "
                self.chat_text.insert("end", icon, "success_icon")
            elif "warning" in message.lower() or "error" in message.lower():
                icon = "⚠ "
                self.chat_text.insert("end", icon, "warning_icon")
        
        # Insert sender with appropriate tag
        self.chat_text.insert("end", f"{sender}: ", f"{msg_type}_sender")
        
        # Insert message with appropriate tag
        self.chat_text.insert("end", f"{message}", f"{msg_type}_message")
        
        # Add timestamp
        timestamp = datetime.now().strftime("%I:%M %p")
        self.chat_text.insert("end", f"  {timestamp}", "timestamp")
        
        self.chat_text.insert("end", "\n\n")
        
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def _on_send(self, event: tk.Event | None = None) -> None:
        message = self.message_var.get().strip()
        
        # Ignore placeholder text
        if not message or message == "Type a command or describe a workflow...":
            return

        print(f"User sent: {message}")
        self._append_message("You", message, "user")
        self.message_var.set("")
        
        # Reset entry color
        self.message_entry.config(foreground=self.text_color)
        
        # Show typing indicator
        self._set_agent_state("executing")
        self._show_typing_indicator()

        fake_reply = "Got it, I will learn this workflow later."
        self.after(1500, lambda: self._finish_agent_reply(fake_reply))
    
    def _show_typing_indicator(self) -> None:
        """Show typing indicator animation."""
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", "Agent is typing", "system_message")
        self.chat_text.insert("end", "...", "timestamp")
        self.typing_indicator_mark = self.chat_text.index("end-1c linestart")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")
    
    def _finish_agent_reply(self, message: str) -> None:
        """Remove typing indicator and show actual message."""
        # Remove typing indicator
        self.chat_text.configure(state="normal")
        self.chat_text.delete(self.typing_indicator_mark, "end")
        self.chat_text.configure(state="disabled")
        
        # Add actual message
        self._append_message("Agent", message, "agent")
        self._set_agent_state("idle")
    
    def _on_entry_focus_in(self, event: tk.Event) -> None:
        """Handle entry field focus in - remove placeholder."""
        if self.message_var.get() == "Type a command or describe a workflow...":
            self.message_var.set("")
            self.message_entry.config(foreground=self.text_color)
    
    def _on_entry_focus_out(self, event: tk.Event) -> None:
        """Handle entry field focus out - restore placeholder if empty."""
        if not self.message_var.get().strip():
            self.message_var.set("Type a command or describe a workflow...")
            self.message_entry.config(foreground="#9aa5b1")
    
    def _update_send_button_state(self) -> None:
        """Enable/disable send button based on entry content."""
        # Guard during initial build before send_button exists
        if not hasattr(self, 'send_button'):
            return
        message = self.message_var.get().strip()
        if message and message != "Type a command or describe a workflow...":
            self.send_button.state(["!disabled"])
        else:
            self.send_button.state(["disabled"])
    
    def _set_agent_state(self, state: str) -> None:
        """Update agent state and status badge.
        
        Args:
            state: One of 'idle', 'recording', 'executing'
        """
        self.agent_state = state
        
        # Update badge
        state_config = {
            "idle": ("● Idle", "#7c8a99"),
            "recording": ("● Recording", "#ef4444"),
            "executing": ("● Executing", "#10b981"),
        }
        
        text, color = state_config.get(state, ("● Idle", "#7c8a99"))
        self.status_badge.config(text=text, foreground=color)
        
        # Update workflow status panel
        if hasattr(self, 'recording_state_label'):
            state_display = state.capitalize()
            self.recording_state_label.config(text=state_display)
        
        # Update button states
        if hasattr(self, 'record_btn') and hasattr(self, 'stop_btn'):
            if state == "recording":
                self.record_btn.state(["disabled"])
                self.stop_btn.state(["!disabled"])
            else:
                self.record_btn.state(["!disabled"])
                self.stop_btn.state(["disabled"])
        
        # Add system message
        if state == "recording":
            self._append_message("System", "Started recording workflow", "system")
        elif state == "idle" and hasattr(self, 'chat_text'):
            pass  # Don't spam idle messages
    
    def _open_history_window(self) -> None:
        """Open or bring to front the workflow history window."""
        # If window exists and is still open, bring to front
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.lift()
            self.history_window.focus_force()
        else:
            # Create new history window with theme colors
            theme_colors = {
                'bg_color': self.bg_color,
                'card_color': self.card_color,
                'header_bg': self.header_bg,
                'accent_color': self.accent_color,
                'text_color': self.text_color,
                'border_color': self.border_color,
            }
            self.history_window = WorkflowHistoryWindow(self, theme_colors)


if __name__ == "__main__":
    app = App()
    app.mainloop()
