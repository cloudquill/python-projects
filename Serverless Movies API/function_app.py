import urllib.parse

import azure.functions as func

from modules import fetch_movies, fetch_movies_by_year, fetch_movie_summary


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name='getMovies')
@app.route(route= 'getmovies', methods=['GET'])
def getMovies(req: func.HttpRequest) -> func.HttpResponse:
    response = fetch_movies()

    return func.HttpResponse(
        response, 
        status_code=200,
        mimetype='application/json'
    )

@app.function_name('getMoviesByYear')
@app.route(route='getmoviesbyyear/{year}', methods=['GET'])
def getMoviesByYear(req: func.HttpRequest) -> func.HttpResponse:
    url = req.url
    url_parts = url.split('/')
    year = url_parts[-1]

    try:
        if year and isinstance(int(year), int):
            response = fetch_movies_by_year(year)
    except ValueError:
            error_message = ("Please provide a valid year as part of the url: " 
                             "http://localhost:7071/api/getmoviesbyyear/year")
            return func.HttpResponse(error_message, status_code=400)

    return func.HttpResponse(
            response,
            status_code=200,
            mimetype='application/json'
    )

@app.function_name('getMovieSummary')
@app.route(route='getmoviesummary/{movie_name}', methods=['GET'])
def getMovieSummary(req: func.HttpRequest) -> func.HttpResponse:
    url = req.url
    url_parts = url.split('/')
    movie_name = urllib.parse.unquote(url_parts[-1].strip())

    if not movie_name:
        error_message = ("Please provide a movie name as part of the url: "
                         "http://localhost:7071/api/getmoviesbyyear/movie-name")
        return func.HttpResponse(error_message, status_code=400)

    response = fetch_movie_summary(movie_name)
   
    return func.HttpResponse(
        response,
        status_code=200,
        mimetype='application/json'
    )