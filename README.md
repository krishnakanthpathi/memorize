# memorize

Personal Knowledge Base MCP Server with Multi-Media Semantic RAG.

See [BUILD_JOURNAL.md](file:///Users/krishnakanth/Projects/memorize/BUILD_JOURNAL.md) for the detailed build log, architectural insights, and code blueprints.

## How to Run This Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt fastapi uvicorn
```

### 2. Run the FastAPI REST Service
> ⚠️ **Important**: Make sure your terminal is in the project root directory (`/Users/krishnakanth/Projects/memorize`), not inside the `api/` folder.

```bash
cd /Users/krishnakanth/Projects/memorize
python3 -m api.server
```

Or using uvicorn directly:
```bash
cd /Users/krishnakanth/Projects/memorize
python3 -m uvicorn api.server:app --host 0.0.0.0 --port 6999 --reload
```

### 3. Run the FastMCP Server
```bash
cd /Users/krishnakanth/Projects/memorize
python3 main.py
```
