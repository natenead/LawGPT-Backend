from rest_framework import serializers
from .models import UserDetails, Role, Depositionhistoryquestions, Studentrecord,Userlogs


class CustomUserSerializerForPut(serializers.ModelSerializer):
    class Meta:
        model = UserDetails
        exclude = ['role', 'password', 'is_deleted']
        # fields = '__all__'


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserDetails
        # exclude = ('toggle_option','extension_paid')
        exclude = ('toggle_option',)
        # fields = '__all__'

    def save(self, request,value):
        email = self.validated_data.pop('email')
        fullname = self.validated_data.pop('fullname')
        password = self.validated_data.pop('password')
        role = self.validated_data.pop('role')
        is_deleted = self.validated_data.pop('is_deleted')

        new_user = UserDetails(
            email=email,
            fullname=fullname,
            role=role,
            is_deleted=is_deleted,
            toggle_option = True,
            # extension_paid = value

        )
        new_user.set_password(password)
        new_user.save()
        return new_user


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()


class UserRole(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class DepositionhistoryquestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depositionhistoryquestions
        fields = '__all__'


'''
These are used for AI

'''


class Topics(serializers.Serializer):
    topics = serializers.ListSerializer(child=serializers.CharField())
    situation = serializers.CharField(max_length=1000)
    botid = serializers.IntegerField()



class QuestionForTopic(serializers.Serializer):
    topics_list = serializers.ListSerializer(child=serializers.CharField(),required=False)
    situation = serializers.CharField(max_length=1000)


class Questions(serializers.Serializer):
    questions = serializers.ListSerializer(child=serializers.CharField())


class UploadSerializer(serializers.Serializer):
    file_uploaded = serializers.FileField()
    # file_uploaded = serializers.ListField(child=serializers.FileField())


class upload_doc(serializers.Serializer):
    collections = serializers.ListSerializer(child=serializers.CharField())
    files = serializers.ListSerializer(child=serializers.CharField())
    questions = serializers.ListSerializer(child=serializers.CharField())
    botid = serializers.IntegerField()


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Studentrecord
        fields = '__all__'


class StudentUploadDoc(serializers.Serializer):
    filename = serializers.CharField()
    base64 = serializers.CharField()
    extension = serializers.CharField()


class StudentSignUpSerializer(CustomUserSerializer):
    keys = serializers.ListSerializer(child=serializers.CharField())
    filename = serializers.ListSerializer(child=serializers.CharField())
    # image = serializers.CharField()


class PaymentMethod(CustomUserSerializer):
    token = serializers.CharField()
    price = serializers.IntegerField()
    # apikey = serializers.CharField()
    # userid = serializers.IntegerField(required=False)
    # email = serializers.CharField()
    # name = serializers.CharField()

class PaymentMethodAlready(serializers.Serializer):
    token = serializers.CharField()
    price = serializers.IntegerField()

class PaymentCancel(serializers.Serializer):
    subscibeId = serializers.CharField()
    userid = serializers.IntegerField()

class Suggestion(serializers.Serializer):
    content = serializers.CharField()



class APIKey(serializers.Serializer):
    apikey = serializers.CharField()
    # userid = serializers.IntegerField()

class SaveTemplate(serializers.Serializer):
    botid = serializers.IntegerField()
    filename = serializers.CharField()
    content = serializers.CharField()


class CardInfo(serializers.Serializer):
    token = serializers.CharField()


class UpdatePassword(serializers.Serializer):
    password = serializers.CharField()


class MonthlyFilter(serializers.Serializer):
    month = serializers.IntegerField()
    year = serializers.IntegerField()


class ChangePackage(serializers.Serializer):
    STATUS_CHOICES = (
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade'),
    )

    currentRole = serializers.IntegerField()
    updatedRole = serializers.IntegerField()
    bit = serializers.ChoiceField(choices=STATUS_CHOICES)
    token = serializers.CharField(required=False)
    apikey = serializers.CharField(required=False)

class UserLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Userlogs
        fields = "__all__"


class QuerySerializer(serializers.Serializer):
    statesList = serializers.ListSerializer(child=serializers.CharField(),required=False)
    searchbit = serializers.BooleanField()
    botid = serializers.IntegerField()
    query = serializers.CharField()

class ToggleOption(serializers.Serializer):
    userId = serializers.IntegerField()
    toggleOption = serializers.BooleanField(default=False)


class StatesList (serializers.Serializer):
    statesList  = serializers.ListSerializer(child=serializers.CharField())


class QdrantList (serializers.Serializer):
    qdrantCollection  = serializers.ListSerializer(child=serializers.CharField())


class FreeTrail(serializers.Serializer):
    userId = serializers.CharField()
    IsExpired = serializers.BooleanField()



class PaymentMethodForQueryDoc(serializers.Serializer):
    STATUS_CHOICES = (
        ('100QueryDoc', '100QueryDoc'),
        ('50QueryDoc', '50QueryDoc'),
        ('100Query', '100Query'),
        ('50Query', '50Query'),
        ('50Doc', '50Doc'),
        ('25Doc', '25Doc'),
    )
    token = serializers.CharField()
    price = serializers.ChoiceField(choices=STATUS_CHOICES)
