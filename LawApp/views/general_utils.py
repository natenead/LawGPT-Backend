from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.chains.summarize import load_summarize_chain
import tempfile
from langchain_pinecone import PineconeVectorStore

from langchain.vectorstores import FAISS
from .chatbot_utils import IncomingFileProcessor
import openai
from langchain_core.prompts import ChatPromptTemplate
from operator import itemgetter
from pathlib import Path
# from chatbot_utils import IncomingFileProcessor
import asyncio
# from qdrant_client import QdrantClient
# from langchain.vectorstores import Qdrant
# from langchain.vectorstores import Qdrant
from dotenv import load_dotenv
import logging
import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain.embeddings import HuggingFaceEmbeddings
import math, re, time
from langchain.document_loaders import Docx2txtLoader, PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import boto3
from langchain.retrievers.multi_query import MultiQueryRetriever
import tiktoken
from pathlib import Path
import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s:%(name)s:%(levelname)s:%(message)s:%(funcName)s')
file_handler = logging.FileHandler('raf.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
load_dotenv()
aws_key = os.getenv('ACCESS_KEY')
aws_secret_key = os.getenv('SECRET_ACCESS_KEY')
aws_space_name = os.getenv('SPACE_NAME')
region_name = os.getenv('region_name')
endpoint_url = os.getenv('endpoint_url')
gpt_model_name = os.getenv('gpt_model_name')


def get_embedding_funtion():
    embed_model = "sentence-transformers/all-mpnet-base-v2"
    embed_fn = HuggingFaceEmbeddings(model_name=embed_model)
    return embed_fn


def get_number_of_files_based_on_threads(no_of_threads, no_of_files, result):
    if no_of_threads != 0:
        allocated_files = math.ceil(no_of_files / no_of_threads)
        result.append(allocated_files)
        rem_files = float(no_of_files) - allocated_files
        get_number_of_files_based_on_threads(no_of_threads - 1, rem_files, result)
        return result


# class IncomingFileProcessor():
#     def __init__(self, chunk_size=750) -> None:
#         self.chunk_size = chunk_size
#     def load_local_vectordb_using_faiss(self, vectordb_folder_path, embed_fn):
#         index_store_path = Path(vectordb_folder_path)
#         if index_store_path.exists():
#             local_db = FAISS.load_local(str(index_store_path), embed_fn)
#             return local_db
#         else:
#             return None
#
#     def get_pdf_splits(self, pdf_file: str, filename: str):
#         try:
#             loader = PyMuPDFLoader(pdf_file)
#             pages = loader.load()
#             logger.info("Succesfully loaded the pdf file")
#             textsplit = RecursiveCharacterTextSplitter(
#                 chunk_size=self.chunk_size, chunk_overlap=15, length_function=len)
#             doc_list = []
#             for pg in pages:
#                 pg_splits = textsplit.split_text(pg.page_content)
#                 for page_sub_split in pg_splits:
#                     metadata = {"source": filename}
#                     doc_string = Document(page_content=page_sub_split, metadata=metadata)
#                     doc_list.append(doc_string)
#             logger.info("Succesfully split the pdf file")
#             return doc_list
#             # return pages
#         except Exception as e:
#             logger.critical(f"Error in Loading pdf file: {str(e)}")
#             raise Exception(str(e))
#
#     def get_docx_splits(self, docx_file: str, filename: str):
#         try:
#             loader = Docx2txtLoader(str(docx_file))
#             txt = loader.load()
#             logger.info("Succesfully loaded the docx file")
#
#             textsplit = RecursiveCharacterTextSplitter(
#                 chunk_size=self.chunk_size, chunk_overlap=15, length_function=len)
#
#             doc_list = textsplit.split_text(txt[0].page_content)
#             new_doc_list = []
#             for page_sub_split in doc_list:
#                 metadata = {"source": filename}
#                 doc_string = Document(page_content=page_sub_split, metadata=metadata)
#                 new_doc_list.append(doc_string)
#             logger.info("Succesfully split the docx file")
#             return new_doc_list
#         except Exception as e:
#             logger.critical("Error in Loading docx file:" + str(e))
#             raise Exception(str(e))
#

chunk_size = 350
file_processor = IncomingFileProcessor(chunk_size=chunk_size)


def load_data(file_path, file_extension, file_name):
    if file_extension.lower() == "pdf":
        logger.info("enter in pdf file loader")
        texts = file_processor.get_pdf_splits(str(Path.cwd() / file_path), file_name)
        os.remove(file_path)
        logger.info("Successfully remove the pdf file")
        return texts

    elif file_extension.lower() == "docx":
        logger.info("enter in docx file loader")
        texts = file_processor.get_docx_splits(str(Path.cwd() / file_path), file_name)
        os.remove(file_path)
        logger.info("Successfully remove the docx file")
        return texts
    else:
        texts = []
        return texts


# generate_topics_for_deposition
# =====================================================================================#
# Generate topics for deposition based on the situation

def generate_topics(situation, previous_topics, openaikey):
    prompt_template = """
        You are a trained to help lawyers prepare for deposition on a particular situation.
        You are expected to suggest 4/5 relevant topics depending upon the situation. You must not regenerate the previous topics.
        Please provide the topics as numbered list.
        ((((Make the topics concise and legally meaningful. Possibly one liner. (Maximum 15 words in each topic)))))
        The situation is: {situation}
        previous topics: {previous_topics}
        """

    llm = ChatOpenAI(temperature=0.7, model=gpt_model_name, openai_api_key=openaikey)
    llm_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate.from_template(prompt_template)
    )

    return clean_topic_response(llm_chain({"situation": situation, "previous_topics": previous_topics})["text"])


# Clean the topic list
def clean_topic_response(response):
    response_items_str = response.split("\n")

    response_list = []

    for item in response_items_str:
        item = item.replace("'", "")
        response_list.append({"Topic": item.split(". ", 1)[1]})

    return response_list


# generate_question_for_deposition_topics
# =====================================================================================#
# Generate questions for deposition based on the topics
# def generate_questions(topics,openaikey):
#     prompt_template = """
#     You are a trained to help lawyers prepare for deposition on a particaular topic.
#     You are expected to suggest 5/6 relevant questions depending upon the topic.
#     Please provide the questions as numbered list.
#     ((((Make the questions are concise and meaningful. Possibly one liner. (Maximum 15 to 18 words in each topic)))))
#     The topic is: {Topic}"""
#
#     llm = ChatOpenAI(temperature=0.3, model=gpt_model_name,openai_api_key= openaikey)
#     llm_chain = LLMChain(
#         llm=llm,
#         prompt=PromptTemplate.from_template(prompt_template)
#     )
#
#     return clean_questions_response(llm_chain.apply(topics), topics)


def generate_questions(topics, openaikey):
    prompt_template = """
    You are a trained to help lawyers prepare for deposition on a particaular topic.
    You are expected to suggest 5/6 relevant questions on each topic.
    Please provide the questions as numbered list.
    ((((Response must not contain topic before Question))))\n
    ((((Make the questions are concise and meaningful. Possibly one liner. (Maximum 15 to 18 words in each topic)))))\n
    (((You must not add this  '---' in response.)))

    The topic is: {Topic}"""

    llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini", openai_api_key=openaikey)
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    res = chain.invoke({"Topic": topics}).content
    # llm_chain = LLMChain(
    #     llm=llm,
    #     prompt=PromptTemplate.from_template(prompt_template)
    # )

    return clean_questions_response(res, topics)


# def clean_questions_response(response, topics):
#     final_response = []
#
#     for index, i in enumerate(response):
#         topic = topics[index]["Topic"]
#         response = clean_response(i["text"], topic)
#         final_response.append(response)
#
#     return final_response
def clean_questions_response(response, topics):
    final_response = []
    response = response.split("\n\n")
    for index, i in enumerate(response):
        topic = topics[index]["Topic"]
        response = clean_response(i, topic)
        final_response.append(response)

    return final_response


def clean_response(response, topic):
    response_items_str = response.split("\n")
    response_list = []

    for item in response_items_str:
        try:
            response_list.append(item.split(". ", 1)[1])
        except:
            pass
    return {topic: response_list}


def make_dictionary(topics):
    lst = []
    for i in topics:
        print(i)
        lst.append({"Topic": i})
    return lst


# simple_caselaw_search_with_response_and_source
# =====================================================================================#
# Searching the Existing CaseLaws and their Sources.
def search_caselaw(query, local_db, openaikey):
    # Userapikeys.objects.get(userid=AdminUser.present.get(userid=request.user.pk).pk)
    # prompt_template = """
    #     You are trained to extract Answer from the given Context and Question.
    #     If the Answer is not found in the Context, then return "StatusCode:404", otherwise return the Answer.
    #     Context: {context}
    #     Question: {question}
    # """
    # prompt_template = """
    #     You are trained to analyze the given paragraphs and extract relevant information from the query.
    #     If you able to find any relevant information, then you must return it, otherwise you must return "StatusCode:404".
    #     paragraphs: {context}
    #     query: {question}
    #     Relevant information: 
    # """
    prompt_template = """
        You are a legal expert. Your role is to identify whether it is a document, agreement, or legal case 
        from the given paragraphs and then analyze the content to extract relevant information from the query.
        
        paragraphs: {context}
        query: {question}
        Relevant information: 
    """
    num_chunks = 10

    # mprompt_url = PromptTemplate(
    #     template=prompt_template, input_variables=["context", "question"], validate_template=False)
    # chain_type_kwargs = {"prompt": mprompt_url}

    chat_llm = ChatOpenAI(model=gpt_model_name, openai_api_key=openaikey, temperature=0.3)

    multiqa_retriever = MultiQueryRetriever.from_llm(llm=chat_llm,
                                                     retriever=local_db.as_retriever(search_type="similarity",
                                                                                     search_kwargs={"k": num_chunks}))
    # qa = RetrievalQA.from_chain_type(llm=chat_llm,
    #                                  chain_type="stuff",
    #                                 #  retriever=local_db.as_retriever(search_type="similarity", search_kwargs={"k": num_chunks}),
    #                                  retriever = multiqa_retriever,
    #                                  chain_type_kwargs=chain_type_kwargs,
    #                                  return_source_documents=True)

    # qa = RetrievalQA.from_chain_type(llm=chat_llm,
    #                                  chain_type="stuff",
    #                                  retriever=local_db.as_retriever(search_type="similarity",search_kwargs={"k":10}),
    #                                  chain_type_kwargs=chain_type_kwargs,
    #                                  return_source_documents=True,
    #                                  )

    # result = qa({"query": query})

    # return result
    # retriever = local_db.as_retriever(search_type="similarity", search_kwargs={"k": num_chunks})
    prompt = ChatPromptTemplate.from_template(prompt_template)
    setup_and_retrieval = RunnableParallel(
        {"context": multiqa_retriever, "question": RunnablePassthrough()}
    )
    model = ChatOpenAI(model=gpt_model_name, openai_api_key=openaikey, temperature=0.3)
    output_parser = StrOutputParser()
    # chain = setup_and_retrieval | prompt | model | output_parser
    context = setup_and_retrieval.invoke(query)
    prompt_answer = prompt.invoke(context)
    model_answer = model.invoke(prompt_answer)
    response = output_parser.invoke(model_answer)
    return response


def parse_output(documents):
    lst = []
    for doc in documents:
        # doc.metadata['source'].split(".pdf")[0]
        lst.append(doc.metadata['source'].split(".pdf")[0])

    return lst


# simple_chatbot
# =========================================================#
def semantic_search_conversation(query, db):
    # result = qa_conv({"question": query})
    # return str(result["answer"])
    prompt = f"""You are an answer retriever who is expert in generating answers for given legal document queries.
        You should return a comprehensive answer of one paragraph that includes relevant facts from the web. If you don't know the answer, then you must return 'statusCode:303'.
        Query : {query}
        Answer : """
    # print(prompt)
    try:
        response = openai.ChatCompletion.create(
            model=gpt_model_name,
            messages=[
                {"role": "system", "content": "You are an expert in generating answers for legal documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        answer = response['choices'][0]['message']['content']
    except Exception as e:
        raise Exception('OpenAI key Error')
    prompt_template = """
            You are trained to analyze the given paragraphs and extract relevant information from the query. If you don't know the answer, then you must return 'statusCode:303'.
            paragraphs:""" + str(answer) + """{context}
            query: {question}
            Relevant information: 
        """
    mprompt_url = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"], validate_template=False)
    chain_type_kwargs = {"prompt": mprompt_url}

    chat_llm = ChatOpenAI(model=gpt_model_name, openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0.3)
    # multiqa_retriever = MultiQueryRetriever.from_llm(llm=chat_llm,
    #                                      retriever=db.as_retriever(search_kwargs={"k": num_chunks}))
    qa = RetrievalQA.from_chain_type(llm=chat_llm,
                                     chain_type="stuff",
                                     retriever=db.as_retriever(search_type="similarity", search_kwargs={"k": 2}),
                                     #  retriever = multiqa_retriever,
                                     chain_type_kwargs=chain_type_kwargs)

    result = qa.run(query)
    return result


# summarise_the_uploaded_document
# =========================================================#
def summarize(all_texts, key):
    try:
        openai.api_key = key
        if len(all_texts) > 12:
            all_texts = all_texts[:4] + all_texts[len(all_texts) // 2 - 2: len(all_texts) // 2 + 2] + all_texts[-4:]

        prompt = f"""You are text summarizer who is expert at performing Extreme TLDR generation for given text. 
            Extreme TLDR is a form of extreme summarization, which performs high source compression, removes stop words and
            summarizes the text whilst retaining meaning. The result is the shortest possible summary that retains all of 
            the original meaning and context of the text. 
            text for Extreme TLDR generation : {all_texts}
            Extreme TLDR : """
        # print(prompt)
        try:
            response = openai.chat.completions.create(
                model=gpt_model_name,

                messages=[
                    {"role": "system", "content": "You are an expert in generating summaries for legal documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            summary = response.choices[0].message.content
            return summary

        # Handle API error here, e.g. retry or log
        except openai.error.APIError as e:
            logger.critical(f"OpenAI API returned an API Error")
            raise openai.error.APIError('OpenAI API returned an API Error')
        # Handle connection error here
        except openai.error.APIConnectionError as e:
            logger.critical(f"Failed to connect to OpenAI API")
            raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
        # Handle rate limit error (we recommend using exponential backoff)
        except openai.error.RateLimitError as e:
            logger.critical(f"OpenAI API request exceeded rate limit")
            raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
        except Exception as e:
            logger.critical(f'Error : {str(e)}')
            raise Exception("AI is not available")

    except Exception as ex:
        logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
        return None


# generate_Vector_DB
# =========================================================#
# def handling_files(contents, file_extension, original_filename):
#     file_processor = IncomingFileProcessor(chunk_size=450)
#     try:
#         if contents:
#             if file_extension.endswith('docx'):
#                 filename = Path.cwd() / "Temp_File" / "docx_file"
#                 print(filename)
#                 with open(filename, 'wb') as tmp_file:
#                     tmp_file.write(contents)
#                 texts = file_processor.get_docx_splits(str(filename), original_filename)
#
#             elif file_extension.endswith('.pdf'):
#                 filename = Path.cwd() / "Temp_File" / "pdf_file"
#                 print(filename)
#                 with open(filename, 'wb') as tmp_file:
#                     tmp_file.write(contents)
#                 texts = file_processor.get_pdf_splits(str(filename), original_filename)
#
#             return texts
#
#     except Exception as e:
#         raise e

def handling_files(contents, file_extension, original_filename):
    file_processor = IncomingFileProcessor(chunk_size=512)
    try:
        if contents:
            suffix = ".docx" if file_extension.endswith('docx') else ".pdf"

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(contents)

            try:
                if file_extension.endswith('docx'):
                    texts = file_processor.get_docx_splits(tmp_file.name, original_filename)
                elif file_extension.endswith('.pdf'):
                    texts = file_processor.get_pdf_splits(tmp_file.name, original_filename)
                else:
                    texts = ""

            finally:
                # Clean up the temporary file
                Path(tmp_file.name).unlink()

            return texts

    except Exception as e:
        raise e


# extract_contract_clauses
# =========================================================#
def semantic_search_on_contract_clauses(db, key):
    # prompt_template = """
    #     You are trained to analyze the Question asked by the user.
    #     You will analyze the document and give the answer according to the query:
    #     Context: {context}
    #     Question: {question}
    #     """
    num_chunks = 10
    #
    # mprompt_url = PromptTemplate(
    #     template=prompt_template, input_variables=["context", "question"], validate_template=False)
    # chain_type_kwargs = {"prompt": mprompt_url}

    query = """
        Please analyze the document and give the following specifc details on that:
        1. Find accurate deal terms from the document.
        2. Find specific dollar amounts $.
        3. Find specific dataes.
        4. Find specific clauses from document in a set.
        5. Find anything that can be useful to understand the contract.
    """

    # llm_gpt35 = ChatOpenAI(model_name=gpt_model_name,openai_api_key= key)
    # qa = RetrievalQA.from_chain_type(llm=llm_gpt35, chain_type="stuff",
    #                                  retriever=db.as_retriever(search_kwargs={"k": num_chunks}),
    #                                  chain_type_kwargs=chain_type_kwargs)
    #

    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": num_chunks})
    template = """
        You are trained to analyze the Question asked by the user. 
        You will analyze the document and give the answer according to the query:
        Context: {context}
        Question: {question}
        """
    prompt = ChatPromptTemplate.from_template(template)
    setup_and_retrieval = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    )
    model = ChatOpenAI(model=gpt_model_name, openai_api_key=key.strip())
    output_parser = StrOutputParser()
    # chain = setup_and_retrieval | prompt | model | output_parser
    context = setup_and_retrieval.invoke(query)
    prompt_answer = prompt.invoke(context)
    model_answer = model.invoke(prompt_answer)
    response = output_parser.invoke(model_answer)
    return response
    # return qa.run(query).replace("Answer: ", "")


# contract_compliance
# =====================================================================================#

# def create_new_vectorstore_qdrant(doc_list, embed_fn, COLLECTION_NAME, qdrant_url, qdrant_api_key ):
#     try:
#         qdrant = Qdrant.from_documents(
#             documents = doc_list,
#             embedding = embed_fn,
#             url=qdrant_url,
#             prefer_grpc=True,
#             api_key=qdrant_api_key,
#             collection_name=COLLECTION_NAME,
#         )
#         return qdrant
#     except Exception as ex:
#         raise Exception({"Error": str(ex)})


def convert_para_to_html(paragraph):
    try:

        prompt = f"""As an expert in creating visually appealing content, your task is to convert the following paragraphs into HTML format to enhance their readability. Utilize suitable HTML tags to structure the content effectively and ensure its coherence.

        Paragraphs: {paragraph}

        Your HTML-formatted response should focus on structuring the content for improved readability without any additional commentary or lines.
        """

        # print(prompt)
        try:
            response = openai.chat.completions.create(
                model=gpt_model_name,
                messages=[
                    {"role": "system", "content": "You are an expert in generating updated text for legal documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            paragraph = response.choices[0].message.content
            # paragraph = paragraph.replace("h3", "h5").replace("h4", "h5").replace("h1", "h4").replace("h2", "h4")
            return paragraph
        except Exception as e:
            print(e)

        # Handle API error here, e.g. retry or log
        except openai.error.APIError as e:
            logger.critical(f"OpenAI API returned an API Error")
            raise openai.error.APIError('OpenAI API returned an API Error')
        # Handle connection error here
        except openai.error.APIConnectionError as e:
            logger.critical(f"Failed to connect to OpenAI API")
            raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
        # Handle rate limit error (we recommend using exponential backoff)
        except openai.error.RateLimitError as e:
            logger.critical(f"OpenAI API request exceeded rate limit")
            raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
        except Exception as e:
            logger.critical(f'Error : {str(e)}')
            raise Exception("AI is not available")

    except Exception as ex:
        logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
        return None


def semantic_search_on_contract_compliance(db, key):
    # prompt_template = """
    #     You are trained to analyze the points raised by the user.
    #     You will analyze the document and give the answer according to the query:
    #     Context: {context}
    #     Question: {question}
    #     """

    # prompt_template = """
    #
    #     You are trained to analyze the points raised by the user. You will analyze the Context and give the answer
    #     according to the Question. If the Context does not seem legal, return 'statusCode:404', otherwise return the
    #     answer according to the Question: Context: {context} Question: {question}
    #
    #     """
    prompt_template = """
            You are trained to analyze the points raised by the user in *Question*. 
            You will analyze the *Context* and give the answer according 
            to the *Question*. 

            ((( *Question:* {question} )))

            ((( *Context:* {context} )))


            """

    num_chunks = 10

    # mprompt_url = PromptTemplate(
    #     template=prompt_template, input_variables=["context", "question"], validate_template=False)
    # chain_type_kwargs = {"prompt": mprompt_url}

    query = """
        Conduct a comprehensive evaluation of the designated section within the document, focusing on the following key objectives:

        1. Risk Identification: Thoroughly assess the language employed and determine any potential risks associated with its non-compliance. 
        These risks may encompass legal implications, misinterpretations, offensive connotations, or any other adverse consequences that could 
        arise due to the usage of specific words or phrases.

        2. Contextual Analysis: Consider the context in which the non-compliant language is situated. Evaluate whether the language's 
        inappropriateness is influenced by the subject matter, the intended audience, or the broader communication goals. 
        This step is crucial for pinpointing nuances that might impact the severity of the identified risks.

        3. Relevance of Language: Examine the extent to which the non-compliant language deviates from established guidelines or industry standards. 
        Determine whether the language contradicts specific terminology requirements, branding directives, or overall communication policies.

        4. Recommended Revisions: Formulate well-founded suggestions for revising the flagged language. These recommendations should be geared 
        towards aligning the language with established compliance standards while preserving the document's intended message. Consider offering 
        alternative phrasing, synonyms, or explanations that ensure the language remains accurate and effective.

        5. Risk Mitigation Strategies: Propose strategies for mitigating the identified risks. This could involve not only language modification 
        but also supplementary actions such as legal consultations, additional disclaimers, or clarification statements. The aim is to provide a 
        comprehensive approach that minimizes potential negative outcomes.

        6. Clarity and Readability: Evaluate how the recommended revisions contribute to the overall clarity and readability of the document. 
        Ensure that the language remains coherent, understandable, and suitable for the target audience, even after incorporating the suggested changes.

        7. Ethical and Cultural Sensitivity: Consider any ethical or cultural implications associated with the language choices. Assess whether the 
        non-compliant language could be offensive, insensitive, or inappropriate from cultural, gender, or diversity perspectives. Offer alternatives 
        that demonstrate cultural awareness and inclusivity.

        In summary, perform a meticulous analysis of the document excerpt, highlighting risks stemming from non-compliant language and providing 
        actionable suggestions for revisions. Strive to strike a balance between adherence to standards and the effective conveyance of the 
        document's intended meaning.
    """

    # llm_gpt35 = ChatOpenAI(model_name=gpt_model_name,openai_api_key= key)
    # qa = RetrievalQA.from_chain_type(llm=llm_gpt35, chain_type="stuff",
    #                                  retriever=db.as_retriever(search_kwargs={"k": num_chunks}),
    #                                  chain_type_kwargs=chain_type_kwargs)

    # response = qa.run(query)

    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": num_chunks})
    prompt = ChatPromptTemplate.from_template(prompt_template)
    setup_and_retrieval = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    )
    model = ChatOpenAI(model=gpt_model_name, openai_api_key=key)
    output_parser = StrOutputParser()
    # chain = setup_and_retrieval | prompt | model | output_parser
    context = setup_and_retrieval.invoke(query)
    prompt_answer = prompt.invoke(context)
    model_answer = model.invoke(prompt_answer)
    response = output_parser.invoke(model_answer)

    if 'statusCode:404' in response:
        response = 'Sorry, the document you uploaded does not appear to be a legal document'
    else:
        response = convert_para_to_html(response)
        response = response.replace("h3", "h5").replace("h4", "h5").replace("h1", "h4").replace("h2", "h4")
    return response
    # response = convert_para_to_html(response)

    # return response


def semantic_search_on_contract_review_automation(db, key):
    # prompt_template = """
    #     You are trained to analyze the points raised by the user.
    #     You will analyze the Context and give the answer according
    #     to the Question. If the Context does not seem legal, return 'statusCode:404', otherwise return the answer according to the Question:
    #     Context: {context}
    #     Question: {question}
    #
    #     """
    prompt_template = """
            You are trained to analyze the points raised by the user in *Question*. 
            You will analyze the *Context* and give the answer according 
            to the *Question*. 

            ((( *Question:* {question} )))

            ((( *Context:* {context} )))


            """
    num_chunks = 10

    # mprompt_url = PromptTemplate(
    #     template=prompt_template, input_variables=["context", "question"], validate_template=False)
    # chain_type_kwargs = {"prompt": mprompt_url}

    query = """
        Objective: Review and redline the uploaded contract document to identify potential legal challenges or clauses that may be legally challenging for a business. 
        Highlight and explain the clauses that could have adverse implications, raise concerns, or require further legal scrutiny.


        1. Introduction: Provide context
           Please thoroughly analyze the uploaded contract document. The document is a legally binding contract intended for a business transaction. 
           Your task is to review and redline the contract, focusing on identifying any clauses, terms, or sections that could potentially create legal 
           challenges or "gotchas" for the involved parties. Highlight and explain these points in detail.

        2. Clarity is Key: Explain the Analysis
           As you review the contract, provide clear explanations for each potential legal challenge you identify. Explain why these clauses might be problematic, 
           referencing relevant legal principles or precedents when possible. Consider implications for both parties involved in the transaction.

        3. Highlight and Redline: Direct Edits
           While explanations are crucial, don't forget to directly redline or annotate the specific clauses within the contract that you believe could pose challenges. 
           Use clear formatting to make these edits stand out.

        4. Diverse Challenges: Cover Different Aspects
           Consider various legal aspects, such as terms of payment, delivery obligations, dispute resolution mechanisms, termination conditions, intellectual 
           property rights, confidentiality, indemnity clauses, and any other relevant areas based on the contract's nature.

        5. Business Impact: Discuss Ramifications
           For each identified challenge, discuss the potential business impact and risks associated with that clause. 
           How could it affect the parties financially, operationally, or legally? What steps could the parties take to mitigate these risks?

        6. Provide Recommendations: Suggest Solutions
           Where possible, provide suggestions for improving the problematic clauses. This could include rephrasing, adding specific definitions, 
           or suggesting alternative approaches that would be more balanced and legally sound.

        Conclude Professionally
        In conclusion, summarize the main legal challenges you've identified in the contract. Emphasize the importance of addressing these issues before finalizing the agreement.
        Highlight the potential benefits of clarifying or amending these clauses to ensure a smoother business relationship.
    """

    # llm_gpt35 = ChatOpenAI(model_name=gpt_model_name,openai_api_key= key)
    # qa = RetrievalQA.from_chain_type(llm=llm_gpt35, chain_type="stuff",
    #                                  retriever=db.as_retriever(search_kwargs={"k": num_chunks}),
    #                                  chain_type_kwargs=chain_type_kwargs)
    # response = qa.run(query)

    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": num_chunks})
    prompt = ChatPromptTemplate.from_template(prompt_template)
    setup_and_retrieval = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    )
    model = ChatOpenAI(model=gpt_model_name, openai_api_key=key)
    output_parser = StrOutputParser()
    # chain = setup_and_retrieval | prompt | model | output_parser
    context = setup_and_retrieval.invoke(query)
    prompt_answer = prompt.invoke(context)
    model_answer = model.invoke(prompt_answer)
    response = output_parser.invoke(model_answer)
    if 'statusCode:404' in response:
        response = 'Sorry, the document you uploaded does not appear to be a legal document'
    else:
        response = convert_para_to_html(response)
        response = response.replace("h3", "h5").replace("h4", "h5").replace("h1", "h4").replace("h2", "h4")
    return response


# def create_new_vectorstore_qdrant(doc_list, embed_fn, COLLECTION_NAME):
#     try:
#         qdrant = Qdrant.from_documents(
#             documents = doc_list,
#             embedding = embed_fn,
#             url=os.getenv('qdrant_url'),
#             prefer_grpc=True,
#             api_key=os.getenv('api_key'),
#             collection_name=COLLECTION_NAME,
#         )
#         logger.info("Successfully created the vectordb")
#         return qdrant
#     except Exception as ex:
#         logger.critical("Vectordb Failed:"+str(ex))
#         raise Exception({"Error": str(ex)})

# def load_local_vectordb_using_qdrant(vectordb_folder_path, embed_fn):
#     qdrant_client = QdrantClient(
#         url=os.getenv('qdrant_url'),
#         prefer_grpc=True,
#         api_key=os.getenv('api_key'),
#     )
#     qdrant_store= Qdrant(qdrant_client, vectordb_folder_path, embed_fn)
#     return qdrant_store

# def delete_vectordb_using_qdrant( vectordb_folder_path,  qdrant_url=os.getenv('qdrant_url'), qdrant_api_key=os.getenv('api_key')):
#     try:
#         qdrant_client = QdrantClient(
#             url=qdrant_url,
#             prefer_grpc=True,
#             api_key=qdrant_api_key,
#         )
#         qdrant_client.delete_collection(collection_name=vectordb_folder_path)
#     except Exception as e:
#         raise Exception(str(e))
#     return "Done"
# def get_collection_list_qdrant(qdrant_url=os.getenv('qdrant_url'), qdrant_api_key=os.getenv('api_key')):
#     try:
#         qdrant_client = QdrantClient(
#             url=qdrant_url,
#             prefer_grpc=True,
#             api_key=qdrant_api_key,
#         )
#         collections=qdrant_client.get_collections()
#     except Exception as e:
#         raise Exception(str(e))
#     return collections

# Initialize a session using DigitalOcean Spaces.


def generate_headings(content, key):
    openai.api_key = key
    len_tokens = num_tokens_from_string(content, gpt_model_name)
    if len_tokens > 16000:
        content = content[:15999]
    try:

        prompt = f"""You are a Expert legal document drafter. Given a legal document content, your job is to suggest headings which are missing from the legal document content. You are expected to suggest 4-8 missing headings.
        You must provide the headings as numbered list.
        ((((Make the missing headings concise and legally meaningful. Possibly one liner. (Maximum 5 words in each heading.)))))
        legal document content: {content}
        headings: """

        # print(prompt)
        try:
            response = openai.chat.completions.create(
                model=gpt_model_name,
                messages=[
                    {"role": "system", "content": "You are an expert in generating updated text for legal documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            headings = response.choices[0].message.content
            return headings
        # Handle API error here, e.g. retry or log
        except openai.error.APIError as e:
            logger.critical(f"OpenAI API returned an API Error")
            raise openai.error.APIError('OpenAI API returned an API Error')
        # Handle connection error here
        except openai.error.APIConnectionError as e:
            logger.critical(f"Failed to connect to OpenAI API")
            raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
        # Handle rate limit error (we recommend using exponential backoff)
        except openai.error.RateLimitError as e:
            logger.critical(f"OpenAI API request exceeded rate limit")
            raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
        except Exception as e:
            logger.critical(f'Error : {str(e)}')
            raise Exception("AI is not available")

    except Exception as ex:
        logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
        return None


# def generate_headings(content,key):
#     openai.api_key = key
#     len_tokens = num_tokens_from_string(content, 'gpt-3.5-turbo-16k')
#     if len_tokens > 16000:
#         content = content[:15999]
#     try:
#
#         prompt = f"""You are a Expert legal document drafter. Given a legal document content, your job is to suggest headings which are missing from the legal document content. You are expected to suggest 4-8 missing headings.
#         You must provide the headings as numbered list.
#         ((((Make the missing headings concise and legally meaningful. Possibly one liner. (Maximum 5 words in each heading.)))))
#         legal document content: {content}
#         headings: """
#
#         # print(prompt)
#         try:
#             response = openai.ChatCompletion.create(
#                 model=gpt_model_name,
#                 messages=[
#                     {"role": "system", "content": "You are an expert in generating updated text for legal documents."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.7
#             )
#             headings = response['choices'][0]['message']['content']
#             return headings
#
#         # Handle API error here, e.g. retry or log
#         except openai.error.APIError as e:
#             logger.critical(f"OpenAI API returned an API Error")
#             raise openai.error.APIError('OpenAI API returned an API Error')
#         # Handle connection error here
#         except openai.error.APIConnectionError as e:
#             logger.critical(f"Failed to connect to OpenAI API")
#             raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
#         # Handle rate limit error (we recommend using exponential backoff)
#         except openai.error.RateLimitError as e:
#             logger.critical(f"OpenAI API request exceeded rate limit")
#             raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
#         except Exception as e:
#             logger.critical(f'Error : {str(e)}')
#             raise Exception("AI is not available")
#
#     except Exception as ex:
#         logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
#         return None


def update_text(text, context, key):
    try:
        openai.api_key = key
        prompt = f"""You are a legal document writer and expert. You will recieve a sentence and a paragraph from which sentence is taken. Your task is to revise the sentence while retaining its original meaning, tone, and context which you can learn from the paragraph. The revised sentence must be suitable for a legal document. Only return the revised sentence. You must not return the rephrased paragraph.
        sentence: {text}
        paragraph: {context}
        Revised sentence: """

        # print(prompt)
        try:
            response = openai.ChatCompletion.create(
                model=gpt_model_name,

                messages=[
                    {"role": "system", "content": "You are an expert in generating updated text for legal documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            updated_text = response['choices'][0]['message']['content']
            return updated_text

        # Handle API error here, e.g. retry or log
        except openai.error.APIError as e:
            logger.critical(f"OpenAI API returned an API Error")
            raise openai.error.APIError('OpenAI API returned an API Error')
        # Handle connection error here
        except openai.error.APIConnectionError as e:
            logger.critical(f"Failed to connect to OpenAI API")
            raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
        # Handle rate limit error (we recommend using exponential backoff)
        except openai.error.RateLimitError as e:
            logger.critical(f"OpenAI API request exceeded rate limit")
            raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
        except Exception as e:
            logger.critical(f'Error : {str(e)}')
            raise Exception("AI is not available")

    except Exception as ex:
        logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
        return None


def generate_heading_content(heading, key):
    try:
        openai.api_key = key

        prompt = f"""You are a Expert legal document drafter. Given a legal document heading, your job is to write a paragraph of 3/4 sentences related to the heading. The paragraph must be suitable for a legal document. 
        ((((Make the paragraph legally meaningful. (Maximum 3-4 sentences in a paragraph.)))))
        legal document heading: {heading}
        paragraph: """

        # print(prompt)
        try:
            # response = openai.ChatCompletion.create(
            # model=gpt_model_name,
            # messages=[
            #         {"role": "system", "content": "You are an expert in generating updated text for legal documents."},
            #         {"role": "user", "content":prompt }
            #     ],
            # temperature = 0.3
            # )
            # client = OpenAI()
            response = openai.chat.completions.create(
                model=gpt_model_name,
                messages=[
                    {"role": "system", "content": "You are an expert in generating updated text for legal documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            paragraph = response.choices[0].message.content
            return paragraph

        # Handle API error here, e.g. retry or log
        except openai.error.APIError as e:
            logger.critical(f"OpenAI API returned an API Error")
            raise openai.error.APIError('OpenAI API returned an API Error')
        # Handle connection error here
        except openai.error.APIConnectionError as e:
            logger.critical(f"Failed to connect to OpenAI API")
            raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
        # Handle rate limit error (we recommend using exponential backoff)
        except openai.error.RateLimitError as e:
            logger.critical(f"OpenAI API request exceeded rate limit")
            raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
        except Exception as e:
            logger.critical(f'Error : {str(e)}')
            raise Exception("AI is not available")

    except Exception as ex:
        logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
        return None


def search_caselaw_for_search_module(query, local_db, openaikey, state_list):
    # raise Exception("Your Quota Exceed!")
    try:
        prompt_template = """
            Your task is to extract a concise answer (less than 10 words) from the provided context and question.

            Context: {context}
            Question: {question}
            Answer (less than 10 words):
        """
        # state_list=state_list[0]
        # prompt_template = """
        #     You are trained to analyze the given paragraphs and extract relevant information from the query.
        #     The relevant information length should be less than 10 words.
        #     paragraphs: {context}
        #     query: {question}
        #     Relevant information:
        # """
        # prompt_template = """
        #      You are trained to analyze the given paragraphs and extract relevant information from the query.
        #      If you able to find any relevant information, then you must return 'Yes', otherwise you must return "No".

        #     context: {context}
        #     query: {question}
        #     Relevant information:
        # """
        # You will only return 'statuscode:404' you can't able to find even a single relevant context, otherwise you must return the relevant information:

        num_chunks = 50

        mprompt_url = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"], validate_template=False)
        chain_type_kwargs = {"prompt": mprompt_url}

        chat_llm = ChatOpenAI(model=gpt_model_name, openai_api_key=openaikey, temperature=0.3)
        if state_list == True:
            qa = RetrievalQA.from_chain_type(llm=chat_llm,
                                             chain_type="stuff",
                                             retriever=local_db.as_retriever(search_type="similarity",
                                                                             search_kwargs={"k": num_chunks}),
                                             chain_type_kwargs=chain_type_kwargs,
                                             return_source_documents=True)
            logger.info("successfully initialize the qa chain without state_list")
        else:
            qa = RetrievalQA.from_chain_type(llm=chat_llm,
                                             chain_type="stuff",
                                             retriever=local_db.as_retriever(search_type="similarity",
                                                                             search_kwargs={"k": num_chunks, "filter": {
                                                                                 "state": {"$in": state_list}}}),
                                             chain_type_kwargs=chain_type_kwargs,
                                             return_source_documents=True)
            logger.info("successfully initialize the qa chain having state_list")
        result = qa.invoke({"query": query})
        # result = qa.invoke()
        source_documents = result['source_documents']
        states_with_space = ["American Samoa", "District of Columbia", "New Hampshire", "New Jersey", "New Mexico",
                             "New York", "North Carolina", "North Dakota", "Puerto Rico", "Rhode Island",
                             "South Carolina", "South Dakota", "United States", "Virgin Islands"]

        len_documents = []
        check = None
        for case in source_documents:
            if len(case.page_content) > 350:
                court = case.metadata['court']
                for state_space in states_with_space:
                    if state_space.lower() in court:
                        check = state_space.lower()
                        break
                if check:
                    try:
                        if set((check,)) & set([v.lower() for v in state_list]):
                            len_documents.append(case)
                    except:
                        len_documents.append(case)
                else:
                    if state_list != True:

                        if not list(set(case.metadata['court'].split()) & set([v.lower() for v in state_list])):
                            pass
                        else:
                            len_documents.append(case)
                    else:
                        len_documents.append(case)

        result['source_documents'] = len_documents
    except Exception as e:
        logger.critical(f"Error: {e}")
        raise Exception(e)
    return result


def fetch_source_from_query_drafting_view(query, local_db, num_chunks, openaikey):
    """Responsible for getting relevant source file from db  for drafter

    Args:
        situation (str): text/situation given by the user

    Returns:
        dict: returns topics for deposition
    """
    # prompt_template = """
    #     You are trained to analyze the given paragraphs and extract relevant information from the query.
    #     If you able to find any relevant information, then you must return it, otherwise you must return "StatusCode:404".
    #     paragraphs: {context}
    #     query: {question}
    #     Relevant information:
    # """
    # first_para = """This Asset Purchase Agreement (“Agreement”) is made as of the date entered below (the “Effective Date”) by and among West Coast Career Services, LLC, a Washington limited liability company (“Buyer”), West Coast Careers, Inc., a Washington corporation (“Seller”) and Edward Beaulieu and Christopher Shablak (each an “Owner” and collectively, the “Owners”)."""
    # prompt_template = """
    # You are trained to analyze the given paragraphs and extract relevant information from the query.
    # paragraphs: """+str(first_para)+"""{context}
    # query: {question}
    # Relevant information:
    # """
    # prompt_template = """
    #     You are trained to analyze the given paragraphs and extract relevant information from the query.
    #     paragraphs: {context}
    #     query: {question}
    #     Relevant information:
    # """
    prompt_template = """
        You are a legal expert. Your role is to identify whether it is a document, agreement, or legal case 
        from the given paragraphs and then analyze the content to extract relevant information from the query.

        paragraphs: {context}
        query: {question}
        Relevant information: 
    """
    mprompt_url = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"], validate_template=False)
    chain_type_kwargs = {"prompt": mprompt_url}

    chat_llm = ChatOpenAI(model=gpt_model_name, openai_api_key=openaikey, temperature=0.3)
    multiqa_retriever = MultiQueryRetriever.from_llm(llm=chat_llm,
                                                     retriever=local_db.as_retriever(search_kwargs={"k": num_chunks}))
    qa = RetrievalQA.from_chain_type(llm=chat_llm,
                                     chain_type="stuff",
                                     #  retriever=local_db.as_retriever(search_type="similarity", search_kwargs={"k": num_chunks}),
                                     retriever=multiqa_retriever,
                                     chain_type_kwargs=chain_type_kwargs,
                                     return_source_documents=True)

    # result = qa({"query": query})
    result = qa.invoke(query)

    return result


def fetch_source_from_query(query, local_db, num_chunks, openaikey):
    """Responsible for getting relevant source file from db  for drafter

    Args:
        situation (str): text/situation given by the user

    Returns:
        dict: returns topics for deposition
    """
    # prompt_template = """
    #      You are trained to analyze the given paragraphs and extract relevant information from the query.
    #      If you able to find any relevant information, then you must return 'Yes', otherwise you must return "No".
    #
    #     context: {context}
    #     query: {question}
    #     Relevant information:
    # """

    prompt_template = """
        You are trained to extract relevant paragraph from the given Context and Query.
        If the relevant paragraph is not found in the Context, then return "StatusCode:404", otherwise return the paragraph.
        Context: {context}
        Query: {question}
    """

    mprompt_url = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"], validate_template=False)
    chain_type_kwargs = {"prompt": mprompt_url}
    chat_llm = ChatOpenAI(model=gpt_model_name, openai_api_key=openaikey, temperature=0.3)
    qa = RetrievalQA.from_chain_type(llm=chat_llm,
                                     chain_type="stuff",
                                     retriever=local_db.as_retriever(search_type="similarity",
                                                                     search_kwargs={"k": num_chunks}),
                                     chain_type_kwargs=chain_type_kwargs,
                                     return_source_documents=True)

    result = qa({"query": query})

    return result


# def generate_summary(all_texts,openaikey):
#     try:
#         openai.api_key = openaikey
#         if len(all_texts) > 12:
#             all_texts = all_texts[:4] + all_texts[len(all_texts) // 2 - 2: len(all_texts) // 2 + 2] + all_texts[-4:]
#         prompt = f"""You are text summarizer who is expert at performing Extreme TLDR generation for given text.
#         Extreme TLDR is a form of extreme summarization, which performs high source compression, removes stop words and
#         summarizes the text whilst retaining meaning. The result is the shortest possible summary that retains all of
#         the original meaning and context of the text.
#         text for Extreme TLDR generation : {all_texts}
#         Extreme TLDR : """
#         # print(prompt)
#         try:
#             response = openai.ChatCompletion.create(
#                 model=gpt_model_name,
#                 messages=[
#                     {"role": "system", "content": "You are an expert in generating summaries for legal documents."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.2
#             )
#             summary = response['choices'][0]['message']['content']
#             return summary
#
#         # Handle API error here, e.g. retry or log
#         except openai.error.APIError as e:
#             logger.critical(f"OpenAI API returned an API Error")
#             raise openai.error.APIError('OpenAI API returned an API Error')
#         # Handle connection error here
#         except openai.error.APIConnectionError as e:
#             logger.critical(f"Failed to connect to OpenAI API")
#             raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
#         # Handle rate limit error (we recommend using exponential backoff)
#         except openai.error.RateLimitError as e:
#             logger.critical(f"OpenAI API request exceeded rate limit")
#             raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
#         except Exception as e:
#             logger.critical(f'Error : {str(e)}')
#             raise Exception("AI is not available")
#
#     except Exception as ex:
#         logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
#         return None
#


def generate_summary(all_texts, key):
    try:
        openai.api_key = key
        if len(all_texts) > 12:
            all_texts = all_texts[:4] + all_texts[len(all_texts) // 2 - 2: len(all_texts) // 2 + 2] + all_texts[-4:]
        prompt = f"""You are text summarizer who is expert at performing Extreme TLDR generation for given text. 
        Extreme TLDR is a form of extreme summarization, which performs high source compression, removes stop words and
        summarizes the text whilst retaining meaning. The result is the shortest possible summary that retains all of 
        the original meaning and context of the text. 
        text for Extreme TLDR generation : {all_texts}
        Extreme TLDR : """
        # print(prompt)
        try:
            response = openai.chat.completions.create(
                model=gpt_model_name,
                messages=[
                    {"role": "system", "content": "You are an expert in generating summaries for legal documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            summary = response.choices[0].message.content
            return summary

        # Handle API error here, e.g. retry or log
        except openai.error.APIError as e:
            logger.critical(f"OpenAI API returned an API Error")
            raise openai.error.APIError('OpenAI API returned an API Error')
        # Handle connection error here
        except openai.error.APIConnectionError as e:
            logger.critical(f"Failed to connect to OpenAI API")
            raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
        # Handle rate limit error (we recommend using exponential backoff)
        except openai.error.RateLimitError as e:
            logger.critical(f"OpenAI API request exceeded rate limit")
            raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
        except Exception as e:
            logger.critical(f'Error : {str(e)}')
            raise Exception("AI is not available")

    except Exception as ex:
        logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
        return None


def generate_content(heading, openaikey):
    try:
        openai.api_key = openaikey
        prompt = f"""You are a Legal Expert. Given a prompt, your job is to write a paragraph of 3/4 sentences related to the prompt. The paragraph must be suitable for a legal document. 
        ((((Make the paragraph legally meaningful. (Maximum 3-4 sentences in a paragraph.)))))
        prompt: {heading}
        paragraph: """

        # print(prompt)
        try:
            response = openai.chat.completions.create(
                model=gpt_model_name,
                messages=[
                    {"role": "system", "content": "You are a Legal Expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            paragraph = response.choices[0].message.content
            return paragraph

        # Handle API error here, e.g. retry or log
        except openai.error.APIError as e:
            logger.critical(f"OpenAI API returned an API Error")
            raise openai.error.APIError('OpenAI API returned an API Error')
        # Handle connection error here
        except openai.error.APIConnectionError as e:
            logger.critical(f"Failed to connect to OpenAI API")
            raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
        # Handle rate limit error (we recommend using exponential backoff)
        except openai.error.RateLimitError as e:
            logger.critical(f"OpenAI API request exceeded rate limit")
            raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
        except Exception as e:
            logger.critical(f'Error : {str(e)}')
            raise Exception("AI is not available")

    except Exception as ex:
        logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
        return None


# def generate_content(heading,openaikey):
#     try:
#         openai.api_key = openaikey
#         prompt = f"""You are a Legal Expert. Given a prompt, your job is to write a paragraph of 3/4 sentences related to the prompt. The paragraph must be suitable for a legal document.
#         ((((Make the paragraph legally meaningful. (Maximum 3-4 sentences in a paragraph.)))))
#         prompt: {heading}
#         paragraph: """
#
#         # print(prompt)
#         try:
#             response = openai.ChatCompletion.create(
#                 model=gpt_model_name,
#                 messages=[
#                     {"role": "system", "content": "You are a Legal Expert."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.3
#             )
#             paragraph = response['choices'][0]['message']['content']
#             return paragraph
#
#         # Handle API error here, e.g. retry or log
#         except openai.error.APIError as e:
#             logger.critical(f"OpenAI API returned an API Error")
#             raise openai.error.APIError('OpenAI API returned an API Error')
#         # Handle connection error here
#         except openai.error.APIConnectionError as e:
#             logger.critical(f"Failed to connect to OpenAI API")
#             raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
#         # Handle rate limit error (we recommend using exponential backoff)
#         except openai.error.RateLimitError as e:
#             logger.critical(f"OpenAI API request exceeded rate limit")
#             raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
#         except Exception as e:
#             logger.critical(f'Error : {str(e)}')
#             raise Exception("AI is not available")
#
#     except Exception as ex:
#         logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
#         return None


def generate_template_content(user_requirements, key):
    openai.api_key = key
    try:

        prompt = f"""You are a Legal Drafter Expert tasked with crafting a comprehensive legal contract tailored to specific user requirements. To ensure the effectiveness of the contract, please take into account the following additional guidelines:

User Requirement: {user_requirements}

Additional Requirements:

Leverage your extensive legal expertise and adept research skills to construct a contract that encompasses vital terms and conditions crucial to the agreement. Such elements include, but are not limited to, the scope of work, payment details, project timelines, ownership rights, confidentiality clauses, termination protocols, and dispute resolution mechanisms.

Employ lucid and precise language throughout the document to minimize any potential ambiguity or confusion that may arise.

Employ a systematic approach by using numbered headings and bullet points to distinctly delineate the various sections and clauses of the contract.

Adopt a first-person perspective and employ the present tense when referring to the involved parties and their respective obligations.

Aim for a target length of approximately 1000 words.

To ensure the contract's clarity and accessibility for users, it must be drafted using HTML tags.

Contract Template"""
        # print(prompt)
        try:
            response = openai.chat.completions.create(
                model=gpt_model_name,
                messages=[
                    {"role": "system", "content": "You are a Legal Expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            paragraph = response.choices[0].message.content
            paragraph = paragraph.replace("h3", "h5").replace("h4", "h5").replace("h1", "h4").replace("h2",
                                                                                                      "h4").replace(
                "\n", "")
        # Handle API error here, e.g. retry or log
        except openai.error.APIError as e:
            logger.critical(f"OpenAI API returned an API Error")
            raise openai.error.APIError('OpenAI API returned an API Error')
        # Handle connection error here
        except openai.error.APIConnectionError as e:
            logger.critical(f"Failed to connect to OpenAI API")
            raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
        # Handle rate limit error (we recommend using exponential backoff)
        except openai.error.RateLimitError as e:
            logger.critical(f"OpenAI API request exceeded rate limit")
            raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
        except Exception as e:
            logger.critical(f'Error : {str(e)}')
            raise Exception("AI is not available")
        return paragraph


    except Exception as ex:
        logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
        return None


def missing_values(text, openaikey):
    try:
        openai.api_key = openaikey
        response = openai.ChatCompletion.create(
            model=gpt_model_name,
            messages=[
                {"role": "user", "content": "You are Data Entry Specialist."},
                {"role": "user", "content": f" text: \n {text}"},
                {'role': 'user',
                 'content': 'For given text, You must replace all information enclosed in <mark style=\'background-color: green; color: white;> dummy value</mark> with dummy values that must look like real value/information/checkbox.'}

            ],
            temperature=0.3,
            max_tokens=10000
        )
        answer = response['choices'][0].message['content']
        answer = re.sub(r'\d+\.\s*pasha', 'pasha', answer)
        answer_list = answer.split("pasha")[1:]
        # print(answer_list)
        return answer_list
    except openai.error.RateLimitError as e:
        time.sleep(3)
        logger.critical(f"OpenAI API request exceeded rate limit")
        pass

    except openai.error.OpenAIError as e:
        logger.critical(f"OpenAI API Error: {e}")
        raise
    except Exception as e:
        logger.critical(f'Error: {e}')
        raise


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    # encoding = tiktoken.encoding_for_model(encoding_name)
    encoding = tiktoken.get_encoding('cl100k_base')
    num_tokens = len(encoding.encode(string))
    return num_tokens


# def search_summary(text):
#     len_tokens = num_tokens_from_string(text, 'gpt-3.5-turbo-16k')
#     if len_tokens>16000:
#         text = text[:15999]
#     try:
#         prompt = f"""You are text summarizer who is expert at performing Extreme TLDR generation for given text.
#         Extreme TLDR is a form of extreme summarization, which performs high source compression, removes stop words and
#         summarizes the text whilst retaining meaning. The result is the shortest possible summary that retains all of
#         the original meaning and context of the text.
#         text for Extreme TLDR generation : {text}
#         Extreme TLDR : """
#         # print(prompt)
#         try:
#             response = openai.ChatCompletion.create(
#             model=gpt_model_name,
#             messages=[
#                     {"role": "system", "content": "You are an expert in generating summaries for legal documents."},
#                     {"role": "user", "content":prompt }
#                 ],
#             temperature = 0.2
#             )
#             summary = response['choices'][0]['message']['content']
#             return summary
#
#         #Handle API error here, e.g. retry or log
#         except openai.error.APIError as e:
#             logger.critical(f"OpenAI API returned an API Error")
#             raise openai.error.APIError('OpenAI API returned an API Error')
#         #Handle connection error here
#         except openai.error.APIConnectionError as e:
#             logger.critical(f"Failed to connect to OpenAI API")
#             raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
#         #Handle rate limit error (we recommend using exponential backoff)
#         except openai.error.RateLimitError as e:
#             logger.critical(f"OpenAI API request exceeded rate limit")
#             raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
#         except Exception as e:
#             logger.critical(f'Error : {str(e)}')
#             raise Exception("AI is not available")
#
#     except Exception as ex:
#         logger.critical(f'Generate Summary Unsuccessful: {str(ex)}')
#         return None
#
#

def search_summary(text):
    len_tokens = num_tokens_from_string(text, gpt_model_name)
    if len_tokens > 16000:
        text = text[:15999]
    try:
        prompt = f"""You are text summarizer who is expert at performing Extreme TLDR generation for given text. 
        Extreme TLDR is a form of extreme summarization, which performs high source compression, removes stop words and
        summarizes the text whilst retaining meaning. The result is the shortest possible summary that retains all of 
        the original meaning and context of the text. 
        text for Extreme TLDR generation : {text}
        Extreme TLDR : """
        # print(prompt)
        try:

            summarizer_prompt = ChatPromptTemplate.from_template(prompt)
            summarizer_prompt.format(text=text)
            # chat_llm = ChatMistralAI(mistral_api_key = os.getenv('MISTRAL_API_KEY'))
            chat_llm = ChatOpenAI(model=gpt_model_name, openai_api_key=os.getenv('OPENAI_API_KEY'))
            summarizer_chain = {"text": itemgetter("text")} | summarizer_prompt | chat_llm
            response = summarizer_chain.invoke({'text': text}).content
            return response
        except Exception as ex:
            logger.critical(f'Error: {str(ex)}')
            return None

        # Handle API error here, e.g. retry or log
        # except openai.error.APIError as e:
        #     logger.critical(f"OpenAI API returned an API Error")
        #     raise openai.error.APIError('OpenAI API returned an API Error')
        # #Handle connection error here
        # except openai.error.APIConnectionError as e:
        #     logger.critical(f"Failed to connect to OpenAI API")
        #     raise openai.error.APIConnectionError('Failed to connect to OpenAI API')
        # #Handle rate limit error (we recommend using exponential backoff)
        # except openai.error.RateLimitError as e:
        #     logger.critical(f"OpenAI API request exceeded rate limit")
        #     raise openai.error.RateLimitError('OpenAI API request exceeded rate limit')
        # except Exception as e:
        #     logger.critical(f'Error : {str(e)}')
        #     raise Exception("AI is not available")

    except Exception as ex:
        logger.critical(f'Error: {str(ex)}')
        return None


def delete_vectordb_using_qdrant(vectordb_folder_path):
    return True
    # try:
    #     docsearch = PineconeVectorStore.from_existing_index(
    #         embedding=embed_fn, index_name=index_name, namespace=namespace)
    #     return docsearch
    # except Exception as e:
    #     raise {"error": e}
    # try:

    #     qdrant_client = QdrantClient(
    #         url=os.getenv('qdrant_url'),
    #         prefer_grpc=True,
    #         api_key=os.getenv('api_key'),
    #     )
    #     qdrant_client.delete_collection(collection_name=vectordb_folder_path)
    # except Exception as e:
    #     raise Exception(str(e))
    # return True
