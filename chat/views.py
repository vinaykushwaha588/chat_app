from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework import status
from django.utils.timezone import now
from .models import *
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from .models import User
from datetime import datetime
from django.db.models import Q

class UserCreateView(CreateAPIView):
    """
        This API is used for the register a new user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'success': True, 'message': "User Created Successfully."}, status=status.HTTP_201_CREATED, headers=headers)


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.last_login = now()
            user.save(update_fields=['last_login'])
            return Response(
                {
                    'success': True,
                    'message': 'Login successful',
                    'token': user.tokens()
                },
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AuthViewSet(ViewSet):
    """
        ViewSet for user authentication including:
        - Logout (blacklisting refresh token)
        - Refresh access token
    """
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
            Blacklists the given refresh token to log out the user.
        """
        token = request.data.get('refresh_token')
        user = request.user
        current_time = datetime.now()

        if not token:
            return Response({"success": False, "message": "Refresh Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(token)
            refresh.blacklist()
            user.last_logout = current_time
            user.save()
            return Response({"success": True, "message": "User logged out successfully."}, status=status.HTTP_200_OK)

        except TokenError:
            return Response({"success": False, "message": "Invalid or expired refresh token."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def refresh_token(self, request):
        """
            Generates a new access token using a valid refresh token.
        """
        token = request.data.get('refresh_token')
       

        if not token:
            return Response({"success": False, "message": "Refresh Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(token)
            new_access_token = str(refresh.access_token)

            return Response({
                "success": True,
                "access_token": new_access_token
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response({"success": False, "message": "Invalid or expired refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'])
    def user_list(self, request):
        users = User.objects.all().exclude(is_superuser=True)
        serializer = UserSerializer(list(users), many=True).data  
        return Response({'success': True, 'data': serializer}, status=status.HTTP_200_OK)




class PrivateChatListCreateView(generics.ListCreateAPIView):
    """
    Lists all private chats of the logged-in user and allows creating a new chat.
    """
    serializer_class = PrivateChatSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return PrivateChat.objects.filter(user1=self.request.user) | PrivateChat.objects.filter(user2=self.request.user)


class ConversationMessageListCreateView(generics.ListCreateAPIView):
    """
        Lists all messages between the logged-in user and another user,
        and allows sending a new message.
    """
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        other_user_id = self.kwargs['user_id']
        return Message.objects.filter(
            Q(sender=self.request.user, receiver_id=other_user_id) |
            Q(sender_id=other_user_id, receiver=self.request.user)
        )

    def perform_create(self, serializer):
        other_user_id = self.kwargs['user_id']
        other_user = get_object_or_404(User, pk=other_user_id)
        serializer.save(sender=self.request.user, receiver=other_user)



"""
    Elastic Search
"""
from django.http import JsonResponse
from chat.elastic import FakeUserDocument

def search_users(request):
    query = request.GET.get('q', '')

    if not query:
        return JsonResponse({'error': 'Please provide a search query'}, status=400)

    search_results = FakeUserDocument.search().query(
        "multi_match",
        query=query,
        fields=["first_name", "last_name", "email", "phone"]
    )

    results = [{"first_name": hit.first_name, "last_name": hit.last_name, "email": hit.email, "phone": hit.phone, "gender": hit.gender} for hit in search_results]

    return JsonResponse({"results": results})
