import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import io
import validators
from urllib.parse import urljoin
import os

def download_image(url, base_url):
    """Convert relative URLs to absolute URLs"""
    if not url.startswith(('http://', 'https://')):
        return urljoin(base_url, url)
    return url

def scrape_website(url, selectors):
    try:
        # Send GET request
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Dictionary to store results
        results = {}
        
        for selector_type, selector_value in selectors.items():
            if selector_value:  # Only process if selector is not empty
                if selector_type == 'Links':
                    elements = soup.find_all('a')
                    results[selector_type] = [elem.get('href') for elem in elements if elem.get('href')]
                elif selector_type == 'Text':
                    elements = soup.find_all(selector_value)
                    results[selector_type] = [elem.get_text(strip=True) for elem in elements]
                elif selector_type == 'Custom Class':
                    elements = soup.find_all(class_=selector_value)
                    results[selector_type] = [elem.get_text(strip=True) for elem in elements]
                elif selector_type == 'Images':
                    elements = soup.find_all('img')
                    image_data = []
                    for img in elements:
                        src = img.get('src')
                        if src:
                            absolute_url = download_image(src, url)
                            alt_text = img.get('alt', 'No alt text')
                            image_data.append({
                                'URL': absolute_url,
                                'Alt Text': alt_text
                            })
                    results[selector_type] = image_data        
        return results, None
    except requests.RequestException as e:
        return None, f"Error fetching the website: {str(e)}"
    except Exception as e:
        return None, f"An error occurred: {str(e)}"

def display_image_preview(image_url):
    """Display image preview in Streamlit"""
    try:
        st.image(image_url, caption=image_url, use_column_width=True)
    except Exception as e:
        st.error(f"Could not load image preview: {image_url}")

def main():
    st.title("Web Scraping Tool 🕸️")
    
    # URL input
    url = st.text_input("Enter the website URL:", "")
    
    # Validate URL
    if url and not validators.url(url):
        st.error("Please enter a valid URL")
        return
    
    # Selector inputs
    st.subheader("Select what to extract")
    
    selectors = {
        'Links': st.checkbox("Extract all links"),
        'Text': st.text_input("HTML tag to extract (e.g., 'p' for paragraphs, 'h1' for headings):"),
        'Custom Class': st.text_input("CSS class to extract (e.g., 'quote' or 'title'):"),
        'Images': st.checkbox("Extract all images")
    }
    
    if st.button("Start Scraping"):
        if url:
            with st.spinner("Scraping in progress..."):
                results, error = scrape_website(url, selectors)
                
                if error:
                    st.error(error)
                elif results:
                    # Display results
                    for selector_type, data in results.items():
                        if data:  # Only show if we have results
                            st.subheader(f"{selector_type} Found:")
                            
                            if selector_type == 'Images':
                                # Create DataFrame for images
                                df = pd.DataFrame(data)
                                st.dataframe(df)
                                
                                # Display image previews
                                st.subheader("Image Previews")
                                for idx, img_data in enumerate(data):
                                    with st.expander(f"Image {idx + 1} - {img_data['Alt Text'][:50]}..."):
                                        display_image_preview(img_data['URL'])
                                
                                # Create download button for image URLs
                                csv_buffer = io.StringIO()
                                df.to_csv(csv_buffer, index=False)
                                
                                st.download_button(
                                    label="Download Image Data as CSV",
                                    data=csv_buffer.getvalue(),
                                    file_name="image_data.csv",
                                    mime="text/csv"
                                )
                            else:
                                # Handle other types of data
                                df = pd.DataFrame(data, columns=[selector_type])
                                st.dataframe(df)
                                
                                csv_buffer = io.StringIO()
                                df.to_csv(csv_buffer, index=False)
                                
                                st.download_button(
                                    label=f"Download {selector_type} as CSV",
                                    data=csv_buffer.getvalue(),
                                    file_name=f"{selector_type.lower()}_data.csv",
                                    mime="text/csv"
                                )
                else:
                    st.warning("No data found with the specified selectors.")
        else:
            st.warning("Please enter a URL first.")
    
    # Add helpful information
    with st.expander("Help & Information"):
        st.markdown("""
        ### How to use this tool:
        1. Enter a website URL
        2. Choose what to extract:
           - Links: Gets all hyperlinks
           - Text: Enter HTML tags like 'p', 'h1', 'span', etc.
           - Custom Class: Enter specific CSS classes from the website
           - Images: Extracts all images with their URLs and alt text
        3. Click 'Start Scraping'
        4. Download results as CSV
        
        ### Image Extraction Features:
        - Extracts image URLs and alt text
        - Converts relative URLs to absolute URLs
        - Provides image previews
        - Allows downloading image data as CSV
        
        ### Note:
        - Some websites may block web scraping
        - Always check a website's robots.txt and terms of service
        - For dynamic websites (using JavaScript), this tool might not capture all content
        - Image previews may not work for some URLs due to website restrictions
        """)

if __name__ == "__main__":
    main()