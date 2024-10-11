from sqladmin import ModelView

from carmain.models.auth import AccessToken
from carmain.models.users import User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email]


class AccessTokenAdmin(ModelView, model=AccessToken):
    column_list = [AccessToken.user_id, AccessToken.token, AccessToken.data]
