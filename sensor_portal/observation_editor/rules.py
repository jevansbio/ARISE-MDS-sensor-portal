from bridgekeeper import perms
from bridgekeeper.rules import R, always_allow
from data_models.models import DataFile
from django.db.models import Q
from utils.rules import check_super, final_query, query_super
from .models import Observation


class CanViewObservationDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)
        if initial_bool is not None:
            return initial_bool
        else:
            return perms['data_models.view_datafile'].filter(
                user, instance.data_files.all()).exists()

    def query(self, user):
        accumulated_q = query_super(user)
        if accumulated_q is not None:
            return accumulated_q
        else:
            accumulated_q = Q(data_files__in=perms['data_models.view_datafile'].filter(
                user, DataFile.objects.filter(observations__isnull=False)))
            return final_query(accumulated_q)

# Define permission to view observations
perms['observation_editor.view_observation'] = always_allow

# Define permission to change observations - allow everyone to edit
perms['observation_editor.change_observation'] = always_allow

# Define permission to delete observations - allow everyone to delete
perms['observation_editor.delete_observation'] = always_allow

# Define permission to view taxa - allow everyone to view
perms['observation_editor.view_taxon'] = always_allow
