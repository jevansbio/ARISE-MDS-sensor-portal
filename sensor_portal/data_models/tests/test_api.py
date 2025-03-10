import os
from copy import copy
from datetime import datetime as dt
from io import BytesIO

import pytest
from data_models.factories import (DeploymentFactory, DeviceFactory,
                                   ProjectFactory)
from data_models.general_functions import create_image
from data_models.models import DataFile
from data_models.serializers import (DeploymentSerializer, DeviceSerializer,
                                     ProjectSerializer)
from utils.test_functions import (api_check_delete, api_check_post,
                                  api_check_update)


@pytest.mark.django_db
def test_create_project(api_client_with_credentials):
    """
    Test: Can project be created and retrieved through the API.
    """
    check_key = 'name'
    serializer = ProjectSerializer
    new_item = ProjectFactory.build(
        name='test_project',
        project_ID='test_pr_ID')
    api_url = '/api/project/'
    payload = serializer(instance=new_item).data
    api_check_post(api_client_with_credentials, api_url,
                   payload, check_key)


@pytest.mark.django_db
def test_update_project(api_client_with_credentials):
    """
    Test: Can project be updated and retrieved through the API.
    """
    user = api_client_with_credentials.handler._force_user
    check_key = 'project_ID'
    new_item = ProjectFactory(
        name='test_project',
        project_ID='test_pr_ID',
        owner=user)

    api_url = f'/api/project/{new_item.pk}/'
    new_value = 'pr_ID_test'
    api_check_update(api_client_with_credentials,
                     api_url, new_value, check_key)


@pytest.mark.django_db
def test_delete_project(api_client_with_credentials):
    """
    Test: Can project be deleted through the API.
    """
    user = api_client_with_credentials.handler._force_user
    new_item = ProjectFactory(
        name='test_project',
        project_ID='test_pr_ID',
        owner=user)

    api_url = f'/api/project/{new_item.pk}/'

    api_check_delete(api_client_with_credentials,
                     api_url)


@pytest.mark.django_db
def test_create_deployment(api_client_with_credentials):
    """
    Test: Can deployment be created and retrieved through the API.
    """
    user = api_client_with_credentials.handler._force_user
    check_key = 'deployment_ID'
    serializer = DeploymentSerializer
    new_item = DeploymentFactory(
        deployment_ID='test_ID',
        project=[]
    )
    new_item.device.owner = user
    new_item.device.save()
    api_url = '/api/deployment/'
    payload = serializer(instance=new_item).data
    new_item.delete()
    api_check_post(api_client_with_credentials, api_url,
                   payload, check_key)


@pytest.mark.django_db
def test_update_deployment(api_client_with_credentials):
    """
    Test: Can deployment be updated and retrieved through the API.
    """
    user = api_client_with_credentials.handler._force_user
    check_key = 'deployment_ID'
    new_item = DeploymentFactory(
        deployment_ID='test_ID',
        project=[],
        owner=user
    )

    api_url = f'/api/deployment/{new_item.pk}/'
    new_value = 'new_deployment'
    api_check_update(api_client_with_credentials,
                     api_url, new_value, check_key)


@pytest.mark.django_db
def test_delete_deployment(api_client_with_credentials):
    """
    Test: Can deployment be deleted through the API.
    """
    user = api_client_with_credentials.handler._force_user
    new_item = DeploymentFactory(
        deployment_ID='test_ID',
        project=[],
        owner=user
    )

    api_url = f'/api/deployment/{new_item.pk}/'

    api_check_delete(api_client_with_credentials,
                     api_url)


# device tests
@pytest.mark.django_db
def test_create_device(api_client_with_credentials):
    """
    Test: Can device be created and retrieved through the API.
    """
    check_key = 'name'
    serializer = DeviceSerializer
    new_item = DeviceFactory()
    api_url = '/api/device/'
    payload = serializer(instance=new_item).data
    payload["managers_ID"] = []
    print(payload)
    new_item.delete()
    api_check_post(api_client_with_credentials, api_url,
                   payload, check_key)


@pytest.mark.django_db
def test_update_device(api_client_with_credentials):
    """
    Test: Can device be updated and retrieved through the API.
    """
    user = api_client_with_credentials.handler._force_user
    check_key = 'name'
    new_item = DeviceFactory(owner=user)
    api_url = f'/api/device/{new_item.pk}/'
    new_value = 'new_device_name'

    api_check_update(api_client_with_credentials,
                     api_url, new_value, check_key)


@pytest.mark.django_db
def test_delete_device(api_client_with_credentials):
    """
    Test: Can device be udeleted through the API.
    """
    user = api_client_with_credentials.handler._force_user
    new_item = DeviceFactory(owner=user)
    api_url = f'/api/device/{new_item.pk}/'
    api_check_delete(api_client_with_credentials,
                     api_url)


# Test file creation with a single deployment
@pytest.mark.django_db
def test_CRUD_datafile(api_client_with_credentials):
    """
    Test: Can files be created, retrieved, updated and delete through the API. This tests using a deployment object.
    This tests all of CRUD in one go as it is neccesary to delete the actual file after testing anyway.
    """

    user = api_client_with_credentials.handler._force_user

    # Generate a file
    temp = BytesIO()
    test_image = create_image()
    test_image.save(temp, format="JPEG")
    temp.name = "test_file.jpeg"
    temp.seek(0)
    files = [temp]

    test_date_time = dt(1066, 1, 2, 0, 0, 0)
    recording_dt = [test_date_time]

    new_item = DeploymentFactory(
        owner=user, deployment_start=dt(1066, 1, 1, 0, 0, 0))

    api_url = '/api/datafile/'
    payload = {
        "deployment": new_item.deployment_device_ID,
        "files": files,
        "recording_dt": recording_dt
    }

    response_create = api_client_with_credentials.post(
        api_url, data=payload,  format='multipart')
    response_create_json = response_create.data

    print(f"Response: {response_create_json}")

    assert response_create.status_code == 201

    assert response_create_json["uploaded_files"][0]["original_name"] == temp.name

    file_object = DataFile.objects.get(
        file_name=response_create_json["uploaded_files"][0]["file_name"])
    file_path = file_object.full_path()

    assert os.path.exists(file_path)

    object_url = f"{api_url}{file_object.pk}/"
    # update the object
    api_check_update(api_client_with_credentials,
                     object_url, "foo.jpg", "original_name")

    # delete the object and clear the file
    response_delete = api_client_with_credentials.delete(
        object_url, format="json")
    print(f"Response: {response_delete}")
    assert response_delete.status_code == 204

    assert not os.path.exists(file_path)

# Test file creation with a device
# Test file creation with a single deployment


@pytest.mark.django_db
def test_CRUD_datafile_by_device(api_client_with_credentials):
    """
    Test: Can files be created and retrieved through the API. 
    This tests using a device object, and checks partial successes.
    """

    user = api_client_with_credentials.handler._force_user

    # Generate a file
    temp = BytesIO()
    test_image = create_image()
    test_image.save(temp, format="JPEG")
    temp.seek(0)
    file_1 = copy(temp)
    file_1.name = "good_file.jpeg"
    file_2 = copy(temp)
    file_2.name = "bad_file.jpeg"

    files = [file_1, file_2]

    test_date_time_good = dt(1066, 1, 2, 0, 0, 0)
    test_date_time_bad = dt(1065, 1, 2, 0, 0, 0)
    recording_dt = [test_date_time_good, test_date_time_bad]

    new_device = DeviceFactory()

    new_deployment = DeploymentFactory(
        owner=user, deployment_start=dt(1066, 1, 1, 0, 0, 0), device=new_device)

    api_url = '/api/datafile/'
    payload = {
        "device": new_device.device_ID,
        "files": files,
        "recording_dt": recording_dt
    }

    response_create = api_client_with_credentials.post(
        api_url, data=payload,  format='multipart')
    response_create_json = response_create.data

    print(f"Response: {response_create_json}")

    assert response_create.status_code == 201

    assert response_create_json["uploaded_files"][0]["original_name"] == file_1.name
    assert file_2.name in response_create_json["invalid_files"][0].keys()

    file_object = DataFile.objects.get(
        file_name=response_create_json["uploaded_files"][0]["file_name"])
    file_path = file_object.full_path()

    assert os.path.exists(file_path)

    # test if the file can be edited to be outside the deployment time
    object_url = f"{api_url}{file_object.pk}/"
    update_payload = {"recording_dt": test_date_time_bad}
    response_update = api_client_with_credentials.patch(
        object_url, data=update_payload)
    print(f"Response: {response_update.data}")

    assert response_update.status_code == 400

    # delete the object and clear the file
    response_delete = api_client_with_credentials.delete(
        object_url, format="json")
    print(f"Response: {response_delete.data}")
    assert response_delete.status_code == 204

    assert not os.path.exists(file_path)

# Test file update
