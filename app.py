import base64
import json
import requests
import streamlit as st

# ---------- PAGE CONFIG ----------

st.set_page_config(
    page_title="Lazy Developer | Learning Journal",
    page_icon="💻",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- GITHUB PUBLIC POSTS URL ----------

GITHUB_API_URL = (
    "https://api.github.com/repos/"
    "Roopampanchal/lazy-developer/contents/posts.json"
)


# ---------- LOAD POSTS (READ ONLY) ----------

@st.cache_data(ttl=10)
def load_posts():
    response = requests.get(
        GITHUB_API_URL,
        params={"ref": "main"},
        headers={
            "Accept": "application/vnd.github+json",
            "Cache-Control": "no-cache",
        },
        timeout=15,
    )
    response.raise_for_status()

    file_data = response.json()

    content = base64.b64decode(
        file_data["content"]
    ).decode("utf-8")

    posts = json.loads(content)

    if not isinstance(posts, list):
        raise ValueError(
            "posts.json must contain a list of posts."
        )

    return posts


# ---------- WEBSITE HEADER ----------

st.title("💻 Lazy Developer")

st.markdown(
    """
    ### Learning. Building. One post at a time. ✨

    A personal learning journal where I share my journey
    with **React, JavaScript, Python, AI/ML, and software development**.
    """
)

st.markdown("---")


# ---------- LEARNING JOURNAL ----------

st.subheader("📚 My Learning Journal")

try:
    posts = load_posts()

    # st.write("DEBUG — Posts loaded:", len(posts))

    # Newest dates first
    posts = sorted(
        posts,
        key=lambda post: post.get("date", ""),
        reverse=True,
    )

    if not posts:
        st.info("No posts yet. New learnings are coming soon! 🌱")

    else:
        categories = [
            "All",
            *sorted({
                post.get("category", "Other")
                for post in posts
            }),
        ]

        selected_category = st.selectbox(
            "Filter by category",
            categories,
        )

        if selected_category != "All":
            posts = [
                post for post in posts
                if post.get("category", "Other")
                == selected_category
            ]

        st.caption(f"{len(posts)} post(s)")

        for post in posts:
            with st.container(border=True):
                st.caption(
                    f"🏷️ {post.get('category', 'Other')} "
                    f"· 📅 {post.get('date', '')}"
                )

                st.subheader(
                    post.get("title", "Untitled")
                )

                st.markdown(
                    post.get("content", "")
                )

except requests.RequestException:
    st.error(
        "Unable to load posts right now. "
        "Please refresh the page and try again."
    )

except (ValueError, json.JSONDecodeError):
    st.error(
        "The posts data could not be read. "
        "Please check the posts.json file in the repository."
    )

# ---------- FOOTER ----------


st.markdown("---")

st.markdown(
    """
    <div style="
        text-align: center;
        padding: 18px 0 10px 0;
        font-family: sans-serif;
    ">
        <div style="
            font-size: 13px;
            letter-spacing: 2px;
            color: #8A94A6;
            margin-bottom: 10px;
        ">
            WORK SMARTER, NOT HARDER
        </div>

        <div style="
            font-size: 19px;
            font-weight: 600;
            letter-spacing: 0.5px;
            color: #5B8DEF;
        ">
            ♡ Lazy Developer
        </div>

        <div style="
            font-size: 11px;
            color: #9CA3AF;
            margin-top: 10px;
        ">
            made with curiosity & a little ☕
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
