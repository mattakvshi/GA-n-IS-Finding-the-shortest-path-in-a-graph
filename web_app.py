"""Web GUI для проекта: ИС для поиска кратчайшего пути.

Запуск:
    python web_app.py

После запуска откроется браузер с интерфейсом:
    http://127.0.0.1:5000
"""

from __future__ import annotations

import json
import math
import random
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

from src.dijkstra_baseline import solve_with_dijkstra
from src.graph_model import WeightedGraph, generate_connected_graph, load_graph_from_json, save_graph_to_json
from src.immune_network import ImmuneNetworkShortestPath
from src.utils import percent_deviation
from src.experiments import run_experiments

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
STATIC_DIR = ROOT / "web_static"
DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")

CURRENT: dict[str, Any] = {
    "graph": None,
    "start": 0,
    "target": 0,
    "positions": {},
    "last_result": None,
}


def _edge_payload(graph: WeightedGraph) -> list[dict[str, Any]]:
    return [
        {"u": e.u, "v": e.v, "weight": e.weight}
        for e in graph.edges()
    ]


def _compute_positions(graph: WeightedGraph, seed: int = 7) -> dict[int, dict[str, float]]:
    """Позиции для SVG-визуализации.

    Используется networkx.spring_layout, но результат приводится к координатам
    в диапазоне [0, 1], чтобы браузеру было удобно масштабировать граф.
    """
    try:
        import networkx as nx

        g = nx.Graph()
        g.add_nodes_from(range(graph.vertices))
        for e in graph.edges():
            g.add_edge(e.u, e.v, weight=e.weight)
        raw = nx.spring_layout(g, seed=seed, weight="weight")
        xs = [float(v[0]) for v in raw.values()]
        ys = [float(v[1]) for v in raw.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1e-9)
        span_y = max(max_y - min_y, 1e-9)
        return {
            int(k): {
                "x": 0.08 + 0.84 * ((float(v[0]) - min_x) / span_x),
                "y": 0.10 + 0.80 * ((float(v[1]) - min_y) / span_y),
            }
            for k, v in raw.items()
        }
    except Exception:
        # Fallback по окружности.
        result = {}
        for i in range(graph.vertices):
            angle = 2 * math.pi * i / graph.vertices
            result[i] = {"x": 0.5 + 0.39 * math.cos(angle), "y": 0.5 + 0.39 * math.sin(angle)}
        return result


def _graph_json(graph: WeightedGraph, start: int, target: int, positions: dict[int, dict[str, float]]) -> dict[str, Any]:
    return {
        "vertices": graph.vertices,
        "edges": _edge_payload(graph),
        "start": start,
        "target": target,
        "positions": {str(k): v for k, v in positions.items()},
    }


def _ensure_demo_graph() -> tuple[WeightedGraph, int, int]:
    demo = DATA_DIR / "graph_demo.json"
    if not demo.exists():
        graph = generate_connected_graph(vertices=14, edges=30, min_weight=1, max_weight=25, seed=77)
        save_graph_to_json(graph, start=0, target=13, path=demo)
    return load_graph_from_json(demo)


def _set_current(graph: WeightedGraph, start: int, target: int, seed: int = 7) -> None:
    CURRENT["graph"] = graph
    CURRENT["start"] = start
    CURRENT["target"] = target
    CURRENT["positions"] = _compute_positions(graph, seed=seed)
    CURRENT["last_result"] = None


def _run_immune(payload: dict[str, Any]) -> dict[str, Any]:
    graph = CURRENT["graph"]
    if graph is None:
        graph, start, target = _ensure_demo_graph()
        _set_current(graph, start, target)
    graph = CURRENT["graph"]
    start = int(CURRENT["start"])
    target = int(CURRENT["target"])

    population_size = int(payload.get("population_size", 70))
    iterations = int(payload.get("iterations", 140))
    mutation_rate = float(payload.get("mutation_rate", 0.50))
    selection_size = max(4, min(population_size, int(payload.get("selection_size", max(8, population_size // 4)))))
    clone_multiplier = int(payload.get("clone_multiplier", 5))
    memory_size = int(payload.get("memory_size", 10))
    seed = int(payload.get("seed", 2026))

    baseline = solve_with_dijkstra(graph, start, target)

    algorithm = ImmuneNetworkShortestPath(
        graph=graph,
        start=start,
        target=target,
        population_size=population_size,
        iterations=iterations,
        selection_size=selection_size,
        clone_multiplier=clone_multiplier,
        mutation_rate=mutation_rate,
        random_injection_rate=0.18,
        memory_size=memory_size,
        seed=seed,
    )
    result = algorithm.run()
    deviation = percent_deviation(result.best_length, baseline.length)

    # Сохраняем краткий JSON для отчётности.
    summary = {
        "algorithm": "Immune Network",
        "student": "Сидоренко Максим",
        "variant": "3 - shortest path in graph",
        "graph_vertices": graph.vertices,
        "graph_edges": graph.edge_count,
        "start": start,
        "target": target,
        "immune_path": result.best_path,
        "immune_path_length": result.best_length,
        "dijkstra_path": baseline.path,
        "dijkstra_path_length": baseline.length,
        "deviation_percent": deviation,
        "elapsed_time_sec": result.elapsed_time,
        "iterations": iterations,
        "population_size": population_size,
        "mutation_rate": mutation_rate,
    }
    (RESULTS_DIR / "web_gui_last_run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    response = {
        "summary": summary,
        "history": result.history,
        "memory": [
            {"path": antibody.path, "length": antibody.objective}
            for antibody in result.memory[: min(len(result.memory), 6)]
        ],
        "explain": [
            "1. Сформирована начальная популяция случайных допустимых путей.",
            "2. Для каждого пути рассчитана длина и аффинность.",
            "3. Лучшие пути были выбраны для клонирования.",
            "4. Клоны прошли гипермутацию: перестройку участков маршрута.",
            "5. Некорректные пути были восстановлены оператором ремонта.",
            "6. Похожие решения удалены супрессией, лучшие сохранены в памяти.",
        ],
    }
    CURRENT["last_result"] = response
    return response


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/demo")
def api_demo():
    graph, start, target = _ensure_demo_graph()
    _set_current(graph, start, target, seed=7)
    return jsonify(_graph_json(graph, start, target, CURRENT["positions"]))


@app.route("/api/generate", methods=["POST"])
def api_generate():
    payload = request.get_json(force=True) or {}
    vertices = max(5, min(120, int(payload.get("vertices", 18))))
    edges = int(payload.get("edges", max(vertices - 1, vertices * 2)))
    max_edges = vertices * (vertices - 1) // 2
    edges = max(vertices - 1, min(edges, max_edges))
    min_weight = max(1, int(payload.get("min_weight", 1)))
    max_weight = max(min_weight, int(payload.get("max_weight", 30)))
    seed = int(payload.get("seed", random.randint(1, 100_000)))

    graph = generate_connected_graph(vertices=vertices, edges=edges, min_weight=min_weight, max_weight=max_weight, seed=seed)
    start = int(payload.get("start", 0))
    target = int(payload.get("target", vertices - 1))
    if start == target:
        target = vertices - 1 if start != vertices - 1 else 0

    _set_current(graph, start, target, seed=seed)
    save_graph_to_json(graph, start, target, DATA_DIR / "web_generated_graph.json")
    return jsonify(_graph_json(graph, start, target, CURRENT["positions"]))


@app.route("/api/run", methods=["POST"])
def api_run():
    payload = request.get_json(force=True) or {}
    try:
        return jsonify(_run_immune(payload))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/experiments", methods=["POST"])
def api_experiments():
    """Запустить стандартную серию экспериментов.

    Для GUI возвращается компактная таблица. PNG-файлы дополнительно
    сохраняются в results.
    """
    try:
        rows = run_experiments()
        return jsonify({"rows": rows, "message": "Эксперименты завершены. Файлы сохранены в results."})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/last")
def api_last():
    if CURRENT["last_result"] is None:
        return jsonify({"message": "Запуск ещё не выполнялся."})
    return jsonify(CURRENT["last_result"])


@app.route("/results/<path:name>")
def serve_results(name):
    return send_from_directory(RESULTS_DIR, name)


def open_browser_later() -> None:
    time.sleep(1.0)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    graph, start, target = _ensure_demo_graph()
    _set_current(graph, start, target)
    threading.Thread(target=open_browser_later, daemon=True).start()
    print("============================================================")
    print(" WEB GUI запущен")
    print(" Откройте в браузере: http://127.0.0.1:5000")
    print(" Для остановки нажмите Ctrl+C в этом окне")
    print("============================================================")
    app.run(host="127.0.0.1", port=5000, debug=False)
