from django.contrib.auth import get_user_model

UserModel = get_user_model()

class EmailOrUsernameBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        user = None
        try:
            # Primeiro tenta username
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # Se tiver @ tenta como email
            if "@" in username:
                try:
                    user = UserModel.objects.get(email=username)
                except UserModel.DoesNotExist:
                    return None
            else:
                return None
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None