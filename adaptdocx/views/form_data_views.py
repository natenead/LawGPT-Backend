import json

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ..serializers import AdaptdocxFormjsonDataSerizalizer, AdaptdocxFormjsonDataUpdateSerizalizer, \
    AdaptdocxSaveJsonDataSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from ..models import AdaptdocxFormjsonData, AdaptdocxFormSubcategory,AdaptdocxFormjsonDataDummy,AdaptdocxClientHistory,AdaptdocxClient,AdaptdocxMatters
from datetime import datetime
from drf_yasg import openapi
from django.db.models import Q


@swagger_auto_schema(method='POST', request_body=AdaptdocxFormjsonDataSerizalizer,
                     responses={status.HTTP_201_CREATED: 'Success',
                                status.HTTP_401_UNAUTHORIZED: 'UNAUTHORIZED', status.HTTP_404_NOT_FOUND: 'Not Found',
                                status.HTTP_409_CONFLICT: 'Already Exists'})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def insert_form_data(request):
    # if request.user.role.pk == 5:
    formjson = request.data['formJson']
    pagename = request.data['categoryName']
    try:
        catg_data = AdaptdocxFormjsonData.objects.get(subcategoryId=request.data['subcategoryId'])
        return Response({'message': 'This Subcategory Already Exists'}, status=status.HTTP_409_CONFLICT)

    except:
        pass
    try:
        subcategoryId = AdaptdocxFormSubcategory.objects.get(id=request.data['subcategoryId'])
    except:
        return Response({'message': 'Please Enter a valid ID'}, status=status.HTTP_404_NOT_FOUND)
    form_obj = AdaptdocxFormjsonData(subcategoryId=subcategoryId, formJson=json.dumps(formjson), pagename=pagename,
                                     createddate=datetime.now(), isdelete=False)
    form_obj.save()

    data_ = {
        'id': form_obj.pk,
        'formjson': formjson,
        'pagename': pagename,
        'subcategoryId': request.data['subcategoryId']

    }

    return Response({'message': 'Form Json save successfully', 'data': data_}, status=status.HTTP_200_OK)

    # return Response({'message': 'You do not have permission to add data', 'data': []},
    #                 status=status.HTTP_401_UNAUTHORIZED)


@swagger_auto_schema(method='GET', manual_parameters=[
    openapi.Parameter('categoryName', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
    openapi.Parameter('subcategoryId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    openapi.Parameter('clientId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
    openapi.Parameter('matterId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False)
],
                     responses={status.HTTP_201_CREATED: 'Success', status.HTTP_401_UNAUTHORIZED: 'UNAUTHORIZED',
                                status.HTTP_404_NOT_FOUND: 'Not Found', })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_form_json_data(request):
    from django.db import connection

    # if request.user.role.pk == 5:
    pg_name = request.query_params.get("categoryName")
    subcategoryId = request.query_params.get("subcategoryId")
    if request.query_params.get("clientId") is not None:

        clientId = request.query_params.get("clientId")

        matterId = request.query_params.get("matterId")
        try:
            client_object = AdaptdocxClient.objects.get(client_id=clientId)
            obj = AdaptdocxClientHistory(clientid=client_object, matterid=AdaptdocxMatters.objects.get(id=matterId), date_time=datetime.now(),
                                              notes="Interview Launched", action="Interview", drafter=client_object.first_name+ ' ' + client_object.middle_name + ' ' +
                          client_object.last_name)

            obj.save()
        except Exception as e:
            return Response({'message': f'Please -- {e} --- Enter a valid Name'}, status=status.HTTP_404_NOT_FOUND)
    try:
        table_name = AdaptdocxFormjsonData._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute("""
                            SELECT * 
                            FROM public.adaptdocx_formjson_data 
                            WHERE "isDelete" = FALSE 
                            AND  "pageName" = %s
                            AND "subcategoryId" = %s
                        """, [pg_name, subcategoryId])

            results = cursor.fetchone()

        data_dict = {
            'id': "",
            'subcategoryId': results[1],
            'formJson': results[2],
            'pagename': results[5],
        }
        # obj_hist = AdaptdocxClientHistory(clientid=client, matterid=matter, date_time=datetime.now(),
        #                                   notes="Interview Launched", action="Interview", drafter=client_fullname)
        # obj_hist.save()
        return Response({'message': 'Json Data', 'data': data_dict}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'message': 'Please Enter a valid Name'}, status=status.HTTP_404_NOT_FOUND)

    # return Response({'message': 'You do not have permission to view data'}, status=status.HTTP_401_UNAUTHORIZED)


@swagger_auto_schema(method='PATCH', request_body=AdaptdocxFormjsonDataUpdateSerizalizer,
                     responses={status.HTTP_201_CREATED: 'Success', status.HTTP_401_UNAUTHORIZED: 'UNAUTHORIZED',
                                status.HTTP_404_NOT_FOUND: 'Not Found', })
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_form_json_data(request):
    # if request.user.role.pk == 5:
    pg_name = request.data['categoryName']
    jsonData = request.data['formJson']
    subcategoryId = request.data['subcategoryId']
    try:
        cat_obj = AdaptdocxFormjsonData.objects.get(
            Q(isdelete=False) & Q(pagename=pg_name) & Q(subcategoryId=subcategoryId))
        cat_obj.formJson = json.dumps(jsonData)
        cat_obj.save()
        data_dict = {
            'id': cat_obj.id,
            'subcategoryId': cat_obj.subcategoryId.id,
            'formJson': jsonData,
            'pagename': cat_obj.pagename,
        }
        return Response({'message': 'Update Data successfully', 'data': data_dict}, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'Please Enter a valid Name'}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='POST', request_body=AdaptdocxSaveJsonDataSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sava_form(request):
    matter_id = request.data['matter_id']
    client_id = request.data['client_id']
    try:
        client = AdaptdocxClient.objects.get(client_id=client_id)
        matter = AdaptdocxMatters.objects.get(id=matter_id)
        client_fullname = client.first_name + ' ' + client.middle_name + ' ' + client.last_name
        obj_hist = AdaptdocxClientHistory(clientid=client, matterid=matter, date_time=datetime.now(),
                                          notes="Interview Completed ", action="Interview", drafter=client_fullname)
        obj_hist.save()
    except:
        return Response({'message': 'Please Enter a valid ID'}, status=status.HTTP_404_NOT_FOUND)

    # obj_hist = AdaptdocxClientHistory(clientid=client, matterid=matter, date_time=datetime.now(),
    #                                   notes="interview launched", action="interview", drafter=client_fullname)
    # obj_hist.save()
    ser = AdaptdocxSaveJsonDataSerializer(data=request.data)
    if ser.is_valid():
        ser.save()
        return Response({'message': 'Data save successfully', 'data': None}, status=status.HTTP_200_OK)
    return Response({'message': f'Error due to {ser.errors}'}, status=status.HTTP_400_BAD_REQUEST)





@swagger_auto_schema(method='POST', request_body=AdaptdocxFormjsonDataSerizalizer,
                     responses={status.HTTP_201_CREATED: 'Success',
                                status.HTTP_401_UNAUTHORIZED: 'UNAUTHORIZED', status.HTTP_404_NOT_FOUND: 'Not Found',
                                status.HTTP_409_CONFLICT: 'Already Exists'})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def insert_form_data_dummy(request):
    # if request.user.role.pk == 5:
    formjson = request.data['formJson']
    pagename = request.data['categoryName']
    try:
        catg_data = AdaptdocxFormjsonData.objects.get(subcategoryId=request.data['subcategoryId'])
        return Response({'message': 'This Subcategory Already Exists'}, status=status.HTTP_409_CONFLICT)

    except:
        pass
    try:
        subcategoryId = AdaptdocxFormSubcategory.objects.get(id=request.data['subcategoryId'])
    except:
        return Response({'message': 'Please Enter a valid ID'}, status=status.HTTP_404_NOT_FOUND)
    form_obj = AdaptdocxFormjsonDataDummy(subcategoryId=subcategoryId, formJson=json.dumps(formjson), pagename=pagename,
                                     createddate=datetime.now(), isdelete=False)
    form_obj.save()

    data_ = {
        'id': form_obj.pk,
        'formjson': formjson,
        'pagename': pagename,
        'subcategoryId': request.data['subcategoryId']

    }

    return Response({'message': 'Form Json save successfully', 'data': data_}, status=status.HTTP_200_OK)