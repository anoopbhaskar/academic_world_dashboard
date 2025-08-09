import streamlit as st
from mysql_utils import (
    get_faculty_by_keywords, 
    get_all_universities, 
    get_all_keywords
)
from mongodb_utils import (
    get_all_universities as get_all_mongo_unis,
    get_faculty_by_university,
    get_all_faculty_names,
    get_faculty_by_name,
    get_publications_by_ids,
    save_to_favorites, 
    get_favorites, 
    get_faculty_by_id, 
    clear_favorites,
    remove_from_favorites,
    get_publication_counts_by_keyword,
    get_user_interests,
    save_user_interests
)
from neo4j_utils import (
    get_keyword_faculty_network, 
    get_all_neo4j_keywords
)
from streamlit_agraph import agraph, Node, Edge, Config
import datetime
import matplotlib.pyplot as plt


if "user" not in st.session_state:
    with st.form("login_form"):
        st.title("Welcome to Academic World Explorer! ")
        st.markdown("Please enter your information to continue.")
        fname = st.text_input("First Name")
        lname = st.text_input("Last Name")
        email = st.text_input("Email")

        submitted = st.form_submit_button("Enter")
        if submitted and fname and lname and email:
            st.session_state["user"] = {
                "name": f"{fname} {lname}",
                "email": email
            }
            clear_favorites(email)
            st.rerun()

    st.stop()

user = st.session_state["user"]


st.sidebar.success(f"Welcome, {user['name']}!")
st.sidebar.markdown(f" Email: [{user['email']}](mailto:{user['email']})")


interests = get_user_interests(user)
if interests:
    st.sidebar.markdown(" **Research Interests:**")
    for interest in interests:
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            st.write(f"- {interest}")
        with col2:
            if st.button("X", key=f"remove_interest_{interest}"):
                updated = [i for i in interests if i != interest]
                save_user_interests(user, updated)
                st.rerun()


favorites = get_favorites(user["email"])
if favorites:
    st.sidebar.markdown(" **Favorites:**")
    for fav in favorites:
        prof = get_faculty_by_id(fav["faculty_id"])
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            st.markdown(f"- {prof['name']}")
        with col2:
            if st.button("X", key=f"remove_fav_{prof['id']}"):
                remove_from_favorites(user["email"], prof["id"])
                st.rerun()



st.title(" Faculty Search by Keywords")

all_keywords = get_all_keywords()
saved_interests = get_user_interests(user)

keywords = st.multiselect(
    "Select Keywords",
    options=all_keywords,
    default=saved_interests,
    placeholder="Search or type a keyword...",
)

if st.button(" Save Interests to My Profile"):
    save_user_interests(user, keywords)
    st.success("Interests saved to your profile!")
    st.rerun()

universities = get_all_universities()
selected_uni = st.selectbox("Filter by University (optional)", ["All"] + universities)

if keywords:
    uni_filter = None if selected_uni == "All" else selected_uni
    results = get_faculty_by_keywords(keywords, university_filter=uni_filter)

    for name, position, faculty_photo, email, uni_name, uni_logo in results:
        col1, col2, col3 = st.columns([1, 5, 1])
        with col1:
            st.image(faculty_photo or "images/default_faculty.png", width=80)
        with col2:
            st.markdown(f"### {name}")
            st.markdown(f"**{position or 'Unknown Position'}** at *{uni_name}*")
            st.markdown(f"[Email](mailto:{email})" if email else " Email: N/A")
        with col3:
            st.image(uni_logo or "images/default_uni.png", width=60)
        st.markdown("---")



st.title(" Faculty Profile Viewer")

mongo_unis = get_all_mongo_unis()
selected_univ = st.selectbox("Filter by University", ["Select..."] + mongo_unis)

if selected_univ == "All":
    faculty_names = get_all_faculty_names()
else:
    faculty_names = [f["name"] for f in get_faculty_by_university(selected_univ)]

selected_name = st.selectbox("Select Faculty", faculty_names, index=None, placeholder="Choose...")

if selected_name:
    profile = get_faculty_by_name(selected_name)
    if profile:
        col1, col2 = st.columns([1, 5])
        with col1:
            st.image(profile.get("photoUrl") or "https://via.placeholder.com/100", width=100)
        with col2:
            st.markdown(f"### {profile['name']}")
            st.markdown(f"**{profile.get('position', 'Unknown Position')}**")
            st.markdown(f"*{profile['affiliation']['name']}*")

        if st.button(" Save to My Favorites"):
            save_to_favorites(user["email"], profile["id"])
            st.success("Saved to favorites!")
            st.rerun()

        st.image(profile["affiliation"].get("photoUrl") or "https://via.placeholder.com/80", width=80)

        st.markdown("### Top Publications")
        pub_ids = profile.get("publications", [])
        if pub_ids:
            pubs = get_publications_by_ids(pub_ids, limit=5)
            for pub in pubs:
                st.markdown(
                    f"- **{pub['title']}** "
                    f"({pub.get('venue', 'Unknown Venue')}, {pub.get('year', 'N/A')}) "
                    f"— *{pub.get('numCitations', 0)} citations*"
                )
        else:
            st.markdown("No publications found.")



st.title(" Research Network Graph")

graph_keyword = st.selectbox("Choose a keyword to explore", get_all_neo4j_keywords())

if graph_keyword:
    network_data = get_keyword_faculty_network(graph_keyword)
    nodes = []
    edges = []
    seen = set()

    nodes.append(Node(id=graph_keyword, label=graph_keyword, shape="ellipse", color="red"))

    for entry in network_data:
        faculty = entry["faculty"]
        co_keywords = entry["co_keywords"]

        if faculty not in seen:
            nodes.append(Node(id=faculty, label=faculty, shape="box", color="lightblue"))
            edges.append(Edge(source=faculty, target=graph_keyword))
            seen.add(faculty)

        for co_kw in co_keywords:
            if co_kw not in seen:
                nodes.append(Node(id=co_kw, label=co_kw, shape="ellipse", color="lightgreen"))
                seen.add(co_kw)
            edges.append(Edge(source=faculty, target=co_kw))

    config = Config(width=800, height=600, directed=True, physics=True)
    agraph(nodes=nodes, edges=edges, config=config)



st.markdown("##  Keyword Publication Trend (Past 15 Years)")

keyword_options = get_all_keywords()
selected_chart_keyword = st.selectbox("Choose a keyword", keyword_options, index=None, placeholder="Select...")

if selected_chart_keyword:
    current_year = datetime.datetime.now().year
    start_year = current_year - 15
    counts, years = get_publication_counts_by_keyword(selected_chart_keyword, start_year)

    st.subheader(f"Number of Publications per Year for '{selected_chart_keyword}'")

    fig, ax = plt.subplots()
    ax.plot(years, counts, marker='o')
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Publications")
    ax.set_title(f"Publications mentioning '{selected_chart_keyword}' (Last 15 years)")
    st.pyplot(fig)
