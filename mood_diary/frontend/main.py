import streamlit as st
import altair as alt
import pandas as pd
import datetime
import random
import requests

st.markdown("""
<style>
.mood-banner {
    background: linear-gradient(90deg, #1e3b29, #2c4a3a);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}
</style>
<div class="mood-banner">
    <h2>How do you feel, #REPLACE WITH USER NAME#</h2>
    <p>Please, mark your mood today</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def get_user_ratings_data():
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    ratings = []
    
    for i in range(len(dates)):
        if random.random() > 0.8:
            continue
            
        rating = random.randint(1, 10)
        ratings.append({
            "date": dates[i],
            "rating": rating,
            "comment": f"User comment for rating {rating}"
        })
    
    df = pd.DataFrame(ratings)
    return df

if 'user_ratings_df' not in st.session_state:
    st.session_state.user_ratings_df = get_user_ratings_data()

if not st.session_state.user_ratings_df.empty:
    user_ratings = st.session_state.user_ratings_df
    
    hover = alt.selection_point(
        fields=["date"],
        nearest=True,
        on="mouseover",
        empty="none",
    )
    
    color_scale = alt.Scale(
        domain=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        range=['#ef4056', '#f47d2f', '#f8c13a', '#c0d23e', '#8dc63f', 
               '#53a78c', '#3e83c3', '#5465b3', '#6247aa', '#4a357f']
    )
    
    base = alt.Chart(user_ratings).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('rating:Q', title='Mood Rating', scale=alt.Scale(domain=[0, 11])),
        color=alt.Color('rating:Q', scale=color_scale, legend=None)
    )
    
    line = base.mark_line(interpolate='monotone', strokeWidth=3).encode(
        color=alt.value("#888888")  # Use a neutral color for the line
    )
    
    points = base.mark_circle(size=100).encode(
        opacity=alt.value(1)
    )
    
    tooltipped_points = points.encode(
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('rating:Q', title='Rating'),
            alt.Tooltip('comment:N', title='Comment')
        ]
    )
    
    highlight_points = base.mark_circle(size=120).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )
    
    rule = alt.Chart(user_ratings).mark_rule(color='gray').encode(
        x='date:T',
    ).transform_filter(hover)
    
    chart = (line + tooltipped_points + highlight_points + rule).add_params(hover)
    
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No mood ratings data available yet. Start tracking your mood below!")

if 'comments' not in st.session_state:
    st.session_state.comments = []

if 'selected_rating' not in st.session_state:
    st.session_state.selected_rating = None

with st.form(key="comment_form", clear_on_submit=True, enter_to_submit=False):
    comment = st.text_area("", placeholder="Type your thoughts here...", label_visibility="collapsed", height=100)
    
    if st.session_state.get('rating_required', False):
        st.markdown("<p class='rating-required'>Please select a rating</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns(10)
    
    with col10:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("10")) {
            background-color: #4a357f;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        ten = st.form_submit_button("10", 
                      help="Rating 10",
                      use_container_width=True)
    with col9:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("9")) {
            background-color: #6247aa;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        nine = st.form_submit_button("9", 
                       help="Rating 9",
                       use_container_width=True)
    with col8:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("8")) {
            background-color: #5465b3;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        eight = st.form_submit_button("8", 
                        help="Rating 8",
                        use_container_width=True)
    with col7:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("7")) {
            background-color: #3e83c3;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        seven = st.form_submit_button("7", 
                        help="Rating 7",
                        use_container_width=True)
    with col6:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("6")) {
            background-color: #53a78c;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        six = st.form_submit_button("6", 
                      help="Rating 6",
                      use_container_width=True)
    with col5:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("5")) {
            background-color: #8dc63f;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        five = st.form_submit_button("5", 
                       help="Rating 5",
                       use_container_width=True)
    with col4:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("4")) {
            background-color: #c0d23e;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        four = st.form_submit_button("4", 
                       help="Rating 4",
                       use_container_width=True)
    with col3:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("3")) {
            background-color: #f8c13a;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        three = st.form_submit_button("3", 
                        help="Rating 3",
                        use_container_width=True)
    with col2:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("2")) {
            background-color: #f47d2f;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        two = st.form_submit_button("2", 
                      help="Rating 2",
                      use_container_width=True)
    with col1:
        st.markdown("""
        <style>
        [data-testid="stButton"] button:has(div:contains("1")) {
            background-color: #ef4056;
            color: white;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        one = st.form_submit_button("1", 
                      help="Rating 1",
                      use_container_width=True)
    
    rating = None
    if one:
        rating = 1
    elif two:
        rating = 2
    elif three:
        rating = 3
    elif four:
        rating = 4
    elif five:
        rating = 5
    elif six:
        rating = 6
    elif seven:
        rating = 7
    elif eight:
        rating = 8
    elif nine:
        rating = 9
    elif ten:
        rating = 10
    
    form_submitted = one or two or three or four or five or six or seven or eight or nine or ten
    
    if form_submitted:
        if comment and rating is not None:
            st.session_state.comments.append({"text": comment, "rating": rating})
            
            new_rating = pd.DataFrame([{
                "date": datetime.datetime.now(),
                "rating": rating,
                "comment": comment
            }])
            
            st.session_state.user_ratings_df = pd.concat([st.session_state.user_ratings_df, new_rating], ignore_index=True)
            
            st.success(f"Comment added with rating: {rating}")
            st.session_state.rating_required = False
            st.rerun()
        elif comment:
            st.session_state.rating_required = True
        elif rating is not None:
            st.warning("Please enter a comment")
st.markdown("</div>", unsafe_allow_html=True)