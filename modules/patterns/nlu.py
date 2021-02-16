INTENT_START = 'start'
INTENT_HELP = 'help'
INTENT_HELP_ELEMENTS = 'help_elements'
INTENT_HELP_HISTORY = 'help_history'
INTENT_HELP_GO_BACK = 'help_go_back'

INTENT_MORE_INFO_FIND = 'more_info_find'
INTENT_MORE_INFO_FILTER = 'more_info_filter'

INTENT_CROSS_RELATION = 'cross_rel'
INTENT_SHOW_RELATIONS = 'show_rel'
INTENT_SHOW_MORE_ELEMENTS = 'show_more_el'
INTENT_SHOW_LESS_ELEMENTS = 'show_less_el'
INTENT_SELECT_ELEMENT_BY_POSITION = 'sel_by_pos'
INTENT_FIND_ELEMENT_BY_ATTRIBUTE = 'find_el_by_attr'
INTENT_FILTER_ELEMENT_BY_ATTRIBUTE = 'filter_el_by_attr'
INTENT_AMBIGUITY_SOLVER = 'ambiguity_solver_intent'

INTENT_ORDER_BY = 'order_by'
INTENT_ORDER_BY_ATTRIBUTE = 'order_by_attribute'

INTENT_SHOW_MORE_EXAMPLES = 'show_more_examples'
INTENT_SHOW_MORE_EXAMPLES_ATTRIBUTE = 'sm' #1-64 bit telegram limitation
INTENT_SHOW_ATTRIBUTES_COMBINATIONS = 'ac'

VIEW_CONTEXT_ELEMENT = 'view_context_el'
INTENT_SHOW_CONTEXT = 'show_context'
INTENT_SHOW_MORE_CONTEXT = 'show_more_context'
INTENT_GO_BACK_TO_CONTEXT_POSITION = 'go_back_to_context_pos'

INTENT_FALLBACK = 'fallback'

ENTITY_ELEMENT = 'el'
ENTITY_RELATION = 'rel'
ENTITY_ATTRIBUTE = 'attr'

ENTITY_RELATED_ELEMENT_NAME = 'rel_el'
ENTITY_BY_ELEMENT_NAME = 'by'
ENTITY_WORD = 'word'
ENTITY_NUMBER = 'num'
ENTITY_COLUMNS = 'columns'
ENTITY_OPERATOR_NUMBER = 'op_num'
ENTITY_POSITION = 'pos'
ENTITY_PHRASE = 'phrase'

VALUE_POSITION_RESET_CONTEXT = -111  # going back to position -111 means deleting the context

INTENT_SHOW_TABLE_CATEGORIES = 'show_table'
INTENT_FIND_ELEMENT_BY_CATEGORY = 'find_category'
