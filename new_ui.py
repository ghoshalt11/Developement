# Import python packages
import streamlit as st


# import 
# import mimetypes
# import numpy as np
from snowflake.snowpark.context import get_active_session

# python UDF function for retrieving recent user-bot conversations to have past context linked to current user prompt
def get_recent_context(chat_history, n=2):
    return chat_history[-n:] if len(chat_history) >= n else chat_history




st.markdown("""
    <style>
    div.stButton > button {
        background-color: #ffffff;
        color: #1a1a1a;
        font-weight: 600;
        font-size: 15px;
        padding: 0.75rem 1.5rem;
        border-radius: 18px;
        border: none;
        box-shadow: 
            0 4px 6px rgba(0, 0, 0, 0.1),
            0 1px 3px rgba(0, 0, 0, 0.08); /* ← Elevated button look */
        transition: all 0.2s ease-in-out;
    }

    div.stButton > button:hover {
        box-shadow: 
            0 6px 16px rgba(41, 181, 232, 0.25),
            0 3px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
        color: #007ACE;
    }

    div.stButton > button:active {
        transform: scale(0.98);
        box-shadow: 
            0 3px 6px rgba(0, 0, 0, 0.08),
            0 1px 2px rgba(0, 0, 0, 0.05);
    }
    </style>
""", unsafe_allow_html=True)



st.markdown(
    """
    <h2 style="
        background-image: linear-gradient(90deg, #007ace, #29B5E8, #5AC8FA);
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        text-align: center;
        margin-top: 10px;
    ">
    ❄️ How May I Assist You?
    </h2>
    """,
    unsafe_allow_html=True
)





st.markdown(
    """
    <div style="
        font-size: 23px;
        font-weight: 700;
        text-align: left;
        background-image: linear-gradient(90deg, #007ACE, #29B5E8, #66CCFF, #5AC8FA);
       /* background-image: linear-gradient(90deg,
  #007ACE,   /* darker blue */
  #29B5E8,   /* snowflake blue */
  #66CCFF,   /* lighter cyan */
  #A2DFFF,   /* pale blue */
  #29B5E8); */
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        color: transparent;
        margin-bottom: 4px;  /* Reduced gap */
        margin-top: -10px;   /* Optional lift-up if needed */
    ">
    Suggested quick actions :
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
# col_center = st.container()

with col1:
    st.button("➕ Create / Update Lead Info", key="lead_tile")

with col2:
    st.button("📞 Log Call / Meetings notes", key="log_tile")


st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
st.button("📈 Update Sales Pipeline", key="pipeline_tile")
st.markdown("</div>", unsafe_allow_html=True)
st.divider()

# To keep a sidebar menu chats
with st.sidebar:    
    if st.button("🗑 clear chat", help="Clear the chat history"):
        st.session_state.chat_history = []
    if st.button("💾 save chat"):
        chat_lines = []
        
        for entry in st.session_state.chat_history:
            role = "👤 User" if entry["role"] == "user" else "🤖 Bot"
            chat_lines.append(f"**{role}:** {entry['message']}")
        chat_md = "\n\n".join(chat_lines)
        
        # Write to file and trigger download
        st.download_button(
            label="Download",
            data=chat_md,
            file_name="sales_chat_history.txt",
            mime="text/plain"
        )
        
# Get the current active snowpark session/credentials
session = get_active_session()

# keeping chat session history logic
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  

# Display existing chat history 
for entry in st.session_state.chat_history:
    with st.chat_message(entry["role"], avatar="❄️" if entry["role"] == "ai" else None):
        st.markdown(entry["message"])

# Horizontal mini toolbar right above chat input



prompt = st.chat_input("Ask anything..")
# uploaded_image = st.file_uploader("📷 Upload Image (e.g., contact card, notes)", type=["png", "jpg", "jpeg"])
uploaded_file=None
# with st.container():
#     col1, col2   = st.columns([0.1, 0.1])

#     with col1:
#         if st.button("📎upload", key="upload_btn"):
#             st.session_state.show_upload = True
            
#             if st.session_state.show_upload:
                
                
uploaded_file = st.file_uploader(
                    "upload",type=["pdf", "png", "jpg", "jpeg", "wav"],accept_multiple_files=False
                        )
                # print(file_ext)
                # if uploaded_file.size>(25 *1024 *1024):
                    
if uploaded_file:
    
    st.write(f"📂 File Type: {uploaded_file.type}")
    st.write(f"📏 File Size: {uploaded_file.size} bytes")
    session = get_active_session()
    PutResult = session.file.put_stream(
    uploaded_file,
    "@CRM_SCHEMA_STAGE",
    auto_compress=False,
    overwrite=True
)
    if PutResult and PutResult.status in ["UPLOADED", "OVERWRITTEN"]:
        
        st.success(f"✅ File uploaded to stage: {PutResult.target}")
        st.json({
        "name": PutResult.target,
        "status": PutResult.status,
        "size": PutResult.source
    })
else:
    st.error("❌ Upload to stage failed.")
    # st.write(result[0])
    st.success(f"✅ File uploaded: ")
                    
    # with col2:
    #     if st.button("🎤 mic", key="mic_btn"):
    #         st.toast("🎙️ Voice input coming soon...")  # Placeholder

# logic to handle when user enters chat prompt
if prompt:
        
    with st.chat_message("user"):
        st.write(f"{prompt}")
        safe_prompt = prompt.replace("'", "''") # to remove any single quote issue entered by user
        st.session_state.chat_history.append({"role": "user", "message": prompt})

        recent_context = get_recent_context(st.session_state.chat_history, n=2)
        context_str = "\n".join([f"{entry['role']}: {entry['message']}" for entry in recent_context])

        # prompt engineering the LLM model 'snowflake-arctic' to reply user's contextual questions.
        
        model_response = session.sql(f"""
            SELECT snowflake.cortex.complete(
            'llama3-8b',$$
            You act as **SalesSense**, an AI-powered CRM assistant for sales reps.  
            Follow these rules strictly.
            ### CONTEXT
            {context_str}
            ### NEW INPUT
            "{safe_prompt}"
            ### RESPONSE RULES
            1. Respond naturally, clearly, and briefly — don't repeat the user’s message.
            2. Only greet if the input is a pure greeting ("hi", "hello").
            3. If User's input is unclear or incomplete, politely ask for **specific missing info** only (not a generic explanation).
            4. If User asks CRM-related data entry tasks/action (like update, insert, view), respond like:
             
             - ✅ Ask only what’s missing (according to below mentioned schema context given) and do not End with `[ACTION: SQL_GENERATION_REQUIRED]` unless it is clear enough to geerate SQL
             - ⛔ Don’t assume missing values or overexplain
             - Only End with `[ACTION: SQL_GENERATION_REQUIRED]` if input is clear enough to generate a respective SQL statement.
           

            ### DATABASE SCHEMA
            - leads(lead_id, name, region, score)
            - deals(deal_id, lead_id, status, close_date)
            Sample statuses: "Closed-Won", "Proposal", "Negotiation"

            Respond now:
            $$)""").collect()

        model_response = model_response[0][0] # Bot model's responses captured in variable model_response
        
        if '[ACTION: SQL_GENERATION_REQUIRED]' in model_response:
            generate_sql=True
        else:
            generate_sql=False
            
        model_response=model_response.replace("[ACTION: SQL_GENERATION_REQUIRED]", "").strip()
        
        cortex_response=model_response
        # generate_sql=True
        result_df=None

        if generate_sql: # if need to generate SQL then

            # Prompting model to generate SQL and execute
            sql_query_generated=session.sql(f"""
            SELECT snowflake.cortex.complete(
            'snowflake-arctic', 
            $$Act as an Snowflake SQL expert, convert this User's natural input prompt into a SQL statement.
            Note - When context is clear to you, then only give me the SQL statement to be executed as output.

             User's natural input prompt:
            "{safe_prompt}"
            
            CRM database schema context given below for for generating SQL :
            
            - leads(lead_id, name, region, score)
            - deals(deal_id, lead_id, status, close_date)  
            sample deal status data - 'Closed-Won', 'Closed-lost', 
            'Proposal' etc., This is just an example  $$)""").collect()[0][0]

            # st.session_state.chat_history.append({"role": "ai", "message": sql_query_generated})

            result_df=session.sql(f""" SELECT     
    concat(l.FIRST_NAME, ' ', 
    l.LAST_NAME) Lead_contact_name, 
    l.company,
    l.country, l.phone,
    d.OPPORTUNITY_NAME, 
    d.AMOUNT, 
    d.STAGE 
FROM 
    CRM_SAMPLE_DB.PUBLIC.LEADS l
JOIN 
    CRM_SAMPLE_DB.PUBLIC.DEALS d ON l.LEAD_ID = d.LEAD_ID
WHERE 
    l.STATUS = 'New' 
    AND d.STAGE = 'Prospecting' 
    AND d.PROBABILITY > 0.5 
ORDER BY 
    d.PROBABILITY DESC;""").to_pandas()
            
            cortex_response=cortex_response+' '+'sql generated:'+sql_query_generated
            
            
            


    # Chatbot relpying back to user response
    with st.chat_message("ai",avatar="❄️"):
        
        st.write(f"{cortex_response}")
        # st.line_chart(np.random.randn(30,3))
        if generate_sql:
            st.dataframe(result_df, use_container_width=True)
            st.markdown("""
<style>
    .element-container:has(.dataframe) {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

        st.session_state.chat_history.append({"role": "ai", "message": cortex_response})

     




