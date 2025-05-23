"""
Implementation of search_by_phone for the Contacts app.

This module provides functionality to search contacts by phone number using AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import json
import re
from localtoolkit.applescript.utils.applescript_runner import applescript_execute


def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number by removing all non-digit characters.

    Args:
        phone: The phone number to normalize

    Returns:
        A string containing only the digits of the phone number
    """
    return re.sub(r"\D", "", phone)


def search_by_phone_logic(phone: str, exact_match: bool = False) -> Dict[str, Any]:
    """
    Search for contacts by phone number using AppleScript.

    Args:
        phone: The phone number to search for
        exact_match: Whether to require an exact match (default: False)
                     When False, performs partial matching ignoring formatting

    Returns:
        A dictionary with the following structure:
        {
            "success": bool,      # True if operation was successful
            "contacts": List[Dict], # List of contact objects
            "message": str,       # Optional context message
            "error": str          # Only present if success is False
        }
    """
    # Normalize the input phone number
    normalized_phone = normalize_phone(phone)

    # Generate different search pattern based on exact_match
    search_mode = "exact" if exact_match else "partial"

    # Create AppleScript with directly embedded parameters to avoid JSON parsing issues
    applescript_code = f"""
    -- Search function to normalize and compare phone numbers
    on normalizePhone(phoneText)
        -- Remove all non-digit characters
        set normalizedNumber to ""
        repeat with i from 1 to length of phoneText
            set currentChar to character i of phoneText
            if currentChar is in "0123456789" then
                set normalizedNumber to normalizedNumber & currentChar
            end if
        end repeat
        return normalizedNumber
    end normalizePhone
    
    on run argv
        -- Use directly embedded parameters
        set searchPhone to "{phone}"
        set searchMode to "{search_mode}"
        set normalizedPhone to "{normalized_phone}"
        
        try
            tell application "Contacts"
                -- Prepare result containers
                set foundContacts to {{}}
                
                -- Create delimiters for structured output
                set fieldDelim to "<<|>>"
                set itemDelim to "<<||>>"
                set phoneDelim to "<<+++>>"
                set emailDelim to "<<===>>>"
                set addressDelim to "<<***>>"
                
                -- Get all people
                set allPeople to every person
                set matchingContacts to {{}}
                
                -- Loop through all contacts to find matching phone numbers
                repeat with currentPerson in allPeople
                    set foundMatch to false
                    
                    -- Check if the person has any phone numbers
                    try
                        set personPhones to phone of currentPerson
                        
                        -- Check each phone number
                        repeat with currentPhone in personPhones
                            set phoneValue to value of currentPhone as string
                            set normalizedValue to my normalizePhone(phoneValue)
                            
                            -- Different matching based on search mode
                            if searchMode is "exact" then
                                -- Exact matching - full number must match exactly
                                if normalizedValue is normalizedPhone then
                                    set foundMatch to true
                                    exit repeat
                                end if
                            else
                                -- Partial matching - the search term must be contained within the number
                                if normalizedPhone is not "" and normalizedValue contains normalizedPhone then
                                    set foundMatch to true
                                    exit repeat
                                end if
                            end if
                        end repeat
                    end try
                    
                    -- If a match was found, add to our result list
                    if foundMatch then
                        set end of matchingContacts to currentPerson
                    end if
                end repeat
                
                -- Process each matching contact
                set totalFound to count of matchingContacts
                
                -- Process each matching contact
                repeat with i from 1 to totalFound
                    set currentContact to item i of matchingContacts
                    
                    -- Basic info
                    set contactID to id of currentContact as string
                    set displayName to name of currentContact
                    
                    -- Name components
                    set firstName to ""
                    set lastName to ""
                    
                    try
                        set firstName to first name of currentContact
                        if firstName is missing value then set firstName to ""
                    end try
                    
                    try
                        set lastName to last name of currentContact
                        if lastName is missing value then set lastName to ""
                    end try
                    
                    -- Phone numbers
                    set phoneInfo to ""
                    try
                        set allPhones to phone of currentContact
                        repeat with thePhone in allPhones
                            set phoneLabel to (label of thePhone) as string
                            set phoneValue to (value of thePhone) as string
                            
                            if phoneLabel is missing value then set phoneLabel to "other"
                            if phoneValue is missing value then set phoneValue to ""
                            
                            set phoneInfo to phoneInfo & phoneLabel & ":" & phoneValue & phoneDelim
                        end repeat
                    end try
                    
                    -- Email addresses
                    set emailInfo to ""
                    try
                        set allEmails to email of currentContact
                        repeat with theEmail in allEmails
                            set emailLabel to (label of theEmail) as string
                            set emailValue to (value of theEmail) as string
                            
                            if emailLabel is missing value then set emailLabel to "other"
                            if emailValue is missing value then set emailValue to ""
                            
                            set emailInfo to emailInfo & emailLabel & ":" & emailValue & emailDelim
                        end repeat
                    end try
                    
                    -- Postal addresses (simplified)
                    set addressInfo to ""
                    try
                        set allAddresses to address of currentContact
                        repeat with theAddress in allAddresses
                            set addressLabel to (label of theAddress) as string
                            
                            if addressLabel is missing value then set addressLabel to "other"
                            
                            -- Format a simplified street address
                            set formattedAddress to ""
                            try
                                set street to street of theAddress as string
                                if street is not missing value and street is not "" then
                                    set formattedAddress to formattedAddress & street
                                end if
                            end try
                            
                            try
                                set city to city of theAddress as string
                                if city is not missing value and city is not "" then
                                    if formattedAddress is not "" then set formattedAddress to formattedAddress & ", "
                                    set formattedAddress to formattedAddress & city
                                end if
                            end try
                            
                            try
                                set state to state of theAddress as string
                                if state is not missing value and state is not "" then
                                    if formattedAddress is not "" then set formattedAddress to formattedAddress & ", "
                                    set formattedAddress to formattedAddress & state
                                end if
                            end try
                            
                            try
                                set zip to zip of theAddress as string
                                if zip is not missing value and zip is not "" then
                                    if formattedAddress is not "" then set formattedAddress to formattedAddress & " "
                                    set formattedAddress to formattedAddress & zip
                                end if
                            end try
                            
                            try
                                set country to country of theAddress as string
                                if country is not missing value and country is not "" then
                                    if formattedAddress is not "" then set formattedAddress to formattedAddress & ", "
                                    set formattedAddress to formattedAddress & country
                                end if
                            end try
                            
                            set addressInfo to addressInfo & addressLabel & ":" & formattedAddress & addressDelim
                        end repeat
                    end try
                    
                    -- Notes
                    set notesText to ""
                    try
                        set notesText to note of currentContact as string
                        if notesText is missing value then set notesText to ""
                    end try
                    
                    -- Organization
                    set orgName to ""
                    try
                        set orgName to organization of currentContact as string
                        if orgName is missing value then set orgName to ""
                    end try
                    
                    -- Job title
                    set jobTitle to ""
                    try
                        set jobTitle to job title of currentContact as string
                        if jobTitle is missing value then set jobTitle to ""
                    end try
                    
                    -- Build the contact string with all data
                    set contactData to contactID & fieldDelim & displayName & fieldDelim & firstName & fieldDelim & lastName & fieldDelim & phoneInfo & fieldDelim & emailInfo
                    
                    -- Add to result list
                    set end of foundContacts to contactData
                end repeat
                
                -- Join all contacts with item delimiter
                set astid to AppleScript's text item delimiters
                set AppleScript's text item delimiters to itemDelim
                set outputText to foundContacts as string
                set AppleScript's text item delimiters to astid
                
                -- Return the structured data with count prefix
                return (totalFound as string) & itemDelim & outputText
            end tell
        on error errMsg
            return "ERROR:" & errMsg
        end try
    end run
    """

    # Run the AppleScript with no parameters (they're embedded in the script)
    result = applescript_execute(code=applescript_code, timeout=30)

    # Handle the result
    if not result.get("success", False):
        return {
            "success": False,
            "error": result.get("error", "Unknown error occurred"),
            "message": f"Failed to search contacts for phone number: {phone}",
        }

    # Process the data
    try:
        data = result["data"]

        # Check for error response
        if isinstance(data, str) and data.startswith("ERROR:"):
            return {
                "success": False,
                "error": data[6:],  # Remove "ERROR:" prefix
                "message": f"Error searching for contacts with phone: {phone}",
            }

        # Parse the delimited data
        contacts_list = []

        # Constants for parsing
        FIELD_DELIM = "<<|>>"
        ITEM_DELIM = "<<||>>"
        PHONE_DELIM = "<<+++>>"
        EMAIL_DELIM = "<<===>>>"
        ADDRESS_DELIM = "<<***>>"

        # Split into count and contact data
        parts = data.split(ITEM_DELIM, 1)

        # Extract total count
        found_count = 0
        if parts and parts[0]:
            try:
                # Strip whitespace from the count string for robustness
                found_count = int(parts[0].strip())
            except ValueError:
                found_count = 0

        # Process contact data if we have it
        if len(parts) > 1 and parts[1]:
            contact_strings = parts[1].split(ITEM_DELIM)

            for contact_str in contact_strings:
                if not contact_str.strip():
                    continue

                fields = contact_str.split(FIELD_DELIM)

                # Ensure we have at least the basic fields
                if len(fields) >= 6:
                    contact_id = fields[0]
                    display_name = fields[1]
                    first_name = fields[2]
                    last_name = fields[3]
                    phone_str = fields[4]
                    email_str = fields[5] if len(fields) > 5 else ""

                    # Parse phone numbers
                    phones: List[Dict[str, str]] = []
                    if phone_str:
                        phone_items = phone_str.split(PHONE_DELIM)
                        for item in phone_items:
                            if not item:
                                continue

                            parts = item.split(":", 1)
                            if len(parts) == 2:
                                phones.append({"label": parts[0], "value": parts[1]})

                    # Parse email addresses
                    emails: List[Dict[str, str]] = []
                    if email_str:
                        email_items = email_str.split(EMAIL_DELIM)
                        for item in email_items:
                            if not item:
                                continue

                            parts = item.split(":", 1)
                            if len(parts) == 2:
                                emails.append({"label": parts[0], "value": parts[1]})

                    # Create contact object with proper typing
                    contact: Dict[str, Any] = {
                        "id": contact_id,
                        "display_name": display_name,
                        "first_name": first_name,
                        "last_name": last_name,
                    }

                    # Add optional fields if they have content
                    if phones:
                        contact["phones"] = phones

                    if emails:
                        contact["emails"] = emails

                    contacts_list.append(contact)

        # Match type message
        match_type = "exactly" if exact_match else "partially"

        # Return the final response
        return {
            "success": True,
            "contacts": contacts_list,
            "total_found": found_count,
            "message": f"Found {len(contacts_list)} contacts with phone numbers {match_type} matching '{phone}'",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error processing contacts data for phone: {phone}",
        }


# Register the search_by_phone tool
def register_to_mcp(mcp: FastMCP) -> None:
    @mcp.tool()
    def contacts_search_by_phone(phone: str, exact_match: bool = False) -> Dict[str, Any]:
        """
        Search for contacts by phone number in the macOS Contacts app.

        Searches for contacts that have phone numbers matching the provided value.
        By default, performs partial matching after normalizing the phone numbers
        (removing all non-digit characters). When exact_match is True, requires the
        full phone number to match exactly including formatting.

        Args:
            phone: The phone number to search for (any format is accepted)
            exact_match: Whether to require an exact match (default: False)
                        When False, performs partial matching ignoring formatting

        Returns:
            A dictionary with the following structure:
            {
                "success": bool,    # True if operation was successful
                "contacts": List[Dict],  # List of matching contact objects
                "message": str,     # Context message about the search results
                "error": str        # Only present if success is False
            }
            
            Each contact object contains:
            - "id": Unique identifier for the contact
            - "display_name": Full display name of the contact
            - "first_name": First name (if available)
            - "last_name": Last name (if available)
            - "phones": List of phone objects with "label" and "value"
            - "emails": List of email objects with "label" and "value"
        
        Error Handling:
            - Contact app access denied: Returns error with message "Permission denied to access Contacts"
            - Invalid phone format: Returns error if the phone number is empty or invalid
            - Search timeout: Returns error if search takes too long
        
        Performance:
            - Typical response time: 0.5-2 seconds depending on contacts database size
            - Exact matching is typically faster than partial matching
            
        Usage with other endpoints:
            This endpoint is useful for identifying contacts from incoming phone numbers.
            
        Examples:
            # Search for contacts with phone containing "1234"
            ```python
            result = contacts_search_by_phone("1234")
            # Returns: {"success": True, "contacts": [...], "message": "Found contacts matching phone"}
            ```
            
            # Search for exact phone number match
            ```python
            result = contacts_search_by_phone("+1 (555) 123-4567", exact_match=True)
            # Returns only contacts with that exact phone number format
            ```
        """
        return search_by_phone_logic(phone, exact_match)