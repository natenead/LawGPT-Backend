from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ..serializers import AdaptdocxFormCategorySerizalizer, AdaptdocxFormSubcategorySerizalizer
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from ..models import AdaptdocxFormCategory, AdaptdocxFormSubcategory
from datetime import datetime
from django.db.models import Q


@swagger_auto_schema(method='POST', request_body=AdaptdocxFormCategorySerizalizer,
                     responses={status.HTTP_201_CREATED: 'Success',
                                status.HTTP_401_UNAUTHORIZED: 'UNAUTHORIZED',
                                status.HTTP_409_CONFLICT: 'Already Exists'})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def insert_category_data(request):
    # if request.user.role.pk == 5:
    cat_name = request.data['categoryname']
    try:
        catg_data = AdaptdocxFormCategory.objects.get(Q(categoryname=cat_name) & Q(isdelete=False))
        return Response({'message': 'Category Name Already Exists'}, status=status.HTTP_409_CONFLICT)
    except:

        cat_obj = AdaptdocxFormCategory(categoryname=cat_name, createddate=datetime.now(), isdelete=False)
        cat_obj.save()
        data_ = AdaptdocxFormCategory.objects.filter(isdelete=False)
        data_ser = AdaptdocxFormCategorySerizalizer(data_, many=True)
        return Response({'message': 'Category Data save successfully', 'data': data_ser.data}, status=status.HTTP_200_OK)

    # return Response({'message': 'You do not have permission to add data'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_category_data(request):
    # if request.user.role.pk == 5:
    cat_obj = AdaptdocxFormCategory.objects.filter(isdelete=False).order_by('-id')

    cat_obj_ser = AdaptdocxFormCategorySerizalizer(cat_obj, many=True)

    return Response({'message': 'All Category Data', 'data': cat_obj_ser.data}, status=status.HTTP_200_OK)

    # return Response({'message': 'You do not have permission to view data'}, status=status.HTTP_401_UNAUTHORIZED)


@swagger_auto_schema(method='POST', request_body=AdaptdocxFormSubcategorySerizalizer,
                     responses={status.HTTP_201_CREATED: 'Success',
                                status.HTTP_401_UNAUTHORIZED: 'UNAUTHORIZED', status.HTTP_404_NOT_FOUND: 'Not Found',
                                status.HTTP_409_CONFLICT: 'Already Exists'})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def insert_subcategory_data(request):
    # if request.user.role.pk == 5:
    subcat_name = request.data['subcategoryname']
    try:
        catg_data = AdaptdocxFormSubcategory.objects.get(Q(subcategoryname=subcat_name) & Q(isdelete=False))
        return Response({'message': 'SubCategory Name Already Exists'}, status=status.HTTP_409_CONFLICT)
    except:
        pass
    try:
        cat_id = AdaptdocxFormCategory.objects.get(id=request.data['categoryid'])
    except:
        return Response({'message': 'Please Enter a valid ID'}, status=status.HTTP_404_NOT_FOUND)
    sub_cat_obj = AdaptdocxFormSubcategory(subcategoryname=subcat_name, categoryid=cat_id,
                                           createddate=datetime.now(), isdelete=False)
    sub_cat_obj.save()
    data_ = AdaptdocxFormSubcategory.objects.filter(isdelete=False)
    data_ser = AdaptdocxFormSubcategorySerizalizer(data_, many=True)
    return Response({'message': 'Subcategory Data save successfully', 'data': data_ser.data}, status=status.HTTP_200_OK)

    # return Response({'message': 'You do not have permission to add data'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subcategory_data(request):
    # if request.user.role.pk == 5:
    cat_obj = AdaptdocxFormSubcategory.objects.filter(isdelete=False)
    cat_obj_ser = AdaptdocxFormSubcategorySerizalizer(cat_obj, many=True)

    return Response({'message': 'All Category Data', 'data': cat_obj_ser.data}, status=status.HTTP_200_OK)

    # return Response({'message': 'You do not have permission to view data'}, status=status.HTTP_401_UNAUTHORIZED)
