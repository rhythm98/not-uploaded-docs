import re
import json
import logging
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def minify_html(html_content):
    """Minify HTML content."""
    # Simple regex-based HTML minification
    # Remove comments
    html_content = re.sub(r'<!--(.*?)-->', '', html_content, flags=re.DOTALL)
    # Remove extra whitespace between tags
    html_content = re.sub(r'>\s+<', '><', html_content)
    # Remove leading and trailing whitespace
    html_content = re.sub(r'^\s+|\s+$', '', html_content, flags=re.MULTILINE)
    return html_content

def extract_article_info(html_content, file_path):
    """Extract article information from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # More flexible article pattern
    article_pattern = re.compile(r'(?:Article|ARTICLE)\s*(\d+)\s*(?:[-–—:.]*\s*(.*)|$)', re.IGNORECASE)
    part_pattern = re.compile(r'(?:Part|PART)\s*(\d+)\s*[-–—:.]*\s*(.*)', re.IGNORECASE)
    chapter_pattern = re.compile(r'(?:Chapter|CHAPTER)\s*(\d+)\s*[-–—:.]*\s*(.*)', re.IGNORECASE)
    
    # Store hierarchy information
    parts = {}  # Key: part number, Value: part info
    chapters = {}  # Key: chapter number, Value: chapter info
    current_part = None
    current_chapter = None
    
    # Log some sample HTML to debug
    logger.debug(f"Sample HTML content: {soup.prettify()[:500]}...")
    
    # Find all text elements that might contain article headers
    all_text_elements = []
    for element in soup.find_all(string=True):
        if element.strip():  # Only include non-empty text
            all_text_elements.append(element)
    
    logger.info(f"Found {len(all_text_elements)} text elements in {file_path}")
    
    # Create a mapping of all elements with their positions
    all_elements = all_text_elements.copy()
    # First pass - identify all structural elements (parts, chapters, articles) and their positions
    article_positions = []
    for i, element in enumerate(all_text_elements):
        text = element.strip() if hasattr(element, 'strip') else str(element)
        
        # Check for part
        part_match = part_pattern.match(text)
        if part_match and len(text) < 100:
            part_number = part_match.group(1)
            part_title = part_match.group(2).strip() if part_match.group(2) else ""
            part_name = f"Part {part_number} - {part_title}"
            part_fullpath = f"part{part_number}"
            
            parts[part_number] = {
                "type": "PART",
                "number": part_number,
                "name": part_name,
                "fullPath": part_fullpath,
                "position": i
            }
            current_part = part_number
        
        # Check for chapter
        chapter_match = chapter_pattern.match(text)
        if chapter_match and len(text) < 100:
            chapter_number = chapter_match.group(1)
            chapter_title = chapter_match.group(2).strip() if chapter_match.group(2) else ""
            chapter_name = f"Chapter {chapter_number} - {chapter_title}"
            
            if current_part:
                chapter_fullpath = f"{parts[current_part]['fullPath']}/chapter{chapter_number}"
            else:
                chapter_fullpath = f"chapter{chapter_number}"
            
            chapters[chapter_number] = {
                "type": "CHAPTER",
                "number": chapter_number,
                "name": chapter_name,
                "fullPath": chapter_fullpath,
                "position": i,
                "part": current_part
            }
            current_chapter = chapter_number
        
        # Check for article
        article_match = None
        try:
            article_match = article_pattern.match(text)
        except (TypeError, AttributeError):
            pass
        if article_match and len(text) < 100:
            article_number = article_match.group(1)
            article_title = article_match.group(2).strip() if article_match.group(2) else ""
            logger.info(f"Found article: Article {article_number} - {article_title}")
            
            parent = element.parent if hasattr(element, 'parent') else None
            article_positions.append({
                "position": i,
                "number": article_number,
                "title": article_title,
                "part": current_part,
                "chapter": current_chapter,
                "element": parent,
                "text": text
            })
    
    # Sort articles by position to ensure correct order
    article_positions.sort(key=lambda x: x["position"])
    
    # Remove duplicate articles (keep the first occurrence)
    seen_numbers = set()
    unique_articles = []
    for article in article_positions:
        if article["number"] not in seen_numbers:
            seen_numbers.add(article["number"])
            unique_articles.append(article)
    
    articles = []
    
    # Second pass - extract content for each article
    for i, article in enumerate(unique_articles):
        article_number = article["number"]
        article_title = article["title"]
        start_pos = article["position"]
        start_element = article["element"]
        
        # Determine end position for this article
        end_pos = len(all_elements)
        if i < len(unique_articles) - 1:
            end_pos = unique_articles[i+1]["position"]
        
        # Extract path information
        path = []
        if article["part"]:
            path.append({
                "type": "PART",
                "number": parts[article["part"]]["number"],
                "name": parts[article["part"]]["name"],
                "fullPath": parts[article["part"]]["fullPath"]
            })
        
        if article["chapter"]:
            path.append({
                "type": "CHAPTER",
                "number": chapters[article["chapter"]]["number"],
                "name": chapters[article["chapter"]]["name"],
                "fullPath": chapters[article["chapter"]]["fullPath"]
            })
            
        # Extract content for the article
        try:
            if start_element:
                # Start from the element containing the article title
                current = start_element
                content_elements = [f"<h3>Article {article_number} - {article_title}</h3>"]
                
                # Collect all elements until the next article title or end
                while current and (i == len(unique_articles) - 1 or all_text_elements.index(current) < end_pos):
                    # Check if we've reached the next article title
                    if (hasattr(current, 'string') and 
                        current.string is not None and 
                        hasattr(current.string, 'strip')):
                        stripped_text = current.string.strip()
                        try:
                            if isinstance(stripped_text, str) and article_pattern.match(stripped_text):
                                break
                        except (TypeError, AttributeError):
                            pass
                    
                    content_elements.append(str(current))
                    current = current.next_sibling if hasattr(current, 'next_sibling') else None
                
                content = "".join(content_elements)
            else:
                # Fallback to text extraction if we can't get HTML structure
                article_text = article["text"] if "text" in article else f"Article {article_number}"
                content = f"<h3>{article_text}</h3>"
                
                content_elements = []
                for j in range(start_pos + 1, end_pos):
                    if j < len(all_text_elements):
                        elem = all_text_elements[j]
                        content_elements.append(str(elem))
                
                content += " ".join(content_elements)
        except Exception as e:
            logger.warning(f"Error extracting content for Article {article_number}: {e}")
            content = f"<h3>Article {article_number} - {article_title}</h3>"
            content_elements = []
            for j in range(start_pos + 1, end_pos):
                if j < len(all_elements):
                    elem = all_elements[j]
                    if hasattr(elem, 'name'):  # HTML tag
                        content_elements.append(str(elem))
                    elif hasattr(elem, 'strip') and elem.strip():  # Text node
                        content_elements.append(elem)
            
            content = "".join(content_elements)
        
        # Clean up the content but preserve HTML structure
        content = minify_html(content)
        
        # Make sure content starts with the article title
        if not content.startswith(f"Article {article_number}"):
            content = f"<h3>Article {article_number} - {article_title}</h3>" + content
        
        # Add article to the list
        articles.append({
            "number": article_number,
            "title": f"Article {article_number} - {article_title}",
            "content": content,
            "orderIndex": int(article_number),
            "path": path
        })
    
    return articles

def process_html_files(directory_path):
    all_articles = []
    
    directory = Path(directory_path)
    html_files = list(directory.glob("**/*.html"))
    logger.info(f"Found {len(html_files)} HTML files in {directory_path}")
    
    if not html_files:
        logger.warning(f"No HTML files found in {directory_path}. Check the directory path.")
    
    for html_file in html_files:
        logger.info(f"Processing file: {html_file}")
        try:
            with open(html_file, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            logger.info(f"File size: {len(html_content)} bytes")
            articles = extract_article_info(html_content, html_file)
            logger.info(f"Extracted {len(articles)} articles from {html_file}")
            all_articles.extend(articles)
        except Exception as e:
            logger.error(f"Error processing {html_file}: {e}")
    
    return all_articles

def save_articles_to_json(articles, output_file):
    """Save articles to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(articles, file, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(articles)} articles to {output_file}")

def main():
    # Directory containing HTML files
    directory_path = r"C:\Users\Rahul V\Desktop\Finteger projects\temp\not-uploaded-docs\Excise Laws\Gcc Common agreeemnt"
    
    # Output JSON file
    output_file = r"C:\Users\Rahul V\Desktop\Finteger projects\temp\GCC_common_agreement_articles.json"
    
    # Process HTML files and get articles
    articles = process_html_files(directory_path)
    
    # Save articles to JSON
    save_articles_to_json(articles, output_file)
    
    # Print summary
    logger.info(f"Processed {len(articles)} articles in total")

if __name__ == "__main__":
    main()