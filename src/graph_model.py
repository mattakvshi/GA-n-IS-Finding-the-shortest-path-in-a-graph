"""Модель взвешенного неориентированного графа и служебные функции."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import heapq
import json
import random


@dataclass(frozen=True)
class Edge:
    """Ребро графа."""

    u: int
    v: int
    weight: float


class WeightedGraph:
    """Взвешенный неориентированный граф.

    В проекте граф используется для задачи поиска кратчайшего пути.
    Вершины нумеруются от 0 до n - 1.
    """

    def __init__(self, vertices: int) -> None:
        if vertices <= 1:
            raise ValueError("Граф должен содержать хотя бы две вершины.")
        self.vertices = vertices
        self._adj: Dict[int, Dict[int, float]] = {i: {} for i in range(vertices)}

    def add_edge(self, u: int, v: int, weight: float) -> None:
        """Добавить неориентированное ребро."""
        self._validate_vertex(u)
        self._validate_vertex(v)
        if u == v:
            raise ValueError("Петли в текущей реализации не используются.")
        if weight <= 0:
            raise ValueError("Вес ребра должен быть положительным.")
        self._adj[u][v] = float(weight)
        self._adj[v][u] = float(weight)

    def neighbors(self, vertex: int) -> Dict[int, float]:
        """Получить соседей вершины."""
        self._validate_vertex(vertex)
        return self._adj[vertex]

    def edges(self) -> List[Edge]:
        """Список рёбер без дублей."""
        result: List[Edge] = []
        seen = set()
        for u, neighbors in self._adj.items():
            for v, weight in neighbors.items():
                key = tuple(sorted((u, v)))
                if key not in seen:
                    seen.add(key)
                    result.append(Edge(u, v, weight))
        return result

    @property
    def edge_count(self) -> int:
        return len(self.edges())

    def has_edge(self, u: int, v: int) -> bool:
        self._validate_vertex(u)
        self._validate_vertex(v)
        return v in self._adj[u]

    def edge_weight(self, u: int, v: int) -> float:
        if not self.has_edge(u, v):
            raise ValueError(f"Ребро ({u}, {v}) отсутствует.")
        return self._adj[u][v]

    def path_length(self, path: List[int]) -> float:
        """Длина пути. Если путь некорректен, возбуждается ValueError."""
        if len(path) < 2:
            raise ValueError("Путь должен содержать минимум две вершины.")
        total = 0.0
        for u, v in zip(path, path[1:]):
            total += self.edge_weight(u, v)
        return total

    def is_valid_path(self, path: List[int], start: int, target: int) -> bool:
        """Проверить, является ли список вершин допустимым путём start -> target."""
        if not path or path[0] != start or path[-1] != target:
            return False
        for u, v in zip(path, path[1:]):
            if not self.has_edge(u, v):
                return False
        return True

    def remove_cycles(self, path: List[int]) -> List[int]:
        """Удалить циклы из пути.

        Если вершина встречается повторно, участок между повторениями удаляется.
        Это полезно после мутаций.
        """
        index_by_vertex = {}
        cleaned: List[int] = []
        for vertex in path:
            if vertex in index_by_vertex:
                idx = index_by_vertex[vertex]
                cleaned = cleaned[: idx + 1]
                index_by_vertex = {v: i for i, v in enumerate(cleaned)}
            else:
                index_by_vertex[vertex] = len(cleaned)
                cleaned.append(vertex)
        return cleaned

    def shortest_path(self, start: int, target: int) -> Tuple[List[int], float]:
        """Эталонный кратчайший путь методом Дейкстры."""
        self._validate_vertex(start)
        self._validate_vertex(target)
        distances = {v: float("inf") for v in range(self.vertices)}
        previous = {v: None for v in range(self.vertices)}
        distances[start] = 0.0
        heap: List[Tuple[float, int]] = [(0.0, start)]
        while heap:
            current_distance, u = heapq.heappop(heap)
            if current_distance > distances[u]:
                continue
            if u == target:
                break
            for v, weight in self.neighbors(u).items():
                candidate = current_distance + weight
                if candidate < distances[v]:
                    distances[v] = candidate
                    previous[v] = u
                    heapq.heappush(heap, (candidate, v))
        if distances[target] == float("inf"):
            raise ValueError("Путь между start и target не найден.")
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        return path, distances[target]

    def random_walk_path(self, start: int, target: int, max_steps: int | None = None, rng: random.Random | None = None) -> List[int]:
        """Построить случайный путь от start до target."""
        self._validate_vertex(start)
        self._validate_vertex(target)
        rng = rng or random.Random()
        max_steps = max_steps or max(4, self.vertices * 2)
        path = [start]
        visited = {start}
        current = start
        for _ in range(max_steps):
            if current == target:
                break
            candidates = [v for v in self.neighbors(current) if v not in visited]
            if not candidates:
                break
            # Смещение в сторону лёгких рёбер повышает качество начальной популяции.
            candidates.sort(key=lambda v: self.edge_weight(current, v))
            top_k = candidates[: max(1, min(len(candidates), 4))]
            nxt = rng.choice(top_k)
            path.append(nxt)
            visited.add(nxt)
            current = nxt
        if path[-1] != target:
            tail, _ = self.shortest_path(path[-1], target)
            path.extend(tail[1:])
        return self.remove_cycles(path)

    def _validate_vertex(self, vertex: int) -> None:
        if vertex < 0 or vertex >= self.vertices:
            raise ValueError(f"Некорректная вершина: {vertex}")


def load_graph_from_json(path: str | Path) -> Tuple[WeightedGraph, int, int]:
    """Загрузить граф из JSON-файла."""
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    graph = WeightedGraph(int(payload["vertices"]))
    for u, v, weight in payload["edges"]:
        graph.add_edge(int(u), int(v), float(weight))
    start = int(payload.get("start", 0))
    target = int(payload.get("target", graph.vertices - 1))
    return graph, start, target


def save_graph_to_json(graph: WeightedGraph, start: int, target: int, path: str | Path) -> None:
    """Сохранить граф в JSON."""
    payload = {
        "vertices": graph.vertices,
        "start": start,
        "target": target,
        "edges": [[edge.u, edge.v, edge.weight] for edge in graph.edges()],
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_connected_graph(vertices: int, edges: int, min_weight: int = 1, max_weight: int = 30, seed: int | None = None) -> WeightedGraph:
    """Сгенерировать связный случайный неориентированный граф."""
    if edges < vertices - 1:
        raise ValueError("Для связного графа нужно минимум vertices - 1 рёбер.")
    max_edges = vertices * (vertices - 1) // 2
    if edges > max_edges:
        raise ValueError("Слишком много рёбер для простого графа.")
    rng = random.Random(seed)
    graph = WeightedGraph(vertices)
    order = list(range(vertices))
    rng.shuffle(order)
    existing = set()
    for i in range(vertices - 1):
        u, v = order[i], order[i + 1]
        graph.add_edge(u, v, rng.randint(min_weight, max_weight))
        existing.add(tuple(sorted((u, v))))
    all_pairs = [(u, v) for u in range(vertices) for v in range(u + 1, vertices) if (u, v) not in existing]
    rng.shuffle(all_pairs)
    need = edges - (vertices - 1)
    for u, v in all_pairs[:need]:
        graph.add_edge(u, v, rng.randint(min_weight, max_weight))
    return graph
