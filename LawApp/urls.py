from django.urls import path
from .views import (
    users_view,
    ai_deposition_view,
    ai_simple_search_view,
    ai_general_chat_view,
    user_history,
    ai_coucel_upload_doc_chat_view,
    contract,
    ai_upload_doc_score,
    student_view,
    admin_dashboard,
    ai_drafting_view,
    payment
)


from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="LawGPT",
        default_version='v1.1',
        description="Nate LawGPT",

    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('docs/', schema_view.with_ui(cache_timeout=0), name='schema-json'),
    path("User", users_view.UserData.as_view()),
    path("User/Verification", users_view.verifyEmail),
    path("User/Profile", users_view.profile),
    path("User/login", users_view.LoginView.as_view()),



    path("User/signup", users_view.signup, name='signup'),
    path("User/APIKey", users_view.get_api_key, name='APIKey'),

    path("User/CreationByAdmin", users_view.CreateUserByAdmin),
    path("User/DeletionByAdmin", users_view.delete_user_by_admin),
    path("User/Roles", users_view.userrole, name='userrole'),
    path("User/Bot/GetLatestId", users_view.get_latest_bot_id),
    path("User/Storage", users_view.get_user_storage),
    # path("User/Bot/HistoryAICouncelData", user_history.get_ai_councel_history),
    path("Deposition/generate_topics_for_deposition", ai_deposition_view.generate_topics_for_deposition),
    path("Deposition/generate_question_for_deposition_topics", ai_deposition_view.generate_question_for_deposition_topics),
    path("SemanticSearch/simple_caselaw_search_with_response_and_source", ai_simple_search_view.simple_caselaw_search_with_response_and_source),
    path("SemanticSearch/simple_chatbot", ai_general_chat_view.simple_chatbot),
    path("Generate/generate_Vector_DB",ai_coucel_upload_doc_chat_view.generate_Vector_DB),
    # path("Summarise/summarise_the_uploaded_document",ai_coucel_upload_doc_chat_view.summarise_the_uploaded_document),
    path("Summarise/summarise_the_uploaded_document",ai_coucel_upload_doc_chat_view.summarise_the_uploaded_document),
    path("Extract/extract_contract_clauses",ai_coucel_upload_doc_chat_view.extract_contract_clauses),
    path("SemanticSearch/simple_chatbot_for_uploaded_document",ai_coucel_upload_doc_chat_view.simple_chatbot_for_uploaded_document),
    path("SemanticSearch/caseid",ai_coucel_upload_doc_chat_view.get_case_id),
    path("Search/Summary",ai_coucel_upload_doc_chat_view.getSummary),


    path("Deposition/Userbots",ai_deposition_view.get_deposition_botid),
    path("Deposition/DepositionHistory",ai_deposition_view.get_deposition_history),


    path("SemanticSearch/GeneralChat/Userbot",ai_general_chat_view.get_generalchat_botid),
    path("SemanticSearch/CaseLawChat/Userbot",ai_simple_search_view.get_simplechat_botid),
    path("SemanticSearch/GeneralChat/History",ai_general_chat_view.get_general_chat_history),
    path("SemanticSearch/CaseLawChat/History",ai_simple_search_view.get_simplechat_history), 




    path("UploadDocument/Userbot",ai_coucel_upload_doc_chat_view.get_user_bot_uploded_doc),
    path("UploadDocument/History",ai_coucel_upload_doc_chat_view.get_uploaded_doc_data),



    path("Search/contract_review_automation",contract.review_contract_compliance),
    path("Search/contract_compliance",contract.contract_compliance),


    path("UploadDocument/Score/searchAndGetScoresFromVectorDBs",ai_upload_doc_score.searchAndGetScoresFromVectorDBs),
    path("UploadDocument/Score/convertFilesIntoVectorDB",ai_upload_doc_score.convertFilesIntoVectorDB),
    path("UploadDocument/Score/Userbot",ai_upload_doc_score.get_score_botid),
    path("UploadDocument/Score/History",ai_upload_doc_score.get_score_history),


    path("Student/AddUser",student_view.student_signup),
    path("Student/UploadDocument",student_view.UploadDocument),
    path("Student/GetList",student_view.get_student_list),
    path("Student/ApproveList",student_view.approved_st_list),
    path("Student/Request",student_view.student_request),
    path("Student/RejectedStudent",student_view.rejected_students),
    path("Student/RestoreRejectedStudents",student_view.restore_student),





    path("Drafting/GetDraft",ai_drafting_view.get_drafts),
    path("Drafting/GenerateHeading",ai_drafting_view.getHeadings),
    path("Drafting/GenerateSuggestion",ai_drafting_view.getHeadingsSuggestion),
    path("Drafting/GenerateHeadingContent",ai_drafting_view.getHeadingsContent),
    path("Drafting/Community",ai_drafting_view.community),
    path("Drafting/insert_into_community",ai_drafting_view.insert_into_community),
    path("Drafting/GetContent",ai_drafting_view.getContent),
    path("Drafting/GetTemplateContent",ai_drafting_view.templateContent),
    path("Drafting/DeleteFile",ai_drafting_view.delete_community_bit),
    path("Drafting/SaveTemplate",ai_drafting_view.saveTemplate),
    path("Drafting/Userbot",ai_drafting_view.get_draft_userdata),
    path("Drafting/History",ai_drafting_view.get_draft_history),
    path("Drafting/GetCommunityList",ai_drafting_view.get_community_list),
    path("Drafting/ReplaceMissingValues",ai_drafting_view.replaceMissingValues),


    # path("Drafting/UpdatedSuggestion",ai_drafting_view.getSuggestion),
    # path("Drafting/convertDocxHTML",ai_drafting_view.convertDocx2HTML),
    # path("Drafting/uploadAndConvertDocxHTML",ai_drafting_view.uploadAndConvertDocx2HTML),



    # path("Payment", payment.create_customer,name="payment"),
    path("Payment/Cancel", payment.cancel_subscribe,name="cancel_subscribe"),
    path("Payment/GetToken", payment.get_token,name="getToken"),
    path("Payment/EditCardInfo", payment.edit_card_info,name="editInfo"),
    path("Payment/GetAllProduts", payment.get_all_prod,name="getAllProd"),
    path("Payment/UpgradeDowngradePackage", payment.downgrade_upgrade,name="downgrade_upgrade_package"),


    path("Admin/Dashboard",admin_dashboard.user_dashboard_data),
    path("Admin/Dashboard/Charts",admin_dashboard.charts),
    path("Admin/Dashboard/mainCharts",admin_dashboard.main_charts),


    path("Search/FetchCasesFromDB", users_view.fetchCasesFromDb),
    path("Search/getDataFromCaseId", ai_simple_search_view.get_data_from_case_id),
    path("Deposition/DepositionChatBot", users_view.deposition_chatbot),


    # path("Fresh/", lobby, name='signup'),
    # path("Fresh/", lobby, name='signup'),

    path("Drafting/Approved", ai_drafting_view.case_approved),
    path("Search/BrowseCases", users_view.browseCases),
    path("User/forgetPassword", users_view.forgetpassword),
    path("User/forgetEmail", users_view.sendForgetEmail),
    path("User/VerifyTheToken", users_view.verifyTheToken),
    path("User/checkQueryRecord", users_view.check_user_query),
    path("User/UpdateUserPassword", users_view.UpdateUserPassword),
    path("User/checkLogs", users_view.check_user_logs),
    path("User/updateTwoFactorToggle", users_view.updateTwoFactorToggle),
    path("User/resendToken", users_view.resend_token),
    path("User/updateFreeTrail", users_view.update_free_trail),
    path("User/buyPackageQueryDoc", payment.buyQueryDocPackage),
    path("qdrant/deleteQdrantCollections", ai_drafting_view.del_collection),

]

