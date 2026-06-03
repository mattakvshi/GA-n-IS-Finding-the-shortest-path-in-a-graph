"""Эталонное решение задачи кратчайшего пути методом Дейкстры."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .graph_model import WeightedGraph


@dataclass(frozen=True)
class DijkstraResult:
    path: List[int]
    length: float


def solve_with_dijkstra(graph: WeightedGraph, start: int, target: int) -> DijkstraResult:
    """Вернуть эталонный кратчайший путь и его длину."""
    path, length = graph.shortest_path(start, target)
    return DijkstraResult(path=path, length=length)
