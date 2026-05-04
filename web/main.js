const TILE_SIZE = 32;
const LEVELS = [
  {
    key: "1",
    title: "Level 1: Variables & expressions",
    description: "Reach the goal using a few moves. Store counts in variables.",
    requirements: "Use at least one variable assignment.",
    board: ["#####", "#S..#", "#...#", "#..G#", "#####"],
    maxMoves: 20,
    docs: [
      "https://docs.python.org/3/tutorial/introduction.html",
      "https://docs.python.org/3/tutorial/introduction.html#variables"
    ]
  }
];

let currentLevel = LEVELS[0];
let world = null;
let game = null;
let scene = null;
let pyodideReady = false;
let pyodide = null;

const outputEl = document.getElementById("output");
const levelTitleEl = document.getElementById("level-title");
const levelRequirementsEl = document.getElementById("level-requirements");
const moveCounterEl = document.getElementById("move-counter");
const docsEl = document.getElementById("docs");

const log = (message) => {
  outputEl.textContent += `${message}\n`;
  outputEl.scrollTop = outputEl.scrollHeight;
};

const clearLog = () => {
  outputEl.textContent = "";
};

const buildWorld = (level) => {
  const rows = level.board.map((row) => row.split("""));
  const height = rows.length;
  const width = rows[0]?.length ?? 0;
  const walls = new Set();
  let start = null;
  let goal = null;

  rows.forEach((row, rowIndex) => {
    row.forEach((cell, colIndex) => {
      if (cell === "#") {
        walls.add(`${rowIndex},${colIndex}`);
      } else if (cell === "S") {
        start = { row: rowIndex, col: colIndex };
      } else if (cell === "G") {
        goal = { row: rowIndex, col: colIndex };
      }
    });
  });

  return {
    rows,
    height,
    width,
    walls,
    start,
    goal,
    position: { ...start },
    movesUsed: 0,
    maxMoves: level.maxMoves
  };
};

const updateStatus = () => {
  levelTitleEl.textContent = currentLevel.title;
  levelRequirementsEl.textContent = `Requirement: ${currentLevel.requirements}`;
  moveCounterEl.textContent = `Moves: ${world.movesUsed}/${world.maxMoves}`;
};

const renderWorld = () => {
  if (!scene || !world) return;
  scene.playerSprite.x = world.position.col * TILE_SIZE + TILE_SIZE / 2;
  scene.playerSprite.y = world.position.row * TILE_SIZE + TILE_SIZE / 2;
  updateStatus();
};

const canMove = (direction) => {
  const delta = directionToDelta(direction);
  const nextRow = world.position.row + delta.row;
  const nextCol = world.position.col + delta.col;
  if (nextRow < 0 || nextRow >= world.height) return false;
  if (nextCol < 0 || nextCol >= world.width) return false;
  return !world.walls.has(`${nextRow},${nextCol}`);
};

const move = (direction, steps = 1) => {
  if (!Number.isInteger(steps) || steps < 1) {
    throw new Error("steps must be a positive integer.");
  }
  for (let i = 0; i < steps; i += 1) {
    world.movesUsed += 1;
    if (world.movesUsed > world.maxMoves) {
      throw new Error(`Move limit exceeded (${world.maxMoves}).`);
    }
    if (!canMove(direction)) {
      log(`Blocked moving ${direction}.`);
      return false;
    }
    const delta = directionToDelta(direction);
    world.position.row += delta.row;
    world.position.col += delta.col;
    renderWorld();
  }
  return true;
};

const directionToDelta = (direction) => {
  const mapping = {
    up: { row: -1, col: 0 },
    down: { row: 1, col: 0 },
    left: { row: 0, col: -1 },
    right: { row: 0, col: 1 }
  };
  if (!mapping[direction]) {
    throw new Error("Direction must be up, down, left, or right.");
  }
  return mapping[direction];
};

const resetWorld = () => {
  world = buildWorld(currentLevel);
  renderWorld();
};

const updateDocs = () => {
  docsEl.innerHTML = "<h3>Docs</h3>";
  const list = document.createElement("ul");
  currentLevel.docs.forEach((doc) => {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = doc;
    link.textContent = doc;
    link.target = "_blank";
    item.appendChild(link);
    list.appendChild(item);
  });
  docsEl.appendChild(list);
};

const setupPhaser = () => {
  const config = {
    type: Phaser.AUTO,
    parent: "game",
    width: currentLevel.board[0].length * TILE_SIZE,
    height: currentLevel.board.length * TILE_SIZE,
    backgroundColor: "#9ac88f",
    pixelArt: true,
    scene: {
      create() {
        scene = this;
        this.tiles = [];
        for (let row = 0; row < world.height; row += 1) {
          this.tiles[row] = [];
          for (let col = 0; col < world.width; col += 1) {
            const cell = world.rows[row][col];
            const isWall = cell === "#";
            const color = isWall ? 0x4e5d50 : 0xcfe8b3;
            const tile = this.add.rectangle(
              col * TILE_SIZE + TILE_SIZE / 2,
              row * TILE_SIZE + TILE_SIZE / 2,
              TILE_SIZE,
              TILE_SIZE,
              color
            );
            tile.setStrokeStyle(1, 0x8aa27b);
            this.tiles[row][col] = tile;
          }
        }
        this.goalSprite = this.add.rectangle(
          world.goal.col * TILE_SIZE + TILE_SIZE / 2,
          world.goal.row * TILE_SIZE + TILE_SIZE / 2,
          TILE_SIZE * 0.8,
          TILE_SIZE * 0.8,
          0xf7d37a
        );
        this.playerSprite = this.add.rectangle(
          world.position.col * TILE_SIZE + TILE_SIZE / 2,
          world.position.row * TILE_SIZE + TILE_SIZE / 2,
          TILE_SIZE * 0.7,
          TILE_SIZE * 0.7,
          0x4f7bd9
        );
        renderWorld();
      }
    }
  };
  game = new Phaser.Game(config);
};

const loadPyodide = async () => {
  pyodide = await window.loadPyodide();
  const helperCode = `import ast\n\nSAFE_BUILTINS = {\n    "abs": abs,\n    "all": all,\n    "any": any,\n    "bool": bool,\n    "dict": dict,\n    "enumerate": enumerate,\n    "float": float,\n    "int": int,\n    "len": len,\n    "list": list,\n    "max": max,\n    "min": min,\n    "print": print,\n    "range": range,\n    "set": set,\n    "sorted": sorted,\n    "str": str,\n    "sum": sum,\n    "tuple": tuple,\n    "zip": zip,\n}\n\ndef validate_code(code):\n    tree = ast.parse(code, mode="exec")\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Import, ast.ImportFrom)):\n            return "Imports are disabled in this game."\n        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):\n            return "Dunder attributes are disabled in this game."\n        if isinstance(node, ast.Name) and node.id.startswith("__"):\n            return "Dunder names are disabled in this game."\n    return None\n\ndef requirement_check(code):\n    tree = ast.parse(code, mode="exec")\n    return any(isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) for node in ast.walk(tree))\n\ndef make_env(move, can_move, position, goal, show):\n    return {\n        "__builtins__": SAFE_BUILTINS,\n        "move": move,\n        "can_move": can_move,\n        "position": position,\n        "goal": goal,\n        "show": show,\n    }\n`;
  pyodide.runPython(helperCode);
  pyodideReady = true;
  log("Python engine ready.");
};

const runCode = async () => {
  if (!pyodideReady) {
    log("Python engine is still loading...");
    return;
  }
  clearLog();
  resetWorld();
  const code = document.getElementById("code").value;
  if (!code.trim()) {
    log("Please enter some code.");
    return;
  }
  try {
    pyodide.globals.set("player_code", code);
    const blocked = pyodide.runPython("validate_code(player_code)");
    if (blocked) {
      log(blocked);
      return;
    }
    const meetsRequirement = pyodide.runPython("requirement_check(player_code)");
    if (!meetsRequirement) {
      log(`Requirement not met: ${currentLevel.requirements}`);
      return;
    }

    const moveProxy = (direction, steps = 1) => move(direction, steps);
    const canMoveProxy = (direction) => canMove(direction);
    const positionProxy = () => [world.position.row, world.position.col];
    const goalProxy = () => [world.goal.row, world.goal.col];
    const showProxy = () => renderWorld();

    pyodide.globals.set("js_move", moveProxy);
    pyodide.globals.set("js_can_move", canMoveProxy);
    pyodide.globals.set("js_position", positionProxy);
    pyodide.globals.set("js_goal", goalProxy);
    pyodide.globals.set("js_show", showProxy);

    pyodide.runPython(
      "env = make_env(js_move, js_can_move, js_position, js_goal, js_show)"
    );
    pyodide.runPython(
      "exec(compile(player_code, '<player_code>', 'exec'), env, env)"
    );

    if (
      world.position.row === world.goal.row &&
      world.position.col === world.goal.col
    ) {
      log("Level complete!");
    } else {
      log("Goal not reached. Try again.");
    }
  } catch (error) {
    log(`Runtime error: ${error.message ?? error}`);
  }
};

const init = async () => {
  world = buildWorld(currentLevel);
  setupPhaser();
  updateDocs();
  updateStatus();
  document.getElementById("run").addEventListener("click", runCode);
  document.getElementById("reset").addEventListener("click", resetWorld);
  await loadPyodide();
};

window.addEventListener("load", init);