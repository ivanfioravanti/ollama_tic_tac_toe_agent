import re
import streamlit as st
from phi.agent import Agent
from phi.model.ollama import Ollama
import ollama

# Constants
BOARD_SIZE = 3
MAX_MOVES = 9
DEFAULT_MODEL = "Phi-4:Q8_0"
AGENT_TEMPERATURE = 0.3

# CSS Styles
BOARD_STYLE = """
    <style>
    .board {
        display: grid;
        grid-template-columns: repeat(3, 80px);
        grid-template-rows: repeat(3, 80px);
        gap: 5px;
        background-color: #2c3e50;
        padding: 10px;
        border-radius: 10px;
    }
    .cell {
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #1a1a1a;
        border: 2px solid #34495e;
        border-radius: 5px;
        font-size: 32px;
        font-weight: bold;
        color: white;
    }
    </style>
"""

# Game State Initialization
all_models = [model.model for model in ollama.list()['models']]
winner = None
started = False

def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'board' not in st.session_state:
        st.session_state.board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    if 'board_container' not in st.session_state:
        st.session_state.board_container = st.empty()
    if 'current_player' not in st.session_state:
        st.session_state.current_player = None
    if 'symbol' not in st.session_state:
        st.session_state.symbol = "X"
    if 'move_count' not in st.session_state:
        st.session_state.move_count = 0

def display_board(board):
    """Display the game board with styling."""
    board_html = BOARD_STYLE
    board_html += '<div class="board-container"><div class="board">'
    for row in board:
        for cell in row:
            cell_value = cell if cell is not None else "&nbsp;"
            board_html += f'<div class="cell">{cell_value}</div>'
    board_html += '</div></div>'
    st.session_state.board_container.markdown(board_html, unsafe_allow_html=True)

def get_board_state(board):
    """Convert the board state to a string representation."""
    rows = []
    for i, row in enumerate(board):
        row_str = " | ".join([f"({i},{j}) {cell or ' '}" for j, cell in enumerate(row)])
        rows.append(f"Row {i}: {row_str}")
    return "\n".join(rows)

def check_winner(board):
    """Check if there's a winner or if the game is a draw."""
    # Check rows and columns
    for i in range(BOARD_SIZE):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] is not None:
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] is not None:
            return board[0][i]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None:
        return board[0][2]
    
    # Check for draw
    if all(cell is not None for row in board for cell in row):
        return "Draw"
    return None

def get_player_instructions(symbol):
    """Generate instructions for the AI agent."""
    opponent_symbol = "O" if symbol == "X" else "X"
    return [
        f"You are a world class Tic-Tac-Toe player using the symbol '{symbol}'.",
        f"Your opponent is using the symbol '{opponent_symbol}'. Block their potential winning moves.",
        "Make your move in the format 'row, col' based on the current board state.",
        "Examples: (0,0) (1,1) (2,2) (0,1) (0,2) (1,0) (1,2) (2,0) (2,1)",
        "Do not include any explanations or extra text. Only provide the move.",
        "Row and column indices start from 0.",
        "To win, you must get three of your symbols in a row (horizontally, vertically, or diagonally).",
    ]

def extract_move(response):
    """Extract the move coordinates from the agent's response."""
    content = response.content.strip()
    match = re.search(r'\d\s*,\s*\d', content)
    if match:
        move = match.group().replace(' ', '')
        return move
    numbers = re.findall(r'\d+', content)
    if len(numbers) >= 2:
        row = int(numbers[0])
        col = int(numbers[1])
        return f"{row},{col}"
    return None

def display_game_result(winner, top_placeholder):
    """Display the game result with styling."""
    with top_placeholder:
        st.markdown("""
        <div style='text-align: center; background-color: #1a1a1a; padding: 20px; border-radius: 10px; margin-top: 20px;'>
            <h3 style='text-align: center; margin-bottom: 20px;'>🏆 Game Results</h3>
        </div>
        """, unsafe_allow_html=True)

        if winner and winner != "Draw":
            st.markdown(f"""
                <div style='text-align: center; background-color: #2c3e50; padding: 15px; border-radius: 8px; margin: 10px 0;'>
                    <p style='text-align: center; font-size: 24px; margin: 0;'>🎉 <strong>Winner:</strong> Player {winner} 🎉</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style='text-align: center; background-color: #2c3e50; padding: 15px; border-radius: 8px; margin: 10px 0;'>
                    <p style='text-align: center; font-size: 24px; margin: 0;'>🤝 <strong>Game Over:</strong> It's a Draw! 🤝</p>
                </div>
            """, unsafe_allow_html=True)

def play_game():
    """Main game loop."""
    game_log_container = st.container()
    winner = None

    while st.session_state.move_count < MAX_MOVES and not winner:
        # Update the board display
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        display_board(st.session_state.board)
        st.markdown("</div>", unsafe_allow_html=True)

        # Prepare the board state for the agent
        board_state = get_board_state(st.session_state.board)
        move_prompt = (
            f"Current board state:\n{board_state}\n"
            f"{st.session_state.current_player.name}'s turn. Make your move in the format 'row, col'."
        )

        # Get the current player's move
        with game_log_container:
            with st.chat_message("assistant"):
                st.write(f"**{st.session_state.current_player.name}'s turn:**")
                move_response = st.session_state.current_player.run(move_prompt)
                st.code(f"Agent {st.session_state.current_player.name} response:\n{move_response.content}", language="markdown")
                move = extract_move(move_response)
                st.write(f"**Extracted move:** {move}")

        if move is None:
            st.error("Invalid move! Please use the format 'row, col'.")
            continue

        try:
            row, col = map(int, move.split(','))
            if st.session_state.board[row][col] is not None:
                st.error("Invalid move! Cell already occupied.")
                continue
            st.session_state.board[row][col] = st.session_state.symbol
        except (ValueError, IndexError):
            st.error("Invalid move! Please use the format 'row, col'.")
            continue

        # Check for a winner or draw
        winner = check_winner(st.session_state.board)
        if not winner:
            # Switch players
            st.session_state.current_player = player_o if st.session_state.current_player == player_x else player_x
            st.session_state.symbol = "O" if st.session_state.symbol == "X" else "X"
            st.session_state.move_count += 1
        else:
            display_game_result(winner, top_placeholder)
            display_board(st.session_state.board)

def main():
    """Main application entry point."""
    global started, player_x, player_o, intro_container, started_container, top_placeholder
    
    st.title("🎮 Phidata Ollama Tic-Tac-Toe")
    
    # Sidebar for model selection
    st.sidebar.title("🤖 Model Selection")
    player_x_model = st.sidebar.selectbox(
        "Model for Player X",
        options=all_models,
        index=all_models.index(DEFAULT_MODEL),
        key="player_x_model"
    )

    player_o_model = st.sidebar.selectbox(
        "Model for Player O",
        options=all_models,
        index=all_models.index(DEFAULT_MODEL),
        key="player_o_model"
    )

    # Initialize agents
    player_x = Agent(
        name="Player X",
        model=Ollama(id=player_x_model, options={"temperature": AGENT_TEMPERATURE}),
        instructions=get_player_instructions("X"),
        markdown=True
    )

    player_o = Agent(
        name="Player O",
        model=Ollama(id=player_o_model, options={"temperature": AGENT_TEMPERATURE}),
        instructions=get_player_instructions("O"),
        markdown=True
    )

    # Game initialization
    intro_container = st.empty()
    started_container = st.empty()
    top_placeholder = st.empty()

    if not started:
        display_welcome_message()
        init_session_state()

    # Start Game Button
    if st.button("Start Game"):
        started = True
        with started_container:
            st.markdown(
                """
                <div style="font-size:20px;">
                <b>GREETINGS PROFESSOR FALKEN</b><br><br>
                HELLO<br><br>
                A STRANGE GAME.<br>
                THE ONLY WINNING MOVE IS<br>
                NOT TO PLAY.<br><br>
                
                </div>
                """, 
                unsafe_allow_html=True
            )
        intro_container.empty()
        st.session_state.board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        st.session_state.board_container = st.empty()
        st.session_state.current_player = player_x
        st.session_state.symbol = "X"
        st.session_state.move_count = 0
        play_game()

def display_welcome_message():
    """Display the welcome message and game instructions."""
    with intro_container:
        with st.chat_message("assistant"):
            st.markdown("""
                **Welcome to the Phidata Ollama Tic-Tac-Toe AI Battle!** 🎮  
                This project pits two advanced AI agents against each other in a classic game of Tic-Tac-Toe.  
                Here's what you need to know:
            """)
            st.info("""
                - **Player X**: Powered by your selected model.  
                - **Player O**: Powered by your selected model.  
                - **How to Play**: Click **Start Game**, and watch the AI battle it out!  
                - **Goal**: The first player to get three of their symbols in a row wins.  
                - **Draw**: If the board fills up without a winner, the game ends in a draw.  
            """)
            st.markdown("Ready to see who wins? Click the **Start Game** button below! 🚀")

if __name__ == "__main__":
    main()