import boto3
from app.config import settings

def extract_form_fieldd(document_path: str) -> dict:
  """
  Extract key-value pairs from neatly filled forms using AWS Textract.
  Reads file binaries locally and submits them directly to the API.
  """
  # Initialize connection using settings parameters
  textract = boto3.client(
      "textract",
      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
      region_name=settings.AWS_REGION
  )

  with open(document_path, "rb") as document_file:
    file_bytes = document_file.read()

  response = textract.analyze_document(
      Document={"Bytes": file_bytes},
      FeatureTypes=["FORMS"]
  )

  blocks = {block["id"]: block for block in response["Blocks"]}
  form_data = {}

  for block in blocks.values():
    if block["BlockType"] == "KEY_VALUE_SET" and "KEY" in block["EntityTypes"]:
      # Reconstruct the Key string
      key_text = "".join([
          blocks[t]["Text"] + " "
          for rel in block.get("Relationships", []) if rel["Type"] == "CHILD"
          for t in rel["Ids"] if blocks[t]["BlockType"] == "WORD"
      ])

      # Locate the associated Value block and reconstruct the text
      value_text = ""
      for rel in block.get("Relationships", []):
        if rel["Type"] == "VALUE":
          for val_id in rel["Ids"]:
            val_block = blocks[val_id]
            if "Relationships" in val_block:
              for val_rel in val_block["Relationships"]:
                if val_rel["Type"] == "CHILD":
                  value_text += "".join([
                      blocks[t]["Text"] + " "
                      for t in val_rel["Ids"] if blocks[t]["BlockType"] == "WORD"
                  ])
      clean_key = key_text.strip().rstrip(":")
      if clean_key:
        form_data[clean_key] = value_text.strip()

  return form_data

