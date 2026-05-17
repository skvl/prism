from __future__ import annotations

import math
import os
import random

from textual import work
from textual.containers import Horizontal, VerticalScroll
from textual.events import Key
from textual.message import Message
from textual.widgets import Button, Label, ListItem, ListView, Static

import json

from prism.graph.links import BacklinkIndex, GraphExporter
from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.vault.vault import Vault

from ..messages import SelectNode

TYPE_COLORS: dict[str, str] = {
    "note": "blue",
    "contact": "green",
    "bookmark": "yellow",
    "file": "magenta",
    "task": "cyan",
    "event": "red",
}


class ForceDirectedLayout:
    def __init__(self, nodes: list[NodeMetadata], links: list[dict[str, str]]) -> None:
        self.positions: dict[str, tuple[float, float]] = {}
        self.velocities: dict[str, tuple[float, float]] = {}
        self.width = 80
        self.height = 40
        for node in nodes:
            self.positions[node.uuid] = (
                random.uniform(10, self.width - 10),
                random.uniform(5, self.height - 5),
            )
            self.velocities[node.uuid] = (0.0, 0.0)
        self.links = links
        self.node_list = nodes

    def tick(self, iterations: int = 50) -> None:
        for _ in range(iterations):
            forces: dict[str, tuple[float, float]] = {}
            for uid in self.positions:
                forces[uid] = (0.0, 0.0)
            uuids = list(self.positions.keys())
            for i in range(len(uuids)):
                for j in range(i + 1, len(uuids)):
                    a, b = uuids[i], uuids[j]
                    ax, ay = self.positions[a]
                    bx, by = self.positions[b]
                    dx = bx - ax
                    dy = by - ay
                    dist = math.sqrt(dx * dx + dy * dy) + 0.01
                    repulsion = 500.0 / (dist * dist)
                    fx = repulsion * dx / dist
                    fy = repulsion * dy / dist
                    fa, fb = forces[a], forces[b]
                    forces[a] = (fa[0] - fx, fa[1] - fy)
                    forces[b] = (fb[0] + fx, fb[1] + fy)
            for link in self.links:
                src = link.get("source", "")
                tgt = link.get("target", "")
                if src in self.positions and tgt in self.positions:
                    sx, sy = self.positions[src]
                    tx, ty = self.positions[tgt]
                    dx = tx - sx
                    dy = ty - sy
                    dist = math.sqrt(dx * dx + dy * dy) + 0.01
                    attraction = 0.01 * dist
                    fx = attraction * dx / dist
                    fy = attraction * dy / dist
                    fs, ft = forces[src], forces[tgt]
                    forces[src] = (fs[0] + fx, fs[1] + fy)
                    forces[tgt] = (ft[0] - fx, ft[1] - fy)
            for uid in self.positions:
                fx, fy = forces[uid]
                vx, vy = self.velocities[uid]
                vx = (vx + fx) * 0.5
                vy = (vy + fy) * 0.5
                self.velocities[uid] = (vx, vy)
                px, py = self.positions[uid]
                px = max(5.0, min(float(self.width - 5), px + vx))
                py = max(3.0, min(float(self.height - 3), py + vy))
                self.positions[uid] = (px, py)

    def render_ascii(self, selected: str | None = None) -> str:
        canvas: list[list[str]] = [
            [" " for _ in range(self.width)] for _ in range(self.height)
        ]
        for link in self.links:
            src = link.get("source", "")
            tgt = link.get("target", "")
            if src in self.positions and tgt in self.positions:
                sx, sy = self.positions[src]
                tx, ty = self.positions[tgt]
                self._draw_line(canvas, int(sx), int(sy), int(tx), int(ty))
        for node in self.node_list:
            uid = node.uuid
            if uid not in self.positions:
                continue
            x, y = self.positions[uid]
            ix, iy = int(x), int(y)
            label = node.title[:8] if node.title else uid[:8]
            color = TYPE_COLORS.get(node.type, "white")
            selected_marker = "*" if uid == selected else " "
            for ci, ch in enumerate(f"{selected_marker}{label}"):
                if 0 <= ix + ci < self.width and 0 <= iy < self.height:
                    canvas[iy][ix + ci] = ch
        return "\n".join("".join(row) for row in canvas)

    def _draw_line(
        self, canvas: list[list[str]], x0: int, y0: int, x1: int, y1: int
    ) -> None:
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                if canvas[y0][x0] == " ":
                    canvas[y0][x0] = "."
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy


class GraphTab(Static):
    CSS = """
    GraphTab {
        height: 1fr;
    }

    #graph-canvas {
        height: 1fr;
        padding: 1;
        border: solid $primary;
    }

    #graph-list-view {
        height: 1fr;
    }

    #type-filter-bar {
        height: 3;
        margin-bottom: 1;
    }
    """

    def __init__(self, vault: Vault | None = None) -> None:
        super().__init__()
        self._vault = vault
        self._manager: NodeManager | None = None
        self._layout: ForceDirectedLayout | None = None
        self._selected_uuid: str | None = None
        self._type_filter: str | None = None
        self._all_links: list[dict[str, str]] = []
        self._all_nodes: list[NodeMetadata] = []
        self._pan_x = 0
        self._pan_y = 0
        self._zoom = 1.0

    def set_vault(self, vault: Vault) -> None:
        self._vault = vault
        self._load_graph()

    def _load_graph(self) -> None:
        if self._vault is None:
            return
        self._manager = NodeManager(self._vault.path)
        self._all_nodes = self._manager.list_nodes()
        exporter = GraphExporter(self._vault.path)
        json_str = exporter.export_json(self._all_nodes, include_paths=False)
        data = json.loads(json_str)
        self._all_links = data.get("edges", [])
        visible_nodes = self._filtered_nodes()
        if len(visible_nodes) > 50:
            self._show_list_view(visible_nodes)
        else:
            self._layout = ForceDirectedLayout(visible_nodes, self._all_links)
            self._layout.tick(100)
            self._render_canvas()

    def _filtered_nodes(self) -> list[NodeMetadata]:
        if self._type_filter:
            return [n for n in self._all_nodes if n.type == self._type_filter]
        return list(self._all_nodes)

    def _render_canvas(self) -> None:
        canvas_widget = self.query_one("#graph-canvas", Static)
        if self._layout is None:
            canvas_widget.update("No graph data")
            return
        ascii_art = self._layout.render_ascii(selected=self._selected_uuid)
        canvas_widget.update(ascii_art)

    def _show_list_view(self, nodes: list[NodeMetadata]) -> None:
        canvas = self.query_one("#graph-canvas", Static)
        canvas.display = False
        list_view = self.query_one("#graph-list-view", ListView)
        list_view.display = True
        list_view.clear()
        for node in nodes:
            connected = sum(
                1
                for link in self._all_links
                if link.get("source") == node.uuid
                or link.get("target") == node.uuid
            )
            label = f"{node.type} {node.title}  ({connected} connections)"
            list_view.append(ListItem(Label(label), id=node.uuid))

    def compose(self) -> ComposeResult:
        yield Static(id="graph-canvas")
        yield ListView(id="graph-list-view")

    def on_mount(self) -> None:
        self.query_one("#graph-list-view", ListView).display = False
        if self._vault is not None:
            self._load_graph()

    def on_key(self, event: Key) -> None:
        if event.key == "t":
            self._prompt_type_filter()
            event.stop()
        elif event.key == "Enter" and self._selected_uuid is not None:
            self._navigate_to_browser()
            event.stop()
        elif event.key in ("left", "right", "up", "down"):
            self._handle_pan(event.key)
            event.stop()
        elif event.key in ("plus", "equal"):
            self._zoom = min(3.0, self._zoom + 0.2)
            event.stop()
        elif event.key == "minus":
            self._zoom = max(0.5, self._zoom - 0.2)
            event.stop()

    def _prompt_type_filter(self) -> None:
        self.notify("Enter type filter (use :command mode)", severity="information", timeout=3)

    def _handle_pan(self, direction: str) -> None:
        if direction == "left":
            self._pan_x -= 5
        elif direction == "right":
            self._pan_x += 5
        elif direction == "up":
            self._pan_y -= 2
        elif direction == "down":
            self._pan_y += 2
        self._render_canvas()

    def _navigate_to_browser(self) -> None:
        if self._selected_uuid is None:
            return
        for node in self._all_nodes:
            if node.uuid == self._selected_uuid:
                self.post_message(SelectNode(node))
                break
