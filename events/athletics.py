import feedparser

def get_athletics_information(rss_url):
    # Parse the RSS feed
    feed = feedparser.parse(rss_url)

    # Initialize a list to hold the formatted entries
    formatted_entries = []

    # Add the feed title and number of entries
    formatted_entries.append(f"Feed Title: {feed.feed.title}")
    formatted_entries.append(f"Number of Entries: {len(feed.entries)}\n")

    # Extract and format information from each entry
    for entry in feed.entries:
        entry_text = (
            f"Title: {entry.title}\n"
            f"Description: {entry.description}\n"
            f"Link: {entry.link}\n"
            f"Start Date: {entry.get('ev_startdate', 'N/A')}\n"
            f"End Date: {entry.get('ev_enddate', 'N/A')}\n"
            f"Local Start Date: {entry.get('s_localstartdate', 'N/A')}\n"
            f"Local End Date: {entry.get('s_localenddate', 'N/A')}\n"
            f"Team Logo: {entry.get('s_teamlogo', 'N/A')}\n"
            f"Opponent Logo: {entry.get('s_opponentlogo', 'N/A')}\n"
            f"Opponent: {entry.get('s_opponent', 'N/A')}\n"
            f"Game ID: {entry.get('s_gameid', 'N/A')}\n"
            f"{'-'*40}\n"
        )
        formatted_entries.append(entry_text)

    # Join all formatted entries into a single string
    return "\n".join(formatted_entries)

# Example usage:
rss_url = "https://gomatadors.com/calendar.ashx/calendar.rss?sport_id=0&_=clyq7bqqp0001359tdrrnto8f"
rss_info = get_athletics_information(rss_url)
