from . import scheduler
from app.utils.refresh_mat_views import refresh_all_mat_views
from app.utils.constants import COUNTRIES

# 5/9 = 5am, 2pm, and 11pm
# https://cron.help/#0_5/9_*_*_*
@scheduler.task("cron", minute="0", hour="5")
def run_task_ALL():

    with scheduler.app.app_context():
        from app.service.routes import call_loader

        for country in COUNTRIES:
            call_loader(
                country=country,
                search=dict(ad_reached_countries=[country], ad_active_status="ALL"),
            )


@scheduler.task("cron", minute="35", hour="*")
def refresh_views():
    with scheduler.app.app_context():
        refresh_all_mat_views(False)
