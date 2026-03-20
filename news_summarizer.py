
import requests
from bs4 import BeautifulSoup
import openai
import os
from datetime import datetime
import time

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
            # 增加对描述信息的抓取，作为备选摘要来源
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
        # 增加超时和重试逻辑
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 移除脚本和样式标签
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        # 尝试寻找文章主体内容
        article_text = ""
        # 常见的文章内容容器标签
        content_tags = soup.find_all(['article', 'div'], class_=['article-body', 'content', 'post-content', 'entry-content'])
        if content_tags:
            article_text = ' '.join([tag.get_text() for tag in content_tags])
        else:
            # 如果没找到特定容器，则抓取所有段落
            paragraphs = soup.find_all('p')
            article_text = ' '.join([p.get_text() for p in paragraphs])
            
        # 清理多余空格
        article_text = ' '.join(article_text.split())
        return article_text if len(article_text) > 200 else "" # 如果内容太短，可能抓取失败
    except Exception as e:
        print(f"Error fetching article content from {url}: {e}")
        return ""

def summarize_text_with_ai(title, description, content):
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = "https://api.scnet.cn/api/llm/v1"
    
    if not api_key:
        return "API_KEY not set."
    
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    # 构造输入内容：优先使用正文，正文不足则使用描述信息
    input_text = f"标题: {title}\n"
    if content:
        input_text += f"正文内容: {content[:3000]}" # 限制长度
    else:
        input_text += f"摘要信息: {description}"
    
    try:
        response = client.chat.completions.create(
            model="MiniMax-M2.5",
            messages=[
                {"role": "system", "content": "你是一个专业的新闻摘要助手。请根据提供的新闻标题和内容，生成一段150-200字的详细文字摘要。要求：语言精炼、客观，涵盖新闻的核心要点。"},
                {"role": "user", "content": f"请为以下新闻生成详细的文字摘要：\n\n{input_text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing text with AI: {e}")
        return "摘要生成出错，请检查 API 配置或网络连接。"

def main():
    news_headlines = get_news_headlines()
    summary_output = f"# 每日新闻摘要 - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    summary_output += "> 自动抓取全球热门新闻，并由 AI 生成详细文字摘要。\n\n---\n\n"

    for i, news in enumerate(news_headlines[:5]): # 总结前5条新闻
        print(f"正在处理第 {i+1} 条新闻: {news['title']}")
        article_content = get_article_content(news['link'])
        
        # 即使抓取不到正文，也利用 RSS 提供的 description 进行摘要
        summary = summarize_text_with_ai(news['title'], news['description'], article_content)
        
        summary_output += f"### {i+1}. {news['title']}\n\n"
        summary_output += f"**摘要内容：**\n{summary}\n\n"
        summary_output += f"**原文链接：** [点击阅读]({news['link']})\n\n"
        summary_output += "---\n\n"
        
        # 避免请求过快
        time.sleep(1)

    output_filename = f"news_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(summary_output)
    print(f"新闻摘要已保存至 {output_filename}")

if __name__ == "__main__":
    main()
