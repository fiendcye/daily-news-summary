
import requests
from bs4 import BeautifulSoup
import openai
import os
from datetime import datetime

def get_news_headlines():
    url = "https://news.google.com/news/rss"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        news_list = []
        for item in items:
            title = item.find('title').text
            link = item.find('link').text
            news_list.append({'title': title, 'link': link})
        return news_list
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news headlines: {e}")
        return []

def get_article_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        article_text = ' '.join([p.get_text() for p in paragraphs])
        return article_text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching article content from {url}: {e}")
        return ""

def summarize_text_with_ai(text):
    # scnet.cn OpenAI-compatible API configuration
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = "https://api.scnet.cn/api/llm/v1" # scnet.cn OpenAI-compatible base URL
    
    if not api_key:
        return "API_KEY not set."
    
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    try:
        response = client.chat.completions.create(
            model="MiniMax-M2.5", # MiniMax model name on scnet.cn
            messages=[
                {"role": "system", "content": "你是一个专业的新闻摘要助手，请用简洁的中文总结新闻内容。"},
                {"role": "user", "content": f"请用3-5句话总结以下新闻文章：{text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing text with AI: {e}")
        return "摘要生成出错。"

def main():
    news_headlines = get_news_headlines()
    summary_output = f"# 每日新闻摘要 - {datetime.now().strftime('%Y-%m-%d')}\n\n"

    for i, news in enumerate(news_headlines[:5]): # Summarize top 5 news articles
        print(f"正在处理第 {i+1} 条新闻: {news['title']}")
        article_content = get_article_content(news['link'])
        if article_content:
            summary = summarize_text_with_ai(article_content)
            summary_output += f"## {news['title']}\n"
            summary_output += f"**链接:** {news['link']}\n"
            summary_output += f"**摘要:** {summary}\n\n"
        else:
            summary_output += f"## {news['title']}\n"
            summary_output += f"**链接:** {news['link']}\n"
            summary_output += f"**摘要:** 无法获取文章内容进行摘要。\n\n"

    output_filename = f"news_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(summary_output)
    print(f"新闻摘要已保存至 {output_filename}")

if __name__ == "__main__":
    main()
