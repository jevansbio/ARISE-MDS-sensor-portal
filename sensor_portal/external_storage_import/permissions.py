from bridgekeeper import perms
from bridgekeeper.rules import is_active, is_authenticated, is_staff
from utils.rules import IsOwner

# or is linked to a project of which a user is a manager/owner.
perms['external_storage_import.view_datastorageinput'] = is_staff | (
    is_authenticated & is_active & IsOwner())
perms['data_models.add_datastorageinput'] = is_staff | (
    is_authenticated & is_active)
perms['data_models.change_datastorageinput'] = is_staff | (
    is_authenticated & is_active & IsOwner())
perms['data_models.delete_datastorageinput'] = is_staff | (
    is_authenticated & is_active & IsOwner())
