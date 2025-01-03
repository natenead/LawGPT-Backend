from rest_framework import serializers
from .models import (
    AdaptdocxFormCategory,
    AdaptdocxFormSubcategory,
    AdaptdocxFormjsonData,
    AdaptdocxClient,
    AdaptdocxMatters,
    AdaptdocxSaveJsonData,
    AdaptdocxClientPhone,
    AdaptdocxClientAddress,
    AdaptdocxClientNotes,
    AdaptdocxClientHistory
)
import datetime


class AdaptdocxFormCategorySerizalizer(serializers.ModelSerializer):
    class Meta:
        model = AdaptdocxFormCategory
        exclude = ('isdelete', 'createddate')


class AdaptdocxFormSubcategorySerizalizer(serializers.ModelSerializer):
    class Meta:
        model = AdaptdocxFormSubcategory
        exclude = ('isdelete', 'createddate')


class AdaptdocxFormjsonDataSerizalizer(serializers.ModelSerializer):
    categoryName = serializers.CharField()

    class Meta:
        model = AdaptdocxFormjsonData
        exclude = ('isdelete', 'createddate', 'pagename')


class AdaptdocxFormjsonDataUpdateSerizalizer(serializers.Serializer):
    categoryName = serializers.CharField()
    formJson = serializers.JSONField()
    subcategoryId = serializers.IntegerField()


class AdaptdocxClientSerializer(serializers.ModelSerializer):
    MARTIAL_CHOICES = (
        ('legallyMarried', 'Legally Married'),
        ('notMarried', 'Individual/Not Married'),
        ('legalRegister', 'Legal Registered Civil Union Or Domestic Patnership'),
    )
    FOUND_US_CHOICES = (
        'Bing', 'Bing Search',
        'Google', 'Google Search',
        'Other', 'Other',
        'Refferal', 'Refferal',
        'Search Engine(Unspecified)', 'Search Engine(Unspecified)',
        'Yahoo Search', 'Yahoo Search'

    )
    Prefix_CHOICES = (
        ('Dr', 'Dr'),
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Ms', 'Ms'),
    )
    SUFFIX_CHOICES = (
        ('II', 'II'),
        ('III', 'III'),
        ('IV', 'IV'),
        ('Jr', 'Jr'),
        ('Sr', 'Sr'),
    )
    martial_status = serializers.ChoiceField(choices=MARTIAL_CHOICES)
    found_us = serializers.ChoiceField(choices=FOUND_US_CHOICES,allow_blank=True,required=False)
    prefix = serializers.ChoiceField(choices=Prefix_CHOICES,required=False,allow_blank=True)
    suffix = serializers.ChoiceField(choices=SUFFIX_CHOICES,required=False,allow_blank=True)
    email = serializers.EmailField(required=False,allow_blank=True)
    spouse_dob = serializers.DateField(default=datetime.date.today, required=False)
    dob = serializers.DateField(default=datetime.date.today)
    primary_phone = serializers.JSONField()
    address_line1 = serializers.JSONField()
    middle_name = serializers.CharField(required=False,allow_blank=True)
    # address_line1 = serializers.JSONField()
    class Meta:
        model = AdaptdocxClient
        exclude = ['user']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

            # Save the updated instance
        instance.save()

        return instance

    def create(self, validated_data):
        obj = AdaptdocxClient(**validated_data)
        # obj.user = validated_data['user']
        obj.save()
        return

    def save(self, user_id, value, **kwargs):
        if value:
            self.instance = self.update(value, self.validated_data)
            return self.instance

        validated_data = {**self.validated_data, **kwargs, 'user': user_id}
        self.instance = self.create(validated_data)
        return self.instance


class AdaptdocxMattersSerializer(serializers.ModelSerializer):
    REPRESENTAION_CHOICE = (
        ('Individual', 'Individual'),
        ('Joint', 'Joint')
    )
    is_delete = serializers.BooleanField(default=False)
    fee = serializers.IntegerField(default=0)
    representation = serializers.ChoiceField(choices=REPRESENTAION_CHOICE)

    class Meta:
        model = AdaptdocxMatters
        fields = '__all__'


class AdaptdocxSaveJsonDataSerializer(serializers.ModelSerializer):
    # clientId = serializers.PrimaryKeyRelatedField(queryset=AdaptdocxClient.objects.all())
    class Meta:
        model = AdaptdocxSaveJsonData
        fields = '__all__'

class AdaptdocxClientPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptdocxClientPhone
        fields = '__all__'



class AdaptdocxClientAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptdocxClientAddress
        fields = '__all__'

class AdaptdocxClientNotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptdocxClientNotes
        fields = '__all__'


class AdaptdocxClientHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptdocxClientHistory
        fields = '__all__'


class MatterSignedClosed(serializers.Serializer):
    matter_id = serializers.IntegerField()
    client_id = serializers.IntegerField()
    signed = serializers.BooleanField()
    closed = serializers.BooleanField()