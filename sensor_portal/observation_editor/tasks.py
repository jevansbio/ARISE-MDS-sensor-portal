import logging

from celery import shared_task
from requests.exceptions import ConnectionError, ConnectTimeout

from sensor_portal.celery import app

from .GBIF_functions import (GBIF_get_or_create_taxon_object_from_taxon_code,
                             GBIF_get_species, GBIF_get_taxoncodes)

logger = logging.getLogger(__name__)


@app.task()
def create_taxon_parents(taxon_pk):
    """
    Generate and set parent taxon objects for a given taxon.

    Args:
        taxon_pk (_type_): Primary key of the taxon object to process.
    """
    from .models import Taxon

    taxon_object = Taxon.objects.get(pk=taxon_pk)
    logger.info(f"Check parents {taxon_object.species_name}")
    try:
        species_data = GBIF_get_species(taxon_object.taxon_code)
        all_taxon_codes = GBIF_get_taxoncodes(species_data)
    except ConnectionError or ConnectTimeout as e:
        logger.error(e)
        return

    all_parents = []
    if len(all_taxon_codes) > 1:
        for i in range(1, len(all_taxon_codes)):
            try:
                parent_taxon_obj, created = GBIF_get_or_create_taxon_object_from_taxon_code(
                    all_taxon_codes[i][0])
            except ConnectionError or ConnectTimeout as e:
                logger.error(e)
                return

            all_parents.append(parent_taxon_obj)
            if created:
                logger.info(f"Create {parent_taxon_obj.species_name}")

        taxon_object.parents.set(all_parents)
        logger.info(f"Set parents {taxon_object.species_name}")
