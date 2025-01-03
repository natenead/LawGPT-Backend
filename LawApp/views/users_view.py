from rest_framework.views import APIView
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from rest_framework.response import Response
from langchain_core.prompts import ChatPromptTemplate
import boto3, requests
from botocore.client import Config
from ..models import Userquerydocrecord
from ..serializers import (
    CustomUserSerializer,
    LoginSerializer,
    UserRole,
    CustomUserSerializerForPut,
    PaymentMethod,
    APIKey,
    UpdatePassword,
    UserLogSerializer,
    ToggleOption,
    StatesList,
    FreeTrail
)
import random, string
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from django.db import connection
import stripe
from langchain.memory import ConversationBufferWindowMemory
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import login, authenticate
from rest_framework.request import Request
from drf_yasg import openapi
from ..tokens import create_jwt_pair_for_user
from datetime import datetime
from langchain.memory import ConversationBufferWindowMemory
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate
from rest_framework import status
from django.db.models import Q, Count
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from ..utils import user_role, hashedAPIKey
from .db_utils import *
from datetime import timezone
from langchain.chains import ConversationChain
import json
from .. import utils
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
import sendgrid
import jwt, random
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from rest_framework.viewsets import ViewSet
load_dotenv()
gpt_model_name = os.getenv('gpt_model_name')

'''
This class is used for login and generate token
'''

with open(os.getcwd() + '/LawApp/views/federal.json') as fp:
    federal_data = json.load(fp)


class LoginView(APIView):
    permission_classes = []

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request: Request):

        new_list = list()
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)

        if user is not None and user.is_deleted == False:
            tokens = create_jwt_pair_for_user(user)
            user_last_login = Userlastlogin(userid=user, createddate=datetime.now())
            user_last_login.save()
            query = 0
            document = 0
            try:
                query = user.userquerydocrecord_set.all()[0].query_number
                document = user.userquerydocrecord_set.all()[0].document_number
            except:
                pass
            my_dict = {
                'id': user.pk,
                'name': user.fullname,
                'email': user.email,
                'role': user.role.pk,
                'toggle_option': user.toggle_option,
                'query':query,
                'documents':document,
            }
            new_list.append(my_dict)
            x = ''.join(
                random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))

            # email_response = requests.post(
            #     "https://api.mailgun.net/v3/mail.law.co/messages",
            #     auth=("api", os.getenv("MAILGUN_KEY")),
            #     data={"from": os.environ.get('SENDER_EMAIL'),
            #           "to": user.email,
            #           "subject": "PIN Request For Login",
            #           "text": f"Greetings,We hope this message finds you in good health. This communication is to "
            #                   f"provide you with your unique PIN, marked as {x}. Kindly input this PIN into your "
            #                   f"Login Window at your earliest convenience."})
            if user.toggle_option == True:
                message = Mail(
                    from_email='accounts@law.co',
                    to_emails=user.email,
                    subject='Your LAW.co Login Code',
                    html_content=f"<h3>Thank you for logging into Law.co <br> Please use the following PIN to access your account:<br></h3>"
                                 f"<h2>{x}</h2>")
                try:
                    sg = SendGridAPIClient(os.getenv("NEW_SENDGRID_KEY"))
                    response = sg.send(message)
                    # print(response.status_code)
                    # print(response.body)
                    # print(response.headers)
                except Exception as e:
                    return Response(data={"message": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)

                user_token = Usertoken(userid=user, createddate=datetime.now(timezone.utc), isarchived=False, token=x)
                user_token.save()
            response = {"message": "Login Successfull", "tokens": tokens, 'data': new_list}
            return Response(data=response, status=status.HTTP_200_OK)

        else:
            try:
                obj = Studentrecord.objects.get(userid=user.pk)
                return Response(data={"message": "Kindly Wait for approval"}, status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response(data={"message": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)

            # return Response(data={"message": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)


'''
This class is used for get all users data,get student data
'''


class UserData(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('studentData', openapi.IN_QUERY, type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_STRING), allow_empty_value=True,
                              required=False),
            openapi.Parameter('UserName', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True,
                              required=False),
            openapi.Parameter('roleId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, allow_empty_value=True,
                              required=False),
            openapi.Parameter('pageNumber', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True,
                              required=False, default=1),
            openapi.Parameter('pageSize', openapi.IN_QUERY, type=openapi.TYPE_STRING, allow_empty_value=True,
                              required=False, default=10)
        ]
    )
    # @swagger_auto_schema(request_body=)
    def get(self, request):
        main_list = list()
        user_name = request.query_params.get('UserName')
        role_id = request.query_params.get('roleId')
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

        if request.user.role_id == 5:
            t_records = 0
            condition = Q()
            if role_id is not None and role_id != "":
                if int(role_id) in [1, 2, 3, 4]:
                    condition &= Q(role=int(role_id))
                else:
                    return Response({'data': None, "message": "Please Enter Valid RoleID"},
                                    status=status.HTTP_400_BAD_REQUEST)

            else:
                condition &= (~Q(role=5))
                condition &= (~Q(role=3))
            if request.query_params.get('studentData') == 'true':
                condition &= Q(role=4)
            if (user_name == "") or (user_name is None):
                user_details = UserDetails.objects.annotate(total_records=Count('*')).filter(condition).filter(
                    is_deleted=False).order_by('-created_date')[start_size:end_size]
                t_records = UserDetails.objects.annotate(total_records=Count('*')).filter(condition).filter(
                    is_deleted=False).count()
            else:
                user_details = UserDetails.objects.filter(condition).filter(is_deleted=False).filter(
                    fullname__icontains=user_name)[start_size:end_size]
                t_records = UserDetails.objects.filter(condition).filter(is_deleted=False).filter(
                    fullname__icontains=user_name).count()
            for users in user_details.iterator():
                temp_dict = {
                    'id': users.pk,
                    'fullname': users.fullname,
                    'email': users.email,
                    'role': users.role.role_name,
                    'toggleOption': users.toggle_option

                }
                main_list.append(temp_dict)
            # main_list.reverse()
            return Response({"msg": 'User Data', 'data': main_list, 'totalRecords': t_records},
                            status=status.HTTP_200_OK)
        elif request.user.role_id == 1:
            user_data = AdminUser.present.filter(adminid=request.user.pk)
            t_records = AdminUser.present.filter(adminid=request.user.pk).count()

            new_list = list()
            # t_records = 0
            for obj in user_data.iterator():
                if (user_name == "") or (user_name is None):
                    try:
                        user_price_ = Userpricing.objects.filter(cancelpayment=False).get(adminuserid=obj.userid.pk)
                        # t_records = Userpricing.objects.filter(cancelpayment=False).filter(adminuserid=obj.userid.pk).count()
                        temp_dict = {
                            'subscribe_id': user_price_.subscribe_id,
                            'subscribe_date': str(user_price_.createddate),
                            'id': obj.userid.pk,
                            'fullname': obj.userid.fullname,
                            'email': obj.userid.email,
                            'role': obj.userid.role.role_name,
                            'toggleOption': obj.userid.toggle_option
                            # 'toggleOption': True

                        }
                        new_list.append(temp_dict)
                    except:
                        pass

                elif obj.userid.fullname.lower() == user_name.lower():
                    try:
                        user_price_ = Userpricing.objects.filter(cancelpayment=False).get(adminuserid=obj.userid.pk)
                        t_records = Userpricing.objects.filter(cancelpayment=False).filter(
                            adminuserid=obj.userid.pk).count()
                        temp_dict = {
                            'subscribe_id': user_price_.subscribe_id,
                            'subscribe_date': str(user_price_.createddate),
                            'id': obj.userid.pk,
                            'fullname': obj.userid.fullname,
                            'email': obj.userid.email,
                            'role': obj.userid.role.role_name,
                            # 'toggleOption': True
                            'toggleOption': obj.userid.toggle_option

                        }
                        new_list.append(temp_dict)
                    except:
                        pass
            new_list.reverse()
            return Response({"msg": 'User Data', 'data': new_list, 'totalRecords': t_records},
                            status=status.HTTP_200_OK)
        else:
            return Response({"msg": 'User Data', 'data': []}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CustomUserSerializerForPut)
    def put(self, request):

        obj = UserDetails.objects.get(id=request.user.pk)
        obj.fullname = request.data.get("fullname")
        obj.email = request.data.get("email")
        obj.save()
        return Response({"msg": 'Update Record for User',
                         'data': {"Name": request.data.get("fullname"), 'email': request.data.get("email")}},
                        status=status.HTTP_200_OK)
        # elif request.user.role.pk == 5:
        #     obj = UserDetails.objects.get(id=id)
        #     obj.fullname = request.data.get("fullname")
        #     obj.email = request.data.get("email")
        #     obj.save()
        #     return Response({"msg": 'Update Record for User', 'data': []}, status=status.HTTP_200_OK)


# @swagger_auto_schema(method='post', request_body=CustomUserSerializer)
# @swagger_auto_schema(method='post', request_body=PaymentMethod)
# @api_view(['POST'])
# @authentication_classes([])
# @permission_classes([])
# def signup(request):
#     stripe.api_key = os.getenv('stripe_dev_key')
#     request.data['role'] = int(request.data['role'])
#     deduct_price = os.getenv('stripe_law_admin')
#     extension_paid = False
#     if request.data['price'] == 50:
#         deduct_price = os.getenv('stripe_extesnion_key')
#         extension_paid = True
#     mydict = {
#         'fullname': request.data['fullname'],
#         'email': request.data['email']
#     }
#     try:
#
#         user_obj = UserDetails.objects.get(email=request.data['email'])
#         if user_obj.is_deleted:
#             if request.data['role'] == 1:
#
#                 new_dict = request.data
#                 token_ = new_dict['token']
#                 price_ = new_dict['price']
#                 try:
#                     customer = stripe.Customer.create(
#
#                         email=new_dict['email'],
#                         name=new_dict['fullname'],
#                         source=new_dict['token']
#
#                     )
#                     st_ = stripe.Subscription.create(
#                         customer=customer.id,
#                         items=[
#                             # {"price": os.getenv('stripe_law_admin_prod')},
#                             {"price": deduct_price}
#                         ],
#                     )
#                     user_price = Userpricing(customerid=customer.id, token=token_, userid=user_obj,
#                                              createddate=datetime.now(), payment=price_, adminuserid=user_obj.pk,
#                                              subscribe_id=st_.id, cancelpayment=False)
#                     user_price.save()
#                 except Exception as e:
#                     return Response({'message': f"Payment Failed {e}"}, status=status.HTTP_400_BAD_REQUEST)
#             try:
#                 mydict['id'] = user_obj.pk
#                 user_obj.is_deleted = False
#                 user_obj.fullname = request.data['fullname']
#                 user_obj.set_password(request.data['password'])
#                 user_obj.extension_paid = True
#                 user_obj.role = Role.objects.get(role_id=request.data['role'])
#                 user_obj.save()
#                 json_data = {
#                     "email": request.data['email'],
#                     "firstName": request.data['fullname'].split()[0],
#                     "lastName": " ".join(request.data['fullname'].split()[1:]),
#                     "createdDate": str(datetime.now()),
#
#                 }
#                 # r = requests.post('https://hooks.zapier.com/hooks/catch/1229844/3laqmwn/',json=json_data)
#                 r = requests.post(
#                     'https://services.leadconnectorhq.com/hooks/tJcbYsf8vodoY73JXEsB/webhook-trigger/8161f044-beaa-4fd4-8b1f-86845d15b22f',
#                     json=json_data)
#                 log_obj = Userlogs(userid=user_obj.pk, logdata=f"New Account Created for {request.data['fullname']}",
#                                    createddate=datetime.now(), isarchived=False)
#                 log_obj.save()
#                 return Response({'message': "User Created Successfully", "data": mydict}, status=status.HTTP_200_OK)
#             except Exception as e:
#                 return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({'message': "User Already Exists", 'data': []}, status=status.HTTP_400_BAD_REQUEST)
#     except:
#         new_dict = request.data
#         token_ = new_dict['token']
#         price_ = new_dict['price']
#
#         if request.data['role'] == 1:
#             '''
#             Change API KEY
#
#             # apikey = new_dict['apikey']
#             # del new_dict['apikey']
#             '''
#
#             try:
#                 customer = stripe.Customer.create(
#
#                     email=new_dict['email'],
#                     name=new_dict['fullname'],
#                     source=new_dict['token']
#
#                 )
#                 st_ = stripe.Subscription.create(
#                     customer=customer.id,
#                     items=[
#                         {"price": deduct_price},
#                         # {"price": os.getenv('stripe_law_admin_prod')},
#                     ],
#                 )
#             except Exception as e:
#                 return Response({'message': f"Payment Failed {e}"}, status=status.HTTP_400_BAD_REQUEST)
#         del new_dict['token']
#         del new_dict['price']
#         '''
#
#             write logics here....
#             if condition
#         '''
#         serializer = CustomUserSerializer(data=new_dict)
#         if serializer.is_valid():
#             ser = serializer.save(request,extension_paid)
#             mydict['id'] = ser.pk
#             if request.data['role'] == 1:
#                 user_price = Userpricing(customerid=customer.id, token=token_, userid=ser, createddate=datetime.now(),
#                                          payment=price_, adminuserid=ser.pk, subscribe_id=st_.id, cancelpayment=False)
#                 user_price.save()
#                 # hash_key = hashedAPIKey(apikey)
#                 # user_price_ = Userapikeys(userid=ser, apikey=apikey, isdelete=False)
#                 # user_price_.save()
#                 log_obj = Userlogs(userid=ser, logdata=f"New Account Created for {request.data['fullname']}",
#                                    createddate=datetime.now(), isarchived=False)
#                 log_obj.save()
#             json_data = {
#                 "email": request.data['email'],
#                 "firstName": request.data['fullname'].split()[0],
#                 "lastName": " ".join(request.data['fullname'].split()[1:]),
#                 "createdDate": str(datetime.now()),
#
#             }
#             # r = requests.post('https://hooks.zapier.com/hooks/catch/1229844/3laqmwn/', json=json_data)
#             r = requests.post(
#                 'https://services.leadconnectorhq.com/hooks/tJcbYsf8vodoY73JXEsB/webhook-trigger/8161f044-beaa-4fd4-8b1f-86845d15b22f',
#                 json=json_data)
#             return Response({'message': "User Created Successfully", "data": mydict}, status=status.HTTP_200_OK)
#
#         return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



@swagger_auto_schema(method='post', request_body=PaymentMethod)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def signup(request):
    request.data['role'] = int(request.data['role'])
    mydict = {
        'fullname': request.data['fullname'],
        'email': request.data['email']
    }
    try:

        user_obj = UserDetails.objects.get(email=request.data['email'])
        if user_obj.is_deleted:
            if request.data['role'] == 1:
                new_dict = request.data
                token_ = new_dict['token']
                price_ = new_dict['price']
                try:
                    customer = stripe.Customer.create(

                        email=new_dict['email'],
                        name=new_dict['fullname'],
                        source=new_dict['token']

                    )
                    st_ = stripe.Subscription.create(
                        customer=customer.id,
                        items=[
                            {"price": os.getenv('stripe_law_admin_prod')},
                        ],
                    )
                    user_price = Userpricing(customerid=customer.id, token=token_, userid=user_obj,
                                             createddate=datetime.now(), payment=price_, adminuserid=user_obj.pk,
                                             subscribe_id=st_.id, cancelpayment=False)
                    user_price.save()
                except Exception as e:
                    return Response({'message': f"Payment Failed {e}"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                mydict['id'] = user_obj.pk
                user_obj.is_deleted = False
                user_obj.fullname = request.data['fullname']
                user_obj.set_password(request.data['password'])
                user_obj.role = Role.objects.get(role_id=request.data['role'])
                user_obj.save()
                json_data = {
                    "email": request.data['email'],
                    "firstName": request.data['fullname'].split()[0],
                    "lastName": " ".join(request.data['fullname'].split()[1:]),
                    "createdDate": str(datetime.now()),

                }
                # r = requests.post('https://hooks.zapier.com/hooks/catch/1229844/3laqmwn/',json=json_data)
                r = requests.post(
                    'https://services.leadconnectorhq.com/hooks/tJcbYsf8vodoY73JXEsB/webhook-trigger/8161f044-beaa-4fd4-8b1f-86845d15b22f',
                    json=json_data)
                log_obj = Userlogs(userid=user_obj.pk, logdata=f"New Account Created for {request.data['fullname']}",
                                   createddate=datetime.now(), isarchived=False)
                log_obj.save()
                return Response({'message': "User Created Successfully", "data": mydict}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': "User Already Exists", 'data': []}, status=status.HTTP_400_BAD_REQUEST)
    except:
        new_dict = request.data
        token_ = new_dict['token']
        price_ = new_dict['price']

        if request.data['role'] == 1:
            apikey = new_dict['apikey']
            del new_dict['apikey']

            try:
                customer = stripe.Customer.create(

                    email=new_dict['email'],
                    name=new_dict['fullname'],
                    source=new_dict['token']

                )
                st_ = stripe.Subscription.create(
                    customer=customer.id,
                    items=[
                        # {"price": os.getenv('stripe_law_admin')},
                        {"price": os.getenv('stripe_law_admin_prod')},
                    ],
                )
            except Exception as e:
                return Response({'message': f"Payment Failed {e}"}, status=status.HTTP_400_BAD_REQUEST)
        del new_dict['token']
        del new_dict['price']

        serializer = CustomUserSerializer(data=new_dict)
        if serializer.is_valid():
            ser = serializer.save(request)
            mydict['id'] = ser.pk
            if request.data['role'] == 1:
                user_price = Userpricing(customerid=customer.id, token=token_, userid=ser, createddate=datetime.now(),
                                         payment=price_, adminuserid=ser.pk, subscribe_id=st_.id, cancelpayment=False)
                user_price.save()
                # hash_key = hashedAPIKey(apikey)
                user_price_ = Userapikeys(userid=ser, apikey=apikey, isdelete=False)
                user_price_.save()
                log_obj = Userlogs(userid=ser, logdata=f"New Account Created for {request.data['fullname']}",
                                   createddate=datetime.now(), isarchived=False)
                log_obj.save()
            json_data = {
                "email": request.data['email'],
                "firstName": request.data['fullname'].split()[0],
                "lastName": " ".join(request.data['fullname'].split()[1:]),
                "createdDate": str(datetime.now()),

            }
            # r = requests.post('https://hooks.zapier.com/hooks/catch/1229844/3laqmwn/', json=json_data)
            r = requests.post(
                'https://services.leadconnectorhq.com/hooks/tJcbYsf8vodoY73JXEsB/webhook-trigger/8161f044-beaa-4fd4-8b1f-86845d15b22f',
                json=json_data)
            return Response({'message': "User Created Successfully", "data": mydict}, status=status.HTTP_200_OK)

        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def userrole(request):
    obj = Role.objects.all()
    data = UserRole(obj, many=True)

    return Response({'message': "User Roles", "data": data.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_bot_id(request):
    bot_id = Userbot(userid=request.user, createddate=datetime.now(), isarchive=False)
    bot_id.save()
    return Response({'message': "Latest Bot Id", "data": bot_id.pk}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_storage(request):
    '''

    This API is used to get the latest storage used by user
    '''
    if request.user.role.pk == 3:
        admin_id = AdminUser.present.get(userid=request.user.pk).adminid
        user_storage = Userstorage.objects.get(userid=admin_id.pk).storage
    else:
        user_storage = Userstorage.objects.get(userid=request.user.pk).storage
    return Response({'message': "Get User Storage", "data": user_storage}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='post', request_body=CustomUserSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def CreateUserByAdmin(request):
    new_list = list()
    mydict = {
        'fullname': request.data['fullname'],
        'email': request.data['email']
    }
    if request.user.role_id == 5:
        t_records = UserDetails.objects.annotate(total_records=Count('*')).filter(
            is_deleted=False).filter(~Q(role=5)).filter(~Q(role=3)).count()
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            # .filter(~Q(role=4)) this is for students
            obj = serializer.save(request,False)
            if request.data['role'] == 4:
                user_details = UserDetails.objects.filter(is_deleted=False).filter(Q(role=4)).order_by('-created_date')[
                               0:10]
                for users in user_details:
                    temp_dict = {
                        'id': users.pk,
                        'fullname': users.fullname,
                        'email': users.email,
                        'role': users.role.role_name
                    }
                    new_list.append(temp_dict)
            else:
                user_details = UserDetails.objects.filter(is_deleted=False).filter(
                    ~Q(role=5)).filter(~Q(role=3)).filter(~Q(role=4)).order_by('-created_date')[0:10]
                for users in user_details:
                    temp_dict = {
                        'id': users.pk,
                        'fullname': users.fullname,
                        'email': users.email,
                        'role': users.role.role_name
                    }
                    new_list.append(temp_dict)
            json_data = {
                "email": request.data['email'],
                "firstName": request.data['fullname'].split()[0],
                "lastName": " ".join(request.data['fullname'].split()[1:]),
                "createdDate": str(datetime.now()),

            }
            # r = requests.post('https://hooks.zapier.com/hooks/catch/1229844/3laqmwn/', json=json_data)
            r = requests.post(
                'https://services.leadconnectorhq.com/hooks/tJcbYsf8vodoY73JXEsB/webhook-trigger/8161f044-beaa-4fd4-8b1f-86845d15b22f',
                json=json_data)
            # new_list.reverse()
            return Response({'message': "User Created Successfully", "data": new_list, 'totalRecords': t_records},
                            status=status.HTTP_200_OK)

        else:
            return Response({'message': "Email Already Exists", }, status=status.HTTP_400_BAD_REQUEST)
    if request.user.role_id == 1:
        t_records = AdminUser.present.filter(adminid=request.user.pk).count()
        # count_data = AdminUser.present.filter(adminid=request.user.pk).count()
        # if count_data > 3:
        #     return Response({'message': "You dont have permission to create more than 4 Users"}, status=status.HTTP_400_BAD_REQUEST)
        request.data['role'] = 3
        cust = Userpricing.objects.filter(userid=request.user.pk)
        try:
            cust_id = cust[0].customerid
        except:
            return Response({'message': "You Dont have enough balance", }, status=status.HTTP_400_BAD_REQUEST)
        cust_token = cust[0].token
        try:
            st_ = stripe.Subscription.create(
                customer=cust_id,
                items=[
                    {"price": os.getenv('stripe_law_user')},
                    # {"price": os.getenv('stripe_law_user_prod')},
                ],
            )
        except Exception as e:
            return Response({'message': f"Payment Failed {e}"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save(request,False)
            mydict['id'] = obj.pk
            admin_obj = AdminUser(adminid=UserDetails(id=request.user.pk), userid=obj, is_deleted=False)
            admin_obj.save()
            user_price = Userpricing(customerid=cust_id, token=cust_token, userid=request.user,
                                     createddate=datetime.now(),
                                     payment=25, adminuserid=obj.pk, subscribe_id=st_.id, cancelpayment=False)
            user_price.save()
            user_data = AdminUser.present.filter(adminid=request.user.pk)

            for obj in user_data:
                try:
                    user_price_ = Userpricing.objects.filter(cancelpayment=False).get(adminuserid=obj.userid.pk)
                    _serializer_data = CustomUserSerializer(obj.userid).data
                    _serializer_data['subscribe_id'] = user_price_.subscribe_id
                    _serializer_data['subscribe_date'] = str(user_price_.createddate)
                    new_list.append(_serializer_data)
                except:
                    pass
            new_list.reverse()
            json_data = {
                "email": request.data['email'],
                "firstName": request.data['fullname'].split()[0],
                "lastName": " ".join(request.data['fullname'].split()[1:]),
                "createdDate": str(datetime.now())
            }
            # r = requests.post('https://hooks.zapier.com/hooks/catch/1229844/3laqmwn/', json=json_data)
            r = requests.post(
                'https://services.leadconnectorhq.com/hooks/tJcbYsf8vodoY73JXEsB/webhook-trigger/8161f044-beaa-4fd4-8b1f-86845d15b22f',
                json=json_data)
            log_obj = Userlogs(userid=request.user, logdata=f"{request.user.fullname} Create New Account for its User",
                               createddate=datetime.now(), isarchived=False)
            log_obj.save()
            return Response({'message': "User Created Successfully", "data": new_list, 'totalRecords': t_records},
                            status=status.HTTP_200_OK)
        else:
            return Response({'message': "Email Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': "You dont have permission to create new User"}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='DELETE',
    manual_parameters=[
        openapi.Parameter('userid', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),

    ]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_by_admin(request):
    userid = request.query_params.get('userid')
    if request.user.role_id == 1:
        user_data = AdminUser.present.filter(adminid=request.user.pk).filter(userid=userid)
        if user_data.exists():
            UserDetails.objects.filter(id=userid).update(is_deleted=True)
            user_data.update(is_deleted=True)
            Userbot.objects.filter(userid=userid).update(isarchive=True)
            return Response({'message': "User Deleted Successfully"}, status=status.HTTP_200_OK)
    elif request.user.role_id == 5:
        admin_data = AdminUser.present.filter(adminid=userid)
        if admin_data:
            AdminUser.present.filter(adminid=userid).update(is_deleted=True)
            del_list = list(AdminUser.present.filter(adminid=userid).values_list('userid', flat=True))
            del_list.append(int(userid))
            UserDetails.objects.filter(pk__in=del_list).update(is_deleted=True)
        else:
            UserDetails.objects.filter(pk=userid).update(is_deleted=True)
            # users.update(is_deleted=True)
            # users.save()
        return Response({'message': "User Deleted Successfully"}, status=status.HTTP_200_OK)
    return Response({'message': "You dont have permission to delete User"}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='GET', manual_parameters=[
    openapi.Parameter('email', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True), ])
@api_view(['GET'])
# @authentication_classes([])
@permission_classes([])
def verifyEmail(request):
    email = request.query_params.get('email')
    try:
        obj = UserDetails.objects.filter(is_deleted=False).get(email=email)
        return Response({'message': "Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({'message': "User Does not exists"}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', request_body=APIKey)
@api_view(['POST'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def get_api_key(request):
    apikey = request.data['apikey']
    if request.user.is_authenticated:
        try:
            obj = Userapikeys.objects.get(userid=request.user.pk)
            obj.isdelete = False
            obj.apikey = apikey
            obj.save()
        except:
            # hash_key = hashedAPIKey(apikey)
            obj = Userapikeys(userid=request.user, apikey=apikey, isdelete=False)
            obj.save()
    else:
        return Response({'message': "User is Not Authenticate"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': "API Key save successfully"}, status=status.HTTP_200_OK)


@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def profile(request):
    data = {
        'id': request.user.pk,
        'UserName': request.user.fullname,
        'Email': request.user.email,
        'role': request.user.role_id,

    }
    return Response({'data': data}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='POST', request_body=StatesList, manual_parameters=[
    openapi.Parameter('query', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
    openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    openapi.Parameter('titleSearch', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, required=True,enum=[True,False]),

])
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def fetchCasesFromDb(request):
    cursor = connection.cursor()
    path = os.path.abspath("data.json")
    query = request.query_params.get("query")
    title_search = request.query_params.get("titleSearch")
    states_list = request.data.get("statesList")

    # cache_key = query.lower() +" "+ " ".join(states_list)
    try:
        opinion_list = []
        # cache_data = cache.get(key=cache_key)
        # if cache_data:
        #     return Response({"message": "Response Generated Successfully!",
        #                      "Query": query,
        #                      "Answer": "Successfully get the answers",
        #                      "Sources": cache_data[0],
        #                      "main": cache_data[1],
        #                      "citation": cache_data[2],
        #                      "casebody": cache_data[3],
        #                      "opinion": cache_data[4],
        #                      "attorney": cache_data[5],
        #                      "court": cache_data[6],
        #                      "judges": cache_data[7],
        #                      "jurisdiction": cache_data[8],
        #                      "parties": cache_data[9],
        #                      "reporter": cache_data[10]
        #                      }, status=status.HTTP_200_OK)
        # try:
        # opinion_list.extend(search_keywords_in_main(query))
        # except Exception as e:
        #     print(e)
        # opinion_list.extend(search_keywords_in_cites_to(query))

        serach_keyword = search_keywords_in_opinion(query,request.query_params.get("titleSearch"))
        if request.query_params.get("titleSearch") == 'true':
            opinion_list.extend(serach_keyword)
        else:
            opinion_list.extend(serach_keyword[0])
        # for lst_ in serach_keyword[1]:
        #     cache.get(key=lst_.replace("%",'') +' ' +  " ".join(states_list))
        # results = list(set(opinion_list))
        # k = random.randint(40, 50)
        opinion_list = list(set(opinion_list))
        if states_list[0] == 'string':
            states_list = []
        # results = opinion_list[0:k]
        id_string = ', '.join(str(id) for id in opinion_list)

        try:
            main, citesto, citation, casebody, opinion, attorney, court, judges, jurisdiction, parties, reporter,op_list = extract_keyword_data_from_db(
                opinion_list, states_list)
            # for _ in serach_keyword[1]:

            # cache.set(
            #     key=cache_key,
            #     value=(opinion_list,main,  citation, casebody, opinion, attorney, court, judges, jurisdiction, parties, reporter),
            #
            # )
            # main, citation, casebody = updated_extract_data_from_db(id_string,opinion_list, cursor)            # with open(path, 'r') as fp:
            # with open(os.getcwd() + '/LawApp/views/data.json') as fp:
            #     data = json.load(fp)
            # for result in citesto:
            #     count = 0
            #     for state_name in data.keys():
            #         if result['Reporter'] in data[state_name]:
            #             result['Category'] = state_name
            #             count += 1
            #     if count == 0:
            #         result['Category'] = 'United States'
        except Exception as e:
            print(e, "------------------------")

        return Response({"message": "Response Generated Successfully!",
                         "Query": query,
                         "Answer": "Successfully get the answers",
                         "Sources": op_list,
                         "main": main,
                         "citation": citation,
                         "casebody": casebody,
                         "opinion": opinion,
                         "attorney": attorney,
                         "court": court,
                         "judges": judges,
                         "jurisdiction": jurisdiction,
                         "parties": parties,
                         "reporter": reporter
                         }, status=status.HTTP_200_OK)
    except Exception as ex:
        print(ex, "==================================")
        return Response({"error": "Error while fetching cases from keywords"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('userQuery', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
    openapi.Parameter('botId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    openapi.Parameter('userId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    ])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposition_chatbot(request):
    cursor = connection.cursor()
    userQuery = request.query_params.get("userQuery")
    botId = request.query_params.get("botId")
    userId = request.query_params.get("userId")

    try:
        question_list = []
        answer_list = []
        history_list = []

        # row = DepositionChatHistory.objects.values_list("prompt", "response").filter(userid=userId, botid=botId).order_by("createddate")[:5]
        check_deposition_chat_record = f"""
                                      SELECT prompt,response FROM "DepositionChatHistory" WHERE "userId"={int(userId)} AND "botId"={int(botId)}  ORDER BY "createdDate" ASC LIMIT  5
                        """
        cursor.execute(check_deposition_chat_record)
        row = cursor.fetchall()

        if len(row) < 5:
            answer_from_deposition = ""

            # row_topic = Depositionhistorytopics.objects.values_list("topicid", "topics", "situation").filter(botid=botId).order_by("createddate")[:9]
            check_from_deposition_topic = f"""
                    SELECT "TopicId", "Topics", situation FROM "DepositionHistoryTopics" WHERE "BotId"={int(botId)}  ORDER BY "CreatedDate" ASC LIMIT  9
                """
            cursor.execute(check_from_deposition_topic)
            row_topic = cursor.fetchall()
            situation = ""
            for record in row_topic:
                topic_id = record[0]
                topic = record[1]
                situation = record[2]
                # row_topic_questions = Depositionhistoryquestions.objects.values_list("question").filter(tid=topic_id).order_by("createddate")[:4]
                check_from_deposition_questions = f"""
                 SELECT "Question" FROM "DepositionHistoryQuestions" WHERE "TId"={int(topic_id)}  ORDER BY "CreatedDate" ASC LIMIT  4
                 """
                cursor.execute(check_from_deposition_questions)
                row_topic_questions = cursor.fetchall()
                answer_from_deposition += "Deposition Details: \n"
                answer_from_deposition += f"\n\nTopic: {topic}\n Questions:"
                for question in row_topic_questions:
                    answer_from_deposition += f"{question[0]}\n"
            question_list.append(situation)
            answer_list.append(answer_from_deposition)
            history_list.append(f"Prompt: {situation}")
            history_list.append(f"Response: {answer_from_deposition}")
        if len(row):
            for i in row:
                question = i[0]
                answer = i[1]
                question_list.append(question)
                answer_list.append(answer)
                history_list.append(f"Prompt: {question}")
                history_list.append(f"Response: {answer}")
        result_string = " ".join(history_list)

        # logger.info("Successfully Load the chat history from the database")
    except Exception as ex:
        # logger.critical(f" Unable to read Data from Database: {str(ex)}")
        return Response({"error": "Database Connection Error."}, status=status.HTTP_400_BAD_REQUEST)

    # try:
    #
    #     memory_var = ConversationBufferWindowMemory(human_prefix='Prompt', ai_prefix='Response', return_messages=True,
    #                                                 k=5)
    #     for question, answer in zip(question_list, answer_list):
    #         memory_var.save_context({"Prompt": question}, {"Response": answer})
    #
    # except Exception as e:
    #     # logger.critical(str(e))
    #     return Response({"error": "OpenAI Not Available."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # prompt_template = """
        # You are a Legal Expert. Your role is to write or improve a deposition based on the chat history and the latest user prompt. \
        # You must return the improved deposition in the response.\
        # chat history: {history}
        # latest user prompt: {input}
        # Improved deposition:
        # """
        # CONDENSEprompt = PromptTemplate(
        #     template=prompt_template, input_variables=["input", "history"], validate_template=False)
        # conv_chain = ConversationChain(
        #     prompt=CONDENSEprompt,
        #     llm=ChatOpenAI(model='gpt-3.5-turbo-16k'),
        #     memory=memory_var,
        #     verbose=True
        # )
        # generated_response = conv_chain.predict(input=userQuery)
        prompt_template = """
                You are a Legal Expert. Your role is to write or improve a deposition based on the chat history and the latest user prompt. \
                You must return the improved deposition in the response.\
                chat history: {history}
                latest user prompt: {input}
                Improved deposition:
                """
        chat_prompt = ChatPromptTemplate.from_template(prompt_template)
        question_fetcher = itemgetter("input")
        setup_and_retrieval = {"history": itemgetter("history"),
                               "input": question_fetcher}
        llm = ChatOpenAI(model=gpt_model_name)
        output_parser = StrOutputParser()
        chat_chain = setup_and_retrieval | chat_prompt | llm | output_parser
        generated_response = chat_chain.invoke({"input": userQuery, "history": result_string})
        current_utc_time = datetime.now(timezone.utc)
        desired_timezone = timezone(timedelta(hours=-7))
        current_time_with_timezone = current_utc_time.astimezone(desired_timezone)
        formatted_timestamp = current_time_with_timezone.strftime("%Y-%m-%d %H:%M:%S%z")
        data = (userId, str(userQuery), str(generated_response), str(formatted_timestamp), botId)
        insert_query = f'INSERT INTO "DepositionChatHistory" ("userId",prompt,response,"createdDate","botId") VALUES (%s, %s, %s, %s, %s)'
        try:
            cursor.execute(insert_query, data)
        except Exception as e:
            # logger.critical(e)
            return Response({"error": "Database Connection Error"}, status=status.HTTP_400_BAD_REQUEST)
        # myresponse = [{
        #     'type': "question",
        #     'content':
        #         userQuery,
        # },
        #     {
        #         'type': "answer",
        #         'content':
        #             generated_response,
        # }]
        myresposne = generated_response
        return Response({"message": "Response Generated Successfully!", "Response": myresposne},
                        status=status.HTTP_200_OK)
    except Exception as ex:
        # logger.critical(ex)
        return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('federal', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
    openapi.Parameter('state', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
    openapi.Parameter('year', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
    openapi.Parameter('caseName', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
    ])
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def browseCases(request):
    cursor = connection.cursor()
    state = request.query_params.get("state")
    federal = request.query_params.get("federal")
    year = request.query_params.get("year")
    case_name = request.query_params.get("caseName")
    try:
        if federal and not state and not year and not case_name:
            federal_list = federal_data[federal]
            return Response({"message": "Response Generated Successfully!", "Federal": federal_list},
                            status=status.HTTP_200_OK)
        if state and not year:
            year_list = browse_state_cases(state, cursor)
            year_list.sort(reverse=True)
            return Response({"message": "Response Generated Successfully!", "Year": year_list},
                            status=status.HTTP_200_OK)

        elif state and year and not case_name:
            year_cases_list = browse_state_year_cases(state, year, cursor)
            return Response({"message": "Response Generated Successfully!", "Cases": year_cases_list},
                            status=status.HTTP_200_OK)

        elif case_name:
            opinion_list = browse_cases_from_case_name(case_name, cursor)
            # id_string = ', '.join(str(id) for id in opinion_list)
            main, citesto, citation, casebody, opinion, attorney, court, judges, jurisdiction, parties, reporter = extract_data_from_db(
                opinion_list)
            return Response({"message": "Response Generated Successfully!",
                             "Query": 'Hardcoded',
                             "Answer": "Successfully get the answers",
                             "Sources": opinion_list,
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
                             }, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No Data available"},
                            status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": "Error while fetching cases from keywords"},
                        status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
    openapi.Parameter('password', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)])
@api_view(['POST'])
@permission_classes([])
def forgetpassword(request):
    token = request.query_params.get("token")
    password = request.query_params.get("password")
    try:
        # Decode the token
        decoded_token = jwt.decode(token, os.getenv('TOKEN_SECRET_KEY'), algorithms=['HS256'])

        # Extract the email from the decoded token
        extracted_email = decoded_token.get('email')
        emails = UserDetails.objects.values_list("email", flat=True)
        if extracted_email in emails:
            user_obj = UserDetails.objects.get(email=extracted_email)
            user_obj.set_password(password)
            user_obj.save()
            return Response({'message': "Email get Successfully", "data": {"email": extracted_email}},
                            status=status.HTTP_200_OK)
        else:
            return Response({'message': "User doesn't exist"}, status=status.HTTP_400_BAD_REQUEST)
        # user_obj = UserDetails.objects.get(email=extracted_email)
        # user_obj.set_password(password)
        # user_obj.save()

    except jwt.ExpiredSignatureError:
        # Handle token expiration error
        return Response({'message': "expired token"}, status=status.HTTP_400_BAD_REQUEST)
    except jwt.InvalidTokenError:
        # Handle invalid token error
        return Response({'message': "invalid token"}, status=status.HTTP_400_BAD_REQUEST)


# remove authentication
@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('email', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True), ])
@api_view(['POST'])
@permission_classes([])
def sendForgetEmail(request):
    email = request.query_params.get("email")
    expiration_time = datetime.utcnow() + timedelta(hours=1)

    # Email verification token
    email_verification_payload = {"email": email, "exp": expiration_time}
    email_verification_token = jwt.encode(email_verification_payload, os.getenv('TOKEN_SECRET_KEY'), algorithm='HS256')
    emails = UserDetails.objects.values_list("email", flat=True)

    if email not in emails:
        return Response({'message': "User doesn't exist"}, status=status.HTTP_400_BAD_REQUEST)
    # try:
    #     sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_KEY'))
    #     from_email = Email(os.environ.get('SENDER_EMAIL'))  # Change to your verified sender
    #     to_email = To(email)  # Change to your recipient
    #     subject = " Reset Your Password for LawGPT App"
    #     content = Content("text/plain",
    #                         f"Hi User, \n\t In order to reset your password, kindly click on the secure link provided below: \n Link: https://lawgptapp.xeventechnologies.com/dashboard/token?={email_verification_token} . \nIf you did not request a password reset or have any concerns, please contact our support team immediately. \n\n Best regards, \nLawGPT App Support Team ")
    #     my_mail = Mail(from_email, to_email, subject, content)
    #     mail_json = my_mail.get()

    #     # Send an HTTP POST request to /mail/send
    #     response = sg.client.mail.send.post(request_body=mail_json)

    #     return Response({'message': "Email Sent Successfully", "data": {"token":email_verification_token }}, status=status.HTTP_200_OK)

    try:
        # Validate email
        # email_exist_status = requests.get(
        #     "https://api.mailgun.net/v4/address/validate",
        #     auth=("api", os.getenv("MAILGUN_KEY")),
        #     params={"address": email})
        # if json.loads(email_exist_status.text)['result']=="undeliverable":
        #     return Response({'message': "Email does not Exist"}, status=status.HTTP_400_BAD_REQUEST)
        message = Mail(
            from_email='accounts@law.co',
            to_emails=email,
            subject='Password Reset Request - Action Required',
            html_content=f"Greetings, \n\t We trust this message finds you well. A recent request to reset your password for the LawGPT App account has been initiated. To ensure the security of your account, we kindly request your immediate attention to complete the process. Click on the secure link provided below to proceed with the password reset:\n https://app.law.co/reset-password?token={email_verification_token}  \nIf you have not initiated a password reset or if you harbor any concerns regarding this request, please reach out to our dedicated support team without delay. We are committed to assisting you promptly. \n\n Best regards, \nLawGPT App Support Team ")
        try:
            sg = SendGridAPIClient(os.getenv("NEW_SENDGRID_KEY"))
            response = sg.send(message)
            # print(response.status_code)
            # print(response.body)
            # print(response.headers)
        except Exception as e:
            return Response({'message': e}, status=status.HTTP_400_BAD_REQUEST)
        # response = requests.post(
        # "https://api.mailgun.net/v3/mail.law.co/messages",
        # auth=("api", os.getenv("MAILGUN_KEY")),
        # data={"from": os.environ.get('SENDER_EMAIL'),
        #       "to": email,
        #       "subject": "Password Reset Request - Action Required",
        #     #   "text": f"Greetings, \n\t In order to reset your password, kindly click on the secure link provided below: \n Link: http://localhost:3000/reset-password?token={email_verification_token} . \nIf you did not request a password reset or have any concerns, please contact our support team immediately. \n\n Best regards, \nLawGPT App Support Team "})
        #       "text": f"Greetings, \n\t We trust this message finds you well. A recent request to reset your password for the LawGPT App account has been initiated. To ensure the security of your account, we kindly request your immediate attention to complete the process. Click on the secure link provided below to proceed with the password reset:\n https://app.law.co/reset-password?token={email_verification_token}  \nIf you have not initiated a password reset or if you harbor any concerns regarding this request, please reach out to our dedicated support team without delay. We are committed to assisting you promptly. \n\n Best regards, \nLawGPT App Support Team "})

        if response.status_code == 202:
            return Response({'message': "Email Sent Successfully", "data": {"token": email_verification_token}},
                            status=status.HTTP_200_OK)
        else:
            return Response({'message': response.reason}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'message': e}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True), ])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verifyTheToken(request):
    query = 0
    document = 0
    try:
        query = request.user.userquerydocrecord_set.all()[0].query_number
        document = request.user.userquerydocrecord_set.all()[0].document_number
    except:
        pass
    subscribe = False
    new_list = list()
    my_dict = {
        'id': request.user.pk,
        'name': request.user.fullname,
        'email': request.user.email,
        'role': request.user.role.pk,
        'query': query,
        'documents': document,
    }
    new_list.append(my_dict)
    if request.user.role.pk == 2:
        if (datetime.now(timezone.utc) - request.user.created_date).days > 30:
            subscribe = True
    token = request.query_params.get("token")
    user_id = request.user.pk
    user_token = Usertoken.objects.filter(userid=user_id, isarchived=False).last()
    if user_token is not None:
        if user_token.token == token:
        # u_token = user_token[len(user_token) - 1]
            if (datetime.now(timezone.utc) - user_token.createddate).total_seconds() < 1800:
                user_token.isarchived = True
                user_token.save()
                return Response(
                    {'message': "Login Successfully", "tokens": {'access': 'Bearer ' + request.auth.token.decode("utf-8")},
                     'subscribe': subscribe, 'data': new_list}, status=status.HTTP_200_OK)
        return Response({'message': "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': "invalid security code"}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='POST', request_body=UpdatePassword)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def UpdateUserPassword(request):
    request.user.set_password(request.data.get('password'))
    request.user.save()
    return Response({'message': "Password Updated Successfully"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_logs(request):
    user_log = Userlogs.objects.filter(userid=request.user.pk)
    user_log_ser = UserLogSerializer(user_log, many=True)
    user_log.update(isarchived=True)
    return Response({'message': 'User Logs', "data": user_log_ser.data}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='POST', request_body=ToggleOption)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateTwoFactorToggle(request):
    if request.user.role_id == 5:
        try:
            obj = UserDetails.objects.get(id=request.data.get('userId'))
        except:
            return Response({'message': 'Please Enter a valid UserID', "data": None},
                            status=status.HTTP_400_BAD_REQUEST)
        obj.toggle_option = request.data.get('toggleOption')
        obj.save()
        return Response({'message': 'User 2FA Update successfully', "data": None}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'You dont have permission to upadate the record', "data": None},
                        status=status.HTTP_400_BAD_REQUEST)



@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('email', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)])
@api_view(['POST'])
@permission_classes([])
def resend_token(request):
    email = request.query_params.get("email")
    x = ''.join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
    message = Mail(
        from_email='accounts@law.co',
        to_emails=email,
        subject='Your LAW.co Login Code',
        html_content=f"<h3>Thank you for logging into Law.co <br> Please use the following PIN to access your account:<br></h3>"
                     f"<h2>{x}</h2>")
    try:
        sg = SendGridAPIClient(os.getenv("NEW_SENDGRID_KEY"))
        response = sg.send(message)

    except Exception as e:
        return Response(data={"message": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)
    user = UserDetails.objects.get(email=email)
    user_token = Usertoken(userid=user, createddate=datetime.now(timezone.utc), isarchived=False, token=x)
    user_token.save()
    return Response({'message': 'Token Send Successfully', "data": []}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='PATCH',request_body=FreeTrail)
@api_view(['PATCH'])
@permission_classes([])
def update_free_trail(request):
    user_id = request.data.get('userId')
    is_expired = request.data.get('IsExpired')
    if not is_expired:
        try:
            obj = Userfreetrail.objects.get(user=user_id)
            obj.created_date = datetime.now()
            obj.expired_date = datetime.now() + timedelta(days = 30)
            obj.save()
        except:
            obj = Userfreetrail(user=UserDetails.objects.get(id=user_id),created_date=datetime.now(),expired_date=datetime.now() + timedelta(days = 30))
            obj.save()
    else:
        try:
            obj = Userfreetrail.objects.get(user=user_id)
            obj.expired_date = datetime.now()
            obj.save()
        except:
            obj = Userfreetrail(user=UserDetails.objects.get(id=user_id), created_date=datetime.now(),expired_date=datetime.now())
            obj.save()
    return Response({'message': 'Trail Update Successfully', "data": []}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_query(request):
    try:
        if request.user.role.pk == 3 or request.user.role.pk == 1:
            user_log = Userquerydocrecord.objects.filter(user=request.user.pk)
            new_dict = {
                "query":user_log[0].query_number,
                "document":user_log[0].document_number,
            }
            return Response({'message': 'User Query', "data": new_dict}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'User has full access', "data": None}, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'Kindly Buy a package', "data": None},
                        status=status.HTTP_400_BAD_REQUEST)





