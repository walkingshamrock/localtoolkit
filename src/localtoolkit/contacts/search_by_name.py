"""
Implementation of search_by_name for the Contacts app.

This module provides functionality to search contacts by name using AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import json
import time
from localtoolkit.applescript.utils.applescript_runner import applescript_execute

def search_by_name_logic(name: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for contacts by name using AppleScript.
    
    Args:
        name: The name to search for (first name, last name, or full name)
        limit: Maximum number of results to return (default: 10)
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,      # True if operation was successful
            "contacts": List[Dict], # List of contact objects
            "message": str,       # Optional context message
            "error": str          # Only present if success is False
        }
    """
    start_time = time.time()
    
    # Escape quotes in the search name to avoid AppleScript injection
    escaped_name = name.replace('"', '\\"')
    
    # Create AppleScript with direct parameter inclusion
    applescript_code = f"""
    on run argv
        -- Using directly passed parameters
        set searchName to "{escaped_name}"
        set maxResults to {limit}
        
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
                
                -- Perform the search using multiple strategies
                set nameMatches to (every person whose name contains searchName)
                set firstNameMatches to (every person whose first name contains searchName)
                set lastNameMatches to (every person whose last name contains searchName)
                
                -- Combine all matches (will have duplicates)
                set allMatches to nameMatches & firstNameMatches & lastNameMatches
                
                -- Remove duplicates by using a dictionary-like approach
                set uniqueIDs to {{}}
                set uniqueContacts to {{}}
                
                repeat with currentContact in allMatches
                    set currentID to id of currentContact as string
                    
                    -- Check if we've already seen this contact
                    if uniqueIDs does not contain currentID then
                        -- Add to our unique lists
                        set end of uniqueIDs to currentID
                        set end of uniqueContacts to currentContact
                    end if
                end repeat
                
                -- Get total found and limit results
                set totalFound to count of uniqueContacts
                
                if totalFound > maxResults then
                    set contactsToProcess to maxResults
                else
                    set contactsToProcess to totalFound
                end if
                
                -- Process each unique contact
                repeat with i from 1 to contactsToProcess
                    set currentContact to item i of uniqueContacts
                    
                    -- Basic info
                    set contactID to id of currentContact as string
                    set displayName to name of currentContact
                    
                    -- Additional fields (with error handling)
                    set firstName to ""
                    set lastName to ""
                    set phoneInfo to ""
                    set emailInfo to ""
                    set addressInfo to ""
                    set birthdayInfo to ""
                    set notesInfo to ""
                    set organizationInfo to ""
                    
                    try
                        set firstName to first name of currentContact
                        if firstName is missing value then set firstName to ""
                    end try
                    
                    try
                        set lastName to last name of currentContact
                        if lastName is missing value then set lastName to ""
                    end try
                    
                    -- Process phone numbers
                    try
                        set allPhones to phones of currentContact
                        repeat with eachPhone in allPhones
                            set phoneLabel to label of eachPhone
                            set phoneValue to value of eachPhone
                            set phoneInfo to phoneInfo & phoneLabel & ":" & phoneValue & phoneDelim
                        end repeat
                    end try
                    
                    -- Process email addresses
                    try
                        set allEmails to emails of currentContact
                        repeat with eachEmail in allEmails
                            set emailLabel to label of eachEmail
                            set emailValue to value of eachEmail
                            set emailInfo to emailInfo & emailLabel & ":" & emailValue & emailDelim
                        end repeat
                    end try
                    
                    -- Process physical addresses
                    try
                        set allAddresses to addresses of currentContact
                        repeat with eachAddress in allAddresses
                            set addressLabel to label of eachAddress
                            set addressParts to ""
                            
                            try
                                set streetValue to street of eachAddress
                                if streetValue is not missing value then
                                    set addressParts to addressParts & "street:" & streetValue & ","
                                end if
                            end try
                            
                            try
                                set cityValue to city of eachAddress
                                if cityValue is not missing value then
                                    set addressParts to addressParts & "city:" & cityValue & ","
                                end if
                            end try
                            
                            try
                                set stateValue to state of eachAddress
                                if stateValue is not missing value then
                                    set addressParts to addressParts & "state:" & stateValue & ","
                                end if
                            end try
                            
                            try
                                set zipValue to zip of eachAddress
                                if zipValue is not missing value then
                                    set addressParts to addressParts & "zip:" & zipValue & ","
                                end if
                            end try
                            
                            try
                                set countryValue to country of eachAddress
                                if countryValue is not missing value then
                                    set addressParts to addressParts & "country:" & countryValue & ","
                                end if
                            end try
                            
                            set addressInfo to addressInfo & addressLabel & ":" & addressParts & addressDelim
                        end repeat
                    end try
                    
                    -- Get birthday if available
                    try
                        set bdayValue to birth date of currentContact
                        if bdayValue is not missing value then
                            set birthdayInfo to (year of bdayValue as string) & "-" & (month of bdayValue as string) & "-" & (day of bdayValue as string)
                        end if
                    end try
                    
                    -- Get notes if available
                    try
                        set notesValue to note of currentContact
                        if notesValue is not missing value then
                            set notesInfo to notesValue
                        end if
                    end try
                    
                    -- Get organization info
                    try
                        set orgName to organization of currentContact
                        if orgName is not missing value then
                            set organizationInfo to orgName
                        end if
                    end try
                    
                    -- Format all data with delimiters
                    set contactData to contactID & fieldDelim & displayName & fieldDelim & firstName & fieldDelim & lastName & fieldDelim & phoneInfo & fieldDelim & emailInfo & fieldDelim & addressInfo & fieldDelim & birthdayInfo & fieldDelim & notesInfo & fieldDelim & organizationInfo
                    
                    -- Add to results list
                    set end of foundContacts to contactData
                end repeat
                
                -- Format final result with delimiter
                set resultText to ""
                repeat with i from 1 to (count of foundContacts)
                    set resultText to resultText & (item i of foundContacts)
                    if i < (count of foundContacts) then
                        set resultText to resultText & itemDelim
                    end if
                end repeat
                
                -- Return with counts (ensure totalFound is a clean string)
                return (totalFound as string) & itemDelim & resultText
                
            end tell
        on error errorMessage
            -- Return error
            return "ERROR:" & errorMessage
        end try
    end run
    """
    
    # Execute the AppleScript
    result = applescript_execute(applescript_code)
    
    # Process the result
    if not result["success"]:
        return {
            "success": False,
            "contacts": [],
            "message": "Failed to search contacts",
            "error": result.get("error", "Unknown error during contact search"),
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    # Parse the output
    output = result["data"]
    
    # Check for error
    if isinstance(output, str) and output.startswith("ERROR:"):
        return {
            "success": False,
            "contacts": [],
            "message": "Error searching contacts",
            "error": output[6:],  # Remove ERROR: prefix
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    # Process valid output
    try:
        # Split by the item delimiter to get the total count and contact data
        parts = output.split("<<||>>", 1)
        # Strip whitespace from the count string for robustness
        total_count = int(parts[0].strip())
        
        contacts = []
        
        if len(parts) > 1 and parts[1]:
            contact_data_list = parts[1].split("<<||>>")
            
            for contact_data in contact_data_list:
                if not contact_data:
                    continue
                    
                fields = contact_data.split("<<|>>")
                
                if len(fields) < 10:
                    continue  # Not enough fields
                
                contact_id = fields[0]
                display_name = fields[1]
                first_name = fields[2]
                last_name = fields[3]
                
                # Process phone numbers
                phones = []
                phone_data = fields[4]
                if phone_data:
                    phone_parts = phone_data.split("<<+++>>")
                    for phone_part in phone_parts:
                        if not phone_part:
                            continue
                        try:
                            phone_label, phone_value = phone_part.split(":", 1)
                            phones.append({
                                "label": phone_label,
                                "value": phone_value
                            })
                        except ValueError:
                            pass  # Skip malformed entries
                
                # Process emails
                emails = []
                email_data = fields[5]
                if email_data:
                    email_parts = email_data.split("<<===>>>")
                    for email_part in email_parts:
                        if not email_part:
                            continue
                        try:
                            email_label, email_value = email_part.split(":", 1)
                            emails.append({
                                "label": email_label,
                                "value": email_value
                            })
                        except ValueError:
                            pass  # Skip malformed entries
                
                # Process addresses
                addresses = []
                address_data = fields[6]
                if address_data:
                    address_parts = address_data.split("<<***>>")
                    for address_part in address_parts:
                        if not address_part:
                            continue
                        try:
                            address_label, address_components = address_part.split(":", 1)
                            
                            # Parse address components
                            address_info = {}
                            for component in address_components.split(","):
                                if ":" in component:
                                    comp_key, comp_val = component.split(":", 1)
                                    address_info[comp_key] = comp_val
                            
                            addresses.append({
                                "label": address_label,
                                "components": address_info
                            })
                        except ValueError:
                            pass  # Skip malformed entries
                
                # Get other fields
                birthday = fields[7] if len(fields) > 7 else ""
                notes = fields[8] if len(fields) > 8 else ""
                organization = fields[9] if len(fields) > 9 else ""
                
                # Build contact object
                contact = {
                    "id": contact_id,
                    "display_name": display_name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phones": phones,
                    "emails": emails,
                    "addresses": addresses,
                }
                
                # Only add non-empty fields
                if birthday:
                    contact["birthday"] = birthday
                if notes:
                    contact["notes"] = notes
                if organization:
                    contact["organization"] = organization
                
                contacts.append(contact)
        
        # Return final result
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        if contacts:
            return {
                "success": True,
                "contacts": contacts,
                "message": f"Found {len(contacts)} contact(s)",
                "metadata": {
                    "total_matches": total_count,
                    "execution_time_ms": execution_time_ms
                }
            }
        else:
            return {
                "success": True,
                "contacts": [],
                "message": "No contacts found matching the search criteria",
                "metadata": {
                    "total_matches": 0,
                    "execution_time_ms": execution_time_ms
                }
            }
    
    except Exception as e:
        return {
            "success": False,
            "contacts": [],
            "message": "Error processing contact data",
            "error": str(e),
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }


def register_to_mcp(mcp: FastMCP) -> None:
    """Register the contacts_search_by_name tool with the MCP server."""
    @mcp.tool()
    def contacts_search_by_name(
        name: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search for contacts by name (first name, last name, or full name).
        
        This endpoint provides a way to search the macOS Contacts app for contacts
        matching a name search string. The search is performed across first name,
        last name, and full name fields.
        
        Args:
            name: The name to search for (required)
            limit: Maximum number of results to return (default: 10)
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,        # True if search was successful
                "contacts": list,       # List of matching contact objects
                "message": str,         # Context message
                "metadata": {           # Additional metadata
                    "total_matches": int,       # Total matches before limiting
                    "execution_time_ms": int,   # Execution time in milliseconds
                },
                "error": str            # Only present if success is False
            }
            
            Each contact object contains:
            {
                "id": str,              # Unique Contact ID
                "display_name": str,    # Full display name
                "first_name": str,      # First name
                "last_name": str,       # Last name
                "phones": list,         # List of phone objects
                "emails": list,         # List of email objects
                "addresses": list,      # List of address objects
                "birthday": str,        # Birthday in YYYY-MM-DD format (optional)
                "notes": str,           # Contact notes (optional)
                "organization": str     # Company/organization (optional)
            }
        
        Error Handling:
            - Invalid searches: Returns error if the search couldn't be performed
            - Permission issues: Returns error if Contacts access is restricted
            
        Performance:
            - Response time increases with the size of your contacts database
            - Using more specific search terms improves performance
            
        Examples:
            # Search for contacts with "John" in their name
            result = contacts_search_by_name("John")
            # Returns matching contacts with name containing "John"
            
            # Search with limit
            result = contacts_search_by_name("Smith", limit=5)
            # Returns up to 5 contacts with "Smith" in their name
        """
        return search_by_name_logic(name, limit)