from . import scheduler
from app.utils.refresh_mat_views import refresh_all_mat_views
import datetime


@scheduler.task("cron", month="*", day="*", hour="*", minute="8")
def run_task_US():
    with scheduler.app.app_context():
        from app.service.routes import call_loader

        # TODO remove `search`
        # TODO remove `all_ads`

        # aggressive update on all current ads
        now = datetime.datetime.now()
        today_date_string = now.strftime("%Y-%m-%d")
        search = dict(
            ad_delivery_date_min=today_date_string,
            ad_delivery_date_max=today_date_string,
        )

        call_loader(country="US", search=search, all_ads=True)


@scheduler.task("cron", month="*", day="*", hour="22", minute="8")
def run_task_GB():
    with scheduler.app.app_context():
        from app.service.routes import call_loader

        call_loader(country="GB")


@scheduler.task("cron", month="*", day="*", hour="*", minute="35")
def refresh_views():
    with scheduler.app.app_context():
        refresh_all_mat_views(False)
