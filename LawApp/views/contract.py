from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from .general_utils import *
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from langchain.embeddings import HuggingFaceEmbeddings
from ..models import Uploadeddocumenthistory
from ..utils import getOpenAIKey,check_number_of_queries,is_user_able_to_query
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from .qdrant_ops import *
embed_fn = HuggingFaceEmbeddings(model_name=os.getenv("model_name"))

embed_fn_qdrant = HuggingFaceEmbeddings(model_name=os.getenv("model_name_qdrant"))

@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True), ]
                     )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])

def review_contract_compliance(request):
    try:
        # userid = request.user.pk
        # file = request.FILES.get('file')
        # contents = file.read()
        #
        # file_extension = file.name[-4:].lower()
        # original_filename = file.name
        #
        # doc_list = handling_files(contents, file_extension, original_filename)
        #
        # collection_name = str(file.file) + "_" + str(userid) + "_contract_review_automation _" + str(datetime.now())
        # collection_name = collection_name.replace(":", "_")
        #
        # url = "https://c0f04618-5c68-4005-be2a-b1d1b96d1f59.us-east-1-0.aws.cloud.qdrant.io:6333"
        # qd_api_key = "bQD_ZilrNEyygefhichfbEXOKdGz0xqScuYaUnxMR-MaAVU7_4A9FA"
        #
        # contract_review_automation_db = create_new_vectorstore_qdrant(doc_list, embed_fn, collection_name, url, qd_api_key)
        botid = request.query_params.get('botid')
        uploaded_data = Uploadeddocumenthistory.objects.get(botid=botid)
        db = load_local_vectordb_using_qdrant(uploaded_data.collectionname, embed_fn)
        if not db:
            return Response({"message": "Your Document is deleted."}, status=status.HTTP_400_BAD_REQUEST)
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request, 1, 0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        response = semantic_search_on_contract_review_automation(db,open_ai_key)

        return Response({"message": "Response Generated Successfully!", "Response": response}, status=status.HTTP_200_OK)

    except Exception as ex:
        return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True), ]
                     )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def contract_compliance(request):
    try:
        num_query = check_number_of_queries(request)
        if num_query == 2:
            return Response({'message': "Please Subscribe", "data": []}, status=status.HTTP_402_PAYMENT_REQUIRED)
        elif num_query == 3:
            return Response({'message': "Please Enter Your Own API Key", "data": []},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        elif num_query == 1:
            pass
        # userid = request.user.pk
        # file = request.FILES.get('file')
        # contents = file.read()
        #
        # file_extension = file.name[-4:].lower()
        # original_filename = file.name
        #
        # doc_list = handling_files(contents, file_extension, original_filename)
        #
        # collection_name = str(file.name) + "_" + str(userid) + "_contract_compliance_" + str(datetime.now())
        # collection_name = collection_name.replace(":", "_")
        #
        # url = "https://c0f04618-5c68-4005-be2a-b1d1b96d1f59.us-east-1-0.aws.cloud.qdrant.io:6333"
        # qd_api_key = "bQD_ZilrNEyygefhichfbEXOKdGz0xqScuYaUnxMR-MaAVU7_4A9FA"
        #
        # contract_compliance_db = create_new_vectorstore_qdrant(doc_list, embed_fn, collection_name, url, qd_api_key)
        botid = request.query_params.get('botid')
        uploaded_data = Uploadeddocumenthistory.objects.get(botid=botid)

        db = load_local_vectordb_using_qdrant(uploaded_data.collectionname, embed_fn)
        if not db:
            return Response({"message":"Your Document is deleted." }, status=status.HTTP_400_BAD_REQUEST)
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request, 1, 0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        response = semantic_search_on_contract_compliance(db,open_ai_key)

        return Response({"message": "Response Generated Successfully!", "Response": response}, status=status.HTTP_200_OK)

    except Exception as ex:
        return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)