import requests
import pandas as pd
import streamlit as st
from openai import OpenAI

# Constants
URL = "https://efts.sec.gov/LATEST/search-index"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Origin': 'https://www.sec.gov',
    'Referer': 'https://www.sec.gov/'
}

# Sidebar for the chatbot interface
with st.sidebar:
    with st.popover("OpenAI API Key", help = "Please insert you API Key to use the chatbot"):
        st.header("💬 ChatGPT")
        openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

    # Use a separate session state key for chatbot messages
    if "chatbot_messages" not in st.session_state:
        st.session_state["chatbot_messages"] = [{"role": "assistant", "content": "Ask me anything about the Form D filings"}]

    for msg in st.session_state["chatbot_messages"]:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()

        client = OpenAI(api_key=openai_api_key)
        st.session_state["chatbot_messages"].append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        response = client.chat.completions.create(model="gpt-4o", messages=st.session_state["chatbot_messages"])
        msg = response.choices[0].message.content
        st.session_state["chatbot_messages"].append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)

def fetch_sec_filings(start_date, end_date):
    """Fetch SEC filings between two dates."""
    params = {'dateRange': 'custom', 'startdt': start_date, 'enddt': end_date, 'forms': 'D'}
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()  # Raises a HTTPError for bad responses
        return clean_up(response.json())  # Assuming the response is JSON
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
        return None

def clean_up(response):
    """Extract and format data from SEC response."""
    results = []
    for item in response["hits"]["hits"]:
        source = item["_source"]
        edgar_links = ', '.join([f'<a href="https://www.sec.gov/edgar/browse/?CIK={cik}" target="_blank">Link</a>' for cik in source["ciks"]])
        result = {
            "Company Name": ', '.join(source["display_names"]),
            "File Date": source["file_date"],
            "Business Location(s)": ', '.join(source["biz_locations"]),
            "Edgar": edgar_links
        }
        results.append(result)
    return results

def main():
    """Main function to run the Streamlit app."""
    st.title('Daily Form D Filings')

    # Custom CSS to center text in the table
    center_css = """
    <style>
    th, td {
        text-align: center;
    }
    </style>
    """
    st.markdown(center_css, unsafe_allow_html=True)

    # Use a separate session state key for form submissions
    if "filing_results" not in st.session_state:
        st.session_state["filing_results"] = None

    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    if st.button("Check for Filings"):
        filings = fetch_sec_filings(start_date, end_date)
        if filings:
            df = pd.DataFrame(filings)
            st.session_state["filing_results"] = df
            # Render the dataframe as HTML to allow styling and make links clickable
            st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.write("No filings found or an error occurred.")
    elif st.session_state["filing_results"] is not None:
        # Display existing results if the form was already run
        st.write(st.session_state["filing_results"].to_html(escape=False, index=False), unsafe_allow_html=True)

if __name__ == "__main__":
    main()