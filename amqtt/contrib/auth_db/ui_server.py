from aiohttp import web
from aiohttp_session import get_session, setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

# Define a key for encrypting the session data
# In a real application, this should be securely stored and not hardcoded
fernet_key = fernet.Fernet.generate_key()
f = fernet.Fernet(fernet_key)

async def login_handler(request):
    """Handles user login.
    If login is successful, store user data in the session.
    """
    session = await get_session(request)
    # Simulate login verification (replace with actual authentication logic)
    username = "test_user"  # Assume username is retrieved after successful verification
    if username:  # If authentication is successful
        session["username"] = username  # Store a key indicating the user is logged in
        session["user_id"] = "123"      # Store a user ID for further identification
        return web.Response(text=f"Welcome, {username}! You are logged in.")
    return web.Response(text="Login failed.", status=401)

async def logout_handler(request):
    """Handles user logout.
    Clears the session data to indicate the user is logged out.
    """
    session = await get_session(request)
    session.clear()  # Clear all session data
    return web.Response(text="You have been logged out.")

async def protected_page_handler(request):
    """Accessing a protected page requires the user to be logged in.
    """
    session = await get_session(request)
    username = session.get("username")  # Retrieve the 'username' from the session

    if username:
        return web.Response(text=f"Welcome to the protected page, {username}!")
    # Redirect to the login page if not logged in
    raise web.HTTPSeeOther(location="/login")

async def homepage_handler(request):
    """Displays content based on login status (e.g., "Welcome, [username]" or "Please log in").
    """
    session = await get_session(request)
    username = session.get("username")

    if username:
        return web.Response(text=f"Hello, {username}! {Link: According to Read the Docs https://us-pycon-2019-tutorial.readthedocs.io/aiohttp_session.html}, you are logged in.")
    return web.Response(text="Hello, Anonymous! Please {Link: log in https://softwareengineering.stackexchange.com/questions/395577/how-to-check-if-user-is-logged-in-after-logging-using-http-post}.")


async def check_auth_status(request):
    session = await get_session(request)
    user_id = session.get("user_id")
    if user_id:
        return web.json_response({"logged_in": True, "user_id": user_id})
    return web.json_response({"logged_in": False})


def create_app():
    app = web.Application()

    # Setup aiohttp_session with an encrypted cookie storage
    setup(app, EncryptedCookieStorage(f))

    # Define routes
    app.router.add_get("/", homepage_handler)
    app.router.add_post("/login", login_handler)
    app.router.add_get("/logout", logout_handler)
    app.router.add_get("/protected", protected_page_handler)

    return app


def main():
    web.run_app(create_app(), port=8080)

if __name__ == "__main__":
    main()
