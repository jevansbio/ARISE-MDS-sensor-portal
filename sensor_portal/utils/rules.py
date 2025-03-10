from bridgekeeper.rules import R
from django.db.models import Q


def final_query(accumulated_q):
    if len(accumulated_q) == 0:
        return Q(id=-1)
    else:
        return Q(accumulated_q)


def query_super(user):
    accumulated_q = Q()

    if user.is_superuser:
        return accumulated_q

    return None


def check_super(user):
    if user.is_superuser:
        return True

    return None


class IsOwner(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            return user == instance.owner

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            accumulated_q = Q(owner=user)
            return final_query(accumulated_q)
