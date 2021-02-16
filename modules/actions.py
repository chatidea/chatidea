import copy
import logging
import re
from pprint import pprint
import random
import matplotlib.pyplot as plt
from functools import reduce
from modules import commons
from modules.database import resolver, broker
from modules import patterns
from modules.patterns import btn, msg, nlu
from settings import ELEMENT_VISU_LIMIT, CONTEXT_VISU_LIMIT, ELEMENT_SIMILARITY_DISTANCE_THRESHOLD
from modules import nltrasnslator, autocompleter

logger = logging.getLogger(__name__)


# ENTITIES EXTRACTORS

def extract_entities(entities, entity_name):
    found = []
    for e in entities:
        if e.get('entity').startswith(entity_name):  # el_1 -> el, word_2_4 -> word
            found.append(e)
    return found


def extract_single_entity_value(entities, entity_name):
    found = extract_entities(entities, entity_name)
    if found:
        return found[0]['value']  # the first one
    return None

#takes entities
#for every words gives back a list composed by the word and the attribute that is related to it
def compute_ordered_entity_list(entities):
    ordered_entities = []
    index_previous_attribute = None
    index_previous_entity_number_op = None
    for index, e in enumerate(entities):
        ty = None
        op = '='  # the control of the presence of the OP is made here!
        match = re.match("(\w+)_\d+_(\d+)|el_(columns)", e['entity'])
        if re.match("attr_\d+_\d+", entities[index-1]['entity']):
            index_previous_attribute = entities[index-1]
        elif entities[index-1]['entity'].startswith('op_num'):
            index_previous_entity_number_op = entities[index-1]
        if match:
            what = match.group(1)
            if what == None:
                what = match.group(3)
            if what == nlu.ENTITY_WORD:
                ty = 'word'
                maybe_op = next((a['value'] for a in entities if a['entity'].startswith('op_word')), None)
                if maybe_op and maybe_op.endswith('ne'):
                    op = '<>'
                else:
                    op = 'LIKE'  # here forcing the attribute of type "word" to be LIKE and NOT equal
            elif what == nlu.ENTITY_NUMBER:
                ty = 'num'
                if index_previous_entity_number_op:
                    maybe_op = index_previous_entity_number_op['value']
                else:
                    maybe_op = None
                maybe_op = commons.extract_similar_value(maybe_op, ['less than', 'more than'], 6)
                if maybe_op:
                    if maybe_op == 'less than':
                        op = '<'
                    elif maybe_op == 'more than':
                        op = '>'
                else:
                    op = '='
            elif what == nlu.ENTITY_COLUMNS:
                ty = 'columns'
                op = 'ORDER BY'
        if ty:
            oe = {'type': ty, 'operator': op, 'value': e['value']}
            for index2, e2 in enumerate(entities):
                if index2 == index+1:
                    if e2['entity'] == 'or':
                        oe['and_or'] = 'or'
                    elif re.match('attr_\d+_\d+',e2['entity']) or e2['entity'] == 'and':
                        oe['and_or'] = 'and'
            if ty == 'columns':
                attr = next((a['value'] for a in entities if re.match("order_by", a['entity'])), None)
            else:
                if index_previous_attribute:
                    attr = index_previous_attribute['value']
                else:
                    attr = None
            if attr:
                oe['attribute'] = attr
            ordered_entities.append(oe)
            #entities = entities[entities.index(e)+1:]

    return ordered_entities


# ATTRIBUTES HANDLERS
# this is used to map ordered entities to  right columns (this takes care of the join part in case it's needed)
def get_attributes_from_ordered_entities(element_name, ordered_entities,response):
    attributes = []

    for oe in ordered_entities:

        # if the entity has an attribute, i.e. if it not implied
        if oe.get('attribute'):
            order_by_alias = ['order by','ordered by', 'sort by', 'sorted by']
            keyword_list = [a['keyword'] for a in resolver.extract_attributes_with_keyword(element_name)]
            for alias in order_by_alias:
                keyword_list.append(alias)
            attribute_name = commons.extract_similar_value(oe['attribute'],
                                                           keyword_list,
                                                           ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)

            if attribute_name:
                new_attr = resolver.get_attribute_by_name(element_name, attribute_name)
                if new_attr:
                    attr = new_attr.copy()
                else:
                    attr = None
                if attr == None and attribute_name in order_by_alias:
                    columns = oe['value']
                    columns_element = handle_columns_name_similarity(element_name, columns)
                    if columns_element:
                        oe['value'] = columns_element
                        attr =  {'columns': [columns_element], 'keyword': 'order by', 'operator': 'ORDER BY', 'type': 'columns', 'value': columns_element}
                    else:
                        response.add_message('Sorry, there is no attribute "'+columns+'" for '+element_name)
                        return []
                if attr.get('type') == oe.get('type'):
                    attr['value'] = oe.get('value')
                    if 'and_or' in oe:
                        attr['and_or'] = oe.get('and_or')
                    attr['operator'] = oe.get('operator', '=')  # should not happen
                    attributes.append(attr)

            else:  # if it has an attribute but is not recognized
                return []  # something unwanted just happened -> attribute extracted but not matched

        # if the entity does not have an attribute
        else:
            new_attr = resolver.get_attribute_without_keyword_by_type(element_name, oe.get('type'))
            if new_attr:
                attr = new_attr.copy()
                attr['value'] = oe.get('value')
                if 'and_or' in oe:
                    attr['and_or'] = oe.get('and_or')
                attr['operator'] = oe.get('operator', '=')
                attributes.append(attr)

    return attributes


def get_attributes_string(attributes):
    return ', '.join(('{} '.format(a.get('keyword')) if a.get('keyword') else '')
                              + ('{} '.format(a.get('operator')) if a.get('type') == 'num' else '')
                              + str(a['value']) for a in attributes)


# SIMILARITY HANDLERS

def handle_element_name_similarity(element_name_received):
    all_elements_names = resolver.get_all_primary_element_names_and_aliases()
    similar = commons.extract_similar_value(element_name_received,
                                            all_elements_names,
                                            ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
    if similar:
        return resolver.get_element_name_from_possible_alias(similar)
    return None


def handle_element_relations_similarity(element_name, relation_name_received):
    relations = resolver.extract_relations(element_name)
    all_relations_names = [r['keyword'] for r in relations]
    return commons.extract_similar_value(relation_name_received,
                                         all_relations_names,
                                         ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)

def handle_columns_name_similarity(element_name_alias, columns_name_received):
    displayable_attributes = resolver.simulate_view(element_name_alias)
    attribute_names = [i['attribute'] for i in displayable_attributes if 'attribute' in i]
    displayed_names = [i['display'] for i in displayable_attributes if 'display' in i]
    similar = commons.extract_similar_value(columns_name_received, attribute_names, ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
    if similar:
        return similar
    else:
        similar = commons.extract_similar_value(columns_name_received, displayed_names, ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
        if similar:
            for i in displayable_attributes:
                if i['display'] is similar:
                    return i['attribute']
        else:
            return None


    """element_name = resolver.extract_element(element_name_alias)
    table_name = element_name.get('table_name')
    table_schema = broker.get_table_schema_from_name(table_name)
    all_columns_name = table_schema.get('column_list')
    all_columns_name_alias = table_schema.get('column_alias_list')
    similar = commons.extract_similar_value(columns_name_received, all_columns_name, ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
    if similar:
        return similar
    else:
        if all_columns_name_alias:
            all_columns_name_alias_inv = {v: k for k, v in all_columns_name_alias.items()}
            similar = commons.extract_similar_value(columns_name_received, all_columns_name_alias_inv, ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
            if similar:
                value = all_columns_name_alias_inv.get(similar)
                return value
            else:
                return None
        else:
            return None"""


# RESPONSE HANDLERS

def handle_response_for_quantity_found_element(response, element, context):
    if element['real_value_length'] == 1:
        response.add_message(msg.ONE_RESULT_FOUND)
    else:
        response.add_message(msg.N_RESULTS_FOUND_PATTERN.format(element['real_value_length']))
        if element.get('action_type') != 'filter' and \
                element.get('element_name') in resolver.get_all_primary_element_names():
            response.add_message(msg.REMEMBER_FILTER)
            response.add_button(btn.get_button_filter_hints())
            response.add_button(btn.get_button_history())


# SELECTION HANDLERS

def is_selection_valid(element, position):
    return 0 < position <= len(element['value'])  # element['real_value_length']:


def add_selected_element_to_context(element, position, context):
    # copying the dictionary
    selected_element = dict(element)

    # I must save it as a list
    selected_element['value'] = [element['value'][position - 1]]
    selected_element['query'] = None
    selected_element['real_value_length'] = 1
    selected_element['action_name'] = '...selected from:'
    selected_element['action_type'] = 'select'

    context.append_element(selected_element)

def add_to_context(name, entities, context):
    selected_element = dict()
    selected_element['value'] = "     "
    selected_element['entities'] = entities
    selected_element['query'] = None
    selected_element['real_value_length'] = 777
    selected_element['action_name'] = name
    selected_element['action_type'] = name
    selected_element['element_name'] = name
    context.append_element(selected_element)

def is_value_in_selection_valid(element, position, title):
    # copying the dictionary
    selected_element = dict(element)
    # I must save it as a list
    selected_element['value'] = [element['value'][position - 1]]
    match = resolver.get_element_show_string(selected_element['element_name'],selected_element['value'][0])
    match = clean_title_for_selection(match)
    if match[:29] == title: #29 chars is max title payload
        return True
    else:
        return False

def clean_title_for_selection(title):
    title = msg.cleanhtml(title)
    clean = re.compile('"|;')
    title = re.sub(clean, '', title)
    clean = re.compile("'")
    title = re.sub(clean, '', title)
    title = title.rstrip()
    return title

# ACTIONS

def action_start(entities, response, context, add = True):
    start_message = msg.HI_THERE + "\n" + msg.element_names_examples()
    response.add_message(start_message)
    response.add_buttons(btn.get_buttons_tell_me_more())
    if add:
        add_to_context("start", entities, context)
    else:
        response.add_button(btn.get_button_help_on_elements())
        response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
        response.add_button(btn.get_button_history())


def action_help(entities, response, context):
    response.add_message("For what do you need help?")
    response.add_buttons(btn.get_buttons_help())

def action_help_elements(entities, response, context):
    response.add_message(msg.element_names_examples())
    response.add_buttons(btn.get_buttons_tell_me_more())


def action_help_history(entities, response, context):
    response.add_message(msg.REMEMBER_HISTORY)
    response.add_button(btn.get_button_help_on_elements())


def action_help_go_back(entities, response, context):
    response.add_message(msg.REMEMBER_GO_BACK)
    response.add_button(btn.get_button_help_on_elements())


def action_more_info_find(entities, response, context, add = True):
    element_name = handle_element_name_similarity(extract_single_entity_value(entities, nlu.ENTITY_ELEMENT))
    if element_name:
        if add:
            element = dict()
            element['value'] = 0
            element['element_name'] = 'more_info_find'
            element['element_value'] = element_name
            element['action_name'] = 'more info find'
            element['action_type'] = 'more_info_find'
            element['entities'] = entities
            element['query'] = None
            element['real_value_length'] = 1
            context.append_element(element)

        response.add_message(msg.find_element_examples(element_name))
        #response.add_button(btn.get_button_help_on_elements())
        #response.add_button(btn.get_button_show_more_examples(element_name))
        response.add_button(btn.get_button_show_more_examples(element_name))
        category = resolver.extract_categories(element_name)
        if category:
            response.add_buttons(btn.get_button_show_table_categories(element_name))
        #response.add_button(btn.get_button_help_on_elements())


    else:
        response.add_message('I am sorry, I understood that you want more info, but not on what...')
    response.add_button(btn.get_button_help_on_elements())
        #response.add_message('Remember that you can always go back, just click the button')
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
    response.add_button(btn.get_button_history())


def action_more_info_filter(entities, response, context):
    element_name = handle_element_name_similarity(extract_single_entity_value(entities, nlu.ENTITY_ELEMENT))
    if element_name:
        response.add_message(msg.filter_element_examples(element_name))
    else:
        element = context.get_last_element()
        if element and element['real_value_length'] > 1:
            response.add_message(msg.filter_element_examples(element['element_name']))
        else:
            response.add_message('I am sorry, but there is nothing to filter... You\'d better tell on which element.\n'
                                 'Try, for instance, with "how to filter {}"'
                                 .format(resolver.get_all_primary_element_names()[0]))
    response.add_button(btn.get_button_help_on_elements())
    #response.add_message('Remember that you can always go back, just click the button')
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
    response.add_button(btn.get_button_history())

def find_word_el_number(entities):
    for i in range(0, len(entities)) :
        match = re.match("(\w+)_(\d+)_(\d+)", entities[i]['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_WORD:
                return (match.group(2))

def find_el_number(entities):
    for i in range(0, len(entities)):
        match = re.match("(\w+)_(\d+)", entities[i]['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_ELEMENT:
                return(int(match.group(2)))
    return 0

def find_word_numbers(entities):
    for i in range(0, len(entities)) :
        match = re.match("(\w+)_(\d+)_(\d+)", entities[i]['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_WORD:
                return str(match.group(2)+"_"+match.group(3))
    return 0

def replace_el_name(entities, name):
    for i in range(0, len(entities)):
        match = re.match("(\w+)_(\d+)", entities[i]['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_ELEMENT:
                entities[i]['value'] = name

def replace_word_numbers(entities, numbers):
    for i in range(0, len(entities)) :
        match = re.match("(\w+)_(\d+)_(\d+)", entities[i]['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_WORD:
                entities[i]['entity'] = "word_"+numbers

def remove_el(entities):
    for i in entities:
        match = re.match("(\w+)_(\d+)", i['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_ELEMENT:
                entities.remove(i)


def action_ambiguity_solver(entities, response, context):
    element_name = handle_element_name_similarity(extract_single_entity_value(entities, nlu.ENTITY_ELEMENT))
    replace_el_name(entities, element_name)

    if not contain(entities, nlu.ENTITY_WORD) and not contain(entities, nlu.ENTITY_NUMBER):
        action_find_element_by_attribute(entities, response, context)
        return

    el_number = int(find_el_number(entities))
    word_el_number = int(find_word_el_number(entities))

    if contain(entities, nlu.ENTITY_ELEMENT) and el_number == word_el_number:
        new_entities = entities.copy()
        autocompleter.autocomplete_from_word(new_entities, response, context)

    else:
        for e in entities:
            e['entity'] = e['entity'].replace("num", "word")

        all_similar_words = resolver.extract_similar_values(find_word_numbers(entities))
        remove_el(entities)
        for word in all_similar_words:
            new_entities = entities.copy()
            replace_word_numbers(new_entities, word)
            autocompleter.autocomplete_from_word(new_entities, response, context)

    nltrasnslator.build_response(response, context)

def contain(entities, word):
    if(word == nlu.ENTITY_ELEMENT):
        for i in entities:
            match = re.match("(\w+)_(\d+)", i['entity'])
            if match:
                what = match.group(1)
                if what == nlu.ENTITY_ELEMENT:
                    return True
    else:
        for e in entities:
            match = re.match("(\w+)_(\d+)_(\d+)", e['entity']) #for word e attr
            if match and match.group(1) == word:
                return True
    return False

def action_find_element_by_attribute(entities, response, context):
    element_name = handle_element_name_similarity(extract_single_entity_value(entities, nlu.ENTITY_ELEMENT))
    ordered_entities = compute_ordered_entity_list(entities)

    if element_name:
        attributes = get_attributes_from_ordered_entities(element_name, ordered_entities,response) if ordered_entities else []
        if attributes:
            element = resolver.query_find(element_name, attributes)
            if element['value']:
                element['action_name'] = '...found with attribute(s) "{}"'.format(get_attributes_string(attributes))
                element['action_type'] = 'find'
                context.append_element(element)
                #handle_response_for_quantity_found_element(response, element, context)
                action_view_context_element(entities, response, context)
            else:
                response.add_message(msg.NOTHING_FOUND)
                response.add_button(btn.get_button_help_on_elements())
                #response.add_message('Remember that you can always go back, just click the button')
                response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
                response.add_button(btn.get_button_history())
        else:
            if response.isEmpty():
                response.add_message('Ok so you want to find some concepts of type {}, but you should '
                'tell me something more, otherwise I can\'t help you explore!'.format(element_name))
                response.add_message(msg.find_element_examples(element_name))
                response.add_button(btn.get_button_help_on_elements())
                #response.add_message('Remember that you can always go back, just click the button')
                response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
                response.add_button(btn.get_button_history())

    else:
        response.add_message('I guess you want to find something, but I did not understand what!\n')
        response.add_message(msg.element_names_examples())
        response.add_button(btn.get_button_help_on_elements())
        #response.add_message('Remember that you can always go back, just click the button')
        response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
        response.add_button(btn.get_button_history())

def action_filter_element_by_attribute(entities, response, context):
    element = context.get_last_element()

    if element:

        if element['real_value_length'] > 1:
            ordered_entities = compute_ordered_entity_list(entities)
            attributes = get_attributes_from_ordered_entities(element['element_name'], ordered_entities,response)

            if attributes:
                # here down union of attributes
                all_attributes = copy.deepcopy(element['attributes']) if element.get('attributes') else []
                if all_attributes[-1]['keyword'] == 'order by':#  'and' the last where in the context with the first of the filter
                    all_attributes[-1]['and_or'] = 'and'
                else:
                    all_attributes[-1]['and_or'] = 'and'
                all_attributes += copy.deepcopy(attributes)
                result_element = resolver.query_find(element['element_name'], all_attributes)
                if result_element['value']:
                    result_element['action_name'] = '...by filtering with property(s) ' \
                                                    '"{}":'.format(get_attributes_string(attributes))
                    result_element['action_type'] = 'filter'
                    context.append_element(result_element)
                    handle_response_for_quantity_found_element(response, result_element, context)
                    action_view_context_element(entities, response, context)

                else:
                    error_message = "Nothing as been found for {} ".format(element['element_name'])
                    error_message += ", ".join(["{} {}".format(e['attribute'], e['value']) for e in ordered_entities])
                    response.add_message(error_message)
                    #response.add_message(msg.NOTHING_FOUND)
                    response.add_button(btn.get_button_help_on_elements())
                    #response.add_message('Remember that you can always go back, just click the button')
                    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
                    response.add_button(btn.get_button_history())

            else:
                response.add_message("I didn't understand for what do you want to filter by\n")
                action_more_info_filter(entities, response, context)

        else:
            response.add_message('Filtering is not possible now, there is only one element under to view!')
            response.add_button(btn.get_button_help_on_elements())
            #response.add_message('Remember that you can always go back, just click the button')
            response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
            response.add_button(btn.get_button_history())

    else:
        response.add_message(msg.EMPTY_CONTEXT_LIST)


def action_cross_relation(entities, response, context):
    element = context.get_last_element()

    if element:

        extracted_relation_name = extract_single_entity_value(entities, nlu.ENTITY_RELATION)
        relation_name = handle_element_relations_similarity(element['element_name'], extracted_relation_name)

        if relation_name:

            # control if there is ONLY an element in context_list
            if element['real_value_length'] == 1:

                result_element = resolver.query_join(element, relation_name)

                if result_element['value']:

                    result_element['action_name'] = '...reached with the relation "{}", from {}:' \
                        .format(relation_name, element['element_name'])
                    result_element['action_type'] = 'cross'

                    context.append_element(result_element)

                    #handle_response_for_quantity_found_element(response, result_element, context)

                    action_view_context_element(entities, response, context)

                else:
                    response.add_message(msg.NOTHING_FOUND)
                    response.add_button(btn.get_button_help_on_elements())
                    response.add_button(btn.get_button_view_context_element('- GO BACK TO THE CONCEPT! -'))
                    #response.add_message('Remember that you can always go back, just click the button')
                    response.add_button(btn.get_button_history())

    else:
        response.add_message(msg.ERROR)
        response.add_button(btn.get_button_help_on_elements())


def action_show_relations(entities, response, context):
    element = context.get_last_element()
    if element:
        buttons = btn.get_buttons_element_relations(element['element_name'])
        if buttons:
            response.add_message('If you want more information, I can tell you:')
            response.add_buttons(buttons)
    else:
        response.add_message(msg.EMPTY_CONTEXT_LIST)


def action_select_element_by_position(entities, response, context):
    pos = extract_single_entity_value(entities, nlu.ENTITY_POSITION)
    title = extract_single_entity_value(entities,'title')

    if pos:
        # attention, I suppose "position" is in the form "1st", "2nd", ...
        position = int(pos)

        element = context.get_last_element()

        if element:

            if element['real_value_length'] == 1:
                response.add_message('There is only one element!\n')
                action_view_context_element(entities, response, context)

            else:
                if is_selection_valid(element, position):
                    if is_value_in_selection_valid(element, position, title):
                        add_selected_element_to_context(element, position, context)
                        action_view_context_element(entities, response, context)
                    else:
                        response.add_message('Error! The selected element not belonging to the context!')
                        response.add_button(btn.get_button_help_on_elements())
                        response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
                        response.add_button(btn.get_button_history())
                else:
                    response.add_message('Error! Out of range selection!')
                    response.add_button(btn.get_button_help_on_elements())
                    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
                    response.add_button(btn.get_button_history())
        else:
            response.add_message(msg.EMPTY_CONTEXT_LIST)
            response.add_button(btn.get_button_help_on_elements())
            response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
            response.add_button(btn.get_button_history())

    else:
        response.add_message(msg.ERROR)
        response.add_button(btn.get_button_help_on_elements())
        #response.add_message('Remember that you can always go back, just click the button')
        response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
        response.add_button(btn.get_button_history())


def action_view_context_element(entities, response, context, show_less=False):
    element = context.view_last_element()
    previous_element = context.view_second_to_last_element()
    if element:
        if element['element_name'] == "more_info_find":
            action_more_info_find(element['entities'], response, context , False)
            return

        if element['element_name'] == "start":
            action_start(element['entities'],response,context , False)
            return

        if element['element_name'] == "show_table_categories":
            action_show_table_categories(element['entities'],response,context , False)
            return

        if element['real_value_length'] == 1:
            if previous_element:
                if element['element_name'] == previous_element['element_name'] and previous_element['real_value_length'] > 1:
                    previous_results_list = ''
                    showed_elements = previous_element['show']['to']
                    for i in previous_element['value'][:showed_elements]:
                        previous_results_list += '- ' + resolver.get_element_show_string(previous_element['element_name'], i) + '\n'
                    response.add_message(previous_results_list)
            #response.add_message(msg.INTRODUCE_ELEMENT_TO_SHOW_PATTERN.format(element['element_name']))
            response.add_message(msg.element_attributes(element))
            #response.add_button(btn.get_button_help_on_elements())
            #response.add_message('Remember that you can always go back, just click the button')
            #response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
            if element.get('element_name') in resolver.get_all_primary_element_names():
                action_show_relations(entities, response, context)
        else:
            if element['show']['from'] == 0 and not show_less:
                #response.add_message('Remember that you can always go back, just click the button')
                #response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
                response.add_message(msg.SELECT_FOR_INFO_PATTERN.format(element.get('element_name')))
            response.add_message('Shown results from {} to {} of {}'.format(element['show']['from'] + 1,
                                                                            element['show']['to'],
                                                                            element['real_value_length']))

            #  response.add_message(msg.element_list(element))
            #response.add_button(btn.get_button_help_on_elements())
            response.add_buttons(btn.get_buttons_select_element(element))
            if element['show']['to'] < element['real_value_length']:
                response.add_button(btn.get_button_show_more_element())
            if element['show']['from'] >= 1:
                response.add_button(btn.get_button_show_less_element())
            response.add_button(btn.get_button_order_by())
            response.add_button(btn.get_button_filter_hints())
    else:
        #response.add_button(btn.get_button_help_on_elements())
        response.add_message(msg.EMPTY_CONTEXT_LIST)
    response.add_button(btn.get_button_help_on_elements())
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
    response.add_button(btn.get_button_history())


def action_show_more_elements(entities, response, context):
    element = context.get_last_element()

    if element and element['real_value_length'] > 1:
        if element['show']['to'] < element['real_value_length']:
            element['show']['from'] = element['show']['from'] + ELEMENT_VISU_LIMIT
            element['show']['to'] = min(element['real_value_length'], element['show']['to'] + ELEMENT_VISU_LIMIT)
            context.reset_show_last_element = False
            action_view_context_element(entities, response, context)
        else:
            response.add_message('I am sorry, but there is nothing to show more...')
    else:
        response.add_message('I am sorry, but there is nothing to show more...')

def action_show_less_elements(entities, response, context):
    element = context.get_last_element()
    if element and element['real_value_length'] > 1 and element['show']['to'] > ELEMENT_VISU_LIMIT:
        diff = 0
        if element['show']['to'] == element['real_value_length']:
            diff = element['show']['to'] - (element['show']['from'] + 1)
        element['show']['to'] = element['show']['to'] - ELEMENT_VISU_LIMIT
        element['show']['to'] += diff
        element['show']['from'] = max(0, element['show']['from'] - ELEMENT_VISU_LIMIT)
        context.reset_show_last_element = False
        action_view_context_element(entities, response, context, show_less = True)

    else:
        response.add_message('I am sorry, but there is nothing to show less...')


def action_order_by(entities, response, context):
    element = context.get_last_element()
    if element:
        value = element['value']
        element_name = element['element_name']
        value_attributes = value[0] #take first element
        response.add_message('Choose the property you want to order')
        #response.add_button(btn.get_button_help_on_elements())
        response.add_buttons(btn.get_buttons_order_by_attribute(value_attributes,element_name))
    else:
        #response.add_button(btn.get_button_help_on_elements())
        response.add_message('I am sorry, but there is nothing to order...')
    response.add_button(btn.get_button_help_on_elements())
    response.add_button(btn.get_button_history())
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))

def action_order_by_attribute(entities, response, context):
    attribute_to_order_by = extract_single_entity_value(entities, nlu.ENTITY_POSITION)
    element = context.get_last_element()
    value = element['value']
    value = sorted(value, key=lambda k: (k[attribute_to_order_by] is None, k[attribute_to_order_by])) # All None element are put in the end
    element['value'] = value
    context.reset_show_last_element = False
    action_view_context_element(entities, response, context)

def action_show_more_examples(entities, response, context):
    element_name = entities[0]['value']
    attributes = resolver.extract_all_attributes(element_name)
    response.add_message('Select the property of "' + element_name +  '" you want to see examples of')
    response.add_buttons(btn.get_buttons_show_more_ex_attr(element_name, attributes))
    #response.add_button(btn.get_button_attribute_combinations(element_name))
    response.add_button(btn.get_button_help_on_elements())
    response.add_button(btn.get_button_history())
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))

"""def action_show_attributes_combinations(entities, response, context):
    element_name = entities[0]['value']
    attributes = resolver.extract_all_attributes(element_name)
    response.add_message(msg.find_element_combinations(element_name,attributes))
    response.add_button(btn.get_button_help_on_elements())
    response.add_button(btn.get_button_history())
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))"""

def action_show_more_examples_attribute(entities, response, context):
    for e in entities:
        if e['entity'] is 'e':
            element_name = e['value']
        elif e['entity'] is 'k':
            key = '' if e['value'] is ' ' else e['value']
    attribute = resolver.get_attribute_by_name(element_name, key)
    if not attribute:
        attribute = resolver.get_attribute_without_keyword(element_name)
    if 'by' in attribute:
        new_table_name = attribute.get('by')[-1]['to_table_name']
        new_element_name = resolver.get_element_name_from_table_name(new_table_name)
        examples = resolver.query_show_attributes_examples(new_element_name, attribute['columns'])
        attribute_alias = resolver.extract_attributes_alias(new_element_name)
    else:
        examples = resolver.query_show_attributes_examples(element_name, attribute['columns'])
        attribute_alias = resolver.extract_attributes_alias(element_name)
    columns = []
    for c in attribute['columns']:
        if attribute_alias and c in attribute_alias:
            columns.append(attribute_alias[c])
        else:
            columns.append(c)
    """message = ('Here some examples of ')
    message += ', '.join(columns)
    message += ':'
    response.add_message(message)"""
    attribute_message = ""
    loop = True
    i = 0
    #for _ in range(10):
    while loop:
        #attribute_message += "{}, ".format(random.choice(examples))
        attribute_message += "- Find {} ".format(element_name)
        if attribute['keyword']:
            attribute_message += "{} ".format(attribute['keyword'])
        example = random.choice(examples)
        examples.remove(example)
        attribute_message += "{}\n".format(example)
        i += 1
        if i == 9 or not examples:
            loop = False
    response.add_message(attribute_message)
    response.add_button(btn.get_button_help_on_elements())
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
    response.add_button(btn.get_button_history())

def action_show_context(entities, response, context):
    context_list = context.view_context_list()  # _to_show()

    if context_list:

        up = context.context_list_indices['up']
        down = context.context_list_indices['down']

        for i, el in enumerate(context_list[down:up][::-1]): #veramente brutto TODO sistemare con uno switch in caso di avanzo di tempo

            if el['element_name'] =="more_info_find":
                result = 'Examples of "{}"'.format(el['element_value'])

            else:
                if el['element_name'] == "start":
                    result = 'Start'

                else:
                    if el['element_name'] == "show_table_categories":
                        result = 'Categories of "{}"'.format(el['element_value'])
                    else:
                        if el['real_value_length'] == 1:
                            result = '{}'.format(resolver.get_element_show_string(el['element_name'], el['value'][0]))
                        else:
                            result = 'A list of type "{}"'.format(el['element_name'])

            if up == len(context_list) and i == 0:  # the very first one
                #response.add_message(msg.REMEMBER_RESET_HISTORY)
                #m = 'Currently you are viewing'
                #m += ' {}:'.format(context_list[-1]['element_name']) \
                #    if context_list[-1]['real_value_length'] == 1 else ':'
                #response.add_message(m)
                response.add_message("Here is history, click on a button to see the related element")
                response.add_button(btn.get_button_view_context_element(result))

            else:
                #if i == 0:  # the first ones, in a "show more" list
                    # adding the last action name of the previous "set" of actions
                    #response.add_message(context_list[up]['action_name'])
                response.add_button(btn.get_button_go_back_to_context_position(result, up-i))

            #if i != up - down - 1 or down == 0 and el['action_type'] == 'find':
                #response.add_message(el['action_name'])
        response.add_button(btn.get_button_reset_context())
        if down != 0:
            response.add_button(btn.get_button_show_more_context())

    else:
        response.add_message(msg.EMPTY_CONTEXT_LIST)

    response.add_button(btn.get_button_help_on_elements())
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
    response.add_button(btn.get_button_history())

def action_show_more_context(entities, response, context):
    context_list = context.get_context_list()

    if context_list:
        if context.context_list_indices['down'] != 0:  # if it is not 0
            context.context_list_indices['down'] = max(context.context_list_indices['down'] - CONTEXT_VISU_LIMIT, 0)
            context.context_list_indices['up'] = context.context_list_indices['up'] - CONTEXT_VISU_LIMIT
            context.reset_show_context_list = False
            action_show_context(entities, response, context)
        else:
            response.add_message('I am sorry, but there is nothing to show more...')
            response.add_button(btn.get_button_help_on_elements())
            #response.add_message('Remember that you can always go back, just click the button')
            response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
            response.add_button(btn.get_button_history())
    else:
        response.add_message('I am sorry, but there is nothing to show more...')
        response.add_button(btn.get_button_help_on_elements())
        #response.add_message('Remember that you can always go back, just click the button')
        response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
        response.add_button(btn.get_button_history())


def action_go_back_to_context_position(entities, response, context):
    pos = extract_single_entity_value(entities, nlu.ENTITY_POSITION)
    # if context is not empty
    if context.get_context_list():

        length = len(context.get_context_list())

        position = int(pos) if pos else (length - 1)
        # if no position is extracted, set the value to go back only once

        if position == nlu.VALUE_POSITION_RESET_CONTEXT or \
                len(context.get_context_list()) == 1 and position == 0:  # if the list is one el long and no entity pos
            context.reset_context_list()
            if position == nlu.VALUE_POSITION_RESET_CONTEXT:
                response.add_message(msg.CONTEXT_LIST_RESET)
            else:
                response.add_message(msg.NO_GO_BACK)
            response.add_button(btn.get_button_help_on_elements())#response.add_message('Remember that you can always go back, just click the button')
            response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
            response.add_button(btn.get_button_history())

        elif position - 1 < length:
            context.go_back_to_position(position)
            response.add_message('Ok, now resuming your history of {} position{}... DONE!'
                                 .format(length - position, "s" if length - position > 1 else ""))
            action_view_context_element(entities, response, context)

        else:
            # wrong selection
            action_show_context(entities, response, context)
    else:
        response.add_message(msg.EMPTY_CONTEXT_LIST)
        response.add_button(btn.get_button_help_on_elements())
        response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
        response.add_button(btn.get_button_history())


def action_find_element_by_category(entities,response, context):
    element = context.get_last_element()
    if element:
        element_name = element['element_value']
        category_name = entities[0]['entity']
        category_value = entities[0]['value']
        if element_name and category_value:
            element = resolver.query_category_value(element_name, category_name, category_value)
            if element['value']:
                element['action_name'] = '...found from category {0} of table {1}'.format(category_value, element_name.upper())
                element['action_type'] = 'find'
                context.append_element(element)
                #handle_response_for_quantity_found_element(response, element, context)
                action_view_context_element(entities, response, context)

            else:
                response.add_message(msg.NOTHING_FOUND)
        else:
            response.add_message(msg.ERROR)


def action_show_table_categories(entities, response, context, add = True):
    element_name = entities[0]['entity']
    category_column = entities[0]['value']
    category = resolver.extract_category(element_name, category_column)
    if element_name:
        if category:
            element = resolver.query_category(element_name, category['column'])
            create_plot(element, category['alias'].upper())
            response.add_message('The concepts of type {} can be categorized based on {}.'.format(element_name, category['alias']))
            response.add_message('Pie chart')
            response.add_message('You can select {}s related to a specific category by clicking on the related button.'.format(element_name))
            response.add_buttons(btn.get_buttons_select_category(element_name, category['column'], element['value']))

            if add:
                element = dict()
                element['value'] = 0
                element['element_name'] = 'show_table_categories'
                element['element_value'] = element_name
                element['action_name'] = 'show_table_categories'
                element['action_type'] = 'show_table_categories'
                element['entities'] = entities
                element['query'] = None
                element['real_value_length'] = 1
                context.append_element(element)

        else:
            response.add_message('I cannot find more info about {}s.'.format(element_name))

    else:
        response.add_message(msg.NOTHING_FOUND)

    response.add_button(btn.get_button_help_on_elements())
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
    response.add_button(btn.get_button_history())

"""
def categories_to_string(element):
    total = 0
    items = element['value']
    displayed_items = 5 if len(items) > 5 else len(items)
    str = "These are the top {} categories: ".format(displayed_items)
    for i in items:
        total += i['count']
    for i in range(displayed_items):
        str += "\n- {0} ({1:.2f}%)".format(items[i]['category'], items[i]['count']*100/total)
    return str
"""

def create_plot(categories, legend_title):
    plt.switch_backend('Agg')

    total = 0
    labels = []
    sizes = []
    perc = []
    items = categories['value']
    displayed_items = 5 if len(items) > 5 else len(items)

    for i in items:
        total += i['count']

    for i in range(displayed_items):
        labels.append(items[i]['category'])
        sizes.append(items[i]['count'])
        perc.append(sizes[i]*100/total)

    if displayed_items < len(items):
        other_count = 0
        for i in range(displayed_items, len(items)):
            other_count += items[i]['count']
        labels.append('Other')
        sizes.append(other_count)
        perc.append(sizes[displayed_items]*100/total)


    colors = ['tomato', 'mediumseagreen', 'pink', 'darkturquoise', 'gold', 'dimgrey']
    patches, texts = plt.pie(sizes, colors=colors, autopct=None, startangle=90, labeldistance=None, textprops={'fontsize': 14}, wedgeprops = {'linewidth': 0.5, 'edgecolor' : 'black'})
    plt.legend(patches, labels=['%s, %1.1f %%' % (l, p) for l, p in zip(labels, perc)], title=legend_title, title_fontsize='large', loc='lower center', bbox_to_anchor=(0.5, 1))

    plt.axis('equal')
    plt.savefig('static/pie.png', bbox_inches="tight")
    plt.close()





# EXECUTION

intents_to_action_functions = {
    nlu.INTENT_HELP: action_help,
    nlu.INTENT_START: action_start,
    nlu.INTENT_HELP_ELEMENTS: action_help_elements,
    nlu.INTENT_HELP_HISTORY: action_help_history,
    nlu.INTENT_HELP_GO_BACK: action_help_go_back,
    nlu.INTENT_MORE_INFO_FIND: action_more_info_find,
    nlu.INTENT_MORE_INFO_FILTER: action_more_info_filter,
    nlu.INTENT_FIND_ELEMENT_BY_ATTRIBUTE: action_find_element_by_attribute,
    nlu.INTENT_FILTER_ELEMENT_BY_ATTRIBUTE: action_filter_element_by_attribute,
    nlu.INTENT_CROSS_RELATION: action_cross_relation,
    nlu.INTENT_SHOW_RELATIONS: action_show_relations,
    nlu.INTENT_SHOW_MORE_ELEMENTS: action_show_more_elements,
    nlu.INTENT_SHOW_LESS_ELEMENTS: action_show_less_elements,
    nlu.INTENT_SELECT_ELEMENT_BY_POSITION: action_select_element_by_position,
    nlu.INTENT_ORDER_BY: action_order_by,
    nlu.INTENT_ORDER_BY_ATTRIBUTE: action_order_by_attribute,
    nlu.INTENT_SHOW_MORE_EXAMPLES: action_show_more_examples,
    nlu.INTENT_SHOW_MORE_EXAMPLES_ATTRIBUTE: action_show_more_examples_attribute,
    #nlu.INTENT_SHOW_ATTRIBUTES_COMBINATIONS: action_show_attributes_combinations,
    nlu.VIEW_CONTEXT_ELEMENT: action_view_context_element,
    nlu.INTENT_SHOW_CONTEXT: action_show_context,
    nlu.INTENT_SHOW_MORE_CONTEXT: action_show_more_context,
    nlu.INTENT_GO_BACK_TO_CONTEXT_POSITION: action_go_back_to_context_position,
    nlu.INTENT_SHOW_TABLE_CATEGORIES: action_show_table_categories,
    nlu.INTENT_AMBIGUITY_SOLVER: action_ambiguity_solver,
    nlu.INTENT_FIND_ELEMENT_BY_CATEGORY: action_find_element_by_category
}


def execute_action_from_intent_name(intent_name, entities, context):

    response = patterns.Response()
    action_function = intents_to_action_functions.get(intent_name)
    if action_function:
        context.log('Calling action: {}'.format(action_function.__name__))
        action_function(entities, response, context)
    else:
        context.log('Executing fallback action')
        response.add_message(msg.ERROR)
        response.add_button(btn.get_button_help_on_elements())
        response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
        response.add_button(btn.get_button_history())
    context.log('Response will be:\n'
                '\n'
                '{}\n'
                '\n'
                '- - - - - -'.format(response.get_printable_string()))

    return response
