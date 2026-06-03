"""Искусственная иммунная сеть для поиска кратчайшего пути в графе."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import random
import time

from .graph_model import WeightedGraph


@dataclass
class Antibody:
    """Антитело — возможный путь от start до target."""

    path: List[int]
    objective: float
    affinity: float

    def clone(self) -> "Antibody":
        return Antibody(path=self.path[:], objective=self.objective, affinity=self.affinity)

    @property
    def key(self) -> Tuple[int, ...]:
        return tuple(self.path)


@dataclass
class ImmuneNetworkResult:
    best_path: List[int]
    best_length: float
    elapsed_time: float
    history: List[float]
    population_size: int
    iterations: int
    memory: List[Antibody]


class ImmuneNetworkShortestPath:
    """Искусственная иммунная сеть с клональным отбором и супрессией.

    Адаптация к задаче кратчайшего пути:
    - антиген: граф и пара вершин start-target;
    - антитело: допустимый путь start -> target;
    - целевая функция: суммарная длина пути;
    - аффинность: 1 / (1 + длина пути);
    - гипермутация: перестройка участка пути;
    - супрессия: удаление одинаковых и слишком похожих путей;
    - память: лучшие найденные решения.
    """

    def __init__(
        self,
        graph: WeightedGraph,
        start: int,
        target: int,
        population_size: int = 60,
        iterations: int = 120,
        selection_size: int = 15,
        clone_multiplier: int = 4,
        mutation_rate: float = 0.45,
        suppression_threshold: float = 0.85,
        random_injection_rate: float = 0.20,
        memory_size: int = 8,
        seed: int | None = 42,
    ) -> None:
        if population_size < 4:
            raise ValueError("population_size должен быть не меньше 4.")
        if selection_size < 1 or selection_size > population_size:
            raise ValueError("selection_size должен быть в диапазоне [1, population_size].")
        self.graph = graph
        self.start = start
        self.target = target
        self.population_size = population_size
        self.iterations = iterations
        self.selection_size = selection_size
        self.clone_multiplier = clone_multiplier
        self.mutation_rate = mutation_rate
        self.suppression_threshold = suppression_threshold
        self.random_injection_rate = random_injection_rate
        self.memory_size = memory_size
        self.rng = random.Random(seed)

    def run(self) -> ImmuneNetworkResult:
        """Запустить алгоритм."""
        start_time = time.perf_counter()
        population = self._initial_population()
        memory: List[Antibody] = []
        history: List[float] = []
        for _ in range(self.iterations):
            population = self._evaluate_population(population)
            population.sort(key=lambda antibody: antibody.objective)
            memory = self._update_memory(memory, population)
            history.append(memory[0].objective)
            selected = population[: self.selection_size]
            clones = self._clone_and_mutate(selected)
            clones = self._evaluate_population(clones)
            combined = population + clones + memory
            combined.sort(key=lambda antibody: antibody.objective)
            suppressed = self._suppress(combined)
            population = suppressed[: self.population_size]
            population = self._inject_random_antibodies(population)
            population = self._evaluate_population(population)
            population.sort(key=lambda antibody: antibody.objective)
            population = population[: self.population_size]
        population = self._evaluate_population(population)
        population.sort(key=lambda antibody: antibody.objective)
        memory = self._update_memory(memory, population)
        best = memory[0] if memory else population[0]
        elapsed = time.perf_counter() - start_time
        return ImmuneNetworkResult(
            best_path=best.path,
            best_length=best.objective,
            elapsed_time=elapsed,
            history=history,
            population_size=self.population_size,
            iterations=self.iterations,
            memory=memory,
        )

    def _initial_population(self) -> List[Antibody]:
        return [self._make_antibody(self.graph.random_walk_path(self.start, self.target, rng=self.rng)) for _ in range(self.population_size)]

    def _make_antibody(self, path: List[int]) -> Antibody:
        path = self._repair_path(path)
        objective = self._objective(path)
        affinity = 1.0 / (1.0 + objective)
        return Antibody(path=path, objective=objective, affinity=affinity)

    def _evaluate_population(self, population: List[Antibody]) -> List[Antibody]:
        return [self._make_antibody(antibody.path) for antibody in population]

    def _objective(self, path: List[int]) -> float:
        if self.graph.is_valid_path(path, self.start, self.target):
            return self.graph.path_length(path)
        penalty = 10000.0
        repaired = self._repair_path(path)
        if self.graph.is_valid_path(repaired, self.start, self.target):
            return self.graph.path_length(repaired) + penalty
        return penalty * 10

    def _clone_and_mutate(self, selected: List[Antibody]) -> List[Antibody]:
        clones: List[Antibody] = []
        for rank, antibody in enumerate(selected):
            clone_count = max(1, self.clone_multiplier + (self.selection_size - rank) // 4)
            for _ in range(clone_count):
                clone = antibody.clone()
                if self.rng.random() < self.mutation_rate:
                    clone.path = self._hypermutate(clone.path)
                clones.append(clone)
        return clones

    def _hypermutate(self, path: List[int]) -> List[int]:
        if len(path) <= 2:
            return self.graph.random_walk_path(self.start, self.target, rng=self.rng)
        mode = self.rng.choice(["rebuild_tail", "insert_detour", "shortcut"])
        if mode == "rebuild_tail":
            cut = self.rng.randint(0, len(path) - 2)
            prefix = path[: cut + 1]
            tail = self.graph.random_walk_path(prefix[-1], self.target, rng=self.rng)
            return self.graph.remove_cycles(prefix + tail[1:])
        if mode == "insert_detour":
            idx = self.rng.randint(0, len(path) - 2)
            u = path[idx]
            neighbors = list(self.graph.neighbors(u).keys())
            if not neighbors:
                return path
            mid = self.rng.choice(neighbors)
            tail = self.graph.random_walk_path(mid, self.target, rng=self.rng)
            return self.graph.remove_cycles(path[: idx + 1] + [mid] + tail[1:])
        if len(path) >= 4:
            i = self.rng.randint(0, len(path) - 3)
            j = self.rng.randint(i + 2, len(path) - 1)
            bridge, _ = self.graph.shortest_path(path[i], path[j])
            return self.graph.remove_cycles(path[:i] + bridge + path[j + 1 :])
        return path

    def _repair_path(self, path: List[int]) -> List[int]:
        if not path:
            return self.graph.random_walk_path(self.start, self.target, rng=self.rng)
        if path[0] != self.start:
            path = [self.start] + path
        if path[-1] != self.target:
            path = path + [self.target]
        repaired = [path[0]]
        for next_vertex in path[1:]:
            current = repaired[-1]
            if current == next_vertex:
                continue
            if self.graph.has_edge(current, next_vertex):
                repaired.append(next_vertex)
            else:
                bridge, _ = self.graph.shortest_path(current, next_vertex)
                repaired.extend(bridge[1:])
        if repaired[-1] != self.target:
            tail = self.graph.random_walk_path(repaired[-1], self.target, rng=self.rng)
            repaired.extend(tail[1:])
        repaired = self.graph.remove_cycles(repaired)
        if repaired[0] != self.start or repaired[-1] != self.target:
            repaired = self.graph.random_walk_path(self.start, self.target, rng=self.rng)
        return repaired

    def _update_memory(self, memory: List[Antibody], population: List[Antibody]) -> List[Antibody]:
        candidates = memory + population
        candidates.sort(key=lambda antibody: antibody.objective)
        unique: List[Antibody] = []
        seen = set()
        for antibody in candidates:
            if antibody.key not in seen:
                unique.append(antibody.clone())
                seen.add(antibody.key)
            if len(unique) >= self.memory_size:
                break
        return unique

    def _suppress(self, population: List[Antibody]) -> List[Antibody]:
        result: List[Antibody] = []
        for antibody in population:
            if not result:
                result.append(antibody)
                continue
            too_similar = any(self._path_similarity(antibody.path, existing.path) >= self.suppression_threshold for existing in result)
            if not too_similar:
                result.append(antibody)
            if len(result) >= self.population_size:
                break
        return result

    def _inject_random_antibodies(self, population: List[Antibody]) -> List[Antibody]:
        target_random = max(1, int(self.population_size * self.random_injection_rate))
        result = population[:]
        while len(result) < self.population_size:
            result.append(self._make_antibody(self.graph.random_walk_path(self.start, self.target, rng=self.rng)))
        result.sort(key=lambda antibody: antibody.objective)
        for i in range(target_random):
            replace_idx = len(result) - 1 - i
            if replace_idx > 0:
                result[replace_idx] = self._make_antibody(self.graph.random_walk_path(self.start, self.target, rng=self.rng))
        return result

    @staticmethod
    def _path_similarity(left: List[int], right: List[int]) -> float:
        def edge_set(path: List[int]) -> set[Tuple[int, int]]:
            return {tuple(sorted((u, v))) for u, v in zip(path, path[1:])}
        a = edge_set(left)
        b = edge_set(right)
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)
