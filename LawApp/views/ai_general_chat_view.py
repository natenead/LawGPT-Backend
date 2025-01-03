from rest_framework.decorators import api_view, permission_classes, authentication_classes
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from langchain_core.messages import AIMessage, HumanMessage, get_buffer_string
# from langchain.vectorstores import Pinecone
from ..utils import check_number_of_queries,is_user_able_to_query
from ..models import Generalchathistory,Userbot
from rest_framework.response import Response
from rest_framework import status
from .general_utils import *
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from pinecone import Pinecone
import os
from dotenv import load_dotenv


from django.db.models.functions import RowNumber
from django.db.models import F
from django.db.models import Window
embed_fn = HuggingFaceEmbeddings(model_name=os.getenv("model_name"))
from langchain.llms import OpenAI
from datetime import datetime, timezone, timedelta
from django.db import connection
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import format_document
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from langchain_pinecone import PineconeVectorStore as lang_pinecone

load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
vectordb = lang_pinecone(index= index, embedding=embed_fn, text_key="text")

# pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINCONE_ENV"))
# index = pinecone.Index(index_name=os.getenv("PINECONE_INDEX_NAME"))
# vectordb = Pinecone(index, embed_fn.embed_query, "text")
retriever = vectordb.as_retriever(search_type='similarity', search_kwargs={"k": 5})
llm_conv = OpenAI(temperature=0.2)
memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True)
qa_conv = ConversationalRetrievalChain.from_llm(llm_conv, retriever, memory=memory)
gpt_model_name = os.getenv('gpt_model_name')


@swagger_auto_schema(method='GET',manual_parameters=[openapi.Parameter('userQuery', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
                                                    openapi.Parameter('botId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
                                                    openapi.Parameter('userId', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
                                                                                 ])
@api_view(['GET'])
# @authentication_classes([])
@permission_classes([IsAuthenticated])
def simple_chatbot(request):
    cursor = connection.cursor()
    botId = request.query_params.get('botId')
    userId = request.query_params.get('userId')
    userQuery = request.query_params.get('userQuery')
    # open_ai_key = getOpenAIKey(request)
    open_ai_key = is_user_able_to_query(request, 1, 0)
    if open_ai_key == 0:
        return Response({"message": "Kindly buy a package"}, status=status.HTTP_402_PAYMENT_REQUIRED)
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
            userbot = Userbot.objects.get(botid=botId)
        except Exception as e:
            logger.critical(f"Error: userbot error: {e}")
            return Response({"error": "Please Enter a valid bot"}, status=status.HTTP_400_BAD_REQUEST)

        question_list = []
        answer_list = []
        history_list = []
        check_chat_record = f"""
                            SELECT "Question","Answer" FROM "GeneralChatHistory" WHERE "UserId"={int(userId)} AND "BotId"={int(botId)}  ORDER BY "CreatedDate" ASC LIMIT  5
                        """
        cursor.execute(check_chat_record)
        row = cursor.fetchall()

        if len(row):
            for i in row:
                question = i[0]
                answer = i[1]
                question_list.append(question)
                answer_list.append(answer)
                history_list.append(HumanMessage(question))
                history_list.append(AIMessage(answer))
        logger.info("Successfully Load the chat history from the database")
    except Exception as ex:
        logger.critical(f" Unable to read Data from Database: {str(ex)}")
        return Response({"error": "Database Connection Error."},
                            status=status.HTTP_400_BAD_REQUEST)

    # try:

    #     memory_var = ConversationBufferWindowMemory(memory_key="chat_history", human_prefix='Question',
    #                                                 ai_prefix='Answer', return_messages=True, k=5)
    #     for question, answer in zip(question_list, answer_list):
    #         memory_var.save_context({"Question": question}, {"Answer": answer})
    #     logger.info("Successfully load the memory var")
    # except Exception as e:
    #     logger.critical(f"Error: Load the memory var: str({e})")
    #     return Response({"error": "OpenAI Not Available."}, status=status.HTTP_400_BAD_REQUEST)

    try:

        # prompt_template = """Answer the following question truthfully and provide a response based on the given context, chat history, and your knowledge. If no context and chat history is available, then you must give a detailed answer of more than 500 words from your knowledge without using chatty words but answer must not only in one paragraph.
        #
        #   Context:
        #   {context}
        #
        #   Chat History:
        #   {chat_history}
        #
        #   Question: {question}
        #
        #   Detailed Answer in English:  """
        #
        # CONDENSEprompt = PromptTemplate(
        #     template=prompt_template, input_variables=["context", "chat_history", "question"],
        #     validate_template=False)
        # conv_chain = ConversationalRetrievalChain.from_llm(
        #     llm=ChatOpenAI(model='gpt-3.5-turbo-16k'), retriever=vectordb.as_retriever(search_kwargs={"k": 50}),
        #     memory=memory_var, return_source_documents=False,
        #     combine_docs_chain_kwargs={'prompt': CONDENSEprompt})
        # logger.info("success conv_chain")
        # try:
        #     # logger.info(f'UserQuery: {userQuery}')
        #     # logger.info(f'conv_chain: {conv_chain}')
        #
        #     generated_response = conv_chain(userQuery)
        #     logger.info(f"success generate the response: {generated_response}")
        # except Exception as e:
        #     logger.critical(f"error generate the response {e}")
        # generated_response = generated_response['answer']
        # logger.info("success: replace response")

        num_chunks = 50
        _template = """Given the following conversation and a follow up question, rephrase the follow up question to 
        be a standalone question, in its original language.

        Chat History:
        {chat_history}
        Follow Up Input: {question}
        Standalone question: """


        CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)
        template = """Answer the following question truthfully and provide a response based on the given context, 
        chat history, and your knowledge. If no context and chat history is available, then you must give a detailed 
        answer of more than 500 words from your knowledge without using chatty words but answer must not only in one 
        paragraph.
        **Instructions for response:**
        (((
        1-response must not be in one long paragraph.
        2-Organize the response with clear separation between sections and multiple new lines between paragraphs for readability.
        )))

        Context:
        {context}

        Question: {question}

        Detailed Answer in English:
        """
        ANSWER_PROMPT = ChatPromptTemplate.from_template(template)
        DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")
        retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": num_chunks})
        llm = ChatOpenAI(model =gpt_model_name,openai_api_key= open_ai_key)

        def _combine_documents(
                docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
        ):
            doc_strings = [format_document(doc, document_prompt) for doc in docs]
            return document_separator.join(doc_strings)

        _inputs = RunnableParallel(
            standalone_question=RunnablePassthrough.assign(
                chat_history=lambda x: get_buffer_string(x["chat_history"])
            )
                                | CONDENSE_QUESTION_PROMPT
                                | llm
                                | StrOutputParser(),
        )
        if not history_list:
            setup_and_retrieval = RunnableParallel(
                {"context": retriever, "question": RunnablePassthrough()}
            )
            output_parser = StrOutputParser()
            context = setup_and_retrieval.invoke(userQuery)
            docs = _combine_documents(context['context'])
            doc_dict = {'context': docs, "question":userQuery}
            answer_prompt = ANSWER_PROMPT.invoke(doc_dict)
            final_response = llm.invoke(answer_prompt)
            generated_response=final_response.content
            # response = output_parser.invoke(final_response)
            logger.info("chat generated")
            # return response
        else:
            rephrase_question = _inputs.invoke({
                "question": userQuery,
                "chat_history": history_list,
            })
            setup_and_retrieval = RunnableParallel(
                {"context": retriever, "question": RunnablePassthrough()}
            )
            output_parser = StrOutputParser()
            context = setup_and_retrieval.invoke(rephrase_question['standalone_question'])
            docs = _combine_documents(context['context'])
            doc_dict = {'context': docs, "question": rephrase_question['standalone_question']}
            answer_prompt = ANSWER_PROMPT.invoke(doc_dict)
            final_response = llm.invoke(answer_prompt)
            generated_response=final_response.content
        current_utc_time = datetime.now(timezone.utc)
        desired_timezone = timezone(timedelta(hours=-7))
        current_time_with_timezone = current_utc_time.astimezone(desired_timezone)
        formatted_timestamp = current_time_with_timezone.strftime("%Y-%m-%d %H:%M:%S%z")
        # logger.info(f"formateed timestamp: {formatted_timestamp}")
        data = (userId, str(userQuery), str(generated_response), str(formatted_timestamp), botId)
        insert_query = f'INSERT INTO "GeneralChatHistory" ("UserId","Question","Answer","CreatedDate","BotId") VALUES (%s, %s, %s, %s, %s)'
        try:
            cursor.execute(insert_query, data)
            logger.info(f"successfully insert the data")
        except Exception as e:
            logger.critical(f"Error: Insert data {e}")
            return Response({"error": "Database Connection Error"},
                                status=status.HTTP_400_BAD_REQUEST)

        myresposne = [{
            'type': "question",
            'content':
                userQuery,
        },
            {
                'type': "answer",
                'content':
                    generated_response,
            }]
        logger.info("Success: end response")
        return Response({"message": "Response Generated Successfully!", "data": myresposne}, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"End error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_generalchat_botid(request):
    bot_list = [v.pk for v in Userbot.objects.filter(userid=request.user.pk).filter(isarchive=False)]
    subquery = Generalchathistory.objects.annotate(
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
            'question':query_data.question,
            'answer':query_data.answer,
            'botid':query_data.botid.pk
        }
        new_list.append(new_dict)
    return Response({'message':'General Chat User Bot ID','data':new_list},status=status.HTTP_200_OK)


@swagger_auto_schema(method='GET',
                     manual_parameters=[
                         openapi.Parameter('botid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True), ])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_general_chat_history(request):
    new_list = list()
    general_chat = Generalchathistory.objects.filter(botid= request.query_params.get('botid')).order_by('createddate')
    for chat in general_chat:
        myresposne = {
            'type': "question",
            'content':
                chat.question,
        }
        myresposne1 = {
                'type': "answer",
                'content':
                    chat.answer,
            }
        new_list.append(myresposne)
        new_list.append(myresposne1)
    return Response({'message': 'General Chat User History', 'data': new_list}, status=status.HTTP_200_OK)