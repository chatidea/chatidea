import logging

from rasa.nlu import model as nlu_model
from settings import NLU_MODEL_PATH

logger = logging.getLogger(__name__)

inter = None


def load_model():
    global inter
    logger.info('NLU model:\n'
                '"' + NLU_MODEL_PATH + '"')
    logger.info('Loading the NLU model WITHOUT training...')
    inter = nlu_model.Interpreter.load(NLU_MODEL_PATH)
    logger.info('NLU model loaded!')


def parse(message):
    """
    Gives result in the form:
    {
        'intent': {'name': 'find_teacher_by_word', 'confidence': 0.9642855525016785},
        'entities': [
            {'value': 'Nicola', 'entity': 'word'}
        ]
        'original_message': 'find the teacher Nicola'
    }
    :param message: the message to be converted
    :return: the dictionary representing the interpretation
    """

    logger.info('Message to parse: "{}"'.format(message))

    if message.startswith('/'):
        parsed_message = dict()
        message = message[1:]
        split_message = message.split('{', 1)
        intent_name = split_message[0]
        entities = []
        #added for autocomplete buttons
        if(intent_name == 'find_el_by_attr'):
            for el in split_message:
                splitted_el = el.split(':', 1)
                if len(splitted_el) > 1:
                    return(parse(splitted_el[1].replace('"', "").replace('}', "")))
        if len(split_message) > 1:  # if there are entities
            entity_list = split_message[1].split(';')
            for i, e in enumerate(entity_list):
                import re
                matches = re.findall(r'.*(?:\"|\')(.+?)(?:\"|\'):.*(?:\"|\')(.+?)(?:\"|\').*', e)
                entities.append({'entity': matches[0][0], 'value': matches[0][1], 'start': i+1})

        parsed_message['intent'] = {'name': intent_name, 'confidence': 1}
        parsed_message['entities'] = entities
    else:
        message = message.lower()
        parsed_message = inter.parse(message)
        for intent in parsed_message['intent_ranking']:
            if intent['confidence'] > 0.3:
                print("Name: " + intent['name'] + " ---- Confidence: "+ str(intent['confidence']))
        del parsed_message['text']
        for e in parsed_message.get('entities'):
            # del e['start']
            del e['end'], e['confidence'], e['extractor']
            if e.get('processors'):
                del e['processors']

    parsed_message['original_message'] = message
    print(parsed_message)

    logger.info('Parsed message: {}'.format(parsed_message))
    return parsed_message

