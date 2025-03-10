from celery import shared_task

from .GBIF_functions import (GBIF_get_or_create_taxon_object_from_taxon_code,
                             GBIF_get_species, GBIF_get_taxoncodes)


@shared_task()
def create_taxon_parents(taxon_pk):
    from .models import Taxon

    taxon_object = Taxon.objects.get(pk=taxon_pk)
    print(f"Check parents {taxon_object.species_name}")
    species_data = GBIF_get_species(taxon_object.taxon_code)
    all_taxon_codes = GBIF_get_taxoncodes(species_data)
    print(all_taxon_codes)
    all_parents = []
    if len(all_taxon_codes) > 1:
        for i in range(1, len(all_taxon_codes)):
            parent_taxon_obj, created = GBIF_get_or_create_taxon_object_from_taxon_code(
                all_taxon_codes[i][0])
            all_parents.append(parent_taxon_obj)
            if created:
                print(f"Create {parent_taxon_obj.species_name}")

        taxon_object.parents.set(all_parents)
        print(f"Set parents {taxon_object.species_name}")
