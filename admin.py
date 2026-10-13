
import base64
import json
import uuid
from datetime import date
from urllib.parse import quote

import requests
import streamlit as st

# ---------- PAGE CONFIG ----------

st.set_page_config(
    page_title="Lazy Developer | Admin",
    page_icon="🔐",
    layout="centered",
)

# ---------- SECRETS ----------

ADMIN_USERNAME = st.secrets.get("admin_username", "")
ADMIN_PASSWORD = st.secrets.get("admin_password", "")
GITHUB_TOKEN = st.secrets.get("github_token", "")
GITHUB_REPO = st.secrets.get(
    "github_repo", "Roopampanchal/lazy-developer"
)
GITHUB_BRANCH = st.secrets.get("github_branch", "main")
POSTS_PATH = st.secrets.get("posts_path", "posts.json")

CATEGORIES = [
    "React",
    "JavaScript",
    "Python",
    "AI/ML",
    "Career",
    "Other",
]

CONFIGURED = bool(
    ADMIN_USERNAME and ADMIN_PASSWORD and GITHUB_TOKEN
)


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
    return (
        f"https://api.github.com/repos/"
        f"{repo}/contents/{path}"
    )


def get_posts():
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

    raw_content = base64.b64decode(
        file_data["content"]
    ).decode("utf-8")

    posts = json.loads(raw_content)

    if not isinstance(posts, list):
        raise ValueError("posts.json must contain a JSON list.")

    return posts, file_data["sha"]


def save_posts(posts, message):
    # Fetch the latest file SHA before updating GitHub.
    _, sha = get_posts()

    content = json.dumps(
        posts,
        indent=2,
        ensure_ascii=False,
    )

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": message,
        "content": encoded_content,
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


def report_error(action, error):
    st.error(
        f"Could not {action}. Please try again. "
        f"Details: {error}"
    )


# ---------- SESSION STATE ----------

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if "editing_post_id" not in st.session_state:
    st.session_state.editing_post_id = None


# ---------- LOGIN PAGE ----------

if not st.session_state.admin_authenticated:
    st.title("🔐 Lazy Developer")
    st.subheader("Admin Login")
    st.caption("Authorized administrators only.")

    if not CONFIGURED:
        st.error(
            "Admin configuration is incomplete. "
            "Please configure Streamlit Secrets."
        )
        st.stop()

    with st.form("admin_login"):
        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password",
        )

        login_clicked = st.form_submit_button(
            "Login",
            use_container_width=True,
        )

    if login_clicked:
        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.stop()


# ---------- ADMIN DASHBOARD ----------

st.title("💻 Lazy Developer")
st.subheader("Admin Dashboard")
st.caption("Create, update, and manage your learning posts.")

if st.button("Log out"):
    st.session_state.admin_authenticated = False
    st.session_state.editing_post_id = None
    st.rerun()

if not CONFIGURED:
    st.error("Admin configuration is incomplete.")
    st.stop()

try:
    posts, _ = get_posts()
except (
    requests.RequestException,
    ValueError,
    KeyError,
    json.JSONDecodeError,
) as error:
    report_error("load posts from GitHub", error)
    st.stop()

# Give older posts unique IDs and persist the migration.
needs_migration = any(not p.get("id") for p in posts)

if needs_migration:
    for post in posts:
        if not post.get("id"):
            post["id"] = str(uuid.uuid4())

    try:
        save_posts(posts, "Add IDs to existing blog posts")
    except (
        requests.RequestException,
        ValueError,
        KeyError,
    ) as error:
        report_error("migrate existing posts", error)
        st.stop()

st.markdown("---")

create_tab, manage_tab = st.tabs([
    "➕ Create Post",
    "📝 Edit / Delete Posts",
])


# ---------- CREATE POST ----------

with create_tab:
    st.subheader("Publish a new post")

    with st.form("create_post", clear_on_submit=True):
        title = st.text_input("Post title")

        category = st.selectbox(
            "Category",
            CATEGORIES,
        )

        content = st.text_area(
            "Your learning notes",
            height=220,
            placeholder="What did you learn today?",
        )

        publish = st.form_submit_button(
            "Publish Post 🚀",
            use_container_width=True,
        )

    if publish:
        if not title.strip() or not content.strip():
            st.warning("Please enter both title and content.")
        else:
            try:
                latest_posts, _ = get_posts()

                new_post = {
                    "id": str(uuid.uuid4()),
                    "title": title.strip(),
                    "category": category,
                    "content": content.strip(),
                    "date": date.today().isoformat(),
                }

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
                report_error("publish post", error)


# ---------- EDIT / DELETE POSTS ----------

with manage_tab:
    st.subheader("Manage published posts")

    if not posts:
        st.info("No posts published yet.")
    else:
        post_labels = {
            (
                f"{post.get('title', 'Untitled')} · "
                f"{post.get('date', '')} · {post['id'][:8]}"
            ): post["id"]
            for post in posts
        }

        selected_label = st.selectbox(
            "Select a post",
            list(post_labels.keys()),
        )

        selected_id = post_labels[selected_label]

        selected_post = next(
            post for post in posts
            if post["id"] == selected_id
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
                height=220,
            )

            update_clicked = st.form_submit_button(
                "Save Changes",
                use_container_width=True,
            )

        if update_clicked:
            if not edit_title.strip() or not edit_content.strip():
                st.warning("Title and content are required.")
            else:
                try:
                    latest_posts, _ = get_posts()

                    matching_post = next(
                        (
                            post for post in latest_posts
                            if post.get("id") == selected_id
                        ),
                        None,
                    )

                    if matching_post is None:
                        st.error(
                            "This post no longer exists. "
                            "Refresh and select another post."
                        )
                    else:
                        matching_post.update({
                            "title": edit_title.strip(),
                            "category": edit_category,
                            "content": edit_content.strip(),
                        })

                        save_posts(
                            latest_posts,
                            f"Update post: {edit_title.strip()[:60]}",
                        )

                        st.success("Post updated successfully!")
                        st.rerun()

                except (
                    requests.RequestException,
                    ValueError,
                    KeyError,
                ) as error:
                    report_error("update post", error)

        st.markdown("---")
        st.warning(
            f"Selected post: {selected_post.get('title', 'Untitled')}"
        )

        confirm_delete = st.checkbox(
            "I confirm that I want to permanently delete this post."
        )

        if st.button(
            "🗑️ Delete Post",
            disabled=not confirm_delete,
            use_container_width=True,
        ):
            try:
                latest_posts, _ = get_posts()

                remaining_posts = [
                    post for post in latest_posts
                    if post.get("id") != selected_id
                ]

                if len(remaining_posts) == len(latest_posts):
                    st.error(
                        "Post not found. Refresh and try again."
                    )
                else:
                    save_posts(
                        remaining_posts,
                        "Delete blog post",
                    )

                    st.success("Post deleted successfully!")
                    st.rerun()

            except (
                requests.RequestException,
                ValueError,
                KeyError,
            ) as error:
                report_error("delete post", error)


st.markdown("---")
st.caption("Lazy Developer · Admin Panel")
