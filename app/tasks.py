from . import scheduler


@scheduler.task("cron", month="*", day="*", hour="1,9,18", minute="8")
def run_task():
    with scheduler.app.app_context():
        from app.service.routes import call_loader

        call_loader()
