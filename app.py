# app.py
from flask import Flask, request, jsonify
from utils import search_articles, fetch_article_content, concatenate_content, generate_answer
import logging
from dotenv import load_dotenv
import os
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

app = Flask(__name__)

# @app.route('/query', methods=['POST'])
# def query():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "No data provided"}), 400

#         query_text = data.get('query')
#         if not query_text:
#             return jsonify({"error": "No query provided"}), 400

#         # Use the API key directly
#         api_key = '47ad0aa53435efa7034d65e734a487ed640fe40f'

#         # Search for articles
#         article_urls = search_articles(query_text, api_key)
#         if not article_urls:
#             return jsonify({"error": "No articles found"}), 404

#         # Process articles and fetch content
#         article_content = []
#         for url in article_urls:
#             try:
#                 content = fetch_article_content(url)
#                 if content:
#                     article_content.append({"url": url, "content": content})
#             except Exception as e:
#                 logger.error(f"Error fetching content from {url}: {str(e)}")

#         if not article_content:
#             return jsonify({"error": "Could not fetch any article content"}), 404

#         # Concatenate content and generate answer
#         combined_content = concatenate_content(article_content)
#         answer = generate_answer(combined_content, query_text)

#         return jsonify({
#             "answer": answer,
#             "sources": [article["url"] for article in article_content]
#         })

#     except Exception as e:
#         logger.error(f"Error processing request: {str(e)}")
#         return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# if __name__ == '__main__':
#     app.run(host='localhost', port=5001, debug=True)

app = Flask(__name__)

# Load API key from environment variable
API_KEY = os.getenv('SERPER_API_KEY')  # Replace 'default_api_key' with a placeholder or secure logic.

@app.route('/query', methods=['POST'])
def query():
    try:
        # Parse JSON data
        data = request.get_json()
        if not data or 'query' not in data:
            logger.warning("No query provided in the request.")
            return jsonify({"error": "No query provided"}), 400

        query_text = data['query']
        logger.info(f"Received query: {query_text}")

        # Search for articles
        article_urls = search_articles(query_text, API_KEY)
        if not article_urls:
            logger.info(f"No articles found for query: {query_text}")
            return jsonify({"error": "No articles found"}), 404

        # Fetch content from articles
        article_content = []
        for url in article_urls:
            try:
                content = fetch_article_content(url)
                if content:
                    article_content.append({"url": url, "content": content})
            except Exception as e:
                logger.error(f"Error fetching content from {url}: {str(e)}")

        if not article_content:
            logger.warning("Could not fetch any content from the articles.")
            return jsonify({"error": "Could not fetch any article content"}), 404

        # Concatenate content and generate answer
        combined_content = concatenate_content(article_content)
        answer = generate_answer(combined_content, query_text)

        logger.info("Successfully generated an answer.")
        return jsonify({
            "answer": answer,
            "sources": [article["url"] for article in article_content]
        })

    except Exception as e:
        logger.exception(f"Error processing request: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)