from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from .general_utils import *
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
import os
from ..utils import check_number_of_queries, getOpenAIKey, is_user_able_to_query
from pinecone import Pinecone
from langchain.embeddings import HuggingFaceEmbeddings
from .db_utils import *
from django.db.models.functions import RowNumber
from django.db.models import F
from django.db.models import Window
from ..models import Mostlyusedfeature
import random
import json
from ..serializers import StatesList

embed_fn = HuggingFaceEmbeddings(model_name=os.getenv("model_name"))

load_dotenv()

from langchain_pinecone import PineconeVectorStore as lang_pinecone

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
vectordb = lang_pinecone(index=index, embedding=embed_fn, text_key="text")

# pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINCONE_ENV"))
# index = pinecone.Index(index_name=os.getenv("PINECONE_INDEX_NAME"))
# vectordb = Pinecone(index, embed_fn.embed_query, "text")

file_processor = IncomingFileProcessor(chunk_size=450)


@swagger_auto_schema(method='POST', request_body=StatesList,
                     manual_parameters=[
                         openapi.Parameter('query', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                         openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
                         openapi.Parameter('searchbit', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, required=True, ),
                     ]
                     )
@api_view(['POST'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def simple_caselaw_search_with_response_and_source(request):
    path = os.path.abspath("data.json")
    botid = request.query_params.get('botid')
    # open_ai_key = getOpenAIKey(request)
    open_ai_key = is_user_able_to_query(request, 1, 0)

    states_list = request.data.get("statesList")
    # cache_key = request.query_params.get('query').lower() + " " + " ".join(states_list) + "parallel"
    # cache_data = cache.get(key=cache_key)
    # if cache_data:
    #     return Response({"message": "Response Generated Successfully!",
    #                      "Query": cache_data[0],
    #                      "Sources": cache_data[1],
    #                      "main": cache_data[2],
    #                      "cites_to": cache_data[3],
    #                      "citation": cache_data[4],
    #                      "casebody": cache_data[5],
    #                      "opinion": cache_data[6],
    #                      "attorney": cache_data[7],
    #                      "court": cache_data[8],
    #                      "judges": cache_data[9],
    #                      "jurisdiction": cache_data[10],
    #                      "parties": cache_data[11],
    #                      "reporter": cache_data[12]
    #                      },
    #                     status=status.HTTP_200_OK)

    if open_ai_key == 0:
        return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
    searchbit = request.query_params.get('searchbit')
    if botid:
        num_query = check_number_of_queries(request)
        if num_query == 2:
            return Response({'message': "Please Subscribe", "data": []}, status=status.HTTP_402_PAYMENT_REQUIRED)
        elif num_query == 3:
            return Response({'message': "Please Enter Your Own API Key", "data": []},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        elif num_query == 1:
            pass

    try:
        if botid:
            userbot = Userbot.objects.get(botid=botid)
    except:
        return Response({"error": "Please Enter a valid bot"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        if states_list[0] == 'string':
            states_list = True
        response = search_caselaw_for_search_module(request.query_params.get('query').lower(), vectordb, open_ai_key,
                                                    states_list)
        # response = search_caselaw(request.query_params.get('query').lower(), vectordb,open_ai_key)

    except Exception as e:
        return Response({"message": f"Your API key is invalid OR {e}"}, status=status.HTTP_402_PAYMENT_REQUIRED)

    if response['result'].lower() == "no" and searchbit == 'false':
        return Response(
            {"message": "AI system did not yield any pertinent results in relation to the query."},
            status=status.HTTP_400_BAD_REQUEST)
    else:
        k = random.randint(15, 20)
        sources = list(set(parse_output(response['source_documents'][0:k])))
        # sources = list(set(parse_output(response['source_documents'])))
        main, citesto, citation, casebody, opinion, attorney, court, judges, jurisdiction, parties, reporter = extract_data_from_db(
            sources)
        # with open(path, 'r') as fp:
        with open(os.getcwd() + '/LawApp/views/data.json') as fp:
            data = json.load(fp)
        for result in citesto:
            count = 0
            for state_name in data.keys():
                if result['Reporter'] in data[state_name]:
                    result['Category'] = state_name
                    count += 1
            if count == 0:
                result['Category'] = 'United States'
        if searchbit == 'false' and botid:
            obj = Simplechathistory(botid=userbot, Sources=sources, createddate=datetime.now(),
                                    query=request.query_params.get('query'))
            obj.save()
        mostly_used = Mostlyusedfeature.objects.get(featureid=3)
        count = mostly_used.count
        count += 1
        mostly_used.count = count
        mostly_used.save()

        # cache.set(
        #     key=cache_key,
        #     value=(
        #         response['query'],
        #         sources, main,citesto, citation, casebody, opinion, attorney, court, judges, jurisdiction, parties, reporter),
        # )
        try:
            return Response({"message": "Response Generated Successfully!",
                             "Query": response['query'],
                             "Sources": sources,
                             "main": main,
                             "cites_to": citesto,
                             "citation": citation,
                             "casebody": casebody,
                             "opinion": opinion,
                             "attorney": attorney,
                             "court": court,
                             "judges": judges,
                             "jurisdiction": jurisdiction,
                             "parties": parties,
                             "reporter": reporter},
                            status=status.HTTP_200_OK)
        except Exception as e:
            print(e)


# remove authentication
# @swagger_auto_schema(method='POST',request_body=QuerySerializer,
#                      # manual_parameters=[
#                      #     openapi.Parameter('query', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
#                      #     openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
#                      #    openapi.Parameter('searchbit',  openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, required=True)    ,
#                      # ]
#                      )
# @api_view(['POST'])
# # @authentication_classes([])
# @permission_classes([])
# def simple_caselaw_search_with_response_and_source(request):
#     path = os.path.abspath("data.json")
#     states_list = request.data['statesList']
#     botid=request.data['botid']
#     # open_ai_key = getOpenAIKey(request)
#     open_ai_key = os.getenv('OPENAI_API_KEY')
#     if open_ai_key == 0:
#         return Response({"message": "Your API key is invalid"}, status=status.HTTP_402_PAYMENT_REQUIRED)
#     searchbit = request.data['searchbit']
#     if botid:
#         if not check_number_of_queries(request):
#             return Response({'message': "You Don't have permission to query", "data": []},
#                             status=status.HTTP_402_PAYMENT_REQUIRED)
#     try:
#         if botid:
#             userbot = Userbot.objects.get(botid=botid)
#     except:
#         return Response({"error": "Please Enter a valid bot"}, status=status.HTTP_400_BAD_REQUEST)
#     try:
#         response = search_caselaw(request.data['query'].lower(), vectordb, states_list,open_ai_key)
#         response = fetch_source_from_query(request.data['query'].lower(), vectordb,10,open_ai_key)
#         # response = search_caselaw(request.query_params.get('query').lower(), vectordb,open_ai_key)
#
#     except:
#         return Response({"message": "Your API key is invalid"}, status=status.HTTP_402_PAYMENT_REQUIRED)
#
#     if response['result'].lower() == "no" and searchbit == 'false':
#         return Response(
#             {"message": "AI system did not yield any pertinent results in relation to the query."},
#             status=status.HTTP_400_BAD_REQUEST)
#     else:
#         k = random.randint(4, 10)
#         sources = list(set(parse_output(response['source_documents'][0:k])))
#         # sources = list(set(parse_output(response['source_documents'])))
#         main, citesto, citation, casebody, opinion, attorney, court, judges, jurisdiction, parties, reporter = extract_data_from_db(
#             sources)
#         # with open(path, 'r') as fp:
#         with open(os.getcwd() + '/LawApp/views/data.json') as fp:
#             data = json.load(fp)
#         for result in citesto:
#             count = 0
#             for state_name in data.keys():
#                 if result['Reporter'] in data[state_name]:
#                     result['Category'] = state_name
#                     count += 1
#             if count == 0:
#                 result['Category'] = 'United States'
#         if searchbit == 'false' and botid:
#             obj = Simplechathistory(botid=userbot, Sources=sources, createddate=datetime.now(),
#                                     query=request.query_params.get('query'))
#             obj.save()
#         mostly_used = Mostlyusedfeature.objects.get(featureid=3)
#         count = mostly_used.count
#         count += 1
#         mostly_used.count = count
#         mostly_used.save()
#         return Response({"message": "Response Generated Successfully!",
#                          "Query": response['query'],
#                          "Sources": sources,
#                          "main": main,
#                          "cites_to": citesto,
#                          "citation": citation,
#                          "casebody": casebody,
#                          "opinion": opinion,
#                          "attorney": attorney,
#                          "court": court,
#                          "judges": judges,
#                          "jurisdiction": jurisdiction,
#                          "parties": parties,
#                          "reporter": reporter},
#                         status=status.HTTP_200_OK)

# @swagger_auto_schema(method='GET',
#                      manual_parameters=[
#                          openapi.Parameter('pageNo', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
#                          openapi.Parameter('pageSize', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
#                      ]
#                      )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_simplechat_botid(request):
    # try:
    #     pg_no = int(request.query_params.get('pageNo'))
    #     pgSize = int(request.query_params.get('pageSize'))
    #     end_size = pg_no * pgSize
    #     start_size = end_size - pgSize
    #
    # except:
    #     return Response({"success": False, 'data': None, "message": "Please Provide Page Number"},
    #                     status=status.HTTP_400_BAD_REQUEST)

    bot_list = [v.pk for v in Userbot.objects.filter(userid=request.user.pk).filter(isarchive=False)]
    subquery = Simplechathistory.objects.annotate(
        rn=Window(
            expression=RowNumber(),
            partition_by=[F('botid')]
        )
    ).filter(botid__in=bot_list).order_by('-id')

    # [start_size:end_size]

    new_list = list()
    for query_data in subquery:
        new_dict = {
            'id': query_data.pk,
            'query': query_data.query,
            'botid': query_data.botid.pk
        }
        new_list.append(new_dict)
    # new_list.reverse()
    return Response({'message': 'General Chat User Bot ID', 'data': new_list}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET', manual_parameters=[
    openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)])
@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def get_simplechat_history(request):
    main_list = list()
    simplechat_hist = Simplechathistory.objects.filter(id=request.query_params.get('id')).order_by('-createddate')
    for obj in simplechat_hist:
        new_list = list()
        main, citesto, citation, casebody, opinion, attorney, court, judges, jurisdiction, parties, reporter = extract_data_from_db(
            obj.Sources)
        new_dict = {
            "Query": obj.query,
            "Sources": obj.Sources,
            "main": main,
            "cites_to": citesto,
            "citation": citation,
            "casebody": casebody,
            "opinion": opinion,
            "attorney": attorney,
            "court": court,
            "judges": judges,
            "jurisdiction": jurisdiction,
            "parties": parties,
            "reporter": reporter
        }
        # new_list.append(new_dict)
        main_list.append(new_dict)
    return Response({'message': 'General Chat Data', 'data': main_list}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('caseId', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True), ]
                     )
@api_view(['GET'])
# @authentication_classes([])
@permission_classes([])
def get_data_from_case_id(request):
    main_list = list()
    main_list_ = list()

    case_id = request.query_params.get('caseId')
    main_list_.append(case_id)
    main, citesto, citation, casebody, opinion, attorney, court, judges, jurisdiction, parties, reporter = extract_data_from_db(
        main_list_)
    new_dict = {
        "Query": "User Query",
        "Answer": "Successfully get the answers",
        "main": main,
        "cites_to": citesto,
        "citation": citation,
        "casebody": casebody,
        "opinion": opinion,
        "attorney": attorney,
        "court": court,
        "judges": judges,
        "jurisdiction": jurisdiction,
        "parties": parties,
        "reporter": reporter
    }
    # new_list.append(new_dict)
    main_list.append(new_dict)

    return Response({'message': 'Case Data', 'data': main_list}, status=status.HTTP_200_OK)
