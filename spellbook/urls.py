from django.urls import path
from .views import (complete_section_endpoint, proofread_text,
                    draft_outline_heading, ghsotwriter, translate_text,
                    negotiation_ponts, prompts, revision, explain_5_year, defining_undefine_terms)

urlpatterns = [
    path('spellbook/complete_section/', complete_section_endpoint, name='complete_section'),
    path('spellbook/proofread/', proofread_text, name='proofread'),
    path('spellbook/draft_outline/', draft_outline_heading, name='draft_outline_heading'),
    path('spellbook/ghostwriter/', ghsotwriter, name='ghsotwriter'),
    path('spellbook/translate/', translate_text, name='translate_text'),
    path('spellbook/point_to_negotiation/', negotiation_ponts, name='point_to_negotiation'),
    path('spellbook/prompts/', prompts, name='prompts'),
    path('spellbook/revision/', revision, name='revision'),
    path('spellbook/explain_as_5_year/', explain_5_year, name='explain_5_year'),
    path('spellbook/define_undefine_terms/', defining_undefine_terms, name='explain_5_year'),
]
