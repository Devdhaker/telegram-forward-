import json
import os
import asyncio
import random
from telethon import TelegramClient, events
from config import API_ID, API_HASH, USERS_FILE

# Ensure users.json exists
def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)

# Load all users
def load_users():
    ensure_users_file()
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# Add a new user
async def add_user(phone, session_name, client):
    users = load_users()
    try:
        me = await client.get_me()
        username = me.username if me.username else f"User_{me.id}"
    except Exception:
        username = "Unknown"
    
    users.append({
        "phone": phone,
        "session": session_name,
        "username": username,
        "source_chats": [],
        "destination_chats": []
    })
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# Function to create a new session
async def create_session():
    phone = input("\n📞 Enter your Telegram number (e.g., +917878066868): ").strip()
    if not phone.startswith("+") or not phone[1:].isdigit():
        print("❌ Invalid number format! Use +917878066868")
        return

    session_name = phone.replace("+", "").replace(" ", "")
    if not os.path.exists("sessions"):
        os.makedirs("sessions")

    client = TelegramClient(f"sessions/{session_name}", API_ID, API_HASH)
    try:
        await client.start(phone)
        print("✅ Session created successfully!")
        await add_user(phone, session_name, client)
    except Exception as e:
        print(f"❌ Error creating session: {e}")
    finally:
        await client.disconnect()

# Function to get chat ID from username or ID
async def get_chat_id(client, chat_input):
    try:
        if chat_input.isdigit():
            return int(chat_input)
        entity = await client.get_entity(chat_input)
        return entity.id
    except Exception as e:
        print(f"⚠️ Error fetching ID for '{chat_input}': {e}")
        return None

# Set up forwarding
async def setup_forwarding():
    users = load_users()
    if not users:
        print("⚠️ No users found! Create a session first.")
        return

    phone = input("📞 Enter the phone number for setup: ").strip()
    user = next((u for u in users if u["phone"] == phone), None)
    if not user:
        print("❌ This number is not logged in! Create a session first.")
        return

    session_name = user["session"]
    client = TelegramClient(f"sessions/{session_name}", API_ID, API_HASH)
    await client.start()

    source_chats = input("📥 Enter source chat IDs/usernames (comma separated): ").split(",")
    destination_chats = input("📤 Enter destination chat IDs/usernames (comma separated): ").split(",")

    user["source_chats"] = []
    user["destination_chats"] = []

    for chat in source_chats:
        chat_id = await get_chat_id(client, chat.strip())
        if chat_id:
            user["source_chats"].append(chat_id)

    for chat in destination_chats:
        chat_id = await get_chat_id(client, chat.strip())
        if chat_id:
            user["destination_chats"].append(chat_id)

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    print("✅ Forwarding setup complete!")
    await client.disconnect()

# Start forwarding messages
async def start_forwarding():
    users = load_users()
    if not users:
        print("⚠️ No users found! Create a session first.")
        return

    clients = []

    for user in users:
        if not user.get("source_chats") or not user.get("destination_chats"):
            print(f"⚠️ Forwarding setup missing for {user['phone']}!")
            continue

        client = TelegramClient(f"sessions/{user['session']}", API_ID, API_HASH)
        await client.start()

        async def handler(event, user=user, client=client):
            print(f"📩 New message from {user['username']} ({user['phone']}):")
            
            for dest in user["destination_chats"]:
                try:
                    print(f"🔄 Forwarding message to {dest}...")
                    await event.message.forward_to(dest)
                    print(f"✅ Message forwarded to {dest}!")
                    await asyncio.sleep(random.uniform(2, 4))  # Safe delay
                except Exception as e:
                    print(f"⚠️ Error forwarding to {dest}: {e}")

        client.add_event_handler(handler, events.NewMessage(chats=user["source_chats"]))

        clients.append(client)

    print("🚀 Bot is now live!")
    await asyncio.gather(*(client.run_until_disconnected() for client in clients))
    await main()

# Main menu
async def main():
    while True:
        print("\n🔹 Telegram Forwarding Bot 🔹\n")
        print("1️⃣ Create new Telegram session")
        print("2️⃣ Set up message forwarding")
        print("3️⃣ Start bot")
        print("4️⃣ Exit")

        choice = input("➡️ Choose an option (1/2/3/4): ").strip()

        if choice == "1":
            await create_session()
        elif choice == "2":
            await setup_forwarding()
        elif choice == "3":
            await start_forwarding()
        elif choice == "4":
            print("👋 Exiting bot.")
            break
        else:
            print("❌ Invalid input! Choose 1, 2, 3, or 4.")

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())
