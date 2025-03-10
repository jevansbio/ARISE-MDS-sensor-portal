from bridgekeeper.rules import R
from django.db.models import Q
from utils.rules import check_super, final_query, query_super


# PROJECT RULES
class IsManager(R):

    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            return user in instance.managers.all()

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            accumulated_q = Q(
                managers=user)
            return final_query(accumulated_q)


class IsAnnotator(R):

    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            return user in instance.annotators.all()

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            accumulated_q = Q(
                annotators=user)
            return final_query(accumulated_q)


class IsViewer(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            return user in instance.viewers.all()

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # in project group
            accumulated_q = Q(viewers=user)

            return final_query(accumulated_q)


class CanViewDeploymentInProject(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            # SHOULD EXIT SOONER.
            is_viewer = user.pk in instance.values_list(
                'project__viewers__pk', flat=True)
            is_annotator = user.pk in instance.values_list(
                'project__annotators__pk', flat=True)
            is_manager = user.pk in instance.values_list(
                'project__managers__pk', flat=True)
            is_owner = user.pk in instance.values_list(
                'project__owner__pk', flat=True)

            return any([is_viewer, is_annotator,  is_manager, is_owner])

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(project__viewers=user)
            accumulated_q = accumulated_q | Q(
                project__annotators=user)
            # manage
            accumulated_q = accumulated_q | Q(
                project__managers=user)
            # owner
            accumulated_q = accumulated_q | Q(project__owner=user)

        return final_query(accumulated_q)


class CanViewDeviceInProject(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_viewer = user.pk in instance.values_list(
                'deployments__project__viewers__pk', flat=True)
            is_annotator = user.pk in instance.values_list(
                'deployments__project__annotators__pk', flat=True)
            is_manager = user.pk in instance.values_list(
                'deployments__project__managers__pk', flat=True)
            is_owner = user.pk in instance.values_list(
                'deployments__project__owner__pk', flat=True)

            return any([is_viewer, is_annotator,  is_manager, is_owner])

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(deployments__project__viewers=user)
            # annotate
            accumulated_q = accumulated_q | Q(
                deployments__project__annotators=user)
            # manage
            accumulated_q = accumulated_q | Q(
                deployments__project__managers=user)
            # own
            accumulated_q = accumulated_q | Q(
                deployments__project__owner=user)

        return final_query(accumulated_q)


class CanViewProjectContainingDevice(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_viewer = user.pk in instance.values_list(
                "deployments__project__viewers__pk", flat=True)
            is_annotator = user.pk in instance.values_list(
                "deployments__project__annotator__pk", flat=True)
            is_manager = user.pk in instance.values_list(
                "deployments__project__managers__pk", flat=True)
            is_owner = user.pk in instance.values_list(
                "deployments__project__owner__pk", flat=True)

            return any([is_viewer, is_manager, is_owner])

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(deployments__project__viewers=user)
            # annotate
            accumulated_q = accumulated_q | Q(
                deployments__project__annotators=user)
            # manage
            accumulated_q = accumulated_q | Q(
                deployments__project__managers=user)
            # own
            accumulated_q = accumulated_q | Q(deployments__project__owner=user)

        return final_query(accumulated_q)


class CanManageProjectContainingDeployment(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_manager = user.pk in instance.project.all().values_list('managers__pk', flat=True)
            is_owner = user.pk in instance.project.all().values_list('owner__pk', flat=True)
            return any([is_manager, is_owner])

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            print(self)
            # can manage/own a deployment within project
            # manage
            accumulated_q = Q(project__managers=user)
            # own
            accumulated_q = accumulated_q | Q(project__owner=user)

        return final_query(accumulated_q)


class CanViewProjectContainingDeployment(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            return user.pk in instance.project.all().values_list("viewers__pk", flat=True)

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(project__viewers=user) | Q(
                project__annotators=user)

        return final_query(accumulated_q)


class CanManageDeployedDevice(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)
        if initial_bool is not None:
            return initial_bool
        else:
            is_manager = user in instance.device.managers.all()
            is_owner = user.pk == instance.device.owner

            return any([is_manager, is_owner])

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # manage
            accumulated_q = Q(device__managers=user)
            # own
            accumulated_q = accumulated_q | Q(device__owner=user)
        return final_query(accumulated_q)


class CanViewDeployedDevice(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_viewer = user in instance.device.viewers.all()
            is_annotator = user in instance.device.annotators.all()
            return any([is_viewer, is_annotator])

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(device__viewers=user) | Q(
                device__annotators=user)

        return final_query(accumulated_q)


class CanManageProjectContainingDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_manager = user.pk in instance.deployment.project.all().values_list(
                "managers__pk", flat=True)
            is_owner = user.pk in instance.deployment.project.all().values_list(
                "owner__pk", flat=True)

            return any([is_manager, is_owner])

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(deployment__project__managers=user)
            # own
            accumulated_q = accumulated_q | Q(deployment__project__owner=user)

        return final_query(accumulated_q)


class CanAnnotateProjectContainingDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:

            is_annotator = user.pk in instance.deployment.project.all().values_list(
                "annotators__pk", flat=True)
            return is_annotator

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(
                deployment__project__annotators=user)

        return final_query(accumulated_q)


class CanViewProjectContainingDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_viewer = user.pk in instance.deployment.project.all().values_list(
                "viewers__pk", flat=True)

            return is_viewer

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(deployment__project__viewers=user)

        return final_query(accumulated_q)


class CanManageDeploymentContainingDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_manager = user.pk in instance.deployment.managers.all().values_list("pk",
                                                                                   flat=True)
            is_owner = user == instance.deployment.owner

            return any([is_manager, is_owner])

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(deployment__managers=user)
            # own
            accumulated_q = accumulated_q | Q(deployment__owner=user)

        return final_query(accumulated_q)


class CanAnnotateDeploymentContainingDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_annotator = user.pk in instance.deployment.annotators.all().values_list(
                "pk", flat=True)
            return is_annotator

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(
                deployment__annotators=user)

        return final_query(accumulated_q)


class CanViewDeploymentContainingDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:

            is_viewer = user.pk in instance.deployment.viewers.all().values_list(
                "pk", flat=True)

            return is_viewer

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(deployment__viewers=user)

        return final_query(accumulated_q)


class CanManageDeviceContainingDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_manager = user.pk in instance.deployment.device.managers.all()\
                .values_list(
                "pk", flat=True)
            is_owner = user == instance.deployment.device.owner

            return any([is_manager, is_owner])

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(deployment__device__managers=user)
            # own
            accumulated_q = accumulated_q | Q(deployment__device__owner=user)

        return final_query(accumulated_q)


class CanAnnotateDeviceContainingDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:

            is_annotator = user.pk in instance.deployment.device.annotators.all().values_list(
                "pk", flat=True)
            return is_annotator

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(
                deployment__device__annotators=user)

        return final_query(accumulated_q)


class CanViewDeviceContainingDataFile(R):
    def check(self, user, instance=None):
        initial_bool = check_super(user)

        if initial_bool is not None:
            return initial_bool
        else:
            is_viewer = user.pk in instance.deployment.device.viewers.all().values_list(
                "pk", flat=True)
            return is_viewer

    def query(self, user):
        accumulated_q = query_super(user)

        if accumulated_q is not None:
            return accumulated_q
        else:
            # can view/manage/own a deployment within project
            # view
            accumulated_q = Q(deployment__device__viewers=user)

        return final_query(accumulated_q)
