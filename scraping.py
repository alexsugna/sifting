"""
This file scrapes wikipedia for information on a subject. It then
compiles that information to a text file that can be used for 
text generation in a rnn.

Alex Angus

March 21, 2020
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from bs4.element import Comment
import text_generation


class Page():
    def __init__(self, title, links):
        self.title = title
        self.links = links
        self.num_links = len(self.links)
        self.text = None
        self.cleaned = False
        
    def add_text(self, text):
        """
        Adds a string of text to the page
        """
        self.cleaned = False
        self.text = text
        
    def clean_text(self):
        """
        Removes citations and double spaces from text
        """
        cleaned_text = ''
        started = False
        for char in self.text:
            if char == '[':
                started = True
            elif started and (char == ']'):
                started = False
            elif started and (char != ']'):
                continue
            else:
                cleaned_text += char
        self.add_text(cleaned_text)
        cleaned_text = ''
        last_space = False
        for char in self.text:
            if (char == ' ') and not last_space:
                cleaned_text += char
                last_space = True
            elif (char == ' ') and last_space:
                last_space = True
            else:
                cleaned_text += char
                last_space = False
        self.add_text(cleaned_text)
        self.cleaned = True
        
    def format_text(self):
        """
        Reformats text by putting a newline character between each sentence and
        removing sentences that start with a number (these are usually captions)
        """
        sentences = []
        current = ''
        for char in self.text:
            if char == '\n':
                char = ' '
            current += char
            if char == '.':
                if (current == '.') or (len(current) < 10):
                    current = ''
                    continue
                sentences.append(current)
                current = ''
        formatted_text = ''
        for sentence in sentences:
            if (not sentence[0].isnumeric()) and ('×' not in sentence):
                formatted_text += (sentence + '\n')
        self.add_text(formatted_text)
        
                
def get_text(soup):
    body = soup.findAll('p')
    compiled_text = ''
    for text in body:
        paragraph = text.text
        if paragraph is not None:
            compiled_text += paragraph
            
    return compiled_text
    
    
def scrape_page(url, get_links=False):
    """
    This function takes a url and returns a page object
    """
    r = requests.get(url)                               # request page
    soup = BeautifulSoup(r.text, 'html.parser')         # convert html to text
    page_links = []
    if get_links:
        for link in soup.findAll('a'):                      # retrieve all links from page
            link_text = link.get('href')
            if link_text != None:
                if '#' not in link_text:
                    if 'http' not in link_text:
                        link_text = 'https://en.wikipedia.org' + link_text
                    if 'en.' in link_text:
                        page_links.append(link_text)
    
    heading = soup.find(id='firstHeading')
    if heading is not None:
        title = heading.text
    else:
        title = url
    text = get_text(soup)
    page = Page(title, page_links)
    page.add_text(text)
    page.clean_text()
    page.format_text()
    page.clean_text()
    return page


def main():
    picasso_url = 'https://en.wikipedia.org/wiki/Pablo_Picasso'
    pages = []
    picasso = scrape_page(picasso_url, get_links=True)    
    pages.append(picasso)
    link_queue = picasso.links
    visited = [picasso_url]
    count = 0
    while len(link_queue) > 0:
        current_link = link_queue.pop(0)
        if 'File:' in current_link:
            continue
        
        if current_link not in visited:
            visited.append(current_link)
            page = scrape_page(current_link)
            if 'Help' in page.title:
                continue
            pages.append(page)
            link_queue += page.links
            print("Page: ", page.title)
            print("Number of links in queue: ", len(link_queue))
            count += 1
        if count > 100:
            break
    text_file = open("training_text.txt", 'w')
    for page in pages:
        text_file.writelines(page.text)
    text_file.close()
    
    train = True
    if train:
        text_generation.train()
    
if __name__ == "__main__":
    main()
