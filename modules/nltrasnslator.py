from modules import commons
from modules.database import resolver
from modules.patterns import btn, msg, nlu
import re
from modules import actions

phrases = list()

def traslate_to_nl(entities, response, begin = "Find"):
    ordered_entities = order_entities(entities)
    phrase = create_phrase(ordered_entities, response, begin)

    if phrase not in phrases:
        phrases.append(phrase)

def create_phrase(entities, response, begin = "Find"): #begin = Find to be changed in future applications, to force reiterate 
    el_added = False  #these 3 are used to ensure that every phrase has every part only once
    attr_added = False
    word_added = False
    phrase = begin
    for e in entities:
        match = re.match("(\w+)_(\d+)", e['entity'])
        if match and match.group(1) == nlu.ENTITY_ELEMENT and not el_added:
            phrase += " " +e['value']
            el_added = True
        match = re.match("(\w+)_(\d+)_(\d+)", e['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_ATTRIBUTE and not attr_added:
                phrase += " " + e['value']
                attr_added = True
            if what == nlu.ENTITY_WORD and not word_added:
                phrase += " " + e['value']
                word_added = True

    return phrase

def build_response(response, context):
    response.add_message(msg.AMBIGUITY_FOUND)
    response.add_buttons(btn.get_buttons_select_phrases(phrases))
    response.add_button(btn.get_button_help_on_elements())
    #response.add_message('Remember that you can always go back, just click the button')
    response.add_button(btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1))
    response.add_button(btn.get_button_history())
    phrases.clear()


def order_entities(entities): #brutally orders entities in shape [el - attr - word]
    new_entites = [0] * 3
    for e in entities:
        match = re.match("(\w+)_(\d+)", e['entity'])
        if match and match.group(1) == nlu.ENTITY_ELEMENT:
            new_entites[0] = e
            
        match = re.match("(\w+)_(\d+)_(\d+)", e['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_ATTRIBUTE:
                new_entites[1] = e
                
            if what == nlu.ENTITY_WORD:
                new_entites[2] = e
        
    return new_entites