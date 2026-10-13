
import base64
import json
import uuid
from datetime import date
from urllib.parse import quote

import requests
import streamlit as st

st.set_page_config(
    page_title="Lazy Developer",
    page_icon="💻",
    layout="centered",
)

# ---------- CONFIGURATION ----------

ADMIN_USERNAME = st.secrets.get("admin_username", "")
ADMIN_PASSWORD = st.secrets.get("admin_password", "")
GITHUB_TOKEN = st.secrets.get("github_token", "")
GITHUB_REPO = st.secrets.get(
    "github_repo", "Roopampanchal/lazy-developer"
)
GITHUB_BRANCH = st.secrets.get("github_branch", "main")
POSTS_PATH = st.secrets.get("posts_path", "posts.json")

ADMIN_CONFIGURED = all([
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    GITHUB_TOKEN,
])

CATEGORIES = [
    "React", "JavaScript", "Python",
    "AI/ML", "Career", "Other",
]

# ---------- GITHUB STORAGE ----------

def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_file_url():
    repo = quote(GITHUB_REPO, safe="/")
    path = quote(POSTS_PATH, safe="/")
    return f"https://api.github.com/repos/{repo}/contents/{path}"


def get_posts():
    """Return posts and current GitHub file SHA."""
    response = requests.get(
        github_file_url(),
        headers=github_headers(),
        params={"ref": GITHUB_BRANCH},
        timeout=15,
    )

    if response.status_code == 404:
        return [], None

    response.raise_for_status()
    file_data = response.json()

    content = base64.b64decode(
        file_data["content"]
    ).decode("utf-8")

    posts = json.loads(content)

    if not isinstance(posts, list):
        raise ValueError("posts.json must contain a JSON list.")

    return posts, file_data["sha"]


def save_posts(posts, commit_message):
    """Save posts to the configured GitHub branch."""
    # Retrieve the current SHA required by GitHub to update a file.
    _, sha = get_posts()

    content = json.dumps(
        posts, indent=2, ensure_ascii=False
    )
    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }

    if sha:
        payload["sha"] = sha

    response = requests.put(
        github_file_url(),
        headers=github_headers(),
        json=payload,
        timeout=20,
    )
    response.raise_for_status()


def show_storage_error(action, error):
    st.error(
        f"Unable to {action}. Your posts have not been "
        f"confirmed saved. Please try again. ({error})"
    )


# ---------- SESSION / AUTHENTICATION ----------

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "edit_post_id" not in st.session_state:
    st.session_state.edit_post_id = None


# ---------- HEADER ----------

st.title("💻 Lazy Developer")
st.caption("Learning. Building. One post at a time. ✨")
st.markdown("---")


# ---------- ADMIN LOGIN ----------

with st.sidebar:
    st.title("🔐 Admin")

    if st.session_state.is_admin:
        st.success("Logged in")

        if st.button("Log out", use_container_width=True):
            st.session_state.is_admin = False
            st.session_state.edit_post_id = None
            st.rerun()

    else:
        with st.form("admin_login"):
            username = st.text_input("Username")
            password = st.text_input(
                "Password", type="password"
            )
            login_clicked = st.form_submit_button(
                "Login", use_container_width=True
            )

        if login_clicked:
            if not ADMIN_CONFIGURED:
                st.error(
                    "Admin login is not configured. "
                    "Contact the site administrator."
                )
            elif (
                username == ADMIN_USERNAME
                and password == ADMIN_PASSWORD
            ):
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Invalid username or password.")


# ---------- LOAD POSTS ----------

if not GITHUB_TOKEN:
    st.error(
        "Post storage is not configured. "
        "Please configure GitHub Secrets."
    )
    st.stop()

try:
    posts, _ = get_posts()
except (
    requests.RequestException,
    ValueError,
    KeyError,
    json.JSONDecodeError,
) as error:
    st.error(
        "Unable to load posts from GitHub. "
        "Please check the repository, branch, token and posts.json."
    )
    st.stop()


# ---------- ADMIN DASHBOARD ----------

if st.session_state.is_admin:
    st.markdown("## ✍️ Admin Dashboard")

    create_tab, manage_tab = st.tabs([
        "➕ Create Post",
        "📝 Manage Posts",
    ])

    # ----- CREATE POST -----

    with create_tab:
        with st.form("create_post", clear_on_submit=True):
            title = st.text_input("Post title")

            category = st.selectbox(
                "Category", CATEGORIES
            )

            content = st.text_area(
                "Your learning notes", height=200
            )

            publish = st.form_submit_button(
                "Publish post 🚀"
            )

        if publish:
            if not title.strip() or not content.strip():
                st.warning("Enter both title and content.")
            else:
                new_post = {
                    "id": str(uuid.uuid4()),
                    "title": title.strip(),
                    "category": category,
                    "content": content.strip(),
                    "date": date.today().isoformat(),
                }

                try:
                    latest_posts, _ = get_posts()
                    latest_posts.insert(0, new_post)

                    save_posts(
                        latest_posts,
                        f"Add post: {new_post['title'][:60]}",
                    )
                    st.success("Post published successfully!")
                    st.rerun()

                except (
                    requests.RequestException,
                    ValueError,
                    KeyError,
                ) as error:
                    show_storage_error("publish post", error)

    # ----- EDIT AND DELETE -----

    with manage_tab:
        if not posts:
            st.info("No posts to manage yet.")
        else:
            # Add IDs to older posts created by the original app.
            # These are migrated when a post is next saved.
            normalized_posts = []
            for post in posts:
                normalized_posts.append({
                    **post,
                    "id": post.get("id") or str(uuid.uuid4()),
                })

            post_options = {
                f"{p.get('title', 'Untitled')} · "
                f"{p.get('date', '')} · {p['id'][:8]}": p["id"]
                for p in normalized_posts
            }

            selected_label = st.selectbox(
                "Choose a post to manage",
                list(post_options.keys()),
            )
            selected_id = post_options[selected_label]

            selected_post = next(
                p for p in normalized_posts
                if p["id"] == selected_id
            )

            with st.form("edit_post"):
                edit_title = st.text_input(
                    "Title",
                    value=selected_post.get("title", ""),
                )

                old_category = selected_post.get(
                    "category", "Other"
                )
                category_index = (
                    CATEGORIES.index(old_category)
                    if old_category in CATEGORIES
                    else CATEGORIES.index("Other")
                )

                edit_category = st.selectbox(
                    "Category",
                    CATEGORIES,
                    index=category_index,
                )

                edit_content = st.text_area(
                    "Content",
                    value=selected_post.get("content", ""),
                    height=200,
                )

                update = st.form_submit_button(
                    "Save changes"
                )

            if update:
                if not edit_title.strip() or not edit_content.strip():
                    st.warning("Title and content are required.")
                else:
                    try:
                        latest_posts, _ = get_posts()
                        found = False

                        for post in latest_posts:
                            if post.get("id") == selected_id:
                                post.update({
                                    "title": edit_title.strip(),
                                    "category": edit_category,
                                    "content": edit_content.strip(),
                                })
                                found = True
                                break

                        if not found:
                            st.error(
                                "This post has changed or was deleted. "
                                "Refresh and try again."
                            )
                        else:
                            # Preserve/migrate IDs for legacy posts.
                            for post in latest_posts:
                                if not post.get("id"):
                                    post["id"] = str(uuid.uuid4())

                            save_posts(
                                latest_posts,
                                f"Update post: {edit_title.strip()[:60]}",
                            )
                            st.success("Post updated!")
                            st.rerun()

                    except (
                        requests.RequestException,
                        ValueError,
                        KeyError,
                    ) as error:
                        show_storage_error("update post", error)

            st.markdown("---")
            st.warning(
                f"Delete post: {selected_post.get('title', 'Untitled')}"
            )

            confirm_delete = st.checkbox(
                "I understand this will permanently remove the post."
            )

            if st.button(
                "🗑️ Delete post",
                disabled=not confirm_delete,
            ):
                try:
                    latest_posts, _ = get_posts()
                    remaining_posts = [
                        p for p in latest_posts
                        if p.get("id") != selected_id
                    ]

                    if len(remaining_posts) == len(latest_posts):
                        st.error("Post not found. Refresh and retry.")
                    else:
                        save_posts(
                            remaining_posts,
                            f"Delete post: "
                            f"{selected_post.get('title', 'Untitled')[:60]}",
                        )
                        st.session_state.edit_post_id = None
                        st.success("Post deleted.")
                        st.rerun()

                except (
                    requests.RequestException,
                    ValueError,
                    KeyError,
                ) as error:
                    show_storage_error("delete post", error)


# ---------- PUBLIC JOURNAL (READ-ONLY) ----------

st.markdown("---")
st.subheader("📚 My Learning Journal")

if not posts:
    st.info("No posts published yet. Check back soon.")
else:
    for post in posts:
        with st.container(border=True):
            st.caption(
                f"{post.get('category', 'Other')} · "
                f"{post.get('date', '')}"
            )
            st.subheader(post.get("title", "Untitled"))
            st.markdown(post.get("content", ""))
