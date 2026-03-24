# In your application code
import sqlite3


from src.application.services.role_admin_service import RoleServiceFactory
from src.domain.rbac.permissions import UserPermission, AdminPermission
from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection

# Initialize
connection=Connection.create_connection(url="../../db/admins.db", engine=sqlite3)
uow = SQLiteUnitOfWork(connection)
service_factory = RoleServiceFactory(uow)

# Use admin role service
admin_service = service_factory.admin_service()

# ✅ Create admin role - type safe
admin_role = admin_service.create_role(
    name="Super Admin",
    permissions={
        AdminPermission.VIEW_ADMIN,
        AdminPermission.ASSIGN_ROLE,
        AdminPermission.VIEW_AUDIT_LOG,
        AdminPermission.UPDATE_ADMIN,
        AdminPermission.REVOKE_ROLE
    },
    description="Full system access",
    is_system_role=True,
)

# ❌ This won't compile - type error!
# admin_role = admin_service.create_role(
#     name="Wrong Role",
#     permissions={UserPermission.CREATE_TICKET},  # Type error!
# )

# Use user role service
user_service = service_factory.user_service()

# ✅ Create user role
user_role = user_service.create_role(
    name="Ticket Creator",
    permissions={
        UserPermission.CREATE_TICKET,
        UserPermission.VIEW_OWN_TICKET,
    },
    description="Can create and view own tickets",
)

# Get roles
all_admin_roles = admin_service.get_all_roles()
all_user_roles = user_service.get_all_roles()
print(all_admin_roles)
print(all_user_roles)
# Delete a role
#admin_service.delete_role(admin_role.role_id)

# Or use generic service if needed
#generic_service = service_factory.generic_service()
#role = generic_service.get_role(1, AdminPermission)