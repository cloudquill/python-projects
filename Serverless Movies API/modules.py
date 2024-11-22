import json

from config import container, co

def convert_to_list(query_result):
    """Converts query result to a list

    Args:
        query_result (itemPaged): Query result from DB

    Returns:
        list: List of items from the query result
    """
    return [item for item in query_result]

def query_db(query, parameters=[]):
    """Queries the database for items

    Args:
        query (str): The query string
        parameters (list, optional): A list of parameters for the query
    
    Returns:
        list: a list of items returned by the query
    """
    try:
        query_result = container.query_items(
            query,
            parameters,
            enable_cross_partition_query=True
        )
    
        return convert_to_list(query_result)
    except Exception:
        return display_result("An error occurred while querying the database."
                              " Please try again later.")

def fetch_movies():
    """Retrieves all movie information from the DB

    Returns:
        str: A JSON-formatted string of all movies
    """
    query = 'SELECT c.title Title, c.year Year, c.genres Genres FROM c'
    query_result = query_db(query)

    return display_result(query_result)

def fetch_movies_by_year(year):
    """Retrieves movies released in a given year
    
    Args:
        year (int): Year movie was released
    
    Returns:
        str: A JSON-formatted string of movies released a specific year
    """
    query = ('SELECT c.title Title, c.year Year, c.genres Genres FROM c'
             ' WHERE c.year = @year')
    parameters = [{'name': '@year', 'value': year}]
    query_result = query_db(query, parameters)

    return display_result(query_result)

def fetch_movie_summary(movie_name):
    """Retrieves a specific movie's information along with a summary.
    
    Args:
        movie_name (str): Name of the movie

    Returns:
        str: A JSON-formatted string of a specific movie with its summary
    """
    query = ('SELECT c.title, c.year, c.genres FROM c'
             ' WHERE LOWER(c.title) = LOWER(@movie_name)')
    parameters = [{'name': '@movie_name', 'value': movie_name}]
    query_result = query_db(query, parameters)

    ai_summary = ''

    if not query_result:
        return display_result("Movie not in database.")
    
    year = query_result[0]['year']
    instruction = (f'Write a plot summary for the movie {movie_name}'
                   f' released in {year}')

    try:
        # Instructs Cohere AI on how to respond
        system_message = 'You respond concisely, in 2-3 sentences'

        ai_summary = co.chat(
            model='command-r-plus-08-2024',
            messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': instruction}
            ]
        )
    except:
        return display_result("An error occurred while generating a summary for"
                             f" {movie_name}. Please try again later.")
    
    return display_result(query_result, ai_summary)


def display_result(result, ai_summary=''):
    """Formats results in JSON
    
    Args:
        result (list): Data returned from DB or error message
        ai_summary (str, optional): Movie summary

    Returns:
        str: A JSON-formatted string of results
    """
    if ai_summary:
        content_to_display = {
            "Title": result[0]['title'],
            "Year": result[0]['year'],
            "Genres": ", ".join(result[0]['genres']),
            "Summary": ai_summary.message.content[0].text
        }
    else:
        content_to_display = result

    return json.dumps(content_to_display, indent=4)