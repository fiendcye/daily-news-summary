
import requests
from bs4 import BeautifulSoup
import openai
import os
from datetime import datetime
import time
import glob

def get_news_headlines():
    url = "https://news.google.com/news/rss"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, verify=False) # 添加 verify=False
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        news_list = []
        for item in items:
            title = item.find('title').text
            link = item.find('link').text
            description = item.find('description').text if item.find('description') else ""
            news_list.append({'title': title, 'link': link, 'description': description})
        return news_list
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news headlines: {e}")
        return []

def get_article_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False) # 添加 verify=False
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        article_text = ""
        content_tags = soup.find_all(['article', 'div'], class_=['article-body', 'content', 'post-content', 'entry-content'])
        if content_tags:
            article_text = ' '.join([tag.get_text() for tag in content_tags])
        else:
            paragraphs = soup.find_all('p')
            article_text = ' '.join([p.get_text() for p in paragraphs])
            
        article_text = ' '.join(article_text.split())
        return article_text if len(article_text) > 200 else ""
    except Exception as e:
        print(f"Error fetching article content from {url}: {e}")
        return ""

def summarize_text_with_ai(title, description, content):
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = "https://api.scnet.cn/api/llm/v1"
    
    if not api_key:
        return "API_KEY not set."
    
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    input_text = f"新闻标题: {title}\n"
    if content:
        input_text += f"新闻正文: {content[:4000]}\n" # 限制长度，避免超出模型限制
    elif description:
        input_text += f"新闻描述: {description}\n"
    else:
        input_text += "无可用新闻内容。"

    try:
        response = client.chat.completions.create(
            model="MiniMax-M2.5",
            messages=[
                {"role": "system", "content": "你是一个专业的新闻摘要助手。请根据提供的新闻标题、正文或描述，生成一段150-200字的详细、客观、精炼的文字摘要。摘要应涵盖新闻的核心要点，避免重复和冗余。"},
                {"role": "user", "content": f"请为以下新闻生成详细的文字摘要：\n\n{input_text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing text with AI: {e}")
        return "摘要生成出错，请检查 API 配置或网络连接。"

def clean_old_summaries(today_date_str):
    # 删除当天所有旧的摘要文件
    pattern = f"news_summary_{today_date_str}*.md"
    old_files = glob.glob(pattern)
    for f in old_files:
        try:
            os.remove(f)
            print(f"Deleted old summary file: {f}")
        except OSError as e:
            print(f"Error deleting file {f}: {e}")

def main():
    today_date_str = datetime.now().strftime("%Y-%m-%d")
    clean_old_summaries(today_date_str)

    news_headlines = get_news_headlines()
    summary_output = f"# 每日新闻摘要 - {today_date_str}\n\n"
    summary_output += "> 自动抓取全球热门新闻，并由 AI 生成详细文字摘要。\n\n---\n\n"

    for i, news in enumerate(news_headlines[:5]): # 总结前5条新闻
        print(f"正在处理第 {i+1} 条新闻: {news['title']}")
        article_content = get_article_content(news['link'])
        
        summary = summarize_text_with_ai(news['title'], news['description'], article_content)
        
        summary_output += f"### {i+1}. {news['title']}\n\n"
        summary_output += f"**摘要内容：**\n{summary}\n\n"
        summary_output += f"**原文链接：** [点击阅读]({news['link']})\n\n"
        summary_output += "---\n\n"
        
        time.sleep(1) # 避免请求过快

    output_filename = f"news_summary_{today_date_str}.md"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(summary_output)
    print(f"新闻摘要已保存至 {output_filename}")

if __name__ == "__main__":
    main()
