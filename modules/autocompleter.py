from modules import commons
from modules.database import resolver
from modules.patterns import btn, msg, nlu
import re
from modules import actions, nltrasnslator

def autocomplete_from_word(entities, response, context):
    element_name = actions.handle_element_name_similarity(actions.extract_single_entity_value(entities, nlu.ENTITY_ELEMENT))
    #ordered_entities = compute_ordered_entity_list(entities)
    #se non ci sono word non posso capire niente
    
    if not element_name and entities:
        #cerco di capire l'elemento a partire dalle word o dall'attributo
        entities = add_entity_from_word(entities)
        element_name = actions.handle_element_name_similarity(actions.extract_single_entity_value(entities, nlu.ENTITY_ELEMENT))

    #se c'è una word senza l attr di collegamento
    if element_name and contain(entities, nlu.ENTITY_WORD) and not contain(entities, nlu.ENTITY_ATTRIBUTE):

        #prima di tutto devo riconoscere la word da sola
        entities = add_attribute_from_word_number_and_el_number(entities)
        #cerco di completare autonomamente

    #alla fine chiamo il normale find element by attribute con l'array completato
    print("ENTITIES DOPO COMPLETAMENTO--------------------")
    print(entities)
    nltrasnslator.traslate_to_nl(entities, response)

def contain(entities, word):
    for e in entities:
        match = re.match("(\w+)_(\d+)_(\d+)", e['entity'])
        if match and match.group(1) == word:

            return True
    return False

def add_entity_from_word(entities):

    for i in range(0, len(entities)) :
        match = re.match("(\w+)_(\d+)_(\d+)", entities[i]['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_WORD:
                entity_number= match.group(2)
                entity_name = get_el_name_from_number(entity_number)  #order can be different?
                entities.insert(0, {'start': 0, 'value': entity_name, 'entity': nlu.ENTITY_ELEMENT+ "_"+ str(entity_number)}) #starting point doesn't really matter
                i+=1  #else it adds infinite enitities
    return entities

def add_attribute_from_word_number_and_el_number(entities):
    for i in range(0, len(entities)):
        
        match = re.match("(\w+)_(\d+)", entities[i]['entity']) #devi fare il numero e dividere i gruppi
        if match:
            
            what = match.group(1)
            if what == nlu.ENTITY_ELEMENT:
                attributes = resolver.extract_all_attributes(entities[i]['value'])
                entity_number = int(match.group(2))

    for i in range(0, len(entities)):
        match = re.match("(\w+)_(\d+)_(\d+)", entities[i]['entity'])
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_WORD:
                entity_number_from_word = match.group(2)
                attribute_number= match.group(3)
                position = i
                i +=1

    if str(entity_number) != str(entity_number_from_word):
        return entities
    #now searching for the right attribute from all the list found
    if attribute_number and attributes:
        entities.insert(position, {'start': 0, 'value': attributes[int(attribute_number) - 1]['keyword'], 'entity': nlu.ENTITY_ATTRIBUTE + "_"+ str(entity_number) +"_"+ str(attribute_number)})
    return entities

def get_el_name_from_number(number):
    names= resolver.get_all_primary_element_names()
    entity_name = names[int(number)-1]
    return entity_name