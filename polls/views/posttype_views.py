from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import PostType
from ..serializers import PostTypeSerializer

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def posttype_list(request):
    if request.method == 'GET':
        types = PostType.objects.all()
        serializer = PostTypeSerializer(types, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = PostTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PUT':
        pk = request.data.get('id')
        try:
            post_type = PostType.objects.get(pk=pk)
        except PostType.DoesNotExist:
            return Response({"error": "PostType not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = PostTypeSerializer(post_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        pk = request.data.get('id')
        try:
            post_type = PostType.objects.get(pk=pk)
        except PostType.DoesNotExist:
            return Response({"error": "PostType not found"}, status=status.HTTP_404_NOT_FOUND)
        post_type.delete()
        return Response({"message": "PostType deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
