from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .pagination import UsersPagination
from .serializers import AvatarSerializer


User = get_user_model()

class CustomUserViewSet(UserViewSet):
    pagination_class = UsersPagination

    def get_queryset(self):
        return User.objects.all()

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar')
    def set_or_delete_avatar(self, request):
        if request.method == 'PUT':
            serializers = AvatarSerializer(
                instance=request.user,
                data=request.data,
                partial=True
            )
            serializers.is_valid(raise_exception=True)
            serializers.save()
            return Response(serializers.data, status=status.HTTP_200_OK)
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'me':
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()
