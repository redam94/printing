"""Shared, versioned build123d component library.

Every public component is a function decorated with ``@component`` from
``lib.component``.  Import a component from its module::

    from lib.patterns.pi import pi5_mount
    from lib.fasteners.heat_set_boss import heat_set_boss

Run ``uv run python scripts/reindex.py`` after any change here; the generated
``PARTS.md`` / ``parts.json`` are the source of truth for what exists.
"""
