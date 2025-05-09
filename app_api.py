import streamlit as st
import requests
import pandas as pd

#tags to be displayed
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

# API configuration
API_URL = "http://localhost:8000/parse-resume/"


#Now we will parse our pdf using the api
def parse_resume_via_api(file_bytes, tags):
    API_URL = "http://localhost:8000/parse-resume/"

    try:
        # Prepare the request
        files = {'file': ('resume.pdf', file_bytes)}
        data = {'tags': tags}  # Ensure tags is a list

        # Make the request
        response = requests.post(API_URL, files=files, data=data)
        response.raise_for_status()  # Raises exception for 4XX/5XX errors

        # Parse and validate response
        result = response.json()

        if not isinstance(result, dict):
            raise ValueError("API returned unexpected format")

        if 'results' not in result:
            raise ValueError("API response missing 'results' key")

        return result

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None
    except ValueError as e:
        st.error(f"API response error: {str(e)}")
        return None



def app_main():
    st.title("Resume Parser with API")
    st.write("Please upload a PDF file.")

    selected_tags = st.multiselect("Select information to extract", available_tags)

    file = st.file_uploader("Choose a PDF file to upload", type=["pdf"])



    if file is not None and selected_tags:

        try:

            with st.spinner("Analyzing resume..."):
                # Call the API
                api_response = parse_resume_via_api(file.read(), selected_tags)

                if api_response and api_response.get('status') == 'success':

                    # Get the results dictionary
                    results = api_response['results']

                    st.subheader("Extracted information")

                    output_data = []

                    for tag, data in results.items():
                        if isinstance(data, dict) and 'error' in data:
                            output_data.append({
                            'Tag':tag,
                            'Value': data["error"],
                            'Context': "",
                            "Similar words": ""
                            })
                        elif isinstance(data, dict):
                            output_data.append({
                                'Tag': tag,
                                'Value': ", ".join(data.get('matches', [])) or "No matches",
                                'Context': data.get('context', ""),
                                'Similar Words': ", ".join(data.get('similar_words', []))
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

        print("API Response:", results)

if __name__ == "__main__":
    app_main()