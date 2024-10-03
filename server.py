import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from urllib.parse import parse_qs, urlparse
import json
import pandas as pd
from datetime import datetime
import uuid
import os
from typing import Callable, Any
from wsgiref.simple_server import make_server

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('stopwords', quiet=True)

adj_noun_pairs_count = {}
sia = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words('english'))

reviews = pd.read_csv('data/reviews.csv').to_dict('records')

class ReviewAnalyzerServer:
    def __init__(self) -> None:
        # This method is a placeholder for future initialization logic
        pass

    def analyze_sentiment(self, review_body):
        sentiment_scores = sia.polarity_scores(review_body)
        return sentiment_scores

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> bytes:
        """
        The environ parameter is a dictionary containing some useful
        HTTP request information such as: REQUEST_METHOD, CONTENT_LENGTH, QUERY_STRING,
        PATH_INFO, CONTENT_TYPE, etc.
        """

        # Handle GET requests
        if environ["REQUEST_METHOD"] == "GET":
            # Create the response body from the reviews and convert to a JSON byte string
            # response_body = json.dumps(reviews, indent=2).encode("utf-8")
            
            # Write your code here
            valid_locations = ['Albuquerque, New Mexico','Carlsbad, California', 'Chula Vista, California', 'Colorado Springs, Colorado', 'Denver, Colorado', 'El Cajon, California', 'El Paso, Texas', 'Escondido, California', 'Fresno, California', 'La Mesa, California', 'Las Vegas, Nevada', 'Los Angeles, California', 'Oceanside, California', 'Phoenix, Arizona', 'Sacramento, California', 'Salt Lake City, Utah', 'San Diego, California', 'Tucson, Arizona']
           
            response_list = []
            # confirm that the query string is not empty
            if environ['QUERY_STRING']:
                parsed = parse_qs(environ['QUERY_STRING'])
                try:
                    # check if location, start_date, end_date is in the query string
                    location = parsed['location'][0]
                    start_date = datetime.strptime(parsed["start_date"][0], "%Y-%m-%d")
                    end_date = datetime.strptime(parsed["end_date"][0], "%Y-%m-%d")
                    # if all are present, filter the reviews based on the location, start_date and end_date
                    if location in valid_locations:
                        for item in reviews:
                            time_stamp = datetime.strptime(item["Timestamp"].split()[0], "%Y-%m-%d")
                            if item["Location"] == location and start_date <= time_stamp <= end_date:
                                item['sentiment'] = sia.polarity_scores(item["ReviewBody"])
                                response_list.append(item)
                except KeyError:
                    try:
                        # check if start_date and end_date is in the query string now that location is not present
                        start_date = datetime.strptime(parsed["start_date"][0], "%Y-%m-%d")
                        end_date = datetime.strptime(parsed["end_date"][0], "%Y-%m-%d")
                        for item in reviews:
                            time_stamp = datetime.strptime(item["Timestamp"].split()[0], "%Y-%m-%d")
                            if start_date <= time_stamp <= end_date:
                                item['sentiment'] = sia.polarity_scores(item["ReviewBody"])
                                response_list.append(item)
                    except KeyError:
                        try:
                            # check if start_date is in the query string now that location and end_date is not present
                            start_date = datetime.strptime(parsed["start_date"][0], "%Y-%m-%d")
                            for item in reviews:
                                time_stamp = datetime.strptime(item["Timestamp"].split()[0], "%Y-%m-%d")
                                if start_date <= time_stamp:
                                    item['sentiment'] = sia.polarity_scores(item["ReviewBody"])
                                    response_list.append(item)
                        except KeyError:
                            # check if end_date is in the query string now that location, start_date is not present
                            try:
                                end_date = datetime.strptime(parsed["end_date"][0], "%Y-%m-%d")
                                for item in reviews:
                                    time_stamp = datetime.strptime(item["Timestamp"].split()[0], "%Y-%m-%d")
                                    if time_stamp <= end_date:
                                        item['sentiment'] = sia.polarity_scores(item["ReviewBody"])
                                        response_list.append(item)
                            except KeyError:
                                # check if location is in the query string now that start_date, end_date is not present 
                                try:
                                    location = parsed['location'][0]
                                    if location in valid_locations:
                                        for item in reviews:
                                            if item["Location"] == location:
                                                item['sentiment'] = sia.polarity_scores(item["ReviewBody"])
                                                response_list.append(item)

                                except KeyError:
                                    # Set the appropriate response headers
                                    start_response("504 Bad Request", [
                                    ("Content-Type", "504 Error"),
                                    ])
                                    return ["Bad Request".encode('utf-8')]

            else:
                for item in reviews:
                    item["sentiment"] = sia.polarity_scores(item["ReviewBody"])
                    response_list.append(item)
                    
            # Sort the response list based on sentiment scores in descending order   
            sorted_response_list = sorted(response_list, key=lambda x: x["sentiment"]["compound"], reverse=True)

            # Convert the sorted response list to JSON and encode it
            response_body = json.dumps(sorted_response_list, indent=2).encode("utf-8")

            # Set the appropriate response headers
            start_response("200 OK", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body)))
             ])
            
            # Return the response body
            return [response_body]

        # Handle POST request
        if environ["REQUEST_METHOD"] == "POST":
            # Write your code here

            # List of valid locations
            valid_locations = ['Albuquerque, New Mexico','Carlsbad, California', 'Chula Vista, California', 'Colorado Springs, Colorado', 'Denver, Colorado', 'El Cajon, California', 'El Paso, Texas', 'Escondido, California', 'Fresno, California', 'La Mesa, California', 'Las Vegas, Nevada', 'Los Angeles, California', 'Oceanside, California', 'Phoenix, Arizona', 'Sacramento, California', 'Salt Lake City, Utah', 'San Diego, California', 'Tucson, Arizona']
            
            # Get the size of the request body
            try:
                request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0

            # fetch POST payload
            request_body = environ['wsgi.input'].read(request_body_size)

            #parse request body
            parsed = parse_qs(request_body.decode("utf-8"))
            try:
                new_location = parsed["Location"][0]

                # Check if location is valid
                if new_location not in valid_locations:
                    start_response(
                        '400 Invalid location',
                        [("Content-Type", "Error String")]
                    )
                    return ["400 Invalid location".encode('utf-8')]
                
            except KeyError:
                start_response(
                    '400 Missing location',
                    [("Content-Type", "Error String")]
                )
                return ["400 Missing location".encode('utf-8')]
            try:
                new_review_body = parsed["ReviewBody"][0]
            except KeyError:
                start_response(
                    '400 Missing review body',
                    [("Content-Type", "Error String")]
                )
                return ["400 Missing review body".encode('utf-8')]

            # Set the appropriate response headers
            start_response("201 OK", [
            ("Content-Type", "application/json"),
             ])
            # Create a new review object
            new_review = {
                "ReviewId": str(uuid.uuid4()),
                "ReviewBody": new_review_body,
                "Location": new_location,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            # Add the new review to the list of reviews
            reviews.append(new_review)
            new_response_body = json.dumps(new_review, indent=2).encode("utf-8")

            return [new_response_body]


if __name__ == "__main__":
    app = ReviewAnalyzerServer()
    port = os.environ.get('PORT', 8000)
    with make_server("", port, app) as httpd:
        print(f"Listening on port {port}...")
        httpd.serve_forever()