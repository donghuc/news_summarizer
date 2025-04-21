import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import re
import time



client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

headers = {
    "User-Agent": "Mozilla/5.0"
}

def is_valid_url(url):
    # Simple pattern to check if URL starts with http(s):// and has a domain
    pattern = re.compile(r'^(http|https)://[^\s]+$')
    return re.match(pattern, url) is not None


def fetch_article_text(url):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.MissingSchema:
        st.error("⚠️ Invalid URL. Did you forget to include 'https://'?")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Error fetching the article: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    article = "\n".join([p.get_text() for p in paragraphs])
    return article if article.strip() else None

def summarize_text(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Vui lòng tóm tắt bài báo dưới đây thành một đoạn văn ngắn bằng tiếng Việt:\n" + text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"⚠️ Error during summarization: {e}")
        return None

# Streamlit UI
st.set_page_config(page_title="News Summarizer", layout="centered")
st.title("📰 Tóm tắt bài báo bằng ChatGPT")
st.caption("Dán link bài viết và nhận đoạn tóm tắt bằng tiếng Việt ✨")
st.markdown("## Tóm tắt thông minh với ChatGPT 🚀")


url = st.text_input("🔗 Dán đường link bài báo:")

if st.button("Tóm tắt"):
    if url:
        if not is_valid_url(url):
            st.warning("⚠️ Link không hợp lệ. Đảm bảo link bắt đầu bằng http:// hoặc https://")
        else:
            with st.spinner("⏳ Đang lấy nội dung..."):
                time.sleep(2)  # Fake delay to simulate a long fetch
                article = fetch_article_text(url)

            if article:
                with st.spinner("🧠 Đang tóm tắt..."):
                    time.sleep(2)
                    summary = summarize_text(article[:4000])
                if summary:
                    st.success("✅ Tóm tắt:")
                    st.write(summary)
            else:
                st.error("❌ Không thể lấy nội dung bài viết.")
    else:
        st.warning("⚠️ Bạn chưa nhập link.")

st.write("")
st.write("")
st.write("")
st.markdown("""
---
🧠 Made with ❤️ by [ChatGPT]  
🔗 Powered by [OpenAI](https://openai.com) and [Streamlit](https://streamlit.io)
""")
