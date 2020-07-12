import os

from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions

WATSON_APIKEY = os.environ.get('WATSON_APIKEY')

# IBM Authentication
authenticator = IAMAuthenticator(WATSON_APIKEY)
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2019-07-12',
    authenticator=authenticator
)

# Functions


def fn_ibm_nlu(analyze_text, reqd_limit=20):
    response = natural_language_understanding.analyze(
        text=analyze_text,
        features=Features(
            #entities=EntitiesOptions(emotion=False, sentiment=False, limit=reqd_limit),
            keywords=KeywordsOptions(emotion=False, sentiment=False, limit=reqd_limit))).get_result()
    return response


# Send text to Watson API and cache response for future use
def fn_analyze_text_nlu(text):
    try:
        res = fn_ibm_nlu(text)
    except:
        res = {'usage': {'text_units': 0, 'text_characters': 0, 'features': 0},
               'language': 'Error', 'keywords': [], 'entities': []}
    return res


# Extract Required components from Watson's Response
def fn_extract_watson_response(watson_response, cutoff=0.6):
    results = {'keywords': [], 'entities': []}
    for ind_topic in ['keywords']:
        for ind_topic_entity in watson_response[ind_topic]:
            if ind_topic_entity['relevance'] > cutoff:
                results.setdefault(ind_topic, []).append(ind_topic_entity['text'])
    return results


def get_keywords(watson_response, cutoff=0.6):
    res_extract = fn_extract_watson_response(watson_response, cutoff)
    return res_extract['keywords']
