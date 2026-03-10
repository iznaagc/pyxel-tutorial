# Project Rules

## Development Environment
- All python code **MUST** be run within the `.venv` virtual environment. Do not use the global python environment.
- Python version is 3.14.

## Pyxel Coding Standards
- **Separation of Concerns:** 
  - `update()`: Only handle game logic, state updates, and input here. Do not draw.
  - `draw()`: Only handle rendering (e.g., `pyxel.cls()`, `pyxel.blt()`, `pyxel.text()`). Do not update game state here.
- **Assets:**
  - Load resources (like `.pyxres` files, images, sounds) from the `assets/` directory.

## File Structure
- Main entry point is `src/main.py`.
- Keep the root directory clean; place source code in `src/` and resources in `assets/`.
