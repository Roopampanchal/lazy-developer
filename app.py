import json
import requests
import streamlit as st
from datetime import date

# ---------- PAGE CONFIG ----------

st.set_page_config(
    page_title="Lazy Developer | Learning Journal",
    page_icon="💻",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- GITHUB PUBLIC POSTS URL ----------

POSTS_URL = (
    "https://raw.githubusercontent.com/"
    "Roopampanchal/lazy-developer/main/posts.json"
)


# ---------- LOAD POSTS (READ ONLY) ----------

def load_posts():
    response = requests.get(
        POSTS_URL,
        params={"refresh": str(date.today())},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


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
    <div style="text-align:center; color:gray;">
        Made with 💙 and Python · Lazy Developer
    </div>
    """,
    unsafe_allow_html=True,
)
