# import os
# from google import genai
# from dotenv import load_dotenv

# load_dotenv()

# # API key from .env
# api_key = os.getenv("GEMINI_API_KEY")
# client = genai.Client(api_key=api_key)

# # Test prompt
# prompt = """
# Artificial Intelligence (AI) is transforming industries worldwide by automating processes, 
# enhancing decision-making, and enabling innovative solutions that were previously unimaginable. 
# From healthcare, where AI assists in diagnosing diseases and predicting patient outcomes, 
# to finance, where it helps in fraud detection and algorithmic trading, the applications 
# are vast and growing rapidly. Additionally, AI impacts everyday life through personal 
# assistants, recommendation systems, and smart home devices, making tasks more efficient 
# and improving user experiences. As AI technology continues to evolve, ethical considerations, 
# such as bias in algorithms, privacy concerns, and job displacement, must be carefully addressed 
# to ensure its responsible and beneficial deployment across society.
# """

# # Generate content using gemini-2.5-flash
# response = client.models.generate_content(
#     model="gemini-2.5-flash",  # from your available models
#     contents=prompt
# )
# print("Response:", response.text)

# import os
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from dotenv import load_dotenv
# from google import genai
# import fitz
# from youtube_transcript_api import YouTubeTranscriptApi

# load_dotenv()
# app = Flask(__name__)
# CORS(app,origins="http://localhost:5173")

# api_key = os.getenv("GEMINI_API_KEY")
# client = genai.Client(api_key=api_key)

# def get_summary(prompt):
#     response = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents="You are a helpful assistant that summarizes text:\n" + prompt,
        
#     )
#     return response.text


# @app.route("/summarize/text",methods=['POST'])
# def summarize_text():
#     data = request.get_json()#this will get the json data from the request body
#     text = data.get("text", "")#this will get the prompt from the json data
#     summary = get_summary(text)
#     return jsonify({"summary": summary})

# #whenever app.route anf function is written it means on that route this function will be called
# @app.route("/summarize/pdf",methods=['POST'])
# def summarize_pdf():
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part in the request"}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400

#     if file:
#         doc = fitz.open(stream=file.read(), filetype="pdf")
#         text = ""
#         for page in doc:
#             text += page.get_text()
#         prompt=f"Summarize the following text:\n{text}"    

#         summary = get_summary(prompt)
#         return jsonify({"summary": summary})

#     return jsonify({"error": "File processing failed"}), 500

# @app.route("/summarize/youtube",methods=['POST'])
# def summarize_youtube():
#     data = request.get_json()
#     url = data.get("url", "")#i am sending the url in the request body
#     #from url we need to extract the video id 
#     video_id = url.split("v=")[-1]
#     prompt = f"Summarize the content of this YouTube video: {url}"
#     #now get the transcript using youtube-transcript-api
#     transcript = YouTubeTranscriptApi.get_transcript(video_id)
#     transcript_text = " ".join([entry["text"] for entry in transcript])
#     prompt = f"Summarize the content of this YouTube video: {url}\nTranscript: {transcript_text}"
#     summary = get_summary(prompt)
#     return jsonify({"summary": summary})

# if __name__ == "__main__":
#     app.run(debug=True)
    
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq
import fitz  # PyMuPDF
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
# ------------------ Setup ------------------
load_dotenv()

app = Flask(__name__)
# CORS(app, origins="http://localhost:5173")
# CORS(app, origins=["https://aisummarizer-chi.vercel.app"])
CORS(app, 
     origins=["https://aisummarizer-chi.vercel.app", "http://localhost:5173"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type"],
     supports_credentials=True)


client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ------------------ Helper Function ------------------
def get_summary(prompt):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # fast & free-tier friendly
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes content clearly and concisely."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()

# ------------------ Routes ------------------

@app.route("/summarize/text", methods=["POST"])
def summarize_text():
    data = request.get_json()
    text = data.get("text", "")

    if not text.strip():
        return jsonify({"error": "Text is empty"}), 400

    summary = get_summary(f"Summarize the following text:\n{text}")
    return jsonify({"summary": summary})


@app.route("/summarize/pdf", methods=["POST"])
def summarize_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""

    for page in doc:
        text += page.get_text()

    if not text.strip():
        return jsonify({"error": "No text found in PDF"}), 400

    summary = get_summary(f"Summarize the following document:\n{text}")
    return jsonify({"summary": summary})



@app.route("/summarize/youtube", methods=["POST"])
def summarize_youtube():
    print("➡️ YouTube summarize API hit")

    try:
        data = request.get_json()
        print(" Request data:", data)

        url = data.get("url", "")
        print(" URL:", url)

        # Extract video ID
        if "v=" in url:
            video_id = url.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[-1].split("?")[0]
        else:
            raise ValueError("Invalid YouTube URL")

        print("🎥 Video ID:", video_id)

        # Create instance of YouTubeTranscriptApi
        ytt_api = YouTubeTranscriptApi()
        
        # Try to get transcript with multiple language codes
        fetched_transcript = None
        languages_to_try = [
            ['en'],  # English
            ['hi'],  # Hindi
            ['es'],  # Spanish
            ['fr'],  # French
            ['de'],  # German
            ['it'],  # Italian
            ['pt'],  # Portuguese
            ['ja'],  # Japanese
            ['ko'],  # Korean
            ['zh-CN'],  # Chinese (Simplified)
            ['zh-TW'],  # Chinese (Traditional)
            ['ar'],  # Arabic
            ['ru'],  # Russian
            ['nl'],  # Dutch
            ['pl'],  # Polish
            ['tr'],  # Turkish
        ]
        
        # Try each language
        for lang_list in languages_to_try:
            try:
                fetched_transcript = ytt_api.fetch(video_id, languages=lang_list)
                print(f" Transcript fetched in language: {lang_list[0]}")
                break
            except:
                continue
        
        # If no specific language worked, try without language specification (gets default)
        if not fetched_transcript:
            try:
                fetched_transcript = ytt_api.fetch(video_id)
                print("📝 Transcript fetched (default language)")
            except Exception as e:
                raise Exception(f"Could not fetch transcript. The video might not have captions available. Error: {str(e)}")

        if not fetched_transcript:
            raise Exception("No transcript available for this video")

        # Access the snippets attribute and get text from each snippet
        transcript_text = " ".join(snippet.text for snippet in fetched_transcript.snippets)
        print(f"📄 Transcript length: {len(transcript_text)} characters")

        # Generate summary
        summary = get_summary(transcript_text)
        print("Summary generated")

        return jsonify({
            "summary": summary,
            "language": fetched_transcript.language_code,
            "is_generated": fetched_transcript.is_generated
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    
# ------------------ Run Server ------------------
if __name__ == "__main__":
    app.run(debug=True)
