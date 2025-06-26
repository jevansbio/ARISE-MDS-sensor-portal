from bridgekeeper.rules import R
from django.conf import settings
from django.db.models import Q
from utils.rules import check_super, final_query, query_super


class IsManager(R):
    """
    Rule for checking if a user is a manager of a given instance.
    """

    def check(self, user, instance=None):
        """
        Check if the user is a manager of the instance.

        Parameters
        ----------
        user : User
            The user to check.
        instance : Model, optional
            The instance to check against.

        Returns
        -------
        bool
            True if user is a manager, False otherwise.
        """
        return user in instance.managers.all()

    def query(self, user):
        """
        Construct a query to filter instances managed by the user.

        Parameters
        ----------
        user : User
            The user to filter by.

        Returns
        -------
        Q
            Query for filtering managed instances.
        """
        accumulated_q = Q(managers=user)
        return final_query(accumulated_q)


class IsAnnotator(R):
    """
    Rule for checking if a user is an annotator for a given instance.
    """

    def check(self, user, instance=None):
        """
        Check if the user is an annotator for the instance.

        Parameters
        ----------
        user : User
            The user to check.
        instance : Model, optional
            The instance to check against.

        Returns
        -------
        bool
            True if user is an annotator, False otherwise.
        """
        return user in instance.annotators.all()

    def query(self, user):
        """
        Construct a query to filter instances where user is an annotator.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
            Query for filtering instances.
        """
        accumulated_q = Q(annotators=user)
        return final_query(accumulated_q)


class IsViewer(R):
    """
    Rule for checking if a user is a viewer of a given instance.
    """

    def check(self, user, instance=None):
        """
        Check if the user is a viewer for the instance.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user in instance.viewers.all()

    def query(self, user):
        """
        Construct a query for viewer access.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(viewers=user)
        return final_query(accumulated_q)


class CanViewDeploymentInProject(R):
    """
    Rule for determining if a user can view a deployment within a project.
    """

    def check(self, user, instance=None):
        """
        Check if the user can view the deployment via project roles.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return (
            user.pk in instance.project.viewers.values_list('pk', flat=True)
            or user.pk in instance.project.annotators.values_list('pk', flat=True)
            or user.pk in instance.project.managers.values_list('pk', flat=True)
            or user.pk == instance.project.owner.pk
        )

    def query(self, user):
        """
        Construct a query for deployments the user can view via project roles.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = (
            Q(project__viewers=user)
            | Q(project__annotators=user)
            | Q(project__managers=user)
            | Q(project__owner=user)
        )
        return final_query(accumulated_q)


class CanViewDeviceInProject(R):
    """
    Rule for determining if a user can view a device within a project.
    """

    def check(self, user, instance=None):
        """
        Check if the user can view the device via project roles.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return (
            user.pk in instance.values_list(
                'deployments__project__viewers__pk', flat=True)
            or user.pk in instance.values_list('deployments__project__annotators__pk', flat=True)
            or user.pk in instance.values_list('deployments__project__managers__pk', flat=True)
            or user.pk in instance.values_list('deployments__project__owner__pk', flat=True)
        )

    def query(self, user):
        """
        Construct a query for devices the user can view via project roles.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = (
            Q(deployments__project__viewers=user)
            | Q(deployments__project__annotators=user)
            | Q(deployments__project__managers=user)
            | Q(deployments__project__owner=user)
        )
        return final_query(accumulated_q)


class CanViewProjectContainingDevice(R):
    """
    Rule for determining if a user can view a project containing a device.
    """

    def check(self, user, instance=None):
        """
        Check if the user can view the project via device deployments.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return (
            user.pk in instance.values_list(
                "deployments__project__viewers__pk", flat=True)
            or user.pk in instance.values_list("deployments__project__annotator__pk", flat=True)
            or user.pk in instance.values_list("deployments__project__managers__pk", flat=True)
            or user.pk in instance.values_list("deployments__project__owner__pk", flat=True)
        )

    def query(self, user):
        """
        Construct a query for devices in projects the user can access.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = (
            Q(deployments__project__viewers=user)
            | Q(deployments__project__annotators=user)
            | Q(deployments__project__managers=user)
            | Q(deployments__project__owner=user)
        )
        return final_query(accumulated_q)


class CanManageProjectContainingDeployment(R):
    """
    Rule for determining if a user can manage or own a project containing a deployment.
    """

    def check(self, user, instance=None):
        """
        Check if the user is a manager or owner of the deployment's project.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return (
            user.pk in instance.project.all().values_list('managers__pk', flat=True)
            or user.pk in instance.project.all().values_list('owner__pk', flat=True)
        )

    def query(self, user):
        """
        Construct a query for deployments user can manage or own.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(project__managers=user) | Q(project__owner=user)
        return final_query(accumulated_q)


class CanViewProjectContainingDeployment(R):
    """
    Rule for determining if a user can view a project containing a deployment.
    """

    def check(self, user, instance=None):
        """
        Check if the user can view the deployment's project.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user.pk in instance.project.all().values_list("viewers__pk", flat=True)

    def query(self, user):
        """
        Construct a query for deployments in projects the user can view or annotate.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(project__viewers=user) | Q(project__annotators=user)
        return final_query(accumulated_q)


class CanManageDeployedDevice(R):
    """
    Rule for determining if a user can manage a deployed device.
    """

    def check(self, user, instance=None):
        """
        Check if the user can manage the deployed device.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user in instance.device.managers.all() or user.pk == instance.device.owner

    def query(self, user):
        """
        Construct a query for deployed devices user can manage.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(device__managers=user) | Q(device__owner=user)
        return final_query(accumulated_q)


class CanViewDeployedDevice(R):
    """
    Rule for determining if a user can view a deployed device.
    """

    def check(self, user, instance=None):
        """
        Check if the user can view the deployed device.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user in instance.device.viewers.all() or user in instance.device.annotators.all()

    def query(self, user):
        """
        Construct a query for deployed devices user can view.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(device__viewers=user) | Q(device__annotators=user)
        return final_query(accumulated_q)


class CanManageDataFileDeployment(R):
    """
    Rule for determining if a user can manage a data file deployment.
    """

    def check(self, user, instance=None):
        """
        Check if the user is a manager of the data file deployment.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user in instance.deployment.managers.all()

    def query(self, user):
        """
        Construct a query for data file deployments user can manage.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(deployment__managers=user)
        return final_query(accumulated_q)


class CanAnnotateDataFileDeployment(R):
    """
    Rule for determining if a user can annotate a data file deployment.
    """

    def check(self, user, instance=None):
        """
        Check if the user is an annotator of the data file deployment.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user in instance.deployment.annotators.all()

    def query(self, user):
        """
        Construct a query for data file deployments user can annotate.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(deployment__annotators=user)
        return final_query(accumulated_q)


class CanViewDataFileDeployment(R):
    """
    Rule for determining if a user can view a data file deployment.
    """

    def check(self, user, instance=None):
        """
        Check if the user can view the data file deployment.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user in instance.deployment.viewers.all()

    def query(self, user):
        """
        Construct a query for data file deployments user can view.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(deployment__viewers=user)
        return final_query(accumulated_q)


class CanManageProjectContainingDataFile(R):
    """
    Rule for determining if a user can manage a project containing a specific data file.
    """

    def check(self, user, instance=None):
        """
        Check if the user is a manager or owner of the project containing the data file.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return (
            user.pk in instance.deployment.project.all().values_list("managers__pk", flat=True)
            or user.pk in instance.deployment.project.all().values_list("owner__pk", flat=True)
        )

    def query(self, user):
        """
        Construct a query for projects containing data files user can manage.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(deployment__project__managers=user) | Q(
            deployment__project__owner=user)
        return final_query(accumulated_q)


class CanAnnotateProjectContainingDataFile(R):
    """
    Rule for determining if a user can annotate a project containing a specific data file.
    """

    def check(self, user, instance=None):
        """
        Check if the user is an annotator for the project containing the data file.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user.pk in instance.deployment.project.all().values_list("annotators__pk", flat=True)

    def query(self, user):
        """
        Construct a query for projects containing data files user can annotate.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(deployment__project__annotators=user)
        return final_query(accumulated_q)


class CanViewProjectContainingDataFile(R):
    """
    Rule for determining if a user can view a project containing a specific data file.
    """

    def check(self, user, instance=None):
        """
        Check if the user can view the project containing the data file.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user.pk in instance.deployment.project.all().values_list("viewers__pk", flat=True)

    def query(self, user):
        """
        Construct a query for projects containing data files user can view.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(deployment__project__viewers=user)
        return final_query(accumulated_q)


class CanManageDeviceContainingDataFile(R):
    """
    Rule for determining if a user can manage a device containing a data file.
    """

    def check(self, user, instance=None):
        """
        Check if the user is the owner or a manager of the device containing the data file.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return (
            user == instance.deployment.device.owner
            or user in instance.deployment.device.managers.all().values_list("pk", flat=True)
        )

    def query(self, user):
        """
        Construct a query for devices containing data files user can manage.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(deployment__device__managers=user) | Q(
            deployment__device__owner=user)
        return final_query(accumulated_q)


class CanAnnotateDeviceContainingDataFile(R):
    """
    Rule for determining if a user can annotate a device containing a data file.
    """

    def check(self, user, instance=None):
        """
        Check if the user is an annotator of the device containing the data file.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user.pk in instance.deployment.device.annotators.all().values_list("pk", flat=True)

    def query(self, user):
        """
        Construct a query for devices containing data files user can annotate.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(deployment__device__annotators=user)
        return final_query(accumulated_q)


class CanViewDeviceContainingDataFile(R):
    """
    Rule for determining if a user can view a device containing a specific data file.
    """

    def check(self, user, instance=None):
        """
        Check if the user can view the device containing the data file.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return user.pk in instance.deployment.device.viewers.all().values_list("pk", flat=True)

    def query(self, user):
        """
        Construct a query for devices containing data files user can view.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(deployment__device__viewers=user)
        return final_query(accumulated_q)


class DataFileHasNoHuman(R):
    """
    Rule for determining if a data file does not contain human-related data.
    """

    def check(self, user, instance=None):
        """
        Check if the data file does not contain human data.

        Parameters
        ----------
        user : User
        instance : Model, optional

        Returns
        -------
        bool
        """
        return not instance.has_human

    def query(self, user):
        """
        Construct a query for data files without human data.

        Parameters
        ----------
        user : User

        Returns
        -------
        Q
        """
        accumulated_q = Q(has_human=False)
        return final_query(accumulated_q)
