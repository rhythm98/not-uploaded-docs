import json
import os
import re
 
# Directory containing the HTML files - using raw string
html_directory = r'D:\Pages\dtaa\dtaa'  # Using a raw string
 
# Sample JSON data
json_data = [
    {
        "title":"",
        "content": "",
        "country-name": "UAE"
    },
]
 
# Function to extract title from HTML content
def extract_title(html_content):
    # Find content between <title> tags
    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        return title_match.group(1).strip()
    return "Untitled Document"  # Default title if none found
 
# Function to minify HTML content without external dependencies
def minify_html(html_content):
    # Remove comments
    html_content = re.sub(r'<!--(.*?)-->', '', html_content, flags=re.DOTALL)
   
    # Remove extra whitespace between tags
    html_content = re.sub(r'>\s+<', '><', html_content)
   
    # Remove leading and trailing whitespace from lines
    html_content = re.sub(r'^\s+|\s+$', '', html_content, flags=re.MULTILINE)
   
    # Collapse multiple whitespace characters into a single space within text content
    html_content = re.sub(r'(?<=>)\s+(?=<)', ' ', html_content)
   
    # Remove unnecessary whitespace around attributes
    html_content = re.sub(r'\s*=\s*', '=', html_content)
   
    # Remove spaces between attribute quotes
    html_content = re.sub(r'"\s+', '"', html_content)
    html_content = re.sub(r'\s+"', '"', html_content)
   
    # Replace double quotes with single quotes in attribute values
    # This regex finds attributes with double quotes and converts them to single quotes
    html_content = re.sub(r'(\w+)="([^"]*)"', r"\1='\2'", html_content)
   
    return html_content
 
# Function to get all HTML files from the directory
def get_html_files(directory):
    html_files = []
    try:
        for filename in os.listdir(directory):
            if filename.endswith('.html'):
                html_files.append(os.path.join(directory, filename))
        return html_files
    except OSError as e:
        print(f"Error accessing directory: {e}")
        return []
 
# Function to read the HTML file and add minified content to the JSON
def update_json_with_html(json_data, html_files):
    updated_json = json_data.copy()
   
    for i, file in enumerate(html_files):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                html_content = f.read()
               
                # Extract the title from the HTML content
                title = extract_title(html_content)
               
                minified_html = minify_html(html_content)
               
                # Assuming you want to add the minified HTML to the first empty spot in the JSON array
                if i < len(updated_json):
                    updated_json[i]['title'] = title  # Use the extracted title
                    updated_json[i]['content'] = minified_html
                    updated_json[i]['country'] =   UAE
                    # updated_json[i]['law-slug'] = 'uae-cit'
                else:
                    updated_json.append({
 
                        'title': title,
                        'content': minified_html,
                        'country': 'UAE',
                    })
        except FileNotFoundError:
            print(f"File {file} not found.")
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
   
    return updated_json
 
# Get the list of HTML files from the specified directory
html_files = get_html_files(html_directory)
print("The list of HTML files name: ", html_files)
 
# Call the function to update the JSON with minified HTML content only if files were found
if html_files:
    updated_json = update_json_with_html(json_data, html_files)
 
    # Print the updated JSON (you can also save it to a file)
    print(json.dumps(updated_json, indent=4))
 
    # Save the updated JSON to a file
    with open('uae-cit-fdl-47.json', 'w', encoding='utf-8') as outfile:
        json.dump(updated_json, outfile, indent=4)
    print("JSON file has been created successfully.")
else:
    print("No HTML files were found or could not access the directory.")