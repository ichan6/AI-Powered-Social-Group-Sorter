import pandas as pd
from io import BytesIO

def parse_spreadsheet(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xls', '.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("Unsupported file type foo")

        return df
    except Exception as e:
        print("Error Processing File: ", e)
        return None
