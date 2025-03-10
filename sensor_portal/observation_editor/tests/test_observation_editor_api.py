import pytest
from data_models.factories import DataFileFactory
from observation_editor.factories import ObservationFactory, TaxonFactory
from observation_editor.models import Taxon
from utils.test_functions import (api_check_delete, api_check_post,
                                  api_check_update)


@pytest.mark.django_db
def test_create_obs(api_client_with_credentials):
    """
    Test: Can observation be created and retrieved through the API.
    """
    # Create datafile
    user = api_client_with_credentials.handler._force_user
    new_data_file = DataFileFactory()
    new_data_file.deployment.owner = user
    new_data_file.save()
    check_key = 'species_name'
    payload = {"data_files": [new_data_file.pk],
               "source": "human", "species_name": "homo sapiens"}
    api_url = '/api/observation/'
    # New taxon
    api_check_post(api_client_with_credentials, api_url,
                   payload, check_key)

    # Existing taxon
    api_check_post(api_client_with_credentials, api_url,
                   payload, check_key)

    # Should now be
    assert new_data_file.observations.count() == 2

    assert Taxon.objects.filter(species_name='homo sapiens').count() == 1

    new_data_file.delete()


@pytest.mark.django_db
def test_update_obs(api_client_with_credentials):
    """
    Test: Can observation be updated and retrieved through the API.
    """
    user = api_client_with_credentials.handler._force_user
    new_data_file = DataFileFactory()
    new_data_file.deployment.owner = user
    new_data_file.save()
    new_taxon = TaxonFactory(species_name="vulpix")
    new_obs = ObservationFactory(taxon=new_taxon, data_files=[
                                 new_data_file], owner=user)
    check_key = 'species_name'
    api_url = f'/api/observation/{new_obs.pk}/'
    new_value = 'vulpes vulpes'
    api_check_update(api_client_with_credentials,
                     api_url, new_value, check_key)


@pytest.mark.django_db
def test_delete_obs(api_client_with_credentials):
    """
    Test: Can observation be delete through the API.
    """
    user = api_client_with_credentials.handler._force_user
    new_data_file = DataFileFactory()
    new_data_file.deployment.owner = user
    new_data_file.save()
    new_taxon = TaxonFactory(species_name="vulpix")
    new_obs = ObservationFactory(taxon=new_taxon, data_files=[
                                 new_data_file], owner=user)
    api_url = f'/api/observation/{new_obs.pk}/'

    api_check_delete(api_client_with_credentials,
                     api_url)
