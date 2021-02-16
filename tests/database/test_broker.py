from unittest import TestCase

from modules.database import broker as b


class TestBroker(TestCase):
    customer_in_context = {
        'element_name': 'customer',
        'value': [
            {
                'customerNumber': 114, 'customerName': 'Australian Collectors, Co.',
                'contactLastName': 'Ferguson', 'contactFirstName': 'Peter', 'phone': '03 9520 4555',
                'addressLine1': '636 St Kilda Road', 'addressLine2': 'Level 3', 'city': 'Melbourne',
                'state': 'Victoria', 'postalCode': '3004', 'country': 'Australia', 'salesRepEmployeeNumber': 1611,
                'creditLimit': '117300.00'
            }  # it should be Decimal('117300.00')
        ]
    }

    customer_element = {
        "element_name": "customer",
        "type": "primary",
        "table_name": "customers",
        "show_columns": ["customerName"],
        "attributes": [
            {
                "keyword": "",
                "type": "word",
                "columns": ["customerName"]
            },
            {
                "keyword": "with contact",
                "type": "word",
                "columns": ["contactLastName", "contactFirstName"]
            },
            {
                "keyword": "located in",
                "type": "word",
                "columns": ["city", "state", "country"]
            },
            {
                "keyword": "paid",
                "type": "num",
                "columns": ["amount"],
                "by": [
                    {
                        "from_table_name": "customers",
                        "from_columns": ["customerNumber"],
                        "to_table_name": "payments",
                        "to_columns": ["customerNumber"]
                    }
                ]
            },
            {
                "keyword": "ordered",
                "type": "word",
                "columns": ["productName"],
                "by": [
                    {
                        "from_table_name": "customers",
                        "from_columns": ["customerNumber"],
                        "to_table_name": "orders",
                        "to_columns": ["customerNumber"]
                    },
                    {
                        "from_table_name": "orders",
                        "from_columns": ["orderNumber"],
                        "to_table_name": "orderdetails",
                        "to_columns": ["orderNumber"]
                    },
                    {
                        "from_table_name": "orderdetails",
                        "from_columns": ["productCode"],
                        "to_table_name": "products",
                        "to_columns": ["productCode"]
                    }
                ]
            },
            {
                "keyword": "reported to",
                "type": "word",
                "columns": ["lastName", "firstName"],
                "by": [
                    {
                        "from_table_name": "customers",
                        "from_columns": ["salesRepEmployeeNumber"],
                        "to_table_name": "employees",
                        "to_columns": ["employeeNumber"]
                    }
                ]
            },
        ],
        "relations": [
            {
                "keyword": "payments made",
                "element_name": "payment",
                "by": [
                    {
                        "from_table_name": "customers",
                        "from_columns": ["customerNumber"],
                        "to_table_name": "payments",
                        "to_columns": ["customerNumber"]
                    }
                ]
            },
            {
                "keyword": "related sales representative",
                "element_name": "employee",
                "by": [
                    {
                        "from_table_name": "customers",
                        "from_columns": ["salesRepEmployeeNumber"],
                        "to_table_name": "employees",
                        "to_columns": ["employeeNumber"]
                    }
                ]
            },
            {
                "keyword": "orders made",
                "element_name": "order",
                "by": [
                    {
                        "from_table_name": "customers",
                        "from_columns": ["customerNumber"],
                        "to_table_name": "orders",
                        "to_columns": ["customerNumber"]
                    }
                ]
            }
        ]
    }

    customer_self_attribute = {
        "keyword": "test to customer",
        "type": "word",
        "table_name": "customers",
        "columns": ["customerName"],
        "by": [
            {
                "from_table_name": "customers",
                "from_columns": ["selfRelationCustNumber"],
                "to_table_name": "customers",
                "to_columns": ["customerNumber"]
            }
        ]
    }

    def addAttributesAndValues(self):
        for a in self.customer_element['attributes']:
            a['operator'] = '='

        for a in self.customer_element['attributes']:
            a['value'] = '123'

    def test_label_attribute_columns(self):
        b.label_attributes(self.customer_element['attributes'])

        for a in self.customer_element['attributes']:
            print(a['letter'])
            for r in a.get('by', []):
                print('{} {}'.format(r['from_letter'], r['to_letter']))
            print('- - -')
        # self.fail()

    def test_get_FROM_query_string(self):
        self.customer_element['attributes'].append(self.customer_self_attribute)
        self.addAttributesAndValues()
        b.label_attributes(self.customer_element['attributes'])
        print(b.get_FROM_query_string(self.customer_element['attributes']),'customers')

    def test_get_WHERE_JOIN_query_string(self):
        self.customer_element['attributes'].append(self.customer_self_attribute)
        self.addAttributesAndValues()
        b.label_attributes(self.customer_element['attributes'])
        print(b.get_WHERE_JOIN_query_string(self.customer_element['attributes']))

    def test_get_WHERE_ATTRIBUTES_query_string(self):
        self.customer_element['attributes'].append(self.customer_self_attribute)
        self.addAttributesAndValues()
        b.label_attributes(self.customer_element['attributes'])
        print(b.get_WHERE_ATTRIBUTES_query_string(self.customer_element['attributes']))

    def test_execute_query_find(self):
        b.load_db_schema()
        b.test_connection()
        attr = self.customer_element['attributes'][0]
        attr['value'] = 'Peter'
        res = b.query_find('customers', [attr])
        print(res['query']['q_string'])
        print(res['value'])

    def test_execute_query_join(self):
        b.load_db_schema()
        b.test_connection()
        res = b.query_join(self.customer_in_context, self.customer_element['relations'][1])
        print(res['query']['q_string'])
        print(res['value'])
