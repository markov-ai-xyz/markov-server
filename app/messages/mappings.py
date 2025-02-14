from langchain.schema import AIMessage, HumanMessage


def map_chat_history_to_langchain(messages):
    conversation = []
    for m in messages:
        if m.get("type") == "bot":
            langchain_ai_message = AIMessage(content=m.get("message"))
            conversation.append(langchain_ai_message)
        elif m.get("type") == "user":
            langchain_human_message = HumanMessage(content=m.get("message"))
            conversation.append(langchain_human_message)
        else:
            raise ValueError("Invalid message")
    return conversation
