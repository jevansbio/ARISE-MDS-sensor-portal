from data_models.job_handling_functions import register_job

from sensor_portal.celery import app

from .api_client import ARISEDSIClient
from .api_functions import post_data

# Freek Test project 139
# Freek Test Site 1
# Freek Test Model 1


@app.task(name="push_to_dsi")
@register_job("Push to ARISE DSI", "push_to_dsi", "datafile", True, max_items=100,
              default_args={"dsi_project_id": 202, "dsi_site_id": 2, "dsi_sensor_model_id": 2})
def push_to_dsi_task(datafile_pks, dsi_project_id, dsi_site_id, dsi_sensor_model_id, **kwargs):
    post_data(media_pks=datafile_pks, dsi_project_id=dsi_project_id,
              dsi_site_id=dsi_site_id, dsi_sensor_model_id=dsi_sensor_model_id)


@app.task(name="refresh_dsi_token")
def refresh_dsi_token():
    DSIclient = ARISEDSIClient()
    DSIclient.initialise_authentication()
