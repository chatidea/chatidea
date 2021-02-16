import logging

from nltk import edit_distance

logger = logging.getLogger(__name__)


def get_dict(*variables):
    return {var_name(s=s): s for s in variables}


def var_name(**variables):
    return list(variables.keys())[0]


KEY_QUERY = 'query'
KEY_QUERY_STRING = 'q_string'
KEY_QUERY_TUPLE = 'q_tuple'
KEY_ACTION_DESCRIPTION = 'action_description'
KEY_VALUE = 'value'
KEY_BY_VALUE = 'by_value'
KEY_REAL_VALUE_LENGTH = 'real_value_length'


def extract_similar_value(keyword, keyword_list, threshold=5):
    winner = None
    if keyword:
        if keyword in keyword_list:
            winner = keyword
        else:
            logger.info('I will compute some similarity distance '
                        'for the received element "{}"...'.format(keyword))
            sim = 100  # very high number
            for el_name in keyword_list:
                received = keyword
                cur = edit_distance(el_name, received)
                if cur < sim and cur < threshold:
                    sim = cur
                    winner = el_name
            logger.info('...I decided on: {}, with similarity distance: {}'.format(winner, sim))
    return winner

