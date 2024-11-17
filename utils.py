# utils.py
import os
import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

class LLMManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            if not GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            cls._instance = ChatGroq(
                api_key=GROQ_API_KEY,  # Changed from groq_api_key to api_key
                model_name="mixtral-8x7b-32768"
            )
        return cls._instance

def search_articles(query: str, api_key: str) -> List[str]:
    """Search for articles using the Serper API."""
    try:
        url = "https://google.serper.dev/search"
        
        payload = json.dumps({
            "q": query
        })
        
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.request("POST", url, headers=headers, data=payload)
        logger.info(f"Serper API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            urls = []
            if 'organic' in data:
                urls = [result['link'] for result in data['organic'] if 'link' in result]
                logger.info(f"Found {len(urls)} URLs")
                return urls[:3]
        else:
            logger.error(f"Serper API Error: {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error in search_articles: {str(e)}")
        return []

def fetch_article_content(url: str) -> str:
    """Fetch and parse article content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout= 50)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Get text from article body or main content
        paragraphs = soup.find_all('p')
        content = ' '.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
        print(content[:5000])
        print("-"*100)
        return content[:5000] # Limit content length
    
    except Exception as e:
        logger.error(f"Error fetching content from {url}: {str(e)}")
        return ""

def concatenate_content(articles: List[Dict[str, str]]) -> str:
    """Concatenate article content with proper formatting."""
    combined_content = []
    for idx, article in enumerate(articles, 1):
        content = f"Article {idx}:\n{article['content']}\n\n"
        combined_content.append(content)
    return '\n'.join(combined_content)



def generate_answer(content: str, query: str) -> str:
    """Generate an answer using the LLM."""
    try:
        # Get LLM instance
        llm = LLMManager.get_instance()
        
        # Construct the prompt
        system_message = """
        You are an intelligent Web Search Content Summarizer, specialized in extracting, analyzing, and presenting information from web search results. Your primary goal is to provide clear, concise, and relevant summaries while maintaining the accuracy of the original content.
PRIMARY FUNCTIONS:

Content Synthesis


Extract key information from multiple search results
Identify main themes and crucial points
Remove redundant information
Present a unified, coherent summary
Highlight unique insights from different sources


Smart Summarization


Prioritize recent and relevant information
Focus on answering the user's specific question
Remove fluff and marketing language
Maintain the original meaning while condensing text
Include essential details and context


Information Organization


Structure information in order of relevance
Group related points together
Use bullet points for better readability
Present contrasting viewpoints when present
Highlight key statistics or data points


Source Integration


Link information to respective sources
Indicate when multiple sources confirm a point
Note any significant disagreements between sources
Provide context for source reliability when relevant

RESPONSE FORMAT:

Quick Summary (2-3 sentences)
[Provide the most important information that directly answers the query]
Key Points


[Main point 1]
[Main point 2]
[Main point 3]
...


Detailed Insights
[Expanded information organized by theme or relevance]


Theme/Topic 1:
• Detail
• Context
• Relevant data
Theme/Topic 2:
• [Similar structure]




HANDLING DIFFERENT QUERY TYPES:

Product/Service Queries


Focus on key features and benefits
Include relevant pricing information
Highlight user experiences and reviews
Note any common issues or limitations
Compare with alternatives if available


How-to/Instructions


Present steps in logical order
Include important prerequisites
Note common pitfalls or tips
Mention alternative methods if available
Add relevant safety warnings if applicable


News/Current Events


Prioritize most recent information
Include important background context
Note ongoing developments
Present different perspectives
Indicate information currency


Comparisons


Create clear comparison points
Highlight key differences
Note similarities when relevant
Include pros and cons
Mention context-dependent factors

QUALITY GUIDELINES:

Accuracy


Maintain factual accuracy
Cross-reference important claims
Note any uncertainties
Avoid exaggeration
Correct any contradictions


Relevance


Stay focused on the query
Remove irrelevant information
Prioritize user's specific needs
Include contextual information only when helpful


Clarity


Use simple, clear language
Define technical terms when needed
Break down complex concepts
Use examples for difficult ideas
Maintain logical flow


Conciseness


Remove redundant information
Use precise language
Break up long paragraphs
Prioritize essential information
Keep summaries focused

RESPONSE CHECKLIST:
✓ Directly answers the main question
✓ Includes relevant key points
✓ Removes redundant information
✓ Maintains original meaning
✓ Provides clear structure
✓ Links to sources
✓ Uses simple language
✓ Highlights important data
✓ Notes any uncertainties
✓ Stays focused on query
EXAMPLE RESPONSE:
Query: "What are the latest developments in wireless charging technology?"
Quick Summary:
Recent advances in wireless charging focus on extended range charging, faster charging speeds, and multi-device support. The technology has seen significant improvements in efficiency and adoption across various industries.
Key Points:

Extended range charging up to 30 feet now possible
New standards support 15W+ charging speeds
Multi-device charging mats becoming mainstream
Vehicle wireless charging gaining traction

Detailed Insights:
Recent Advancements:
• Long-range wireless power transmission using focused beams
• Enhanced efficiency through improved coil design
• Integration with common furniture and surfaces
Industry Adoption:
• Major smartphone manufacturers implementing new standards
• Automotive industry developing universal charging pads
• Public spaces beginning to install wireless charging infrastructure


Remember to:

Adapt summary length to query complexity
Include only relevant information
Maintain objective tone
Verify key claims across sources
Present information in digestible chunks
        """
        
        user_message = f"""Based on the following articles, please answer this question: {query}

        Articles:
        {content}

        Please provide a clear, concise answer based on the information in the articles above.
        If the information is not directly available in the articles, please say so."""
        
        # Generate response using the correct method
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Try invoke method first
            response = llm.invoke(messages)
            logger.info("Successfully used invoke method")
            return response.content if hasattr(response, 'content') else str(response)
        except AttributeError:
            try:
                # Try complete method as fallback
                response = llm.complete(user_message)
                logger.info("Successfully used complete method")
                return response.text if hasattr(response, 'text') else str(response)
            except AttributeError:
                try:
                    # Try predict method as final fallback
                    response = llm.predict(user_message)
                    logger.info("Successfully used predict method")
                    return str(response)
                except Exception as e:
                    logger.error(f"Error with predict method: {str(e)}")
                    return "Sorry, I couldn't generate an answer at this time."

    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        return "Sorry, I couldn't generate an answer at this time."