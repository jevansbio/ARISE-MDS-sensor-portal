import datetime
from django.conf import settings
import pytest
from data_models.factories import (
    DataTypeFactory,
    DeploymentFactory,
    DeviceFactory,
    DeviceModelFactory,
    ProjectFactory,
    SiteFactory,
)
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point

# Project


@pytest.mark.django_db
def test_project_ID_create():
    """
    Test: On project creation, is a short ID automatically generated?
    """
    new_project = ProjectFactory(
        name="project_name_longer_than_10"
    )

    assert new_project.project_ID == "project_na"

# Site
# Is a short ID automatically generated


@pytest.mark.django_db
def test_site_shortname_create():
    """
    Test: On site creation, is a short ID automatically generated?
    """
    new_site = SiteFactory(
        name="project_name_longer_than_10"
    )

    assert new_site.short_name == "project_na"

# Device


@pytest.mark.django_db
def test_create_device_wrong_model():
    """
    Test: Can a device be created with a mismatch between the device type and the model device type?
    """

    type_1 = DataTypeFactory(name="data_type_1")
    type_2 = DataTypeFactory(name="data_type_2")

    new_device_model = DeviceModelFactory(
        type=type_1
    )
    with pytest.raises(ValidationError):
        DeviceFactory(
            type=type_2,
            model=new_device_model
        )


@pytest.mark.django_db
def test_deployment_from_date():
    """
    Test: Does the `deployment_from_date` function work?
    """

    new_device = DeviceFactory(type=None)
    deployment_1 = DeploymentFactory(device_type=None,
                                     device=new_device,
                                     deployment_start=datetime.datetime(
                                         1066, 1, 1),
                                     deployment_end=datetime.datetime(1066, 12, 31))
    deployment_2 = DeploymentFactory(device_type=None,
                                     device=new_device,
                                     deployment_start=datetime.datetime(
                                         1067, 1, 1),
                                     deployment_end=datetime.datetime(1067, 12, 31))
    deployment_3 = DeploymentFactory(device_type=None,
                                     device=new_device,
                                     deployment_start=datetime.datetime(
                                         1068, 1, 1),
                                     deployment_end=None)

    assert new_device.deployment_from_date("1066-06-06") == deployment_1
    assert new_device.deployment_from_date("1067-06-06") == deployment_2
    assert new_device.deployment_from_date("1068-06-06") == deployment_3


@pytest.mark.django_db
def test_device_user_creation():
    """
    Test: Check if a device user is created on device creation.
    """
    new_device = DeviceFactory(type=None)
    assert new_device.managers.all().exists() is True


# Deployment
#
@pytest.mark.django_db
def test_overlapping_deployment_end_date():
    """
    Test: Check if overlapping deployments (where deployment has an end date) can be created (should fail).
    """
    new_device = DeviceFactory(type=None)
    DeploymentFactory(device_type=None,
                      device=new_device,
                      deployment_start=datetime.datetime(
                          1066, 1, 1),
                      deployment_end=datetime.datetime(1066, 12, 31))
    with pytest.raises(ValidationError):
        DeploymentFactory(device_type=None,
                          device=new_device,
                          deployment_start=datetime.datetime(
                              1066, 1, 1),
                          deployment_end=datetime.datetime(1067, 12, 31))


@pytest.mark.django_db
def test_overlapping_deployment_open():
    """
    Test: Check if overlapping deployments (where deployment is open) can be created (should fail).
    """
    new_device = DeviceFactory(type=None)
    DeploymentFactory(device_type=None,
                      device=new_device,
                      deployment_start=datetime.datetime(
                          1066, 1, 1),
                      deployment_end=None)
    with pytest.raises(ValidationError):
        DeploymentFactory(device_type=None,
                          device=new_device,
                          deployment_start=datetime.datetime(
                              1066, 1, 1),
                          deployment_end=datetime.datetime(1067, 12, 31))


@pytest.mark.django_db
def test_deployment_end_after_start():
    """
    Test: Check if deployment can end before it starts (should fail).
    """
    with pytest.raises(ValidationError):
        DeploymentFactory(device_type=None,
                          deployment_start=datetime.datetime(
                              1066, 1, 1),
                          deployment_end=datetime.datetime(
                              1065, 1, 1))


@pytest.mark.django_db
def test_global_project():
    """
    Test: Check if the global project is added to a deployment on creation and after editing.
    """
    new_deployment = DeploymentFactory(device_type=None, project=[])
    print("Check if globabl project exists after creation")
    assert new_deployment.project.all().exists() is True
    new_deployment.project.clear()
    new_deployment.save()
    print("Check if globabl project exists after edit")
    assert new_deployment.project.all().exists() is True


@pytest.mark.django_db
def test_combo_project():
    """
    Test: Check if combo project string is correctly generated.
    """
    new_project_1 = ProjectFactory(name="test_1")
    new_project_2 = ProjectFactory(name="test_2")

    new_deployment = DeploymentFactory(device_type=None, project=[])
    new_deployment.project.add(new_project_1)
    target_string_1 = (" ").join(
        [settings.GLOBAL_PROJECT_ID, new_project_1.project_ID])

    print("Check if combo project is correct on creation")
    assert new_deployment.combo_project == target_string_1

    new_deployment.project.add(new_project_2)
    target_string_2 = (" ").join(
        [settings.GLOBAL_PROJECT_ID, new_project_1.project_ID, new_project_2.project_ID])

    print("Check if combo project is correct on edit")
    assert new_deployment.combo_project == target_string_2

    new_deployment.project.clear()
    new_deployment.project.add(new_project_2)
    target_string_3 = (" ").join(
        [settings.GLOBAL_PROJECT_ID, new_project_2.project_ID])

    print("Check if combo project is correct after clear")
    assert new_deployment.combo_project == target_string_3


@pytest.mark.django_db
def test_lat_lon_to_point():
    """
    Test: Is spatial point generated from lat/lon fields.
    """
    new_deployment = DeploymentFactory(longitude=5, latitude=4.5)
    assert new_deployment.point.coords == (5, 4.5)


@pytest.mark.django_db
def test_point_to_lat_lon():
    """
    Test: Are lat/lon fields generated from point.
    """
    new_deployment = DeploymentFactory(point=Point(4.5, 5))
    assert (new_deployment.longitude == 4.5) & (new_deployment.latitude == 5)

# Is a deployment marked as active or not after creation and update?
