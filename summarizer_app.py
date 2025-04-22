import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import re
import io
import time
from fpdf import FPDF


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

headers = {
    "User-Agent": "Mozilla/5.0"
}

# Define options dictionary
SUMMARY_STYLES = {
    "brief": {
        "label": "Ngắn gọn",
        "prompts": {
            "Tiếng Việt": "Tóm tắt nội dung sau một cách ngắn gọn bằng tiếng Việt.",
            "English": "Summarize the following text briefly in English."
        }
    },
    "professional": {
        "label": "Chuyên nghiệp",
        "prompts": {
            "Tiếng Việt": "Tóm tắt bài viết sau theo phong cách chuyên nghiệp và trang trọng bằng tiếng Việt.",
            "English": "Summarize this article in a professional and formal tone in English."
        }
    },
    "friendly": {
        "label": "Thân thiện",
        "prompts": {
            "Tiếng Việt": "Tóm tắt bài báo một cách thân thiện và dễ hiểu bằng tiếng Việt.",
            "English": "Summarize this article in a friendly and clear tone in English."
        }
    },
    "bulleted": {
        "label": "Dạng gạch đầu dòng",
        "prompts": {
            "Tiếng Việt": "Tóm tắt bài viết bằng tiếng Việt dưới dạng gạch đầu dòng.",
            "English": "Summarize the article as English bullet points."
        }
    },
    "funny": {
        "label": "Hài hước",
        "prompts": {
            "Tiếng Việt": "Tóm tắt bài viết bằng tiếng Việt theo phong cách vui vẻ, hài hước.",
            "English": "Summarize the article in a humorous tone in English."
        }
    }
}

length_modifiers = {
    "Ngắn gọn": " Chỉ cung cấp thông tin quan trọng nhất.",
    "Vừa phải": " Bao gồm các điểm chính với một chút chi tiết.",
    "Chi tiết": " Bao gồm nhiều chi tiết cụ thể trong phần tóm tắt."
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
    article = "\n".join([p.get_text().strip() for p in paragraphs])
    return article if article.strip() else None

def summarize_text(text, style_key, language, length):

    style_prompt = SUMMARY_STYLES[style_key]["prompts"][language]
    prompt = f"{style_prompt}{length_modifiers[length]}\n\n{text}"


    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"⚠️ Error during summarization: {e}")
        return None


#Create PDF file
def create_summary_pdf(title, summary_text):
    pdf = FPDF()
    pdf.add_page()
    # Add Unicode font (Google Font)
    pdf.add_font("Roboto", "", "Roboto-Regular.ttf", uni=True)
    pdf.set_font("Roboto", size=12)
    pdf.cell(200, 10, txt=title, ln=True, align="L")
    pdf.ln(5)

    for line in summary_text.split("\n"):
        pdf.multi_cell(0, 10, txt=line)

    # Create file in memory
    # Instead of writing to file, return PDF as binary string
    pdf_binary = pdf.output(dest="S").encode("latin1")  # PDF must be encoded as latin1
    return io.BytesIO(pdf_binary)


# Streamlit UI
st.set_page_config(page_title="News Summarizer", layout="centered")
st.title("📰 Tóm tắt bài báo bằng ChatGPT")
st.caption("Dán link bài viết và nhận đoạn tóm tắt bằng tiếng Việt ✨")

st.divider()

# 🔗 URL input
url_input = st.text_area("🔗 Dán 1 hoặc nhiều link (mỗi dòng một link):")



# 🧠 Options
style_key = st.selectbox(
    "✍️ Chọn phong cách tóm tắt:",
    options=list(SUMMARY_STYLES.keys()),
    format_func=lambda k: SUMMARY_STYLES[k]["label"]
)

language = st.selectbox(
    "🌐 Chọn ngôn ngữ:",
    ["Tiếng Việt", "English"]
)

summary_length = st.selectbox(
    "📏 Chọn độ dài tóm tắt:",
    ["Ngắn gọn", "Vừa phải", "Chi tiết"]
)
st.divider()

# Sidebar 
with st.sidebar:
    st.header("📘 Giới thiệu")
    st.markdown("""
    Đây là ứng dụng demo tóm tắt bài báo bằng ChatGPT.
    
    - 📚 Dán một liên kết tin tức
    - ✍️ Chọn phong cách & ngôn ngữ
    - 📋 Sao chép hoặc tải tóm tắt

    ---
    🔗 [OpenAI](https://openai.com)  
    🔗 [Streamlit](https://streamlit.io)
    """)


if st.button("Tóm tắt"):
    if url_input.strip():
        urls = [line.strip() for line in url_input.strip().splitlines() if line.strip()]
        for i, url in enumerate(urls, 1):
            st.divider()
            st.markdown(f"🔗 **Link #{i}:** {url}")

            if not is_valid_url(url):
                st.warning("⚠️ Link không hợp lệ.")
                continue
            with st.spinner("⏳ Đang lấy nội dung..."):
                article = fetch_article_text(url)
            if not article:
                st.error("❌ Không thể lấy nội dung bài viết.")
                continue
            with st.spinner("🧠 Đang tóm tắt..."):
                summary = summarize_text(article[:4000], style_key, language, summary_length)
            if summary:
                st.success("✅ Tóm tắt:")
                from streamlit.components.v1 import html
                    
                # Render summary and copy button with JS
                html(f"""
                <div>
                    <label><strong>📄 Nội dung tóm tắt:</strong></label><br>
                    <textarea id="summary_text" rows="15" style="width:100%; font-size: 14px; padding: 8px;">{summary}</textarea><br><br>
                    <button onclick="copySummary()" style="padding: 8px 16px; font-size: 14px;">📋 Sao chép tóm tắt</button>
                </div>

                <script>
                function copySummary() {{
                    const summaryText = document.getElementById("summary_text");
                    summaryText.select();
                    document.execCommand("copy");
                    alert("📋 Đã sao chép nội dung tóm tắt!");
                }}
                </script>
                """, height=420)
                st.caption(f"📝 Độ dài tóm tắt: {len(summary)} ký tự")
                # Create a downloadable text file
                buffer = io.StringIO()
                buffer.write(summary)
                buffer.seek(0)

                file_name = f"tom_tat_bai_bao_{time.strftime('%Y%m%d_%H%M%S')}.txt"

                st.download_button(
                    label="⬇️ Tải xuống tóm tắt (.txt)",
                    data=summary,
                    file_name=file_name,
                    mime="text/plain"
                )
                pdf_file = create_summary_pdf(f"Tóm tắt - Link #{i}", summary)

                st.download_button(
                    label="⬇️ Tải xuống PDF",
                    data=pdf_file,
                    file_name=f"tom_tat_bai_bao_{i}.pdf",
                    mime="application/pdf"
                )

            else:
                st.error("❌ Không thể tạo tóm tắt.")
            
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
