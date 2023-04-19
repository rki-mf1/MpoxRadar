#!/bin/bash

# Set the URL to check
url="https://mpoxradar.net/"
url="localhost:8050"
# Make a request to the URL and store the response status code
response=$(curl -sL -w "%{http_code}\\n" "$url" -o /dev/null)

# Check the response status code
if [ "$response" -eq 200 ]; then
    echo "Website is accessible"
else
    echo "Website is not accessible. Response code: $response"
    # Set email parameters
    to="youremail@example.com"
    from="noreply@example.com"
    subject="Website Status Alert"
    # Send email
    body="The website $url is not accessible. Response code: $response"
    echo "$body" | mail -s "$subject" -r "$from" "$to"
fi
