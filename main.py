"""Демонстрационный запуск искусственной иммунной сети.

Вариант 3: поиск кратчайшего пути в графе.
Исполнитель: Сидоренко Максим.
"""

from __future__ import annotations

from pathlib import Path

from src.dijkstra_baseline import solve_with_dijkstra
from src.graph_model import load_graph_from_json, save_graph_to_json, generate_connected_graph
from src.immune_network import ImmuneNetworkShortestPath
from src.utils import save_json, percent_deviation
from src.visualization import draw_graph_with_path, plot_objective_history


def ensure_demo_graph() -> Path:
    """Создать демонстрационный граф, если его ещё нет."""
    root = Path(__file__).resolve().parent
    data_dir = root / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    graph_path = data_dir / 'graph_demo.json'
    if graph_path.exists():
        return graph_path
    graph = generate_connected_graph(vertices=14, edges=30, min_weight=1, max_weight=25, seed=77)
    save_graph_to_json(graph, start=0, target=13, path=graph_path)
    return graph_path


def main() -> None:
    root = Path(__file__).resolve().parent
    results_dir = root / 'results'
    results_dir.mkdir(exist_ok=True)
    graph_path = ensure_demo_graph()
    graph, start, target = load_graph_from_json(graph_path)
    baseline = solve_with_dijkstra(graph, start, target)
    algorithm = ImmuneNetworkShortestPath(
        graph=graph,
        start=start,
        target=target,
        population_size=70,
        iterations=140,
        selection_size=18,
        clone_multiplier=5,
        mutation_rate=0.50,
        random_injection_rate=0.18,
        memory_size=10,
        seed=2026,
    )
    result = algorithm.run()
    deviation = percent_deviation(result.best_length, baseline.length)
    print('=== Искусственная иммунная сеть: кратчайший путь ===')
    print(f'Граф: {graph.vertices} вершин, {graph.edge_count} рёбер')
    print(f'Стартовая вершина: {start}')
    print(f'Конечная вершина: {target}')
    print(f'Путь ИС: {" -> ".join(map(str, result.best_path))}')
    print(f'Длина пути ИС: {result.best_length:.4f}')
    print(f'Эталон Дейкстры: {" -> ".join(map(str, baseline.path))}')
    print(f'Длина по Дейкстре: {baseline.length:.4f}')
    print(f'Отклонение: {deviation:.2f}%')
    print(f'Время выполнения ИС: {result.elapsed_time:.6f} сек')
    draw_graph_with_path(
        graph=graph,
        path=result.best_path,
        start=start,
        target=target,
        output_path=results_dir / 'path_visualization.png',
        title=f'ИС: путь {result.best_length:.1f}; Дейкстра: {baseline.length:.1f}',
    )
    plot_objective_history(
        history=result.history,
        output_path=results_dir / 'objective_vs_iterations_demo.png',
        optimal=baseline.length,
    )
    save_json(
        {
            'algorithm': 'Immune Network',
            'variant': '3 - shortest path in graph',
            'student': 'Сидоренко Максим',
            'graph_vertices': graph.vertices,
            'graph_edges': graph.edge_count,
            'start': start,
            'target': target,
            'immune_path': result.best_path,
            'immune_path_length': result.best_length,
            'dijkstra_path': baseline.path,
            'dijkstra_path_length': baseline.length,
            'deviation_percent': deviation,
            'elapsed_time_sec': result.elapsed_time,
        },
        results_dir / 'demo_summary.json',
    )


if __name__ == '__main__':
    main()
