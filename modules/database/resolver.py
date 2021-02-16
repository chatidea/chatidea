import logging
import json

from modules.database import broker
from settings import DB_CONCEPT_PATH, DB_CONCEPT_PATH_S

logger = logging.getLogger(__name__)

db_concept = []
db_concept_s = []

# Database properties


def load_db_concept():
    global db_concept
    global db_concept_s
    logger.info('Database concept file:\n'
                '"' + DB_CONCEPT_PATH + '"')
    logger.info('Loading database concept file...')
    with open(DB_CONCEPT_PATH) as f:
        db_concept = json.load(f)
    with open(DB_CONCEPT_PATH_S) as f1:
        db_concept_s = json.load(f1)
    logger.info('Database concept file has been loaded!')

def extract_similar_values(word):
    all_words = []
    for e in db_concept_s:
        for s in e.get('similars'):
            if word in s:
                all_words = s
    if len(all_words) == 0:
        all_words = [word]
    return all_words

def get_all_primary_element_names():
    res = []
    for e in db_concept:
        if e.get('type') == 'primary':
            res.append(e.get('element_name'))
    return res


def get_all_primary_element_names_and_aliases():
    res = []
    for e in db_concept:
        if e.get('type') == 'primary':
            res.extend([e.get('element_name')] + e.get('aliases', []))
    return res


def get_element_aliases(element_name):
    element = extract_element(element_name)
    return element.get('aliases', [])


def get_element_name_from_possible_alias(element_or_alias_name):
    for e in db_concept:
        if e.get('element_name') == element_or_alias_name or element_or_alias_name in e.get('aliases', []):
            return e.get('element_name')
    return None

def get_element_name_from_table_name(table_name):
    for e in db_concept:
        if e.get('table_name') == table_name:
            return e.get('element_name')
    return None


def extract_element(element_name):
    for e in db_concept:
        if e.get('element_name') == element_name:
            return e
    return None


def extract_show_columns(element_name):
    e = extract_element(element_name)
    return e.get('show_columns') if e else None


def extract_relations(element_name):
    e = extract_element(element_name)
    return e.get('relations') if e else None


def extract_all_attributes(element_name):
    e = extract_element(element_name)
    return e.get('attributes') if e else None


def extract_categories(element_name):
    e = extract_element(element_name)
    return e.get('category') if e else None


def extract_category(element_name, column_name):
    e = extract_element(element_name)
    for c in e.get('category'):
        if c['column'] == column_name:
            return c
    return None

def extract_attributes_with_keyword(element_name):
    attributes = extract_all_attributes(element_name)
    if attributes:
        return [a for a in attributes if a.get('keyword')]
    return None

def extract_attributes_alias(element_name):
    e = extract_element(element_name)
    table_name = e.get('table_name')
    table_schema = broker.get_table_schema_from_name(table_name)
    if 'column_alias_list' in table_schema:
        return table_schema['column_alias_list']
    else:
        return None

def get_attribute_by_name(element_name, attribute_name):
    attributes = extract_attributes_with_keyword(element_name)
    for a in attributes:
        if a.get('keyword') == attribute_name:
            return a
    return None


def get_attribute_without_keyword_by_type(element_name, attribute_type):
    attributes = [a for a in extract_all_attributes(element_name)
                  if a not in extract_attributes_with_keyword(element_name)]
    for a in attributes:
        if a.get('type') == attribute_type:
            return a
    return None

def get_attribute_without_keyword(element_name):
    attributes = [a for a in extract_all_attributes(element_name) if a not in extract_attributes_with_keyword(element_name)]
    for a in attributes:
        return a
    return None

def get_element_show_string(element_name, element_value):
    show_columns = extract_show_columns(element_name)
    return ', '.join((sh['keyword'] + ': ' if sh.get('keyword') else '')
                     + ' '.join(str(element_value[x]) for x in sh['columns'])
                     for sh in show_columns)


def query_find(element_name, attributes):
    e = extract_element(element_name)
    table_name = e.get('table_name')
    result_element = broker.query_find(table_name, attributes)
    result_element['element_name'] = element_name
    return result_element

def query_show_attributes_examples(element_name, attributes):
    e = extract_element(element_name)
    table_name = e.get('table_name')
    result_element = broker.query_show_attributes_examples(table_name, attributes)
    result_element = list(filter(None,result_element))
    return result_element


def query_join(element, relation_name):
    all_relations = extract_relations(element['element_name'])

    # there should always be the relation we want, the control is made in the executor
    relation = [rel for rel in all_relations if rel['keyword'] == relation_name][0]

    result_element = broker.query_join(element, relation)
    result_element['element_name'] = relation['element_name']
    return result_element


def query_category(element_name, category):
    e = extract_element(element_name)
    table_name = e.get('table_name')
    result_element = broker.query_category(table_name, category)
    result_element['element_name'] = element_name
    return result_element


def query_category_value(element_name, category_column, category_value):
    e = extract_element(element_name)
    table_name = e.get('table_name')
    category = extract_category(element_name, category_column)
    result_element = broker.query_category_value(e.get('element_name'), table_name, category, category_value)
    result_element['element_name'] = element_name
    return result_element


def simulate_view(element_name):
    e = extract_element(element_name)
    table_name = e.get('table_name')
    result_element = broker.simulate_view(table_name)
    return result_element
