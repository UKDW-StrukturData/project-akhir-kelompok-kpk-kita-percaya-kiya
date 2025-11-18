from google import genai
def geminiSearch():
    api_key =  "AIzaSyC-IQvTBHUA3Y2A5IlQTmsHw-zQ3o_XZvc"
    client = genai.Client(api_key= api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Explain how AI works in a few words",
    )

    print(response.text)