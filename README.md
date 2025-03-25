# AI Agent

An advanced AI agent that can process voice commands, detect emotions, and generate contextual responses using various AI models.

## Features

- Wake word detection
- Voice command processing
- Emotion detection
- Natural language response generation
- Text-to-speech output
- Real-time internet information retrieval

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Internet connection for API calls

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AIAgent
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file in the root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

Run the main program:
```bash
python main.py
```

The agent will start listening for the wake word. Once detected:
1. Speak your command
2. The agent will process your command
3. You'll receive a response based on your input and detected emotion

## Stopping the Program

Press Ctrl+C to stop the program. The agent will perform cleanup operations before shutting down. 