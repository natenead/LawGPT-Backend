from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.urls import path
from .views import (
    category_views,
    form_data_views,
    client_views,
    clients_notes
    )
schema_view = get_schema_view(
    openapi.Info(
        title="AdaptDocx",
        default_version='v1.1',
        description="AdaptDocx",

    ),
    public=False,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('adpt', schema_view.with_ui(cache_timeout=0), name='schema-json'),
    path('category/insertCategory',category_views.insert_category_data),
    path('category/getCategory',category_views.get_category_data),
    path('category/insertSubcategory',category_views.insert_subcategory_data),
    path('category/getSubCategory',category_views.get_subcategory_data),
    path('form/insertForm',form_data_views.insert_form_data),
    path('form/insertForm/dummy',form_data_views.insert_form_data_dummy),
    path('form/saveForm',form_data_views.sava_form),
    path('form/getJsonData',form_data_views.get_form_json_data),
    path('form/updateJsonData',form_data_views.update_form_json_data),
    path('client/addClient',client_views.insert_client),
    path('client/updateClient',client_views.update_client_data),
    path('client/getClient',client_views.get_client),
    path('client/getClientWithIdName',client_views.get_client_name_id),
    path('client/addMatter',client_views.add_matter),
    path('client/getMatter',client_views.get_matter),
    path('client/getMatter/id',client_views.get_matter_id),
    path('client/getClient/id',client_views.get_client_id),
    path('client/deleteMatter',client_views.delete_matter),
    path('client/updateMatterTitle',client_views.update_matter_title),
    path('client/updateMatterFeeOffering',client_views.update_matter_fee_offering),
    path('client/additionalPhoneNumber',client_views.add_additional_phone_number),
    path('client/additionalAddressInfo',client_views.add_additional_address_data),
    path('client/clientNotes',clients_notes.add_client_notes),
    path('client/getClientNotes',clients_notes.get_client_notes),
    path('client/deleteClient',client_views.delete_client),
    path('client/history',client_views.get_history),
    path('client/signedClosedMatter',client_views.signedClosedMatter),


    ]