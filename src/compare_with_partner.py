"""Сравнение результатов ИС с результатами напарника по ГА.

Сценарий нужен для финальной парной сдачи: пользователь реализует ИС,
напарник реализует ГА. Если напарник отдаст CSV в том же формате,
скрипт объединит результаты и построит сравнительные графики.

Запуск из папки "Мои решения":
    python -m src.compare_with_partner path/to/ga_results.csv

Формат CSV ожидается такой же, как у results/experiment_results.csv:
algorithm, graph_vertices, graph_edges, start_vertex, target_vertex,
best_path_length, dijkstra_path_length, deviation_percent,
execution_time_sec, iterations, best_path
"""

from __future__ import annotations

from pathlib import Path
import csv
import sys
from typing import List, Dict

import matplotlib.pyplot as plt

from .utils import project_root


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"CSV-файл не найден: {source}")
    with source.open('r', encoding='utf-8', newline='') as file:
        return list(csv.DictReader(file))


def write_csv(rows: List[Dict[str, str]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError('Нет строк для записи.')
    with output.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_metric(rows: List[Dict[str, str]], metric: str, ylabel: str, title: str, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    algorithms = []
    for row in rows:
        alg = row['algorithm']
        if alg not in algorithms:
            algorithms.append(alg)

    plt.figure(figsize=(10, 6))
    for algorithm in algorithms:
        subset = [r for r in rows if r['algorithm'] == algorithm]
        subset.sort(key=lambda r: int(float(r['graph_vertices'])))
        x = [int(float(r['graph_vertices'])) for r in subset]
        y = [float(r[metric]) for r in subset]
        plt.plot(x, y, marker='o', linewidth=2, label=algorithm)

    plt.xlabel('Количество вершин')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=180)
    plt.close()


def main() -> None:
    root = project_root()
    own_csv = root / 'results' / 'experiment_results.csv'

    if len(sys.argv) < 2:
        print('Укажите путь к CSV напарника с результатами ГА.')
        print('Пример: python -m src.compare_with_partner ../ga_results.csv')
        print(f'CSV с результатами ИС уже лежит здесь: {own_csv}')
        return

    partner_csv = Path(sys.argv[1])
    own_rows = read_csv(own_csv)
    partner_rows = read_csv(partner_csv)
    combined = own_rows + partner_rows

    output_csv = root / 'results' / 'combined_results_ga_vs_is.csv'
    write_csv(combined, output_csv)

    plot_metric(
        combined,
        metric='execution_time_sec',
        ylabel='Время выполнения, сек',
        title='Сравнение времени выполнения: ГА и ИС',
        output_path=root / 'results' / 'comparison_time_ga_vs_is.png',
    )

    plot_metric(
        combined,
        metric='deviation_percent',
        ylabel='Отклонение от эталона Дейкстры, %',
        title='Сравнение качества решений: ГА и ИС',
        output_path=root / 'results' / 'comparison_quality_ga_vs_is.png',
    )

    print(f'Объединённая таблица сохранена: {output_csv}')
    print('Графики сохранены в папку results/.')


if __name__ == '__main__':
    main()
