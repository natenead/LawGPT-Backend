import random
from rest_framework.response import Response
# from langchain.vectorstores import Pinecone
from ..models import Drafttemplates, Mostlyusedfeature, Savedraftertemplate, Userbot, AdminUser
from langchain.embeddings import HuggingFaceEmbeddings
from drf_yasg.utils import swagger_auto_schema
import requests
from langchain_pinecone import PineconeVectorStore as lang_pinecone

from django.db.models import Window
from django.db.models.functions import RowNumber
from django.db.models import F
import pypandoc
from datetime import datetime
import boto3, re
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .general_utils import *
from botocore.client import Config
from dotenv import load_dotenv
import os
from ..models import Userapikeys
from drf_yasg import openapi
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from ..serializers import Suggestion, SaveTemplate,QdrantList
from ..utils import getOpenAIKey,is_user_able_to_query,calculate_page_number

load_dotenv()
aws_key = os.getenv('ACCESS_KEY')
aws_secret_key = os.getenv('SECRET_ACCESS_KEY')
aws_space_name = os.getenv('SPACE_NAME')
embed_fn = HuggingFaceEmbeddings(model_name=os.getenv("model_name"))
from pinecone import Pinecone

api_key = os.getenv("PINECONE_API_KEY")
environment = os.getenv("PINCONE_ENV")


def put_file_to_s3(content, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_path: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # Upload the file
    session = boto3.session.Session()
    region = 'us-east-1'
    client = session.client('s3',
                            region_name=region,
                            endpoint_url=os.getenv("DRAFTING_ENDPOINT_S3_URL"),
                            aws_access_key_id=aws_key,
                            aws_secret_access_key=aws_secret_key,
                            config=Config(signature_version='s3v4')

                            )

    # s3.put_object(Bucket=bucket_name, Key=object_key, Body=file)
    client.put_object(Body=content, Bucket=bucket, Key=object_name)

    return True


def get_object_link(key):
    # key = 'American-Red-Cross-Donation-Receipt-Template.docx'
    aws_key = os.getenv('ACCESS_KEY')
    aws_secret_key = os.getenv('SECRET_ACCESS_KEY')
    # aws_space_name=os.getenv('SPACE_NAME')
    bucket_name = os.getenv("DRAFTING_BUCKET_NAME")
    region = 'us-east-1'
    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=region,
                            endpoint_url=os.getenv("DRAFTING_ENDPOINT_S3_URL"),
                            aws_access_key_id=aws_key,
                            aws_secret_access_key=aws_secret_key,
                            config=Config(signature_version='s3v4')
                            )
    params = {'Bucket': bucket_name, 'Key': key}
    url = client.generate_presigned_url('get_object', Params=params, ExpiresIn=40000)
    return url


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True), ]
                     )
@api_view(['GET'])
@permission_classes([])
def get_drafts(request):
    try:
        # if request.user.role == 1:
        #     api_key_ = Userapikeys.objects.filter(userid=request.user.pk).filter(isdelete = False)
        #     if api_key_:
        #         api_key = api_key_[0].apikey
        # elif request.user.role == 3:
        #     api_key_ = Userapikeys.objects.filter(userid=AdminUser.present.get(userid=request.user.pk).pk).filter(isdelete = False)
        #     if api_key_:
        #         api_key = api_key_[0].apikey
        # else:
        #     api_key_ = Userapikeys.objects.filter(userid=6).filter(isdelete=False)
        #     if api_key_:
        #         api_key = api_key_[0].apikey
        if not request.user.is_authenticated:
            load_dotenv()
            open_ai_key = os.getenv('OPENAI_API_KEY')
        else:
            open_ai_key = is_user_able_to_query(request,1,0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        main_list = list()
        text = request.query_params.get('text')
        embed_fn = HuggingFaceEmbeddings(model_name="intfloat/e5-small-v2")

        index = lang_pinecone.from_existing_index(index_name=os.getenv("DRAFTING_TEMPLATES_PINECONE_INDEX_NAME"),
                                                  embedding=embed_fn)
        # conn, cursor = connect_to_postgres(HOST, PORT, DB_NAME, USER, PASSWORD)
        # random_integer = random.randint(4, 13)
        # print(random_integer)
        resp = {}
        check_source_list = []
        resp_list = list()
        try:
            docs = fetch_source_from_query_drafting_view(text, index, 10, open_ai_key)
        except:
            return Response({"message": "Your API key is invalid"}, status=status.HTTP_400_BAD_REQUEST)

        '''
        if docs['result'].lower() == 'no':
            return Response(
                {"error": "AI system did not yield any pertinent results in relation to the query."},
                status=status.HTTP_404_NOT_FOUND)
        '''

        # docs = index.similarity_search(text, k=int(random_integer))
        # title_list=[]
        # summary_list=[]
        for i in range(0, len(docs['source_documents'])):
            source_name = docs['source_documents'][i].metadata['source']
            source = source_name.replace(".pdf", ".docx")

            if source in check_source_list or source_name == "AST-Tenancy-Agreement..pdf":

                pass
            else:
                query = Drafttemplates.objects.filter(title=source)
                if not query.exists():
                    continue
                resp = {'fileName': source,
                        'summary': query[0].summary,
                        'url': get_object_link(source),
                        'key': source}
                resp_list.append(resp)

                # resp[source] = resp[source] = [query[0].summary, get_object_link(source),source]
            check_source_list.append(source)
        # for doc in docs:
        #     resp = {}
        #     source = docs['source_documents'][i].metadata['source']
        #     title = source[:-4]
        #     source = source[:-4] + '.docx'
        #
        #     # title_list.append(source)
        #     query = Drafttemplates.objects.filter(title=source)
        #     # cursor.execute(query, (source,))
        #     # data = cursor.fetchall()
        #     resp[source] = [query[0].summary, get_object_link(source),source]
        #     main_list.append(resp)
        if request.user.is_authenticated:
            obj = Mostlyusedfeature.objects.get(featureid=2)
            count = obj.count
            count += 1
            obj.count = count
            obj.save()
        return Response({'message': 'Drafter Data', "data": resp_list}, status=status.HTTP_200_OK)

    except Exception as ex:
        return Response({"message": "Error while getDrafs"}, status=status.HTTP_400_BAD_REQUEST)


# @swagger_auto_schema(method='GET',
#                      manual_parameters=[
#                          openapi.Parameter('source', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True), ]
#                      )
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def convertDocx2HTML(request):
#     try:
#         source = request.query_params.get('source')
#         source = get_object_link(source)
#         myuuid = str(uuid.uuid4())
#         response = requests.get(source)
#         doc_file_path=myuuid+".docx"
#         open(doc_file_path, "wb").write(response.content)
#         output = pypandoc.convert_file(doc_file_path, "html", format="docx")
#         os.remove(doc_file_path)
#         return Response({'message':'HTML Response',"data":output.replace('\n','')},status=status.HTTP_200_OK)
#     except Exception as ex:
#         try:
#             os.remove(doc_file_path)
#         except Exception: pass
#         # logger.critical(f'Error while getDrafs: {ex}')
#         return Response({"response":"Error"},status=status.HTTP_400_BAD_REQUEST)


# @swagger_auto_schema(method='POST',
#                      manual_parameters=[
#                          openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True), ]
#                      )
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# @parser_classes([MultiPartParser, FormParser])

# def uploadAndConvertDocx2HTML(request):
#     try:
#         file = request.FILES.get('file')
#         contents = file.read()
#         # contents = file.read()
#         file_extension = file.name.split(".")[-1]
#         if "docx"==file_extension:
#             myuuid = str(uuid.uuid4())+".docx"
#             with open(myuuid, 'wb') as tmp_file:
#                 tmp_file.write(contents)
#             output = pypandoc.convert_file(myuuid, "html", format="docx")
#             os.remove(myuuid)
#             return Response({"response":output.replace("\n","")},status=status.HTTP_200_OK)

#     except Exception as ex:
#         try:
#             os.remove(myuuid)
#         except Exception: pass
#         # logger.critical(f'Error while getDrafs: {ex}')
#         return Response({"error": "Error while getDrafs"},status=status.HTTP_400_BAD_REQUEST)
@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('key', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True), ]
                     )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getHeadings(request):
    try:
        temp_key = request.query_params.get('key')
        source = get_object_link(temp_key)
        suffix = temp_key.split(".")[-1]

        if suffix == "docx":
            loader = Docx2txtLoader(source)
        elif suffix == "pdf":
            loader = PyMuPDFLoader(source)
        else:
            return Response({"error": "Unsupported FIle format"}, status=status.HTTP_404_NOT_FOUND)

        txt = loader.load()
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request, 1, 0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        heading_list = generate_headings(txt[0].page_content, open_ai_key)
        heading_list = heading_list.replace("Missing", "").replace("Headings", "").split("\n")

        return Response(
            {"data": heading_list[-4:]}, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": "Error while getSuggestion"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                         openapi.Parameter('paragraph', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                     ]
                     )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def getSuggestion(request):
    try:
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request, 1, 0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)

        suggestion = update_text(request.query_params.get('text'), request.query_params.get('paragraph'), open_ai_key)

        return Response({"response": suggestion}, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": "Error while getSuggestion"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='GET')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def case_approved(request):
    # open_ai_key = getOpenAIKey(request)
    open_ai_key = is_user_able_to_query(request, 1, 0)
    if open_ai_key == 0:
        return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
    return Response({"response": "Draft added successfully"}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('heading', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                         # openapi.Parameter('paragraph', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                     ]
                     )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getHeadingsContent(request):
    try:
        heading = request.query_params.get('heading')
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request, 1, 0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        heading_content = generate_heading_content(heading, open_ai_key)
        return Response({"response": heading_content, 'heading': heading}, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": "Error while getSuggestion"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='POST',
                     manual_parameters=[
                         openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
                         openapi.Parameter('community_bit', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN,
                                           allow_empty_value=True, required=False),
                     ]
                     )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def community(request):
    community_bit = request.query_params.get('community_bit')
    # """Responsible to brings the uploaded file to the comunity.
    #    (It will upload to s3, summerize it and upload this summary to pinecone vectorstore)
    #
    # Args:
    #     user_id (int): Unique ID of the user
    #     file (file.object): uploaded file.
    #
    # Returns:
    #    json:  HTTP_200_OK if sucessfull otherwise HTTP_404_NOT_FOUND
    # """
    try:
        embed_fn_pinecone_draft = HuggingFaceEmbeddings(model_name="intfloat/e5-small-v2")
        file = request.FILES.get('file')
        user_id = request.user.pk
        contents = file.read()
        file_extension = f".{file.name.split('.')[-1]}"
        filename = f"{user_id}_{file.name}"
        put_file_to_s3(contents, os.getenv('DRAFTING_BUCKET_NAME'), filename)
        s3_url = get_object_link(filename)
        resp = {'key': filename, 'url': s3_url}
        supported_files = [".docx"]
        if file_extension in supported_files:
            if community_bit == 'false':
                return Response({"data": resp}, status=status.HTTP_200_OK)
            if contents:
                docs = handling_files(contents, file_extension, filename)
        else:
            logger.info(f'Unsupported file format, file name: {file.filename}')
            return Response({"error": f'Unsupported file format, file name: {file.filename}'},
                            status=status.HTTP_404_NOT_FOUND)
        # open_ai_key = getOpenAIKey(request)
        if 'docx' in file.name[-4:].lower():
            doc = Document(file)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            text_docx = '\n'.join(full_text)
            total_pages_ = num_tokens_from_string(text_docx, 'abc')
            total_pages_file = math.ceil(total_pages_ / 700)
        else:

            total_pages_file = calculate_page_number(file,contents)
        if total_pages_file == 0:
            return Response({"message": "Unsupported File"}, status=status.HTTP_404_NOT_FOUND)
        open_ai_key = is_user_able_to_query(request, 1, total_pages_file)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        summary_txt = generate_summary(docs, open_ai_key)  # replace
        try:
            index_name = os.getenv("DRAFTING_TEMPLATES_PINECONE_INDEX_NAME")
            test = Pinecone(api_key=api_key, environment=environment)
            index = test.Index(index_name)
            lang_pinecone.from_documents(docs, embed_fn, index_name=index_name)
        except Exception as ex:
            print(ex)
        # index_name = os.getenv("DRAFTING_TEMPLATES_PINECONE_INDEX_NAME")
        # pinecone.init(api_key=api_key, environment=environment)
        # index = pinecone.Index(index_name=index_name)
        # Pinecone.from_documents(docs, embed_fn_pinecone_draft, index_name=index_name)
        obj = Drafttemplates(title=str(filename), summary=str(summary_txt), community=True)
        obj.save()
        # conn, cursor = connect_to_postgres(HOST, PORT, DB_NAME, USER, PASSWORD)
        # data_to_insert = [
        #     (str(filename), str(summary_txt)),
        # ]
        # insert_query = """
        # INSERT INTO drafttemplates (title, summary) VALUES (%s, %s)
        # """
        # cursor.executemany(insert_query, data_to_insert)
        # conn.commit()
        return Response({"message": "Sucessfully uploaded the file and save into db", "data": resp},
                        status=status.HTTP_200_OK)
    except Exception as ex:
        logger.critical(f'Error while getDrafs: {ex}')
        return Response({"error": "Error while community"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('prompt', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                         # openapi.Parameter('paragraph', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                     ]
                     )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getContent(request):
    try:
        prompt = request.query_params.get('prompt')
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request, 1, 0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        prompt_content = generate_content(prompt, open_ai_key)
        if prompt_content is not None:
            return Response({"data": prompt_content}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Error while getting Content"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as ex:
        return Response({"error": "Error while getSuggestion"}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('prompt', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                         # openapi.Parameter('paragraph', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                     ]
                     )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def templateContent(request):
    prompt = request.query_params.get('prompt')
    try:
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request,1,0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        prompt_content = generate_template_content(prompt, open_ai_key)
        if prompt_content is not None:
            return Response({"response": prompt_content}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Error while getting Content"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as ex:
        return Response({"error": "Error while getSuggestion"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='POST', request_body=Suggestion)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def getHeadingsSuggestion(request):
    try:
        content = request.data.get("content")
        # temp_key = request.query_params.get('key')
        # source = get_object_link(temp_key)
        # suffix = temp_key.split(".")[-1]
        #
        # if suffix == "docx":
        #     loader = Docx2txtLoader(source)
        # elif suffix == "pdf":
        #     loader = PyMuPDFLoader(source)
        # else:
        #     return Response({"error": "Unsupported FIle format"}, status=status.HTTP_404_NOT_FOUND)
        #
        # txt = loader.load()

        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request,1,0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        heading_list = generate_headings(content, open_ai_key)
        heading_list = heading_list.replace("Missing", "").replace("Headings", "").split("\n")

        return Response(
            {"data": heading_list[-6:]}, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": "Error while getSuggestion"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='DELETE',
                     manual_parameters=[
                         openapi.Parameter('filename', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                         # openapi.Parameter('paragraph', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                     ]
                     )
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_community_bit(request):
    try:
        bucket_name = os.getenv("DRAFTING_BUCKET_NAME")
        region = 'us-east-1'
        filename = request.query_params.get('filename')

        test = Pinecone(api_key=api_key, environment=environment)

        index = test.Index('draftemplates')
        delete_response = index.delete(filter={'source': filename})
        session = boto3.session.Session()
        client = session.client('s3',
                                region_name=region,
                                endpoint_url=os.getenv("DRAFTING_ENDPOINT_S3_URL"),
                                aws_access_key_id=aws_key,
                                aws_secret_access_key=aws_secret_key,
                                config=Config(signature_version='s3v4')

                                )
        obj = Drafttemplates.objects.filter(title=filename)
        obj.delete()
        client.delete_object(Bucket=bucket_name, Key=filename)
        return Response({"message": "Successfully delete the file"}, status=status.HTTP_200_OK)

    except Exception as ex:
        return Response({"error": "Error while deleting file of pinecone"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='POST', request_body=SaveTemplate)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def saveTemplate(request):
    content = request.data.get("content")
    botid = request.data.get("botid")
    filename = request.data.get("filename")
    save_temp = Savedraftertemplate(botid=Userbot.objects.get(botid=botid), content=content, filename=filename,
                                    createddate=datetime.now())
    save_temp.save()
    return Response({"message": "Save Successfully"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_draft_userdata(request):
    bot_list = [v.pk for v in Userbot.objects.filter(userid=request.user.pk).filter(isarchive=False)]
    subquery = Savedraftertemplate.objects.annotate(
        rn=Window(
            expression=RowNumber(),
            partition_by=[F('botid')],
            order_by=[F('createddate').desc()]
        )
    ).filter(rn=1).filter(botid__in=bot_list)

    # subquery = Savedraftertemplate.objects.filter(botid__in=bot_list).order_by('createddate')

    new_list = list()
    for query_data in subquery:
        new_dict = {
            'id': query_data.pk,
            'botid': query_data.botid.pk,
            'filename': query_data.filename,
        }
        new_list.append(new_dict)
    new_list.reverse()
    return Response({'message': 'Uploading file User Bot ID', 'data': new_list}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET', manual_parameters=[
    openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)])
@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def get_draft_history(request):
    botid = request.query_params.get('botid')
    obj = Savedraftertemplate.objects.filter(botid=botid)
    return Response({'message': 'Drafter Data', 'data': obj[obj.count() - 1].content}, status=status.HTTP_200_OK)


@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def get_community_list(request):
    if request.user.role.pk == 5:
        obj = Drafttemplates.objects.filter(community=True)
        main_list = list()
        for data in obj:
            url_ = get_object_link(data.title)

            temp_dict = {
                'title': data.title,
                'url': url_
            }
            main_list.append(temp_dict)

        return Response({'message': 'Drafter Data', 'data': main_list}, status=status.HTTP_200_OK)
    return Response({'message': 'You dont have permission to delete this'}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('s3_key', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)])
@api_view(['POST'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def replaceMissingValues(request):
    try:
        s3_key = request.query_params.get('s3_key')
        s3_url = get_object_link(s3_key)
        # file_ext is the extension of the file e.g. docx, pdf
        file_ext = s3_key.split(".")[-1]

        if file_ext == "docx":
            loader = Docx2txtLoader(s3_url)
        elif file_ext == "pdf":
            loader = PyMuPDFLoader(s3_url)
        else:
            return Response({"error": "Unsupported FIle format"}, status=status.HTTP_404_NOT_FOUND)

        txt = loader.load()
        txt_list = txt[0].page_content.split(".")
        pattern = r"\[.*?\]"
        # start_time = time.time()
        index_list = []
        count = 1
        text = ""
        # updated_items_list = []
        for i in range(0, len(txt_list)):
            # Use re.findall() to find all occurrences of the pattern in the string
            matches = re.findall(pattern, txt_list[i])
            if len(matches):
                for match in matches:
                    txt_list[i] = txt_list[i].replace(match,
                                                      f"<mark style='background-color: green; color: white;'>{match}</mark>")
                text += f"{count}. pasha {txt_list[i]}. \n"
                index_list.append(i)
                count += 1
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request,1,0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        updated_text_list = missing_values(text, open_ai_key)
        for i, index in enumerate(index_list):
            txt_list[index] = updated_text_list[i]
        filled_text = ". ".join(txt_list)
        # print("time:"+ str(int(time.time()-start_time)))
        return Response({"response": filled_text}, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": "Error while replace missing values"}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(method='DELETE',request_body=QdrantList)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def del_collection(request):
    try:
        collection_name = request.data.get("qdrantCollection")
        for name in collection_name:
            generaed_response = delete_vectordb_using_qdrant(name)
        return Response({"message": "Collection deleted Successfully!",
                         }, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"message": f"Error occurred while deleting the collection: {str(ex)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@swagger_auto_schema(method='POST',
                     manual_parameters=[
                         openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),

                     ]
                     )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def insert_into_community(request):
    # community_bit = request.query_params.get('community_bit')
    # """Responsible to brings the uploaded file to the comunity.
    #    (It will upload to s3, summerize it and upload this summary to pinecone vectorstore)
    #
    # Args:
    #     user_id (int): Unique ID of the user
    #     file (file.object): uploaded file.
    #
    # Returns:
    #    json:  HTTP_200_OK if sucessfull otherwise HTTP_404_NOT_FOUND
    # """
    try:
        embed_fn_pinecone_draft = HuggingFaceEmbeddings(model_name="intfloat/e5-small-v2")
        file = request.FILES.get('file')
        user_id = request.user.pk
        contents = file.read()
        file_extension = f".{file.name.split('.')[-1]}"
        filename = f"{user_id}_{file.name}"
        put_file_to_s3(contents, os.getenv('DRAFTING_BUCKET_NAME'), filename)
        s3_url = get_object_link(filename)
        resp = {'key': filename, 'url': s3_url}
        supported_files = [".docx"]
        if file_extension in supported_files:
            # if community_bit == 'false':
            #     return Response({"data": resp}, status=status.HTTP_200_OK)
            if contents:
                docs = handling_files(contents, file_extension, filename)
        else:
            logger.info(f'Unsupported file format, file name: {file.filename}')
            return Response({"error": f'Unsupported file format, file name: {file.filename}'},
                            status=status.HTTP_404_NOT_FOUND)
        # open_ai_key = getOpenAIKey(request)
        if 'docx' in file.name[-4:].lower():
            doc = Document(file)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            text_docx = '\n'.join(full_text)
            total_pages_ = num_tokens_from_string(text_docx, 'abc')
            total_pages_file = math.ceil(total_pages_ / 700)
        else:
            total_pages_file = calculate_page_number(file,contents)
        if total_pages_file == 0:
            return Response({"message": "Unsupported File"}, status=status.HTTP_404_NOT_FOUND)
        open_ai_key = is_user_able_to_query(request, 1, total_pages_file)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        summary_txt = generate_summary(docs, open_ai_key)  # replace
        try:
            index_name = os.getenv("DRAFTING_TEMPLATES_PINECONE_INDEX_NAME")
            test = Pinecone(api_key=api_key, environment=environment)
            index = test.Index(index_name)
            lang_pinecone.from_documents(docs, embed_fn, index_name=index_name)
        except Exception as ex:
            print(ex)
        # index_name = os.getenv("DRAFTING_TEMPLATES_PINECONE_INDEX_NAME")
        # pinecone.init(api_key=api_key, environment=environment)
        # index = pinecone.Index(index_name=index_name)
        # Pinecone.from_documents(docs, embed_fn_pinecone_draft, index_name=index_name)
        obj = Drafttemplates(title=str(filename), summary=str(summary_txt), community=False)
        obj.save()
        # conn, cursor = connect_to_postgres(HOST, PORT, DB_NAME, USER, PASSWORD)
        # data_to_insert = [
        #     (str(filename), str(summary_txt)),
        # ]
        # insert_query = """
        # INSERT INTO drafttemplates (title, summary) VALUES (%s, %s)
        # """
        # cursor.executemany(insert_query, data_to_insert)
        # conn.commit()
        return Response({"message": "Sucessfully uploaded the file and save into db", "data": resp},
                        status=status.HTTP_200_OK)
    except Exception as ex:
        logger.critical(f'Error while getDrafs: {ex}')
        return Response({"error": "Error while community"}, status=status.HTTP_404_NOT_FOUND)

