from rest_framework import viewsets, generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Chat, Message, File, User
from .serializers import UserSerializer, ChatSerializer, MessageSerializer, ChatListSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class ChatListView(generics.ListAPIView):
    serializer_class = ChatListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user)

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['username', 'first_name', 'last_name', 'phone_number']
    ordering = ['username']
    search_fields = ['username', 'phone_number']

class CreateChatView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'شناسه کاربر الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'کاربر مورد نظر یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        chat = Chat.objects.create()
        chat.participants.add(request.user, other_user)

        return Response({'chat_id': chat.id}, status=status.HTTP_201_CREATED)

class AuthView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')

        if not phone_number or not otp:
            return Response({'error': 'شماره تلفن و کد OTP الزامی هستند.'}, status=status.HTTP_400_BAD_REQUEST)

        if otp != "12345":
            return Response({'error': 'کد OTP نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(phone_number=phone_number)

        if created:
            user.username = f"user_{phone_number}"
            user.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'phone_number': user.phone_number,
            'is_new_user': created
        }, status=status.HTTP_200_OK)

class SendMessageAPIView(APIView):
    def post(self, request):
        chat_id = request.data.get('chat_id')
        message_text = request.data.get('message')
        file = request.FILES.get('file')

        if not chat_id or (not message_text and not file):
            return Response({'error': 'chat_id و متن پیام یا فایل الزامی هستند'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat = Chat.objects.get(id=chat_id)
            message = Message.objects.create(
                chat=chat,
                sender=request.user,
                content=message_text or ''
            )

            if file:
                file_instance = File.objects.create(
                    message=message,
                    file=file,
                    file_name=file.name,
                    file_type=file.content_type
                )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_id}",
                {
                    "type": "chat_message",
                    "message": {
                        "id": message.id,
                        "sender": message.sender.username,
                        "content": message.content,
                        "file": file_instance.file.url if file else None,
                        "timestamp": message.timestamp.isoformat()
                    }
                }
            )

            return Response({'message_id': message.id}, status=status.HTTP_201_CREATED)
        except Chat.DoesNotExist:
            return Response({'error': 'چت مورد نظر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

class UserChatListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'کاربر مورد نظر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        chats = Chat.objects.filter(participants=request.user).filter(participants=other_user)

        if not chats.exists():
            return Response({'message': 'چتی بین شما و این کاربر وجود ندارد.'}, status=status.HTTP_204_NO_CONTENT)

        chat_list = []
        for chat in chats:
            chat_list.append({
                'chat_id': chat.id,
                'participants': [
                    {
                        'user_id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'phone_number': user.phone_number,
                        'profile_picture': user.profile_picture.url if user.profile_picture else None
                    } for user in chat.participants.all()
                ],
                'created_at': chat.created_at.isoformat()
            })

        other_user_info = {
            'user_id': other_user.id,
            'username': other_user.username,
            'first_name': other_user.first_name,
            'last_name': other_user.last_name,
            'phone_number': other_user.phone_number,
            'profile_picture': other_user.profile_picture.url if other_user.profile_picture else None
        }

        return Response({
            'other_user_info': other_user_info
        }, status=status.HTTP_200_OK)