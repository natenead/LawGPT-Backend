from .general_utils import *

from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_section_endpoint(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        text = request.query_params.get('text')
        section = complete_section(text)
        time.sleep(5)

        return Response(
            {'section': section},
            status=status.HTTP_200_OK
        )
    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def proofread_text(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        text = request.query_params.get('text')
        proofreadedText = proofread(text)
        time.sleep(5)
        return Response(
            {'proofreadedText': proofreadedText},
            status=status.HTTP_200_OK
        )
    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
    openapi.Parameter('query', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def draft_outline_heading(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        text = request.query_params.get('text')
        query = request.query_params.get('query')
        heading_content = prompt_compose_content(query, text)
        time.sleep(5)
        return Response(
            {'draft_outline': heading_content},
            status=status.HTTP_200_OK
        )
    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('query', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ghsotwriter(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        query = request.query_params.get('query')
        ghostWriter = chain_ghost_writer(query)
        time.sleep(5)
        return Response(
            {'ghostWriter': ghostWriter},
            status=status.HTTP_200_OK
        )

    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
    openapi.Parameter('language', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def translate_text(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        text = request.query_params.get('text')
        language = request.query_params.get('language')
        translatedText = translate(text, language)
        time.sleep(5)
        return Response(
            {'proofreadedText': translatedText},
            status=status.HTTP_200_OK
        )
    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
    openapi.Parameter('prompt', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def negotiation_ponts(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        text = request.query_params.get('text')
        prompt = request.query_params.get('prompt')
        translatedText = points_to_negotiate(text, prompt)
        time.sleep(5)
        return Response(
            {'proofreadedText': translatedText},
            status=status.HTTP_200_OK
        )

    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
    openapi.Parameter('prompt', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def prompts(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        text = request.query_params.get('text')
        prompt = request.query_params.get('prompt')
        user_prompt_response = user_prompts(text, prompt)
        time.sleep(5)
        return Response(
            {'user_prompt_response': user_prompt_response},
            status=status.HTTP_200_OK
        )
    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revision(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        text = request.query_params.get('text')
        revisionText = revise(text)
        time.sleep(5)
        return Response(
            {'revisionText': revisionText},
            status=status.HTTP_200_OK
        )

    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_5_year(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        text = request.query_params.get('text')
        translatedText = explain_for_5_year_old(text)
        time.sleep(5)
        return Response(
            {'proofreadedText': translatedText},
            status=status.HTTP_200_OK
        )

    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(method='POST', manual_parameters=[
    openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def defining_undefine_terms(request):
    try:
        # if not request.user.extension_paid:
        #     return Response(
        #         {'message':'Payment Required'},
        #         status=status.HTTP_402_PAYMENT_REQUIRED,
        #     )
        text = request.query_params.get('text')
        define_terms = define_undefine_terms(text)
        time.sleep(5)
        return Response(
            {'define_terms': define_terms},
            status=status.HTTP_200_OK
        )

    except Exception as e:

        return Response(
            {'section': e},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
