from app import db


def refresh_mat_view(name, concurrently):
    try:
        # since session.execute() bypasses autoflush, must manually flush in order
        # to include newly-created/modified objects in the refresh
        db.session.flush()
        _con = "CONCURRENTLY " if concurrently else ""
        db.session.execute("REFRESH MATERIALIZED VIEW " + _con + name)
    except:
        print("Problem updating view " + name)


def refresh_all_mat_views(concurrently=True):
    """Refreshes all materialized views. Currently, views are refreshed in
    non-deterministic order, so view definitions can't depend on each other."""

    mat_views = db.inspect(db.engine).get_view_names()
    for v in mat_views:
        refresh_mat_view(v, concurrently)
