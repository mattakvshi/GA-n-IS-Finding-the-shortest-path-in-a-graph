"""Визуализация графа, найденного пути и экспериментальных графиков."""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

import matplotlib.pyplot as plt

from .graph_model import WeightedGraph


def draw_graph_with_path(graph: WeightedGraph, path: List[int], start: int, target: int, output_path: str | Path, title: str | None = None) -> None:
    """Сохранить изображение графа с подсвеченным найденным путём."""
    import networkx as nx
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    nx_graph = nx.Graph()
    for vertex in range(graph.vertices):
        nx_graph.add_node(vertex)
    for edge in graph.edges():
        nx_graph.add_edge(edge.u, edge.v, weight=edge.weight)
    pos = nx.spring_layout(nx_graph, seed=7, weight='weight')
    plt.figure(figsize=(12, 8))
    nx.draw_networkx_edges(nx_graph, pos, width=1.2, alpha=0.35)
    nx.draw_networkx_nodes(nx_graph, pos, node_size=650)
    nx.draw_networkx_labels(nx_graph, pos, font_size=10, font_weight='bold')
    labels = {(edge.u, edge.v): int(edge.weight) if float(edge.weight).is_integer() else edge.weight for edge in graph.edges()}
    nx.draw_networkx_edge_labels(nx_graph, pos, edge_labels=labels, font_size=8)
    if path and len(path) >= 2:
        path_edges = [tuple(sorted((u, v))) for u, v in zip(path, path[1:])]
        nx.draw_networkx_edges(nx_graph, pos, edgelist=path_edges, width=4.0)
        nx.draw_networkx_nodes(nx_graph, pos, nodelist=path, node_size=760)
    nx.draw_networkx_nodes(nx_graph, pos, nodelist=[start], node_size=900)
    nx.draw_networkx_nodes(nx_graph, pos, nodelist=[target], node_size=900)
    plt.title(title or 'Искусственная иммунная сеть: найденный путь')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output, dpi=180)
    plt.close()


def plot_time_vs_size(rows: Sequence[dict], output_path: str | Path) -> None:
    """Построить график зависимости времени от размерности графа."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    vertices = [int(row['graph_vertices']) for row in rows]
    times = [float(row['execution_time_sec']) for row in rows]
    plt.figure(figsize=(10, 6))
    plt.plot(vertices, times, marker='o', linewidth=2)
    plt.xlabel('Количество вершин')
    plt.ylabel('Среднее время выполнения, сек')
    plt.title('Зависимость времени выполнения ИС от размерности графа')
    plt.grid(True, alpha=0.35)
    plt.tight_layout()
    plt.savefig(output, dpi=180)
    plt.close()


def plot_objective_history(history: Sequence[float], output_path: str | Path, optimal: float | None = None) -> None:
    """Построить график значения целевой функции по итерациям."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.plot(list(range(1, len(history) + 1)), history, linewidth=2, label='Лучшее значение ИС')
    if optimal is not None:
        plt.axhline(optimal, linestyle='--', linewidth=1.5, label='Эталон Дейкстры')
    plt.xlabel('Итерация')
    plt.ylabel('Длина найденного пути')
    plt.title('Зависимость значения целевой функции от числа итераций')
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=180)
    plt.close()
