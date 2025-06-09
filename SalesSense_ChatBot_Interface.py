# Import python packages
import streamlit as st
from snowflake.snowpark.context import get_active_session

# python UDF function for retrieving recent user-bot conversations to have past context linked to current user prompt
def get_recent_context(chat_history, n=2):
    return chat_history[-n:] if len(chat_history) >= n else chat_history

# ChatBot Title
st.title("❄️SalesSense",help="Next-gen AI-powered CRM assistant developed by SnowPals.")

# To keep a sidebar menu for -Clear chat history & save & download session chats
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

prompt = st.chat_input("Ask anything..")

# logic to handle when user enters chat prompt
if prompt:
        
    with st.chat_message("user"):
        st.write(f"{prompt}")
        safe_prompt = prompt.replace("'", "''")    #this line of code is for to remove any single quote issue entered by user
        st.session_state.chat_history.append({"role": "user", "message": prompt})

        recent_context = get_recent_context(st.session_state.chat_history, n=2)
        context_str = "\n".join([f"{entry['role']}: {entry['message']}" for entry in recent_context])

        # prompt engineering the LLM model to reply user's contextual questions.
        # Model - 'snowflake-arctic'
        model_response = session.sql(f"""
            SELECT snowflake.cortex.complete(
            'snowflake-arctic',$$ You are SalesSense, a friendly AI-powered CRM assistant.

            Recent conversation happend with you and user last:
            {context_str}

            User's latest message:
            "{safe_prompt}"

            Carefully follow these guidelines when replying:

            1. If the user has provided specific CRM-related details (e.g., lead name, contact, email, phone number, location),
            acknowledge the received details explicitly in short summarized way and confirm you are on it to udpate them. 
            Avoid asking again for the same details but no need to start with Hello! repeatedly,
            and at the end of your message, append: [ACTION: SQL_GENERATION_REQUIRED]

            2. If any provided information is unclear or incomplete, politely request just the missing or unclear details.

            3. For casual greetings or non-CRM tasks, reply naturally and concisely.
            4. Only greet (like "Hey" "Hello" or "Hi") if this is the very first interaction (hint : check from given past context {context_str} )or if the user explicitly greets you first.

            Respond now clearly and explicitly based on the above:
            $$)""").collect()

        model_response = model_response[0][0] # Bot model's responses captured in variable model_response
        
        if '[ACTION: SQL_GENERATION_REQUIRED]' in model_response:
            generate_sql=True
        else:
            generate_sql=False
            
        model_response=model_response.replace("[ACTION: SQL_GENERATION_REQUIRED]", "").strip()
        
        cortex_response=model_response

        if generate_sql: # if need to generate SQL then

            # Prompting model to generate SQL and execute
            sql_query_generated=session.sql(f"""
            SELECT snowflake.cortex.complete(
            'snowflake-arctic', 
            $$Act as an Snowflake SQL expert, convert this User's natuaral input prompt into a SQL statement.
            Note - When context is clear to you, then only give me the SQL statement to be executed as output.
            
            CRM database schema context given below for for generating SQL :
            
            - leads(lead_id, name, region, score)
            - deals(deal_id, lead_id, status, close_date)  
            sample deal status data - 'Closed-Won', 'Closed-lost', 
            'Proposal' etc., This is just an example  $$)""").collect()[0][0]

            st.session_state.chat_history.append({"role": "ai", "message": sql_query_generated})
            
            


    # Chatbot relpying back to user response
    with st.chat_message("ai",avatar="❄️"):
        
        st.write(f"{cortex_response}")
        st.session_state.chat_history.append({"role": "ai", "message": cortex_response})

     




