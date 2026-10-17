<!-- What lives in experiments/: design experiments that compare component options -->
# Design experiments

Design experiments compare component options during development. They're grouped by component, in `ingestion/` and `advisor/`, and each group runs in its own uv environment, which imports the backend's code by path, so the backend never installs what only an experiment needs. Each experiment gets its own folder holding its protocol, code and data, and writes to its group's `results/` folder, so it can be rerun on its own. Each group's README records its decisions: the choice, the options, the rule that decided it, why it won and what it costs. They are not run in CI.
