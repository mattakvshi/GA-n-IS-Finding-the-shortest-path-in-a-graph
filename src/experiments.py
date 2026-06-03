"""Экспериментальное исследование искусственной иммунной сети."""

from __future__ import annotations

import csv
import statistics

from .dijkstra_baseline import solve_with_dijkstra
from .graph_model import generate_connected_graph, save_graph_to_json
from .immune_network import ImmuneNetworkShortestPath
from .utils import percent_deviation, project_root
from .visualization import plot_objective_history, plot_time_vs_size


def run_experiments() -> list[dict]:
    """Запустить серию экспериментов и сохранить результаты.

    Параметры подобраны так, чтобы эксперимент быстро выполнялся на обычном
    ноутбуке, но всё равно показывал рост времени при увеличении графа.
    """
    root = project_root()
    data_dir = root / 'data' / 'generated'
    results_dir = root / 'results'
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    cases = [
        {'vertices': 10, 'edges': 18, 'iterations': 45, 'population': 28},
        {'vertices': 18, 'edges': 38, 'iterations': 55, 'population': 32},
        {'vertices': 26, 'edges': 65, 'iterations': 65, 'population': 36},
        {'vertices': 34, 'edges': 95, 'iterations': 75, 'population': 40},
    ]

    rows: list[dict] = []
    history_for_plot = None
    optimal_for_plot = None

    for index, case in enumerate(cases, start=1):
        vertices = case['vertices']
        edges = case['edges']
        start = 0
        target = vertices - 1
        graph = generate_connected_graph(vertices, edges, seed=100 + index)
        save_graph_to_json(graph, start, target, data_dir / f'graph_{vertices}_vertices.json')
        baseline = solve_with_dijkstra(graph, start, target)

        run_lengths = []
        run_times = []
        best_path = None
        best_history = None
        best_length_seen = float('inf')

        for run_index in range(2):
            algorithm = ImmuneNetworkShortestPath(
                graph=graph,
                start=start,
                target=target,
                population_size=case['population'],
                iterations=case['iterations'],
                selection_size=max(6, case['population'] // 4),
                clone_multiplier=3,
                mutation_rate=0.48,
                random_injection_rate=0.20,
                memory_size=6,
                seed=1000 + index * 10 + run_index,
            )
            result = algorithm.run()
            run_lengths.append(result.best_length)
            run_times.append(result.elapsed_time)
            if result.best_length < best_length_seen:
                best_length_seen = result.best_length
                best_path = result.best_path
                best_history = result.history

        avg_length = statistics.mean(run_lengths)
        avg_time = statistics.mean(run_times)
        deviation = percent_deviation(avg_length, baseline.length)
        row = {
            'algorithm': 'Immune Network',
            'graph_vertices': vertices,
            'graph_edges': graph.edge_count,
            'start_vertex': start,
            'target_vertex': target,
            'best_path_length': round(avg_length, 4),
            'dijkstra_path_length': round(baseline.length, 4),
            'deviation_percent': round(deviation, 4),
            'execution_time_sec': round(avg_time, 6),
            'iterations': case['iterations'],
            'best_path': ' -> '.join(map(str, best_path or [])),
        }
        rows.append(row)
        if history_for_plot is None:
            history_for_plot = best_history
            optimal_for_plot = baseline.length

    csv_path = results_dir / 'experiment_results.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    plot_time_vs_size(rows, results_dir / 'time_vs_graph_size.png')
    if history_for_plot:
        plot_objective_history(history_for_plot, results_dir / 'objective_vs_iterations.png', optimal_for_plot)
    return rows


if __name__ == '__main__':
    rows = run_experiments()
    print('Эксперименты завершены. Полученные строки:')
    for row in rows:
        print(row)
