import datetime
import threading
from pprint import pformat

from modules import conversation
from modules import actions
from settings import INTENT_CONFIDENCE_THRESHOLD, CONTEXT_PERSISTENCE_SECONDS
import re

context_dict = {}

lock = threading.Lock()


def run_action_from_parsed_message(parsed_message, chat_id):

    intent_confidence = parsed_message.get('intent').get('confidence')
    intent_name = parsed_message.get('intent').get('name')

    intent_name = re.sub('_el_\d', '', intent_name)
    entities = parsed_message.get('entities')

    if intent_confidence < INTENT_CONFIDENCE_THRESHOLD:
        intent_name = None

    context = get_context(chat_id)

    context.log('New message received!\n'
                'Original message: {}\n'
                'Intent matched: {}\n'
                'Entities:\n'
                '{}'.format(parsed_message['original_message'],
                            intent_name,
                            pformat(entities)))
   
    return actions.execute_action_from_intent_name(intent_name, entities, context)


def get_context(chat_id):

    lock.acquire()

    #check_timestamps()

    # conversation was already defined
    if context_dict.get(chat_id):

        update_timestamp(chat_id)
        context = context_dict[chat_id]['context']

    else:

        context = conversation.Context(chat_id)
        context_dict[chat_id] = {'context': context}
        update_timestamp(chat_id)

        # schedule_delete_event(chat_id)

    lock.release()

    return context


def check_timestamps():

    max_age = datetime.datetime.now() - datetime.timedelta(seconds=CONTEXT_PERSISTENCE_SECONDS)

    for k, v in list(context_dict.items()):
        if v['timestamp'] < max_age:
            del context_dict[k]


def update_timestamp(chat_id):
    context_dict[chat_id]['timestamp'] = datetime.datetime.now()
