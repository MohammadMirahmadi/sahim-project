from rest_framework import serializers
from .models import User, Chat, Message, File
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'phone_number', 'profile_picture']

class ChatSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'participants', 'created_at']

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'file', 'file_name', 'file_type', 'uploaded_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'content', 'timestamp', 'is_read', 'files']

class ChatListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'other_participant', 'last_message', 'created_at']

    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        return MessageSerializer(last_message).data if last_message else None

    def get_other_participant(self, obj):
        request = self.context.get('request')
        other_user = obj.participants.exclude(id=request.user.id).first()
        return UserSerializer(other_user).data if other_user else None

class AuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=5)

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError("شماره تلفن باید ۱۱ رقم باشد.")
        return value

    def validate_otp(self, value):
        if not value.isdigit() or len(value) != 5:
            raise serializers.ValidationError("کد OTP باید ۵ رقم باشد.")
        return value

class AuthResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    user_id = serializers.IntegerField()
    phone_number = serializers.CharField()
    is_new_user = serializers.BooleanField()