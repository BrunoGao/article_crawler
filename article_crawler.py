import argparse
import os
import requests
from bs4 import BeautifulSoup
import html2text
import random
import json
from datetime import datetime
import re

html_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Document</title>
</head>
<body>
{article}
</body>
</html>
"""
date_published = ""
class MarkdownHeader:
    def __init__(self, title, date, authors, tags, summary):
        self.title = title
        self.date = date
        self.authors = authors  # authors现在是一个包含多个属性的结构体
        self.tags = tags
        self.summary = summary
        

    def to_markdown(self):
        tags_formatted = ', '.join([f'"{tag}"' for tag in self.tags])
        # 格式化authors信息，假设authors是一个字典
        authors_formatted = f'name: {self.authors["name"]}\n' \
                            f'  title: {self.authors["title"]}\n' \
                            f'  url: {self.authors["url"]}\n' \
                            f'  image_url: {self.authors["image_url"]}'
        return f"""---
title: "{self.title}"
publishdate: {self.date}
authors: 
  {authors_formatted}
tags: [{tags_formatted}]
summary: >-
  {self.summary}
---
 """

class MarkdownFooter:
    def __init__(self, authors, docUrl):
        self.authors = authors
        self.docUrl = docUrl

    def to_markdown(self):
        return f"""
:::tip 版权说明

作者：{self.authors}

链接：{self.docUrl}
::: 
"""
        



USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36"
]


class ArticleCrawler():
    def __init__(self, url, output_folder, config_path='./config.json'):
        self.url = url
        self.output_folder = output_folder
        self.config = self.load_config(config_path, url)
        self.headers = {
            'user-agent': random.choice(USER_AGENT_LIST)
        }
        self.html_str = html_str
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"{output_folder} does not exist, automatically create...")

    def load_config(self, config_path, url):
        with open(config_path, 'r') as file:
            config = json.load(file)
        # Extract the domain name from the URL to match with the config
        domain = url.split('/')[2].split('.')[-2]
        print("domain: "  + domain)
        if domain in config:
            return config[domain]
        else:
            raise ValueError(f"No configuration found for {domain}")

    def fetch_author_info(self, soup):
        author_info = {}
        selectors = self.config.get('author_info_selectors', {})
        
        # 获取作者名称
        name_selector = selectors.get('name')
        if name_selector:
            name_tag = soup.select_one(name_selector)
            if name_tag:
                author_info['name'] = name_tag.text.strip() if name_tag.name != 'meta' else name_tag['content']
                
        # 获取作者职称
        title_selector = selectors.get('title')
        print("title_selector: " + title_selector)
        if title_selector:
            title_tag = soup.select_one(title_selector)
            print( title_tag.text.strip())
            if title_tag:
                author_info['title'] = title_tag.text.strip() if title_tag.name != 'meta' else title_tag['content']
        
        # 获取作者个人页面的URL
        url_selector = selectors.get('url')
        if url_selector:
            url_tag = soup.select_one(url_selector)
            if url_tag:
                author_info['url'] = url_tag['content'] if url_tag.name == 'meta' else url_tag['href']
        
        # 获取作者头像的URL
        image_url_selector = selectors.get('image_url')
        if image_url_selector:
            image_url_tag = soup.select_one(image_url_selector)
            if image_url_tag:
                author_info['image_url'] = image_url_tag['content'] if image_url_tag.name == 'meta' else image_url_tag['src']
        
        return author_info

    def deal_code(self, soup):
        code_blocks = soup.find_all('code', class_=lambda x: x and re.search(r'(hljs|language-)', x))
        #code_selector = self.config.get('code_selector', {})
        
        #print(code_selector)
        #code_blocks = soup.find_all(code_selector['item'], class_=code_selector['class'])
        print(code_blocks)
        for code_block in code_blocks:
        
            #lang = code_block.get('lang', None)  # 使用get方法安全地获取lang属性，如果不存在则返回None
            lang_classes = [cls for cls in code_block.get('class', []) if 'language-' in cls]
            lang = lang_classes[0].split('-')[1] if lang_classes else 'plaintext'  # Default to 'plaintext' if no language class found
        
            if lang:
                print(f"Found a code block with lang='{lang}'")
            else:
                lang = "plaintext"
            
            code_content = code_block.text
            formatted_code = f"```{lang}\n{code_content}\n```"
            code_block.replace_with(BeautifulSoup(formatted_code, 'html.parser'))

    def deal_images(self, soup):
        image_tags = soup.find_all('img')
        for img in image_tags:
            src = img.get('src')
            alt = img.get('alt', '')
            markdown_image = f"![{alt}]({src})\n\n"
            img.replace_with(BeautifulSoup(markdown_image, 'html.parser'))

    def send_request(self, url):
        response = requests.get(url=url, headers=self.headers)
        response.encoding = "utf-8"
        if response.status_code == 200:
            return response

    def parse_detail(self, response):
        html = response.text
        soup = BeautifulSoup(html, 'lxml')
        
        title_selector = self.config.get('title_selector', {})
        
        print(title_selector)
        title_tag = soup.find(attrs=title_selector)
        title = title_tag['content'] if title_tag and 'content' in title_tag.attrs else title_tag.text.strip()
        print("title:" + title)
        
        

        # Attempt to find the 'datePublished' meta tag, default to today's date if not found
        date_published_meta = soup.find('meta', itemprop='datePublished')
        date_published = date_published_meta['content'][:10] if date_published_meta else datetime.today().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
        print("date_published:" + date_published)


        authors_info = self.fetch_author_info(soup)
        author_name = authors_info['name']
        print("author_name:" + author_name)
        
        keywords_selector = self.config.get('keywords_selector', {})
        
        print(keywords_selector)
        keywords_tag = soup.find(attrs=keywords_selector)
        print(keywords_tag)
        keywords = keywords_tag['content'].split(',') #if keywords_tag and 'content' in keywords_tag.attrs else keywords_tag.text.strip().split(',')
        
        tags = keywords  # Or however you wish to define tags based on the extracted keywords
        print(tags)
        
        
        summary = "Your summary here"  # Placeholder for where you might define a summary
        markdown_header = MarkdownHeader(title, date_published, authors_info, tags, summary).to_markdown()
        markdown_footer = MarkdownFooter(author_name, self.url).to_markdown()
        
        self.deal_code(soup)  # 在这里调用deal_code方法
        self.deal_images(soup)  # 处理图片
          # Use the tag and id from the loaded config for content extraction
        content_tag = self.config.get('tag', 'div')  # Default to 'div' if not specified
        content_id = self.config.get('id', 'article-root')  # Default to empty string if not specified
        print(content_tag + content_id)
        content = soup.find(content_tag, id=content_id).prettify()
        #print(content)
        html = self.html_str.format(article=content)
        
        self.write_content(html, title, markdown_header, markdown_footer, date_published)

    def write_content(self, content, name, markdown_header, markdown_footer, date_published):
        if not os.path.exists(self.output_folder + '/HTML'):
            os.makedirs(self.output_folder + '/HTML')
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder )
        
        html_path = os.path.join(self.output_folder, "HTML", name + ".html")
        
        name= date_published+"-" + name 
    
        md_path = os.path.join(self.output_folder, name + ".md")
        
        #print("md_path: " + md_path)

        with open(html_path, 'w', encoding="utf-8") as f:
            f.write(content)
            print(f"create {name}.html in {self.output_folder} successfully")

        html_text = open(html_path, 'r', encoding='utf-8').read()
        markdown_text = html2text.html2text(html_text, bodywidth=0)
        markdown_text = markdown_header + markdown_text + markdown_footer
        #print(markdown_text)
        #self.deal_images(markdown_text)
        with open(md_path, 'w', encoding='utf-8') as file:
            file.write(markdown_text)
            print(f"create {name}.md in {self.output_folder} successfully")

    def change_title(self, title):
        return title

    def start(self):
        response = self.send_request(self.url)
        if response:
            self.parse_detail(response)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Article Crawler")
    parser.add_argument("-u", "--url", required=True, help="URL of the article to crawl")
    parser.add_argument("-o", "--output", required=True, help="Output folder for the crawled article")
    parser.add_argument("-c", "--config", default="config.json", help="Path to the configuration file")
    args = parser.parse_args()

    # 假设您的 ArticleCrawler 类已经适当地实现了抓取逻辑
    # 您可能需要根据实际情况调整 tag, class_, 和 id 参数
    crawler = ArticleCrawler(url=args.url, output_folder=args.output, config_path=args.config)
    crawler.start()