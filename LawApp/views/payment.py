from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from ..models import Userpricing, UserDetails, AdminUser, Userquerydocrecord, Userapikeys, Userlogs
from rest_framework.response import Response
from rest_framework import status
from ..serializers import CardInfo, PaymentMethodAlready, PaymentMethodForQueryDoc, ChangePackage
from datetime import datetime
import os
import stripe
from django.db import transaction
from ..utils import hashedAPIKey
from dotenv import load_dotenv
from drf_yasg import openapi

load_dotenv()

stripe.api_key = os.getenv('stripe_dev_key')


@api_view(['GET'])
@permission_classes([])
def create_customer(request):
    return Response({'message': "Please use valid API"}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='POST', request_body=PaymentMethodAlready)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_token(request):
    token = request.data['token']
    price = request.data['price']
    new_list = list()
    email = request.user.email
    fullname = request.user.fullname
    try:
        customer = stripe.Customer.create(
            email=email,
            name=fullname,
            source=token
        )
    except Exception as e:
        return Response({'message': "Invalid Card Number"}, status=status.HTTP_400_BAD_REQUEST)
    if price == 30:
        try:
            # this is for 49$
            st_ = stripe.Subscription.create(
                customer=customer.id,
                items=[

                    {"price": os.getenv('stripe_law_admin')},
                    # {"price": os.getenv('stripe_law_admin_prod')},
                ],
            )
        except Exception as e:
            return Response({'message': "Pricing Failed"}, status=status.HTTP_400_BAD_REQUEST)
        log_obj = Userlogs(userid=request.user, logdata=f"{request.user.fullname} buy new package for 49$",
                           createddate=datetime.now(), isarchived=False)
        log_obj.save()
    else:
        try:
            # this is 25$
            st_ = stripe.Subscription.create(
                customer=customer.id,
                items=[
                    {"price": os.getenv('stripe_law_user')},
                    # {"price": os.getenv('stripe_law_user_prod')},
                ],
            )
        except Exception as e:
            return Response({'message': "Pricing Failed"}, status=status.HTTP_400_BAD_REQUEST)
        log_obj = Userlogs(userid=request.user, logdata=f"{request.user.fullname} buy new package for 25$",
                           createddate=datetime.now(), isarchived=False)
        log_obj.save()

    user_price = Userpricing(customerid=customer.id, token=request.data['token'], userid=request.user,
                             createddate=datetime.now(), cancelpayment=False, payment=49)
    user_price.save()

    return Response({'message': f"Successfully Subscribed! {price}$"}, status=status.HTTP_200_OK)


@api_view(['POST'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def cancel_subscribe(request):
    '''
    This api is used to cancel the payment method
    '''
    if request.user.role.pk == 1:
        with transaction.atomic():
            try:
                user_id = request.user.pk
                user_price = Userpricing.objects.filter(userid=user_id)
                for cancel_package in user_price.values_list('subscribe_id', flat=True).filter(cancelpayment=False):
                    try:
                        stripe_cancel = stripe.Subscription.cancel(user_price[0].subscribe_id)
                    except:
                        pass
                user_price.update(cancelpayment=True)
                UserDetails.objects.filter(id__in=user_price.values_list('adminuserid', flat=True)).update(
                    is_deleted=True)
                obj = UserDetails.objects.get(id=user_id)
                obj.role_id = 2
                obj.is_deleted = False
                obj.save()
            except Exception as e:
                transaction.set_rollback(True)
                return Response({'message': f"Error {e}", 'data': None}, status=status.HTTP_400_BAD_REQUEST)
            log_obj = Userlogs(userid=request.user, logdata=f"Payment Cancel For {request.user.fullname} ",
                               createddate=datetime.now(), isarchived=False)
            log_obj.save()
            return Response({'message': "Downgrade package successfully", 'data': None}, status=status.HTTP_200_OK)
        # subscibeid = request.data['subscibeId']
        # userid = request.user.pk
        # try:
        #     user_price = Userpricing.objects.filter(cancelpayment=False).get(adminuserid=userid).values_list()
        # except:
        #     return Response({'message': "You dont have permission! "}, status=status.HTTP_400_BAD_REQUEST)
        # user_list = list(AdminUser.present.filter(adminid= request.user.pk).values_list('userid',flat=True))
        # if userid not in user_list:
        #     return Response({'message': "You dont have permission! "}, status=status.HTTP_400_BAD_REQUEST)
        #
        # stripe_cancel = stripe.Subscription.cancel(subscibeid)
        # user_obj = UserDetails.objects.get(id=userid)
        # user_obj.is_deleted = True
        # user_obj.save()
        # user_price = Userpricing.objects.get(adminuserid=userid)
        # user_price.cancelpayment = True
        # user_price.save()
        # return Response({'message':f"Successfully Cancel the payment! "}, status=status.HTTP_200_OK)
    else:
        return Response({'message': "You dont have permission! "}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='POST', request_body=CardInfo)
@api_view(['POST'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def edit_card_info(request):
    token = request.data['token']
    email = request.user.email
    fullname = request.user.fullname
    customer = stripe.Customer.create(

        email=email,
        name=fullname,
        source=token

    )
    user_pricing = Userpricing.objects.filter(userid=request.user.pk).filter(cancelpayment=False)
    if user_pricing:
        obj = user_pricing[0]
        obj.customerid = customer.id
        obj.token = request.data['token']
        obj.createddate = datetime.now()
        log_obj = Userlogs(userid=request.user, logdata=f"{request.user.fullname} update Card Information",
                           createddate=datetime.now(), isarchived=False)
        log_obj.save()
        return Response({'message': f"Successfully Update the Card Info! "}, status=status.HTTP_200_OK)
    else:
        if request.user.role.pk == 1:
            # st_ = stripe.Subscription.create(
            #     customer=customer.id,
            #     items=[
            #         # {"price": os.getenv('stripe_law_admin')},
            #         {"price": os.getenv('stripe_law_admin')},
            #     ],
            # )
            user_price = Userpricing(customerid=customer.id, token=request.data['token'], userid=request.user,
                                     createddate=datetime.now(), cancelpayment=False, payment=49)
            user_price.save()
            return Response({'message': f"Successfully Update the Card Info! "}, status=status.HTTP_200_OK)
    return Response({'message': "We dont have your info in our database!"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def get_all_prod(request):
    if request.user.role.pk == 5:
        stripe.api_key = os.getenv('stripe_key')
        stripe_data = stripe.Product.list()
        return Response({'message': "Product Data", 'data': stripe_data}, status=status.HTTP_200_OK)
    return Response({'message': "Permission Denied!"}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema("POST", request_body=ChangePackage)
@api_view(['POST'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def downgrade_upgrade(request):
    '''
    This method is used to downgrade or upgrade user package from free user to paid user or vice versa

    '''
    packge_change_list = ['upgrade', 'downgrade']
    bit = request.data.get('bit')
    if bit not in packge_change_list:
        return Response({'message': 'Please Enter a valid Package Name'}, status=status.HTTP_400_BAD_REQUEST)
    if bit == 'downgrade':
        user_id = request.user.pk
        # user_id = 301
        with transaction.atomic():
            try:

                user_price = Userpricing.objects.filter(userid=user_id)
                for cancel_package in user_price.values_list('subscribe_id', flat=True).filter(cancelpayment=False):
                    try:
                        stripe_cancel = stripe.Subscription.cancel(user_price[0].subscribe_id)
                    except:
                        pass
                user_price.update(cancelpayment=True)
                UserDetails.objects.filter(id__in=user_price.values_list('adminuserid', flat=True)).update(
                    is_deleted=True)
                obj = UserDetails.objects.get(id=user_id)
                obj.role_id = request.data.get('updatedRole')
                obj.is_deleted = False
                obj.save()
            except Exception as e:
                transaction.set_rollback(True)
                return Response({'message': f"Error {e}", 'data': None}, status=status.HTTP_400_BAD_REQUEST)
            log_obj = Userlogs(userid=request.user, logdata=f"{request.user.fullname} downgrade the package",
                               createddate=datetime.now(), isarchived=False)
            log_obj.save()
            return Response({'message': "Downgrade package successfully", 'data': None}, status=status.HTTP_200_OK)
    else:
        try:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=request.user.fullname,
                source=request.data.get('token')
            )
            st_ = stripe.Subscription.create(
                customer=customer.id,
                items=[
                    {"price": os.getenv('stripe_law_admin')},
                    # {"price": os.getenv('stripe_law_admin_prod')},
                ],
            )

        except Exception as e:
            return Response({'message': f"Error {e}", 'data': None}, status=status.HTTP_400_BAD_REQUEST)
        user_price = Userpricing(customerid=customer.id, token=request.data.get('token'), userid=request.user,
                                 createddate=datetime.now(),
                                 payment=30, adminuserid=request.user.pk, subscribe_id=st_.id, cancelpayment=False)
        user_price.save()
        hash_key = hashedAPIKey(request.data.get('apikey'))
        try:
            user_price_ = Userapikeys.objects.get(userid=request.user.pk)
            user_price_.apikey = hash_key
            user_price_.save()
        except:
            user_price_ = Userapikeys(userid=request.user, apikey=hash_key, isdelete=False)
            user_price_.save()
        obj = UserDetails.objects.get(id=request.user.pk)
        obj.role_id = request.data.get('updatedRole')
        obj.save()
        log_obj = Userlogs(userid=request.user, logdata=f"{request.user.fullname} upgrade the package for 49$",
                           createddate=datetime.now(), isarchived=False)
        log_obj.save()
        return Response({'message': 'Upgrade Successfully'}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='POST', request_body=PaymentMethodForQueryDoc)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buyQueryDocPackage(request):
    token = request.data['token']
    price = request.data['price']
    previous_query = 0
    previous_doc = 0
    price_dict = {
        '100QueryDoc': [os.getenv('stripe_100QueryDoc'), 100, 50],
        '50QueryDoc': [os.getenv('stripe_50QueryDoc'), 50, 25],
        '100Query': [os.getenv('stripe_100Query'), 100, 0],
        '50Query': [os.getenv('stripe_50Query'), 50, 0],
        '50Doc': [os.getenv('stripe_50Doc'), 0, 50],
        '25Doc': [os.getenv('stripe_25Doc'), 0, 25]
    }
    try:
        original_key = price_dict[price]
        original_price = original_key[0]


    except:
        return Response({'message': 'Kindly Provide Correct Key'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user_query = Userquerydocrecord.objects.get(user=request.user.pk)
        previous_query = user_query.query_number
        previous_doc = user_query.document_number
        user_query.query_number = previous_query + original_key[1]
        user_query.document_number = previous_doc + original_key[2]
        user_query.save()
        customer = stripe.Customer.create(
            email=request.user.email,
            name=request.user.fullname,
            source=token
        )
        st_ = stripe.Subscription.create(
            customer=customer.id,
            items=[
                {
                    "price": original_price
                },
            ],
        )
        user_price = Userpricing(customerid=customer.id, token=token, userid=request.user,
                                 createddate=datetime.now(),
                                 payment=original_key[1] + original_key[2], adminuserid=request.user.pk,
                                 subscribe_id=st_.id, cancelpayment=False)
        user_price.save()
        return Response({'message': 'You Buy Package Successfully', 'data': {
            'query': previous_query + original_key[1],
            'documents': previous_doc + original_key[2]
        }}, status=status.HTTP_200_OK)
    except:
        try:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=request.user.fullname,
                source=token
            )
            st_ = stripe.Subscription.create(
                customer=customer.id,
                items=[
                    {
                        "price": original_price
                    },
                ],
            )
            user_price = Userpricing(customerid=customer.id, token=token, userid=request.user,
                                     createddate=datetime.now(),
                                     payment=original_key[1] + original_key[2], adminuserid=request.user.pk,
                                     subscribe_id=st_.id, cancelpayment=False)
            user_price.save()
            user_query = Userquerydocrecord(query_number=original_key[1], document_number=original_key[2],
                                            user=request.user, created_date=datetime.now(), updated_date=datetime.now(),
                                            is_delete=False)
            user_query.save()
            log_obj = Userlogs(userid=request.user, logdata=f"{request.user.fullname} buy new package for {original_price}$",
                               createddate=datetime.now(), isarchived=False)
            log_obj.save()
            return Response({'message': 'You Buy Package Successfully','data':{
                'query':previous_query + original_key[1],
                'documents':previous_doc + original_key[2]
            }}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f'Error -> {e}'}, status=status.HTTP_400_BAD_REQUEST)

