from setuptools import setup, find_packages

setup(
    name="device-registration-portal",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot==20.7",
        "flask==2.3.3",
        "python-dotenv==1.0.0",
        "werkzeug==2.3.7",
        "aiohttp==3.8.5",
    ],
    author="Your Name",
    description="Device Registration Portal with Telegram Bot integration",
    python_requires=">=3.8",
)