from app import create_app

markov = create_app()

if __name__ == "__main__":
    markov.run(host="0.0.0.0", port=5000)
