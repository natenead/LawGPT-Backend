import openai
import os
import tempfile
import time

from langchain.chains import ConversationChain
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

load_dotenv()

open_api_key = os.getenv("openAIAPI")


def complete_section(file):
    """
    Completes the content for a section based on the provided text.

    Args:
    - file (str): The input text for the section.

    Returns:
    - str or None: Completed section content or None if an error occurs.
    """
    try:
        tokens = file.split()
        # Count the total number of tokens
        total_tokens = len(tokens)
        # Set the target number of tokens to 6000
        target_tokens = 1000
        # Ensure that we don't exceed the total number of tokens
        start_index = max(len(tokens) - target_tokens, 0)
        # for heading of section
        approx_start_index = max(len(tokens) - 10, 0)
        # Trim tokens from the beginning to have a total of 600 tokens from the last
        trimmed_tokens = tokens[start_index:]
        approc_section_trimmed_tokens = tokens[approx_start_index:]
        # Join the tokens to form the final preprocessed text
        preprocessed_text = ' '.join(trimmed_tokens)
        section_approx_text = ' '.join(approc_section_trimmed_tokens)

        prompt = ChatPromptTemplate.from_template('''You are a section creator. Your task is to create content for the section given in 
        the text {section} based on the context {context}. You have the following tasks:
        1) Evaluate the text, If the text isn't related to law, respond with 'Please provide text related to law.'.
        2) Create content for that section {section}, it should only be strings with good english. There should be no special 
        chracters or space lines.
        3) Your response should start from the previous point and produce 1 or 2 more sections after that section. Do not include 
        anything else. This is your task!
        4) Output only the response information without additional information.''')

        model = ChatOpenAI(
            model='gpt-4-turbo',
            temperature=0.7,
            openai_api_key=open_api_key
        )
        output_parser = StrOutputParser()

        chain = (prompt | model | output_parser)

        response = chain.invoke({"section": section_approx_text, "context": preprocessed_text})
        return response
    except Exception as e:
        print("Error in complete_section function:", e)
        return None


def proofread(file):
    """
    Proofreads the legal text for errors.

    Args:
    - file (str): The legal text to be proofread.

    Returns:
    - str or None: Proofread version of the text or None if an error occurs.
    """
    # If the text
    #     isn't related to law, respond with 'Please provide text related to law.' Output only the translated version without additional
    #     information.
    try:
        prompt = ChatPromptTemplate.from_template('''You are a proofreader for legal text. You will be provided with legal statements. 
        Evaluate the text, if it is a legal related text than move on else return 'Please provide text related to law'. Revise the text 
        provided to you and make changes if required. Only return the modified text. 
        text : {text}''')
        model = ChatOpenAI(
            model='gpt-4o',
            temperature=0.9,
            openai_api_key=open_api_key
        )
        output_parser = StrOutputParser()

        chain = prompt | model | output_parser
        response = chain.invoke({"text": file})
        return response
    except Exception as e:
        print("Error in proofread function:", e)
        return None


def translate(file, language):
    """
    Translates the legal text into the specified language.

    Args:
    - file (str): The legal text to be translated.
    - language (str): The target language for translation.

    Returns:
    - str or None: Translated version of the text or None if an error occurs.
    """
    try:
        prompt = ChatPromptTemplate.from_template('''You are a translator for legal text. Translate the legal text {text} into particular 
        language {language}. If the text isn't related to law, respond with 'Please provide text related to law.' Output only the translated version without 
        additional information.''')
        model = ChatOpenAI(
            model='gpt-4o',
            temperature=0.7,
            openai_api_key=open_api_key
        )
        output_parser = StrOutputParser()

        chain = (prompt | model | output_parser)

        response = chain.invoke({"text": file, "language": language})
        return response
    except Exception as e:
        print("Error in translate function:", e)
        return None


def points_to_negotiate(file, user_prompt):
    """
    Identifies and explains potential negotiation strategies to improve the legal outcome.

    Args:
    - file (str): The legal text to be analyzed.
    - user_prompt (str): Additional instructions or prompts from the user.

    Returns:
    - str or None: Potential negotiation strategies or None if an error occurs.
    """
    try:
        prompt = ChatPromptTemplate.from_template('''You are a legal negotiation strategist analyzing a text {text}. 

        **Goal:** Identify and explain potential negotiation strategies to improve the legal outcome. 

        **Analysis:** 
        * Consider the legal strengths and weaknesses. 
        * Look for indicators of leverage, concessions, trade-offs, and alternative offers. 

        **Output:** Provide potential negotiation strategies that could benefit. Your output should be in the form of list (no more than 4 points) and
        each point in list should not be more than 2 sentences. 

        If the text isn't related to law, respond with 'Please provide text related to law.' Moreover, do not include unnecessary information such as 
        text is related to law. 
        Moreover, user can modify the prompt. If user gives any instructions, kindly prioritize them. User prompt: {user_prompt}. 
        ''')

        model = ChatOpenAI(
            model='gpt-4o',
            temperature=0.9,
            openai_api_key=open_api_key
        )
        output_parser = StrOutputParser()

        chain = (prompt | model | output_parser)

        response = chain.invoke({"text": file, "user_prompt": user_prompt})
        return response
    except Exception as e:
        print("Error in points_to_negotiate function:", e)
        return None


def explain_for_5_year_old(file):
    """
    Explains legal text as if explaining to a 5 year old kid.

    Args:
    - file (str): The legal text to be explained.

    Returns:
    - str or None: Explained text or None if an error occurs.
    """
    try:
        prompt = ChatPromptTemplate.from_template('''You are a legal text reader. Your task is to explain text {text} as if explaining to a 
        5 year old kid. If the text isn't related to law, respond with 'Please provide text related to law.' Output only the translated version without 
        additional information.''')
        model = ChatOpenAI(
            model='gpt-4o',
            temperature=0.7,
            openai_api_key=open_api_key
        )
        output_parser = StrOutputParser()

        chain = (prompt | model | output_parser)

        response = chain.invoke({"text": file})
        return response
    except Exception as e:
        print("Error in explain_for_5_year_old function:", e)
        return None


def define_undefine_terms(file):
    """
    Defines legal terms present in the text.

    Args:
    - file (str): The text containing legal terms.

    Returns:
    - str or None: Defined legal terms or None if an error occurs.
    """
    try:
        prompt = ChatPromptTemplate.from_template('''You are a legal term reader. Your task is to define terms in {text}.
        You need to do the above functionality only if you think that {text} is related to legal documents or any kind of law etc, If you are 
        confident (score above 20%) than perform the above functionality. Otherwise, respond with 'Please provide text related to law.' Output only the defined text without 
        additional information.''')
        model = ChatOpenAI(
            model='gpt-4o',
            temperature=0.9,
            openai_api_key=open_api_key
        )
        output_parser = StrOutputParser()

        chain = (prompt | model | output_parser)

        response = chain.invoke({"text": file})
        return response
    except Exception as e:
        print("Error in define_undefine_terms function:", e)
        return None


def user_prompts(file, prompts):
    """
    Provides responses to user prompts based on the input text.

    Args:
    - file (str): The input text.
    - prompts (str): Prompts or instructions for generating responses.

    Returns:
    - str or None: Generated responses or None if an error occurs.
    """
    try:
        prompt = ChatPromptTemplate.from_template('''{prompts}. Your task is to give response for {text} according
        to prompt {prompts}. If the text isn't related to law, respond with 'Please provide text related to law.' Output only the translated version without 
        additional information.''')
        model = ChatOpenAI(
            model='gpt-3.5-turbo-1106',
            temperature=0.7,
            openai_api_key=open_api_key
        )
        output_parser = StrOutputParser()

        chain = (prompt | model | output_parser)

        response = chain.invoke({"text": file, "prompts": prompts})
        return response
    except Exception as e:
        print("Error in user_prompts function:", e)
        return None


def prompt_compose_content(statement, text):
    """
    Composes content based on a given statement and text.

    Args:
    - statement (str): The statement to be evaluated and responded to.
    - text (str): The text to be evaluated for context.

    Returns:
    - str or None: Composed content based on the statement and text or None if an error occurs.
    """
    try:
        prompt_template = """You are a legal text reader. Your task is to evaluate the given text {text} and a statement {statement} keeping the text
        in context, generate content for the given statement. The content should not be less than 5 sentences. 
        You need to do the above functionality only if you think that {text} is related to legal documents or any kind of law etc, If you are confident (score above 20%) 
        than perform the above functionality. Otherwise, respond with 'Please provide text related to law.' Output only the defined text without 
        additional information.

         text paragraphs: {text}
         statement: {statement}
         Answer:
         """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        model = ChatOpenAI(openai_api_key=open_api_key, model_name='gpt-4-turbo', temperature=0.9)
        output_parser = StrOutputParser()
        chain = prompt | model | output_parser
        text_data = text
        res = chain.invoke({"statement": statement, "text": text})
        return res
    except Exception as e:
        print("Error in prompt_compose_content function:", e)
        return None


def chain_ghost_writer(query):
    """
    Writes detailed content based on a provided topic.

    Args:
    - query (str): The topic for which content is to be written.

    Returns:
    - str or None: Detailed content based on the topic or None if an error occurs.
    """
    try:
        prompt_template = '''You are a ghostwriter for legal text. As a ghostwriter you will be provided a {topic} about which you have to write 
        content. The content should not be less than 300 words. Write detailed content and put headings where required. If the topic isn't related
        to law, respond with "Please provide text related to law." '''
        prompt = ChatPromptTemplate.from_template(prompt_template)
        model = ChatOpenAI(model_name='gpt-4o', temperature=0.9, max_tokens=2000, openai_api_key=open_api_key)
        output_parser = StrOutputParser()
        chain = prompt | model | output_parser
        result = chain.invoke({"topic": query})
        return result
    except Exception as e:
        print("Error in chain_ghost_writer function:", e)
        return None


def revise(text):
    """
    Revises legal text provided for proofreading and makes changes if required.

    Args:
    - text (str): The legal text to be revised.

    Returns:
    - str or None: The revised legal text or None if an error occurs.
    """
    try:
        prompt_template = '''You are a proofreader for legal text. You will be provided with legal statements. 
        Evaluate the text, if it is a legal related text than move on else return 'Please provide text related to law'. Revise the text 
        provided to you and make changes if required. Only return the modified text. 
        text : {text}
        '''
        prompt = ChatPromptTemplate.from_template(prompt_template)
        model = ChatOpenAI(openai_api_key=open_api_key, model_name='gpt-4o', temperature=0.9)
        output_parser = StrOutputParser()
        chain = prompt | model | output_parser
        result = chain.invoke({"text": text})
        print("REVISED=", result)
        return result
    except Exception as e:
        print("Error in revise function:", e)
        return None
