from django.db import models
from .manager import CustomUserManager, AdminUserManager
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.postgres.fields import ArrayField


class Role(models.Model):
    role_id = models.AutoField(db_column='RoleId', primary_key=True)
    role_name = models.CharField(max_length=50)
    objects = models.Manager()

    class Meta:
        # managed = False
        db_table = 'UserRole'


class UserDetails(AbstractBaseUser):
    fullname = models.CharField(max_length=64)
    email = models.CharField(max_length=254, unique=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=0)
    created_date = models.DateTimeField(auto_now=True)
    toggle_option = models.BooleanField(db_column='toggle_option', default=False)
    # extension_paid = models.BooleanField(db_column='extension_paid', default=False)
    last_login = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        # managed = False
        db_table = 'UserDetails'

    # @property
    # def modified_by(self):
    #     return self.user_id

    def __str__(self):
        return self.email


class UserHistory(models.Model):
    id = models.AutoField(primary_key=True)
    userid = models.ForeignKey('UserDetails', on_delete=models.DO_NOTHING, db_column='UserId')
    query = models.CharField(max_length=5000, db_column='Query')
    answer = models.CharField(max_length=5000, db_column='Answer')

    class Meta:
        db_table = 'Userhistory'
        managed = False


class Attorneys(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    attorney = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'attorneys'


class Casebody(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    head_matter = models.TextField(blank=True, null=True)
    corrections = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'casebody'


class Citation(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    cite = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'citation'


class CitesTo(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    cite = models.TextField(blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    reporter = models.TextField(blank=True, null=True)
    year = models.TextField(blank=True, null=True)
    opinion_id = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'cites_to'


class Court(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    court_id = models.BigIntegerField(blank=True, null=True)
    court_name = models.TextField(blank=True, null=True)
    court_name_abbreviation = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'court'


class Judges(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    judge = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'judges'


class Jurisdiction(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    jurisdiction_id = models.BigIntegerField(blank=True, null=True)
    jurisdiction_name = models.TextField(blank=True, null=True)
    jurisdiction_name_abbreviation = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'jurisdiction'


class Main(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    name_abbreviation = models.TextField(blank=True, null=True)
    decision_date = models.TextField(blank=True, null=True)
    docket_number = models.TextField(blank=True, null=True)
    frontend_pdf_url = models.TextField(blank=True, null=True)
    head_matter = models.TextField(blank=True, null=True)
    reporter_id = models.BigIntegerField(blank=True, null=True)
    court_id = models.BigIntegerField(blank=True, null=True)
    jurisdiction_id = models.BigIntegerField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'main'


class Opinion(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    opinion_text = models.TextField(blank=True, null=True)
    opinion_type = models.TextField(blank=True, null=True)
    opinion_author = models.TextField(blank=True, null=True)
    opinion_id = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'opinion'


class Parties(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    party = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'parties'


class Reporter(models.Model):
    case_id = models.BigIntegerField(primary_key=True)
    reporter_id = models.BigIntegerField(blank=True, null=True)
    reporter_name = models.TextField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'reporter'


class Notifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    description = models.CharField(db_column='Description', max_length=255, blank=True, null=True)
    createddate = models.DateField(db_column='CreatedDate', blank=True, null=True)
    createdid = models.BigIntegerField(db_column='CreatedId', blank=True, null=True)
    forwhichuser = models.BigIntegerField(db_column='ForWhichUser', blank=True, null=True)
    isread = models.TextField(db_column='IsRead', blank=True, null=True)
    permanenetdel = models.TextField(db_column='PermanenetDel', blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'Notifications'


class Userbot(models.Model):
    botid = models.BigAutoField(db_column='BotId', primary_key=True)  # Field name made lowercase.
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId')  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    isarchive = models.BooleanField(db_column='isArchive', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserBot'


class Depositionhistorytopics(models.Model):
    topicid = models.BigAutoField(db_column='TopicId', primary_key=True)  # Field name made lowercase.
    topics = models.CharField(db_column='Topics', blank=True, null=True)  # Field name made lowercase.
    botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='BotId', blank=True,
                              null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    situation = models.CharField(blank=True, null=True)

    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'DepositionHistoryTopics'


class Depositionhistoryquestions(models.Model):
    questionid = models.BigAutoField(db_column='QuestionId', primary_key=True)  # Field name made lowercase.
    tid = models.ForeignKey('Depositionhistorytopics', models.DO_NOTHING, db_column='TId', blank=True,
                            null=True)  # Field name made lowercase.
    question = models.CharField(db_column='Question', blank=True, null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'DepositionHistoryQuestions'


class Generalchathistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True,
                               null=True)  # Field name made lowercase.
    question = models.CharField(db_column='Question', blank=True, null=True)  # Field name made lowercase.
    answer = models.CharField(db_column='Answer', blank=True, null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='BotId', blank=True,
                              null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'GeneralChatHistory'


class Simplechathistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='BotId', blank=True,
                              null=True)  # Field name made lowercase.
    query = models.CharField(db_column='Query', blank=True, null=True)  # Field name made lowercase.
    Sources = ArrayField(models.IntegerField(db_column='Sources', blank=True,
                                             null=True))  # Field name made lowercase. This field type is a guess.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'SimpleChatHistory'


class AdminUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    adminid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='AdminId')  # Field name made lowercase.
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId',
                               related_name='adminuser_userid_set', blank=True, null=True)  # Field name made lowercase.
    is_deleted = models.BooleanField(db_column='isDelete')
    present = AdminUserManager()

    class Meta:
        managed = False
        db_table = 'AdminUser'


# class Uploadedfilescorehistory(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='botid', blank=True, null=True)
#     filename = models.JSONField(db_column='FileName', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
#     VDName = ArrayField(models.CharField(max_length=500,blank=True, null=True))  # Field name made lowercase. This field type is a guess.
#     createddate = models.DateField(db_column='CreatedDate', blank=True, null=True)
#     class Meta:
#         managed = False
#         db_table = 'UploadedFileScoreHistory'
#


class Uploadedfilescorehistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='botid', blank=True, null=True)
    VDName = ArrayField(models.CharField(max_length=5000, blank=True, null=True))
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)
    FileName = ArrayField(models.CharField(max_length=5000, blank=True, null=True))
    Questions = ArrayField(models.CharField(max_length=5000, blank=True, null=True))
    response = models.JSONField(db_column='Response', blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UploadedFileScoreHistory'


class Studentrecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True, null=True)
    Records = ArrayField(models.CharField(max_length=5000, blank=True, null=True))
    FileNames = ArrayField(models.CharField(max_length=5000, blank=True, null=True))
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)
    isrejected = models.BooleanField(db_column='isRejected', blank=True, null=True)
    isapproved = models.BooleanField(db_column='isApproved', blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'StudentRecord'


class Userqueryrecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True,
                               null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserQueryRecord'


class Drafttemplates(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    community = models.BooleanField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'drafttemplates'


class Userlastlogin(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True,
                               null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserLastLogin'


class Uploadeddocumenthistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='BotId', blank=True,
                              null=True)  # Field name made lowercase.
    collectionname = models.CharField(db_column='CollectionName', blank=True, null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.

    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UploadedDocumentHistory'


class Uploadeddocumentsummary(models.Model):
    id = models.BigAutoField(primary_key=True)
    botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='BotId', blank=True,
                              null=True)  # Field name made lowercase.
    # summary = models.TextField(db_column='Summary', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    summary = models.JSONField(db_column='Summary', blank=True, null=True)

    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UploadedDocumentSummary'


class Uploadeddocumentqueries(models.Model):
    id = models.BigAutoField(primary_key=True)
    botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='BotId', blank=True,
                              null=True)  # Field name made lowercase.
    question = models.CharField(db_column='Question', blank=True, null=True)  # Field name made lowercase.
    answer = models.CharField(db_column='Answer', blank=True, null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.

    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UploadedDocumentQueries'


class Lookups(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(db_column='Name', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Lookups'


class Mostlyusedfeature(models.Model):
    id = models.BigAutoField(primary_key=True)
    featureid = models.ForeignKey('Lookups', models.DO_NOTHING, db_column='FeatureId', blank=True,
                                  null=True)  # Field name made lowercase.
    count = models.BigIntegerField(db_column='Count', blank=True, null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'MostlyUsedFeature'


class Userpricing(models.Model):
    id = models.BigAutoField(primary_key=True)
    customerid = models.CharField(db_column='customerId', blank=True, null=True)  # Field name made lowercase.
    token = models.CharField(db_column='Token', blank=True, null=True)  # Field name made lowercase.
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True,
                               null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    payment = models.BigIntegerField(db_column='Payment', blank=True, null=True)  # Field name made lowercase.
    adminuserid = models.BigIntegerField(db_column='AdminUserId', blank=True, null=True)  # Field name made lowercase.
    subscribe_id = models.CharField(blank=True, null=True)
    cancelpayment = models.BooleanField(db_column='cancelPayment', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserPricing'


class Savedraftertemplate(models.Model):
    id = models.BigAutoField(primary_key=True)
    botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='BotId', blank=True,
                              null=True)  # Field name made lowercase.
    filename = models.CharField(db_column='FileName', blank=True, null=True)  # Field name made lowercase.
    content = models.JSONField(blank=True, null=True)
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'SaveDrafterTemplate'


class Userapikeys(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True,
                               null=True)  # Field name made lowercase.
    apikey = models.CharField(db_column='ApiKey ', blank=True,
                              null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    isdelete = models.BooleanField(db_column='IsDelete', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserAPIKeys'


class Userstorage(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True,
                               null=True)  # Field name made lowercase.
    storage = models.BigIntegerField(blank=True, null=True)
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    isdelete = models.BooleanField(db_column='IsDelete', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserStorage'


class DepositionChatHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True,
                               null=True)  # Field name made lowercase.
    prompt = models.TextField()
    response = models.TextField()
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    botid = models.ForeignKey('Userbot', models.DO_NOTHING, db_column='BotId', blank=True,
                              null=True)  # Field name made lowercase.


class Usertoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True,
                               null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    isarchived = models.BooleanField(db_column='IsArchived', blank=True, null=True)  # Field name made lowercase.
    token = models.CharField(db_column='Token', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserToken'


class Userlogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='UserId', blank=True,
                               null=True)  # Field name made lowercase.
    logdata = models.CharField(db_column='LogData', blank=True, null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    isarchived = models.BooleanField(db_column='IsArchived', blank=True, null=True)  # Field name made lowercase.
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserLogs'


class Userfreetrail(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('Userdetails', models.DO_NOTHING, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    expired_date = models.DateTimeField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserFreeTrail'


class Userquerydocrecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    query_number = models.IntegerField(blank=True, null=True)
    document_number = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey('Userdetails', models.DO_NOTHING, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    is_delete = models.BooleanField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'UserQueryDocRecord'


class Pineconeindexname(models.Model):
    id = models.BigAutoField(primary_key=True)
    index_name = models.CharField(blank=True, null=True)
    isfull = models.BooleanField(db_column='isFull', blank=True, null=True)
    isfree = models.BooleanField(db_column='isFree', blank=True, null=True)
    datetime = models.DateTimeField(db_column='dateTime', blank=True, null=True)
    objects = models.Manager()
    class Meta:
        managed = False
        db_table = 'PineconeIndexName'
