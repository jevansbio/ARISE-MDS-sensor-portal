from bridgekeeper import perms
from bridgekeeper.rules import always_allow, is_active, is_authenticated, is_superuser

from .rules import is_user

perms['user_management.view_user'] = is_authenticated & is_active
perms['user_management.add_user'] = always_allow
perms['user_management.delete_user'] = is_superuser
perms['user_management.edit_user'] = is_superuser | is_user
