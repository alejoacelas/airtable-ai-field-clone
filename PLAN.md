# Claude Code: AI Spreadsheet Interface - Implementation Specification

## Project Overview

Create a Streamlit-based spreadsheet interface that connects to OpenAI's Responses API to run custom prompts on spreadsheet columns, with persistent storage in Google Sheets. The interface functions similar to Airtable's Field AI but with enhanced prompt capabilities and XML-based response extraction.

## Technical Architecture

### Core Technologies
- **Frontend**: Streamlit with `st.data_editor` 
- **AI Processing**: OpenAI Responses API (GPT-4.1/GPT-5-thinking)
- **Storage**: Google Sheets via `st-gsheets-connection`
- **Async Processing**: `tenacity` for exponential backoff
- **Response Parsing**: XML tag extraction system

### Key Features
1. **Dynamic Data Editor**: Edit spreadsheet data with add/delete row capabilities
2. **Prompt Management**: Column-specific prompts that can reference other columns
3. **Batch AI Processing**: Run prompts across selected columns with async processing
4. **XML Response Extraction**: Parse AI responses into structured sections
5. **Persistent Storage**: Automatic sync with Google Sheets
6. **Multi-tab Interface**: Separate views for main data and extracted response sections

## UI Component Specifications

### 1. Prompt Configuration Table
**Location**: Top section of the page
**Purpose**: Configure AI prompts for each column

**Columns**:
- `Column Name`: Display name of the data column
- `Prompt Text`: Editable text area for the prompt (default: "LOCKED")
- `Replace Mode`: Checkbox - "Replace all values" vs "Fill empty cells only"
- `Web Search`: Whether to use web-search in the API call

**Behavior**:
- Prompts set to "LOCKED" are skipped during processing
- Prompts can reference other columns using syntax like `{column_name}`
- Real-time validation of column references

### 2. Main Data Table
**Location**: Center section in primary tab
**Implementation**: `st.data_editor` with `num_rows="dynamic"`

**Features**:
- Error highlighting for failed AI calls

### 3. Response Extraction Tabs
**Location**: Additional tabs alongside main data tab
**Purpose**: Display extracted sections from AI responses

**Default Tabs**:
- `Sources`: Content from `<sources>` tags
- `Reasoning`: Content from `<reasoning>` tags  
- `Annotations`: Content from `<annotations>` tags
- `Answer`: Content from `<answer>` tags

**Customization**: Users can configure additional XML tags to extract

### 4. Control Panel
**Location**: Bottom section or sidebar
**Components**:
- `Run Prompts` button with progress bar
- `Save to Google Sheets` button
- `Load from Google Sheets` button
- Configuration options for XML tags
- API usage metrics display

## Data Flow Architecture

### 1. Initialization Flow
```
1. Check Google Sheets connection
2. Load existing data if sheets exist with correct format
3. Initialize prompt configuration table
4. Set up session state for data persistence
```

### 2. Prompt Execution Flow
```
1. Validate active prompts and column references
2. Build prompt strings with column value substitutions
3. Create async API calls with tenacity retry logic
4. Process responses and extract XML content
5. Update main data table and extraction tabs
6. Auto-save to Google Sheets once finished
```

### 3. Storage Flow
```
1. Main data stored in primary worksheet
2. Prompt configurations stored in secondary worksheet
3. XML extractions stored in separate worksheets per tag type
```

## Implementation Modules

### Module 1: Google Sheets Integration
**Files**: `sheets_manager.py`
**Dependencies**: `streamlit-gsheets-connection`, `pandas`

**Key Functions**:
- `initialize_sheets_connection()`: Set up authentication
- `load_data_from_sheets()`: Read main data and configurations
- `save_data_to_sheets()`: Write data with proper formatting
- `create_backup()`: Snapshot before changes
- `validate_sheet_structure()`: Ensure proper column setup

**Configuration**:
```toml
[connections.gsheets]
spreadsheet = "sheet_url_or_id"
type = "service_account"  # or "" for public sheets
# Service account credentials...
```

### Module 2: OpenAI API Integration  
**Files**: `ai_processor.py`
**Dependencies**: `openai`, `tenacity`, `asyncio`

**Key Functions**:
- `setup_openai_client()`: Initialize client with proper config
- `build_prompt_with_references()`: Substitute column values into prompts
- `execute_batch_prompts()`: Process multiple prompts asynchronously
- `extract_xml_content()`: Parse response for specified tags
- `handle_api_errors()`: Graceful error handling and logging

**API Configuration**:
```python
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
async def call_responses_api(prompt, model="gpt-4.1"):
    response = await client.responses.create(
        model=model,
        input=prompt,
        tools=[{"type": "web_search_preview"}] if needs_search else []
    )
    return response
```

### Module 3: UI Components
**Files**: `ui_components.py`
**Dependencies**: `streamlit`, `pandas`

**Key Functions**:
- `render_prompt_config_table()`: Prompt management interface
- `render_main_data_editor()`: Primary data editing interface  
- `render_extraction_tabs()`: XML content display tabs
- `render_control_panel()`: Action buttons and configuration
- `handle_session_state()`: Manage data persistence across reruns

### Module 4: Response Processing
**Files**: `response_parser.py`
**Dependencies**: `xml.etree.ElementTree`, `re`

**Key Functions**:
- `parse_xml_tags()`: Extract content from specified XML tags
- `validate_response_structure()`: Check for expected response format
- `merge_extracted_content()`: Combine extractions into structured data
- `handle_parsing_errors()`: Fallback for malformed responses

## Implementation Phases

### Phase 1: Foundation 
**Scope**: Basic Streamlit app with Google Sheets integration
**Deliverables**:
- [ ] Streamlit app structure with tabs
- [ ] Google Sheets connection (read/write)
- [ ] Basic data editor with dynamic rows
- [ ] Session state management
- [ ] Simple prompt configuration table

**Validation Criteria**:
- Can load/save data to Google Sheets
- Data editor works with add/delete functionality
- Session state persists data across reruns
- Basic error handling for connection issues

### Phase 2: AI Integration
**Scope**: OpenAI Responses API integration with basic prompts
**Deliverables**:
- [ ] OpenAI client setup with API key management
- [ ] Single prompt execution with column reference
- [ ] Basic response handling and error management
- [ ] Simple XML tag extraction (answer tags only)
- [ ] Progress indicators for API calls

**Validation Criteria**:
- Can execute prompts that reference other columns
- Basic XML extraction works for `<answer>` tags
- Proper error handling for API failures
- Response time acceptable for single prompts

### Phase 3: Batch Processing
**Scope**: Async batch processing with full XML extraction
**Deliverables**:
- [ ] Async prompt execution for multiple rows
- [ ] Tenacity retry logic with exponential backoff
- [ ] Full XML tag extraction system
- [ ] Progress tracking for batch operations
- [ ] Response validation and error recovery

**Validation Criteria**:
- Can process multiple prompts simultaneously
- Retry logic handles temporary API failures
- All specified XML tags extracted correctly
- Batch operations complete within reasonable time

### Phase 4: Advanced Features
**Scope**: Enhanced UI and advanced prompt features
**Deliverables**:
- [ ] Customizable XML tag configuration
- [ ] Advanced prompt templates with multiple column references
- [ ] Response history and versioning
- [ ] Export capabilities for processed data
- [ ] Performance optimization and caching

**Validation Criteria**:
- Users can configure custom XML tags
- Complex prompts with multiple references work
- Performance acceptable for large datasets
- Full feature integration testing complete

### Phase 5: Polish & Production
**Scope**: Production readiness and documentation
**Deliverables**:
- [ ] Comprehensive error handling and user feedback
- [ ] Security audit for API key management
- [ ] User documentation and tutorials
- [ ] Performance testing and optimization
- [ ] Deployment configuration

**Validation Criteria**:
- Production-ready error handling
- Security best practices implemented
- Complete user documentation
- Performance benchmarks met

## Technical Specifications

### Google Sheets Structure
**Primary Worksheet**: "Main_Data"
- User-defined columns for actual data
- System columns: `_id`, `_created_at`, `_updated_at`

**Configuration Worksheet**: "Prompt_Config"
- `column_name`, `prompt_text`, `replace_mode`, `is_active`

**Extraction Worksheets**: "Extract_[TagName]"
- `row_id`, `original_column`, `extracted_content`, `extraction_date`

### API Usage Patterns
**Prompt Template Example**:
```
Analyze the following data:
Name: {name}
Description: {description}
Category: {category}

Based on this information, provide:
<reasoning>Your analysis process</reasoning>
<answer>Your conclusion</answer>
<sources>Any sources you reference</sources>
```

**Column Reference Syntax**:
- `{{column_name}}` - Insert value from specified column
- `{column_name:default_value}` - Use default if column empty

### Session State Management
**Key Variables**:
- `main_data`: Primary dataset DataFrame
- `prompt_config`: Prompt configuration DataFrame  
- `extraction_data`: Dictionary of extracted content by tag
- `api_progress`: Progress tracking for batch operations
- `last_saved`: Timestamp of last save operation

## Configuration and Security

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key
SHEETS_SERVICE_ACCOUNT_JSON=path_to_service_account.json
DEFAULT_MODEL=gpt-4.1
MAX_CONCURRENT_REQUESTS=5
```

### Secrets Management
```toml
# .streamlit/secrets.toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID"
type = "service_account"
project_id = "your_project_id"
private_key_id = "your_private_key_id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your_service_account@your_project.iam.gserviceaccount.com"
client_id = "your_client_id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your_service_account%40your_project.iam.gserviceaccount.com"

[openai]
api_key = "your_openai_api_key"
```

## Testing Strategy

### Unit Tests
- Google Sheets connection and CRUD operations
- OpenAI API integration and error handling
- XML parsing and extraction logic
- Session state management

### Integration Tests  
- End-to-end data flow from Sheets → AI → back to Sheets
- Multi-user concurrent access scenarios
- Large dataset performance testing
- API rate limiting and retry logic

### User Acceptance Tests
- Complete workflow from setup to results
- Error recovery scenarios
- Performance under realistic usage
- Security and data privacy validation

## Deployment Options

### Local Development
- Streamlit development server
- Local Google Sheets connection
- Environment-based configuration

### Cloud Deployment
- Streamlit Cloud hosting
- Secure secrets management
- Production Google Sheets integration
- Monitoring and logging setup

## Risk Mitigation

### API Rate Limiting
- Implement request queuing
- Exponential backoff with jitter
- User feedback for long operations
- Graceful degradation on failures

### Data Loss Prevention
- Automatic backups before AI operations
- Version history in Google Sheets
- Rollback capabilities
- Export functionality for data recovery

### Security Considerations
- Secure API key storage
- Google Sheets access controls
- Input validation and sanitization
- Rate limiting and abuse prevention

## Success Metrics

### Performance Targets
- Single prompt execution: < 10 seconds
- Batch processing: < 2 minutes for 100 rows
- Google Sheets sync: < 5 seconds for typical datasets
- UI responsiveness: < 1 second for all interactions

### Quality Targets
- API success rate: > 95%
- XML extraction accuracy: > 98%
- Data persistence reliability: > 99.9%
- User error recovery: < 30 seconds average

This implementation specification provides a comprehensive roadmap for building your AI-powered spreadsheet interface. The modular approach ensures each component can be developed and tested independently before integration.