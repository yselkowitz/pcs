from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from unittest import TestCase

from lxml import etree

from pcs.lib import error_codes
from pcs.lib.cib.constraint import resource_set
from pcs.lib.errors import ReportItemSeverity as severities
from pcs.test.tools.assertions import(
    assert_raise_library_error,
    assert_xml_equal
)
from pcs.test.tools.pcs_mock import mock


class PrepareSetTest(TestCase):
    def test_return_corrected_resurce_set(self):
        find_valid_id = mock.Mock()
        find_valid_id.side_effect = lambda id: {"A": "AA", "B": "BB"}[id]
        self.assertEqual(
            {"ids": ["AA", "BB"], "attrib": {"sequential": "true"}},
            resource_set.prepare_set(find_valid_id, {
                "ids": ["A", "B"],
                "attrib": {"sequential": "true"}
            })
        )

    def test_refuse_invalid_attribute_name(self):
        assert_raise_library_error(
            lambda: resource_set.prepare_set(mock.Mock(), {
                "ids": ["A", "B"],
                "attrib": {"invalid_name": "true"}
            }),
            (severities.ERROR, error_codes.INVALID_OPTION, {
                'allowed_raw': ['action', 'require-all', 'role', 'sequential'],
                'option': 'invalid_name',
            }),
        )

    def test_refuse_invalid_attribute_value(self):
        assert_raise_library_error(
            lambda: resource_set.prepare_set(mock.Mock(), {
                "ids": ["A", "B"],
                "attrib": {"role": "invalid"}
            }),
            (severities.ERROR, error_codes.INVALID_OPTION_VALUE, {
                'option_name': 'role',
                'allowed_values_raw': ('Stopped', 'Started', 'Master', 'Slave'),
                'option_value': 'invalid',
            }),
        )

class ExtractIdListTest(TestCase):
    def test_return_id_list_from_resource_set_list(self):
        self.assertEqual(
            [["A", "B"], ["C", "D"]],
            resource_set.extract_id_set_list([
                {"ids": ["A", "B"], "attrib": {}},
                {"ids": ["C", "D"], "attrib": {}},
            ])
        )

class CreateTest(TestCase):
    def test_resource_set_to_parent(self):
        constraint_element = etree.Element("constraint")
        resource_set.create(
            constraint_element,
            {"ids": ["A", "B"], "attrib": {"sequential": "true"}},
        )
        assert_xml_equal(etree.tostring(constraint_element).decode(), """
            <constraint>
              <resource_set id="pcs_rsc_set_A_B" sequential="true">
                <resource_ref id="A"></resource_ref>
                <resource_ref id="B"></resource_ref>
              </resource_set>
            </constraint>
        """)

class GetResourceIdListTest(TestCase):
    def test_returns_id_list_from_element(self):
        element = etree.Element("resource_set")
        for id in ("A", "B"):
            etree.SubElement(element, "resource_ref").attrib["id"] = id

        self.assertEqual(
            ["A", "B"],
            resource_set.get_resource_id_set_list(element)
        )

class ExportTest(TestCase):
    def test_returns_element_in_dict_representation(self):
        element = etree.Element("resource_set")
        element.attrib.update({"role": "Master"})
        for id in ("A", "B"):
            etree.SubElement(element, "resource_ref").attrib["id"] = id

        self.assertEqual(
            {'attrib': {'role': 'Master'}, 'ids': ['A', 'B']},
            resource_set.export(element)
        )
