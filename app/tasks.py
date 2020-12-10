from . import scheduler
from app.utils.refresh_mat_views import refresh_all_mat_views


@scheduler.task("cron", month="*", day="*", hour="10", minute="8")
def run_task_US():
    with scheduler.app.app_context():
        from app.service.routes import call_loader

        call_loader(country="US")


@scheduler.task("cron", month="*", day="*", hour="22", minute="8")
def run_task_GB():
    with scheduler.app.app_context():
        from app.service.routes import call_loader

        call_loader(country="GB")


@scheduler.task("cron", month="*", day="*", hour="*", minute="35")
def refresh_views():
    with scheduler.app.app_context():
        refresh_all_mat_views(False)
