import streamlit as st
from mysql_utils import (
    get_faculty_by_keywords, 
    get_all_universities, 
    get_all_keywords
)
from mongodb_utils import (
    get_all_universities,
    get_faculty_by_university,
    get_all_faculty_names,
    get_faculty_by_name,
    get_publications_by_ids,
    save_to_favorites, 
    get_favorites, 
    get_faculty_by_id, 
    clear_favorites,
    remove_from_favorites
)
from neo4j_utils import (
    get_keyword_faculty_network, 
    get_all_neo4j_keywords
)

from streamlit_agraph import (
    agraph, 
    Node, 
    Edge, 
    Config
)

user = "demo_user"
clear_favorites(user)  

st.set_page_config(page_title="Faculty Search", layout="wide")
st.title("Faculty Search by Keywords")
 


all_keywords = get_all_keywords()

keywords = st.multiselect(
    "Select Keywords",
    options=all_keywords,
    placeholder="Search or type a keyword...",
)

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
            if email:
                st.markdown(f" [Email](mailto:{email})")
            else:
                st.markdown(" Email: N/A")

        with col3:
            st.image(uni_logo or "images/default_uni.png", width=60)

        st.markdown("---")


st.set_page_config(page_title="Faculty Profile Viewer", layout="wide")
st.title("Faculty Profile Viewer")

universities = get_all_universities()
selected_univ = st.selectbox("Filter by University", ["Select..."] + universities)


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

        if st.button("Save to My Favorites"):
            save_to_favorites(user, profile["id"])
            st.success("Saved to favorites!")

        
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


st.set_page_config(page_title="My Favorite Faculty", layout="wide")
st.title("My Favorite Faculty")
favorites = get_favorites(user)

if not favorites:
    st.write("You haven't saved any faculty yet.")
else:
    for fav in favorites:
        prof = get_faculty_by_id(fav["faculty_id"])
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"- **{prof['name']}** ({prof['affiliation']['name']})")
        with col2:
            if st.button(f"Remove", key=f"remove_{prof['id']}"):
                from mongodb_utils import remove_from_favorites
                remove_from_favorites(user, prof["id"])
                st.experimental_rerun()



from neo4j_utils import get_keyword_faculty_network, get_all_neo4j_keywords
from streamlit_agraph import agraph, Node, Edge, Config

st.markdown("## Research Network Graph")

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



