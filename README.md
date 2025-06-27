# ARISE-MDS sensor portal
 
This is a shareable version of the ARISE-MDS sensor portal. It is currently a work in progress. This documentation will be updated when the code approaches a release. 


## Starting the project for the first time

```bash
docker compose -f docker-compose-dev.yml build
```

```bash
docker compose -f docker-compose-dev.yml up
```

Starting the project in dev mode means different settings will be used in the django container. This compose file also uses volumes to allow live changes to containers during development.


## Environmental varaibles

There are a number of environmental variables that the containers will use. The easiest way to provide these is with a .env file in the root of the project.


## Required Variables

| Variable              | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `POSTGRES_NAME`       | Name of the database schema the project will use.                           |
| `POSTGRES_USER`       | Username to the database.                                                   |
| `POSTGRES_PASSWORD`   | Password to access the database.                                            |
| `CELERY_BROKER`       | Celery broker address, e.g. `redis://sensor_portal_redis:6379/0`            |
| `CELERY_BACKEND`      | Celery address for handling results. Can be the same as `CELERY_BROKER`.    |
| `CAPTCHA_SECRET_KEY`  | Key for use with [Google reCaptcha](https://cloud.google.com/security/products/recaptcha). |
| `CAPTCHA_SITE_KEY`    | Site key for use with [Google reCaptcha](https://cloud.google.com/security/products/recaptcha). |

## Optional / Deployment-only Variables

| Variable                   | Description                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------|
| `FIELD_ENCRYPTION_KEY`     | Key to allow use of [encrypted fields in the database](https://pypi.org/project/django-encrypted-model-fields/). |
| `EMAIL_HOST`               | Host for SMTP email server.                                                                     |
| `EMAIL_HOST_USER`          | Username for email server.                                                                      |
| `EMAIL_HOST_PASSWORD`      | Password for email server.                                                                      |
| `DJANGO_SECRET_KEY`        | [Django secret key](https://docs.djangoproject.com/en/5.2/ref/settings/#std-setting-SECRET_KEY) |
| `DJANGO_ALLOWED_HOSTS`     | [Django allowed hosts](https://docs.djangoproject.com/en/5.2/ref/settings/#allowed-hosts)       |
| `DJANGO_CSRF`              | [CSRF trusted origins](https://docs.djangoproject.com/en/5.2/ref/settings/#allowed-hosts)       |
| `DJANGO_CSRF_COOKIE_DOMAIN`| [CSRF cookie domain](https://docs.djangoproject.com/en/5.2/ref/settings/#std-setting-CSRF_COOKIE_DOMAIN) |


### Init database & super user:

```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py migrate
```

```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py createsuperuser
```


## Populating with dummy data
To generate some dummy data you can use the included factories.

```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py shell
```

```py
from data_models import factories

factories.DeploymentFactory()
```

## Testing
To run tests you can use:

```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django pytest
```

## Notes
This project can still be considered WIP. While the back end is fairly solid and well documented, the front end likely needs more behind the scenes work, documentation and bugfixing.

