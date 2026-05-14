from celery import Celery
app = Celery('demo')
def send_job():
    app.send_task('tasks.echo', args=['hi'])
