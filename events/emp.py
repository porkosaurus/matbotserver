import requests
from icalendar import Calendar

def get_emp_information(ics_url):
    # Download the .ics file content
    response = requests.get(ics_url)

    # Check if the response is successful
    if response.status_code == 200:
        ics_content = response.content
        
        try:
            # Parse the .ics file content
            calendar = Calendar.from_ical(ics_content)

            # Extract event details
            events = []
            for component in calendar.walk():
                if component.name == "VEVENT":
                    event = {
                        "Summary": component.get('summary'),
                        "Start": component.get('dtstart').dt,
                        "End": component.get('dtend').dt,
                        "Description": component.get('description'),
                        "Location": component.get('location'),
                        "URL": component.get('url'),
                    }
                    events.append(event)

            # Format the extracted event information as a string
            formatted_events = []
            for event in events:
                event_text = (
                    f"Summary: {event['Summary']}\n"
                    f"Start: {event['Start']}\n"
                    f"End: {event['End']}\n"
                    f"Description: {event['Description']}\n"
                    f"Location: {event['Location']}\n"
                    f"URL: {event['URL']}\n"
                    f"{'-' * 40}\n"
                )
                formatted_events.append(event_text)
            
            # Join all formatted events into a single string
            return "\n".join(formatted_events)
        
        except ValueError as e:
            return f"Failed to parse the .ics content: {e}"
    else:
        return f"Failed to retrieve the .ics file. HTTP Status Code: {response.status_code}"

# Example usage:
ics_url = "https://www.csun.edu/feeds/ics/events/76181/export.ics"
event_info = get_emp_information(ics_url)
