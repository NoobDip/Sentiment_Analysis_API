from fastapi import FastAPI, UploadFile, HTTPException
import pandas as pd
import os
import json
from groq import Groq

app = FastAPI()
REVIEW_COLUMN_ALIASES = (
    "Review",
    "review",
    "review_text",
    "tweet_text",
    "full_text",
    "text",
    "content",
    "comment",
    "message",
)


def find_review_column(columns):
    lookup = {str(column).strip().lower(): column for column in columns}
    for alias in REVIEW_COLUMN_ALIASES:
        column = lookup.get(alias.lower())
        if column is not None:
            return column
    return None

@app.get("/")
def read_root():
    return {"How to use": "Upload a CSV or Excel file containing reviews. Supported text columns include Review, review_text, tweet_text, full_text, text, content, comment, and message."}

@app.post("/read_reviews")
def read_reviews(file: UploadFile):
    """
    This endpoint takes in a CSV or EXCEL file containing reviews with a column named 'Review' and returns the average POSITIVE, NEGATIVE and NEUTRAL sentiment score of the reviews.
    
    Args:
        file (UploadFile): The uploaded file containing the reviews.
        
    Returns:
        dict: A dictionary containing the average POSITIVE, NEGATIVE and NEUTRAL sentiment scores.
        
    Raises:
        HTTPException: If the file format is incorrect or if the column 'Review' is not found in the file.
    """
    # Check if the file is in the correct format
    filename = file.filename or ""
    if filename.endswith(".xlsx"):
        df = pd.read_excel(file.file)
    elif filename.endswith(".csv"):
        df = pd.read_csv(file.file)
    else:
        raise HTTPException(status_code=400, detail="Incorrect format of input file")
    
    try:
        # Extract the reviews from the file
        review_column = find_review_column(df.columns)
        if review_column is None:
            supported = ", ".join(REVIEW_COLUMN_ALIASES)
            raise HTTPException(status_code=400, detail=f"No supported review column found. Use one of: {supported}")
        reviews = [
            str(item).strip()
            for item in df[review_column].dropna().tolist()
            if str(item).strip()
        ]
        if not reviews:
            raise HTTPException(status_code=400, detail="No non-empty reviews found")
        # Format the reviews in a JSON compatible format
        formatted_reviews = ', '.join(f"{index}: '{item}'" for index, item in enumerate(reviews))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Review column could not be read")
    
    # Create a Groq client with the API key
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured")

    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY")
    )
    # Send the reviews to the Groq API for sentiment analysis
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a DATA ANALYST capable of sentiment analysis from a  list of reviews that responds in only JSON format. Make sure to stick to JSON and output a valid JSON and provide response for all the reviews in the list. The JSON schema is as follows:{\"<list_index>(in double quotes)\": {\"POSITIVE\": numeric(0-1), \"NEGATIVE\": numeric(0-1), \"NEUTRAL\": numeric(0-1)}}",
            },
            {
                "role": "user",
                "content": f"{formatted_reviews}",
            },
        ],
        model="mixtral-8x7b-32768",
        max_tokens=32768,
    )
    
    try:
        # Parse the sentiment analysis response from JSON
        response_text = chat_completion.choices[0].message.content
        review  = json.loads(response_text)
        
        # Compute the average sentiment scores for each review
        total = len(review)
        positive_sum = 0
        negative_sum = 0
        neutral_sum = 0
        for _, value in review.items():
            positive_sum += value["POSITIVE"]
            negative_sum += value["NEGATIVE"]
            neutral_sum += value["NEUTRAL"]
        average_positive = positive_sum / total
        average_negative = negative_sum / total
        average_neutral = neutral_sum / total
        
        # Create a dictionary with the average sentiment scores
        analysis = {
            "positive": average_positive,
            "negative": average_negative,
            "neutral": average_neutral
        }
        
        return {"data": analysis}
    except Exception:
        raise HTTPException(status_code=400, detail="Reupload file")
    
