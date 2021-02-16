import copy
import json
import logging
import os
import string

from pprint import pprint
from mysql import connector
from modules.database import resolver

from settings import DATABASE_NAME, DB_SCHEMA_PATH, DB_VIEW_PATH, DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, QUERY_LIMIT

logger = logging.getLogger(__name__)

db_schema = None

db_view = None


def test_connection():
    logger.info('Database:\n'
                '"' + DATABASE_NAME + '"')
    logger.info('Testing connection with the database...')
    connection = connect()
    logger.info('Connection succeeded! Closing connection...')
    disconnect(connection)
    logger.info('Connection closed.')


def connect():
    return connector.connect(user=DATABASE_USER,
                             password=DATABASE_PASSWORD,
                             host=DATABASE_HOST,
                             database=DATABASE_NAME)


def disconnect(connection):
    connection.close()


def load_db_schema():
    global db_schema
    logger.info('Database schema file:\n'
                '"' + DB_SCHEMA_PATH + '"')
    logger.info('Loading database schema file...')
    with open(DB_SCHEMA_PATH) as f:
        db_schema = json.load(f)
    logger.info('Database schema file has been loaded!')


def load_db_view():
    global db_view
    logger.info('Database view file:\n'
                '"' + DB_VIEW_PATH + '"')
    logger.info('Loading database view file...')
    with open(DB_VIEW_PATH) as f:
        db_view = json.load(f)
    logger.info('Database view file has been loaded!')


def execute_query_select(query, t=None):
    # HERE FORCING THE LIMIT OF THE QUERY
    if QUERY_LIMIT:
        query += ' LIMIT 100'
    logger.info('Executing query...')
    logger.info('Query: "{}"'.format(query))
    if t:
        logger.info('Tuple: {}'.format(t))

    connection = connect()
    cursor = connection.cursor()
    cursor.execute(query, t)
    rows = cursor.fetchall()
    cursor.close()
    disconnect(connection)
    return rows


def get_dictionary_result(q_string, q_tuple, rows, columns, attributes):
    query = {'q_string': q_string, 'q_tuple': q_tuple}

    value = list(map(lambda r: dict(zip(columns, r)), rows))

    return {'query': query,
            'value': value,
            'real_value_length': len(value),
            'attributes': attributes}


def get_table_schema_from_name(table_name):
    return db_schema.get(table_name)  # may return None

def get_table_view_from_name(table_name):
    return db_view.get(table_name)  # may return None

def get_references_from_name(table_name):
    return db_schema.get(table_name)['references']


def query_show_attributes_examples(table_name, attributes):
    result = []
    columns = []
    for a in attributes:
        columns.append({'column': a , 'table': table_name})
    query_string = "SELECT DISTINCT " + get_SELECT_query_string(columns, table_name)
    query_string += " FROM " + table_name
    rows = execute_query_select(query_string)
    for r in rows:
        result.append(r[0])
    return result


def query_find(in_table_name, attributes):

    columns = []
    for col in get_table_schema_from_name(in_table_name)['column_list']:
        columns.append({'column': col, 'table': in_table_name})

    for fk in get_references_from_name(in_table_name):
        for col in columns:
            if fk['from_attribute'] == col['column']:
                col['column'] = fk['show_attribute']
                col['table'] = fk['to_table']

    label_attributes(attributes, in_table_name)
    for a in attributes:
        if not a.get('operator'):
            a['operator'] = '='

    query_string = "SELECT DISTINCT " + get_SELECT_query_string(columns, in_table_name)  # ugly but correct
    query_string += " FROM " + get_FROM_query_string(attributes, in_table_name)
    query_string += " WHERE "
    where_join_string = get_WHERE_JOIN_query_string(attributes)
    query_string += where_join_string + " AND " if where_join_string else ""
    where_ref_string = get_WHERE_REFERENCE_query_string(in_table_name)
    query_string += where_ref_string + " AND " if where_ref_string else ""
    query_string += get_WHERE_ATTRIBUTES_query_string(attributes, in_table_name)
    query_string = get_ORDER_BY_ATTRIBUTES_query_string(attributes, query_string, in_table_name)
    print(query_string)
    values = []
    for a in attributes:
        if a["keyword"] != 'order by':
            # if 'a' is a REAL conversational attribute
            if a.get('value'):
                val = str(a['value'])
                if a['operator'] == 'LIKE':
                    val_words = val.split()
                    #val = '%'+val+'%
                    val = ' '.join('%'+word+'%' for word in val_words)
                values.extend([val] * len(a['columns']))
            # if 'a' is a mocked relation
            elif a.get('join_values'):
                values.extend(a['join_values'])
    tup = tuple(values)
    print(tup)
    rows = execute_query_select(query_string, tup)
    return get_dictionary_result(query_string, tup, rows, get_table_schema_from_name(in_table_name)['column_list'], attributes)


def query_join(element, relation):

    to_table_name = relation['by'][-1]['to_table_name']  # the table is the last one of the last "by" in the relation

    to_schema = get_table_schema_from_name(to_table_name)

    to_columns = []
    for col in to_schema['column_list']:
        to_columns.append({'column': col, 'table': to_table_name})

    for fk in get_references_from_name(to_table_name):
        for col in to_columns:
            if fk['from_attribute'] == col['column']:
                col['column'] = fk['show_attribute']
                col['table'] = fk['to_table']

    from_table_name = relation['by'][0]['from_table_name']  # the table is the one of the first "by" in the relation

    from_schema = get_table_schema_from_name(from_table_name)
    primary_columns = from_schema['primary_key_list']
    relation['join_values'] = [element['value'][0][x] for x in primary_columns]

    relation['operator'] = '='

    relation['columns'] = primary_columns

    relation = get_reverse_relation(copy.deepcopy(relation))  # HERE I REVERT THE RELATION to standardize with the attributes

    label_attributes([relation], from_table_name)

    query_string = "SELECT DISTINCT " + get_SELECT_query_string(to_columns, to_table_name)
    query_string += " FROM " + get_FROM_query_string([relation], to_table_name)
    query_string += " WHERE "
    where_join_string = get_WHERE_JOIN_query_string([relation])
    query_string += where_join_string + " AND " if where_join_string else ""
    where_ref_string = get_WHERE_REFERENCE_query_string(to_table_name)
    query_string += where_ref_string + " AND " if where_ref_string else ""
    query_string += get_WHERE_ATTRIBUTES_query_string([relation], join=True)
    query_string += get_ORDER_BY_SHOW_COLUMNS(to_table_name)
    print(query_string)

    tup = tuple(relation['join_values'])
    print(tup)
    rows = execute_query_select(query_string, tup)
    return get_dictionary_result(query_string, tup, rows, get_table_schema_from_name(to_table_name)['column_list'], [relation])  # mocking the relation as attribute


def get_reverse_relation(relation):
    if relation.get('by'):
        relation['by'].reverse()  # reverting the list like a boss
        # here I swap like a boss
        for r in relation['by']:
            r['to_table_name'], r['from_table_name'] = r['from_table_name'], r['to_table_name']
            r['to_columns'], r['from_columns'] = r['from_columns'], r['to_columns']
    return relation


def query_category(in_table_name, category):
    columns = ("category", "count")
    ref = {}

    for fk in get_references_from_name(in_table_name):
        if fk['from_attribute'] == category:
            ref = fk

    if ref:
        query_string = "SELECT " + ref['to_table'] + "." + ref['show_attribute'] + ", COUNT(*)"
        query_string += " FROM " + in_table_name + ", " + ref['to_table']
        query_string += " WHERE " + in_table_name + "." + category + " = " + ref['to_table'] + "." + ref['to_attribute']
        query_string += " GROUP BY " + in_table_name + "." + category
        query_string += " ORDER BY COUNT(*) DESC"
    else:
        query_string = "SELECT " + category + ", COUNT(*)"
        query_string += " FROM " + in_table_name
        query_string += " GROUP BY " + category
        query_string += " ORDER BY COUNT(*) DESC"

    print(query_string)
    tup = None
    rows = execute_query_select(query_string, tup)
    return get_dictionary_result(query_string, tup, rows, columns, category)


def query_category_value(element_name, table_name, category_column, category_value):
    columns = []
    for col in get_table_schema_from_name(table_name)['column_list']:
        columns.append({'column': col, 'table': table_name})

    for fk in get_references_from_name(table_name):
        for col in columns:
            if fk['from_attribute'] == col['column']:
                col['column'] = fk['show_attribute']
                col['table'] = fk['to_table']

    attribute = resolver.get_attribute_by_name(element_name, category_column['keyword'])
    attribute['value'] = category_value
    attribute['operator'] = 'LIKE'

    attributes = [attribute]
    label_attributes(attributes, table_name)

    query_string = "SELECT DISTINCT " + get_SELECT_query_string(columns, table_name)  # ugly but correct
    query_string += " FROM " + get_FROM_query_string([], table_name)
    query_string += " WHERE "
    where_ref_string = get_WHERE_REFERENCE_query_string(table_name)
    query_string += where_ref_string + " AND " if where_ref_string else ""
    query_string += get_WHERE_CATEGORY_query_string(table_name, category_column['column'])
    query_string += get_ORDER_BY_SHOW_COLUMNS(table_name)
    print(query_string)

    val = str(category_value)
    val = '%'+val+'%'
    tup = tuple([val])
    print(tup)

    rows = execute_query_select(query_string, tup)
    return get_dictionary_result(query_string, tup, rows, get_table_schema_from_name(table_name)['column_list'], attributes)


def simulate_view(table_name):
    columns_dict = get_table_view_from_name(table_name)
    columns = columns_dict['column_list']
    return columns



# query helper

def label_attributes(attributes, table_name):
    num2alpha = dict(zip(range(1, 27), string.ascii_lowercase))
    i = 2  # the 'a' is taken by the first
    for a in attributes:
        if a.get('by'):
            for idx, rel in enumerate(a['by']):
                if not idx:
                    rel['from_letter'] = 'a'
                    rel['to_letter'] = num2alpha[i]
                else:
                    rel['from_letter'] = num2alpha[i]
                    rel['to_letter'] = num2alpha[i + 1]
                    i += 1
            a['letter'] = a['by'][-1]['to_letter']  # the last letter
            i += 1
            a['from_table'] = rel['to_table_name']
        else:
            a['from_table'] = table_name


# query creators

def get_SELECT_query_string(columns, table_name):
    col_string_list = []
    for col in columns:
        col_string_list.append("{0}.{1}".format(col['table'], col['column']))
    return ", ".join(col_string_list)


def get_FROM_query_string(attributes, table_name=None):
    tab_string_list = []
    if table_name:
        tab_string_list.append('{}'.format(table_name))
    for a in attributes:
        for rel in a.get('by', []):
            from_tab_string = '{}'.format(rel['from_table_name'])
            if from_tab_string not in tab_string_list:
                tab_string_list.append(from_tab_string)
            to_tab_string = '{}'.format(rel['to_table_name'])
            if to_tab_string not in tab_string_list:
                tab_string_list.append(to_tab_string)
    for fk in get_references_from_name(table_name):
        if fk['to_table'] not in tab_string_list:
            tab_string_list.append('{}'.format(fk['to_table']))
    return ", ".join(tab_string_list)


def get_WHERE_JOIN_query_string(attributes):
    join_string_list = []
    for a in attributes:
        for rel in a.get('by', []):
            # the lists must be equally long, obviously
            for i in range(len(rel['from_columns'])):
                join_string_list.append('{}.{}={}.{}'.format(rel['from_table_name'],
                                                             rel['from_columns'][i],
                                                             rel['to_table_name'],
                                                             rel['to_columns'][i]))
    return " AND ".join(join_string_list)


def get_WHERE_ATTRIBUTES_query_string(attributes, table_name = None, join = False):
    attr_string_list = []
    already_in = []
    or_clause = False
    and_clause = False
    for index,a in enumerate(attributes):
        if a['keyword'] != 'order by':
            if not or_clause:
                open_bracket = "( "
            else:
                open_bracket = " "
            or_clause = False
            and_clause = False
            attr = ""
            attr += " OR ".join(["{}.{} {} %s".format(a['from_table'],  # not so pretty
                                                    col,
                                                    a['operator'])
                                for col in a['columns']])
            if 'and_or' in a:
                if a['and_or'] == 'or':
                    or_clause = True
                    close_bracket = " OR"
                else:
                    and_clause = True
                    close_bracket = " )"
            else:
                close_bracket = " )"
            if index > 0 and 'and_or' in attributes[index-1]:
                if attributes[index-1]['and_or'] == 'or':
                    prec_or_clause = True
            else:
                prec_or_clause = False
            if attr not in already_in or join or prec_or_clause:
                prec_or_clause = False
                already_in.append(attr)
                attr = open_bracket + attr + close_bracket
                if and_clause:
                    attr += " AND"
                attr_string_list.append(attr)
            else:
                primary_key = get_table_schema_from_name(table_name)['primary_key_list']
                primary_key_string =  table_name + "." + primary_key[0]

                attr = "( "
                attr += primary_key_string
                attr += " IN ( SELECT DISTINCT " + primary_key_string
                attr += " FROM " + get_FROM_query_string(attributes, table_name)
                attr += " WHERE "
                where_join_string = get_WHERE_JOIN_query_string(attributes)
                attr += where_join_string + " AND " if where_join_string else ""
                attr += " OR ".join(["{}.{} {} %s".format(a['from_table'], col, a['operator']) for col in a['columns']])
                attr += " ) )"
                if 'and_or' in a:
                    if a['and_or'] == 'or':
                        attr += " OR"
                    else:
                        attr += " AND"
                attr_string_list.append(attr)
    return " ".join(attr_string_list)


def get_WHERE_REFERENCE_query_string(table_name):
    ref_string_list = []
    for ref in get_references_from_name(table_name):
        ref_string_list.append('{}.{}={}.{}'.format(table_name,
                                                     ref['from_attribute'],
                                                     ref['to_table'],
                                                     ref['to_attribute']))
    return " AND ".join(ref_string_list)


def get_WHERE_CATEGORY_query_string(table_name, category_column):
    ret_string = '{}.{} LIKE %s'.format(table_name, category_column)
    for fk in get_references_from_name(table_name):
        if fk['from_attribute'] == category_column:
            ret_string = '{}.{} LIKE %s'.format(fk['to_table'], fk['show_attribute'])
    return ret_string


def get_ORDER_BY_ATTRIBUTES_query_string(attributes, query, in_table_name):
    #attr_string_list = []
    isOrder = False
    tokens = [token for token in query.split(" ") if token != ""]
    if tokens[-1] == 'AND' or tokens[-1] == 'OR': #check if there is a AND/OR before order by clause
        del tokens[-1]
    order_clause = " ".join(tokens)
    for a in attributes:
        if a['keyword'] == 'order by':
            isOrder = True
            order = " ".join(["{}.{}".format(a['from_table'], a['value'])])
            #attr_string_list.append(order)
            order_clause += ' ORDER BY '
            order_clause += order
    if not isOrder:
        order_clause += get_ORDER_BY_SHOW_COLUMNS(in_table_name)
    return order_clause

def get_ORDER_BY_SHOW_COLUMNS(in_table_name):
    element_name = resolver.get_element_name_from_table_name(in_table_name)
    default_order_columns = resolver.extract_show_columns(element_name)[0]['columns']
    if default_order_columns:
        order_clause = ' ORDER BY '
        order_clause += ", ".join(["{}.{}".format(in_table_name, col) for col in default_order_columns])
    return order_clause
