from rest_framework.decorators import api_view, permission_classes, authentication_classes
from ..serializers import Topics, Questions
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from .general_utils import *
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from ..models import Depositionhistorytopics, Depositionhistoryquestions, Userbot,Mostlyusedfeature,Userapikeys,AdminUser
from datetime import datetime
from django.db import transaction
from django.db.models import Window
from django.db.models.functions import RowNumber
from django.db.models import F
from ..serializers import QuestionForTopic
from ..utils import check_number_of_queries,getOpenAIKey,is_user_able_to_query
# @swagger_auto_schema(method='GET',
#                      manual_parameters=[
#                          openapi.Parameter('situation', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
#                          openapi.Parameter('topics_list', openapi.IN_QUERY, type=openapi.TYPE_ARRAY,
#                                            items=openapi.Items(type=openapi.TYPE_STRING), allow_empty_value=True,
#                                            required=False),
#
#                      ],
#                      )
@swagger_auto_schema(method='POST', request_body=QuestionForTopic)
@api_view(['POST'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def generate_topics_for_deposition(request):

    # if request.user.role == 1:
    #     api_key_ = Userapikeys.objects.filter(userid=request.user.pk).filter(isdelete=False)
    #     if api_key_:
    #         api_key = api_key_[0].apikey
    # elif request.user.role == 3:
    #     api_key_ = Userapikeys.objects.filter(userid=AdminUser.present.get(userid=request.user.pk).pk).filter(
    #         isdelete=False)
    #     if api_key_:
    #         api_key = api_key_[0].apikey
    # else:
    #     api_key_ = Userapikeys.objects.filter(userid=6).filter(isdelete=False)
    #     if api_key_:
    #         api_key = api_key_[0].apikey
    # open_ai_key = getOpenAIKey(request)
    open_ai_key = is_user_able_to_query(request,1,0)
    if open_ai_key == 0:
        return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)

    situation = request.data.get('situation')
    topics_list = request.data.get('topics_list')
    if request.data.get('topics_list')[0] == 'string':
        topics_list = []
    try:
        data = generate_topics(situation, topics_list,open_ai_key)
    except:
        return Response({"message": "Your API key is invalid"}, status=status.HTTP_402_PAYMENT_REQUIRED)
    for prev_topic in topics_list:
        if prev_topic == "":
            continue
        new_dict = {
            'Topic':prev_topic
        }
        data.append(new_dict)
    if data:
        return Response({'message': "Topics Generated Successfully", "data": data}, status=status.HTTP_200_OK)
    else:
        return Response({'message': "Request Failed!", "data": []}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='POST', request_body=Topics)
@api_view(['POST'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def generate_question_for_deposition_topics(request):
    # if not check_number_of_queries(request):
    #         return Response({'message': "You Don't have permission to query", "data": []}, status=status.HTTP_402_PAYMENT_REQUIRED)
    num_query = check_number_of_queries(request)
    if num_query == 2:
        return Response({'message': "Please Subscribe", "data": []}, status=status.HTTP_402_PAYMENT_REQUIRED)
    elif num_query == 3:
        return Response({'message': "Please Enter Your Own API Key", "data": []},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    elif num_query == 1:
        pass
    try:
        userbot = Userbot.objects.get(botid=request.data.get('botid'))
    except:
        return Response({"error": "Please Enter a valid bot"}, status=status.HTTP_400_BAD_REQUEST)
    # open_ai_key = getOpenAIKey(request)
    open_ai_key = is_user_able_to_query(request, 1, 0)
    if open_ai_key == 0:
        return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
    topics = [v for v in request.data.get('topics') if v != ""]
    data = generate_questions(make_dictionary(topics),open_ai_key)
    current_date = datetime.now()

    with transaction.atomic():
        try:
            for topics_ in data:

                new_topics = Depositionhistorytopics(topics=list(topics_.keys())[0],
                                                     botid=userbot,
                                                     createddate=current_date,
                                                     situation=request.data.get('situation')
                                                     )
                new_topics.save()

                for quest in topics_[list(topics_.keys())[0]]:
                    obj = Depositionhistoryquestions(tid=new_topics, question=quest, createddate=current_date)
                    obj.save()
        except:
            transaction.set_rollback(True)
            return Response({'message': "Request Failed!", "data": []}, status=status.HTTP_400_BAD_REQUEST)
    if data:
        mostly_used = Mostlyusedfeature.objects.get(featureid=1)
        count = mostly_used.count
        count += 1
        mostly_used.count = count
        mostly_used.save()

        return Response({'message': "Questions Generated Successfully", "data": data}, status=status.HTTP_200_OK)
    else:
        return Response({'message': "Request Failed!", "data": []}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_deposition_botid(request):
    bot_list = [v.pk for v in Userbot.objects.filter(userid=request.user.pk).filter(isarchive=False)]
    subquery = Depositionhistorytopics.objects.annotate(
        rn=Window(
            expression=RowNumber(),
            partition_by=[F('botid')],
            order_by=[F('createddate').desc()]
        )
    ).filter(rn=1).filter(botid__in=bot_list)
    new_list = list()
    for query_data in subquery:
        if query_data.situation is None:
            pass
        else:
            new_dict = {
                'id':query_data.pk,
                'situation':query_data.situation,
                'botid':query_data.botid.pk
            }
            new_list.append(new_dict)
    new_list.reverse()
    return Response({'message':'Deposition User Bot ID','data':new_list},status=status.HTTP_200_OK)




#
# @swagger_auto_schema(method='GET',
#                      manual_parameters=[
#                          openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True), ])
#
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_deposition_history(request):
#
#     new_list = list()
#     first_time = True
#     botid = request.query_params.get('botid')
#     deposition_history_data = Depositionhistorytopics.objects.annotate(
#         rn=Window(
#             expression=RowNumber(),
#             partition_by=[F('createddate')],
#             order_by=[F('createddate').desc()]
#         )
#     ).filter(botid=botid)
#     if deposition_history_data.exists() is False:
#         return Response({'message': 'Please Enter a valid Bot ID', 'data': []}, status=status.HTTP_400_BAD_REQUEST)
#     for index, dep_hist in enumerate(deposition_history_data):
#         if index == 0:
#             main_list = list()
#         if dep_hist.rn == 1:
#             if main_list !=[]:
#                 new_list.append(main_list)
#             main_list = list()
#         new_dict = {
#             dep_hist.topics:DepositionhistoryquestionsSerializer(dep_hist.depositionhistoryquestions_set.all(),many=True).data
#         }
#         main_list.append(new_dict)
#         #     if first_time:
#         #         first_time = False
#         #
#         #     else:
#         #         pass
#         # new_dict = {
#         #     # 'id':dep_hist.pk,
#         #     'type':'questions',
#         #     index: {dep_hist.topics: [""]}
#         #
#         # }
#         # mylst = list()
#         # for ind,i in enumerate(dep_hist.depositionhistoryquestions_set.all()):
#         #
#         #     mylst.append(i.question)
#         # final = {dep_hist.topics: mylst}
#         # quest_hist = {
#         #         "type":'answers',
#         #         index:final
#         #
#         # }
#         # new_list.append(new_dict)
#         # new_list.append(quest_hist)
#
#     return Response({'message':'Deposition User Bot Histoy','data':new_list},status=status.HTTP_200_OK)
# #
# #

@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True), ])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_deposition_history(request):
    new_list = list()
    first_time = True
    botid = request.query_params.get('botid')
    deposition_history_data = Depositionhistorytopics.objects.annotate(
        rn=Window(
            expression=RowNumber(),
            partition_by=[F('createddate')],
            order_by=[F('createddate').desc()]
        )
    ).filter(botid=botid)
    if deposition_history_data.exists() is False:
        return Response({'message': 'Please Enter a valid Bot ID', 'data': []}, status=status.HTTP_400_BAD_REQUEST)
    main_list = list()
    topic_dict = dict()
    quest_dict = dict()
    val = 0
    for index, dep_hist in enumerate(deposition_history_data):
        if dep_hist.rn == 1:
            if index != 0:
                topic_dict['type'] = 'questions'
                quest_dict['type'] = 'answers'
                main_list.append(topic_dict)
                main_list.append(quest_dict)
            topic_dict = dict()
            quest_dict = dict()

        topic_dict[dep_hist.rn-1] = {
                dep_hist.topics: [""]
            }

        mylst = list()
        for ind,i in enumerate(dep_hist.depositionhistoryquestions_set.all()):
            # mydct = {
            #     ind:i.question
            # }
            mylst.append(i.question)
        # final = {dep_hist.topics: mylst}
        quest_dict[dep_hist.rn-1] = {
                dep_hist.topics: mylst
            }

    topic_dict['type'] = 'questions'
    quest_dict['type'] = 'answers'
    main_list.append(topic_dict)
    main_list.append(quest_dict)
    return Response({'message':'Deposition User Bot Histoy','data':main_list},status=status.HTTP_200_OK)