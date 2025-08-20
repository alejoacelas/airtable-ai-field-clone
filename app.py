import streamlit as st
import pandas as pd
from sheets_manager import SheetsManager
from datetime import datetime
import logging
import asyncio
from typing import Dict, List, Any
from ai_processor import (
    setup_openai_client,
    build_prompt_with_references,
    execute_batch_prompts,
    PromptJob,
    PromptResult
)
from response_parser import validate_response_structure, extract_tags_from_dataframe

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="AI Spreadsheet Interface",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables."""
    if "sheets_manager" not in st.session_state:
        st.session_state.sheets_manager = SheetsManager()
        
    if "sheets_main_data" not in st.session_state:
        st.session_state.sheets_main_data = pd.DataFrame()
        
    if "sheets_prompt_config" not in st.session_state:
        st.session_state.sheets_prompt_config = pd.DataFrame()
        
    if "editor_main_data" not in st.session_state:
        st.session_state.editor_main_data = pd.DataFrame()
        
    if "editor_prompt_config" not in st.session_state:
        st.session_state.editor_prompt_config = pd.DataFrame()
        
        
    if "api_progress" not in st.session_state:
        st.session_state.api_progress = {}
        
    if "last_saved" not in st.session_state:
        st.session_state.last_saved = None
        
    if "sheets_connected" not in st.session_state:
        st.session_state.sheets_connected = False


def get_current_main_data() -> pd.DataFrame:
    """Get the most current version of main data (editor version if available, else sheets version)."""
    # If editor version has content, use it
    if hasattr(st.session_state, 'editor_main_data') and not st.session_state.editor_main_data.empty:
        return st.session_state.editor_main_data
    # Otherwise use sheets version
    if hasattr(st.session_state, 'sheets_main_data'):
        return st.session_state.sheets_main_data
    # Fallback to empty DataFrame
    return pd.DataFrame()


def get_current_prompt_config() -> pd.DataFrame:
    """Get the most current version of prompt config (editor version if available, else sheets version)."""
    # If editor version has content, use it
    if hasattr(st.session_state, 'editor_prompt_config') and not st.session_state.editor_prompt_config.empty:
        return st.session_state.editor_prompt_config
    # Otherwise use sheets version
    if hasattr(st.session_state, 'sheets_prompt_config'):
        return st.session_state.sheets_prompt_config
    # Fallback to empty DataFrame
    return pd.DataFrame()


def setup_sheets_connection():
    """Set up Google Sheets connection."""
    if not st.session_state.sheets_connected:
        with st.spinner("Connecting to Google Sheets..."):
            if st.session_state.sheets_manager.initialize_connection():
                if st.session_state.sheets_manager.validate_sheet_structure():
                    st.session_state.sheets_connected = True
                    st.success("✅ Connected to Google Sheets")
                    
                    # Load existing data
                    st.session_state.sheets_main_data = st.session_state.sheets_manager.load_main_data()
                    st.session_state.sheets_prompt_config = st.session_state.sheets_manager.load_prompt_config()
                    # Initialize editor versions with loaded data
                    st.session_state.editor_main_data = st.session_state.sheets_main_data.copy()
                    st.session_state.editor_prompt_config = st.session_state.sheets_prompt_config.copy()
                    
                else:
                    st.error("❌ Failed to validate sheet structure")
            else:
                st.error("❌ Failed to connect to Google Sheets")

def render_connection_status():
    """Render connection status in sidebar."""
    st.sidebar.header("📋 Connection Status")
    
    if st.session_state.sheets_connected:
        st.sidebar.success("🟢 Google Sheets Connected")
        
        # Show connection details
        status = st.session_state.sheets_manager.get_connection_status()
        if status.get("spreadsheet_url"):
            st.sidebar.write(f"📊 [Open Spreadsheet]({status['spreadsheet_url']})")
            
        if st.session_state.last_saved:
            st.sidebar.write(f"💾 Last saved: {st.session_state.last_saved}")
            
    else:
        st.sidebar.error("🔴 Not Connected")
        if st.sidebar.button("🔄 Retry Connection"):
            setup_sheets_connection()
            st.rerun()

def render_control_panel():
    """Render control panel in sidebar."""
    st.sidebar.header("🎛️ Control Panel")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("💾 Save to Sheets", disabled=not st.session_state.sheets_connected):
            save_all_data()
            
    with col2:
        if st.button("🔄 Load from Sheets", disabled=not st.session_state.sheets_connected):
            load_all_data()
    
    if st.button("🚀 Run AI Prompts", disabled=not st.session_state.sheets_connected):
        run_ai_prompts()
    
    # Configuration options
    st.sidebar.subheader("⚙️ Configuration")
    
    # XML tags configuration
    st.sidebar.write("**XML Tags to Extract:**")
    default_tags = ["sources", "reasoning", "annotations", "answer"]
    
    for tag in default_tags:
        st.sidebar.checkbox(tag.title(), value=True, key=f"extract_{tag}")

def save_all_data():
    """Save all data to Google Sheets."""
    try:
        with st.spinner("Saving to Google Sheets..."):
            # Use editor versions as the source of truth for saving
            editor_main_data = get_current_main_data()
            editor_prompt_config = get_current_prompt_config()
            
            # Save main data
            if not editor_main_data.empty:
                if st.session_state.sheets_manager.save_main_data(editor_main_data):
                    st.success("✅ Main data saved")
                    # Update sheets version with saved data
                    st.session_state.sheets_main_data = editor_main_data.copy()
                else:
                    st.error("❌ Failed to save main data")
                    return
            
            # Save prompt configuration  
            if not editor_prompt_config.empty:
                if st.session_state.sheets_manager.save_prompt_config(editor_prompt_config):
                    st.success("✅ Prompt configuration saved")
                    # Update sheets version with saved data
                    st.session_state.sheets_prompt_config = editor_prompt_config.copy()
                else:
                    st.error("❌ Failed to save prompt configuration")
                    return
            
            st.session_state.last_saved = datetime.now().strftime("%H:%M:%S")
            
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")

def load_all_data():
    """Load all data from Google Sheets."""
    try:
        with st.spinner("Loading from Google Sheets..."):
            st.session_state.sheets_main_data = st.session_state.sheets_manager.load_main_data()
            st.session_state.sheets_prompt_config = st.session_state.sheets_manager.load_prompt_config()
            # Update editor versions with loaded data
            st.session_state.editor_main_data = st.session_state.sheets_main_data.copy()
            st.session_state.editor_prompt_config = st.session_state.sheets_prompt_config.copy()
            
            # No extraction data loading needed - extracted on-demand from main data
            
        st.success("✅ Data loaded from Google Sheets")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")


def run_ai_prompts():
    """Execute AI prompts on the configured columns."""
    try:
        # Get current data versions
        current_main_data = get_current_main_data()
        current_prompt_config = get_current_prompt_config()
        
        # Validate we have data and configuration
        if current_main_data.empty:
            st.error("No data to process. Please add some data first.")
            return
            
        if current_prompt_config.empty:
            st.error("No prompt configuration found. Please configure prompts first.")
            return
        
        # Get active prompts (not "LOCKED" and is_active=True)
        active_prompts = current_prompt_config[
            (current_prompt_config['prompt_text'] != 'LOCKED') &
            (current_prompt_config['is_active'] == True)
        ]
        
        if active_prompts.empty:
            st.warning("No active prompts found. Please configure at least one active prompt.")
            return
        
        # Run the async processing
        with st.spinner("Initializing AI processing..."):
            asyncio.run(process_prompts_async(active_prompts))
            
    except Exception as e:
        st.error(f"Error running AI prompts: {str(e)}")
        logging.error(f"AI prompt error: {str(e)}")


async def process_prompts_async(active_prompts: pd.DataFrame):
    """Process prompts asynchronously with progress tracking."""
    try:
        # Setup OpenAI client
        client, model = setup_openai_client()
        
        # Build jobs for each row and active column
        jobs = []
        main_data = get_current_main_data().copy()
        
        for _, prompt_config in active_prompts.iterrows():
            column_name = prompt_config['column_name']
            prompt_template = prompt_config['prompt_text']
            replace_mode = prompt_config.get('replace_mode', False)
            web_search = prompt_config.get('web_search', False)
            
            # Skip if column doesn't exist in main data
            if column_name not in main_data.columns:
                continue
                
            for idx, row in main_data.iterrows():
                    # Skip if not in replace mode and cell already has content
                if not replace_mode and pd.notna(row[column_name]) and str(row[column_name]).strip():
                    continue
                
                # Build prompt with column references
                row_values = row.to_dict()
                final_prompt = build_prompt_with_references(prompt_template, row_values)
                
                job = PromptJob(
                    row_index=idx,
                    column_name=column_name,
                    prompt=final_prompt,
                    needs_search=web_search
                )
                jobs.append(job)
        
        if not jobs:
            st.warning("No prompts to process. Check your configuration and data.")
            return
            
        # Setup progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(completed: int, total: int):
            progress = completed / total if total > 0 else 0
            progress_bar.progress(progress)
            status_text.text(f"Processing... {completed}/{total} completed")
        
        # Execute batch prompts
        status_text.text(f"Starting batch processing of {len(jobs)} prompts...")
        results = await execute_batch_prompts(
            client=client,
            model=model,
            jobs=jobs,
            progress_callback=update_progress
        )
        
        # Process results
        await process_ai_results(results)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"✅ Completed processing {len(results)} prompts!")
        
        # Auto-save results to sheets
        save_all_data()
        
        # Refresh the app to show new data
        st.rerun()
        
    except Exception as e:
        st.error(f"Error in async processing: {str(e)}")
        logging.error(f"Async processing error: {str(e)}")


async def process_ai_results(results: List[PromptResult]):
    """Process AI results and update data structures."""
    # Process each result
    for result in results:
        if result.error:
            # Handle errors - could show in UI or log
            logging.warning(f"Error in row {result.row_index}, column {result.column_name}: {result.error}")
            continue
            
        if not result.text.strip():
            continue
            
        # Update editor main data with result
        st.session_state.editor_main_data.loc[result.row_index, result.column_name] = result.text
    
    # Save extraction data to Google Sheets for each tag type
    current_main_data = st.session_state.editor_main_data
    if not current_main_data.empty:
        for tag_name in ["sources", "reasoning", "annotations", "answer"]:
            extracted_df = extract_tags_from_dataframe(current_main_data, tag_name)
            # Only save if there's content
            has_content = False
            for col in extracted_df.columns:
                if extracted_df[col].astype(str).str.strip().ne('').any():
                    has_content = True
                    break
            if has_content:
                st.session_state.sheets_manager.save_extraction_data(tag_name, extracted_df)

def render_prompt_configuration():
    """Render prompt configuration table."""
    st.subheader("🎯 Prompt Configuration")
    
    # Get column names from current main data
    current_main_data = get_current_main_data()
    if not current_main_data.empty:
        available_columns = list(current_main_data.columns)
    else:
        available_columns = ["sample_column"]
    
    # Initialize editor prompt config if empty
    if st.session_state.editor_prompt_config.empty:
        st.session_state.editor_prompt_config = pd.DataFrame({
            "column_name": available_columns,
            "prompt_text": ["LOCKED"] * len(available_columns),
            "replace_mode": [False] * len(available_columns),
            "web_search": [False] * len(available_columns),
            "is_active": [True] * len(available_columns)
        })
    
    # Update config if new columns are added
    existing_columns = set(st.session_state.editor_prompt_config["column_name"].tolist())
    new_columns = [col for col in available_columns if col not in existing_columns]
    
    if new_columns:
        new_config = pd.DataFrame({
            "column_name": new_columns,
            "prompt_text": ["LOCKED"] * len(new_columns),
            "replace_mode": [False] * len(new_columns),
            "web_search": [False] * len(new_columns),
            "is_active": [True] * len(new_columns)
        })
        st.session_state.editor_prompt_config = pd.concat([st.session_state.editor_prompt_config, new_config], 
                                                 ignore_index=True)
    
    # Display editable configuration
    edited_config = st.data_editor(
        st.session_state.editor_prompt_config,
        column_config={
            "column_name": st.column_config.SelectboxColumn(
                "Column Name",
                options=available_columns,
                required=True
            ),
            "prompt_text": st.column_config.TextColumn(
                "Prompt Text",
                help="Enter your prompt or 'LOCKED' to skip",
                max_chars=None,
                width="large"
            ),
            "replace_mode": st.column_config.CheckboxColumn(
                "Replace All",
                help="Replace all values vs fill empty columns only"
            ),
            "web_search": st.column_config.CheckboxColumn(
                "Web Search",
                help="Enable web search in API calls"
            ),
            "is_active": st.column_config.CheckboxColumn(
                "Active",
                help="Include this prompt in batch processing"
            )
        },
        hide_index=True,
        use_container_width=True,
        key="prompt_config_editor"
    )
    
    # Update editor_prompt_config from editor directly
    st.session_state.editor_prompt_config = edited_config
    
    # Return current prompt config
    return st.session_state.editor_prompt_config

def render_main_data_editor():
    """Render main data editor."""
    st.subheader("📊 Data Editor")
    
    # Initialize with sample data if empty
    if st.session_state.editor_main_data.empty and st.session_state.sheets_main_data.empty:
        st.session_state.editor_main_data = pd.DataFrame({
            "sample_column": ["Sample data 1", "Sample data 2", "Sample data 3"]
        })
    
    # Use current main data for display
    current_data = get_current_main_data()
    
    # Convert all columns to string to prevent type enforcement
    display_data = current_data.copy()
    for col in display_data.columns:
        display_data[col] = display_data[col].astype(str)
    
    edited_data = st.data_editor(
        display_data,
        num_rows="dynamic", 
        use_container_width=True,
        key="main_data_editor"
    )
    
    # Update editor version with changes
    st.session_state.editor_main_data = edited_data
    
    return edited_data

def render_extraction_tabs():
    """Render extraction tabs for XML content."""
    extraction_tabs = ["Sources", "Reasoning", "Annotations", "Answer"]
    
    tabs = st.tabs(extraction_tabs)
    
    for tab, tag_name in zip(tabs, extraction_tabs):
        with tab:
            tag_key = tag_name.lower()
            
            if tag_key in st.session_state.extraction_data and not st.session_state.extraction_data[tag_key].empty:
                st.dataframe(
                    st.session_state.extraction_data[tag_key],
                    use_container_width=True
                )
            else:
                st.info(f"No {tag_name.lower()} extractions yet. Run AI prompts to populate this tab.")

def main():
    """Main application function."""
    
    # Initialize session state
    initialize_session_state()
    
    # App header
    st.title("📊 AI Spreadsheet Interface")
    st.markdown("*Connect, analyze, and extract insights from your data using AI*")
    
    # Setup connection
    setup_sheets_connection()
    
    # Sidebar
    render_connection_status()
    render_control_panel()
    
    # Prompt configuration (outside tabs)
    render_prompt_configuration()
    
    st.divider()
    
    # Main content tabs
    tabs_list = ["Main Data", "Sources", "Reasoning", "Annotations", "Answer"]
    main_tab, sources_tab, reasoning_tab, annotations_tab, answer_tab = st.tabs(tabs_list)

    with main_tab:
        # Main data editor
        render_main_data_editor()

    # Extraction tabs
    extraction_tabs_data = [
        (sources_tab, "sources"),
        (reasoning_tab, "reasoning"),
        (annotations_tab, "annotations"),
        (answer_tab, "answer")
    ]

    for tab, tag_name in extraction_tabs_data:
        with tab:
            # Get current main data and extract tag content
            current_main_data = get_current_main_data()
            if not current_main_data.empty:
                # Extract tag content from main data
                extracted_df = extract_tags_from_dataframe(current_main_data, tag_name)
                
                # Only show if there's actual extracted content
                has_content = False
                for col in extracted_df.columns:
                    if extracted_df[col].astype(str).str.strip().ne('').any():
                        has_content = True
                        break
                
                if has_content:
                    st.dataframe(
                        extracted_df,
                        use_container_width=True
                    )
                else:
                    st.info(f"No {tag_name} extractions yet. Run AI prompts to populate this tab.")
            else:
                st.info(f"No {tag_name} extractions yet. Run AI prompts to populate this tab.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit and Google Sheets API*")

if __name__ == "__main__":
    main()
