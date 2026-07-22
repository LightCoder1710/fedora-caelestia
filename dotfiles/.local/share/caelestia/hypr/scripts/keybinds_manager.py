#!/usr/bin/env python3
import sys
import os
import re
import subprocess
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QLabel,
    QDialog, QFormLayout, QComboBox, QMessageBox, QHeaderView
)

KEYBINDS_PATH = os.path.expanduser("~/.config/hypr/hyprland/keybinds.conf")

class KeySequenceEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Click here and press shortcut keys...")
        self.setReadOnly(True)
        self.mods = []
        self.key_name = ""

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        # Map modifiers
        mod_list = []
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            mod_list.append("Super")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            mod_list.append("Alt")
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            mod_list.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            mod_list.append("Shift")
            
        key_name = ""
        # Identify standard/special keys
        if key not in (Qt.Key.Key_Meta, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift):
            seq = QKeySequence(key)
            key_name = seq.toString()
            # Normalize common keys
            if key == Qt.Key.Key_Return:
                key_name = "Return"
            elif key == Qt.Key.Key_Enter:
                key_name = "Enter"
            elif key == Qt.Key.Key_Space:
                key_name = "Space"
            elif key == Qt.Key.Key_Tab:
                key_name = "Tab"
            elif key == Qt.Key.Key_Escape:
                key_name = "Escape"
            elif key == Qt.Key.Key_Backspace:
                key_name = "BackSpace"
            elif key == Qt.Key.Key_Delete:
                key_name = "Delete"
            elif key == Qt.Key.Key_Print:
                key_name = "Print"
            elif key == Qt.Key.Key_Left:
                key_name = "left"
            elif key == Qt.Key.Key_Right:
                key_name = "right"
            elif key == Qt.Key.Key_Up:
                key_name = "up"
            elif key == Qt.Key.Key_Down:
                key_name = "down"
        
        self.mods = mod_list
        self.key_name = key_name
        
        display_mods = "+".join(mod_list)
        if display_mods and key_name:
            self.setText(f"{display_mods}, {key_name}")
        elif display_mods:
            self.setText(display_mods)
        elif key_name:
            self.setText(key_name)
        else:
            self.setText("")
            
        event.accept()

class KeybindDialog(QDialog):
    def __init__(self, parent=None, bind_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add Keybind" if bind_data is None else "Edit Keybind")
        self.resize(450, 320)
        self.bind_data = bind_data
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.cmd_combo = QComboBox()
        self.cmd_combo.addItems(["bind", "binde", "bindl", "bindle", "bindr", "bindi", "bindin"])
        if bind_data:
            self.cmd_combo.setCurrentText(bind_data.get("bind_cmd", "bind"))
            
        self.key_edit = KeySequenceEdit()
        if bind_data:
            mods = bind_data.get("mods", "")
            key = bind_data.get("key", "")
            if mods:
                self.key_edit.setText(f"{mods}, {key}")
            else:
                self.key_edit.setText(key)
            self.key_edit.mods = mods.split("+") if mods else []
            self.key_edit.key_name = key
            
        self.disp_edit = QLineEdit()
        self.disp_edit.setPlaceholderText("e.g. exec, workspace, killactive")
        if bind_data:
            disp = bind_data.get("dispatcher", "")
            args = bind_data.get("args", "")
            if args:
                self.disp_edit.setText(f"{disp}, {args}")
            else:
                self.disp_edit.setText(disp)
                
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("e.g. Launch Terminal")
        if bind_data:
            self.desc_edit.setText(bind_data.get("description", ""))
            
        form_layout.addRow(QLabel("Bind Type:"), self.cmd_combo)
        form_layout.addRow(QLabel("Shortcut:"), self.key_edit)
        form_layout.addRow(QLabel("Action:"), self.disp_edit)
        form_layout.addRow(QLabel("Description:"), self.desc_edit)
        
        layout.addLayout(form_layout)
        
        buttons_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_save)
        
        layout.addLayout(buttons_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1e;
                color: #e1e1e6;
            }
            QLabel {
                color: #c4c4cc;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                background-color: #26262b;
                border: 1px solid #3c3c42;
                border-radius: 6px;
                padding: 8px;
                color: #e1e1e6;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #ff79c6;
            }
            QPushButton {
                background-color: #26262b;
                border: 1px solid #3c3c42;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e1e1e6;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #323238;
                border-color: #ff79c6;
            }
        """)

    def get_data(self):
        shortcut_text = self.key_edit.text()
        if "," in shortcut_text:
            parts = [p.strip() for p in shortcut_text.split(",", 1)]
            mods = parts[0]
            key = parts[1]
        else:
            mods = ""
            key = shortcut_text.strip()
            
        action_text = self.disp_edit.text().strip()
        dispatcher = ""
        args = ""
        if "," in action_text:
            parts = [p.strip() for p in action_text.split(",", 1)]
            dispatcher = parts[0]
            args = parts[1]
        else:
            dispatcher = action_text
            
        return {
            "bind_cmd": self.cmd_combo.currentText(),
            "mods": mods,
            "key": key,
            "dispatcher": dispatcher,
            "args": args,
            "description": self.desc_edit.text().strip()
        }

class KeybindsManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyprland Keybinds Manager")
        self.setObjectName("hypr-keybinds-manager")
        self.resize(900, 650)
        
        self.lines_data = []
        self.load_data()
        
        self.init_ui()
        
    def load_data(self):
        self.lines_data = []
        current_section = "General"
        recent_comments = []
        
        if not os.path.exists(KEYBINDS_PATH):
            return
            
        with open(KEYBINDS_PATH, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                stripped = line.strip()
                
                if stripped.startswith("# ##"):
                    current_section = stripped.replace("# ##", "").strip()
                    self.lines_data.append({"type": "meta", "content": line, "line_no": line_idx})
                    recent_comments = []
                    continue
                    
                if not stripped or stripped.startswith("#"):
                    self.lines_data.append({"type": "meta", "content": line, "line_no": line_idx})
                    if stripped.startswith("#"):
                        comment_text = stripped.lstrip("#").strip()
                        if comment_text:
                            recent_comments.append(comment_text)
                    else:
                        recent_comments = []
                    continue
                
                bind_match = re.match(r"^(bind[a-z]*)\s*=\s*(.*)$", stripped)
                if bind_match:
                    bind_cmd = bind_match.group(1)
                    rest = bind_match.group(2)
                    
                    inline_comment = ""
                    if " # " in rest:
                        parts = rest.split(" # ", 1)
                        rest = parts[0].strip()
                        inline_comment = parts[1].strip()
                    elif "  #" in rest:
                        parts = rest.split("  #", 1)
                        rest = parts[0].strip()
                        inline_comment = parts[1].strip()
                    elif "#" in rest and not rest.startswith("#"):
                        parts = rest.rsplit("#", 1)
                        if len(parts) == 2 and not ("'" in parts[1] or '"' in parts[1]):
                            rest = parts[0].strip()
                            inline_comment = parts[1].strip()
                    
                    tokens = [t.strip() for t in rest.split(",")]
                    
                    mods = ""
                    key = ""
                    dispatcher = ""
                    args = ""
                    
                    if tokens:
                        if tokens[0].startswith("$"):
                            mods = ""
                            key = tokens[0]
                            if len(tokens) > 1:
                                dispatcher = tokens[1]
                            if len(tokens) > 2:
                                args = ", ".join(tokens[2:])
                        else:
                            if len(tokens) >= 3:
                                mods = tokens[0]
                                key = tokens[1]
                                dispatcher = tokens[2]
                                args = ", ".join(tokens[3:])
                            elif len(tokens) == 2:
                                mods = tokens[0]
                                key = tokens[1]
                            else:
                                key = tokens[0]
                    
                    description = inline_comment
                    if not description and recent_comments:
                        description = " / ".join(recent_comments)
                    
                    self.lines_data.append({
                        "type": "bind",
                        "bind_cmd": bind_cmd,
                        "mods": mods,
                        "key": key,
                        "dispatcher": dispatcher,
                        "args": args,
                        "description": description,
                        "section": current_section,
                        "original_line": line,
                        "line_no": line_idx
                    })
                else:
                    self.lines_data.append({"type": "meta", "content": line, "line_no": line_idx})

    def save_data(self):
        with open(KEYBINDS_PATH, "w", encoding="utf-8") as f:
            for item in self.lines_data:
                if item["type"] == "meta":
                    f.write(item["content"])
                elif item["type"] == "bind":
                    bind_cmd = item["bind_cmd"]
                    mods = item.get("mods", "")
                    key = item.get("key", "")
                    dispatcher = item.get("dispatcher", "")
                    args = item.get("args", "")
                    desc = item.get("description", "")
                    
                    if key.startswith("$"):
                        bind_str = f"{key}, {dispatcher}"
                        if args:
                            bind_str += f", {args}"
                    else:
                        bind_str = f"{mods}, {key}, {dispatcher}"
                        if args:
                            bind_str += f", {args}"
                    
                    line = f"{bind_cmd} = {bind_str}"
                    if desc:
                        line += f"  # {desc}"
                    line += "\n"
                    f.write(line)
                    
        # Apply changes instantly
        subprocess.run(["hyprctl", "reload"])

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Header Layout
        header_layout = QHBoxLayout()
        title_label = QLabel("Hyprland Keyboard Shortcuts")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff79c6;")
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search shortcuts by keys, actions, or descriptions...")
        self.search_edit.setFixedWidth(350)
        self.search_edit.textChanged.connect(self.filter_table)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.search_edit)
        
        main_layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Shortcut", "Action", "Description", "Section", "Type"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        main_layout.addWidget(self.table)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add Shortcut")
        self.btn_add.clicked.connect(self.on_add)
        self.btn_edit = QPushButton("Edit Selected")
        self.btn_edit.clicked.connect(self.on_edit)
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.clicked.connect(self.on_delete)
        
        self.btn_save = QPushButton("Save & Apply")
        self.btn_save.setObjectName("saveButton")
        self.btn_save.clicked.connect(self.on_save)
        
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        
        bottom_layout.addWidget(self.btn_add)
        bottom_layout.addWidget(self.btn_edit)
        bottom_layout.addWidget(self.btn_delete)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_close)
        bottom_layout.addWidget(self.btn_save)
        
        main_layout.addLayout(bottom_layout)
        
        # Styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121214;
            }
            QWidget {
                background-color: #121214;
                color: #e1e1e6;
                font-family: 'Open Sans', 'Inter', sans-serif;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #202024;
                border: 1px solid #323238;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e1e1e6;
            }
            QLineEdit:focus {
                border-color: #ff79c6;
            }
            QTableWidget {
                background-color: #121214;
                alternate-background-color: #18181b;
                gridline-color: #202024;
                border: 1px solid #202024;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #ff79c6;
                color: #121214;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #202024;
                color: #c4c4cc;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                background-color: #202024;
                border: 1px solid #323238;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e1e1e6;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #323238;
                border-color: #ff79c6;
            }
            QPushButton#saveButton {
                background-color: #ff79c6;
                color: #121214;
                border: none;
            }
            QPushButton#saveButton:hover {
                background-color: #ff92df;
            }
        """)
        
        self.populate_table()

    def populate_table(self):
        self.table.setRowCount(0)
        bind_items = [item for item in self.lines_data if item["type"] == "bind"]
        self.table.setRowCount(len(bind_items))
        
        for idx, item in enumerate(bind_items):
            shortcut = f"{item['mods']}, {item['key']}" if item['mods'] else item['key']
            action = f"{item['dispatcher']}, {item['args']}" if item['args'] else item['dispatcher']
            desc = item['description']
            sec = item['section']
            cmd = item['bind_cmd']
            
            row_items = [shortcut, action, desc, sec, cmd]
            for col, text in enumerate(row_items):
                table_item = QTableWidgetItem(text)
                table_item.setFlags(table_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                table_item.setData(Qt.ItemDataRole.UserRole, item) # Store reference to original object
                self.table.setItem(idx, col, table_item)

    def filter_table(self):
        query = self.search_edit.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def get_selected_item(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return None
        row = selected_ranges[0].topRow()
        item = self.table.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def on_add(self):
        dialog = KeybindDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            new_bind = {
                "type": "bind",
                "bind_cmd": data["bind_cmd"],
                "mods": data["mods"],
                "key": data["key"],
                "dispatcher": data["dispatcher"],
                "args": data["args"],
                "description": data["description"],
                "section": "User Keybinds"
            }
            
            # Find User Keybinds section header or add it
            found_idx = -1
            for i, item in enumerate(self.lines_data):
                if item["type"] == "meta" and "User Keybinds" in item["content"]:
                    found_idx = i
                    break
            
            if found_idx != -1:
                # Insert after the header
                insert_idx = found_idx + 1
                while insert_idx < len(self.lines_data) and self.lines_data[insert_idx]["type"] == "meta" and not self.lines_data[insert_idx]["content"].strip().startswith("# ##"):
                    insert_idx += 1
                self.lines_data.insert(insert_idx, new_bind)
            else:
                self.lines_data.append({"type": "meta", "content": "\n# ## User Keybinds\n"})
                self.lines_data.append(new_bind)
                
            self.populate_table()

    def on_edit(self):
        bind_data = self.get_selected_item()
        if not bind_data:
            QMessageBox.warning(self, "No Selection", "Please select a keybind row to edit.")
            return
            
        dialog = KeybindDialog(self, bind_data)
        if dialog.exec():
            new_data = dialog.get_data()
            
            # Update values in lines_data
            bind_data["bind_cmd"] = new_data["bind_cmd"]
            bind_data["mods"] = new_data["mods"]
            bind_data["key"] = new_data["key"]
            bind_data["dispatcher"] = new_data["dispatcher"]
            bind_data["args"] = new_data["args"]
            bind_data["description"] = new_data["description"]
            
            self.populate_table()

    def on_delete(self):
        bind_data = self.get_selected_item()
        if not bind_data:
            QMessageBox.warning(self, "No Selection", "Please select a keybind row to delete.")
            return
            
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the shortcut for {bind_data.get('key')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.lines_data.remove(bind_data)
            self.populate_table()

    def on_save(self):
        try:
            self.save_data()
            QMessageBox.information(self, "Success", "Keybinds saved and applied successfully!")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save keybinds: {e}")

if __name__ == "__main__":
    # Ensure correct Wayland settings for Qt
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"
    
    app = QApplication(sys.argv)
    
    # Configure WM class / App ID for window rules to match correctly
    app.setApplicationName("hypr-keybinds-manager")
    app.setDesktopFileName("hypr-keybinds-manager")
    
    window = KeybindsManager()
    window.show()
    sys.exit(app.exec())
