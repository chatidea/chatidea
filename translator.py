"""
This module takes in input the mapping (concept) of the db and generates the chatito file
"""
import random
import re
import copy
from nltk.util import ngrams
from modules.database import resolver, broker
from settings import CHATITO_TEMPLATE_PATH, CHATITO_MODEL_PATH

if __name__ == "__main__":
    MAX_NUMBER_OF_NGRAMS = 3

    resolver.load_db_concept()
    db_concept = resolver.db_concept

    broker.load_db_schema()
    broker.test_connection()

    whole_text_more_info_find = ""
    whole_text_more_info_filter = ""
    whole_text_find = ""
    whole_text_find_or = ""
    whole_text_filter = ""
    whole_text_and_or_el = ""
    whole_text_ambiguity_solver = ""
    whole_text_ambiguity_solver_words = "    "

    whole_element_text = ""
    whole_attribute_text = ""
    whole_example_type_text = ""
    whole_column_text = "@[el_columns]\n"

    idx_e = 1
    idx_e_alias = 0
    idx_tot = 0

    for e in db_concept:
        idx_tot += 1

           
        if e.get('type') == 'primary':
            #aggiunta 10/03  
            e_name = e.get('element_name')
            e_name = resolver.extract_element(e_name)
            e_name = e_name.get('table_name')
            table_schema = broker.get_table_schema_from_name(e_name)
            all_columns_name = table_schema.get('column_list')
            for column in all_columns_name:
                column_text = "    "
                column_text += column
                whole_column_text += column_text + "\n"
            if table_schema.get('column_alias_list'):
                all_columns_name_alias = table_schema.get('column_alias_list')
                for k,v in all_columns_name_alias.items():
                    column_text = "    "
                    column_text += v
                    whole_column_text += column_text + "\n"
            #fine aggiunta 
            
            whole_text_more_info_find += "    ~[show?] ~[more_info_find] @[el_{}]\n".format(idx_e)
            whole_text_more_info_filter += "    ~[show?] ~[more_info_filter] @[el_{}]\n".format(idx_e)
            whole_text_and_or_el += "~[and_or_clause_el_{}]\n".format(idx_e)

            element_text = "@[el_{}]\n" \
                           "    ".format(idx_e)
            element_text += "\n    ".join([e.get('element_name')] + e.get('aliases', []))
            whole_element_text += element_text + "\n\n"

            idx_e_alias += 1 + len(e.get('aliases', []))

            idx_a = 1
            for a in e.get('attributes', []):
                
                idx_tot += 1
                #aggiunta 10/03
                if a.get('keyword'):

                    attribute_text = "@[attr_{}_{}]\n" \
                                     "    {}".format(idx_e, idx_a, a.get('keyword'))
                    whole_attribute_text += attribute_text + "\n\n"

                example_type_text = "@[{}_{}_{}]\n".format(a.get('type'), idx_e, idx_a)

                for col in a.get('columns', []):
                    q_string = "SELECT DISTINCT {} FROM {}".format(col,
                                                          e.get('table_name')
                                                          if not a.get('by') else
                                                          a.get('by')[-1].get('to_table_name'))
                    res = list(broker.execute_query_select(q_string))
                    if res:
                        for r in res[:50]:  # max 50 examples each
                            if r[0]:
                                idx_tot += 1
                                string_word = str(r[0])
                                string_word = re.sub(r'[^a-zA-Z0-9\s]', ' ', string_word) #Replace all none alphanumeric characters with spaces
                                string_word = string_word.rstrip()
                                tokens = [token for token in string_word.split(" ") if token != ""] #Break sentence in the token, remove empty tokens
                                if len(tokens) > 2: #ngrams only string with more than 2 words
                                    k=0 #k is limitatore
                                    for i in range(len(tokens),0,-1):
                                        output = list(ngrams(tokens, i))
                                        k +=1
                                        for output_element in output:
                                            if k < MAX_NUMBER_OF_NGRAMS:
                                                output_list = list(output_element)
                                                words = output_list
                                                words[-1] = words[-1].rstrip('\'\"-,.:;!?')
                                                example_type_text += "    " + " ".join(words).lower() 
                                                example_type_text += "\n"
                                            
                                else:
                                    words = string_word.split()
                                    words[-1] = words[-1].rstrip('\'\"-,.:;!?')
                                    example_type_text += "    " + " ".join(words).lower()
                                    example_type_text += "\n"
                #fine aggiunta
                whole_example_type_text += example_type_text + "\n"
                #da qui 
                text = ""

                if a.get('keyword'):
                    text += "@[attr_{}_{}] ".format(idx_e, idx_a)

                    if a.get('type') == 'num':  # use nlu.ENTITY_ATTR?
                        text += '@[op_num?] '

                text += "@[{}_{}_{}]".format(a.get('type'), idx_e, idx_a)
                
                whole_text_find += "    ~[find] @[el_{}] ".format(idx_e) + text + " ~[and_or_clause_el_{}?]".format(idx_e) + " ~[order_by_clause?]" "\n"
                whole_text_filter += "    ~[filter] ~[those?] " + text + "\n"
                #aggiunta 10/03
                whole_text_and_or_el += "    " + "@[and] " +text + "\n"
                whole_text_and_or_el += "    " + "@[or] " +text + "\n"
                #fine aggiunta

                #single words training
                new_text = re.sub('@[attr_*[0-9]*_*[0-9]*]', '', text)
                new_text = new_text.replace(" ","", 1)
                new_text += ("\n    ")
                whole_text_ambiguity_solver_words += new_text
                
                #a qui 
                idx_a += 1
            whole_text_and_or_el += "\n"
            idx_e += 1
            

    idx_tot = min(idx_tot, 1200)  # max training set
    idx_e_alias = max(idx_e_alias, 100)
    
    #  prepending here...
    whole_text_and_or_el += "@[and]\n" + "    " + "and\n" + "\n@[or]\n" + "    "+"or\n"

    whole_text_more_info_find = "%[more_info_find]('training': '{}', 'testing': '{}')\n{}"\
        .format(idx_e_alias*2 - idx_e_alias*2 // 5, idx_e_alias*2 // 5, whole_text_more_info_find)  # 1:4 proportion

    whole_text_more_info_filter = "%[more_info_filter]('training': '{}', 'testing': '{}')\n{}" \
        .format(idx_e_alias*2 - idx_e_alias*2 // 5, idx_e_alias*2 // 5, whole_text_more_info_filter)  # 1:4 proportion

    whole_text_ambiguity_solver = whole_text_find

    whole_text_find = "%[find_el_by_attr]('training': '{}', 'testing': '{}')\n{}" \
        .format(idx_tot - idx_tot // 5, idx_tot // 5, whole_text_find)  # 1:4 proportion

    whole_text_filter = "%[filter_el_by_attr]('training': '{}', 'testing': '{}')\n{}"\
        .format(idx_tot - idx_tot // 5, idx_tot // 5, whole_text_filter)  # 1:4 proportion

    
    whole_text_ambiguity_solver = whole_text_ambiguity_solver.replace("~[find]", "~[w_question?]")
    whole_text_ambiguity_solver += (re.sub('@[el_*[0-9]*]', '', whole_text_ambiguity_solver)).replace("  @", " @")
    whole_text_ambiguity_solver = re.sub('and_or_clause_el_*[0-9]*', '', whole_text_ambiguity_solver).replace(" ~[?]", "")
    whole_text_ambiguity_solver = re.sub('order_by_clause', '', whole_text_ambiguity_solver).replace(" ~[?]", "")
    whole_text_ambiguity_solver += whole_text_ambiguity_solver_words[:-5]
    
    whole_text_ambiguity_solver = "%[ambiguity_solver_intent]('training': '{}', 'testing': '{}')\n{}"\
        .format( idx_tot - idx_tot // 5 , idx_tot // 5 , whole_text_ambiguity_solver).replace("\n    \n", "\n")
    
    final_text = "\n" + "\n".join([whole_element_text, whole_column_text.lower(), whole_attribute_text, whole_example_type_text,
                                   whole_text_find, whole_text_and_or_el,  whole_text_filter,
                                   whole_text_more_info_find, whole_text_more_info_filter,
                                    whole_text_ambiguity_solver])

    with open(CHATITO_TEMPLATE_PATH, 'r') as f:
        template = f.read()
        final_text = template + final_text
        with open(CHATITO_MODEL_PATH, 'w') as f2:
            f2.write(final_text)
