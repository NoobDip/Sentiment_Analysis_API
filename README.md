# Sentiment Analysis API

FastAPI endpoint for analyzing review sentiment from uploaded CSV or Excel files.

## Upload Format

`POST /read_reviews` accepts `.csv` and `.xlsx` files. The review text column can be named `Review`, `review`, `review_text`, `tweet_text`, `full_text`, `text`, `content`, `comment`, or `message`.

Blank review rows are skipped before analysis. If no usable review text remains, the API returns a 400 response instead of sending an empty prompt.

## Configuration

Set `GROQ_API_KEY` in the environment before running the API. If the key is missing, the API returns a clear configuration error.
