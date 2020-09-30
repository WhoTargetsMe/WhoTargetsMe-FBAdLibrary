from . import scheduler


@scheduler.task("cron", month="*", day="*", hour="*", minute="8")
def run_task_US():
    with scheduler.app.app_context():
        from app.service.routes import call_loader

        call_loader(country="US")


@scheduler.task("cron", month="*", day="*", hour="22", minute="8")
def run_task_GB():
    with scheduler.app.app_context():
        from app.service.routes import call_loader

        call_loader(country="GB")
