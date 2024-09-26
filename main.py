from fastapi import FastAPI, UploadFile, HTTPException
import pandas as pd
import os
import json
from groq import Groq

app = FastAPI()


@app.get("/")
def read_root():
    return {"How to use": "API takes in a CSV or EXCEL file containing reviews with a column named 'Review' and returns the average POSITIVE, NEGATIVE and NEUTRAL sentiment score of the reviews."}

@app.post("/read_reviews")
def read_reviews(file: UploadFile):

    if file.filename.endswith(".xlsx"):
        df = pd.read_excel(file.file)
    elif file.filename.endswith(".csv"):
        df = pd.read_csv(file.file)
    else:
        raise HTTPException(status_code=400, detail="Incorrect format of input file")
    
    try:
        reviews = list(df["Review"])
        formatted_reviews = ', '.join(f"{index}: '{item}'" for index, item in enumerate(reviews))
    except Exception as e:
        raise HTTPException(status_code=400, detail="No column 'Review' found")
    client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
    )

    chat_completion = client.chat.completions.create(
            messages=[
            {
                "role": "system",
                "content": "You are a DATA ANALYST capable of sentiment analysis from a  list of reviews that responds in only JSON format. Make sure to stick to JSON and output a valid JSON  and provide response for all the reviews in the list. The JSON schema is as follows:{\"<list_index>(in double quotes)\": {\"POSITIVE\": numeric(0-1), \"NEGATIVE\": numeric(0-1), \"NEUTRAL\": numeric(0-1)}}",
            },
            {
                "role": "user",
                "content": f"{formatted_reviews}",
            },
        ],
        model="mixtral-8x7b-32768",max_tokens=32768,
    )
    try:
        str = chat_completion.choices[0].message.content
        review  = json.loads(str)
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
        analysis = {
            "positive": average_positive,
            "negative": average_negative,
            "neutral": average_neutral
        }
        return {"data": analysis}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Reupload file")
    
