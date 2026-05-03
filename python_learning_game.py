"""Python Learning Quest: a gamified, level-based Python practice game."""

from __future__ import annotations

import ast
import signal
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Iterable


SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "print": print,
    "range": range,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}


@dataclass(frozen=True)
class Requirement:
    name: str
    message: str
    check: Callable[[ast.AST], bool]


@dataclass(frozen=True)
class Level:
    key: str
    title: str
    description: Iterable[str]
    docs: Iterable[str]
    board: Iterable[str]
    requirements: Iterable[Requirement]
    max_moves: int = 50
    timeout_seconds: int = 3


class ExecutionTimeout(RuntimeError):
    pass


@contextmanager
def execution_timeout(seconds: int) -> Iterable[None]:
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def handle_timeout(_signum: int, _frame: object) -> None:
        raise ExecutionTimeout("Execution time limit exceeded.")

    previous_handler = signal.signal(signal.SIGALRM, handle_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


class GridWorld:
    def __init__(self, board: Iterable[str], max_moves: int) -> None:
        self._rows = [list(row) for row in board]
        self.height = len(self._rows)
        self.width = len(self._rows[0]) if self._rows else 0
        self.max_moves = max_moves
        self.walls: set[tuple[int, int]] = set()
        self.start: tuple[int, int] | None = None
        self.goal: tuple[int, int] | None = None
        for row_index, row in enumerate(self._rows):
            if len(row) != self.width:
                raise ValueError("Board rows must be the same width.")
            for col_index, cell in enumerate(row):
                if cell == "#":
                    self.walls.add((row_index, col_index))
                elif cell == "S":
                    self.start = (row_index, col_index)
                elif cell == "G":
                    self.goal = (row_index, col_index)
        if self.start is None or self.goal is None:
            raise ValueError("Board must contain S (start) and G (goal).")
        self.reset()

    def reset(self) -> None:
        self.position = self.start
        self.moves_used = 0

    def render(self) -> None:
        for row_index in range(self.height):
            row_chars: list[str] = []
            for col_index in range(self.width):
                spot = (row_index, col_index)
                if spot == self.position:
                    row_chars.append("@")
                elif spot == self.goal:
                    row_chars.append("G")
                elif spot in self.walls:
                    row_chars.append("#")
                else:
                    row_chars.append(".")
            print("".join(row_chars))
        print()

    def at_goal(self) -> bool:
        return self.position == self.goal

    def can_move(self, direction: str) -> bool:
        delta = self._direction_delta(direction)
        next_row = self.position[0] + delta[0]
        next_col = self.position[1] + delta[1]
        return (
            0 <= next_row < self.height
            and 0 <= next_col < self.width
            and (next_row, next_col) not in self.walls
        )

    def move(self, direction: str, steps: int = 1) -> bool:
        if not isinstance(steps, int) or steps < 1:
            raise ValueError("steps must be a positive integer.")
        for _ in range(steps):
            self.moves_used += 1
            if self.moves_used > self.max_moves:
                raise RuntimeError(
                    f"Move limit exceeded ({self.max_moves}). Try a shorter route."
                )
            if not self.can_move(direction):
                print(f"Blocked moving {direction}.")
                self.render()
                return False
            delta = self._direction_delta(direction)
            self.position = (self.position[0] + delta[0], self.position[1] + delta[1])
            self.render()
        return True

    @staticmethod
    def _direction_delta(direction: str) -> tuple[int, int]:
        mapping = {
            "up": (-1, 0),
            "down": (1, 0),
            "left": (0, -1),
            "right": (0, 1),
        }
        if direction not in mapping:
            raise ValueError("Direction must be up, down, left, or right.")
        return mapping[direction]


def requires_nodes(
    node_types: tuple[type[ast.AST], ...], message: str, name: str
) -> Requirement:
    def check(tree: ast.AST) -> bool:
        return any(isinstance(node, node_types) for node in ast.walk(tree))

    return Requirement(name=name, message=message, check=check)


def validate_tree(tree: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "Imports are disabled in this game."
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return "Dunder attributes are disabled in this game."
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            return "Dunder names are disabled in this game."
    return None


def read_user_code() -> str | None:
    print("Type your Python code. End with a line containing only END.")
    print("Type QUIT to leave the game.")
    lines: list[str] = []
    while True:
        prompt = ">>> " if not lines else "... "
        line = input(prompt)
        stripped = line.strip()
        if stripped.upper() == "QUIT":
            return None
        if stripped.upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def build_environment(world: GridWorld) -> dict[str, object]:
    def position() -> tuple[int, int]:
        return world.position

    return {
        "__builtins__": SAFE_BUILTINS,
        "move": world.move,
        "can_move": world.can_move,
        "position": position,
        "goal": world.goal,
        "show": world.render,
    }


def run_level(level: Level) -> bool:
    print("=" * 60)
    print(level.title)
    for line in level.description:
        print(f"- {line}")
    print("Docs:")
    for link in level.docs:
        print(f"  {link}")
    print("=" * 60)
    while True:
        world = GridWorld(level.board, level.max_moves)
        world.render()
        code = read_user_code()
        if code is None:
            return False
        if not code.strip():
            print("Please enter some code.")
            continue
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError as exc:
            print(f"Syntax error: {exc.msg} (line {exc.lineno})")
            continue
        blocked = validate_tree(tree)
        if blocked:
            print(blocked)
            continue
        missing = [
            req.message for req in level.requirements if not req.check(tree)
        ]
        if missing:
            print("Level requirements not met:")
            for message in missing:
                print(f"- {message}")
            continue
        env = build_environment(world)
        try:
            compiled = compile(tree, "<player_code>", "exec")
            with execution_timeout(level.timeout_seconds):
                exec(compiled, env, env)
        except ExecutionTimeout as exc:
            print(exc)
            continue
        except (
            RuntimeError,
            ValueError,
            TypeError,
            NameError,
            KeyError,
            IndexError,
            AttributeError,
            ZeroDivisionError,
            RecursionError,
        ) as exc:
            print(f"Runtime error: {exc}")
            continue
        if world.at_goal():
            print("Level complete!")
            return True
        print("Goal not reached. Try again.")


LEVELS = [
    Level(
        key="1",
        title="Level 1: Variables & expressions",
        description=[
            "Reach the goal using a few moves.",
            "Store counts in variables, then call move().",
            "API: move(direction, steps=1) where direction is 'up', 'down', 'left', 'right'.",
        ],
        docs=[
            "https://docs.python.org/3/tutorial/introduction.html",
            "https://docs.python.org/3/tutorial/introduction.html#using-python-as-a-calculator",
            "https://docs.python.org/3/tutorial/introduction.html#variables",
        ],
        board=[
            "#####",
            "#S..#",
            "#...#",
            "#..G#",
            "#####",
        ],
        requirements=[
            requires_nodes(
                (ast.Assign, ast.AnnAssign, ast.AugAssign),
                "Use at least one variable assignment.",
                "assignment",
            )
        ],
        max_moves=20,
    ),
    Level(
        key="2",
        title="Level 2: Conditionals",
        description=[
            "Use can_move(direction) with an if/else to pick a safe path.",
            "Example idea: if can_move('right'): move('right') else: move('down')",
        ],
        docs=["https://docs.python.org/3/tutorial/controlflow.html#if-statements"],
        board=[
            "######",
            "#S...#",
            "#.##.#",
            "#....#",
            "#.##G#",
            "######",
        ],
        requirements=[
            requires_nodes((ast.If,), "Use an if statement.", "if"),
        ],
        max_moves=35,
    ),
    Level(
        key="3",
        title="Level 3: Loops",
        description=[
            "Use a for or while loop to repeat moves.",
            "Tip: the corridor is longer than it looks.",
        ],
        docs=[
            "https://docs.python.org/3/tutorial/controlflow.html#for-statements",
            "https://docs.python.org/3/tutorial/controlflow.html#the-while-statement",
        ],
        board=[
            "########",
            "#S....G#",
            "########",
        ],
        requirements=[
            requires_nodes(
                (ast.For, ast.While),
                "Use a for loop or a while loop.",
                "loop",
            )
        ],
        max_moves=15,
    ),
    Level(
        key="4",
        title="Level 4: Functions",
        description=[
            "Define a function that handles part of the path, then call it.",
            "You still need to reach the goal after your function runs.",
        ],
        docs=["https://docs.python.org/3/tutorial/controlflow.html#defining-functions"],
        board=[
            "#######",
            "#S....#",
            "#.###.#",
            "#....G#",
            "#######",
        ],
        requirements=[
            requires_nodes(
                (ast.FunctionDef, ast.AsyncFunctionDef),
                "Define at least one function with def.",
                "function",
            )
        ],
        max_moves=30,
    ),
    Level(
        key="5",
        title="Level 5: Lists",
        description=[
            "Create a list of directions and loop through it to move.",
            "This level rewards clean, readable route planning.",
        ],
        docs=[
            "https://docs.python.org/3/tutorial/introduction.html#lists",
            "https://docs.python.org/3/tutorial/datastructures.html#looping-techniques",
        ],
        board=[
            "#######",
            "#S#...#",
            "#.#.#G#",
            "#...#.#",
            "#######",
        ],
        requirements=[
            requires_nodes((ast.List, ast.ListComp), "Create a list.", "list"),
            requires_nodes(
                (ast.For, ast.While),
                "Loop over your list to move.",
                "loop",
            ),
        ],
        max_moves=40,
    ),
    Level(
        key="6",
        title="Level 6: Dictionaries",
        description=[
            "Build a dictionary that maps short commands to directions.",
            "Then use it to decode a route and reach the goal.",
        ],
        docs=["https://docs.python.org/3/tutorial/datastructures.html#dictionaries"],
        board=[
            "########",
            "#S..#..#",
            "#.#.#..#",
            "#.#.##G#",
            "#......#",
            "########",
        ],
        requirements=[
            requires_nodes((ast.Dict, ast.DictComp), "Create a dictionary.", "dict"),
        ],
        max_moves=60,
    ),
    Level(
        key="7",
        title="Level 7: Classes",
        description=[
            "Create a class (e.g., Bot) with a method that moves to the goal.",
            "Instantiate the class and call the method.",
        ],
        docs=["https://docs.python.org/3/tutorial/classes.html"],
        board=[
            "########",
            "#S.....#",
            "#.####.#",
            "#.....G#",
            "########",
        ],
        requirements=[
            requires_nodes((ast.ClassDef,), "Define a class.", "class"),
        ],
        max_moves=45,
    ),
    Level(
        key="8",
        title="Level 8: Generators (advanced)",
        description=[
            "Create a generator function that yields directions.",
            "Loop over the generator and move with each yielded value.",
        ],
        docs=[
            "https://docs.python.org/3/howto/functional.html#generators",
            "https://docs.python.org/3/reference/expressions.html#yield-expressions",
        ],
        board=[
            "########",
            "#S..#..#",
            "#.#.#..#",
            "#.#.##.#",
            "#....#G#",
            "########",
        ],
        requirements=[
            requires_nodes(
                (ast.Yield, ast.YieldFrom),
                "Use yield in a generator.",
                "yield",
            ),
        ],
        max_moves=70,
    ),
]


def main() -> None:
    print("Welcome to Python Learning Quest!")
    print("You will write Python code to move the @ symbol to the G.")
    print("Each level focuses on a new Python concept with official docs.")
    print("Need to stop? Type QUIT when prompted for code.")
    for level in LEVELS:
        completed = run_level(level)
        if not completed:
            print("Goodbye! Come back to continue your Python quest.")
            return
    print("Congratulations! You cleared all levels.")


if __name__ == "__main__":
    main()
