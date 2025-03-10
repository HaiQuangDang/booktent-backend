from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile
from rest_framework.validators import UniqueValidator

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["avatar", "address"]  # Added address

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This email has been used." 
            )]  # Enforce unique email
    )

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "is_staff", "is_superuser", "profile"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {})
        print(validated_data, profile_data)  # Debugging output
        user = User.objects.create_user(**validated_data)
        
        # Create or update the profile with avatar and address if provided
        Profile.objects.get_or_create(user=user)
        if "avatar" in profile_data:
            user.profile.avatar = profile_data["avatar"]
        if "address" in profile_data:
            user.profile.address = profile_data["address"]
        user.profile.save()
        
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
        instance.save()

        # Update avatar and address if provided
        if "avatar" in profile_data:
            instance.profile.avatar = profile_data["avatar"]
        if "address" in profile_data:
            instance.profile.address = profile_data["address"]
        if profile_data:  # Only save if there’s data to update
            instance.profile.save()

        return instance