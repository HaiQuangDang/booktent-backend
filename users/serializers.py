from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile
from rest_framework.validators import UniqueValidator

class ProfileSerializer(serializers.ModelSerializer):
    # avatar = serializers.ImageField(required=False)  # Allow file uploads
    class Meta:
        model = Profile
        fields = ["avatar", "address", "phone_number"]  # ✅ Added phone_number

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This email has been used." 
            )]
    )
    current_password = serializers.CharField(write_only=True, required=False)  # Current password (optional)
    password = serializers.CharField(write_only=True, required=False)  # New password (optional)

    class Meta:
        model = User
        fields = ["id", "username", "password", "current_password", "email", "is_staff", "is_superuser", "profile"]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
        }

    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {})
        user = User.objects.create_user(**validated_data)
        
        # Create or update profile
        Profile.objects.get_or_create(user=user)
        if "avatar" in profile_data:
            user.profile.avatar = profile_data["avatar"]
        if "address" in profile_data:
            user.profile.address = profile_data["address"]
        if "phone_number" in profile_data:  # ✅ Add phone_number on creation
            user.profile.phone_number = profile_data["phone_number"]
        user.profile.save()
        
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})

        # Update username and email
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)

        # Handle password change (only if both new password and current password are provided)
        current_password = validated_data.pop("current_password", None)
        new_password = validated_data.pop("password", None)
        
        if new_password:
            if not current_password or not instance.check_password(current_password):
                raise serializers.ValidationError({"current_password": "Current password is incorrect."})
            instance.set_password(new_password)

        instance.save()

        # Update profile fields if provided
        if "avatar" in profile_data:
            instance.profile.avatar = profile_data["avatar"]
        if "address" in profile_data:
            instance.profile.address = profile_data["address"]
        if "phone_number" in profile_data:  # ✅ Add phone_number on update
            instance.profile.phone_number = profile_data["phone_number"]
        
        if profile_data:
            instance.profile.save()

        return instance
