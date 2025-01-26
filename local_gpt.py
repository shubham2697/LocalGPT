import streamlit as st
import ollama

# Clear chat history from the history
def clear_chat_history():
    st.session_state.messages = START_MESSAGE

# Function for generating LLaMA2 response
def generate_llama2_response():
    string_dialogue = f"You are a {assistant_role}. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"

    output = ollama.generate(
        model = selected_model,
        prompt = string_dialogue,
        stream = enable_streaming,
        options = slider_values if enable_options else None
    )
    return output

# Function to add the backquotes to the response if thinking text is displayed
def add_backquote(next_token, thinking, still_thinking):

    if not enable_streaming and "</think>" in next_token:
        _next_token = next_token.split("</think>")
        next_token = (_next_token[0] + "</think>").replace("\n", "\n>") + _next_token[1]
    else:
        if "<think>" in next_token:
            thinking = 1
            next_token = ">" + next_token
        elif "\n" in next_token and thinking:
            still_thinking = 1
        elif still_thinking:
            next_token = ">" + next_token
            still_thinking = 0

        if "</think>" in next_token:
            still_thinking = thinking = 0

    return next_token, thinking, still_thinking

# App Const
ST_SLIDERS = {
    "temperature" : [0.01, 2.0, 0.1, 0.01],
    "top_p" : [0.01, 1.0, 0.9, 0.01],
    "max_length" : [8, 4096, 512, 8],
    "repetition_penalty" : [0.1, 2.0, 1.0, 0.1]
}

AVAILABLE_MODEL_AND_ITS_CONFIGS = {
    "llama3.2" : ["temperature", "top_p", "repetition_penalty"],
    "deepseek-r1" : ["temperature", "top_p", "max_length", "repetition_penalty"],
    "deepseek-r1:8b" : ["temperature", "top_p", "max_length", "repetition_penalty"],
}
START_MESSAGE = [{"role": "assistant", "content": "How may I assist you today?"}]

# App title
st.set_page_config(page_title="LocalGPT")
with st.sidebar:
    st.title('LocalGPT')
    assistant_role = st.sidebar.text_input('Define a role for your assistant... go wild!', "assistant", key='assistant_role')
    st.subheader('Models and parameters')

    selected_model = st.sidebar.selectbox('Choose a Local model to use', list(AVAILABLE_MODEL_AND_ITS_CONFIGS.keys()), key='selected_model')
    enable_streaming = st.sidebar.selectbox('Do you want to stream the response?', [True, False], key='enable_streaming')
    enable_options = st.sidebar.selectbox('Do you want to enable Advance model params', [False, True], key='enable_options')
    if enable_options:
        slider_values = {
            slider_name : st.sidebar.slider(slider_name, *config, key = slider_name)
            for slider_name, config in ST_SLIDERS.items()
            if slider_name in AVAILABLE_MODEL_AND_ITS_CONFIGS[selected_model]
        }

    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = START_MESSAGE
    
# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User-provided prompt
prompt = st.chat_input()
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_llama2_response()
            # print(response)
            placeholder = st.empty()
            full_response = ''
            thinking = still_thinking = 0
            for item in response:
                # print(item)
                ## fetch next Token
                if not enable_streaming and item[0] == "response": next_token = item[1]
                elif not enable_streaming: continue
                elif enable_streaming: next_token = item["response"]

                ## Cleaning and adding blockquotes in the markdown for Thinking Block
                next_token = next_token.replace("\n\n", "\n")
                next_token, thinking, still_thinking = add_backquote(next_token, thinking, still_thinking)
                full_response += next_token.replace("<think>", "Started thinking...\n>").replace("</think>", "\n>Thinking Complete...\n")
                
                # print(next_token)
                placeholder.markdown(full_response)
            # placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)