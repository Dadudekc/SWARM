#!/usr/bin/env python3
"""
odyssey_board.py
----------------
PyQt5 board: 3 tabs (one per Odyssey path) ▸ drag-and-drop columns: TODO, DOING, DONE.

Start:
    python tools/odyssey_board.py runtime/planning/odyssey/agent_2_odyssey.yaml
"""
import sys, yaml
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QHBoxLayout,
    QListWidget, QListWidgetItem, QMessageBox
)

COLUMNS = ["TODO", "DOING", "DONE"]


class KanbanColumn(QListWidget):
    def __init__(self, title: str):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setObjectName(title)
        self.setFont(QFont("Inter", 10))
        self.setSpacing(6)
        self.setStyleSheet("QListWidget { background:#202225; color:#DCDDDE; border:none; }")

    # drag-n-drop overrides
    def dragEnterEvent(self, e): e.accept()
    def dragMoveEvent (self, e): e.accept()
    def dropEvent     (self, e): super().dropEvent(e)


class OdysseyBoard(QMainWindow):
    def __init__(self, yaml_path: Path):
        super().__init__()
        self.setWindowTitle(f"Odyssey Board — {yaml_path.name}")
        self.resize(920, 540)
        self.plan_path = yaml_path
        self.plan_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        self._build_tabs()

    # ╭───────────────────────────── UI BUILDERS ─────────────────────────────╮
    def _build_tabs(self):
        for track in self.plan_data["odyssey_plan"]:
            tab = QWidget()
            hbox = QHBoxLayout(tab)
            columns = {c: KanbanColumn(c) for c in COLUMNS}
            for col in columns.values(): hbox.addWidget(col)
            self.tabs.addTab(tab, track["name"])
            # autogenerate starter cards from location / focus / fear
            columns["TODO"].addItem(QListWidgetItem(f"🎯 Focus → {track['focus'] or 'tbd'}"))
            columns["TODO"].addItem(QListWidgetItem(f"📍 Move → {track['location'] or 'tbd'}"))
            columns["TODO"].addItem(QListWidgetItem(f"😱 Mitigate fear → {track['fear'] or 'tbd'}"))
        self.tabs.setStyleSheet("QTabBar::tab { height:28px; width: 140px; }")

    # ╭──────────────────────────── SAVE EXIT HOOK ───────────────────────────╮
    def closeEvent(self, ev):
        if QMessageBox.question(self, "Save?",
                "Save board state back into YAML?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
            self._persist_board()
        ev.accept()

    def _persist_board(self):
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            track = self.plan_data["odyssey_plan"][i]
            state = {}
            for col_idx, col_name in enumerate(COLUMNS):
                column = widget.layout().itemAt(col_idx).widget()
                state[col_name] = [column.item(j).text() for j in range(column.count())]
            track["kanban"] = state
        self.plan_path.write_text(yaml.dump(self.plan_data, sort_keys=False), encoding="utf-8")
        print(f"💾 Saved → {self.plan_path}")


def main(yaml_file: str):
    app  = QApplication(sys.argv)
    win  = OdysseyBoard(Path(yaml_file))
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: odyssey_board.py <odyssey_yaml>")
        sys.exit(1)
    main(sys.argv[1]) 
