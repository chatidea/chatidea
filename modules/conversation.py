import copy
import logging
import pprint
from logging import handlers

from modules.database import resolver
from modules.patterns import msg, btn
from settings import LOG_DIR_PATH_AND_SEP, ELEMENT_VISU_LIMIT, CONTEXT_VISU_LIMIT, CONTEXT_MAX_LENGTH

"""
{'action_name': '...found with attribute(s) "located in Spain".',
 'attributes': [{'columns': ['city', 'state', 'country'],
                 'keyword': 'located in',
                 'letter': 'a',
                 'operator': 'LIKE',
                 'type': 'word',
                 'value': 'Spain'}],
 'element_name': 'customer',
 'query': {'q_string': 'SELECT DISTINCT a.customerNumber, a.customerName, '
                       'a.contactLastName, a.contactFirstName, a.phone, '
                       'a.addressLine1, a.addressLine2, a.city, a.state, '
                       'a.postalCode, a.country, a.salesRepEmployeeNumber, '
                       'a.creditLimit FROM customers a WHERE ( a.city LIKE %s '
                       'OR a.state LIKE %s OR a.country LIKE %s )',
           'q_tuple': ('%Spain%', '%Spain%', '%Spain%')},
 'real_value_length': 7,
 'show': {'from': 0, 'to': 5},
 'value': [{'addressLine1': 'C/ Moralzarzal, 86',
            'addressLine2': None,
            'city': 'Madrid',
            'contactFirstName': 'Diego ',
            'contactLastName': 'Freyre',
            'country': 'Spain',
            'creditLimit': Decimal('227600.00'),
            'customerName': 'Euro+ Shopping Channel',
            'customerNumber': 141,
            'phone': '(91) 555 94 44',
            'postalCode': '28034',
            'salesRepEmployeeNumber': 1370,
            'state': None},
           {'addressLine1': 'Rambla de Cataluña, 23',
            'addressLine2': None,
            'city': 'Barcelona',
            'contactFirstName': 'Eduardo ',
            'contactLastName': 'Saavedra',
            'country': 'Spain',
            'creditLimit': Decimal('60300.00'),
            'customerName': 'Enaco Distributors',
            'customerNumber': 216,
            'phone': '(93) 203 4555',
            'postalCode': '08022',
            'salesRepEmployeeNumber': 1702,
            'state': None},
           {'addressLine1': 'Gran Vía, 1',
            'addressLine2': None,
            'city': 'Madrid',
            'contactFirstName': 'Alejandra ',
            'contactLastName': 'Camino',
            'country': 'Spain',
            'creditLimit': Decimal('0.00'),
            'customerName': 'ANG Resellers',
            'customerNumber': 237,
            'phone': '(91) 745 6555',
            'postalCode': '28001',
            'salesRepEmployeeNumber': None,
            'state': None},
           {'addressLine1': 'Merchants House',
            'addressLine2': "27-30 Merchant's Quay",
            'city': 'Madrid',
            'contactFirstName': 'Jesus',
            'contactLastName': 'Fernandez',
            'country': 'Spain',
            'creditLimit': Decimal('59600.00'),
            'customerName': 'CAF Imports',
            'customerNumber': 344,
            'phone': '+34 913 728 555',
            'postalCode': '28023',
            'salesRepEmployeeNumber': 1702,
            'state': None},
           {'addressLine1': 'C/ Araquil, 67',
            'addressLine2': None,
            'city': 'Madrid',
            'contactFirstName': 'Martín ',
            'contactLastName': 'Sommer',
            'country': 'Spain',
            'creditLimit': Decimal('104600.00'),
            'customerName': 'Corrida Auto Replicas, Ltd',
            'customerNumber': 458,
            'phone': '(91) 555 22 82',
            'postalCode': '28023',
            'salesRepEmployeeNumber': 1702,
            'state': None},
           {'addressLine1': 'c/ Gobelas, 19-1 Urb. La Florida',
            'addressLine2': None,
            'city': 'Madrid',
            'contactFirstName': 'Carmen',
            'contactLastName': 'Anton',
            'country': 'Spain',
            'creditLimit': Decimal('0.00'),
            'customerName': 'Anton Designs, Ltd.',
            'customerNumber': 465,
            'phone': '+34 913 728555',
            'postalCode': '28023',
            'salesRepEmployeeNumber': None,
            'state': None},
           {'addressLine1': 'C/ Romero, 33',
            'addressLine2': None,
            'city': 'Sevilla',
            'contactFirstName': 'José Pedro ',
            'contactLastName': 'Roel',
            'country': 'Spain',
            'creditLimit': Decimal('65700.00'),
            'customerName': 'Iberia Gift Imports, Corp.',
            'customerNumber': 484,
            'phone': '(95) 555 82 82',
            'postalCode': '41101',
            'salesRepEmployeeNumber': 1702,
            'state': None}]}
"""


class Context:

    def __init__(self, chat_id):
        self.context_list = []
        self.reset_show_context_list = True
        self.context_list_indices = {'up': 0, 'down': 0}
        self.reset_show_last_element = True
        self.logger = logging.Logger(__name__, logging.INFO)
        self.log_path = LOG_DIR_PATH_AND_SEP + 'context_' + str(chat_id) + '.log'
        log_handler = handlers.RotatingFileHandler(self.log_path, maxBytes=500)
        log_handler.setLevel(logging.INFO)
        log_handler.setFormatter(logging.Formatter('--> %(asctime)s:\n'
                                                   '%(message)s\n'))
        self.logger.addHandler(log_handler)
        self.log(' ********* NEW INITIALIZATION OF LOG FILE ********* ')

    def reset_context_list(self):
        self.logger.info('The context has been reset')
        del self.context_list[:]

    def get_element_by_name(self, element_name):
        """
        Returns None if the element is not found
        """
        return next(filter(lambda el: el['element_name'] == element_name, self.context_list), None)

    def get_last_element(self):
        """
        Returns None if the context_list is empty
        """
        return self.context_list[-1] if self.context_list else None

    def get_second_to_last_element(self):
        """
        Returns None if the context_list is empty
        """
        return self.context_list[-2] if self.context_list and len(self.context_list) > 1 else None

    def view_last_element(self):
        if self.reset_show_last_element:
            self.show_last_element_from_start()
        self.reset_show_last_element = True
        return self.get_last_element()

    def view_second_to_last_element(self):
        if self.reset_show_last_element:
            self.show_second_to_last_element_from_start()
        self.reset_show_last_element = True
        return self.get_second_to_last_element()

    def append_element(self, element):
        # NEW feature: deletes the element of the same type and all its predecessor
        # the search is limited to the context excluding the last element
        """ NEW FEATURE HERE
        index = -1
        for i, el in enumerate(self.context_list):
            if el['element_name'] == element['element_name']
            and i < len(self.context_list) - 1:  # keep the last
                index = i
                break
        if index > -1:
            self.logger.info('Removing elements from the context list, total: {}'.format(index + 1))
            for i in range(index + 1):
                self.context_list.pop(0)
        """

        self.context_list.append(copy.deepcopy(element))  # deep copying here
        self.show_last_element_from_start()
        self.log('Element {} has been added to the context'.format(element['element_name']))
        # max length context
        if len(self.context_list) > CONTEXT_MAX_LENGTH:
            del self.context_list[: len(self.context_list)-CONTEXT_MAX_LENGTH]
            self.log('Context length is exceeding maximum of {},'
                     ' I remove old concepts.'.format(CONTEXT_MAX_LENGTH))

        #self.log_context()

    def show_last_element_from_start(self):
        element = self.context_list[-1]
        if element['real_value_length'] > 1:
            element['show'] = {'from': 0, 'to': min(ELEMENT_VISU_LIMIT, element['real_value_length'])}

    def show_second_to_last_element_from_start(self):
        if len(self.context_list) > 1:
            element = self.context_list[-2]
            if element['real_value_length'] > 1:
                element['show'] = {'from': 0, 'to': min(ELEMENT_VISU_LIMIT, element['real_value_length'])}

    def go_back_to_position(self, position):
        del self.context_list[position:]
        self.log('Going back to position {} in the context'.format(position))
        #self.log_context()
        self.show_last_element_from_start()

    def get_context_list(self):
        return self.context_list

    def view_context_list(self):
        if self.reset_show_context_list:
            self.show_context_list_from_start()
        self.reset_show_context_list = True
        return self.get_context_list()

    def show_context_list_from_start(self):
        self.context_list_indices['up'] = len(self.context_list)
        self.context_list_indices['down'] = max(len(self.context_list) - CONTEXT_VISU_LIMIT, 0)

    def log_context(self):
        """
        Logs the context_list in a human-readable way
        """
        string_log = 'The context of the conversation at this moment' \
                     ' is {} element(s) long:\n'.format(len(self.context_list))
        for i, el in enumerate(self.context_list):
            string_log += 'POSITION {}:'.format(i+1)
            if i == len(self.context_list)-1:
                el_mod = copy.deepcopy(el)
                if el_mod.get('real_value_length', 0) > 1:
                    el_mod['show']['to'] = el_mod['real_value_length']
                    el_mod['value'] = [b['title'] for b in btn.get_buttons_select_element(el_mod)]
            else:
                el_mod = {'action_name': copy.deepcopy(el['action_name']),
                          'element_name': copy.deepcopy(el['element_name']),
                          'real_value_length': copy.deepcopy(el['real_value_length'])}
            string_log += '\n' \
                          '{}\n'.format(pprint.pformat(el_mod))

        self.log(string_log)

    def log(self, string_log):
        self.logger.info(string_log)
