from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from ..serializers import AdaptdocxClientNotesSerializer
from rest_framework import status
from rest_framework.response import Response
from .backend_logic import insert_record_matter, insert_record_phone
from ..models import AdaptdocxClientNotes
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from django.db.models import Q
from datetime import date

@swagger_auto_schema(method='POST', request_body=AdaptdocxClientNotesSerializer)
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def add_client_notes(request):
    serializer = AdaptdocxClientNotesSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Add Client notes successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
    return Response({'message': f'Error {serializer.errors}', 'data': None}, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_client_notes(request):
    obj = AdaptdocxClientNotes.objects.all()
    ser = AdaptdocxClientNotesSerializer(obj,many=True)
    return Response({'message': 'Client notes Data', 'data': ser.data}, status=status.HTTP_200_OK)