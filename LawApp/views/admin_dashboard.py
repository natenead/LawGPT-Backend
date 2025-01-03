from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import UserDetails, Studentrecord,Userlastlogin,Mostlyusedfeature,Userpricing
from ..serializers import (
    CustomUserSerializer,
    StudentSerializer,StudentSignUpSerializer,
    MonthlyFilter
)
from ..utils import check_number_of_queries
from django.db.models.functions import RowNumber
import itertools
from datetime import date,timedelta
from botocore.client import Config
from dotenv import load_dotenv
import os
from ..models import UserDetails,AdminUser
from drf_yasg import openapi
from django.db.models import Max,Q,Window,F
from datetime import timezone
import calendar

load_dotenv()
import requests
aws_key=os.getenv('ACCESS_KEY')
aws_secret_key=os.getenv('SECRET_ACCESS_KEY')
aws_space_name=os.getenv('SPACE_NAME')

from copy import copy
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes

from drf_yasg.utils import swagger_auto_schema

from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
#
# @swagger_auto_schema(method='GET',
#                      manual_parameters=[
#                          openapi.Parameter('UserID',  openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
#                          openapi.Parameter('approved',  openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, required=True),
#                      ]
#                      )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_data(request):
    if request.user.role.pk == 5:

        recent_user_list = list()
        main_list = list()
        mostly_used = Mostlyusedfeature.objects.filter(count=Mostlyusedfeature.objects.aggregate(max_count=Max('count'))['max_count'])[0]
        total_user_ = UserDetails.objects.filter(is_deleted=False)
        total_active_ = total_user_.count()
        total_user_count = UserDetails.objects.all().count()
        total_student_count = total_user_.filter(role = 4).count()
        total_free_count = total_user_.filter(role = 2).count()
        total_paid_count = total_user_.filter(Q(role = 1) | Q(role=3)).count()
        total_inactiver_count = UserDetails.objects.filter(is_deleted=True).count()
        recent_user = UserDetails.objects.filter(
           created_date__gte=date.today() - timedelta(days=30)).filter(is_deleted=False).count()

        recent_login = Userlastlogin.objects.filter(
           createddate__gte=date.today() - timedelta(days=10)).annotate(
            rn=Window(
                expression=RowNumber(),
                partition_by=[F('userid')],
                order_by=[F('createddate').desc()]
            )
        ).filter(rn=1)[:20]

        # recent_login = Userlastlogin.objects.filter(
        #    createddate__gte=date.today() - timedelta(days=30)).values('userid').distinct()

        for recent in recent_login:
            new_dict = {
                'email' : recent.userid.email,
                'fullname': recent.userid.fullname,
                'createddate':str(recent.createddate)

            }
            recent_user_list.append(new_dict)
        recent_user_list.reverse()

        temp_dict = {
            'total_users':total_user_count,
            'total_paid_users':total_paid_count,
            'total_student':total_student_count,
            'total_free_user':total_free_count,
            'recent_users':recent_user,
            'active_users':total_active_,
            'inactive_users':total_inactiver_count,
            'last_recent_login':recent_user_list,
            'mostly_used':mostly_used.featureid.name,

        }
        main_list.append(temp_dict)
        return Response({'message': 'Dashboard Data', 'data': main_list,'subscribe': True},
                        status=status.HTTP_200_OK)

    elif (request.user.role.pk == 1) or (request.user.role.pk == 3):
        main_list = list()
        delete_user = 0
        active_user = 0
        total_user = 0
        for users in AdminUser.present.filter(adminid=request.user.pk):
            total_user += 1
            if users.userid.is_deleted:
                delete_user += 1
            else:
                active_user += 1

        final_dict = {
            'total_users':total_user,
            'inactive_users':delete_user,
            'active_users':active_user
        }
        main_list.append(final_dict)
        return Response({'message': 'Dashboard Data', 'data': main_list,'subscribe': True},
                        status=status.HTTP_200_OK)
    else:
        if request.user.role.pk == 2:
            if (datetime.now(timezone.utc)- request.user.created_date).days > 30:
                return Response({'message': 'Free User', 'data': [],'subscribe':False},
                                status=status.HTTP_200_OK)
            return Response({'message': 'Free User', 'data': [], 'subscribe': True},
                            status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def charts(request):
    if request.user.role.pk == 5 or request.user.role.pk == 1:
        weekDays = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        monthly_list = list(itertools.repeat(0, 12))
        weekly_dict = dict()
        monthly_dict = dict()
        main_list = list()
        user_pricing_month = Userpricing.objects.filter(
            createddate__gte=date.today() - timedelta(days=365))
        user_pricing_week = Userpricing.objects.filter(
            createddate__gte=date.today() - timedelta(days=7))

        for monthly in user_pricing_month:
            date_ = str(monthly.createddate).split('-')[1].split()[0]

            monthly_list[int(date_) - 1] += 1

        for week in user_pricing_week:
            # date_ = str(week.createddate).split('-')[2].split()[0]
            try:
                weekly_dict[week.createddate.strftime('%A')] = weekly_dict[week.createddate.strftime('%A')] + 1
            except:
                weekly_dict[week.createddate.strftime('%A')] = 1
        for _week in weekDays:
            try:
                weekly_dict[_week]
            except:
                weekly_dict[_week] = 0

        temp_dict = {

            'weekly_price_data': weekly_dict,
            'monthly_price_data': monthly_list,
        }
        main_list.append(temp_dict)
        return Response({'message': 'Dashboard Data', 'data': main_list},
                        status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Free User', 'data': []},
                        status=status.HTTP_200_OK)

@swagger_auto_schema(method='post', request_body=MonthlyFilter)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def main_charts(request):
    if request.user.role.pk == 5 or request.user.role.pk == 1:
        if (request.data.get('month') > 0) and (request.data.get('month') < 13) and len(str(request.data.get('year'))) ==4:
            year = request.data.get('year')
            month = request.data.get('month')
            first_day = f"{year}-{month:02d}-01"
            _, last_day_ = calendar.monthrange(request.data.get('year'), request.data.get('month'))
            last_day = f"{year}-{month:02d}-{last_day_}"
            # total_user_count = UserDetails.objects.filter(created_date__range=[first_day, last_day]).count()
            total_users = UserDetails.objects.filter(created_date__range=[first_day, last_day])
            last_day_ += 1
            # total_inactiver_count = UserDetails.objects.filter(is_deleted=True).filter(created_date__range=[first_day, last_day]).count()
            # recent_user = UserDetails.objects.filter(created_date__range=[first_day, last_day]).filter(is_deleted=False).count()
            # total_user_ = UserDetails.objects.filter(is_deleted=False).filter(created_date__range=[first_day, last_day])
            # total_student_count = total_user_.filter(role=4).count()
            # total_free_count = total_user_.filter(role=2).count()
            # total_paid_count = total_user_.filter(Q(role=1) | Q(role=3)).count()
            total_user_count_list = [0]* last_day_
            total_inactive_count_list = [0]* last_day_
            total_active_count_list = [0]* last_day_
            total_student_count_list = [0]* last_day_
            total_free_count_list = [0]* last_day_
            total_paid_count_list = [0]* last_day_
            # new_item = dict()
            for new_data in total_users.iterator():
                main_date = int(str(new_data.created_date).split()[0].split('-')[-1])
                total_user_count_list[main_date] += 1
                if new_data.is_deleted:
                    total_active_count_list[main_date] += 1
                else:
                    total_inactive_count_list[main_date] += 1
                if new_data.role.pk == 4:
                    total_student_count_list[main_date] += 1
                elif new_data.role.pk == 2:
                    total_free_count_list[main_date] += 1
                elif new_data.role.pk == 3:
                    total_paid_count_list[main_date] += 1
            main_list = list()
            for items in range(1,last_day_):
                # main_items = dict()
                main_items = {
                    'total_users': total_user_count_list[items],
                    'total_paid_users': total_paid_count_list[items],
                    'total_student': total_student_count_list[items],
                    'total_free_user': total_free_count_list[items],
                    'active_users': total_active_count_list[items],
                    'inactive_users': total_inactive_count_list[items],
                }
                main_list.append(main_items)
            #
            # temp_dict = {
            #     'total_users': total_user_count,
            #     'total_paid_users': total_paid_count,
            #     'total_student': total_student_count,
            #     'total_free_user': total_free_count,
            #     'recent_users': recent_user,
            #     'inactive_users': total_inactiver_count,
            #
            # }

            return Response({'message': 'Dashboard Chart Data', 'data': main_list},
                            status=status.HTTP_200_OK)
        return Response({'message': 'Please Enter a Correct Date and year', 'data': None},
                        status=status.HTTP_400_BAD_REQUEST)


