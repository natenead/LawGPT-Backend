from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from .general_utils import *
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from langchain.embeddings import HuggingFaceEmbeddings
import os,json
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from .qdrant_ops import *
from ..utils import check_number_of_queries
from django.db.models import Window
from django.db.models.functions import RowNumber
from django.db.models import F
embed_fn = HuggingFaceEmbeddings(model_name=os.getenv("model_name"))
from ..serializers import upload_doc
import threading
import time
import random
import string
from ..models import Userbot,Uploadedfilescorehistory,Pineconeindexname
load_dotenv()


qdrant_url  = os.getenv('qdrant_url')
qdrant_api_key  = os.getenv('api_key')

def create_vector_db_for_files(request,files_info,res,user_id):
    for f_info in files_info:
        path=f_info["file_path"]
        filename=f_info["filename"]
        file_extension=filename.split(".")[-1]
        all_texts = load_data(path, file_extension, filename)
        if not all_texts:
            return False
        curr_date = str(datetime.now())
        vec_folder_path = "".join(random.choices(string.ascii_letters, k=4)
                                ) + curr_date.split('.')[0].replace(':', '-').replace(" ", 'T')
        vec_folder_path = Path.cwd() / Path('vectordb') / Path(vec_folder_path)
        # embed_fn=get_embedding_funtion()
        embed_fn = HuggingFaceEmbeddings(model_name=os.getenv("model_name"))
        collection_name=str(filename.split('.')[0])+"_"+str(user_id)+"_"+"Doc_Review_"+curr_date.split('.')[0].replace(':', '-').replace(" ", '_')
        if request.user.role == 2:
            pinecone_index_data = Pineconeindexname.objects.filter(isfree=True)
        else:
            pinecone_index_data = Pineconeindexname.objects.filter(isfree=False).filter(isfull=False)
        index_name = pinecone_index_data[0].index_name
        create_new_vectorstore_qdrant(all_texts,embed_fn,collection_name,index_name)
        # filesize = request.FILES.getlist('files')[0].size/1000000000
        filesize = 0.028
        get_vectors_count(request, filesize)
        logger.info('VectorDB stored successfully on filesystem')
        res.append({
            "filename" : filename,
            "vecdb_path" : vec_folder_path,
            "collection_name":collection_name + '__ind__' + index_name,
        })
        # print(res)
    return res


@swagger_auto_schema(
        method='post',
        manual_parameters=[
            openapi.Parameter('files', in_=openapi.IN_FORM, type=openapi.TYPE_ARRAY,items=openapi.Items(type=openapi.TYPE_FILE), required=True,
                              description='List of files to upload'),
        ],
        operation_description="Upload multiple files",
        responses={200: "Files uploaded successfully"},
    )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])

def convertFilesIntoVectorDB(request):
    # if not check_number_of_queries(request):
    #     return Response({'message': "You Don't have permission to query", "data": []}, status=status.HTTP_402_PAYMENT_REQUIRED)
    num_query = check_number_of_queries(request)
    if num_query == 2:
        return Response({'message': "Please Subscribe", "data": []}, status=status.HTTP_402_PAYMENT_REQUIRED)
    elif num_query == 3:
        return Response({'message': "Please Enter Your Own API Key", "data": []},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    elif num_query == 1:
        pass
    try:
        upload_folder = "uploaded_files"
        files = request.FILES.getlist('files')
        os.makedirs(upload_folder, exist_ok=True)
        files_info = []
        for file in files:
            file_path = os.path.join(upload_folder, file.name)
            contents = file.read()
            file_extension = file.name[-4:].lower()
            file_extension = file_extension.replace(".", "")
            supported_files = ["pdf", "docx"]
            if file_extension in supported_files:
                if contents:
                    _file = {
                        "filename": file.name,
                        "file_path": file_path,
                    }
                    files_info.append(_file)
                    with open(file_path, "wb") as f:
                        f.write(contents)
                    logger.info(f'File: {file.name} upload successful')
            else:
                logger.info(f'Unsupported file format, file name: {file.name}')
                return Response({"error": f'Unsupported file format, file name: {file.name}'},
                                    status=status.HTTP_400_BAD_REQUEST)
    except Exception as ex:
        logger.critical(f'File upload Unsuccessful: {str(ex)}')
        return Response({"error": f'File upload Unsuccessful:'}, status=status.HTTP_404_NOT_FOUND)

    try:
        t1 = time.time()
        no_of_threads = 4  # No of threads by default it is one but you can increase it based on your requirements.
        no_of_files = len(files_info)
        no_of_files_list = []
        no_of_files_list = get_number_of_files_based_on_threads(no_of_threads, no_of_files, no_of_files_list)
        no_of_files_list = [i for i in no_of_files_list if i != 0]  # Remove zeros from list as it is not neede
        res = []
        thread_list = []
        i = 0
        res = create_vector_db_for_files(request,files_info, res, request.user.pk)
        if res is False:
            return Response({"error": "File doesnot contain any text or maybe corrupted"},
                            status=status.HTTP_404_NOT_FOUND)
        # for thread_number in range(len(no_of_files_list)):
        #     res = create_vector_db_for_files(files_info[i:no_of_files_list[thread_number] + i], res, request.user.pk)
            # thread = threading.Thread(target=create_vector_db_for_files,
            #                           args=(files_info[i:no_of_files_list[thread_number] + i], res, request.user.pk))
            # thread_list.append(thread)
            # logger.info("Successfully initialize the threads")
            # print(f"[{i}:{no_of_files_list[thread_number] + i}]")
            # i = no_of_files_list[thread_number] + i
        # for j in thread_list:
        #     j.start()
        #     logger.info("Successfully start the threads")
        #     time.sleep(2)
        # for t in thread_list:
        #     t.join()
        #     logger.info("Successfully wait for the threads")
        collection_list = []
        file_list = []
        if len(res) == 0:
            return Response({"error": "File doesnot contain any text or maybe corrupted"},
                            status=status.HTTP_404_NOT_FOUND)
        for r in res:
            collection_list.append(r["collection_name"])
            file_list.append(r["filename"])
        t2 = time.time()
        print("time taken is:", t2 - t1, "seconds")
        if len(collection_list) > 0:
            # logger.info(f'Sucessfully created vectordb of all files')
            return Response({"collection_list": collection_list, "file_list": file_list},
                                status=status.HTTP_200_OK)
        else:
            # logger.critical(f'Error while creating the vectordb of the files: {ex}')
            return Response({"error": "Error while creating the vectordb of the files"},
                                status=status.HTTP_404_NOT_FOUND)
    except Exception as ex:
        logger.critical(f'Error while creating the vectordb of the files: {ex}')
        return Response({"error": "Error while creating the vectordb of the files"},
                            status=status.HTTP_404_NOT_FOUND)



        # try:
    #     t1 = time.time()
    #     # files_info=resp["files_info"]
    #     # user_id=resp["user_id"]
    #     no_of_threads = 1
    #     no_of_files = len(files_info)
    #     no_of_files_list = []
    #     no_of_files_list = get_number_of_files_based_on_threads(no_of_threads, no_of_files, no_of_files_list)
    #     no_of_files_list = [i for i in no_of_files_list if i != 0]  # Remove zeros from list
    #     res = []
    #     thread_list = []
    #     i = 0
    #     for thread_number in range(len(no_of_files_list)):
    #         thread = threading.Thread(target=create_vector_db_for_files,
    #                                   args=(files_info[i:no_of_files_list[thread_number] + i], res, request.user.pk))
    #         thread_list.append(thread)
    #         logger.info("Successfully initialize the threads")
    #         # print(f"[{i}:{no_of_files_list[thread_number] + i}]")
    #         i = no_of_files_list[thread_number] + i
    #     for j in thread_list:
    #         j.start()
    #         logger.info("Successfully start the threads")
    #         time.sleep(2)
    #     # for t in thread_list:
    #     #     t.join()
    #     #     logger.info("Successfully wait for the threads")
    #     collection_list = []
    #     file_list = []
    #     for r in res:
    #         collection_list.append(r["collection_name"])
    #         file_list.append(r["filename"])
    #     t2 = time.time()
    #     # print("time taken is:", t2 - t1, "seconds")
    #     if len(collection_list) > 0:
    #         logger.info(f'Sucessfully created vectordb of all files')
    #         return Response({"collection_list": collection_list, "file_list": file_list},status=status.HTTP_200_OK)
    #     else:
    #         logger.critical(f'Error while creating the vectordb of the files:')
    #         return Response({"error": "Error while creating the vectordb of the files"},status=status.HTTP_404_NOT_FOUND)
    #
    # except Exception as ex:
    #     logger.critical(f'Error while creating the vectordb of the files: {ex}')
    #     return Response({"error": "Error while creating the vectordb of the files"},status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', request_body=upload_doc)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def searchAndGetScoresFromVectorDBs(request):
    # if not check_number_of_queries(request):
    #     return Response({'message': "You Don't have permission to query", "data": []}, status=status.HTTP_402_PAYMENT_REQUIRED)
    num_query = check_number_of_queries(request)
    if num_query == 2:
        return Response({'message': "Please Subscribe", "data": []}, status=status.HTTP_402_PAYMENT_REQUIRED)
    elif num_query == 3:
        return Response({'message': "Please Enter Your Own API Key", "data": []},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    elif num_query == 1:
        pass
    try:
        try:
            bot_data = Userbot.objects.get(botid = request.data['botid'])
        except:
            return Response({"message": "Please Enter a valid bot id"},status=status.HTTP_400_BAD_REQUEST)
        collection_list = request.data.get('collections')
        files = request.data.get('files')
        questions = request.data.get('questions')
        questions = [v for v in questions if len(v) > 0 ]


        response = []
        question_with_score = {}

        key = 1
        for filename, colection in zip(files, collection_list):
            try:
                vectordb = load_local_vectordb_using_qdrant(vectordb_folder_path=colection,embed_fn=embed_fn)
                if not vectordb:
                    return Response({"message": "Your Document is deleted."}, status=status.HTTP_400_BAD_REQUEST)
                logger.info("VectorDB Loaded Successfully")
            except Exception as ex:
                logger.critical(f'Failure: {str(ex)}')
                return Response({"message": "VectorDB Loaded Unsuccessful"},
                                    status=status.HTTP_400_BAD_REQUEST)
            dic = {
                "key": key,
                "name": filename,

            }
            key = key + 1
            # dic1=dic.copy()
            i = 1
            for question in questions:
                try:
                    found_docs = vectordb.similarity_search_with_score(question)
                    document, score = found_docs[0]
                    # print(document.page_content)
                    # print(f"\nScore: {score}")
                    # if score>0 and score<0.5:
                    if score < 0.3:
                        quality = "No"
                    elif score > 0.3 and score < 0.35:
                        quality = "Insuffcient"
                    else:
                        quality = "Yes it does"
                    dic[str(question)] = quality
                    # dic["question" + str(i)] = quality
                    i = i + 1
                    logger.info("Successfully get the similarity_search_with_score")
                except Exception as ex:
                    logger.critical(f'Failure: {str(ex)}')
                    return Response({"message": "similarity_search_with_score Unsuccessful"},
                                        status=status.HTTP_400_BAD_REQUEST)
            response.append(dic)
        try:
            obj = Uploadedfilescorehistory(botid=bot_data, response=json.dumps(response),VDName=collection_list,Questions=questions,FileName=files,createddate=datetime.now())
            obj.save()
        except Exception as e:
            return Response({"message": f"Failed {str(e)}", "response": []},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({"response": response}, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.critical(f'Error while search_and_get_scores_from_vector_dbs: {ex}')
        return Response({"error": "Error while search_and_get_scores_from_vector_dbs"},
                            status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_score_botid(request):
    bot_list = [v.pk for v in Userbot.objects.filter(userid=request.user.pk).filter(isarchive=False)]
    subquery = Uploadedfilescorehistory.objects.annotate(
        rn=Window(
            expression=RowNumber(),
            partition_by=[F('botid')],
            order_by=[F('createddate').desc()]
        )
    ).filter(rn=1).filter(botid__in=bot_list)
    new_list = list()
    for query_data in subquery:
        new_dict = {
            'id':query_data.pk,
            'filename':query_data.FileName,
            'botid':query_data.botid.pk
        }
        new_list.append(new_dict)
    new_list.reverse()
    return Response({'message':'Uploading file User Bot ID','data':new_list},status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET',manual_parameters=[openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)])
@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def get_score_history(request):
    main_list = list()
    document_hist = Uploadedfilescorehistory.objects.filter(botid = request.query_params.get('botid'))
    for obj in document_hist:
        new_dict = {
            'documents':obj.FileName,
            'type':'document question',
        }
        new_dict1 = {
            'response': obj.response,
            'type': 'document answer',
        }
        main_list.append(new_dict)
        main_list.append(new_dict1)
    return Response({'message': 'Uploaded File History', 'data': main_list}, status=status.HTTP_200_OK)
