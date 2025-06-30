import datetime
import logging
import os

import openapi_client
from data_models.models import DataFile, Deployment, Device
from openapi_client import ApiV1DeploymentsPostRequest, ApiV1SensorsPostRequest
from openapi_client.rest import ApiException

from .api_client import ARISEDSIClient

logger = logging.getLogger(__name__)


def post_data(media_pks, dsi_sensor_model_id=1, dsi_project_id=139, dsi_site_id=1):

    DSIclient = ARISEDSIClient()
    DSIclient.initialise_authentication()

    with openapi_client.ApiClient(DSIclient.openapi_client_configuration) as api_client:

        # get DataFile
        datafile_objs = DataFile.objects.filter(
            pk__in=media_pks, local_storage=True)

        # get Deployments
        deployment_pks = datafile_objs.values_list(
            'deployment', flat=True).distinct()
        deployment_objs = Deployment.objects.filter(pk__in=deployment_pks)

        # Get Device objs
        device_pks = deployment_objs.values_list(
            'device', flat=True).distinct()
        device_objs = Device.objects.filter(pk__in=device_pks)

        sensors_api = openapi_client.SensorsApi(api_client)
        deployments_api = openapi_client.DeploymentsApi(api_client)
        media_api = openapi_client.MediaApi(api_client)

        for device_obj in device_objs:
            # Check if sensor already exists on DSI (when this filter is available)

            if (device_dsi_id := device_obj.extra_data.get("dsi_id")) is not None:
                logger.info(
                    f"Device {device_obj.device_ID} already has DSI ID: {device_dsi_id}.")
            else:
                logger.info(
                    f"Device {device_obj.device_ID} does not have DSI ID, creating new sensor.")
                # If not, create it

                create_sensor_response = sensors_api.api_v1_sensors_post(ApiV1SensorsPostRequest(
                    name=device_obj.device_ID,
                    sensor_model_id=dsi_sensor_model_id)
                )
                logger.info(
                    f"Create sensor response: {create_sensor_response}.")

                if not create_sensor_response:
                    logger.error("Unable to create sensor object")
                    continue

                device_dsi_id = create_sensor_response.id
                device_obj.extra_data["dsi_upload"] = str(
                    datetime.datetime.now())
                device_obj.extra_data["dsi_id"] = device_dsi_id
                device_obj.save()

            # For each deployment of this sensor
            device_deployment_objs = device_obj.deployments.all().filter(pk__in=deployment_pks)

            for deployment_obj in device_deployment_objs:
                # Check if deployment already exists
                if (deloyment_dsi_id := deployment_obj.extra_data.get("dsi_id")) is not None:
                    logger.info(
                        f"Deployment {deployment_obj.deployment_device_ID} already has DSI ID: {deloyment_dsi_id}.")
                else:
                    # If not create it
                    new_deployment = ApiV1DeploymentsPostRequest(
                        name=deployment_obj.deployment_device_ID,
                        latitude=deployment_obj.latitude,
                        longitude=deployment_obj.longitude,
                        start_time=deployment_obj.deployment_start,
                        end_time=deployment_obj.deployment_end,
                        site_id=dsi_site_id,
                        sensor_id=device_dsi_id,
                        project_id=dsi_project_id,
                    )

                    create_deployment_response = deployments_api.api_v1_deployments_post(
                        new_deployment)
                    logger.info(
                        f"Create deployment response: {create_deployment_response}.")

                    if not create_deployment_response:
                        logger.error("Unable to create deployment object")
                        continue
                    deloyment_dsi_id = create_deployment_response.deployment_id
                    deployment_obj.extra_data["dsi_upload"] = str(datetime.datetime.now(
                    ))
                    deployment_obj.extra_data["dsi_id"] = deloyment_dsi_id
                    deployment_obj.save()

                deployment_datafiles = datafile_objs.filter(
                    deployment=deployment_obj, extra_data__dsi_upload__isnull=True)

                objects_to_update = []
                # For each media item of this deployment
                for datafile_obj in deployment_datafiles:
                    logger.info(
                        f"Upload {datafile_obj.file_name}.")
                    # Create media item
                    media_file_path = datafile_obj.full_path()
                    with open(media_file_path, "rb") as media_file:
                        file_bytes = media_file.read()
                        files = [(datafile_obj.original_name, file_bytes)]
                        try:
                            media_api.api_v1_media_upload_post(
                                deployment_id=deloyment_dsi_id, file=files)
                            datafile_obj.extra_data["dsi_upload"] = str(datetime.datetime.now(
                            ))
                            objects_to_update.append(datafile_obj)
                        except ApiException as e:
                            logger.error(
                                f"Failed to upload media file {datafile_obj.file_name}: {e}")

                if objects_to_update:
                    DataFile.objects.bulk_update(
                        objects_to_update, ['extra_data'])
                    logger.info(
                        f"Updated {len(objects_to_update)} datafile objects with DSI upload timestamp.")
