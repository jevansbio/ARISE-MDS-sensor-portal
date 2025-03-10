import pytest
from data_models.factories import DataFileFactory
from observation_editor.factories import ObservationFactory, TaxonFactory
from observation_editor.tasks import create_taxon_parents


@pytest.mark.django_db
def test_taxon_create():
    """
    Test: On taxon creation, is a GBIF taxon code found. 
    """
    new_taxon = TaxonFactory(
        species_name="homo sapiens"
    )

    assert new_taxon.taxon_code == 2436436

    assert new_taxon.taxon_source == 1

    assert new_taxon.species_common_name.lower() == "human"


@pytest.mark.django_db
def test_taxon_parent_create():
    """
    Test: Are parent taxons created and correct?
    """
    new_taxon = TaxonFactory(
        species_name="homo sapiens"
    )

    create_taxon_parents(new_taxon.pk)

    assert new_taxon.parents.exists()

    assert new_taxon.parents.all().filter(species_name="Animalia").exists()


@pytest.mark.django_db
def test_custom_taxon():
    """
    Test: Are non GBIF taxons handled correctly?
    """
    new_taxon = TaxonFactory(
        species_name="vehicle"
    )

    assert new_taxon.taxon_source == 0


@pytest.mark.django_db
def test_observation_create():
    """
    Test: Are observation labels and defaults generated from datafiles correctly.
    """
    new_taxon = TaxonFactory(species_name="homo sapiens")
    new_data_file = DataFileFactory.create()
    new_observation = ObservationFactory(taxon=new_taxon,
                                         data_files=[new_data_file]
                                         )
    # assert label
    assert "sapiens" in new_observation.label

    assert new_observation.obs_dt == new_data_file.recording_dt

    new_data_file.delete()
