import streamlit as st
import json
from pathlib import Path
from datetime import date
st.set_page_config(
    page_title="Lazy Developer",
    page_icon="💻",
    layout="centered"
)

POSTS_FILE = Path("posts.json")

def load_posts():
    if POSTS_FILE.exists():
        return json.loads(POSTS_FILE.read_text(encoding="utf-8"))
    return []

def save_posts(posts):
    POSTS_FILE.write_text(
        json.dumps(posts, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
st.title("💻 Lazy Developer")
st.caption("Learning. Building. One post at a time. ✨")
st.markdown("---")

with st.form("new_post", clear_on_submit=True):
    st.subheader("✍️ Share what you learned today")

    title = st.text_input("Post title")
    category = st.selectbox(
        "Category",
        ["React", "JavaScript", "Python", "AI/ML", "Career", "Other"]
    )
    content = st.text_area("Your learning notes", height=180)

    publish = st.form_submit_button("Publish post 🚀")
if publish:
    if title.strip() and content.strip():
        posts = load_posts()

        posts.insert(0, {
            "title": title.strip(),
            "category": category,
            "content": content.strip(),
            "date": date.today().isoformat()
        })

        save_posts(posts)
        st.success("Your post has been published!")
        st.rerun()
    else:
        st.warning("Please enter both a title and content.")

st.markdown("---")
st.subheader("📚 My Learning Journal")

posts = load_posts()

if not posts:
    st.info("No posts yet. Publish your first learning today!")
else:
    for post in posts:
        with st.container(border=True):
            st.caption(
                f"{post['category']} · {post['date']}"
            )
            st.subheader(post["title"])
            st.write(post["content"])
