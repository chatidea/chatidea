import json
import re
import sqlparse
from click._compat import raw_input


def is_parsed_element_table_creation(parsed):
    if parsed.get_type() == 'CREATE':
        if any(t.match(sqlparse.tokens.Keyword, 'TABLE')
               for t in parsed.tokens
               if isinstance(t, sqlparse.sql.Token)):
            return True
    return False


def extract_table_name_from_tokens(tokens):
    table_name = next(t for t in tokens if isinstance(t, sqlparse.sql.Identifier))
    table_name_str = str(table_name)
    # removes the ' '
    return re.match(r'[^\w]*(\w*)', table_name_str).group(1)


def extract_lines_from_tokens(tokens):
    par = next(t for t in tokens if isinstance(t, sqlparse.sql.Parenthesis))
    par_str = str(par)[1:-1]  # removes the ( )
    # split on commas if not in parentheses, using negative lookahead
    return re.split(r',(?![^()]*\))', par_str, re.DOTALL)


def extract_ddl_list(str):
    string_list = str.split(',')
    return list(re.match(r'[^\w]*(\w*)', s).group(1) for s in string_list)


def parse_schema_file():

    schema = dict()

    # with open('../../resources/db/employees.sql') as f:
    #with open('../../resources/db/rasa_db.sql') as f:
    with open('../../resources/db/mysqlsampledatabase.sql') as f:
        raw = f.read()

    for s in sqlparse.split(raw):
        for parsed in sqlparse.parse(s):
            if is_parsed_element_table_creation(parsed):

                table_name = extract_table_name_from_tokens(parsed.tokens)

                table_dict = dict()
                table_dict['column_list'] = []
                table_dict['primary_key_list'] = []
                table_dict['references'] = {}

                lines = extract_lines_from_tokens(parsed.tokens)

                for l in lines:

                    match_column = re.match(r'[^\w]*(\w*)', l, re.DOTALL)
                    match_primary = re.match(r'.*PRIMARY KEY[^\(]*\((.*)\)', l, re.DOTALL)
                    match_constraint = re.match(r'.*FOREIGN KEY[^\(]*\((.*)\).*REFERENCES[^\w]*(\w*)[^\(]*\((.*)\)',
                                                l, re.DOTALL)
                    if match_column:
                        if match_column.group(1) not in ['PRIMARY', 'FOREIGN', 'UNIQUE', 'KEY', 'CONSTRAINT']:
                            table_dict['column_list'].append(match_column.group(1))
                    if match_primary:
                        table_dict['primary_key_list'].extend(extract_ddl_list(match_primary.group(1)))
                    if match_constraint:

                        ref = dict()
                        ref['foreign_key_list'] = extract_ddl_list(match_constraint.group(1))
                        ref['reference_key_list'] = extract_ddl_list(match_constraint.group(3))

                        reference_table_name = match_constraint.group(2)
                        table_dict['references'][reference_table_name] = ref

                schema[table_name] = table_dict
                # for fp in table_dict['foreign_property_list']:
                #   print('{} - {}'.format(table_dict['table_name'], fp['reference_table_name']))

    with open('../../resources/db/db_schema_c.json', 'w') as f:
        json.dump(schema, f, indent=2)


def ask_number(choices, default=0):
    for i, e in enumerate(choices):
        print('{} - {}'.format(i, e))
    while True:
        el = raw_input('(Default: {})\n'.format(default)) or default
        try:
            el = int(el)
            return choices[el]
        except (ValueError, IndexError):
            print('Enter an correct value!')


def create_concept_file():
    with open('../../resources/db/db_schema_c.json') as f:
        schema = json.load(f)

    concept = {}

    for table_name in schema:
        print('TABLE: {}'.format(table_name))

        print('NAME?')
        name = raw_input('(Default: {})\n'.format(table_name)) or table_name
        types = ['primary', 'secondary', 'crossable']
        print('TYPE?')
        chosen_type = ask_number(types)
        concept[name] = {'type': chosen_type, 'table_name': table_name}

    with open('../../resources/db/db_concept_c.json', 'w') as f:
        json.dump(concept, f, indent=2)


if __name__ == '__main__':
    parse_schema_file()
    #create_concept_file()
