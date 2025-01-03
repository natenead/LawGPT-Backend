from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes
from rest_framework import status
from .general_utils import *
from rest_framework.decorators import parser_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from pinecone import Pinecone
import os,math
from docx import Document
from rest_framework.parsers import MultiPartParser, FormParser
# import pinecone
from langchain.embeddings import HuggingFaceEmbeddings
from .db_utils import *
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from django.db import connection
from ..models import Mostlyusedfeature,Userstorage,Pineconeindexname
from ..utils import check_number_of_queries,create_index_pinecone_serverless,get_vectors_count,is_user_able_to_query,pinecone_index_info,calculate_page_number
embed_fn = HuggingFaceEmbeddings(model_name=os.getenv("model_name"))
embed_fn_qdrant = HuggingFaceEmbeddings(model_name=os.getenv("model_name_qdrant"))
from datetime import datetime
from langchain_pinecone import PineconeVectorStore
import PyPDF2
from io import BytesIO
import docx

from langchain_pinecone import PineconeVectorStore as lang_pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
vectordb = lang_pinecone(index= index, embedding=embed_fn, text_key="text")

# pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINCONE_ENV"))
# index = pinecone.Index(index_name=os.getenv("PINECONE_INDEX_NAME"))
# vectordb = Pinecone(index, embed_fn.embed_query, "text")
from qdrant_client import QdrantClient
from ..serializers import Suggestion
file_processor = IncomingFileProcessor(chunk_size=450)
from langchain.vectorstores import Qdrant
from .qdrant_ops import *
os.getenv('qdrant_url')


def background_task(doc_list, embed_fn,filename,index,botid):
    #
    try:
        PineconeVectorStore.from_documents(
            doc_list,
            embedding=embed_fn,
            index_name=index,
            namespace=filename + '__ind__'+ index
        )

    except Exception as e:
        return e

    obj = Uploadeddocumenthistory(botid=Userbot.objects.get(botid=botid),collectionname=filename + '__ind__'+ index,createddate=datetime.now())
    obj.save()
    # return qd
    # rant
    # db = file_processor.create_new_vectorstore(doc_list, embed_fn)
    # db.save_local("./Temp_VectorDB")


@swagger_auto_schema(method='POST',
                     manual_parameters=[
                         openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
                         openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)


                     ]
                     )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def generate_Vector_DB(request):


    botid = request.query_params.get('botid')
    file = request.FILES.get('file')

    contents = file.read()
    if 'docx' in file.name[-4:].lower():
        doc = Document(file)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        text_docx = '\n'.join(full_text)
        total_pages_ = num_tokens_from_string(text_docx,'abc')
        total_pages_file = math.ceil(total_pages_ / 700)
    else:
        total_pages_file = calculate_page_number(file,contents)
        if total_pages_file == 0:
            return Response({"message": "Unsupported File"}, status=status.HTTP_404_NOT_FOUND)
    # open_ai_key = getOpenAIKey(request)
    open_ai_key = is_user_able_to_query(request,1,total_pages_file)

    if open_ai_key == 0:
        return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
    try:
        Uploadeddocumenthistory.objects.get(botid=botid)
        return Response({'message': "Entered Bot ID Already Exists!"},
                        status=status.HTTP_400_BAD_REQUEST)
    except:
        pass
    num_query = check_number_of_queries(request)
    if num_query == 2:
        return Response({'message': "Please Subscribe", "data": []}, status=status.HTTP_402_PAYMENT_REQUIRED)
    elif num_query == 3:
        return Response({'message': "Please Enter Your Own API Key", "data": []}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    elif num_query == 1:
        pass

    try:



        file_extension = file.name[-4:].lower()
        original_filename = file.name

        doc_list = handling_files(contents, file_extension, original_filename)
        if not doc_list:
            return Response({"message": "File Formatting Issue, Please Change the file"}, status=status.HTTP_400_BAD_REQUEST)
        # open_ai_key = getOpenAIKey(request)
        # if open_ai_key == 0:
        #     return Response({"message": "Your API key is invalid"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        response = summarize(doc_list,open_ai_key)
        obj = Uploadeddocumentsummary(botid=Userbot.objects.get(botid=botid),summary = response)
        obj.save()

        # background_thread = threading.Thread(target=background_task, args=(doc_list, embed_fn))
        # background_thread.start()
        #
        # background_thread.join()
        date_ = str(datetime.now()).split(' ')[0] + str(datetime.now()).split(' ')[1].replace(":", '').split('.')[0]
        cl_name = original_filename.split('.')[0] + date_ + '.' + original_filename.split('.')[1]
        if request.user.role == 2:
            pinecone_index_data = Pineconeindexname.objects.filter(isfree=True)
        else:
            pinecone_index_data = Pineconeindexname.objects.filter(isfree=False).filter(isfull=False)
        index_name = pinecone_index_data[0].index_name
        try:
            if pinecone_index_info(index_name):
                background_task(doc_list, embed_fn,cl_name,index_name,botid)
            else:
                new_index_name = str(index_name.split('_')[0] +int(index_name.split('_')[1]) + 1)
                if create_index_pinecone_serverless(new_index_name):
                    pine_obj = Pineconeindexname(index_name = new_index_name,isfull=False,isfree=False,datetime=datetime.now())
                    pine_obj.save()
        except Exception as ex:
            return Response({"message": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

        filesize = file.size / 1000000000
        get_vectors_count(request,filesize)
        mostly_used = Mostlyusedfeature.objects.get(featureid=4)
        count = mostly_used.count
        count += 1
        mostly_used.count = count
        mostly_used.save()

        return Response({"message": "DB Generated Successfully!",'data':original_filename}, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"message": str(ex)}, status=status.HTTP_400_BAD_REQUEST)



#
# @swagger_auto_schema(method='GET',
#                      manual_parameters=[
#                          openapi.Parameter('query', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True), ]
#                      )
@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
                     ]
                     )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def summarise_the_uploaded_document(request):
    try:
        # file = request.FILES.get('file')
        # contents = file.read()

        botid = request.query_params.get('botid')
        #
        # file_extension = file.name[-4:].lower()
        # original_filename = file.name
        #
        # doc_list = handling_files(contents, file_extension, original_filename)
        # response = summarize(doc_list)
        summary_data = Uploadeddocumentsummary.objects.get(botid=botid)
        response = summary_data.summary

        if response:
            return Response({"message": "Response Generated Successfully!", "Response": response},
                                status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed!!"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as ex:
        return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True) ]
                     )
@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def extract_contract_clauses(request):
    try:
        botid = request.query_params.get('botid')
        uploaded_data = Uploadeddocumenthistory.objects.get(botid = botid)
        db = load_local_vectordb_using_qdrant(uploaded_data.collectionname,embed_fn)
        if not db:
            return Response({"message": "Your Document is deleted."}, status=status.HTTP_400_BAD_REQUEST)
        # db = file_processor.load_local_vectordb_using_faiss("./Temp_VectorDB", embed_fn)
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request, 1, 0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        response = semantic_search_on_contract_clauses(db,open_ai_key)

        return Response({"message": "Contract Clauses Extracted Successfully!", "Contract_Clauses": response}, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
@swagger_auto_schema(method='GET',manual_parameters=[openapi.Parameter('query', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                            openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)
                                                                              ])

@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def simple_chatbot_for_uploaded_document(request):
    try:
        query = request.query_params.get('query')
        botid = request.query_params.get('botid')
        uploaded_data = Uploadeddocumenthistory.objects.get(botid=botid)
        db = load_local_vectordb_using_qdrant(uploaded_data.collectionname, embed_fn)
        if not db:
            return Response({"message": "Your Document is deleted."}, status=status.HTTP_400_BAD_REQUEST)
        # db = file_processor.load_local_vectordb_using_faiss("./Temp_VectorDB", embed_fn)
        # open_ai_key = getOpenAIKey(request)
        open_ai_key = is_user_able_to_query(request, 1, 0)
        if open_ai_key == 0:
            return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)

        response_with_source = search_caselaw(query, db,open_ai_key)
        response = response_with_source
        if "StatusCode:404" in response:
            return Response({"message": "Response Generated Successfully!",
                                         "Response": "The query is irrelevant to the document. Kindly ask relevant query."
                                         }, status=status.HTTP_200_OK)
        else:
            obj = Uploadeddocumentqueries(botid=Userbot.objects.get(botid=botid), question=query, answer=response,
                                          createddate=datetime.now())
            obj.save()
            return Response({"message": "Response Generated Successfully!", "Response": response},
                                status=status.HTTP_200_OK)

        # retriever = db.as_retriever(search_type='similarity', search_kwargs={"k":5})
        # llm_conv = OpenAI(temperature=0.2,openai_api_key= open_ai_key)
        # memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True)
        # qa_conv = ConversationalRetrievalChain.from_llm(llm_conv, retriever, memory=memory)

        # response = semantic_search_conversation(query, qa_conv)

        # return Response({"message": "Response Generated Successfully!", "Response": response}, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='GET',manual_parameters=[openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)])
@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def get_uploaded_doc_data(request):
    main_list = list()
    try:
        uploaded_data = Uploadeddocumentqueries.objects.filter(botid = request.query_params.get('botid'))
    except:
        return Response({"message": "Please Enter a valid bot id",}, status=status.HTTP_400_BAD_REQUEST)
    for data in uploaded_data:
        new_dict = {
        'content':data.question,
        'type':'question'
        }
        new_dict1 = {
            'content':data.answer,
            'type': 'answer'
        }

        main_list.append(new_dict)
        main_list.append(new_dict1)
    return Response({"message": "Uploaded File History!", "data": main_list}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_bot_uploded_doc(request):
    main_list = list()
    bot_list = [v.pk for v in Userbot.objects.filter(userid=request.user.pk).filter(isarchive=False)]
    document_data = Uploadeddocumenthistory.objects.filter(botid__in=bot_list)
    for obj in document_data:
        new_dict = {
            'botid':obj.botid_id,
            'filename':obj.collectionname.split('.')[0]
        }
        main_list.append(new_dict)
    main_list.reverse()

    return Response({"message": "Uploaded File Bot id", "data": main_list}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET',manual_parameters=[openapi.Parameter('case_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),])

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_case_id(request):
    case_id = request.query_params.get("case_id")
    cursor = connection.cursor()
    # query = f'''
    #     select c.court_name,m.head_matter,m.name,m.decision_date,o.opinion_type,o.opinion_text from public.main as m join public.opinion as o on o.case_id = m.case_id join public.court as c
    #     on m.case_id = c.case_id where m.case_id = 10
    #     '''
    query = f'''
            select c.court_name,m.head_matter,m.name,m.decision_date,o.opinion_type,o.opinion_text from public.main as m join public.opinion as o on o.case_id = m.case_id join public.court as c 
            on m.case_id = c.case_id where m.case_id = {case_id}
        '''
    cursor.execute(query)
    row = cursor.fetchone()
    new_dict = {
        'title':row[0],
        'data':"\t".join(row[1:])
    }
    return Response({"message": "Citation Data", "data": new_dict}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='POST',request_body=Suggestion)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def getSummary(request):
    text = request.data.get("content")
    try:
        summary_txt = search_summary(text)

        return Response({"response":summary_txt},status=status.HTTP_200_OK)
    except Exception as ex:
        return Response( {"error": "Error while summary_txt"},status=status.HTTP_404_NOT_FOUND)