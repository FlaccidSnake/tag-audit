from aqt import mw, gui_hooks
from aqt import theme  # For checking night mode
from aqt.qt import *
from aqt.utils import tooltip, qconnect
from typing import List, Dict, Set

# --- DIALOG CLASS ---

class TagAuditDialog(QDialog):
    def __init__(self, parent, note_ids: List[int]):
        super().__init__(parent)
        self.note_ids = note_ids
        self.all_note_ids = note_ids.copy()
        self.tag_counts: Dict[str, int] = {}
        self.tag_note_map: Dict[str, Set[int]] = {}
        self.tag_widgets: Dict[str, 'TagButton'] = {}
        self.active_tags: Set[str] = set()
        
        # Load config state
        self.config = mw.addonManager.getConfig(__name__) or {}
        self.abbreviate = self.config.get("abbreviate_tags", False)
        
        self.setWindowTitle("Tag Audit")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.resize(600, 400)
        
        self._collect_tags()
        self._setup_ui()
        
    def _collect_tags(self):
        """Collect all tags from the selected notes with counts and note mappings"""
        self.tag_counts.clear()
        self.tag_note_map.clear()
        
        for nid in self.note_ids:
            try:
                note = mw.col.get_note(nid)
                tags = note.tags
                
                for tag in tags:
                    self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
                    
                    if tag not in self.tag_note_map:
                        self.tag_note_map[tag] = set()
                    self.tag_note_map[tag].add(nid)
            except:
                continue
        
        self.active_tags = set(self.tag_counts.keys())
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- TOP BAR (Checkbox) ---
        top_bar = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 10, 10, 5) 
        
        self.checkbox = QCheckBox("Abbreviate tags")
        self.checkbox.setChecked(self.abbreviate)
        self.checkbox.stateChanged.connect(self._on_toggle_shorten)
        
        # Reverted to simple bold styling.
        # This allows Qt to handle the checkbox indicator natively for both Light/Dark modes.
        self.checkbox.setStyleSheet("font-weight: bold;")
        
        top_layout.addWidget(self.checkbox)
        top_layout.addStretch() 
        top_bar.setLayout(top_layout)
        
        layout.addWidget(top_bar)
        
        # --- SCROLL AREA ---
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame) 
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.container = QWidget()
        self.flow_layout = FlowLayout()
        self.flow_layout.setContentsMargins(10, 0, 10, 10)
        self.container.setLayout(self.flow_layout)
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        
        self._populate_tags()
        self._update_browser_search()
        
        self.setLayout(layout)
    
    def _on_toggle_shorten(self, state):
        self.abbreviate = (state == 2) 
        
        self.config['abbreviate_tags'] = self.abbreviate
        mw.addonManager.writeConfig(__name__, self.config)
        
        for button in self.tag_widgets.values():
            button.update_display_mode(self.abbreviate)

    def _populate_tags(self):
        for tag in list(self.tag_widgets.keys()):
            self._remove_widget(tag)
        
        sorted_tags = sorted(self.tag_counts.keys())
        
        for tag in sorted_tags:
            count = self.tag_counts[tag]
            is_active = tag in self.active_tags
            self._create_tag_widget(tag, count, is_active)
    
    def _create_tag_widget(self, tag: str, count: int, is_active: bool):
        button = TagButton(tag, count, self.abbreviate)
        button.set_active(is_active)
        button.removed.connect(lambda t=tag: self._remove_tag(t))
        
        self.tag_widgets[tag] = button
        self.flow_layout.addWidget(button)
    
    def _remove_tag(self, tag: str):
        if tag in self.tag_widgets:
            self.tag_widgets[tag].set_removed()
        
        if tag in self.tag_note_map:
            notes_to_remove = self.tag_note_map[tag]
            self.note_ids = [nid for nid in self.note_ids if nid not in notes_to_remove]
        
        self._collect_tags()
        self._populate_tags()
        self._update_browser_search()
    
    def _remove_widget(self, tag: str):
        if tag in self.tag_widgets:
            button = self.tag_widgets[tag]
            self.flow_layout.removeWidget(button)
            button.deleteLater()
            del self.tag_widgets[tag]
    
    def _update_browser_search(self):
        browser = self.parent()
        if not self.note_ids:
            browser.search_for("nid:0")
            return
        
        nid_query = f"nid:{','.join(str(nid) for nid in self.note_ids)}"
        browser.search_for(nid_query)


# --- BUTTON CLASS (QFrame) ---

class TagButton(QFrame):
    removed = pyqtSignal()
    
    def __init__(self, tag: str, count: int, abbreviate: bool, parent=None):
        super().__init__(parent)
        self.full_tag = tag
        self.count = count
        self.is_removed = False
        self.is_active = True
        self.abbreviate = abbreviate
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(28) 
        
        # Ensure flat frame to prevent default 3D shadows/blur
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(8, 4, 8, 4) 
        self.layout.setSpacing(5)
        self.setLayout(self.layout)
        
        self.x_label = QLabel("✕")
        self.x_label.setFixedWidth(12)
        self.x_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.x_label)
        
        self.text_label = QLabel()
        self._refresh_text_content()
        self.layout.addWidget(self.text_label)
        
        self._update_style(hover=False)

    def update_display_mode(self, abbreviate: bool):
        self.abbreviate = abbreviate
        self._refresh_text_content()

    def _refresh_text_content(self):
        display = self._get_display_tag(self.full_tag)
        self.text_label.setText(f"{display} ({self.count})")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_removed:
                self.removed.emit()

    def enterEvent(self, event):
        if not self.is_removed and self.is_active:
            self._update_style(hover=True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._update_style(hover=False)
        super().leaveEvent(event)

    def set_removed(self):
        self.is_removed = True
        self._update_style(hover=False)
    
    def set_active(self, is_active: bool):
        self.is_active = is_active
        self._update_style(hover=False)

    def _update_style(self, hover: bool):
        is_night = theme.theme_manager.night_mode
        
        # Define Colors
        if is_night:
            bg_normal = "#404040"
            bg_removed = "#2d2d2d"
            border_normal = "#202020" 
            text_normal = "#ddd"
            text_removed = "#666"
        else:
            bg_normal = "#fcfcfc"
            bg_removed = "#e0e0e0"
            border_normal = "#ccc"
            text_normal = "#333"
            text_removed = "#888"

        bg_hover = "#e81123"
        
        lbl_style = "QLabel { background: transparent; border: none; }"
        
        if self.is_removed:
            self.setStyleSheet(f"""
                TagButton {{
                    background-color: {bg_removed};
                    border: 1px solid {border_normal};
                    border-radius: 4px;
                }}
                {lbl_style}
            """)
            self.x_label.setStyleSheet("color: transparent;")
            self.text_label.setStyleSheet(f"color: {text_removed}; text-decoration: line-through;")
            
        elif hover:
            self.setStyleSheet(f"""
                TagButton {{
                    background-color: {bg_hover};
                    border: 1px solid {bg_hover};
                    border-radius: 4px;
                }}
                {lbl_style}
            """)
            self.x_label.setStyleSheet("color: white; font-weight: bold;")
            self.text_label.setStyleSheet("color: white;")
            
        else:
            self.setStyleSheet(f"""
                TagButton {{
                    background-color: {bg_normal};
                    border: 1px solid {border_normal};
                    border-radius: 4px;
                }}
                {lbl_style}
            """)
            self.x_label.setStyleSheet("color: transparent;")
            self.text_label.setStyleSheet(f"color: {text_normal};")

    def _get_display_tag(self, tag: str) -> str:
        if not self.abbreviate:
            return tag
        
        if "::" not in tag:
            return tag
        parts = tag.split("::")
        if len(parts) <= 2:
            return tag
        return f"{parts[0]}::(...)::{parts[-1]}"

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.ToolTip:
            QToolTip.showText(event.globalPos(), self.full_tag)
            return True
        return super().event(event)


# --- LAYOUT CLASS ---

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.item_list = []
    
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
    
    def addItem(self, item):
        self.item_list.append(item)
    
    def count(self):
        return len(self.item_list)
    
    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientation(0)
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size
    
    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        
        for item in self.item_list:
            widget = item.widget()
            space_x = self.spacing()
            space_y = self.spacing()
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        
        return y + line_height - rect.y() + bottom


# --- MAIN LOGIC ---

def show_tag_audit(browser):
    selected_cards = browser.selected_cards()
    if not selected_cards:
        tooltip("No cards selected")
        return
    
    note_ids = list(set(mw.col.get_card(cid).nid for cid in selected_cards))
    dialog = TagAuditDialog(browser, note_ids)
    dialog.exec()


def setup_menu(browser):
    if hasattr(browser, "tag_audit_action_setup_complete"):
        return
        
    action = QAction("Tag Audit", browser)
    action.setShortcut(QKeySequence("Ctrl+Shift+T"))
    
    qconnect(action.triggered, lambda: show_tag_audit(browser))
    
    browser.form.menu_Notes.addSeparator()
    browser.form.menu_Notes.addAction(action)
    
    browser.tag_audit_action_setup_complete = True

def init_addon():
    gui_hooks.browser_menus_did_init.append(setup_menu)
