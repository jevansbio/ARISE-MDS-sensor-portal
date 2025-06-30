# UVA CONTAINER ORCHESTRATION INSTRUCTIONS

## Basic access 

1. SSH into the server (you must be on a university network to do this)

2. Switch to podman user:

``` bash
sudo -su podman
```

3. View running containers:
```bash
podman ps -a
```

4. Stop all containers:
```bash
podman-compose down
```

5. Start all containers:
```bash
podman-compose up -d
```

The `-d` flag means the process will run detached, not takining over your console.

## View logs and other useful information

#### Follow logs of celery worker or backened container using logs, followed by arguments and the container name

```bash
podman logs arise-mds-sensor-portal_sensor_portal_django_1
```

```bash
podman logs -f --tail 1000 arise-mds-sensor-portal_sensor_portal_worker_1
```

The `-f` flag means the logs are followed live and the `--tail` flag means only the last 1000 lines are returned.

### Use grep to filter logs

#### Find errors:
```bash
podman logs arise-mds-sensor-portal_sensor_portal_django_1 2>&1 | grep ERROR -B 10
```

The `-B` flag will return lines before the string match

#### Follow a certain process ID live:
```bash
podman logs -f --tail 100 arise-mds-sensor-portal_sensor_portal_worker_1 2>&1 | grep pid:60
```

## Check running jobs

1. See all celery jobs and arguments:

```bash
podman exec arise-mds-sensor-portal_sensor_portal_django_1 celery inspect active 

```

2. See just the essential details:

Just running celery inspect active can flood your terminal with all the arguments being used in the jobs (which might be many many files). We can filter the output using grep so as to just see the task names.

```bash
podman exec arise-mds-sensor-portal_sensor_portal_django_1 celery inspect active | grep -o 'type.*' | cut -f2- -d:

```


## Update containers

1. Switch to source code directory:

```bash
cd /home/podman/ARISE-MDS-sensor-portal/
```

2. Get latest version of the source code:
```bash
git pull
```
3. Rebuild container images:

This may take a little time
```bash
podman-compose build
```

4. Stop existing containers.
```bash
podman-compose down
```

5. Start containers using the new images
```bash
podman-compose up -d
```

## Update/Restart ultralytics celery

The ultralytics celery container is optional, but is neccesary to carry out AI inference. It runs on the same network as the other containers, but has its own docker-compose file.

1. Switch to ultralytics-celery directory

```
cd /home/podman/ultralytics_celery
```

2. Get latest version of the source code:
```bash
git pull
```
3. Rebuild container images:

This may take a little time
```bash
podman-compose build
```

4. Stop existing containers.
```bash
podman-compose down
```

5. Start containers using the new images
```bash
podman-compose up -d
```

6. Check the ultralytics celery queue is on the same network as the rest of the containers

```bash
podman exec arise-mds-sensor-portal_sensor_portal_django_1 celery inspect active 

```

## Execute python code inside the containers

1. Enter the container

```bash
podman exec -it arise-mds-sensor-portal_sensor_portal_django_1 python manage.py shell
```

The `-it` flag indicates we want to run this session interactively.

2. Run your python code
```python
print("Hello world, I am inside the container")
```

### Carry out a database query
1. import models
```python
from data_models.models import DataFile
```

2. Carry out a simple query
```python
my_query = DataFile.objects.filter(local_storage=True)
print(my_query)
# do stuff with your query
```
See Django documentation for more details.

### Start a job
1. import tasks
```python
from data_models.tasks import check_device_status
```

2. Run it asynchronously 
```python
check_device_status.apply_async()
```

You will receive an async result, meaning that this task is now running on the celery workers.

3. Run a task with arguments

Often we want to run these jobs with arguments. A common pattern in this system is to pass the primary keys `pk` of objects that the job is to run on.

```python
from data_models.models import DataFile
from dsi.tasks import push_to_dsi_task
# Filter wildlife camera files by those stored locally, and created after a certain date
file_objs = DataFile.objects.filter(file_type__name="wildlifecamera", local_storage=True,
created_on__gte="2025-06-30")

# Get the primary keys of these files as a flat list
file_pks = file_objs.values_list('pk',flat=True)

# Django querysets are not JSON serializable, so convert to a normal python list
file_pks = list(file_pks)

# Other arguments
dsi_project_id = 202
dsi_site_id = 2
dsi_sensor_model_id = 2

# Start the async job to push files to ARISE DSI
push_to_dsi_task.apply_async([file_pks, dsi_project_id, dsi_site_id, dsi_sensor_model_id])

```

See celery documentation for more details on how to run tasks.

## Executing other code inside the containers

You can also enter the OS of the container by running `bash` instead of `python manage.py shell`, after which you can carry out This may be neccesary to execute database migrations.

```bash
podman exec -it arise-mds-sensor-portal_sensor_portal_django_1 bash
```
You will now be inside the container

```bash
ls # Will list files in the container home directory 
```

```bash
python manage.py shell # Enter the python shell as above
```

```bash
python manage.py migrate # Run migrations on the database
```


