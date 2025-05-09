import streamlit as st
import pandas as pd
import numpy as np
from Tools.scripts.dutree import display
from gensim.models import Word2Vec
import fitz

import re
import os




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
@st.cache_resource
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




def app_main():
    st.title("Resume Parser")
    st.write("Please upload a PDF file.")

    selected_tags = st.multiselect("Select information to extract", available_tags)

    file = st.file_uploader("Choose a PDF file to upload", type=["pdf"])

    if file is not None and selected_tags:

        try:

            #Extract the text from the pdfs
            text = extract_text_from_pdf(file)
            st.text_area("Extracted Text", text)

            #Now we will find dimlar terms
            results = find_similar_terms(text, selected_tags)

            st.subheader("Extracted information")

            output_data = []

            for tag, data in results.items():
                if "error" in data:
                    output_data.append({
                        'Tag':tag,
                        'Value': data["error"],
                        'Context': "",
                        "Similar words": ""
                    })
                else:
                    output_data.append({
                        "Tag": tag,
                        "Value": ", ".join(data["matches"]) if data["matches"] else "No matches",
                        "Context": data["context"],
                        "Similar words": ", ".join(data["similar_words"])
                    })

            df = pd.DataFrame(output_data)
            st.dataframe(df)

            #Now we will create a download button
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download as csv", csv,
                "extracted_data.csv",
                "text/csv",
                key="downloaded-csv"
            )

        except Exception as e:
            st.error("An error occurred: We could not process your PDF :("+str(e))




if __name__ == "__main__":
   app_main()


