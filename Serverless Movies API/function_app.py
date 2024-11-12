import azure.functions as func

from modules import getMovies, getMoviesByYear, getMovieSummary


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="getMovies")
@app.route(route= "getmovies", methods=["GET"])
def test(req: func.HttpRequest) -> func.HttpResponse:
    response = getMovies()

    return func.HttpResponse(
        response, 
        status_code=200
    )

@app.function_name('getMoviesByYear')
@app.route(route='getmoviesbyyear/{year}', methods=["GET"])
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    url = req.url
    url_parts = url.split("/")
    year = url_parts[-1]

    try:
        if year and isinstance(int(year), int):
            response = getMoviesByYear(year)
    except:
            response = "Please provide a year as part of the url in this format: http://localhost:7071/api/getmoviesbyyear/year"

    return func.HttpResponse(
            response,
            status_code=200
    )

@app.function_name('getMovieSummary')
@app.route(route='getmoviesummary/{movie_name}', methods=["GET"])
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    url = req.url
    url_parts = url.split("/")
    movie_name = url_parts[-1]

    try:
        if isinstance(movie_name, str) and movie_name.strip():
            response = getMovieSummary(movie_name)
    except:
        response = "Please provide a movie name as part of the url in this format: http://localhost:7071/api/getmoviesbyyear/movie-name"
    
    return func.HttpResponse(
        response,
        status_code=200
    )