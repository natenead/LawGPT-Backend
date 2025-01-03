from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import UserDetails, Studentrecord
from ..serializers import (
    CustomUserSerializer,
    StudentSerializer, StudentSignUpSerializer
)
from ..utils import check_number_of_queries
import boto3
from botocore.client import Config
from dotenv import load_dotenv
import os
from drf_yasg import openapi
from django.db.models import Q
from ipware import get_client_ip

load_dotenv()

aws_key = os.getenv('ACCESS_KEY')
aws_secret_key = os.getenv('SECRET_ACCESS_KEY')
aws_space_name = os.getenv('SPACE_NAME')

from copy import copy
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes

from drf_yasg.utils import swagger_auto_schema

from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated


def aws_session():
    session = boto3.session.Session()
    client = session.client('s3',
                            region_name='us-east-1',
                            endpoint_url='https://lawcobucket.s3.amazonaws.com/',
                            aws_access_key_id=aws_key,
                            aws_secret_access_key=aws_secret_key,
                            config=Config(signature_version='s3v4')

                            )
    space_name = aws_space_name
    return space_name, client


def get_key(key):
    space_name, client = aws_session()
    params = {'Bucket': space_name, 'Key': key}
    url = client.generate_presigned_url('get_object', Params=params)
    return url


@swagger_auto_schema(method='post', request_body=StudentSignUpSerializer)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def student_signup(request):
    request.data['role'] = 4  # 4 hard code
    mydict = {
        'fullname': request.data['fullname'],
        'email': request.data['email']
    }
    st_dict = copy(request.data)
    st_dict['is_deleted'] = True
    del st_dict['filename']
    del st_dict['keys']
    serializer = CustomUserSerializer(data=st_dict)
    if serializer.is_valid():
        ser = serializer.save(request,False)
        mydict['id'] = ser.pk
        try:
            student = Studentrecord(userid=ser, FileNames=request.data['filename'], Records=request.data['keys'],
                                    createddate=datetime.now(), isrejected=False, isapproved=False)
            student.save()
            return Response({'message': "Student Created Successfully", "data": mydict}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f"Failed {e} !", "data": mydict}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'message': "User Aleady exists"}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
        method='GET',
        manual_parameters=[
            openapi.Parameter('StudentName', openapi.IN_QUERY, type=openapi.TYPE_STRING,allow_empty_value=True, required=False),
            openapi.Parameter('pageNumber', openapi.IN_QUERY, type=openapi.TYPE_STRING,allow_empty_value=True, required=False,default=1),
            openapi.Parameter('pageSize', openapi.IN_QUERY, type=openapi.TYPE_STRING,allow_empty_value=True, required=False,default=10),


        ]
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_list(request):
    student_name = request.query_params.get('StudentName')
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
        return Response({"success": False, 'data': None, "message": "Please Provide Page Number"},
                        status=status.HTTP_400_BAD_REQUEST)

    main_list = list()

    st_data = Studentrecord.objects.filter(isrejected=False).filter(isapproved=False)[start_size:end_size]
    st_record = Studentrecord.objects.filter(isrejected=False).filter(isapproved=False).count()
    files = list()
    for student in st_data:
        main_url_list = list()
        for key in student.Records:
            url = get_key(key)
            main_url_list.append(url)
        if (student_name == "") or (student_name is None):
            st_dict = {
                'studentname': student.userid.fullname,
                'studentId': student.userid.pk,
                'email': student.userid.email,

                'files':[{
                    'fileName': student.FileNames,
                    'urls': main_url_list,
                }],
            }
            main_list.append(st_dict)
        elif (student_name == student.userid.fullname) or (student_name in student.userid.fullname):
            st_dict = {
                'studentname': student.userid.fullname,
                'studentId': student.userid.pk,
                'email': student.userid.email,

                'files': [{
                    'fileName': student.FileNames,
                    'urls': main_url_list,
                }],
            }
            main_list.append(st_dict)
    return Response({'message': "Student Data", 'data': main_list,'totalRecord':st_record}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def approved_st_list(request):
    new_list = list()
    user_details = UserDetails.objects.filter(is_deleted=False).filter(Q(role=4))
    for users in user_details:
        temp_dict = {
            'id': users.pk,
            'fullname': users.fullname,
            'email': users.email,
            'role': users.role.role_name
        }
        new_list.append(temp_dict)
    return Response({'message': "Student Data", 'data': new_list}, status=status.HTTP_200_OK)

    # return Response({'message': "Permission Denied",'data':[]}, status=status.HTTP_401_UNAUTHORIZED)


# @swagger_auto_schema(
#         method='post',
#        request_body=StudentUploadDoc
#     )
#
# @api_view(['POST'])
# @authentication_classes([])
# @permission_classes([])
# def UploadDocument(request):
#     files = request.FILES.getlist('files')
#     file_name = request.data['filename']
#     # file_name = file_name+str(datetime.now()).replace(" ",'')+request.data['extension']
#     base64 = request.data['base64']
#     space_name, client = aws_session()
#     client.put_object(Body=base64, Bucket=space_name, Key=file_name)
#     return Response({'message':'File Uploaded Successfully','data':file_name},status=status.HTTP_200_OK)
#


# @swagger_auto_schema(
#         method='GET',
#         manual_parameters=[
#             openapi.Parameter('Key', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
#         ]
#     )
# @api_view(['GET'])
# @authentication_classes([])
# @permission_classes([])
# def get_key(request):
#
#     key = request.query_params.get('Key')
#     space_name,client = aws_session()
#     params = {'Bucket': space_name, 'Key': key}
#     url = client.generate_presigned_url('get_object', Params=params,ExpiresIn=40000)
#     return Response({'url':url})
#
# #
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('files', in_=openapi.IN_FORM, type=openapi.TYPE_ARRAY,
                          items=openapi.Items(type=openapi.TYPE_FILE), required=True,
                          description='List of files to upload'),
    ],
    operation_description="Upload multiple files",
    responses={200: "Files uploaded successfully"},
)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@parser_classes([MultiPartParser, FormParser])
def UploadDocument(request):
    files = request.FILES.getlist('files')
    # file_name = request.data['filename']+request.data['extension']
    # file_name = file_name+str(datetime.now()).replace(" ",'')+request.data['extension']
    # base64 = request.data['base64']
    space_name, client = aws_session()
    main_list = list()
    for f_data in files:
        key = str(datetime.now()).replace(" ", '') + f_data.name
        client.put_object(Body=f_data, Bucket=space_name, Key=key)
        temp_dict = {
            'key': key,
            'filename': f_data.name
        }
        main_list.append(temp_dict)
    return Response({'message': 'File Uploaded Successfully', 'data': main_list}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('UserID', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
                         openapi.Parameter('approved', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, required=True),
                     ]
                     )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_request(request):
    userid = request.query_params.get('UserID')
    if request.query_params.get('approved') == 'true':
        stu_obj = Studentrecord.objects.get(userid=userid)
        stu_obj.isapproved = True
        stu_obj.save()
        user_obj = UserDetails.objects.get(id=userid)
        user_obj.is_deleted = False
        user_obj.save()
        return Response({'message': f'{user_obj.fullname} approved successfully', 'data': []},
                        status=status.HTTP_200_OK)
    elif request.query_params.get('approved') == 'false':
        stu_obj = Studentrecord.objects.get(userid=userid)
        stu_obj.isrejected = True
        stu_obj.save()
        return Response({'message': 'Student Rejected successfully', 'data': []},
                        status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Approved Bit is not correct', 'data': []},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rejected_students(request):
    main_url_list = list()
    main_list = list()
    st_data = Studentrecord.objects.filter(isrejected=True).filter(isapproved=False)
    for student in st_data:
        for key in student.Records:
            url = get_key(key)
            main_url_list.append(url)
        st_dict = {
            'Student Name': student.userid.fullname,
            'Student Id': student.userid.pk,
            'Email': student.userid.email,
            'files':[{
                'FileName': student.FileNames,
            'Urls': main_url_list

                      }]

        }
        main_list.append(st_dict)
    return Response({'message': "Student Data", 'data': main_list}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('StudentID', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def restore_student(request):
    st_id = request.query_params.get('StudentID')
    try:
        obj = Studentrecord.objects.get(userid=st_id)
    except:
        return Response({'message': "Please Enter a valid id", }, status=status.HTTP_400_BAD_REQUEST)
    obj.isrejected = False
    obj.save()
    return Response({'message': 'Student Restore Successfully'}, status=status.HTTP_200_OK)
