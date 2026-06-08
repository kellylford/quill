"""First-party feature modules migrated off ``main_frame.py``.

Each module here expresses a cohesive group of command-shaped features as plain
handlers that act through the wx-free :class:`quill.core.contributions.Host`
facade, exactly as a third-party Quillin's ``register(api)`` would — but against
the rich trusted host. This is the strangler-fig target shape of the Quillin
migration plan (``docs/quillin-migration-plan.md`` §3): logic leaves the
god-object one self-contained, individually testable module at a time.
"""
