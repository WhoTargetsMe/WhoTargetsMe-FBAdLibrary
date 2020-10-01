from . import scheduler
from app.utils.refresh_mat_views import refresh_mat_view


@scheduler.task("cron", month="*", day="*", hour="*", minute="8")
def run_task_US():
    with scheduler.app.app_context():
        from app.service.routes import call_loader

        call_loader(country="US")
        refresh_mat_view("mv_unique_adverts_by_date", False)


@scheduler.task("cron", month="*", day="*", hour="22", minute="8")
def run_task_GB():
    with scheduler.app.app_context():
        from app.service.routes import call_loader

        call_loader(country="GB")
        refresh_mat_view("mv_unique_adverts_by_date", False)
