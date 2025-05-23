"""Contacts-specific test fixtures and configurations."""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_contact_data():
    """Return sample contact data for testing."""
    return [
        {
            "id": "contact-1",
            "display_name": "John Smith",
            "first_name": "John",
            "last_name": "Smith",
            "phones": [
                {"label": "mobile", "value": "(555) 123-4567"},
                {"label": "work", "value": "+1 555 987 6543"}
            ],
            "emails": [
                {"label": "work", "value": "john.smith@company.com"},
                {"label": "home", "value": "john@example.com"}
            ],
            "addresses": [
                {
                    "label": "home",
                    "components": {
                        "street": "123 Main St",
                        "city": "Springfield",
                        "state": "CA",
                        "zip": "90210",
                        "country": "USA"
                    }
                }
            ],
            "organization": "Acme Corp",
            "notes": "Important client"
        },
        {
            "id": "contact-2",
            "display_name": "Jane Doe",
            "first_name": "Jane",
            "last_name": "Doe",
            "phones": [
                {"label": "mobile", "value": "(555) 234-5678"}
            ],
            "emails": [
                {"label": "personal", "value": "jane.doe@email.com"}
            ],
            "addresses": [],
            "birthday": "1985-06-15"
        },
        {
            "id": "contact-3",
            "display_name": "Bob Johnson",
            "first_name": "Bob",
            "last_name": "Johnson",
            "phones": [
                {"label": "home", "value": "(555) 345-6789"},
                {"label": "mobile", "value": "555-456-7890"}
            ],
            "emails": [],
            "addresses": []
        }
    ]


@pytest.fixture
def mock_applescript_contact_output():
    """Return mock AppleScript output for contact search."""
    # This simulates the delimited output from AppleScript
    return """3<<||>>contact-1<<|>>John Smith<<|>>John<<|>>Smith<<|>>mobile:(555) 123-4567<<+++>>work:+1 555 987 6543<<+++>><<|>>work:john.smith@company.com<<===>>>home:john@example.com<<===>>><<|>>home:street:123 Main St,city:Springfield,state:CA,zip:90210,country:USA,<<***>><<|>><<|>>Important client<<|>>Acme Corp<<||>>contact-2<<|>>Jane Doe<<|>>Jane<<|>>Doe<<|>>mobile:(555) 234-5678<<+++>><<|>>personal:jane.doe@email.com<<===>>><<|>><<|>>1985-June-15<<|>><<|>><<||>>contact-3<<|>>Bob Johnson<<|>>Bob<<|>>Johnson<<|>>home:(555) 345-6789<<+++>>mobile:555-456-7890<<+++>><<|>><<|>><<|>><<|>><<|>>"""


@pytest.fixture
def mock_applescript_phone_output():
    """Return mock AppleScript output for phone search."""
    # This simulates finding a contact by phone number
    return """1<<||>>contact-1<<|>>John Smith<<|>>John<<|>>Smith<<|>>mobile:(555) 123-4567<<+++>>work:+1 555 987 6543<<+++>><<|>>work:john.smith@company.com<<===>>>home:john@example.com<<===>>>"""


@pytest.fixture
def mock_applescript():
    """Mock AppleScript executor for contacts tests."""
    from unittest.mock import patch
    # Patch both search_by_name and search_by_phone modules
    with patch('localtoolkit.contacts.search_by_name.applescript_execute') as mock_name, \
         patch('localtoolkit.contacts.search_by_phone.applescript_execute') as mock_phone:
        # Set default return value
        default_return = {
            "success": True,
            "data": "0<<||>>",
            "metadata": {},
            "error": None
        }
        mock_name.return_value = default_return
        mock_phone.return_value = default_return
        
        # Create a wrapper that updates both mocks
        class MockWrapper:
            def __init__(self, name_mock, phone_mock):
                self._name = name_mock
                self._phone = phone_mock
                
            @property
            def return_value(self):
                return self._name.return_value
                
            @return_value.setter
            def return_value(self, value):
                self._name.return_value = value
                self._phone.return_value = value
                
            @property
            def side_effect(self):
                return self._name.side_effect
                
            @side_effect.setter
            def side_effect(self, value):
                self._name.side_effect = value
                self._phone.side_effect = value
                
            @property
            def called(self):
                return self._name.called or self._phone.called
                
            @property
            def call_count(self):
                return self._name.call_count + self._phone.call_count
                
            @property
            def call_args(self):
                # Return whichever was actually called
                if self._phone.called:
                    return self._phone.call_args
                return self._name.call_args
        
        yield MockWrapper(mock_name, mock_phone)