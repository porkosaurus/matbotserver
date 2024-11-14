import requests
from icalendar import Calendar

def get_usu_information(ics_url):
    # Custom headers with a common User-Agent and Referer
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://news.csun.edu/events/category/usu/'
    }

    # Download the .ics file content with custom headers
    response = requests.get(ics_url, headers=headers)

    # Check if the response is successful
    if response.status_code == 200:
        # Check if the content is not HTML
        if response.headers.get('Content-Type', '').startswith('text/calendar'):
            ics_content = response.content

            try:
                # Parse the .ics file content
                calendar = Calendar.from_ical(ics_content)

                # Extract event details
                events = []
                for component in calendar.walk():
                    if component.name == "VEVENT":
                        # Convert Categories to a readable format
                        categories = component.get('categories')
                        if categories:
                            if isinstance(categories, list):
                                # Handle each category item based on its type
                                categories = [
                                    cat.to_ical().decode('utf-8') if hasattr(cat, 'to_ical') else str(cat)
                                    for cat in categories
                                ]
                            else:
                                categories = [str(categories)]

                        event = {
                            "Summary": component.get('summary'),
                            "Start": component.get('dtstart').dt,
                            "End": component.get('dtend').dt,
                            "Location": component.get('location'),
                            "Description": component.get('description'),
                            "URL": component.get('url'),
                            "Organizer": component.get('organizer'),
                            "Categories": categories,
                        }
                        events.append(event)

                # Format the extracted event information as a string
                formatted_events = []
                for event in events:
                    event_text = (
                        f"Summary: {event['Summary']}\n"
                        f"Start: {event['Start']}\n"
                        f"End: {event['End']}\n"
                        f"Location: {event['Location']}\n"
                        f"Description: {event['Description']}\n"
                        f"URL: {event['URL']}\n"
                        f"Organizer: {event['Organizer']}\n"
                        f"Categories: {event['Categories']}\n"
                        f"{'-' * 40}\n"
                    )
                    formatted_events.append(event_text)
                
                # Join all formatted events into a single string
                return "\n".join(formatted_events)
            
            except ValueError as e:
                return f"Failed to parse the .ics content: {e}"
        
        else:
            return "The URL returned content that is not a valid .ics file. It might be an HTML page."
    else:
        return f"Failed to retrieve the .ics file. HTTP Status Code: {response.status_code}"

# Example usage:
ics_url = "https://news.csun.edu/events/category/usu/list/?ical=1"
event_info = get_usu_information(ics_url)
print(event_info)