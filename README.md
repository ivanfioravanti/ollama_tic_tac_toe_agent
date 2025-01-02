# Ollama Tic-Tac-Toe AI Battle

A Streamlit-based web application that pits two AI agents against each other in a game of Tic-Tac-Toe using Ollama models.

## Features

- 🎮 AI vs AI Tic-Tac-Toe gameplay
- 🤖 Support for multiple Ollama models
- 🎯 Real-time game visualization
- 💫 Beautiful, modern UI with Streamlit
- 🔄 Dynamic model selection

## Requirements

- Python 3.8+
- Ollama installed and running locally
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ivanfioravanti/ollama_tic_tac_toe_agent.git
cd ollama_tic_tac_toe_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure Ollama is installed and running locally with your preferred models.

## Usage

1. Start the Streamlit app:
```bash
streamlit run main.py
```

2. Select the AI models for Player X and Player O from the sidebar
3. Click "Start Game" to watch the AI agents battle!

## How it Works

The application uses the Phidata library to create AI agents powered by Ollama models. These agents take turns analyzing the game board and making moves in a classic game of Tic-Tac-Toe. The game state is managed through Streamlit's session state, and the UI is updated in real-time to show the progress of the game.

## License

MIT License - feel free to use this project however you'd like!
