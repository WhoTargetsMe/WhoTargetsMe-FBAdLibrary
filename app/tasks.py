from . import scheduler

@scheduler.task('cron', month='*', day='*', hour='1,7,10,15,19', minute='1')
def run_task():
    with scheduler.app.app_context():
        from app.service.routes import call_loader
        call_loader()
