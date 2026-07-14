import pandas as pd

def process_excel_chunks(file_path: str, chunk_size: int = 200) -> list[dict]:
  """
  Stream large Excel files in chunks to prevent server memory crashes.
  Cleans blank rows and structures everything into raw dictionaries.
  """
  structured_data = []

  # Openpyxl engine efficiently traverse records row by row
  try:
    with pd.read_excel(file_path, chunksize=chunk_size, engine="openpyxl") as reader:
      for chunk in reader:
        # Remove entirely blank entries instantly
        clean_chunk = chunk.dropna(how="all")

        # Replace remaining NaN/Null elements with empty strings for clean JSON
        clean_chunk = clean_chunk.fillna("")

        # Append records to the array matrix
        structured_data.extend(clean_chunk.to_dict(orient="records"))
  except Exception as e:
    raise ValueError(f"Excel parsing framework failure: {str(e)}")

  return structured_data
