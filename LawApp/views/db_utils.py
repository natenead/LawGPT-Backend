from ..models import *
import yake
from django.db import connection
from django.db.models import Q
import random


def main(id_string):
    data = Main.objects.filter(case_id__in=id_string)
    my_list = list()
    url_dict = dict()
    url_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = getattr(i, 'case_id')
        my_dict["Name"] = getattr(i, 'name')
        my_dict["NameAbbreviation"] = getattr(i, 'name_abbreviation')
        my_dict["DecisionDate"] = getattr(i, 'decision_date')
        my_dict["DocketNumber"] = getattr(i, 'docket_number')
        my_dict["FrontendURL"] = getattr(i, 'frontend_pdf_url')
        my_dict["ReporterID"] =getattr(i, 'reporter_id')
        my_dict["CourtID"] = getattr(i, 'court_id')
        my_dict["JurisdictionID"] = getattr(i, 'jurisdiction_id')
        url_dict[my_dict["CaseID"]] = my_dict["FrontendURL"]

        my_list.append(my_dict)
    url_list.append(url_dict)
    return my_list,url_list


# Extracting data from citation Table
def citation(id_string):
    data = Citation.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = getattr(i, 'case_id')
        my_dict["Cite"] = getattr(i, 'cite')
        my_dict["Type"] = getattr(i, 'type')

        my_list.append(my_dict)
    return my_list


# Extracting data from cites_to Table
def cites_to(id_string,url_list):
    new_list = list()
    data = CitesTo.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = getattr(i, 'case_id')
        if my_dict["CaseID"] in new_list:
            continue
        new_list.append(my_dict["CaseID"])
        # my_dict['cite_url'] = Main.objects.get(case_id=my_dict["CaseID"]).frontend_pdf_url
        my_dict['cite_url'] = url_list[0][my_dict["CaseID"]]
        my_dict["Cite"] = getattr(i, 'cite')
        my_dict["Category"] = getattr(i, 'category')
        my_dict["Reporter"] = getattr(i, 'reporter')
        my_dict["Year"] = getattr(i, 'year')
        my_dict["OpinionID"] = getattr(i, 'opinion_id')

        my_list.append(my_dict)
    return my_list


# Extracting data from casebody Table
def casebody(id_string):
    data = Casebody.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = getattr(i, 'case_id')
        my_dict["HeadMatter"] = getattr(i, 'head_matter').replace('\n', '<br/>')
        my_dict["Corrections"] =getattr(i, 'corrections')

        my_list.append(my_dict)
    return my_list


# Extracting data from opinion Table
def opinion(id_string):
    data = Opinion.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = getattr(i, 'case_id')
        my_dict["OpinionText"] = getattr(i, 'opinion_text').replace('\n', '<br/>')
        my_dict["OpinionType"] = getattr(i, 'opinion_type')
        my_dict["OpinionAuthor"] = getattr(i, 'opinion_author')
        my_dict["OpinionID"] = getattr(i, 'opinion_id')

        my_list.append(my_dict)
    return my_list


# Extracting data from attorneys Table
def attorney(id_string):
    data = Attorneys.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = getattr(i, 'case_id')
        my_dict["Attorney"] = getattr(i, 'attorney')

        my_list.append(my_dict)
    return my_list


# Extracting data from court Table
def court(id_string):
    data = Court.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = getattr(i, 'case_id')
        my_dict["CourtID"] = getattr(i, 'court_id')
        my_dict["CourtName"] = getattr(i, 'court_name')
        my_dict["CourtNameAbbreviation"] = getattr(i, 'court_name_abbreviation')

        my_list.append(my_dict)
    return my_list



def court_data(id_string,data):
    condition = Q()
    k = random.randint(30, 50)
    for states in data:
        condition |= Q(court_name__contains=states.lower())
        condition |= Q(court_name__contains=states.capitalize())
        condition |= Q(court_name__contains=states)
    data = Court.objects.filter(case_id__in=id_string).filter(condition)[:k]

    my_list = list()
    new_id_string = list()
    for i in data:
        my_dict = {}
        my_dict["CaseID"] = getattr(i, 'case_id')
        new_id_string.append(getattr(i, 'case_id') )
        my_dict["CourtID"] = getattr(i, 'court_id')
        my_dict["CourtName"] = getattr(i, 'court_name')
        my_dict["CourtNameAbbreviation"] = getattr(i, 'court_name_abbreviation')

        my_list.append(my_dict)
    return my_list,new_id_string

# Extracting data from judges Table
def judges(id_string):
    data = Judges.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = getattr(i, 'case_id')
        my_dict["Judge"] = getattr(i, 'judge')

        my_list.append(my_dict)
    return my_list


# Extracting data from jurisdiction Table
def jurisdiction(id_string):
    data = Jurisdiction.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] =  getattr(i, 'case_id')
        my_dict["jurisdictionID"] = getattr(i, 'jurisdiction_id')
        my_dict["jurisdictionName"] =  getattr(i, 'jurisdiction_name')
        my_dict["jurisdictionNameAbbreviation"] =  getattr(i, 'jurisdiction_name_abbreviation')

        my_list.append(my_dict)
    return my_list


# Extracting data from parties Table
def parties(id_string):
    data = Parties.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] =  getattr(i, 'case_id')
        my_dict["Parties"] = getattr(i, 'party')

        my_list.append(my_dict)
    return my_list


# Extracting data from reporter Table
def reporter(id_string):
    data = Reporter.objects.filter(case_id__in=id_string)

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] =  getattr(i, 'case_id')
        my_dict["ReporterID"] =  getattr(i, 'reporter_id')
        my_dict["ReporterName"] =  getattr(i, 'reporter_name')

        my_list.append(my_dict)
    return my_list


# Extracted Data from the db based on the given ID.
def extract_data_from_db(id_string):
    main_rows,url_list = main(id_string)
    citation_rows = citation(id_string)
    cites_to_rows = cites_to(id_string,url_list)
    casebody_rows = casebody(id_string)
    opinion_rows = opinion(id_string)
    attorney_rows = attorney(id_string)
    court_rows = court(id_string)
    judges_rows = judges(id_string)
    jurisdiction_rows = jurisdiction(id_string)
    parties_rows = parties(id_string)
    reporter_rows = reporter(id_string)

    return main_rows, cites_to_rows, citation_rows, casebody_rows, opinion_rows, attorney_rows, court_rows, judges_rows, jurisdiction_rows, parties_rows, reporter_rows

def search_keywords_in_cites_to(query):
    # query = f"SELECT case_id, cite FROM cites_to WHERE cite ILIKE '%{query}%';"
    queryset = CitesTo.objects.values_list("case_id", "cite").filter(cite__contains=query)

    try:
        case_id_list= []
        if not queryset:
            return []
        else:
            for result in queryset:
                case_id_list.append(result[0])
        return case_id_list
    except Exception as e:
        print(f"Error executing the query: {e}")

# def search_keywords_in_opinion(query):
#     # max_keywords= 2
#     # kw_extractor = yake.KeywordExtractor(top=10, stopwords=None)
#     # keywords = kw_extractor.extract_keywords(query)
#     # top_keywords = sorted(keywords, key=lambda x: x[1], reverse=True)[:max_keywords]
#     # case_id_list= []
#     # try:
#     #     keyword_strings = tuple(kw[0] for kw in top_keywords)
#     #     keywords_pipe = "|".join(keyword_strings)
#     #     for keyword in top_keywords:
#     #         # query = f"SELECT case_id, opinion_text FROM opinion WHERE opinion_text ILIKE '%{keyword[0]}%' LIMIT 5;"
#     #         queryset = Opinion.objects.values_list("case_id", "opinion_text").filter(opinion_text__icontains=keywords_pipe[0])[:5]
#     #
#     #         for result in queryset:
#     #             case_id_list.append(result[0])
#     #     return case_id_list
#     # except Exception as e:
#     #     print(f"Error executing the query: {e}")
#
#     # start_time = time.time()
#     max_keywords = 10
#     kw_extractor = yake.KeywordExtractor(top=max_keywords, stopwords=None)
#     keywords = kw_extractor.extract_keywords(query)
#     top_keywords = sorted(keywords, key=lambda x: x[1], reverse=False)[:max_keywords]
#     case_id_set = set()
#     try:
#         # Extract the keyword strings from the top_keywords list
#         keyword_strings = tuple(kw[0] for kw in top_keywords)
#         keywords_pipe = "|".join(keyword_strings)
#
#         # Use a single query with the IN operator and parameterized placeholders
#         # query = f"SELECT DISTINCT case_id FROM opinion WHERE opinion_text  ~* '{keywords_pipe}' LIMIT 30;" 41s, 77s
#         query = f"SELECT case_id FROM opinion WHERE opinion_text  ~* '{keywords_pipe}' LIMIT 50;"
#
#         # Pass the keyword_strings as a tuple to the execute method
#         with connection.cursor() as cursor:
#             cursor.execute(query)
#             results = cursor.fetchall()
#         # Add the case_id values to the set
#         for result in results:
#             case_id_set.add(result[0])
#         # execution_time = time.time() - start_time
#         # print(f"Execution time: {execution_time}")
#         return case_id_set
#     except Exception as e:
#         print(f"Error executing the query: {e}")


def search_keywords_in_opinion(query,title):
    if title == 'true':
        main_data = Main.objects.filter(name__icontains=query).values_list('case_id')
        return [v[0] for v in main_data]
    max_keywords = 5
    kw_extractor = yake.KeywordExtractor(top=max_keywords, stopwords=None)
    keywords = kw_extractor.extract_keywords(query)
    top_keywords = sorted(keywords, key=lambda x: x[1], reverse=False)[:max_keywords]

    try:
        # Extract the keyword strings from the top_keywords list
        # start_time = time.time()
        keyword_list = [f'%{kw[0]}%' for kw in top_keywords]
        case_id_list = []
        # Use a single query with the IN operator and parameterized placeholders
        # query = f"SELECT DISTINCT case_id FROM opinion WHERE opinion_text  ~* '{keywords_pipe}' LIMIT 30;" 41s, 77s
        # query = f"SELECT case_id FROM opinion WHERE opinion_text  ~* '{keywords_pipe}' LIMIT 50;"
        for case_kw in keyword_list:
            # from django.contrib.postgres.search import SearchVector, SearchQuery

            # query = SearchQuery('family law issue', config='english')
            # vector = SearchVector('opinion_text', config='english')
            # results = OpinionData.objects.annotate(search=vector).filter(search=query)[:10]

            query = f"SELECT case_id FROM opinion WHERE to_tsvector('english', opinion_text) @@ to_tsquery('english', '''{case_kw}''') LIMIT 10000;"
            # Pass the keyword_strings as a tuple to the execute method
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
            # Add the case_id values to the set
            for result in results:
                case_id_list.append(result[0])
        # execution_time = time.time() - start_time
        # print(f"Execution time: {execution_time}")
        return case_id_list,keyword_list
    except Exception as e:
        raise e
        # print(f"Error executing the query: {e}")




def search_keywords_in_main(query):
    # query = f"SELECT case_id, name_abbreviation FROM main WHERE name_abbreviation ILIKE '%{query}%';"
    queryset = Main.objects.values_list("case_id", "name_abbreviation").filter(name_abbreviation__contains=query)

    try:

        case_id_list= []
        if not queryset:
            return []
        else:
            for result in queryset:
                case_id_list.append(result[0])
        return case_id_list
    except Exception as e:
        print(f"Error executing the query: {e}")


def browse_state_cases(state, cursor):
    case_id_list= []
    try:
        query = f"SELECT case_id FROM jurisdiction WHERE jurisdiction_name='{state}';"
        cursor.execute(query)
        results = cursor.fetchall()
        result_year_list=[]
        for result in results:
            case_id_list.append(result[0])
        case_id_tuple= tuple(case_id_list)
        query_year = f"SELECT decision_date FROM main WHERE case_id IN {case_id_tuple};"
        cursor.execute(query_year)
        results_year = cursor.fetchall()

        for result in results_year:
            if result[0]:
                result_year_list.append(int(result[0].split("-")[0]))
        result_year_set = set(result_year_list)
        result_year_list= list(result_year_set)
        return result_year_list
    except Exception as e:
        print(f"Error executing the query: {e}")


def browse_state_year_cases(state, year, cursor):
    case_id_list= []
    try:
        query = f"SELECT case_id FROM jurisdiction WHERE jurisdiction_name='{state}';"
        cursor.execute(query)
        results = cursor.fetchall()
        for result in results:
            case_id_list.append(result[0])
        case_id_tuple= tuple(case_id_list)
        if len(case_id_tuple)==1:
            query_year_cases = f"SELECT case_id, name_abbreviation FROM main WHERE case_id='{case_id_tuple[0]}' AND decision_date LIKE '{year}%';"
        else:
            query_year_cases = f"SELECT case_id, name_abbreviation FROM main WHERE case_id IN {case_id_tuple} AND decision_date LIKE '{year}%';"
        cursor.execute(query_year_cases)
        results_year_cases = cursor.fetchall()
        results_year_cases_list=[]
        for result in results_year_cases:
                dict_sample= {
                    'CaseID': result[0],
                    'case': result[1]
                }
                results_year_cases_list.append(dict_sample)
        return results_year_cases_list
    except Exception as e:
        print(f"Error executing the query: {e}")


def browse_cases_from_case_name(case_name, cursor):
    case_id_list= []
    try:
        query = f"SELECT case_id FROM main WHERE name_abbreviation='{case_name}';"
        cursor.execute(query)
        results = cursor.fetchall()
        for result in results:
            case_id_list.append(result[0])
        return case_id_list
    except Exception as e:
        print(f"Error executing the query: {e}")

def optimized_casebody(cursor, id_string):
    query = f"SELECT case_id, head_matter FROM casebody WHERE case_id IN ({id_string})"
    cursor.execute(query)
    data = cursor.fetchall()

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = i[0]
        my_dict["HeadMatter"] = i[1]

        my_list.append(my_dict)
    return my_list

def optimized_main(cursor, id_string):
    query = f"SELECT case_id, name_abbreviation FROM main WHERE case_id IN ({id_string})"
    cursor.execute(query)
    data = cursor.fetchall()

    my_list = list()

    for i in data:
        my_dict = {}
        my_dict["CaseID"] = i[0]
        my_dict["NameAbbreviation"] = i[1]
        my_list.append(my_dict)
    return my_list

def updated_extract_data_from_db(id_string,opinion_list, cursor):
    main_rows = optimized_main(cursor, id_string)
    citation_rows = citation(opinion_list)
    casebody_rows = optimized_casebody(cursor, id_string)
    return main_rows, citation_rows, casebody_rows



def extract_keyword_data_from_db(id_string,data):
    court_rows,id_string = court_data(id_string,data)
    main_rows,url_list = main(id_string)
    citation_rows = citation(id_string)
    cites_to_rows = cites_to(id_string,url_list)
    casebody_rows = casebody(id_string)
    opinion_rows = opinion(id_string)
    attorney_rows = attorney(id_string)

    judges_rows = judges(id_string)
    jurisdiction_rows = jurisdiction(id_string)
    parties_rows = parties(id_string)
    reporter_rows = reporter(id_string)

    return main_rows, cites_to_rows, citation_rows, casebody_rows, opinion_rows, attorney_rows, court_rows, judges_rows, jurisdiction_rows, parties_rows, reporter_rows,id_string
