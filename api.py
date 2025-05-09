from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from Tools.scripts.dutree import display
from gensim.models import Word2Vec
from typing import List, Dict
import fitz
import re
import os


# Initialize FastAPI
api = FastAPI(title="Resume Parser API")

# CORS configuration
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


available_tags = [
    "cert_issue_date",
    "company",
    "responsibility",
    "job_title",
    "cert_expiry_date",
    "grade",
    "job_skills",
    "grade_type",
    "activity_org",
    "objective",
    "activity_type",
    "institution",
    "languages",
    "location",
    "language_level",
    "cert_provider",
    "degree",
    "cert_skills",
    "grad_year",
    "start_date",
    "major",
    "end_date",
    "skills"
]


#Now we will load our saved model
def load_model(model_path):

    if not os.path.exists(model_path):
        st.error("Model doesn't exist")
        return None

    return Word2Vec.load(model_path)

#Call method to load our trained model
word2vec_embedding_model = load_model('word2vec.model')

#Extract the data from a pdf and return a plain string
def extract_text_from_pdf(file_bytes):
    if not file_bytes:
        raise ValueError("Uploaded PDF is empty.")
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
        return text

#Checks if a file is a pdf
def is_pdf(file):
    if file.type == "application/pdf":
        return True
    else:
        return False



#This is how we will be processing the text
def find_similar_terms(text, target_tags, t=5):
    #We will first preprocess the text We will get a list of words
    words = re.findall(r"[\w']+", text.lower())

    results = {}

    for tag in target_tags:
        try:
            #Find the similar words in the document for each tag topn is the number of similar words that we want the model to return
            #Return the 5 most similar words using the given tag
            similar = word2vec_embedding_model.wv.most_similar(positive=[tag], topn=t)

            #sim[0] extracts just the word (not the similarity score)
            matches = [word for word in words if word in [sim[0] for sim in similar]]

            context = ""

            if matches:
                index = words.index(matches[0])
                start = max(0, index - 5)
                end = min(len(words), index + 5)
                context = " ".join(words[start:end])

            similar_words = [sim[0] for sim in similar]


            results[tag] = {

                #Will return the similar words
                'similar_words': similar_words,

                #Will return the matches
                'matches': matches,

                #this will return the words surrounding the similar word
                'context': context
            }

        except KeyError as e:
            results[tag] = {"error": f"Tag '{tag}' not in vocabulary"}

    return results


@api.post("/parse-resume/")

async def parse_resume(
        tags: List[str],
        file: UploadFile = File(...)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")

    try:
        contents = await file.read()
        text = extract_text_from_pdf(contents)
        results = find_similar_terms(text, tags)
        return {
            "status": "success",
            "text": text[:500] + "..." if len(text) > 500 else text,  # Return first 500 chars
            "results": results
        }
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")

# Health check endpoint
@api.get("/")
def health_check():
    return {"status": "healthy"}

