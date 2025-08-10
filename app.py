import streamlit as st
from mysql_utils import (
    get_faculty_by_keywords, 
    get_all_universities, 
    get_all_keywords,
    get_university_pub_counts_by_keyword
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

@st.cache_data(show_spinner="Ranking universities...")
def cached_get_university_pub_counts_by_keyword(keyword):
    return get_university_pub_counts_by_keyword(keyword)


if "user" not in st.session_state:
    with st.form("login_form"):
        st.title("Welcome to the Academic World Journey Explorer! ")
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
            if st.button("X", key=f"remove_interest_{interest}", help="Remove interest"):
                updated = [i for i in interests if i != interest]
                save_user_interests(user, updated)
                st.rerun()


favorites = get_favorites(user["email"])
if favorites:
    st.sidebar.markdown(" **Favorites:**")
    for fav in favorites:
        try:
            prof = get_faculty_by_id(fav["faculty_id"])
            if prof: 
                col1, col2 = st.sidebar.columns([4, 1])
                with col1:
                    st.markdown(f"- {prof['name']}")
                with col2:
                    if st.button("X", key=f"remove_fav_{prof['id']}", help="Remove favorite"):
                        remove_from_favorites(user["email"], prof["id"])
                        st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error loading favorite: {e}")


st.markdown("##  Keyword Publication Trend (Past 15 Years)")

try:
    keyword_options = get_all_keywords()
    if not keyword_options:
        st.error("No keywords found. Please check your database connection.")
        st.stop()
except Exception as e:
    st.error(f"Error loading keywords: {e}")
    st.stop()

selected_chart_keyword = st.selectbox("Choose a keyword", keyword_options, index=None, placeholder="Select...")

if selected_chart_keyword:
    try:
        current_year = datetime.datetime.now().year
        start_year = current_year - 15
        counts, years = get_publication_counts_by_keyword(selected_chart_keyword, start_year)
        
        if counts and years:
            st.subheader(f"Number of Publications per Year for '{selected_chart_keyword}'")
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(years, counts, marker='o', linewidth=2, markersize=6)
            ax.set_xlabel("Year")
            ax.set_ylabel("Number of Publications")
            ax.set_title(f"Publications mentioning '{selected_chart_keyword}' (Last 15 years)")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
        else:
            st.warning(f"No publication data found for '{selected_chart_keyword}'")
    except Exception as e:
        st.error(f"Error generating publication chart: {e}")


if selected_chart_keyword:
    if st.button(" Save Interest to My Profile"):
        try:
            current_interests = get_user_interests(user) or []
            
            if selected_chart_keyword not in current_interests:
                current_interests.append(selected_chart_keyword)
                save_user_interests(user, current_interests)
                st.success(f"✅ '{selected_chart_keyword}' added to your interests!")
                st.rerun()
            else:
                st.info(f"'{selected_chart_keyword}' is already in your interests.")
                
        except Exception as e:
            st.error(f"Error saving interests: {e}")


if selected_chart_keyword:
    st.subheader(" University Publication Rankings by Keyword")

    try:
        if selected_chart_keyword:
            results = cached_get_university_pub_counts_by_keyword(selected_chart_keyword)

            if results:
                universities = [row[0] for row in results]
                publications = [row[1] for row in results]

                st.subheader(f"Top Universities for '{selected_chart_keyword}'")

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.barh(universities, publications, color='skyblue')
                ax.set_xlabel("Total Publications")
                ax.set_ylabel("University")
                ax.set_title(f"University Rankings by Publication Count for '{selected_chart_keyword}'")
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info(f"No publications found for the keyword '{selected_chart_keyword}'.")
    except Exception as e:
        st.error(f"Error loading university data: {e}")


if selected_chart_keyword:
    st.subheader(f"Top 10 Faculty for '{selected_chart_keyword}'")
    
    try:
        results = get_faculty_by_keywords([selected_chart_keyword])
        
        if not results:
            st.warning(f"No faculty found for keyword '{selected_chart_keyword}'")
        else:
            if 'viewed_profiles' not in st.session_state:
                st.session_state.viewed_profiles = set()
            
            for i, (name, position, faculty_photo, email, uni_name, uni_logo) in enumerate(results):
                faculty_key = f"{name}_{uni_name}_{i}"
                
                with st.container():
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
                    
                    btn_col1, btn_col2 = st.columns([1, 1])
                    
                    with btn_col1:
                        if st.button(" View Profile", key=f"view_profile_{faculty_key}"):
                            if faculty_key in st.session_state.viewed_profiles:
                                st.session_state.viewed_profiles.remove(faculty_key)
                            else:
                                st.session_state.viewed_profiles.add(faculty_key)
                            st.rerun()
                    
                    if faculty_key in st.session_state.viewed_profiles:
                        try:
                            profile = get_faculty_by_name(name)
                            if profile:
                                st.markdown("---")
                                st.markdown("###  Faculty Profile")
                                
                                profile_col1, profile_col2 = st.columns([1, 3])
                                with profile_col1:
                                    st.image(profile.get("photoUrl") or "https://via.placeholder.com/100", width=100)
                                
                                with profile_col2:
                                    st.markdown(f"**{profile['name']}**")
                                    st.markdown(f"Position: {profile.get('position', 'Unknown Position')}")
                                    if 'affiliation' in profile and profile['affiliation']:
                                        st.markdown(f"University: {profile['affiliation']['name']}")
                                
                                fav_button_key = f"save_fav_{profile['id']}_{faculty_key}"
                                
                                current_favorites = get_favorites(user["email"])
                                is_already_favorite = any(fav.get("faculty_id") == profile["id"] for fav in current_favorites)
                                
                                if is_already_favorite:
                                    st.success(" Already in favorites!")
                                else:
                                    if st.button(" Save to My Favorites", key=fav_button_key):
                                        try:
                                            save_to_favorites(user["email"], profile["id"])
                                            st.success("✅ Successfully saved to favorites!")
                                            import time
                                            time.sleep(0.5)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f" Error saving to favorites: {e}")
                                            st.write(f"Debug - User email: {user['email']}")
                                            st.write(f"Debug - Faculty ID: {profile['id']}")
                                st.markdown("###  Top Publications")
                                pub_ids = profile.get("publications", [])
                                if pub_ids:
                                    try:
                                        pubs = get_publications_by_ids(pub_ids, limit=5)
                                        if pubs:
                                            for pub in pubs:
                                                st.markdown(
                                                    f"- **{pub.get('title', 'Unknown Title')}** "
                                                    f"({pub.get('venue', 'Unknown Venue')}, {pub.get('year', 'N/A')}) "
                                                    f"— *{pub.get('numCitations', 0)} citations*"
                                                )
                                        else:
                                            st.markdown("No publications found.")
                                    except Exception as e:
                                        st.error(f"Error loading publications: {e}")
                                else:
                                    st.markdown("No publications found.")
                                    
                                st.markdown("---")
                            else:
                                st.error(" Faculty profile not found.")
                        except Exception as e:
                            st.error(f" Error loading faculty profile: {e}")
                            st.write(f"Debug - Trying to load profile for: {name}")
                    
                    st.markdown("---")
                    
    except Exception as e:
        st.error(f"Error loading faculty data: {e}")

if selected_chart_keyword:
    st.markdown("##  Research Network Graph")
    
    try:
        network_data = get_keyword_faculty_network(selected_chart_keyword)
        
        if network_data:
            nodes = []
            edges = []
            seen = set()

            nodes.append(Node(id=selected_chart_keyword, label=selected_chart_keyword, shape="ellipse", color="red"))

            for entry in network_data:
                faculty = entry["faculty"]
                co_keywords = entry["co_keywords"]

                if faculty not in seen:
                    nodes.append(Node(id=faculty, label=faculty, shape="box", color="lightblue"))
                    edges.append(Edge(source=faculty, target=selected_chart_keyword))
                    seen.add(faculty)

                for co_kw in co_keywords:
                    if co_kw not in seen:
                        nodes.append(Node(id=co_kw, label=co_kw, shape="ellipse", color="lightgreen"))
                        seen.add(co_kw)
                    edges.append(Edge(source=faculty, target=co_kw))

            config = Config(width=800, height=600, directed=True, physics=True)
            agraph(nodes=nodes, edges=edges, config=config)
        else:
            st.warning(f"No network data found for '{selected_chart_keyword}'")
            
    except Exception as e:
        st.error(f"Error generating network graph: {e}")
