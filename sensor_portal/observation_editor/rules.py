from bridgekeeper import perms
from bridgekeeper.rules import R
from data_models.models import DataFile
from django.db.models import Q
from utils.rules import check_super, final_query, query_super


class CanViewObservationDataFile(R):
    """
    Rule to check if a user can view the data files associated with an observation.
    """

    def check(self, user, instance=None):

        return perms['data_models.view_datafile'].filter(
            user, instance.data_files.all()).exists()

    def query(self, user):

        accumulated_q = Q(data_files__in=perms['data_models.view_datafile'].filter(
            user, DataFile.objects.filter(observations__isnull=False)))

        return final_query(accumulated_q)
