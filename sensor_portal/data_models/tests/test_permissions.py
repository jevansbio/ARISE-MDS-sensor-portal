import os
from copy import copy
from datetime import datetime as dt
from io import BytesIO

import pytest
from data_models.factories import (DataFileFactory, DeploymentFactory,
                                   DeviceFactory, ProjectFactory, SiteFactory)
from data_models.general_functions import create_image
from data_models.models import DataFile, Deployment
from data_models.serializers import DeploymentSerializer
from user_management.factories import UserFactory

# permissions
# can't deploy a non-managed device, creation and update


@pytest.mark.django_db
def test_deploy_non_managed_device(api_client_with_credentials):
    """
    Test: Check user cannot deploy a device they do not manage, both at creation and during an update.
    """
    user = api_client_with_credentials.handler._force_user
    site = SiteFactory()
    device_not_owned = DeviceFactory()
    device_owned = DeviceFactory(
        owner=user, type=device_not_owned.type, model=device_not_owned.model)
    not_allowed_deployment = DeploymentFactory.build(
        device=device_not_owned, site=site)
    not_allowed_payload = DeploymentSerializer(
        instance=not_allowed_deployment).data

    api_url = '/api/deployment/'

    response_create_not_allowed = api_client_with_credentials.post(
        api_url, data=not_allowed_payload, format="json")
    print(response_create_not_allowed.data)
    assert response_create_not_allowed.status_code == 403

    # If viewset mixins are resolved in the wrong order, the object can still be created despite receiving a 403
    # Check object was not created.
    assert not Deployment.objects.filter(
        deployment_ID=not_allowed_payload["deployment_ID"]).exists()

    allowed_deployment = DeploymentFactory.build(
        device=device_owned, site=site)
    allowed_payload = DeploymentSerializer(
        instance=allowed_deployment).data

    response_create_allowed = api_client_with_credentials.post(
        api_url, data=allowed_payload, format="json")

    print(response_create_allowed.data)
    assert response_create_allowed.status_code == 201
    response_id = response_create_allowed.data["id"]

    response_update_not_allowed = api_client_with_credentials.patch(
        f'{api_url}{response_id}/', data={"device_ID": device_not_owned.pk}, format="json")
    print(response_update_not_allowed.data)
    assert response_update_not_allowed.status_code == 403

    device_not_owned.managers.add(user)
    response_update_allowed = api_client_with_credentials.patch(
        f'{api_url}{response_id}/', data={"device_ID": device_not_owned.pk}, format="json")
    print(response_update_allowed.data)
    assert response_update_allowed.status_code == 200


@pytest.mark.django_db
def test_deploy_to_non_managed_project(api_client_with_credentials):
    """
    Test: Check user cannot deploy to a project they do not manage, both at creation and during an update.
    """
    user = api_client_with_credentials.handler._force_user
    site = SiteFactory()
    device_owned = DeviceFactory(
        owner=user)
    project_not_owned = ProjectFactory()
    project_owned = ProjectFactory(owner=user)

    api_url = '/api/deployment/'

    new_deployment = DeploymentFactory.build(
        device=device_owned, site=site)
    not_allowed_payload = DeploymentSerializer(
        instance=new_deployment).data
    not_allowed_payload['project_ID'] = [project_not_owned.pk]

    print("create not allowed")
    response_create_not_allowed = api_client_with_credentials.post(
        api_url, data=not_allowed_payload, format="json")
    print(response_create_not_allowed.data)
    assert response_create_not_allowed.status_code == 403
    # If viewset mixins are resolved in the wrong order, the object can still be created despite receiving a 403
    assert not Deployment.objects.filter(
        deployment_ID=not_allowed_payload["deployment_ID"]).exists()

    new_deployment = DeploymentFactory.build(
        device=device_owned, site=site)

    allowed_payload = DeploymentSerializer(
        instance=new_deployment).data
    allowed_payload['project_ID'] = [project_owned.pk]

    print("create allowed")
    response_create_allowed = api_client_with_credentials.post(
        api_url, data=allowed_payload, format="json")
    print(response_create_allowed.data)
    assert response_create_allowed.status_code == 201
    response_id = response_create_allowed.data["id"]

    print("update not allowed")
    response_update_not_allowed = api_client_with_credentials.patch(
        f'{api_url}{response_id}/', data={"project_ID": [project_not_owned.pk]}, format="json")

    print(response_update_not_allowed.data)
    assert response_update_not_allowed.status_code == 403

    response_update_allowed = api_client_with_credentials.patch(
        f'{api_url}{response_id}/', data={"project_ID": [project_owned.pk]}, format="json")

    print(response_update_allowed.data)
    assert response_update_allowed.status_code == 200


@pytest.mark.django_db
def test_device_manager_manage_deployment(api_client_with_credentials):
    """
    Test: Viewers of a device can see a deployment, managers can change it and delete it.

    """
    user = api_client_with_credentials.handler._force_user
    site = SiteFactory()
    device = DeviceFactory()
    device_deployment = DeploymentFactory(
        device=device, site=site, owner=device.owner)
    device.viewers.add(user)

    api_url = f'/api/deployment/{device_deployment.pk}/'
    response_get = api_client_with_credentials.get(
        api_url)
    print(response_get.data)
    assert response_get.status_code == 200

    response_delete_not_allowed = api_client_with_credentials.delete(
        api_url)
    print(response_delete_not_allowed.data)
    assert response_delete_not_allowed.status_code == 403

    response_patch_not_allowed = api_client_with_credentials.patch(
        api_url, {'deployment_ID': 'new_id'}, format='json')
    assert response_patch_not_allowed.status_code == 403

    device.managers.add(user)
    response_patch_allowed = api_client_with_credentials.patch(
        api_url, {'deployment_ID': 'new_id'}, format='json')
    assert response_patch_allowed.status_code == 200
    assert response_patch_allowed.data['deployment_ID'] == 'new_id'

    response_delete_allowed = api_client_with_credentials.delete(
        api_url)
    print(response_delete_allowed.data)
    assert response_delete_allowed.status_code == 204


@pytest.mark.django_db
def test_project_manager_manage_deployment(api_client_with_credentials):
    """
    Test: Viewers of a project can see a deployment, managers can change it and delete it.
    """
    user = api_client_with_credentials.handler._force_user
    site = SiteFactory()
    device = DeviceFactory(
    )
    project = ProjectFactory(owner=device.owner)
    device_deployment = DeploymentFactory(
        device=device, site=site, owner=project.owner, project=[])
    device_deployment.project.add(project)
    project.viewers.add(user)

    api_url = f'/api/deployment/{device_deployment.pk}/'
    response_get = api_client_with_credentials.get(
        api_url)
    print(response_get.data)
    assert response_get.status_code == 200

    response_delete_not_allowed = api_client_with_credentials.delete(
        api_url)
    print(response_delete_not_allowed.data)
    assert response_delete_not_allowed.status_code == 403

    project.managers.add(user)

    response_patch_allowed = api_client_with_credentials.patch(
        api_url, {'deployment_ID': 'new_id'}, format='json')
    print(response_patch_allowed.data)
    assert response_patch_allowed.status_code == 200
    assert response_patch_allowed.data['deployment_ID'] == 'new_id'

    response_delete_allowed = api_client_with_credentials.delete(
        api_url)
    print(response_delete_allowed.data)
    assert response_delete_allowed.status_code == 204


@pytest.mark.django_db
def test_deployment_viewer_view_datafiles(api_client_with_credentials):
    """
    Test: Viewers of a project can see a deployment, managers can change it and delete it.
    """
    user = api_client_with_credentials.handler._force_user
    data_file_object = DataFileFactory()

    object_url = f'/api/datafile/{data_file_object.pk}/'

    response_get_fail = api_client_with_credentials.get(
        object_url, format="json")
    print(f"Response: {response_get_fail.data}")
    assert response_get_fail.status_code == 404

    data_file_object.deployment.viewers.add(user)

    response_get_success = api_client_with_credentials.get(
        object_url, format="json")
    print(f"Response: {response_get_success.data}")
    assert response_get_success.status_code == 200

    data_file_object.delete()


@pytest.mark.django_db
def test_project_manager_upload_files(api_client_with_credentials):
    """
    Test: Viewers of a project can see datafiles, managers can upload and manage.
    """
    user = api_client_with_credentials.handler._force_user
    site = SiteFactory()
    device = DeviceFactory(
    )
    project = ProjectFactory(owner=device.owner)
    device_deployment = DeploymentFactory(
        device=device, site=site, owner=project.owner, project=[],
        deployment_start=dt(1066, 1, 1, 0, 0, 0))
    device_deployment.project.add(project)

    # Test attempting to upload a file
    # Generate a file
    temp = BytesIO()
    test_image = create_image()
    test_image.save(temp, format="JPEG")
    temp.name = "test_file.jpeg"
    temp.seek(0)
    files = [temp]

    test_date_time = dt(1066, 1, 2, 0, 0, 0)
    recording_dt = [test_date_time]

    api_url = '/api/datafile/'
    payload = {
        "deployment": device_deployment.deployment_device_ID,
        "files": files,
        "recording_dt": recording_dt
    }

    response_create_fail = api_client_with_credentials.post(
        api_url, data=payload,  format='multipart')
    response_create_fail_json = response_create_fail.data

    print(f"Response: {response_create_fail_json}")
    assert response_create_fail.status_code == 403

    # Test being allowed to upload a file
    project.managers.add(user)

    temp = BytesIO()
    test_image = create_image()
    test_image.save(temp, format="JPEG")
    temp.name = "test_file.jpeg"
    temp.seek(0)
    files = [temp]
    payload = {
        "deployment": device_deployment.deployment_device_ID,
        "files": files,
        "recording_dt": recording_dt
    }

    response_create_success = api_client_with_credentials.post(
        api_url, data=payload,  format='multipart')
    response_create_success_json = response_create_success.data

    print(f"Response: {response_create_success_json}")
    assert response_create_success.status_code == 201

    file_object = DataFile.objects.get(
        file_name=response_create_success_json["uploaded_files"][0]["file_name"])

    object_url = f"{api_url}{file_object.pk}/"

    # Test being able to view the file
    project.managers.remove(user)

    response_get_fail = api_client_with_credentials.get(
        object_url, format="json")
    print(f"Response: {response_get_fail.data}")
    assert response_get_fail.status_code == 404

    project.viewers.add(user)

    response_get_success = api_client_with_credentials.get(
        object_url, format="json")
    print(f"Response: {response_get_success.data}")
    assert response_get_success.status_code == 200

    # Test attempting to delete
    response_delete_fail = api_client_with_credentials.delete(
        object_url, format="json")
    print(f"Response: {response_delete_fail.data}")
    assert response_delete_fail.status_code == 403

    project.managers.add(user)
    # Test being allowed to delete
    response_delete_success = api_client_with_credentials.delete(
        object_url, format="json")
    print(f"Response: {response_delete_success.data}")
    assert response_delete_success.status_code == 204


@pytest.mark.django_db
def test_device_manager_upload_files(api_client_with_credentials):
    """
    Test: Viewers of a device can see datafiles, managers can upload and manage.
    """
    user = api_client_with_credentials.handler._force_user
    site = SiteFactory()
    device = DeviceFactory(
    )
    project = ProjectFactory(owner=device.owner)
    device_deployment = DeploymentFactory(
        device=device, site=site, owner=project.owner, project=[],
        deployment_start=dt(1066, 1, 1, 0, 0, 0))
    device_deployment.project.add(project)
    device.viewers.add(user)

    # Generate a file
    temp = BytesIO()
    test_image = create_image()
    test_image.save(temp, format="JPEG")
    temp.name = "test_file.jpeg"
    temp.seek(0)
    files = [temp]

    test_date_time = dt(1066, 1, 2, 0, 0, 0)
    recording_dt = [test_date_time]

    api_url = '/api/datafile/'
    payload = {
        "device": device.device_ID,
        "files": files,
        "recording_dt": recording_dt
    }

    response_create_fail = api_client_with_credentials.post(
        api_url, data=payload,  format='multipart')
    response_create_fail_json = response_create_fail.data

    print(f"Response: {response_create_fail_json}")
    assert response_create_fail.status_code == 403

    device.viewers.remove(user)

    device.managers.add(user)

    temp = BytesIO()
    test_image = create_image()
    test_image.save(temp, format="JPEG")
    temp.name = "test_file.jpeg"
    temp.seek(0)
    files = [temp]
    payload = {
        "device": device.device_ID,
        "files": files,
        "recording_dt": recording_dt
    }

    response_create_success = api_client_with_credentials.post(
        api_url, data=payload,  format='multipart')
    response_create_success_json = response_create_success.data

    print(f"Response: {response_create_success_json}")
    assert response_create_success.status_code == 201

    file_object = DataFile.objects.get(
        file_name=response_create_success_json["uploaded_files"][0]["file_name"])
    object_url = f"{api_url}{file_object.pk}/"

    # Test being able to view the file when no longer manager
    device.managers.remove(user)

    response_get_fail = api_client_with_credentials.get(
        object_url, format="json")
    print(f"Response: {response_get_fail.data}")
    assert response_get_fail.status_code == 404

    device.viewers.add(user)

    response_get_success = api_client_with_credentials.get(
        object_url, format="json")
    print(f"Response: {response_get_success.data}")
    assert response_get_success.status_code == 200

    # Test trying to remove the file
    response_delete_fail = api_client_with_credentials.delete(
        object_url, format="json")
    print(f"Response: {response_delete_fail.data}")
    assert response_delete_fail.status_code == 403

    device.managers.add(user)
    # delete the object and clear the file
    response_delete_success = api_client_with_credentials.delete(
        object_url, format="json")
    print(f"Response: {response_delete_success}")
    assert response_delete_success.status_code == 204
