import streamlit as st
import pandas as pd
from sheets_manager import SheetsManager
from datetime import datetime
import logging

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
        
    if "main_data" not in st.session_state:
        st.session_state.main_data = pd.DataFrame()
        
    if "prompt_config" not in st.session_state:
        st.session_state.prompt_config = pd.DataFrame()
        
    if "extraction_data" not in st.session_state:
        st.session_state.extraction_data = {}
        
    if "api_progress" not in st.session_state:
        st.session_state.api_progress = {}
        
    if "last_saved" not in st.session_state:
        st.session_state.last_saved = None
        
    if "sheets_connected" not in st.session_state:
        st.session_state.sheets_connected = False

def setup_sheets_connection():
    """Set up Google Sheets connection."""
    if not st.session_state.sheets_connected:
        with st.spinner("Connecting to Google Sheets..."):
            if st.session_state.sheets_manager.initialize_connection():
                if st.session_state.sheets_manager.validate_sheet_structure():
                    st.session_state.sheets_connected = True
                    st.success("✅ Connected to Google Sheets")
                    
                    # Load existing data
                    st.session_state.main_data = st.session_state.sheets_manager.load_main_data()
                    st.session_state.prompt_config = st.session_state.sheets_manager.load_prompt_config()
                    
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
        st.warning("AI processing not yet implemented")
    
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
            # Save main data
            if not st.session_state.main_data.empty:
                if st.session_state.sheets_manager.save_main_data(st.session_state.main_data):
                    st.success("✅ Main data saved")
                else:
                    st.error("❌ Failed to save main data")
                    return
            
            # Save prompt configuration
            if not st.session_state.prompt_config.empty:
                if st.session_state.sheets_manager.save_prompt_config(st.session_state.prompt_config):
                    st.success("✅ Prompt configuration saved")
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
            st.session_state.main_data = st.session_state.sheets_manager.load_main_data()
            st.session_state.prompt_config = st.session_state.sheets_manager.load_prompt_config()
            
        st.success("✅ Data loaded from Google Sheets")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

def render_prompt_configuration():
    """Render prompt configuration table."""
    st.subheader("🎯 Prompt Configuration")
    
    # Get column names from main data (excluding system columns)
    if not st.session_state.main_data.empty:
        available_columns = [col for col in st.session_state.main_data.columns 
                           if not col.startswith('_')]
    else:
        available_columns = ["sample_column"]
    
    # Initialize prompt config if empty
    if st.session_state.prompt_config.empty:
        st.session_state.prompt_config = pd.DataFrame({
            "column_name": available_columns,
            "prompt_text": ["LOCKED"] * len(available_columns),
            "replace_mode": [False] * len(available_columns),
            "web_search": [False] * len(available_columns),
            "is_active": [True] * len(available_columns)
        })
    
    # Update config if new columns are added
    existing_columns = set(st.session_state.prompt_config["column_name"].tolist())
    new_columns = [col for col in available_columns if col not in existing_columns]
    
    if new_columns:
        new_config = pd.DataFrame({
            "column_name": new_columns,
            "prompt_text": ["LOCKED"] * len(new_columns),
            "replace_mode": [False] * len(new_columns),
            "web_search": [False] * len(new_columns),
            "is_active": [True] * len(new_columns)
        })
        st.session_state.prompt_config = pd.concat([st.session_state.prompt_config, new_config], 
                                                 ignore_index=True)
    
    # Display editable configuration
    config_editor = st.data_editor(
        st.session_state.prompt_config,
        column_config={
            "column_name": st.column_config.SelectboxColumn(
                "Column Name",
                options=available_columns,
                required=True
            ),
            "prompt_text": st.column_config.TextColumn(
                "Prompt Text",
                help="Enter your prompt or 'LOCKED' to skip",
                max_chars=1000
            ),
            "replace_mode": st.column_config.CheckboxColumn(
                "Replace All",
                help="Replace all values vs fill empty cells only"
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
        use_container_width=True
    )
    
    st.session_state.prompt_config = config_editor

def render_main_data_editor():
    """Render main data editor."""
    st.subheader("📊 Data Editor")
    
    # Initialize with sample data if empty
    if st.session_state.main_data.empty:
        st.session_state.main_data = pd.DataFrame({
            "_id": [1, 2, 3],
            "_created_at": [datetime.now().isoformat()] * 3,
            "_updated_at": [datetime.now().isoformat()] * 3,
            "sample_column": ["Sample data 1", "Sample data 2", "Sample data 3"]
        })
    
    # Display only non-system columns for editing
    display_columns = [col for col in st.session_state.main_data.columns 
                      if not col.startswith('_')]
    
    if display_columns:
        display_data = st.session_state.main_data[display_columns].copy()
        
        edited_data = st.data_editor(
            display_data,
            num_rows="dynamic",
            use_container_width=True,
            key="main_data_editor"
        )
        
        # Update main data with edited values
        for col in display_columns:
            st.session_state.main_data[col] = edited_data[col]
        
        # Update row count and system columns
        current_rows = len(edited_data)
        original_rows = len(st.session_state.main_data)
        
        if current_rows != original_rows:
            # Adjust DataFrame size
            if current_rows > original_rows:
                # Add new rows
                new_rows = current_rows - original_rows
                new_data = {
                    "_id": list(range(original_rows + 1, current_rows + 1)),
                    "_created_at": [datetime.now().isoformat()] * new_rows,
                    "_updated_at": [datetime.now().isoformat()] * new_rows
                }
                for col in display_columns:
                    new_data[col] = edited_data[col].iloc[original_rows:].tolist()
                
                new_df = pd.DataFrame(new_data)
                st.session_state.main_data = pd.concat([
                    st.session_state.main_data.iloc[:original_rows],
                    new_df
                ], ignore_index=True)
                
            else:
                # Remove rows
                st.session_state.main_data = st.session_state.main_data.iloc[:current_rows].copy()
                for col in display_columns:
                    st.session_state.main_data[col] = edited_data[col]
        
        # Update timestamps for modified rows
        st.session_state.main_data["_updated_at"] = datetime.now().isoformat()
    
    else:
        st.info("No data columns available. Add some data to get started!")

def render_extraction_tabs():
    """Render extraction tabs for XML content."""
    extraction_tabs = ["Sources", "Reasoning", "Annotations", "Answer"]
    
    tabs = st.tabs(extraction_tabs)
    
    for i, (tab, tag_name) in enumerate(zip(tabs, extraction_tabs)):
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
    
    # Main content tabs
    main_tab, *extraction_tabs = st.tabs(["Main Data"] + ["Sources", "Reasoning", "Annotations", "Answer"])
    
    with main_tab:
        # Prompt configuration
        render_prompt_configuration()
        
        st.divider()
        
        # Main data editor
        render_main_data_editor()
    
    # Extraction tabs
    extraction_tab_names = ["sources", "reasoning", "annotations", "answer"]
    for tab, tag_name in zip(extraction_tabs, extraction_tab_names):
        with tab:
            if tag_name in st.session_state.extraction_data and not st.session_state.extraction_data[tag_name].empty:
                st.dataframe(
                    st.session_state.extraction_data[tag_name],
                    use_container_width=True
                )
            else:
                st.info(f"No {tag_name} extractions yet. Run AI prompts to populate this tab.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit and Google Sheets API*")

if __name__ == "__main__":
    main()