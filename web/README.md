# Python Learning Quest (Web Prototype)

This folder contains a browser-based prototype using Phaser + Pyodide.

## How to run locally

1. From the repository root, start a static server (any will do):
   - Python 3: `python -m http.server 8000`
   - Node (optional): `npx http-server -p 8000`
2. Open `http://localhost:8000/web/` in your browser.

## What it does

- Renders a small 2D grid world in the browser.
- Runs real Python in the browser via Pyodide.
- Exposes `move`, `can_move`, `position`, `goal`, and `show` to player code.

## Next steps

- Add more levels and requirements.
- Replace the simple rectangles with pixel art tiles.
- Add a proper code editor (Monaco or CodeMirror).
- Add AST-based checks for advanced concepts (loops, functions, classes).