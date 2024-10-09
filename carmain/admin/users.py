from sqladmin import ModelView

from carmain.models.users import User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username]
