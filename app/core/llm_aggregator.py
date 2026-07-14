from openai import OpenAI
#from app.config import settings
#from app.schemas import CleanSummarySchema

def aggregate_realtime(form_data: dict, excel_data: list, web_text: str) -> dict:
  """
  Combines the extracted data sources using OpenAI's Structured Outputs.
  Guarantees the result strictly fits the layout expected by PostgreSQL.
  """

  # Explicit connection initialization using injected secrets
  client = OpenAI(api_key=settings.OPENAI_API_KEY)

  # Constrain raw string inputs to prevent blowing past context bounds
  sliced_web_text = web_text[:3000]
  sliced_excel_data = excel_data[:50]

  prompt = (
      f"Cross-reference and audit these real-time data layers:\n\n"
      f"--- Hand-filled Form ---\n{form_data}\n\n"
      f"--- Ledger Sheet Sample (First 50 Rows) ---\n{sliced_excel_data}\n\n"
      f"--- Web Intelligent Data ---\n{sliced_web_text}"
  )

  # Force strict schema adherence
  completion = client.beta.chat.completions.parse(
      model="gpt-4o-mini",
      messages = [
          {
              "role": "system",
              "content": (
                  "You are an automated corporate auditing system. Cross-reference all inputs"
                  "to confirm information aligment. Identify and report any discrepancies exactly."
              )
          },
          {"role": "user", "content": prompt}
      ],
      response_format=CleanSummarySchema,
      temperature=0.0     # Eliminate create variance for highly predictable, deterministic results
  )

  # Return verified object directly matching the Pydantic template structure
  return completion.choices.message.parsed.model_dump()
