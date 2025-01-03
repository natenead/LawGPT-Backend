from .models import (
    Role,
    Userqueryrecord,
    Userapikeys,
    AdminUser,
    Userstorage, UserDetails, Userfreetrail,
    Userquerydocrecord
)
from datetime import datetime
from datetime import date
from datetime import timedelta
from cryptography.fernet import Fernet
import os
from qdrant_client import QdrantClient
import json
import openai
from datetime import timezone
from dotenv import load_dotenv

from pinecone import Pinecone, ServerlessSpec

load_dotenv()


def user_role(role):
    role = Role.objects.get(role_id=role)
    name = role.role_name
    return name


def check_number_of_queries(request):
    try:
        user_trail = Userfreetrail.objects.get(user=request.user.pk)
        if (user_trail.expired_date - datetime.now(timezone.utc)).days > 0:
            return 2
        else:
            api_key_ = Userapikeys.objects.filter(userid=request.user.pk).filter(isdelete=False)
            if api_key_:
                return 1
            return 3
    except:
        if request.user.role.pk == 2:
            if (datetime.now(timezone.utc) - request.user.created_date).days > 30:
                return 2
        if request.user.role.pk == 4:
            if (datetime.now(timezone.utc) - request.user.created_date).days > 1096:
                return 2

        if request.user.role_id == 2 or request.user.role_id == 4:
            user_data = Userqueryrecord.objects.filter(userid=request.user.pk)
            if user_data.count() < 25:
                obj = Userqueryrecord(userid=request.user, createddate=datetime.now())
                obj.save()
                return 1
            else:
                api_key_ = Userapikeys.objects.filter(userid=request.user.pk).filter(isdelete=False)
                if api_key_:
                    return 1
                return 3
        else:
            return 1


def hashedAPIKey(key):
    cipher_suite = Fernet(b'2F2nfZe4E9wSfmEWgFtD6JheR6Qi7ijaCowPEFRwj6E=')
    # print(key)
    # String to be encrypted
    original_string = key

    # Encryption
    encrypted_bytes = cipher_suite.encrypt(original_string.encode())
    return encrypted_bytes


# def getOpenAIKey(request):
#     api_key = 0
#     if request.user.role.pk == 1:
#         api_key_ = Userapikeys.objects.filter(userid=request.user.pk).filter(isdelete=False)
#         if api_key_:
#             api_key = api_key_[0].apikey
#     elif request.user.role.pk == 3:
#         try:
#             api_key_ = Userapikeys.objects.filter(userid=AdminUser.present.get(userid=request.user.pk).adminid_id).filter(
#                 isdelete=False)
#
#         except:
#             return api_key
#         if api_key_:
#             api_key = api_key_[0].apikey
#     else:
#         api_key_ = Userapikeys.objects.filter(userid=6).filter(isdelete=False)
#         if api_key_:
#             api_key = api_key_[0].apikey
#     return api_key
def check_openai_api_key(api_key):
    return True
    openai.api_key = api_key
    try:
        openai.Model.list()
    except openai.error.AuthenticationError as e:
        return False
    else:
        return True


def is_user_able_to_query(request, query, doc):
    if request.user.role.pk == 3 or request.user.role.pk == 1:
        try:
            user_query = Userquerydocrecord.objects.get(user=request.user.pk)
            if user_query.document_number - doc < 0:
                return 0
            if user_query.query_number > 0:
                user_query.query_number = user_query.query_number - query
                user_query.document_number = user_query.document_number - doc
                user_query.save()
                oepnai_api_key = os.getenv('OPENAI_API_KEY')
                return oepnai_api_key
            else:
                return 0

        except:
            return 0
    else:
        return os.getenv('OPENAI_API_KEY')


def getOpenAIKey(request):
    api_key = 0
    api_key_ = Userapikeys.objects.filter(userid=request.user.pk).filter(isdelete=False)
    if api_key_:
        api_key = api_key_[0].apikey
        is_valid = check_openai_api_key(api_key)
        if not is_valid:
            api_key = 0
        return api_key
    if request.user.role.pk == 3:
        try:
            api_key_ = Userapikeys.objects.filter(
                userid=AdminUser.present.get(userid=request.user.pk).adminid_id).filter(
                isdelete=False)

        except:
            return api_key
        if api_key_:
            api_key = api_key_[0].apikey
    else:
        api_key_ = Userapikeys.objects.filter(userid=6).filter(isdelete=False)
        if api_key_:
            api_key = api_key_[0].apikey
    is_valid = check_openai_api_key(api_key)

    if not is_valid:
        api_key = 0

    return api_key


def get_vectors_count(request, count):
    return True

    # qdrant_client = QdrantClient(
    #     url=os.getenv('qdrant_url'),
    #     prefer_grpc=True,
    #     api_key=os.getenv('api_key'),
    # )
    # collection_status = qdrant_client.get_collection(collection_name=name)
    # count = collection_status.vectors_count
    new_count = count
    if request.user.role.pk == 1:
        try:
            old_storage = Userstorage.objects.get(userid=request.user.pk).storage
            new_count = count + old_storage
            old_storage.storage = new_count
            old_storage.save()
        except:
            user_storage = Userstorage(userid=request.user, storage=new_count, createddate=datetime.now(),
                                       isdelete=False)
            user_storage.save()
        '''
            If condition here !!!
        
        '''

    elif request.user.role.pk == 3:
        admin_id = AdminUser.present.get(userid=request.user.pk).adminid
        try:
            old_storage = Userstorage.objects.get(userid=admin_id.pk).storage
            new_count = count + old_storage
            old_storage.storage = new_count
            old_storage.save()
        except:
            try:
                user_storage = Userstorage(userid=UserDetails.objects.get(id=admin_id), storage=new_count,
                                           createddate=datetime.now(),
                                           isdelete=False)
                user_storage.save()
            except:
                raise
        '''
        
            place if condition here
        
        '''
    else:
        try:
            old_storage = Userstorage.objects.get(userid=request.user.pk).storage
            new_count = count + old_storage
            old_storage.storage = new_count
            old_storage.save()
        except:
            try:
                user_storage = Userstorage(userid=request.user.pk, storage=new_count, createddate=datetime.now(),
                                           isdelete=False)
                user_storage.save()
            except:
                raise


def get_file_data(file):
    with open(file, "r") as f:
        return json.load(f)


def pinecone_index_info(index_name):
    try:
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index_stats = pc.Index(index_name)
        namespaces_info = index_stats.describe_index_stats()
        no_of_namespaces = len(namespaces_info["namespaces"])
        if no_of_namespaces < 10000:
            return True
        return False
        # return no_of_namespaces
    except Exception as e:
        raise {"error": e}


def create_index_pinecone_serverless(index):
    try:
        serverless_spec = ServerlessSpec(cloud="aws", region="us-west-2")
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        check = pc.list_indexes().names()
        if index not in check:
            pc.create_index(name=index, metric="cosine", spec=serverless_spec, dimension=384)
            return True
        return False
    except Exception as ex:
        return str(ex)


def calculate_page_number(file,contents) -> int:
    file_extension = file.name[-4:].lower()
    if 'pdf' in file_extension:
        import PyPDF2
        from io import BytesIO

        # contents = file.read()
        pdf_file = BytesIO(contents)

        reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(reader.pages)
        return total_pages
    elif 'docx' in file_extension:
        return 1
        # from PyPDF2 import PdfReader
        # from docx2pdf import convert
        # temp_docx_filename = f"temp_{file.name}"
        # temp_pdf_filename = f"temp_{file.name.replace('.docx', '.pdf')}"
        #
        # with open(temp_docx_filename, "wb") as f:
        #     f.write(contents)
        #
        # try:
        #     # Convert DOCX to PDF
        #     convert(temp_docx_filename, temp_pdf_filename)
        #
        #     # Open the PDF file and count the pages
        #     with open(temp_pdf_filename, "rb") as pdf_file:
        #         pdf_reader = PdfReader(pdf_file)
        #         page_count = len(pdf_reader.pages)
        #
        # except Exception as e:
        #     return 0
        # finally:
        #     # Clean up by removing the temporary files
        #     os.remove(temp_docx_filename)
        #     if os.path.exists(temp_pdf_filename):
        #         os.remove(temp_pdf_filename)
        # return page_count
    else:
        return 0
