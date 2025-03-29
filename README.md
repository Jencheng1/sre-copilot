# SRE Copilot - Multi-Agent Incident RCA System

A powerful Site Reliability Engineering (SRE) Copilot application that leverages multi-agent and multi-modal capabilities to perform incident Root Cause Analysis (RCA) using AWS Bedrock.

## Features

- Multi-agent architecture for comprehensive incident analysis
- Multi-modal data processing (text, metrics, logs, images)
- AWS Bedrock integration for advanced AI capabilities
- Interactive Streamlit dashboard
- Real-time metrics and log visualization
- Automated RCA with confidence scoring
- Actionable recommendations generation

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sre-copilot.git
cd sre-copilot
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Graphviz (required for diagrams):
- Windows: Download and install from https://graphviz.org/download/
- Linux: `sudo apt-get install graphviz`
- macOS: `brew install graphviz`

5. Create a `.env` file with your AWS credentials:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
```

## Running Locally

1. Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Open your browser and navigate to http://localhost:8501

## Deployment to Streamlit Cloud

1. Push your code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/sre-copilot.git
git push -u origin main
```

2. Deploy to Streamlit Cloud:
- Go to https://share.streamlit.io/
- Sign in with your GitHub account
- Click "New app"
- Select your repository and the `streamlit_app.py` file
- Add your AWS credentials as secrets in Streamlit Cloud:
  - Go to app settings
  - Click "Secrets"
  - Add your AWS credentials:
    ```toml
    AWS_ACCESS_KEY_ID = "your_access_key"
    AWS_SECRET_ACCESS_KEY = "your_secret_key"
    AWS_REGION = "your_region"
    ```
- Click "Deploy"

## Project Structure

```
sre-copilot/
├── main.py                 # Main application logic
├── streamlit_app.py        # Streamlit dashboard
├── models/
│   └── incident.py         # Data models
├── utils/
│   ├── diagrams.py         # System diagrams
│   └── test_data.py        # Test data generation
├── static/
│   └── diagrams/          # Generated diagrams
├── requirements.txt        # Python dependencies
└── .env                   # Environment variables
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 