import re
import os
import sys

# ...existing code...

def remove_base64_images(file_path):
    """Remove base64 image data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # More comprehensive pattern that catches all base64 image formats
        pattern = r'src="data:image/[^;]+;base64,[A-Za-z0-9+/=]+"'
        
        # Replace with empty src
        new_content = re.sub(pattern, 'src=""', content)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print(f"Removed base64 images from {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python roman_to_arabic_converter.py <file_path> [mode]")
        return
    
    file_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "roman"
    
    if mode == "pattern":
        if os.path.isfile(file_path):
            replace_specific_pattern(file_path)
        elif os.path.isdir(file_path):
            for root, _, files in os.walk(file_path):
                for file in files:
                    if file.endswith(('.html', '.htm')):
                        replace_specific_pattern(os.path.join(root, file))
    elif mode == "remove-base64":
        if os.path.isfile(file_path):
            remove_base64_images(file_path)
        elif os.path.isdir(file_path):
            for root, _, files in os.walk(file_path):
                for file in files:
                    if file.endswith(('.html', '.htm', '.xml')):
                        remove_base64_images(os.path.join(root, file))
    else:  # Default roman mode
        if os.path.isfile(file_path):
            replace_roman_in_file(file_path)
        elif os.path.isdir(file_path):
            for root, _, files in os.walk(file_path):
                for file in files:
                    if file.endswith(('.txt', '.html', '.md')):
                        replace_roman_in_file(os.path.join(root, file))
    
    if not os.path.exists(file_path):
        print(f"Path not found: {file_path}")

if __name__ == "__main__":
    main()
