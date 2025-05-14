# --- sys-botbase required ---
# Download the latest sys-botbase from: https://github.com/olliz0r/sys-botbase
# Install: Download latest release and extract into your Nintendo Switch SD card. Restart your switch.
#
# sys-botbase enables remote control of your Switch for this tool.

import sys
import subprocess
import importlib
import socket
import time
import os
import json

# --- Dependency auto-installer (for future non-stdlib deps) ---
def ensure_dependencies():
    # Tkinter is stdlib, but check for others here if needed
    missing = []
    try:
        import tkinter
    except ImportError:
        missing.append('tkinter')
    # Add more checks here if you add non-stdlib deps
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}. Please install Python 3.7+ with Tkinter support.")
        sys.exit(1)

ensure_dependencies()

# For distribution: create a .bat file with:
#   python macroBuilder.py
# Or use pythonw for no console window

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

BUTTONS = ["A","B","X","Y","L","R","ZL","ZR","PLUS","MINUS","HOME","CAPTURE","LSTICK","RSTICK"]
DPAD = [
    ("Up", "DUP"), ("Down", "DDOWN"), ("Left", "DLEFT"), ("Right", "DRIGHT"),
    ("Up-Left", "DUPLEFT"), ("Up-Right", "DUPRIGHT"), ("Down-Left", "DDOWNLEFT"), ("Down-Right", "DDOWNRIGHT")
]

CONFIG_FILE = "macrobuilder_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"switch_ip": "192.168.1.100", "switch_port": "6000", "auto_connect": False}

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        try:
            x, y = self.widget.winfo_rootx(), self.widget.winfo_rooty()
            x += 20
            y += 20
        except Exception:
            x, y = 0, 0
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class MacroBuilderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Macros-NX")
        self.geometry("1200x700")
        self.minsize(900, 500)
        self.macros = []
        self.selected_index = None
        self.switch_socket = None
        self.switch_connected = False
        self.config_data = load_config()
        self._build_ui()
        self._refresh_macro_list()
        # Auto-connect if enabled
        if self.config_data.get("auto_connect"):
            self.after(500, self._connect_switch)

    def _open_sysbotbase_link(self):
        import webbrowser
        webbrowser.open_new("https://github.com/olliz0r/sys-botbase")

    def _build_ui(self):
        # --- Tabbed interface ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        # How to Use Tab
        howto_tab = ttk.Frame(self.notebook)
        self.notebook.add(howto_tab, text="How to Use")
        self._build_howto_tab(howto_tab)
        # Macro Builder Tab
        macro_tab = ttk.Frame(self.notebook)
        self.notebook.add(macro_tab, text="Macro Builder")
        # Manual Controls Tab
        manual_tab = ttk.Frame(self.notebook)
        self.notebook.add(manual_tab, text="Manual Controls")
        # Build macro builder UI in macro_tab
        self._build_macro_tab(macro_tab)
        # Build manual controls UI in manual_tab
        self._build_manual_tab(manual_tab)

    def _build_howto_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        # --- Scrollable frame setup ---
        canvas = tk.Canvas(parent, borderwidth=0, highlightthickness=0)
        vscroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        frame = ttk.Frame(canvas)
        frame_id = canvas.create_window((0, 0), window=frame, anchor="nw")
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind("<Configure>", _on_frame_configure)
        def _on_canvas_configure(event):
            canvas.itemconfig(frame_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)
        # Title
        title = tk.Label(frame, text="How to Use Macro Builder", font=("TkDefaultFont", 16, "bold"), anchor="w")
        title.pack(anchor="w", pady=(0, 10))
        # sys-botbase section
        sysbot_title = tk.Label(frame, text="1. Install sys-botbase on your Switch", font=("TkDefaultFont", 12, "bold"), anchor="w")
        sysbot_title.pack(anchor="w", pady=(10, 2))
        sysbot_text = tk.Label(frame, text="This tool requires sys-botbase running on your Nintendo Switch.", anchor="w", justify="left", wraplength=700)
        sysbot_text.pack(anchor="w")
        link = tk.Label(frame, text="Get sys-botbase (GitHub)", fg="#0645AD", cursor="hand2", font=("TkDefaultFont", 11, "underline"), anchor="w")
        link.pack(anchor="w", pady=(0,2))
        link.bind("<Button-1>", lambda e: self._open_sysbotbase_link())
        install_steps = tk.Label(
            frame,
            text="""
Install steps:
  1. Download the latest release from the GitHub page above.
  2. Extract the files into your Nintendo Switch SD card.
  3. Restart your Switch.
  4. The home button should glow if sys-botbase is running.
            """,
            anchor="w", justify="left", wraplength=700
        )
        install_steps.pack(anchor="w")
        # Usage section
        usage_title = tk.Label(frame, text="2. Using Macro Builder", font=("TkDefaultFont", 12, "bold"), anchor="w")
        usage_title.pack(anchor="w", pady=(20, 2))
        usage_text = tk.Label(
            frame,
            text="""
- Use the Macro Builder tab to create, edit, and test macros.
- Use the Manual Controls tab to send individual button or stick commands.
- Import/export macros to share with friends.
- Make sure your Switch and PC are on the same network.
- Enter your Switch's IP and port (default 6000) in the connection panel.
- Click 'Connect' to start sending commands.
            """,
            anchor="w", justify="left", wraplength=700
        )
        usage_text.pack(anchor="w")
        # Stick controls section
        stick_title = tk.Label(frame, text="3. Stick Controls Format", font=("TkDefaultFont", 12, "bold"), anchor="w")
        stick_title.pack(anchor="w", pady=(20, 2))
        stick_text = tk.Label(
            frame,
            text="""
- %x,y = Left stick (e.g. %0,32767 is up)
- &x,y = Right stick (e.g. &32767,0 is right)
- Y = +32767 is up, -32767 is down (not inverted)
- Center is %0,0 or &0,0
            """,
            anchor="w", justify="left", wraplength=700
        )
        stick_text.pack(anchor="w")
        # Troubleshooting
        trouble_title = tk.Label(frame, text="4. Troubleshooting", font=("TkDefaultFont", 12, "bold"), anchor="w")
        trouble_title.pack(anchor="w", pady=(20, 2))
        trouble_text = tk.Label(
            frame,
            text="""
- If nothing happens, check your Switch IP, sys-botbase status, and network connection.
- Make sure sys-botbase is running (home button glows).
- Try restarting your Switch and PC if you have issues.
            """,
            anchor="w", justify="left", wraplength=700
        )
        trouble_text.pack(anchor="w")

    def _build_macro_tab(self, parent):
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)
        left = ttk.Frame(parent)
        left.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        right = ttk.Frame(parent)
        right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(6, weight=1)  # Steps listbox
        right.rowconfigure(15, weight=2) # Interpreted preview
        # --- Switch Connection Panel (shared) ---
        conn_frame = ttk.LabelFrame(left, text="Switch Connection")
        conn_frame.pack(fill=tk.X, pady=(0,10))
        ttk.Label(conn_frame, text="Switch IP:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.switch_ip_var = tk.StringVar(value=self.config_data.get("switch_ip", "192.168.1.100"))
        ip_entry = ttk.Entry(conn_frame, textvariable=self.switch_ip_var, width=15)
        ip_entry.grid(row=0, column=1, padx=2, pady=2)
        Tooltip(ip_entry, "IP address of your Nintendo Switch running sys-botbase.")
        self.switch_ip_var.trace_add("write", self._on_switch_ip_change)
        ttk.Label(conn_frame, text="Port:").grid(row=1, column=0, sticky="w", padx=2, pady=2)
        self.switch_port_var = tk.StringVar(value=self.config_data.get("switch_port", "6000"))
        port_entry = ttk.Entry(conn_frame, textvariable=self.switch_port_var, width=7)
        port_entry.grid(row=1, column=1, padx=2, pady=2)
        Tooltip(port_entry, "Port for sys-botbase (default: 6000)")
        self.switch_port_var.trace_add("write", self._on_switch_port_change)
        self.conn_status_var = tk.StringVar(value="Disconnected")
        self.conn_status_label = ttk.Label(conn_frame, textvariable=self.conn_status_var, foreground="#a00")
        self.conn_status_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=2, pady=2)
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self._connect_switch)
        self.connect_btn.grid(row=3, column=0, padx=2, pady=2)
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self._disconnect_switch, state="disabled")
        self.disconnect_btn.grid(row=3, column=1, padx=2, pady=2)
        Tooltip(self.connect_btn, "Connect to your Switch (sys-botbase must be running)")
        Tooltip(self.disconnect_btn, "Disconnect from Switch")
        # Auto-connect checkbox
        self.auto_connect_var = tk.BooleanVar(value=self.config_data.get("auto_connect", False))
        auto_chk = ttk.Checkbutton(conn_frame, text="Auto-connect on startup", variable=self.auto_connect_var, command=self._on_auto_connect_change)
        auto_chk.grid(row=4, column=0, columnspan=2, sticky="w", padx=2, pady=2)
        # Macro list
        self.macro_listbox = tk.Listbox(left, width=22)
        macro_scroll = ttk.Scrollbar(left, orient="vertical", command=self.macro_listbox.yview)
        self.macro_listbox.config(yscrollcommand=macro_scroll.set)
        self.macro_listbox.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        macro_scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.macro_listbox.bind('<<ListboxSelect>>', self._on_select)
        ttk.Button(left, text="New Macro", command=self._new_macro).pack(fill=tk.X, pady=2)
        Tooltip(self.macro_listbox, "Select a macro to edit. Use New, Delete, Clone, Move Up/Down, Export, Import.")
        ttk.Button(left, text="Delete Macro", command=self._delete_macro).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Move Up", command=self._move_up).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Move Down", command=self._move_down).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Clone Macro", command=self._clone_macro).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Export Macro(s)", command=self._export_macros).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Import Macro(s)", command=self._import_macros).pack(fill=tk.X, pady=2)
        # Macro details
        row = 0
        # --- Macro Name (label+entry side by side) ---
        name_frame = ttk.Frame(right)
        name_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(name_frame, text="Macro Name:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=30)
        name_entry.pack(side=tk.LEFT, padx=(5,0))
        Tooltip(name_entry, "Name for this macro (for your reference)")
        row += 1
        # --- Trigger (label+entry side by side) ---
        trigger_frame = ttk.Frame(right)
        trigger_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(trigger_frame, text="Trigger (chat command):").pack(side=tk.LEFT)
        self.trigger_var = tk.StringVar()
        trigger_entry = ttk.Entry(trigger_frame, textvariable=self.trigger_var, width=20)
        trigger_entry.pack(side=tk.LEFT, padx=(5,0))
        Tooltip(trigger_entry, "What chat command triggers this macro? (e.g. !jump)")
        row += 1
        ttk.Label(right, text="Steps:").grid(row=row, column=0, sticky="w", pady=(10,0))
        row += 1
        self.steps_listbox = tk.Listbox(right, height=7)
        steps_scroll = ttk.Scrollbar(right, orient="vertical", command=self.steps_listbox.yview)
        self.steps_listbox.config(yscrollcommand=steps_scroll.set)
        self.steps_listbox.grid(row=row, column=0, columnspan=2, sticky="nsew")
        steps_scroll.grid(row=row, column=2, sticky="ns")
        self.steps_listbox.bind('<<ListboxSelect>>', self._on_step_select)
        self.steps_listbox.bind('<Button-1>', self._on_step_drag_start)
        self.steps_listbox.bind('<B1-Motion>', self._on_step_drag_motion)
        self.steps_listbox.bind('<ButtonRelease-1>', self._on_step_drag_drop)
        self.steps_listbox.bind('<Double-Button-1>', self._on_step_inline_edit)
        row += 1
        step_btns = ttk.Frame(right)
        step_btns.grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
        ttk.Button(step_btns, text="Up", command=self._move_step_up).pack(side=tk.LEFT, padx=1)
        ttk.Button(step_btns, text="Down", command=self._move_step_down).pack(side=tk.LEFT, padx=1)
        ttk.Button(step_btns, text="Edit", command=self._edit_step).pack(side=tk.LEFT, padx=1)
        ttk.Button(step_btns, text="Delete", command=self._delete_step).pack(side=tk.LEFT, padx=1)
        row += 1
        ttk.Label(right, text="Add Step:").grid(row=row, column=0, sticky="w", pady=(10,0))
        row += 1
        step_type_frame = ttk.LabelFrame(right, text="Step Type")
        step_type_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(5,0))
        self.step_type_var = tk.StringVar(value="Button")
        for t in ["Button","Hold","Release","Stick Move","Wait"]:
            ttk.Radiobutton(step_type_frame, text=t, variable=self.step_type_var, value=t, command=self._update_step_type_panel).pack(side=tk.LEFT, padx=2)
        row += 1
        self.step_type_panel = ttk.Frame(right)
        self.step_type_panel.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(2,0))
        self._build_step_type_panel()
        row += 1
        ttk.Button(right, text="Add Step", command=self._add_step).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        ttk.Button(right, text="Save Macro", command=self._save_macro).grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        # --- Test Macro Button ---
        self.test_status_var = tk.StringVar(value="")
        test_btn = ttk.Button(right, text="Run Macro on Switch", command=self._test_macro)
        test_btn.grid(row=row, column=0, columnspan=2, pady=5)
        Tooltip(test_btn, "Send the selected macro to your Switch and run it live!")
        row += 1
        test_status_label = ttk.Label(right, textvariable=self.test_status_var, foreground="#007700")
        test_status_label.grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        ttk.Label(right, text="Preview (raw):").grid(row=row, column=0, sticky="w")
        row += 1
        self.preview = tk.Text(right, height=3, state=tk.DISABLED, wrap="word")
        self.preview.grid(row=row, column=0, columnspan=2, sticky="nsew")
        right.rowconfigure(row, weight=1)
        row += 1
        ttk.Label(right, text="Preview (interpreted):").grid(row=row, column=0, sticky="w")
        row += 1
        self.interp_preview = tk.Text(right, height=5, state=tk.DISABLED, wrap="word", foreground="#007700")
        self.interp_preview.grid(row=row, column=0, columnspan=2, sticky="nsew")
        right.rowconfigure(row, weight=2)

    def _refresh_macro_list(self):
        self.macro_listbox.delete(0, tk.END)
        for m in self.macros:
            self.macro_listbox.insert(tk.END, m.get('name', ''))
        if self.selected_index is not None and 0 <= self.selected_index < len(self.macros):
            self.macro_listbox.select_set(self.selected_index)
            self.macro_listbox.event_generate('<<ListboxSelect>>')
        else:
            self._new_macro()

    def _on_select(self, event):
        idxs = self.macro_listbox.curselection()
        if not idxs:
            self.selected_index = None
            return
        idx = idxs[0]
        macro = self.macros[idx]
        self.selected_index = idx
        self.name_var.set(macro.get('name', ''))
        self.trigger_var.set(macro.get('trigger', '') or macro.get('chat_command', ''))
        steps = macro.get('steps', [])
        self._set_steps(steps)
        self._update_preview()

    def _set_steps(self, steps):
        self.steps_listbox.delete(0, tk.END)
        for s in steps:
            self.steps_listbox.insert(tk.END, s)

    def _get_steps(self):
        return [self.steps_listbox.get(i) for i in range(self.steps_listbox.size())]

    def _on_step_select(self, event):
        pass

    def _insert_step(self, step):
        if not step:
            return
        idxs = self.steps_listbox.curselection()
        idx = idxs[0] if idxs else self.steps_listbox.size()
        self.steps_listbox.insert(idx, step)
        self._update_preview()

    def _move_step_up(self):
        idxs = self.steps_listbox.curselection()
        if not idxs or idxs[0] == 0:
            return
        idx = idxs[0]
        step = self.steps_listbox.get(idx)
        self.steps_listbox.delete(idx)
        self.steps_listbox.insert(idx-1, step)
        self.steps_listbox.select_set(idx-1)
        self._update_preview()

    def _move_step_down(self):
        idxs = self.steps_listbox.curselection()
        if not idxs or idxs[0] == self.steps_listbox.size()-1:
            return
        idx = idxs[0]
        step = self.steps_listbox.get(idx)
        self.steps_listbox.delete(idx)
        self.steps_listbox.insert(idx+1, step)
        self.steps_listbox.select_set(idx+1)
        self._update_preview()

    def _edit_step(self):
        idxs = self.steps_listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        old = self.steps_listbox.get(idx)
        new = simpledialog.askstring("Edit Step", f"Edit step:", initialvalue=old)
        if new:
            self.steps_listbox.delete(idx)
            self.steps_listbox.insert(idx, new)
            self.steps_listbox.select_set(idx)
            self._update_preview()

    def _delete_step(self):
        idxs = self.steps_listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        self.steps_listbox.delete(idx)
        self._update_preview()

    def _new_macro(self):
        self.selected_index = None
        self.name_var.set("")
        self.trigger_var.set("")
        self._set_steps([])
        self.macro_listbox.selection_clear(0, tk.END)
        self._update_preview()

    def _delete_macro(self):
        idxs = self.macro_listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        del self.macros[idx]
        self.selected_index = None
        self._refresh_macro_list()

    def _move_up(self):
        if self.selected_index is not None and self.selected_index > 0:
            self.macros[self.selected_index-1], self.macros[self.selected_index] = self.macros[self.selected_index], self.macros[self.selected_index-1]
            self.selected_index -= 1
            self._refresh_macro_list()

    def _move_down(self):
        if self.selected_index is not None and self.selected_index < len(self.macros)-1:
            self.macros[self.selected_index+1], self.macros[self.selected_index] = self.macros[self.selected_index], self.macros[self.selected_index+1]
            self.selected_index += 1
            self._refresh_macro_list()

    def _clone_macro(self):
        if self.selected_index is not None:
            macro = self.macros[self.selected_index].copy()
            macro['name'] += " (Copy)"
            self.macros.insert(self.selected_index+1, macro)
            self.selected_index += 1
            self._refresh_macro_list()

    def _export_macros(self):
        if not self.macros:
            messagebox.showinfo("Export", "No macros to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not path:
            return
        try:
            # Export with 'chat_command' as alias for 'trigger'
            export_macros = []
            for m in self.macros:
                macro = m.copy()
                macro['chat_command'] = macro.get('trigger', '')
                export_macros.append(macro)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(export_macros, f, indent=2)
            messagebox.showinfo("Export", f"Exported {len(self.macros)} macros to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _import_macros(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                raise ValueError("Invalid macro file format.")
            # Accept both 'trigger' and 'chat_command' fields
            for m in data:
                if 'chat_command' in m and 'trigger' not in m:
                    m['trigger'] = m['chat_command']
            self.macros.extend(data)
            self._refresh_macro_list()
            messagebox.showinfo("Import", f"Imported {len(data)} macros from {path}")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _save_macro(self):
        name = self.name_var.get().strip()
        trigger = self.trigger_var.get().strip()
        steps = self._get_steps()
        if not name:
            messagebox.showerror("Error", "Macro name is required.")
            return
        if not trigger:
            messagebox.showerror("Error", "Trigger is required.")
            return
        if not steps:
            messagebox.showerror("Error", "At least one step is required.")
            return
        macro = {'name': name, 'trigger': trigger, 'chat_command': trigger, 'steps': steps}
        if self.selected_index is not None and 0 <= self.selected_index < len(self.macros):
            self.macros[self.selected_index] = macro
        else:
            self.macros.append(macro)
            self.selected_index = len(self.macros)-1
        self._refresh_macro_list()
        messagebox.showinfo("Saved", f"Macro '{name}' saved.")

    def _update_preview(self):
        steps = self._get_steps()
        raw = ','.join(steps)
        interp = '\n'.join(self._interpret_step(s) for s in steps)
        self.preview.config(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        self.preview.insert(tk.END, raw)
        self.preview.config(state=tk.DISABLED)
        self.interp_preview.config(state=tk.NORMAL)
        self.interp_preview.delete(1.0, tk.END)
        self.interp_preview.insert(tk.END, interp)
        self.interp_preview.config(state=tk.DISABLED)

    def _interpret_step(self, step):
        # Simple interpretation for user-friendliness
        if step.startswith("Button:"):
            return f"Press {step[7:]}"
        if step.startswith("Hold:"):
            return f"Hold {step[5:]}"
        if step.startswith("Release:"):
            return f"Release {step[8:]}"
        if step.startswith("Stick:"):
            return f"Move stick to {step[6:]}"
        if step.startswith("Wait:"):
            return f"Wait {step[5:]} ms"
        return step

    def _build_step_type_panel(self):
        for w in self.step_type_panel.winfo_children():
            w.destroy()
        t = self.step_type_var.get()
        if t == "Button":
            ttk.Label(self.step_type_panel, text="Button:").pack(side=tk.LEFT)
            self.button_var = tk.StringVar(value=BUTTONS[0])
            btn_menu = ttk.Combobox(self.step_type_panel, textvariable=self.button_var, values=BUTTONS, state="readonly", width=8)
            btn_menu.pack(side=tk.LEFT, padx=2)
            Tooltip(btn_menu, "Which button to press?")
        elif t == "Hold":
            ttk.Label(self.step_type_panel, text="Hold:").pack(side=tk.LEFT)
            self.hold_var = tk.StringVar(value=BUTTONS[0])
            hold_menu = ttk.Combobox(self.step_type_panel, textvariable=self.hold_var, values=BUTTONS, state="readonly", width=8)
            hold_menu.pack(side=tk.LEFT, padx=2)
            Tooltip(hold_menu, "Which button to hold?")
        elif t == "Release":
            ttk.Label(self.step_type_panel, text="Release:").pack(side=tk.LEFT)
            self.release_var = tk.StringVar(value=BUTTONS[0])
            release_menu = ttk.Combobox(self.step_type_panel, textvariable=self.release_var, values=BUTTONS, state="readonly", width=8)
            release_menu.pack(side=tk.LEFT, padx=2)
            Tooltip(release_menu, "Which button to release?")
        elif t == "Stick Move":
            # Stick side selector
            self.stick_side_var = tk.StringVar(value="LEFT")
            ttk.Label(self.step_type_panel, text="Stick:").pack(side=tk.LEFT)
            stick_side_menu = ttk.Combobox(self.step_type_panel, textvariable=self.stick_side_var, values=["LEFT", "RIGHT"], state="readonly", width=6)
            stick_side_menu.pack(side=tk.LEFT, padx=2)
            Tooltip(stick_side_menu, "Which stick to move?")
            # --- Stick grid ---
            grid_frame = ttk.Frame(self.step_type_panel)
            grid_frame.pack(side=tk.LEFT, padx=2)
            ttk.Label(grid_frame, text="Stick Direction:").pack(anchor=tk.W)
            self.stick_canvas = tk.Canvas(grid_frame, width=140, height=140, bg="#f8f8f8", highlightthickness=1, relief=tk.SOLID)
            self.stick_canvas.pack()
            self.stick_canvas.bind("<Button-1>", self._on_stick_grid_click)
            Tooltip(self.stick_canvas, "Click to set stick direction. Center = release.")
            for i in range(1, 7):
                self.stick_canvas.create_line(i*20, 0, i*20, 140, fill="#ccc")
                self.stick_canvas.create_line(0, i*20, 140, i*20, fill="#ccc")
            self.stick_x = 0
            self.stick_y = 0
            self._update_stick_grid_dot()
            release_btn = ttk.Button(grid_frame, text="Stick Release (Center)", command=self._add_stick_release)
            release_btn.pack(pady=2)
            Tooltip(release_btn, "Add a stick release (center) step.")
            help_lbl = ttk.Label(grid_frame, text="Click grid to set stick direction. Center = release.", foreground="#888", font=("TkDefaultFont", 8))
            help_lbl.pack()
        elif t == "Wait":
            ttk.Label(self.step_type_panel, text="Wait (ms):").pack(side=tk.LEFT)
            self.wait_var = tk.StringVar(value="100")
            wait_entry = ttk.Entry(self.step_type_panel, textvariable=self.wait_var, width=8)
            wait_entry.pack(side=tk.LEFT, padx=2)
            Tooltip(wait_entry, "How many milliseconds to wait?")

    def _update_step_type_panel(self):
        self._build_step_type_panel()

    def _add_step(self):
        t = self.step_type_var.get()
        if t == "Button":
            step = f"Button:{self.button_var.get()}"
        elif t == "Hold":
            step = f"Hold:{self.hold_var.get()}"
        elif t == "Release":
            step = f"Release:{self.release_var.get()}"
        elif t == "Stick Move":
            side = self.stick_side_var.get()
            if side == "LEFT":
                step = f"%{self.stick_x},{self.stick_y}"
            else:
                step = f"&{self.stick_x},{self.stick_y}"
        elif t == "Wait":
            try:
                ms = int(self.wait_var.get())
                if ms < 1:
                    raise ValueError
                step = f"Wait:{ms}"
            except Exception:
                messagebox.showerror("Error", "Wait time must be a positive integer (ms)")
                return
        else:
            return
        self._insert_step(step)

    # Drag-and-drop for steps
    def _on_step_drag_start(self, event):
        self._drag_data = {'idx': self.steps_listbox.nearest(event.y)}
    def _on_step_drag_motion(self, event):
        idx = self.steps_listbox.nearest(event.y)
        if hasattr(self, '_drag_data') and idx != self._drag_data['idx']:
            step = self.steps_listbox.get(self._drag_data['idx'])
            self.steps_listbox.delete(self._drag_data['idx'])
            self.steps_listbox.insert(idx, step)
            self.steps_listbox.select_set(idx)
            self._drag_data['idx'] = idx
            self._update_preview()
    def _on_step_drag_drop(self, event):
        self._drag_data = None
    def _on_step_inline_edit(self, event):
        idx = self.steps_listbox.nearest(event.y)
        if idx < 0 or idx >= self.steps_listbox.size():
            return
        old = self.steps_listbox.get(idx)
        new = simpledialog.askstring("Edit Step", f"Edit step:", initialvalue=old)
        if new:
            self.steps_listbox.delete(idx)
            self.steps_listbox.insert(idx, new)
            self.steps_listbox.select_set(idx)
            self._update_preview()

    def _on_stick_grid_click(self, event):
        # Map click to stick range (-32767 to 32767), with Y axis inverted (top=up)
        x = int((event.x / 140) * 2 * 32767 - 32767)
        y = int((1 - event.y / 140) * 2 * 32767 - 32767)
        self.stick_x = max(-32767, min(32767, x))
        self.stick_y = max(-32767, min(32767, y))
        self._update_stick_grid_dot()
    def _update_stick_grid_dot(self):
        if hasattr(self, 'stick_canvas'):
            self.stick_canvas.delete("dot")
            # Convert stick_x/y to canvas coords
            cx = int((self.stick_x + 32767) / (2*32767) * 140)
            cy = int((self.stick_y + 32767) / (2*32767) * 140)
            self.stick_canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill="#0077cc", outline="#003366", tags="dot")
    def _add_stick_release(self):
        # Add a stick release step for the selected stick
        side = getattr(self, 'stick_side_var', None)
        if side is not None and side.get() == "RIGHT":
            self.stick_x = 0
            self.stick_y = 0
            self._update_stick_grid_dot()
            self._insert_step("&0,0")
        else:
            self.stick_x = 0
            self.stick_y = 0
            self._update_stick_grid_dot()
            self._insert_step("%0,0")

    # --- Switch Connection Logic ---
    def _connect_switch(self):
        ip = self.switch_ip_var.get().strip()
        try:
            port = int(self.switch_port_var.get().strip())
        except Exception:
            self.conn_status_var.set("Invalid port")
            self.conn_status_label.config(foreground="#a00")
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((ip, port))
            self.switch_socket = s
            self.switch_connected = True
            self.conn_status_var.set(f"Connected to {ip}:{port}")
            self.conn_status_label.config(foreground="#070")
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
        except Exception as e:
            self.conn_status_var.set(f"Failed: {e}")
            self.conn_status_label.config(foreground="#a00")
            self.switch_socket = None
            self.switch_connected = False
    def _disconnect_switch(self):
        if self.switch_socket:
            try:
                self.switch_socket.close()
            except Exception:
                pass
        self.switch_socket = None
        self.switch_connected = False
        self.conn_status_var.set("Disconnected")
        self.conn_status_label.config(foreground="#a00")
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")

    # --- Macro Test Logic ---
    def _test_macro(self):
        if not self.switch_connected or not self.switch_socket:
            self.test_status_var.set("Not connected to Switch!")
            return
        idxs = self.macro_listbox.curselection()
        if not idxs:
            self.test_status_var.set("No macro selected.")
            return
        macro = self.macros[idxs[0]]
        steps = macro.get('steps', [])
        if not steps:
            self.test_status_var.set("Macro has no steps.")
            return
        try:
            i = 0
            while i < len(steps):
                step = steps[i]
                # --- Button tap (Button:X) ---
                if step.startswith("Button:"):
                    btn = step[7:].upper()
                    next_is_wait = (i+1 < len(steps)) and steps[i+1].startswith("Wait:")
                    if next_is_wait:
                        # For Button:X + Wait, treat as press, wait, release (for compatibility)
                        self._send_sysbot_cmd(f"press {btn}")
                        ms = int(steps[i+1][5:])
                        time.sleep(ms/1000)
                        self._send_sysbot_cmd(f"release {btn}")
                        i += 2
                        continue
                    else:
                        # Normal tap: click (press and release)
                        self._send_sysbot_cmd(f"click {btn}")
                        time.sleep(0.1)
                # --- Hold:X ---
                elif step.startswith("Hold:"):
                    btn = step[5:].upper()
                    self._send_sysbot_cmd(f"press {btn}")
                # --- Release:X ---
                elif step.startswith("Release:"):
                    btn = step[8:].upper()
                    self._send_sysbot_cmd(f"release {btn}")
                # --- Stick moves ---
                elif step.startswith("%"):
                    xy = step[1:].split(",")
                    if len(xy) == 2:
                        x, y = int(xy[0]), int(xy[1])
                        self._send_sysbot_cmd(f"setStick LEFT {x} {y}")
                        time.sleep(0.1)
                elif step.startswith("&"):
                    xy = step[1:].split(",")
                    if len(xy) == 2:
                        x, y = int(xy[0]), int(xy[1])
                        self._send_sysbot_cmd(f"setStick RIGHT {x} {y}")
                        time.sleep(0.1)
                elif step.startswith("Stick:"):
                    # Backward compatibility: treat as left stick
                    xy = step[6:].split(",")
                    if len(xy) == 2:
                        x, y = int(xy[0]), int(xy[1])
                        self._send_sysbot_cmd(f"setStick LEFT {x} {y}")
                        time.sleep(0.1)
                # --- Wait ---
                elif step.startswith("Wait:"):
                    ms = int(step[5:])
                    time.sleep(ms/1000)
                i += 1
            self.test_status_var.set("Macro sent!")
        except Exception as e:
            self.test_status_var.set(f"Error: {e}")

    def _send_sysbot_cmd(self, cmd):
        if not self.switch_socket:
            raise RuntimeError("Not connected")
        # sys-botbase expects ASCII + newline
        self.switch_socket.sendall((cmd+"\n").encode("ascii"))

    def _build_manual_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        # Button controls
        btn_frame = ttk.LabelFrame(parent, text="Buttons")
        btn_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        btn_frame.columnconfigure(tuple(range(7)), weight=1)
        col = 0
        for i, btn in enumerate(BUTTONS):
            b = ttk.Button(btn_frame, text=btn, width=7)
            b.grid(row=i//7, column=col, padx=2, pady=2)
            b.bind('<ButtonPress-1>', lambda e, b=btn: self._manual_click_button(b))
            Tooltip(b, f"Click {btn} to send a button press to Switch.")
            col += 1
            if col >= 7:
                col = 0
        # D-Pad controls
        dpad_frame = ttk.LabelFrame(parent, text="D-Pad")
        dpad_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        dpad_frame.columnconfigure(tuple(range(4)), weight=1)
        for i, (label, dpad) in enumerate(DPAD):
            b = ttk.Button(dpad_frame, text=label, width=10)
            b.grid(row=i//4, column=i%4, padx=2, pady=2)
            b.bind('<ButtonPress-1>', lambda e, d=dpad: self._manual_click_button(d))
            Tooltip(b, f"Click D-Pad {label} to send a press to Switch.")
        # Stick controls (left and right)
        stick_frame = ttk.LabelFrame(parent, text="Stick (Left/Right)")
        stick_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        stick_frame.columnconfigure(0, weight=1)
        stick_frame.columnconfigure(1, weight=1)
        # Left stick
        ttk.Label(stick_frame, text="Left Stick:").pack(anchor=tk.W)
        self.manual_stick_canvas_left = tk.Canvas(stick_frame, width=140, height=140, bg="#f8f8f8", highlightthickness=1, relief=tk.SOLID)
        self.manual_stick_canvas_left.pack(side=tk.LEFT, padx=5, pady=5)
        self.manual_stick_canvas_left.bind("<Button-1>", lambda e: self._manual_stick_grid_click(e, "LEFT"))
        Tooltip(self.manual_stick_canvas_left, "Click to send left stick position. Center = release.")
        for i in range(1, 7):
            self.manual_stick_canvas_left.create_line(i*20, 0, i*20, 140, fill="#ccc")
            self.manual_stick_canvas_left.create_line(0, i*20, 140, i*20, fill="#ccc")
        self.manual_stick_x_left = 0
        self.manual_stick_y_left = 0
        self._manual_update_stick_grid_dot("LEFT")
        release_btn_left = ttk.Button(stick_frame, text="Left Stick Release (Center)", command=lambda: self._manual_stick_release("LEFT"))
        release_btn_left.pack(pady=2)
        Tooltip(release_btn_left, "Send left stick release (center) to Switch")
        # Right stick
        ttk.Label(stick_frame, text="Right Stick:").pack(anchor=tk.W)
        self.manual_stick_canvas_right = tk.Canvas(stick_frame, width=140, height=140, bg="#f8f8f8", highlightthickness=1, relief=tk.SOLID)
        self.manual_stick_canvas_right.pack(side=tk.LEFT, padx=5, pady=5)
        self.manual_stick_canvas_right.bind("<Button-1>", lambda e: self._manual_stick_grid_click(e, "RIGHT"))
        Tooltip(self.manual_stick_canvas_right, "Click to send right stick position. Center = release.")
        for i in range(1, 7):
            self.manual_stick_canvas_right.create_line(i*20, 0, i*20, 140, fill="#ccc")
            self.manual_stick_canvas_right.create_line(0, i*20, 140, i*20, fill="#ccc")
        self.manual_stick_x_right = 0
        self.manual_stick_y_right = 0
        self._manual_update_stick_grid_dot("RIGHT")
        release_btn_right = ttk.Button(stick_frame, text="Right Stick Release (Center)", command=lambda: self._manual_stick_release("RIGHT"))
        release_btn_right.pack(pady=2)
        Tooltip(release_btn_right, "Send right stick release (center) to Switch")
        # Status label
        self.manual_status_var = tk.StringVar(value="")
        status_label = ttk.Label(parent, textvariable=self.manual_status_var, foreground="#007700")
        status_label.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

    # --- Manual Controls: Click (main.py style) ---
    def _manual_click_button(self, btn):
        if not self.switch_connected or not self.switch_socket:
            self.manual_status_var.set("Not connected to Switch!")
            return
        try:
            # Manual controls always use click (tap)
            self._send_sysbot_cmd(f"click {btn}")
            self.manual_status_var.set(f"Clicked: {btn}")
        except Exception as e:
            self.manual_status_var.set(f"Error: {e}")

    def _manual_stick_grid_click(self, event, side):
        x = int((event.x / 140) * 2 * 32767 - 32767)
        y = int((1 - event.y / 140) * 2 * 32767 - 32767)
        if side == "LEFT":
            self.manual_stick_x_left = max(-32767, min(32767, x))
            self.manual_stick_y_left = max(-32767, min(32767, y))
            self._manual_update_stick_grid_dot("LEFT")
        else:
            self.manual_stick_x_right = max(-32767, min(32767, x))
            self.manual_stick_y_right = max(-32767, min(32767, y))
            self._manual_update_stick_grid_dot("RIGHT")
        if not self.switch_connected or not self.switch_socket:
            self.manual_status_var.set("Not connected to Switch!")
            return
        try:
            if side == "LEFT":
                self._send_sysbot_cmd(f"setStick LEFT {self.manual_stick_x_left} {self.manual_stick_y_left}")
                self.manual_status_var.set(f"Sent left stick: {self.manual_stick_x_left},{self.manual_stick_y_left}")
            else:
                self._send_sysbot_cmd(f"setStick RIGHT {self.manual_stick_x_right} {self.manual_stick_y_right}")
                self.manual_status_var.set(f"Sent right stick: {self.manual_stick_x_right},{self.manual_stick_y_right}")
        except Exception as e:
            self.manual_status_var.set(f"Error: {e}")

    def _manual_update_stick_grid_dot(self, side):
        if side == "LEFT" and hasattr(self, 'manual_stick_canvas_left'):
            self.manual_stick_canvas_left.delete("dot")
            cx = int((self.manual_stick_x_left + 32767) / (2*32767) * 140)
            # Invert Y for visual: top is up
            cy = int((32767 - self.manual_stick_y_left) / (2*32767) * 140)
            self.manual_stick_canvas_left.create_oval(cx-6, cy-6, cx+6, cy+6, fill="#0077cc", outline="#003366", tags="dot")
        elif side == "RIGHT" and hasattr(self, 'manual_stick_canvas_right'):
            self.manual_stick_canvas_right.delete("dot")
            cx = int((self.manual_stick_x_right + 32767) / (2*32767) * 140)
            # Invert Y for visual: top is up
            cy = int((32767 - self.manual_stick_y_right) / (2*32767) * 140)
            self.manual_stick_canvas_right.create_oval(cx-6, cy-6, cx+6, cy+6, fill="#0077cc", outline="#003366", tags="dot")

    def _manual_stick_release(self, side):
        if side == "LEFT":
            self.manual_stick_x_left = 0
            self.manual_stick_y_left = 0
            self._manual_update_stick_grid_dot("LEFT")
        else:
            self.manual_stick_x_right = 0
            self.manual_stick_y_right = 0
            self._manual_update_stick_grid_dot("RIGHT")
        if not self.switch_connected or not self.switch_socket:
            self.manual_status_var.set("Not connected to Switch!")
            return
        try:
            if side == "LEFT":
                self._send_sysbot_cmd("setStick LEFT 0 0")
                self.manual_status_var.set("Sent left stick release (center)")
            else:
                self._send_sysbot_cmd("setStick RIGHT 0 0")
                self.manual_status_var.set("Sent right stick release (center)")
        except Exception as e:
            self.manual_status_var.set(f"Error: {e}")

    def _on_switch_ip_change(self, *args):
        self.config_data["switch_ip"] = self.switch_ip_var.get()
        save_config(self.config_data)
    def _on_switch_port_change(self, *args):
        self.config_data["switch_port"] = self.switch_port_var.get()
        save_config(self.config_data)
    def _on_auto_connect_change(self):
        self.config_data["auto_connect"] = self.auto_connect_var.get()
        save_config(self.config_data)

if __name__ == "__main__":
    app = MacroBuilderApp()
    app.mainloop() 