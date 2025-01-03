import json

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from ..serializers import AdaptdocxClientSerializer, AdaptdocxMattersSerializer, AdaptdocxClientPhoneSerializer, \
    AdaptdocxClientAddressSerializer, AdaptdocxClientNotesSerializer, AdaptdocxClientHistorySerializer, \
    MatterSignedClosed
from rest_framework import status
from rest_framework.response import Response
from .backend_logic import insert_record_matter, insert_record_phone
from ..models import AdaptdocxMatters, AdaptdocxClient, AdaptdocxFormSubcategory, AdaptdocxClientPhone, \
    AdaptdocxClientAddress, AdaptdocxSaveJsonData, AdaptdocxClientHistory, AdaptdocxMattersigned
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from django.db.models import Q
from datetime import date, datetime


@swagger_auto_schema(method='POST', request_body=AdaptdocxClientSerializer)
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def insert_client(request):
    data = request.data
    data['primary_phone'] = json.dumps(data['primary_phone'])
    data['address_line1'] = json.dumps(data['address_line1'])
    if data['martial_status'] in ['notMarried', 'legalRegister']:
        data['spouse_prefix'] = None
        data['spouse_firstname'] = None
        data['spouse_middlename'] = None
        data['spouse_lastname'] = None
        data['spouse_suffix'] = None
        data['spouse_nickname'] = None
        data['spouse_gender'] = None
        data['spouse_dob'] = date.today()
        data['spouse_us_citizen'] = None
        data['spouse_phone'] = None
        data['spouse_email'] = None
    serializer = AdaptdocxClientSerializer(data=data)

    if serializer.is_valid():
        serializer.save(request.user, False)
        return Response({'message': 'Client Save', 'data': None}, status=status.HTTP_200_OK)
    return Response({'message': serializer.errors, 'data': None}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='POST', request_body=AdaptdocxMattersSerializer)
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def add_matter(request):
    new_data = request.data
    new_data['drafter'] = request.user
    try:
        record = insert_record_matter(AdaptdocxMatters, new_data)
    except Exception as e:
        return Response({'message': f"ERROR {e}", 'data': None}, status=status.HTTP_400_BAD_REQUEST)
    _ = {
        'client_first_name': record.client.first_name,
        'client_middle_name': record.client.middle_name,
        'client_last_name': record.client.last_name,
        'client_id': record.client_id,
        'offering_id': record.offering_id,
        'matter_id': record.id,
        'matter_title': record.mattertitle,
        'offeringId': record.offering.id,
        'categoryName': record.offering.categoryid.categoryname

    }
    client_fullname = record.client.first_name + ' ' + record.client.middle_name + ' ' + record.client.last_name
    obj_hist = AdaptdocxClientHistory(clientid=record.client, matterid=record, date_time=datetime.now(),
                                      notes="Matter Created", action="Create", drafter=client_fullname)
    obj_hist.save()
    obj_hist = AdaptdocxClientHistory(clientid=record.client, matterid=record, date_time=datetime.now(),
                                      notes=f"Assigned to {client_fullname}", action="Assigned", drafter='system')
    obj_hist.save()

    return Response({'message': 'Matter Save', 'data': _}, status=status.HTTP_200_OK)
    # serializer = AdaptdocxMattersSerializer(data=data)
    # if serializer.is_valid():
    #     serializer.save()
    #     return Response({'messge': 'Client Save', 'data': None}, status=status.HTTP_200_OK)
    # return Response({'messge': serializer.errors, 'data': None}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='GET', manual_parameters=[
    openapi.Parameter('pageNumber', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True, required=False,
                      default=1),
    openapi.Parameter('pageSize', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True, required=False,
                      default=10),
    openapi.Parameter('name', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True, required=False), ])
# @authentication_classes([])
@permission_classes((AllowAny,))
@api_view(['GET'])
def get_client(request):
    try:
        from django.db.models.functions import Lower
        condition = Q()
        pg_no = int(request.query_params.get('pageNumber'))
        pgSize = int(request.query_params.get('pageSize'))
        name = request.query_params.get('name')
        #
        if name is not None:
            # new_name = name.capitalize()
            if name != "":
                name_parts = name.split()
                name_parts_new = [v.capitalize() for v in name_parts]
                if len(name_parts) == 1:
                    new_name_data = " ".join(name_parts_new)

                    condition |= Q(first_name__contains=name)
                    condition |= Q(middle_name__contains=name)
                    condition |= Q(last_name__contains=name)

                    # condition |= Q(first_name__contains=new_name_data)
                    # condition |= Q(middle_name__contains=new_name_data)
                    # condition |= Q(last_name__contains=new_name_data)
                elif len(name_parts) == 2:
                    condition |= (Q(first_name__icontains=name_parts[0]) & Q(last_name__icontains=name_parts[1])) | (
                            Q(first_name__icontains=name_parts[0]) & Q(middle_name__icontains=name_parts[1])) | (
                                         Q(middle_name__icontains=name_parts[0]) & Q(
                                     last_name__icontains=name_parts[1]))
                    # condition |= (Q(first_name__icontains=name_parts_new[0]) & Q(last_name__icontains=name_parts_new[1])) | (
                    #         Q(first_name__icontains=name_parts_new[0]) & Q(middle_name__icontains=name_parts_new[1])) | (
                    #                      Q(middle_name__icontains=name_parts_new[0]) & Q(
                    #                  last_name__icontains=name_parts_new[1]))
                else:
                    condition |= Q(first_name__icontains=name_parts[0]) & Q(middle_name__icontains=name_parts[1]) & Q(
                        last_name__icontains=name_parts[2])
                    # condition |= Q(first_name__icontains=name_parts_new[0]) & Q(middle_name__icontains=name_parts_new[1]) & Q(
                    #     last_name__icontains=name_parts_new[2])
        if pg_no > 0 and pgSize > 0:
            end_size = pg_no * pgSize
            start_size = end_size - pgSize
        else:
            return Response({"success": False, 'data': None, "message": "Please Enter a valid value"},
                            status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({"success": False, 'data': None, "message": "Please Provide Page Number"},
                        status=status.HTTP_400_BAD_REQUEST)

    client_data = AdaptdocxClient.objects.annotate(lower_first_name=Lower('first_name')).annotate(
        lower_middle_name=Lower('middle_name')).annotate(lower_last_name=Lower('last_name')).prefetch_related(
        'client_data').filter(condition).filter(
        user_id=request.user.pk).order_by('-client_id')[
                  start_size:end_size]
    total_count = AdaptdocxClient.objects.filter(user_id=request.user.pk).count()
    main_list = list()
    for data in client_data:
        if data.primary_phone is None:
            primary_phone = None
        else:
            primary_phone = ','.join(data.primary_phone.values())
        if data.address_line1 is None:
            address = None
        else:
            address = ','.join(data.address_line1.values())
        ser = AdaptdocxMattersSerializer(data.client_data.all(), many=True)
        matter_data_id = ser.data
        notes_data_data = None
        if data.adaptdocxclientnotes_set.exists():
            notes_data = data.adaptdocxclientnotes_set.all()
            notes_data_ = AdaptdocxClientNotesSerializer(notes_data, many=True)
            notes_data_data = notes_data_.data
        dict_ = {
            'id': data.client_id,
            'first_name': data.first_name,
            'last_name': data.last_name,
            'middle_name': data.middle_name,
            'email': data.email,
            'state': data.state,
            'phone': primary_phone,
            'matter_data': matter_data_id,
            'address': address,
            'city': data.city,
            'nickname': data.nick_name,
            'martial_status': data.martial_status,
            'refferal_code': data.refferal_code,
            'gender': data.gender,
            'suffix': data.suffix,
            'dob': data.dob,
            'zip_code': data.zip_code,
            'country': data.country,
            'lastUpdate': data.date_time,
            'estate_value': data.estate_value,
            'firm_client_id': data.firm_client_id,
            'notes': notes_data_data,
            'drafter_name': request.user.fullname
        }
        main_list.append(dict_)
    main_list.reverse()
    # client_ser = AdaptdocxClientSerializer(client_data,many=True)
    return Response({'message': 'Client data', 'data': main_list, 'total_records': total_count},
                    status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET', manual_parameters=[
    openapi.Parameter('pageNumber', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True, required=False,
                      default=1),
    openapi.Parameter('pageSize', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True, required=False,
                      default=10),
    openapi.Parameter('matterTitle', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True,
                      required=False),
])
# @authentication_classes([])
@permission_classes((AllowAny,))
@api_view(['GET'])
def get_matter(request):
    try:
        condition = Q()
        pg_no = int(request.query_params.get('pageNumber'))
        pgSize = int(request.query_params.get('pageSize'))
        matterTitle = request.query_params.get('matterTitle')
        if matterTitle is not None:
            if matterTitle != "":
                condition |= Q(mattertitle__contains=matterTitle)
        if pg_no > 0 and pgSize > 0:
            end_size = pg_no * pgSize
            start_size = end_size - pgSize
        else:
            return Response({"success": False, 'data': None, "message": "Please Enter a valid value"},
                            status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({"success": False, 'data': None, "message": "Please Provide Page Number"},
                        status=status.HTTP_400_BAD_REQUEST)
    matter_data = AdaptdocxMatters.objects.filter(is_delete=False).filter(condition).select_related(
        'client').prefetch_related('adaptdocxmattersigned_set').filter(
        client__user_id=request.user.pk).order_by('-id')[start_size:end_size]
    total_count = AdaptdocxMatters.objects.filter(is_delete=False).select_related('client').filter(
        client__user_id=request.user.pk).count()
    main_list = list()

    for data in matter_data:
        last_json = AdaptdocxSaveJsonData.objects.filter(matter_id=data.id).values('date_time').last()
        if last_json is None:
            last_update_date = matter_data[0].date_time
        else:
            last_update_date = last_json.get('date_time')
        signed = False
        closed = False
        interview = False
        if data.adaptdocxmattersigned_set.exists():
            signed_data = data.adaptdocxmattersigned_set.all()[0]
            signed = signed_data.signed
            closed = signed_data.closed
        if AdaptdocxSaveJsonData.objects.filter(matter_id=data.id).exists():
            interview = True
        dict_ = {
            'clientName': data.client.first_name + ' ' + data.client.middle_name + ' ' + data.client.last_name,
            'id': data.id,
            'firmmatterid': data.firmmatterid,
            'mattertitle': data.mattertitle,
            'representation': data.representation,
            'fee': data.fee,
            'clientId': data.client.client_id,
            'signed': signed,
            'closed':closed,
            'interview': interview,
            'last_update_date': last_update_date

        }
        main_list.append(dict_)
    # main_list.reverse()
    return Response({'message': 'Matter Data', 'data': main_list, 'total_records': total_count},
                    status=status.HTTP_200_OK)


@swagger_auto_schema(method='DELETE', manual_parameters=[
    openapi.Parameter('matterId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
])
# @authentication_classes([])
@permission_classes([])
@api_view(['DELETE'])
def delete_matter(request):
    matter_id = request.query_params.get('matterId')
    try:
        matter = AdaptdocxMatters.objects.get(id=matter_id)
        matter.is_delete = True
        matter.save()
        return Response({'message': 'Matter Deleted Successfully', 'data': None}, status=status.HTTP_200_OK)

    except:
        return Response({'data': None, "message": "Please Provide Valid matter id"},
                        status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='PATCH', manual_parameters=[
    openapi.Parameter('matterId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    openapi.Parameter('matterTitle', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['PATCH'])
def update_matter_title(request):
    matter_id = request.query_params.get('matterId')
    matterTitle = request.query_params.get('matterTitle')
    try:
        matter = AdaptdocxMatters.objects.get(id=matter_id)
        matter.mattertitle = matterTitle
        matter.save()
        return Response({'message': 'Matter title Update Successfully', 'data': None}, status=status.HTTP_200_OK)

    except:
        return Response({'data': None, "message": "Please Provide Valid matter id"},
                        status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='PATCH', manual_parameters=[
    openapi.Parameter('matterId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    openapi.Parameter('fee', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    openapi.Parameter('offeringId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
])
@api_view(['PATCH'])
def update_matter_fee_offering(request):
    matter_id = request.query_params.get('matterId')
    fee = request.query_params.get('fee')
    offeringId = request.query_params.get('offeringId')
    try:
        matter = AdaptdocxMatters.objects.get(id=matter_id)
        matter.fee = fee
        matter.offering = AdaptdocxFormSubcategory.objects.get(id=offeringId)
        matter.save()
        return Response({'message': 'Matter data update Successfully', 'data': None}, status=status.HTTP_200_OK)

    except:
        return Response({'data': None, "message": "Please Provide Valid matter id"},
                        status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='GET', manual_parameters=[
    openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
])
# @authentication_classes([])
@permission_classes((AllowAny,))
@api_view(['GET'])
def get_matter_id(request):
    matter_id = request.query_params.get('id')
    matter_data = AdaptdocxMatters.objects.filter(is_delete=False).filter(id=matter_id).select_related('client')
    last_json = AdaptdocxSaveJsonData.objects.filter(matter_id=matter_id).values('date_time').last()
    interview = False
    if last_json is None:
        last_update_date = matter_data[0].date_time
    else:
        interview = last_json.get('date_time')
        last_update_date = last_json.get('date_time')
    dict_ = {}
    notes = ""
    notes_data = AdaptdocxClientNotesSerializer(matter_data[0].client.adaptdocxclientnotes_set.all(), many=True)
    try:
        notes = notes_data.data
    except:
        pass
    if matter_data:
        signed = False
        closed = False
        signed_date = None
        closed_date = None

        if matter_data[0].adaptdocxmattersigned_set.exists():
            signed_closed = matter_data[0].adaptdocxmattersigned_set.all()[0]
            if signed_closed.signed:
                signed = True
                signed_date = signed_closed.signed_date
            if signed_closed.closed:
                closed = True
                closed_date = signed_closed.closed_date

        matter_closed = 'Queued'
        # if AdaptdocxMattersigned.objects.filter(matter_id=matter_id).exists():
        # json_new_data = AdaptdocxSaveJsonData.objects.filter(matter_id=matter_id)
        if closed:
            matter_closed = 'Completed'
        # AdaptdocxSaveJsonData
        dict_ = {
            'clientName': matter_data[0].client.first_name + ' ' + matter_data[0].client.middle_name + ' ' +
                          matter_data[0].client.last_name,
            'id': matter_data[0].id,
            'firmmatterid': matter_data[0].firmmatterid,
            'mattertitle': matter_data[0].mattertitle,
            'representation': matter_data[0].representation,
            'fee': matter_data[0].fee,
            'client_id': matter_data[0].client_id,
            'subcategoryId': matter_data[0].offering_id,
            'categoryName': matter_data[0].offering.categoryid.categoryname,
            'client_email': matter_data[0].client.email,
            'client_phone': matter_data[0].client.primary_phone,
            'client_last_update': matter_data[0].client.date_time,
            'last_update_field': last_update_date,
            'notes': notes,
            'matter_create': matter_data[0].date_time,
            'matter_closed': matter_closed,
            'signed': signed,
            'signed_date': signed_date,
            'closed': closed,
            'closed_date': closed_date,
            'interview': interview

        }
    obj_hist = AdaptdocxClientHistory(clientid=matter_data[0].client, matterid=matter_data[0], date_time=datetime.now(),
                                      notes="", action="Viewed",
                                      drafter=matter_data[0].client.first_name + ' ' + matter_data[
                                          0].client.middle_name + ' ' +
                                              matter_data[0].client.last_name)
    obj_hist.save()
    return Response({'data': dict_, "message": "Matter Data"},
                    status=status.HTTP_200_OK)


@swagger_auto_schema(method='PUT', request_body=AdaptdocxClientSerializer, manual_parameters=[
    openapi.Parameter('clientId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),

])
@permission_classes([IsAuthenticated])
@api_view(['PUT'])
def update_client_data(request):
    try:
        client_data = AdaptdocxClient.objects.get(client_id=request.query_params.get('clientId'))
    except:
        return Response({'message': "Please provide valid client data", 'data': None},
                        status=status.HTTP_400_BAD_REQUEST)
    data = request.data
    # data['user'] =request.user
    if data['martial_status'] in ['notMarried', 'legalRegister']:
        data['spouse_prefix'] = None
        data['spouse_firstname'] = None
        data['spouse_middlename'] = None
        data['spouse_lastname'] = None
        data['spouse_suffix'] = None
        data['spouse_nickname'] = None
        data['spouse_gender'] = None
        data['spouse_dob'] = None
        data['spouse_us_citizen'] = None
        data['spouse_phone'] = None
        data['spouse_email'] = None
    serializer = AdaptdocxClientSerializer(data=data, instance=client_data)

    if serializer.is_valid():
        serializer.save(request.user, client_data)
        return Response({'message': 'Client Data Updated', 'data': None}, status=status.HTTP_200_OK)
    return Response({'message': serializer.errors, 'data': None}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='GET', manual_parameters=[
    openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
])
# @authentication_classes([])
@permission_classes((AllowAny,))
@api_view(['GET'])
def get_client_id(request):
    client_id = request.query_params.get('id')
    client_id = AdaptdocxClient.objects.prefetch_related('client_data').filter(client_id=client_id)
    data = client_id[0]
    dict_ = {}
    if data:
        if data.primary_phone is None:
            primary_phone = None
        else:
            primary_phone = ','.join(data.primary_phone.values())
        if data.address_line1 is None:
            address = None
        else:
            address = ','.join(data.address_line1.values())
        ser = AdaptdocxMattersSerializer(data.client_data.all(), many=True)
        matter_data_id = ser.data
        dict_ = {
            'id': data.client_id,
            'first_name': data.first_name,
            'last_name': data.last_name,
            'middle_name': data.middle_name,
            'email': data.email,
            'country': data.country,
            'phone': primary_phone,
            'matter_data': matter_data_id,
            'address': address,
            'city': data.city
        }

    return Response({'data': dict_, "message": "Matter Data"},
                    status=status.HTTP_200_OK)


@swagger_auto_schema(method='POST', request_body=AdaptdocxClientPhoneSerializer)
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def add_additional_phone_number(request):
    if request.data['is_primary']:
        AdaptdocxClientPhone.objects.filter(client=request.data['client']).update(is_primary=False)
    serializer = AdaptdocxClientPhoneSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Phone Number save successfully', 'data': None}, status=status.HTTP_200_OK)
    return Response({'message': f'Error due to {serializer.errors}'}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='POST', request_body=AdaptdocxClientAddressSerializer)
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def add_additional_address_data(request):
    if request.data['is_primary']:
        AdaptdocxClientAddress.objects.filter(client=request.data['client']).update(is_primary=False)
    serializer = AdaptdocxClientAddressSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Address Save successfully', 'data': None}, status=status.HTTP_200_OK)
    return Response({'message': f'Error due to {serializer.errors}'}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
@api_view(['GET'])
def get_client_name_id(request):
    client_data = AdaptdocxClient.objects.prefetch_related('client_data').filter(user_id=request.user.pk)
    main_list = list()
    for data in client_data:
        dict_ = {
            'id': data.client_id,
            'first_name': data.first_name,
            'last_name': data.last_name,
            'middle_name': data.middle_name,
            'email': data.email,
            'country': data.country,
        }
        main_list.append(dict_)
    main_list.reverse()
    # client_ser = AdaptdocxClientSerializer(client_data,many=True)
    return Response({'message': 'Client data', 'data': main_list},
                    status=status.HTTP_200_OK)


@swagger_auto_schema(method='DELETE', manual_parameters=[
    openapi.Parameter('clientId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
])
# @authentication_classes([])
@permission_classes([])
@api_view(['DELETE'])
def delete_client(request):
    client_id = request.query_params.get('clientId')
    try:
        client = AdaptdocxClient.objects.get(client_id=client_id)
        client.is_delete = True
        client.save()
        return Response({'message': 'Client Deleted Successfully', 'data': None}, status=status.HTTP_200_OK)

    except:
        return Response({'data': None, "message": "Please Provide Valid client id"},
                        status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='GET', manual_parameters=[
    openapi.Parameter('clientId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    openapi.Parameter('matterId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    openapi.Parameter('pageNumber', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True, required=False,
                      default=1),
    openapi.Parameter('pageSize', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True, required=False,
                      default=5),
])
# @authentication_classes([])
@permission_classes((AllowAny,))
@api_view(['GET'])
def get_history(request):
    try:
        pg_no = int(request.query_params.get('pageNumber'))
        pgSize = int(request.query_params.get('pageSize'))
        if pg_no > 0 and pgSize > 0:
            end_size = pg_no * pgSize
            start_size = end_size - pgSize
        else:
            return Response({"success": False, 'data': None, "message": "Please Enter a valid value"},
                            status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({'message': 'Enter valid page number', 'data': None}, status=status.HTTP_400_BAD_REQUEST)
    client_id = request.query_params.get('clientId')
    matter_id = request.query_params.get('matterId')
    client_hist = AdaptdocxClientHistory.objects.filter(Q(clientid=client_id) & Q(matterid=matter_id)).order_by('-id')[
                  start_size:end_size]
    client_hist_count = AdaptdocxClientHistory.objects.filter(Q(clientid=client_id) & Q(matterid=matter_id)).count()
    ser_data = AdaptdocxClientHistorySerializer(client_hist, many=True)
    return Response({'message': 'Client History', 'data': ser_data.data, 'total_count': client_hist_count},
                    status=status.HTTP_200_OK)


@swagger_auto_schema(method='POST', request_body=MatterSignedClosed)
@permission_classes((AllowAny,))
@api_view(['POST'])
def signedClosedMatter(request):
    matter_id = request.data['matter_id']
    client_id = request.data['client_id']
    signed = request.data['signed']
    closed = request.data['closed']
    try:
        matter = AdaptdocxMatters.objects.get(id=matter_id)
    except:
        return Response({'data': None, "message": "Enter Valid Matter ID"},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        client = AdaptdocxClient.objects.get(client_id=client_id)
        client_fullname = client.first_name + ' ' + client.middle_name + ' ' + client.last_name
    except:
        return Response({'message': 'Enter Valid Client ID', 'data': None}, status=status.HTTP_400_BAD_REQUEST)
    try:
        signed_value = AdaptdocxMattersigned.objects.get(matter=matter_id)
        if signed_value.closed and signed_value.signed:
            return Response({'data': None, "message": "Its already closed and Signed"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif closed == True and signed_value.closed == True:
            return Response({'data': None, "message": "Its already closed "},
                            status=status.HTTP_400_BAD_REQUEST)
        elif signed == True and signed_value.signed == True:
            return Response({'data': None, "message": "Its already Signed"},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            if signed:
                obj_hist = AdaptdocxClientHistory(clientid=client, matterid=matter, date_time=datetime.now(),
                                                  notes="Matter Signed", action="Matter", drafter=client_fullname)
                obj_hist.save()
                signed_value.signed = signed
                signed_value.signed_date = datetime.now()
                signed_value.save()
            else:
                obj_hist = AdaptdocxClientHistory(clientid=client, matterid=matter, date_time=datetime.now(),
                                                  notes="Matter Closed", action="Matter", drafter=client_fullname)
                obj_hist.save()
                signed_value.closed = closed

                signed_value.closed_date = datetime.now()

                signed_value.save()
            return Response({'message': 'Date Save Successfully', 'data': None}, status=status.HTTP_200_OK)

    except:

        obj = AdaptdocxMattersigned(matter=matter, signed=signed, closed=closed, closed_date=datetime.now(),
                                    signed_date=datetime.now())
        obj.save()

        if signed:
            obj_hist = AdaptdocxClientHistory(clientid=client, matterid=matter, date_time=datetime.now(),
                                              notes="Matter Signed", action="Matter", drafter=client_fullname)
            obj_hist.save()
        else:
            obj_hist = AdaptdocxClientHistory(clientid=client, matterid=matter, date_time=datetime.now(),
                                              notes="Matter Closed", action="Matter", drafter=client_fullname)
            obj_hist.save()
        return Response({'message': 'Date Save Successfully', 'data': None}, status=status.HTTP_200_OK)
