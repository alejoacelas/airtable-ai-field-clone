# AI Spreadsheet Interface

A Streamlit-based spreadsheet interface that connects to Google Sheets and OpenAI's API to run custom prompts on spreadsheet columns with XML-based response extraction.

## Features

- **Google Sheets Integration**: Seamlessly connect and sync with Google Sheets
- **Dynamic Data Editor**: Edit spreadsheet data with add/delete row capabilities  
- **Prompt Configuration**: Set up column-specific AI prompts with reference capabilities
- **XML Response Extraction**: Parse AI responses into structured sections
- **Multi-tab Interface**: Separate views for main data and extracted response sections

## Phase 1 Implementation Status

✅ **Completed Features:**
- [x] Basic Streamlit app structure with tabs
- [x] Google Sheets connection (read/write) 
- [x] Dynamic data editor with add/delete functionality
- [x] Session state management
- [x] Prompt configuration table
- [x] Basic error handling for connection issues

🚧 **Next Phase Features:**
- [ ] OpenAI API integration
- [ ] AI prompt execution with column references
- [ ] XML tag extraction system
- [ ] Async batch processing
- [ ] Progress indicators

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Google Sheets

1. Create a Google Cloud Project and enable the Google Sheets API
2. Create a service account and download the JSON credentials  
3. Create a Google Sheet and share it with the service account email
4. **Copy the share link** from your Google Sheet (any format works!)
5. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
6. Paste your share link in the `spreadsheet` field - the app will extract the ID automatically

### 3. Configure OpenAI (For Future Phases)

1. Copy `.env.example` to `.env`
2. Add your OpenAI API key to the environment file
3. Update the secrets.toml file with your OpenAI API key

### 4. Run the Application

```bash
streamlit run app.py
```

## Project Structure

```
airtable-clone/
├── app.py                          # Main Streamlit application
├── sheets_manager.py               # Google Sheets integration
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── PLAN.md                        # Detailed implementation plan
├── .env.example                   # Environment variables template
└── .streamlit/
    └── secrets.toml.example       # Streamlit secrets template
```

## Usage

1. **Connect to Google Sheets**: The app will automatically connect using your configured credentials
2. **Configure Prompts**: Set up AI prompts for each column in the configuration table
3. **Edit Data**: Use the dynamic data editor to add, edit, or delete rows
4. **Save/Load**: Use the control panel to save changes to Google Sheets or load fresh data

## Google Sheets Structure

The application creates the following worksheets:

- **Main_Data**: Primary data with system columns (_id, _created_at, _updated_at)
- **Prompt_Config**: Prompt configurations for each column
- **Extract_Sources**: Extracted content from `<sources>` tags
- **Extract_Reasoning**: Extracted content from `<reasoning>` tags  
- **Extract_Annotations**: Extracted content from `<annotations>` tags
- **Extract_Answer**: Extracted content from `<answer>` tags

## Development

This is Phase 1 of the implementation focusing on the foundation:
- ✅ Google Sheets integration 
- ✅ Basic UI components
- ✅ Data management
- 🚧 AI processing (Phase 2)
- 🚧 Batch operations (Phase 3)
- 🚧 Advanced features (Phase 4+)

See `PLAN.md` for the complete implementation roadmap.