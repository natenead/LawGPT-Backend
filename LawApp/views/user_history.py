from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from .general_utils import *
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from ..models import Depositionhistorytopics, Depositionhistoryquestions

@swagger_auto_schema(method='GET',manual_parameters=[openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True), ])
@api_view(['GET'])
# @authentication_classes([])
@permission_classes([])
def get_ai_councel_history(request):
    botid = request.query_params.get('botid')
    dep_topic_data = Depositionhistorytopics.objects.filter(botid=botid).select_related()


    if dep_topic_data:
        return Response({'message': "Topics Generated Successfully", "data": dep_topic_data}, status=status.HTTP_200_OK)
    else:
        return Response({'message': "Request Failed!", "data": []}, status=status.HTTP_400_BAD_REQUEST)
