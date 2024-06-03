import os
from openai import OpenAI
from pymongo import MongoClient

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize MongoDB client
mongodb_client = MongoClient("mongodb://localhost:27017/")
db = mongodb_client["chatbot"]  # choosing database
chat_sessions = db["chat_sessions"]  # choosing collection

# Set user and session to be used for the chat
user_id = input("Enter user_id: ")  # e.g. "user123"
session_id = input("Enter session_id: ")  # e.g. "session123"

# Create index for 'user_id' and 'session_id' to optimize queries
chat_sessions.create_index([("user_id", 1), ("session_id", 1)])


def get_last_conversation():
    """Retrieve last conversation from MongoDB or return default message if none exists."""
    session = chat_sessions.find_one({"user_id": user_id, "session_id": session_id})
    if session and "conversation" in session:
        print_chat_history(session["conversation"])
        return session["conversation"]
    return [{"role": "system", "content": "You are a helpful assistant."}]


def print_chat_history(conversation):
    """Prints relevant chat history to the user. Omits system message."""
    print("______CHAT_HISTORY______")
    for message in conversation:
        if message["role"] == "system":
            continue
        print(f"{message['role'].capitalize()}: {message['content']}")


def save_conversation(conversation):
    """Update or insert current conversation into MongoDB for specified user and session."""
    chat_sessions.update_one(
        {"user_id": user_id, "session_id": session_id},
        {"$set": {"conversation": conversation}},
        upsert=True,
    )


def chat_with_openai(message, conversation):
    """Send user message to OpenAI API and return chatbot's response based on conversation history."""
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation
        + [
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message.content


def main():
    conversation = get_last_conversation()
    while True:
        user_input = input("User: ")
        response = chat_with_openai(user_input, conversation)
        conversation.append({"role": "user", "content": user_input})
        conversation.append({"role": "assistant", "content": response})
        save_conversation(conversation)
        print("Assistant:", response)


if __name__ == "__main__":
    main()
