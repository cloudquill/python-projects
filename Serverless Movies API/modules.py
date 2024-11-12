import json

from config import container, co

def convertToArray(result):
    arr = []

    for item in result:
        arr.append(item)
    
    return arr

def queryDB(query):
    result = container.query_items(
        query,
        enable_cross_partition_query=True
    )

    return result

def getMovies():
    query = "SELECT c.title Title, c.year Year, c.genres Genres FROM c"
    result = queryDB(query)
    
    array_version_of_result = convertToArray(result)

    return displayResult(array_version_of_result)

def getMoviesByYear(year):
    query = (f"SELECT c.title Title, c.year Year, c.genres Genres FROM c "
             f"WHERE c.year = '{year}'")
    result = queryDB(query)
    
    array_version_of_result = convertToArray(result)

    return displayResult(array_version_of_result)

def getMovieSummary(movie_name):
    query = (f"SELECT c.title, c.year, c.genres FROM c "
             f"WHERE LOWER(c.title) = LOWER('{movie_name}')")
    result = queryDB(query)

    array_version_of_result = convertToArray(result)

    if not array_version_of_result:
        return displayResult("Movie not in database.")
    else:
        year = array_version_of_result[0]['year']
        instruction = (f"Write a plot summary for the movie {movie_name} "
                       f"released in {year}")
        
        system_message = "You respond concisely, in 2-3 sentences"

        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": instruction}
            ]
        )

        return displayResult(array_version_of_result, response)


def displayResult(result, summary=''):
    if not summary:
        return json.dumps(result, indent=4)
    else:
        details = {
            "Title": result[0]['title'],
            "Year": result[0]['year'],
            "Genres": ', '.join(result[0]['genres']),
            "Summary":summary.message.content[0].text
        }

        return json.dumps(details, indent=4)