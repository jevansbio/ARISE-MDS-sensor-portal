from django.db import connections
from django.db.models import Manager, QuerySet


class ApproximateCountQuerySet(QuerySet):
    """
    A QuerySet that provides an approximate count of the number of rows in a table.
    This is useful for large datasets where an exact count would be too expensive to compute.
    """

    def approx_count(self):

        cursor = connections[self.db].cursor()
        cursor.execute("SELECT reltuples FROM pg_class "
                       "WHERE relname = '%s';" % self.model._meta.db_table)

        return int(cursor.fetchone()[0])


ApproximateCountManager = Manager.from_queryset(ApproximateCountQuerySet)
