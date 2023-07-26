from newsapi import NewsApiClient


def get_news(category):
    # Init
    newsapi = NewsApiClient(api_key='cbaee1487c0c442c914ab115fb7aa300')

    # Initialize empty list to store all articles
    all_articles = []
    page = 1

    # Loop over each page number from start_page to end_page (inclusive)
    while page < 3:
        # Get top headlines for current page
        top_headlines_business = newsapi.get_top_headlines(
            category=category,
            language='en',
            page=page)

        # Add articles from current page to all_articles list
        all_articles.extend(top_headlines_business['articles'])
        page += 1

    # Return all articles
    return {
        "status": "ok",
        "articles": all_articles
    }
