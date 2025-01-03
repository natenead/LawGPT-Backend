# Generated by Django 4.2.3 on 2024-01-12 12:13

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('LawApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminUser',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_column='isDelete')),
            ],
            options={
                'db_table': 'AdminUser',
                'managed': False,
            },
            managers=[
                ('present', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='Attorneys',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('attorney', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'attorneys',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Casebody',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('head_matter', models.TextField(blank=True, null=True)),
                ('corrections', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'casebody',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Citation',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('cite', models.TextField(blank=True, null=True)),
                ('type', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'citation',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='CitesTo',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('cite', models.TextField(blank=True, null=True)),
                ('category', models.TextField(blank=True, null=True)),
                ('reporter', models.TextField(blank=True, null=True)),
                ('year', models.TextField(blank=True, null=True)),
                ('opinion_id', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cites_to',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Court',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('court_id', models.BigIntegerField(blank=True, null=True)),
                ('court_name', models.TextField(blank=True, null=True)),
                ('court_name_abbreviation', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'court',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Depositionhistoryquestions',
            fields=[
                ('questionid', models.BigAutoField(db_column='QuestionId', primary_key=True, serialize=False)),
                ('question', models.CharField(blank=True, db_column='Question', null=True)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
            ],
            options={
                'db_table': 'DepositionHistoryQuestions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Depositionhistorytopics',
            fields=[
                ('topicid', models.BigAutoField(db_column='TopicId', primary_key=True, serialize=False)),
                ('topics', models.CharField(blank=True, db_column='Topics', null=True)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
                ('situation', models.CharField(blank=True, null=True)),
            ],
            options={
                'db_table': 'DepositionHistoryTopics',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Drafttemplates',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('summary', models.TextField(blank=True, null=True)),
                ('community', models.BooleanField(blank=True, null=True)),
            ],
            options={
                'db_table': 'drafttemplates',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Generalchathistory',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('question', models.CharField(blank=True, db_column='Question', null=True)),
                ('answer', models.CharField(blank=True, db_column='Answer', null=True)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
            ],
            options={
                'db_table': 'GeneralChatHistory',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Judges',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('judge', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'judges',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Jurisdiction',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('jurisdiction_id', models.BigIntegerField(blank=True, null=True)),
                ('jurisdiction_name', models.TextField(blank=True, null=True)),
                ('jurisdiction_name_abbreviation', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'jurisdiction',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Lookups',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, db_column='Name', null=True)),
            ],
            options={
                'db_table': 'Lookups',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Main',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True, null=True)),
                ('name_abbreviation', models.TextField(blank=True, null=True)),
                ('decision_date', models.TextField(blank=True, null=True)),
                ('docket_number', models.TextField(blank=True, null=True)),
                ('frontend_pdf_url', models.TextField(blank=True, null=True)),
                ('head_matter', models.TextField(blank=True, null=True)),
                ('reporter_id', models.BigIntegerField(blank=True, null=True)),
                ('court_id', models.BigIntegerField(blank=True, null=True)),
                ('jurisdiction_id', models.BigIntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'main',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Mostlyusedfeature',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('count', models.BigIntegerField(blank=True, db_column='Count', null=True)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
            ],
            options={
                'db_table': 'MostlyUsedFeature',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Notifications',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('description', models.CharField(blank=True, db_column='Description', max_length=255, null=True)),
                ('createddate', models.DateField(blank=True, db_column='CreatedDate', null=True)),
                ('createdid', models.BigIntegerField(blank=True, db_column='CreatedId', null=True)),
                ('forwhichuser', models.BigIntegerField(blank=True, db_column='ForWhichUser', null=True)),
                ('isread', models.TextField(blank=True, db_column='IsRead', null=True)),
                ('permanenetdel', models.TextField(blank=True, db_column='PermanenetDel', null=True)),
            ],
            options={
                'db_table': 'Notifications',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Opinion',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('opinion_text', models.TextField(blank=True, null=True)),
                ('opinion_type', models.TextField(blank=True, null=True)),
                ('opinion_author', models.TextField(blank=True, null=True)),
                ('opinion_id', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'opinion',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Parties',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('party', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'parties',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Reporter',
            fields=[
                ('case_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('reporter_id', models.BigIntegerField(blank=True, null=True)),
                ('reporter_name', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'reporter',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Savedraftertemplate',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('filename', models.CharField(blank=True, db_column='FileName', null=True)),
                ('content', models.JSONField(blank=True, null=True)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
            ],
            options={
                'db_table': 'SaveDrafterTemplate',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Simplechathistory',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('query', models.CharField(blank=True, db_column='Query', null=True)),
                ('Sources', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True, db_column='Sources', null=True), size=None)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
            ],
            options={
                'db_table': 'SimpleChatHistory',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Studentrecord',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Records', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=5000, null=True), size=None)),
                ('FileNames', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=5000, null=True), size=None)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
                ('isrejected', models.BooleanField(blank=True, db_column='isRejected', null=True)),
                ('isapproved', models.BooleanField(blank=True, db_column='isApproved', null=True)),
            ],
            options={
                'db_table': 'StudentRecord',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Uploadeddocumenthistory',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('collectionname', models.CharField(blank=True, db_column='CollectionName', null=True)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
            ],
            options={
                'db_table': 'UploadedDocumentHistory',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Uploadeddocumentqueries',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('question', models.CharField(blank=True, db_column='Question', null=True)),
                ('answer', models.CharField(blank=True, db_column='Answer', null=True)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
            ],
            options={
                'db_table': 'UploadedDocumentQueries',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Uploadeddocumentsummary',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('summary', models.JSONField(blank=True, db_column='Summary', null=True)),
            ],
            options={
                'db_table': 'UploadedDocumentSummary',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Uploadedfilescorehistory',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('VDName', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=5000, null=True), size=None)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
                ('FileName', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=5000, null=True), size=None)),
                ('Questions', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=5000, null=True), size=None)),
                ('response', models.JSONField(blank=True, db_column='Response', null=True)),
            ],
            options={
                'db_table': 'UploadedFileScoreHistory',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Userapikeys',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('apikey', models.CharField(blank=True, db_column='ApiKey ', null=True)),
                ('isdelete', models.BooleanField(blank=True, db_column='IsDelete', null=True)),
            ],
            options={
                'db_table': 'UserAPIKeys',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Userbot',
            fields=[
                ('botid', models.BigAutoField(db_column='BotId', primary_key=True, serialize=False)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
                ('isarchive', models.BooleanField(blank=True, db_column='isArchive', null=True)),
            ],
            options={
                'db_table': 'UserBot',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Userlastlogin',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
            ],
            options={
                'db_table': 'UserLastLogin',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Userqueryrecord',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
            ],
            options={
                'db_table': 'UserQueryRecord',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Userstorage',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('storage', models.BigIntegerField(blank=True, null=True)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
                ('isdelete', models.BooleanField(blank=True, db_column='IsDelete', null=True)),
            ],
            options={
                'db_table': 'UserStorage',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Usertoken',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
                ('isarchived', models.BooleanField(blank=True, db_column='IsArchived', null=True)),
                ('token', models.CharField(blank=True, db_column='Token', null=True)),
            ],
            options={
                'db_table': 'UserToken',
                'managed': False,
            },
        ),
        migrations.AlterModelOptions(
            name='userhistory',
            options={'managed': False},
        ),
        migrations.AlterModelOptions(
            name='userpricing',
            options={'managed': False},
        ),
        migrations.AlterModelTable(
            name='userdetails',
            table='UserDetails',
        ),
        migrations.CreateModel(
            name='DepositionChatHistory',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('prompt', models.TextField()),
                ('response', models.TextField()),
                ('createddate', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
                ('botid', models.ForeignKey(blank=True, db_column='BotId', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='LawApp.userbot')),
                ('userid', models.ForeignKey(blank=True, db_column='UserId', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
