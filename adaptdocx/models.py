from django.db import models
from LawApp.models import UserDetails
from .manager import ClientsManager

# Create your models here.


class AdaptdocxFormCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    categoryname = models.CharField(db_column='categoryName', blank=True, null=True)
    createddate = models.DateTimeField(db_column='createdDate', blank=True, null=True)
    isdelete = models.BooleanField(db_column='isDelete', blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'adaptdocx_form_category'


class AdaptdocxFormSubcategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    subcategoryname = models.CharField(db_column='subcategoryName', blank=True, null=True)
    categoryid = models.ForeignKey('AdaptdocxFormCategory', models.DO_NOTHING, db_column='categoryId', blank=True,
                                   null=True)
    createddate = models.DateTimeField(db_column='createdDate', blank=True, null=True)
    isdelete = models.BooleanField(db_column='isDelete', blank=True, null=True)

    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'adaptdocx_form_subcategory'


class AdaptdocxFormjsonData(models.Model):
    id = models.BigAutoField(primary_key=True)
    subcategoryId = models.ForeignKey('AdaptdocxFormSubcategory', models.DO_NOTHING, db_column='subcategoryId',
                                      blank=True, null=True)
    formJson = models.JSONField(db_column='formJson', blank=True, null=True)

    createddate = models.DateTimeField(db_column='createdDate', blank=True, null=True)
    pagename = models.CharField(db_column='pageName', blank=True, null=True, default=0)
    isdelete = models.BooleanField(db_column='isDelete', blank=True, null=True)
    date_time = models.DateTimeField(db_column='date_time', blank=True, null=True, auto_now=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'adaptdocx_formjson_data'


class AdaptdocxClient(models.Model):
    client_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserDetails, models.DO_NOTHING)
    email = models.CharField(blank=True, null=True, unique=True)
    martial_status = models.CharField(blank=True, null=True)
    client_private = models.BooleanField(blank=True, null=True)
    primary_phone = models.JSONField()
    firm_client_id = models.CharField(blank=True, null=True)
    estate_value = models.IntegerField(blank=True, null=True)
    found_us = models.CharField(blank=True, null=True)
    refferal_code = models.CharField(blank=True, null=True)
    prefix = models.CharField(blank=True, null=True)
    first_name = models.CharField(blank=True, null=True)
    middle_name = models.CharField(blank=True, null=True)
    last_name = models.CharField(blank=True, null=True)
    suffix = models.CharField(blank=True, null=True)
    nick_name = models.CharField(blank=True, null=True)
    gender = models.CharField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    us_citizen = models.BooleanField(blank=True, null=True)
    address_line1 = models.JSONField()
    # address_line2 = models.CharField(blank=True, null=True)
    zip_code = models.CharField(blank=True, null=True)
    city = models.CharField(blank=True, null=True)
    county = models.CharField(blank=True, null=True)
    state = models.CharField(blank=True, null=True)
    country = models.CharField(blank=True, null=True)

    spouse_prefix = models.CharField(blank=True, null=True)
    spouse_firstname = models.CharField(blank=True, null=True)
    spouse_middlename = models.CharField(blank=True, null=True)
    spouse_lastname = models.CharField(blank=True, null=True)
    spouse_suffix = models.CharField(blank=True, null=True)
    spouse_nickname = models.CharField(blank=True, null=True)
    spouse_gender = models.CharField(blank=True, null=True)
    spouse_dob = models.DateField(blank=True, null=True)
    spouse_us_citizen = models.BooleanField(blank=True, null=True)
    spouse_phone = models.CharField(blank=True, null=True)
    spouse_email = models.CharField(blank=True, null=True)
    is_deleted = models.BooleanField(blank=True,null=True)
    date_time = models.DateTimeField(db_column='date_time', blank=True, null=True, auto_now=True)
    objects = ClientsManager()

    class Meta:
        managed = False
        db_table = 'adaptdocx_client'


class AdaptdocxMatters(models.Model):
    id = models.BigAutoField(primary_key=True)
    drafter = models.ForeignKey(UserDetails, models.DO_NOTHING, db_column='drafter', blank=True, null=True)
    client = models.ForeignKey('AdaptdocxClient', models.DO_NOTHING, db_column='client', blank=True, null=True,
                               related_name='client_data')
    offering = models.ForeignKey('AdaptdocxFormSubcategory', models.DO_NOTHING, db_column='offering', blank=True,
                                 null=True)
    firmmatterid = models.CharField(db_column='firmMatterId', blank=True, null=True)  # Field name made lowercase.
    mattertitle = models.CharField(db_column='matterTitle', blank=True, null=True)  # Field name made lowercase.
    representation = models.CharField(db_column='representation', blank=True, null=True)  # Field name made lowercase.
    fee = models.IntegerField(db_column='fee', blank=True, null=True)
    is_delete = models.BooleanField(db_column='is_delete', default=False)
    date_time = models.DateTimeField(db_column='date_time', blank=True, null=True, auto_now=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'adaptdocx_matters'


class AdaptdocxSaveJsonData(models.Model):
    id = models.BigAutoField(primary_key=True)
    client_id = models.ForeignKey('AdaptdocxClient', models.DO_NOTHING, blank=True, null=True, db_column='client_id')
    matter_id = models.ForeignKey('AdaptdocxMatters', models.DO_NOTHING, blank=True, null=True, db_column='matter_id',related_name='matter_data')
    offering_id = models.ForeignKey('AdaptdocxFormSubcategory', models.DO_NOTHING, blank=True, null=True,
                                    db_column='offering_id')
    form_data = models.JSONField(blank=True, null=True)  # This field type is a guess.
    date_time = models.DateTimeField(db_column='date_time', blank=True, null=True, auto_now=True)
    objects = models.Manager()
    class Meta:
        managed = False
        db_table = 'adaptdocx_save_json_data'


class AdaptdocxClientPhone(models.Model):
    id = models.BigAutoField(primary_key=True)
    client = models.ForeignKey(AdaptdocxClient, models.DO_NOTHING, blank=True, null=True, db_column='client_id')
    phone_type = models.CharField(blank=True, null=True)
    is_primary = models.BooleanField(blank=True, null=True)
    phone_number = models.CharField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'adaptdocx_client_phone'


class AdaptdocxClientAddress(models.Model):
    id = models.BigAutoField(primary_key=True)
    client = models.ForeignKey('AdaptdocxClient', models.DO_NOTHING, blank=True, null=True)
    address_type = models.CharField(blank=True, null=True)
    address_1 = models.CharField(blank=True, null=True)
    address_2 = models.CharField(blank=True, null=True)
    postal_code = models.CharField(blank=True, null=True)
    city = models.CharField(blank=True, null=True)
    country = models.CharField(blank=True, null=True)
    state = models.CharField(blank=True, null=True)
    is_primary = models.BooleanField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'adaptdocx_client_address'


class AdaptdocxClientNotes(models.Model):
    id = models.BigAutoField(primary_key=True)
    client = models.ForeignKey('AdaptdocxClient', models.DO_NOTHING, blank=True, null=True)
    notes = models.CharField(blank=True, null=True)
    date_time = models.DateTimeField(blank=True, null=True)
    objects = models.Manager()
    class Meta:
        managed = False
        db_table = 'adaptdocx_client_notes'




class AdaptdocxFormjsonDataDummy(models.Model):
    id = models.BigAutoField(primary_key=True)
    subcategoryId = models.ForeignKey('AdaptdocxFormSubcategory', models.DO_NOTHING, db_column='subcategoryId',
                                      blank=True, null=True)
    formJson = models.JSONField(db_column='formJson', blank=True, null=True)

    createddate = models.DateTimeField(db_column='createdDate', blank=True, null=True)
    pagename = models.CharField(db_column='pageName', blank=True, null=True, default=0)
    isdelete = models.BooleanField(db_column='isDelete', blank=True, null=True)
    date_time = models.DateTimeField(db_column='date_time', blank=True, null=True, auto_now=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'adaptdocx_formjson_data_dummy'


class AdaptdocxClientHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    clientid = models.ForeignKey('AdaptdocxClient', models.DO_NOTHING, db_column='clientId', blank=True,
                                 null=True)  # Field name made lowercase.
    matterid = models.ForeignKey('AdaptdocxMatters', models.DO_NOTHING, db_column='matterId', blank=True, null=True)
    date_time = models.DateTimeField(blank=True, null=True)
    notes = models.CharField(blank=True, null=True)
    action = models.CharField(blank=True, null=True)
    drafter = models.CharField(blank=True, null=True)
    objects = models.Manager()
    class Meta:
        managed = False
        db_table = 'adaptdocx_client_history'


class AdaptdocxMattersigned(models.Model):
    id = models.BigAutoField(primary_key=True)
    matter = models.ForeignKey('AdaptdocxMatters', models.DO_NOTHING, blank=True, null=True)
    signed = models.BooleanField(blank=True, null=True)
    closed = models.BooleanField(blank=True, null=True)
    signed_date = models.DateTimeField(blank=True, null=True)
    closed_date = models.DateTimeField(blank=True, null=True)
    objects = models.Manager()
    class Meta:
        managed = False
        db_table = 'adaptdocx_mattersigned'
