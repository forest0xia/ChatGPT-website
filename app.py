from app.main import create_app

if __name__ == "__main__":
    app = create_app()
else:
    print("Not running in main/entrypoint mode")
    app = create_app()
