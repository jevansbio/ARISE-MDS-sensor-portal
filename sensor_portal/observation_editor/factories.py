from random import sample

import factory
from data_models.factories import DataFileFactory

from .models import Observation, Taxon


class TaxonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Taxon
        django_get_or_create = ("species_name",)

    species_name = factory.Faker('random_element',
                                 elements=["Homo sapiens",
                                           "Chroicocephalus ridibundus",
                                           "vehicle"])


class ObservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Observation

    taxon = factory.SubFactory(TaxonFactory)

    @factory.post_generation
    def data_files(self, create, extracted, **kwargs):
        if not create:
            # Simple build do nothing.
            return
        if extracted:
            for data_file in extracted:
                self.data_files.add(data_file)
        elif extracted is None:
            for i in range(sample(range(3), 1)[0]):
                self.data_files.add(DataFileFactory())
