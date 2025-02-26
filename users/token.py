from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def get_token(self, user):
        token = super().get_token(user)

        # Add custom claims
        token["is_staff"] = user.is_staff  # ✅ Now JWT includes is_staff
        token["is_superuser"] = user.is_superuser  # (Optional)

        return token
