from modules.patterns import nlu
from modules.database import resolver
import re


def get_buttons_element_relations(element_name):
    relations = resolver.extract_relations(element_name)
    buttons = []
    for rel in relations:
        title = rel['keyword']
        payload = extract_payload(nlu.INTENT_CROSS_RELATION,
                                 [nlu.ENTITY_RELATION, rel['keyword']])
        buttons.append({'title': title, 'payload': payload})
    return buttons


def get_button_filter_hints():
    return {'title': '- FILTER HINTS -', 'payload': extract_payload(nlu.INTENT_MORE_INFO_FILTER)}

def get_button_history():
    return {'title': '- HISTORY -', 'payload': extract_payload(nlu.INTENT_SHOW_CONTEXT)}

def get_buttons_select_element(element):
    buttons = []
    for i in range(element['show']['from'], element['show']['to']):
        title = resolver.get_element_show_string(element['element_name'], element['value'][i])
        cleanr = re.compile('<.*?>|"|;')
        title = re.sub(cleanr, '', title)
        cleanr = re.compile("'")
        title = re.sub(cleanr, '', title)
        title = title.rstrip()
        payload = extract_payload(nlu.INTENT_SELECT_ELEMENT_BY_POSITION,
                                  [nlu.ENTITY_POSITION, str(i+1)],['title',title[:29]])  #if answer is > 64 char too long we get error 400 - invalid data. So we cut at 29 chars
        buttons.append({'title': title, 'payload': payload})
    return buttons

def get_buttons_select_phrases(phrases):
    buttons = []
    for i in phrases:
        payload = extract_payload(nlu.INTENT_FIND_ELEMENT_BY_ATTRIBUTE,
                                    [nlu.ENTITY_PHRASE, i])  #if answer is too long we get error 400 - invalid data. So we cut at 35 chars
        buttons.append({'title': i, 'payload': payload})
    return buttons

def get_button_show_more_element():
    title = '+ SHOW MORE RESULTS +'
    payload = extract_payload(nlu.INTENT_SHOW_MORE_ELEMENTS)
    return {'title': title, 'payload': payload}

def get_button_show_less_element():
    title = '+ SHOW LESS RESULTS +'
    payload = extract_payload(nlu.INTENT_SHOW_LESS_ELEMENTS)
    return{'title':title, 'payload':payload}

def get_button_order_by():
    title = '+ ORDER RESULTS BY +'
    payload = extract_payload(nlu.INTENT_ORDER_BY)
    return {'title': title, 'payload': payload}

def get_buttons_order_by_attribute(element, element_name):
    buttons = []
    """ attribute_alias = resolver.extract_attributes_alias(element_name)
    for e in element:
        title_payload = e
        if attribute_alias and e in attribute_alias:
            title = attribute_alias[e]
        else:
            title = e
        payload = extract_payload(nlu.INTENT_ORDER_BY_ATTRIBUTE, [nlu.ENTITY_POSITION, title_payload])
        buttons.append({'title' :title, 'payload': payload}) """
    displayable_attributes = resolver.simulate_view(element_name)
    attribute_names = [i['attribute'] for i in displayable_attributes if 'attribute' in i]
    displayed_names = [i['display'] for i in displayable_attributes if 'display' in i]
    for k, v in element.items():
        if k in attribute_names:
            title_payload = k
            title_display = displayed_names[attribute_names.index(k)]
            payload = extract_payload(nlu.INTENT_ORDER_BY_ATTRIBUTE, [nlu.ENTITY_POSITION, title_payload])
            buttons.append({'title' :title_display, 'payload': payload})
    return buttons


def get_button_show_more_examples(element):
    title = '+ NEED MORE EXAMPLES? +'
    payload = extract_payload(nlu.INTENT_SHOW_MORE_EXAMPLES, ['element', element])
    return  {'title': title, 'payload': payload}

def get_buttons_show_more_ex_attr(element_name, attributes):
    buttons = []
    for a in attributes:
        """if 'by' in a:
            new_table_name = a.get('by')[-1]['to_table_name']
            new_element_name = resolver.get_element_name_from_table_name(new_table_name)
            attribute_alias = resolver.extract_attributes_alias(new_element_name)
        else:
            attribute_alias = resolver.extract_attributes_alias(element_name)
        columns = []
        for c in a['columns']:
            if attribute_alias and c in attribute_alias:
                columns.append(attribute_alias[c])
            else:
                columns.append(c)"""
        key = a['keyword'] if a['keyword'] else ' '
        #title = ",".join(' {}'.format(c) for c in columns)
        title = "Find {} {} ...".format(element_name,key)
        payload = '/' + nlu.INTENT_SHOW_MORE_EXAMPLES_ATTRIBUTE + '{"e":'+'"'+element_name+'";'+ '"k":'+ '"' +key+'"' #Ugly but data to be sent in a callback query to the bot when button is pressed, 1-64 bytes
        buttons.append({'title' : title, 'payload' : payload})
    return buttons

def get_button_attribute_combinations(element_name):
    title = "+ WANNA DO ATTRIBUTES COMBINATIONS? +"
    payload = '/' + nlu.INTENT_SHOW_ATTRIBUTES_COMBINATIONS + '{"e":'+'"'+element_name+'"}'
    return {'title':title, 'payload':payload}

def get_button_show_more_context():
    title = '+ SHOW MORE HISTORY +'
    payload = extract_payload(nlu.INTENT_SHOW_MORE_CONTEXT)
    return {'title': title, 'payload': payload}

def get_buttons_tell_me_more():
    elements = resolver.get_all_primary_element_names()
    buttons = []
    for e in elements:
        title = "Tell me more about {}".format(e)
        payload = extract_payload(nlu.INTENT_MORE_INFO_FIND, [nlu.ENTITY_ELEMENT, e])
        buttons.append({'title':title, 'payload': payload})
    return buttons


def get_button_view_context_element(title):
    payload = extract_payload(nlu.VIEW_CONTEXT_ELEMENT)
    return {'title': title, 'payload': payload}


def get_button_reset_context():
    payload = extract_payload(nlu.INTENT_GO_BACK_TO_CONTEXT_POSITION,
                              [nlu.ENTITY_POSITION, str(nlu.VALUE_POSITION_RESET_CONTEXT)])
    return {'title': '+ RESET HISTORY +', 'payload': payload}


def get_button_go_back_to_context_position(action_name, pos):
    title = action_name
    payload = extract_payload(nlu.INTENT_GO_BACK_TO_CONTEXT_POSITION,
                              [nlu.ENTITY_POSITION, str(pos)])
    return {'title': title, 'payload': payload}


def get_buttons_help():
    buttons = [{'title': '- SHOW ALL THE CONCEPTS -', 'payload': extract_payload(nlu.INTENT_HELP_ELEMENTS)},
               {'title': '- Help on HISTORY -', 'payload': extract_payload(nlu.INTENT_HELP_HISTORY)},
               {'title': '- Help on GOING BACK -', 'payload': extract_payload(nlu.INTENT_HELP_GO_BACK)}]
    return buttons


def get_buttons_select_category(element, category_column, categories):
    buttons = []
    displayed_categories = categories[:5]
    for c in displayed_categories:
        title = c['category']
        payload = extract_payload(nlu.INTENT_FIND_ELEMENT_BY_CATEGORY, [category_column, c['category']])
        buttons.append({'title': title, 'payload': payload})
    print(buttons)
    return buttons


def get_button_help():
    title = '- HELP -'
    payload = extract_payload(nlu.INTENT_START)
    return {'title': title, 'payload': payload}

def get_button_help_on_elements():
    title = '- SHOW ALL THE CONCEPTS -'
    payload = extract_payload(nlu.INTENT_HELP_ELEMENTS)
    return {'title': title, 'payload': payload}


def get_button_show_table_categories(element):
    buttons = []
    for cat in resolver.extract_categories(element):
        title = "+ SHOW THE {}S OF {} +".format(cat['alias'].upper(), element.upper())
        payload = extract_payload(nlu.INTENT_SHOW_TABLE_CATEGORIES, [element, cat['column']])
        buttons.append({'title': title, 'payload': payload})
    return buttons


# helper

def extract_payload(intent_name, *entity_pairs):
    payload = '/{}'.format(intent_name)
    entities = ';'.join('"{}":"{}"'.format(ep[0], ep[1]) for ep in entity_pairs)
    if entities:
        payload += '{' + entities + '}'
    return payload
