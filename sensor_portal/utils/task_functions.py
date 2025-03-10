from sensor_portal.celery import app


class TooManyTasks(Exception):
    def __init__(self, task):
        self.task_id = task.request.id
        self.task_name = task.name
        self.current_retries = task.request.retries
        self.max_retries = task.max_retries
        super(TooManyTasks, self).__init__()

    def __str__(self):

        return f"{self.task_id} not run. Too many {self.task_name} tasks already running. Try {self.current_retries}/{self.max_retries}"


def check_simultaneous_tasks(task, max_tasks):
    active_tasks = app.control.inspect().active()
    all_tasks = []
    for worker, running_tasks in active_tasks.items():
        for running_task in running_tasks:
            if (task.name in running_task["name"] and running_task["id"] != task.request.id):
                all_tasks.append(task)
    print(f"{len(all_tasks)} running")
    if len(all_tasks)+1 > max_tasks:
        raise (TooManyTasks(task))
