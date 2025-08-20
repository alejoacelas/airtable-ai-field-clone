import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import logging
import re
from typing import Optional, Dict, List, Any

class SheetsManager:
    """Manages Google Sheets connection and data operations."""
    
    def __init__(self):
        self.conn: Optional[GSheetsConnection] = None
        self.spreadsheet_url: Optional[str] = None
        self.spreadsheet_id: Optional[str] = None
        self.worksheets = {
            "main_data": "Main",
            "prompt_config": "Prompt_Config", 
            "extract_sources": "Sources",
            "extract_reasoning": "Reasoning",
            "extract_annotations": "Annotations",
            "extract_answer": "Answer"
        }
    
    @staticmethod
    def extract_sheet_id(url_or_id: str) -> str:
        """Extract sheet ID from various Google Sheets URL formats or return ID if already provided."""
        # Remove whitespace
        url_or_id = url_or_id.strip()
        
        # If it's already just an ID (no slashes), return as-is
        if '/' not in url_or_id and len(url_or_id) > 20:
            return url_or_id
            
        # Pattern to match Google Sheets URLs and extract the ID
        patterns = [
            # Standard sharing URL: https://docs.google.com/spreadsheets/d/SHEET_ID/edit...
            r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)',
            # Alternative format: https://docs.google.com/spreadsheets/d/SHEET_ID
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            # Just the ID part
            r'^([a-zA-Z0-9-_]{20,})$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        # If no pattern matches, assume it's already an ID or invalid
        return url_or_id
        
    def initialize_connection(self) -> bool:
        """Initialize Google Sheets connection."""
        try:
            self.conn = st.connection("gsheets", type=GSheetsConnection)
            
            # Get spreadsheet URL/ID from secrets (supports both [connections.gsheets] and [gsheets])
            raw_spreadsheet = None
            try:
                if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
                    cg = st.secrets["connections"]["gsheets"]
                    if "spreadsheet" in cg:
                        raw_spreadsheet = cg["spreadsheet"]
                if raw_spreadsheet is None and "gsheets" in st.secrets and "spreadsheet" in st.secrets["gsheets"]:
                    raw_spreadsheet = st.secrets["gsheets"]["spreadsheet"]
            except Exception:
                # Secrets access can fail outside Streamlit runtime; allow connection to exist
                raw_spreadsheet = None

            if raw_spreadsheet:
                # Extract sheet ID from URL or use as-is if already an ID
                self.spreadsheet_id = self.extract_sheet_id(str(raw_spreadsheet))
                # Store both the original input and create a proper URL
                self.spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
                return True
            else:
                # Even if we cannot read the spreadsheet here, the connection may still be valid
                st.warning("Google Sheets spreadsheet ID not found in secrets; connection created but URL is unset.")
                return True
                
        except Exception as e:
            st.error(f"Failed to initialize Google Sheets connection: {str(e)}")
            logging.error(f"Sheets connection error: {str(e)}")
            return False
    
    def validate_sheet_structure(self) -> bool:
        """Validate that required worksheets exist with proper structure."""
        if not self.conn:
            return False
            
        try:
            # Check if main worksheets exist
            for worksheet_key, worksheet_name in self.worksheets.items():
                try:
                    df = self.conn.read(worksheet=worksheet_name, ttl=0)
                    logging.info(f"Worksheet '{worksheet_name}' exists")
                except Exception:
                    # Create worksheet if it doesn't exist
                    self._create_worksheet(worksheet_name, worksheet_key)
                    
            return True
            
        except Exception as e:
            st.error(f"Failed to validate sheet structure: {str(e)}")
            return False
    
    def _create_worksheet(self, worksheet_name: str, worksheet_key: str):
        """Create a new worksheet with appropriate structure."""
        if worksheet_key == "main_data":
            # Create main data worksheet
            initial_data = pd.DataFrame({
                "sample_column": []
            })
        elif worksheet_key == "prompt_config":
            # Create prompt configuration worksheet
            initial_data = pd.DataFrame({
                "column_name": [],
                "prompt_text": [],
                "replace_mode": [],
                "web_search": [],
                "is_active": []
            })
        else:
            # Create extraction worksheets with same structure as main data
            initial_data = pd.DataFrame({
                "sample_column": []
            })
            
        try:
            # Use create method to create new worksheet, fallback to update if worksheet exists
            try:
                self.conn.create(worksheet=worksheet_name, data=initial_data)
                logging.info(f"Created new worksheet: {worksheet_name}")
                st.success(f"Created worksheet: {worksheet_name}")
                # Clear cache to ensure fresh data after creation
                st.cache_data.clear()
            except Exception as create_error:
                # If create fails, try update (worksheet might already exist but be empty)
                logging.warning(f"Create failed for {worksheet_name}, trying update: {str(create_error)}")
                self.conn.update(worksheet=worksheet_name, data=initial_data)
                logging.info(f"Updated existing worksheet: {worksheet_name}")
                
        except Exception as e:
            logging.error(f"Failed to create/update worksheet {worksheet_name}: {str(e)}")
            st.error(f"Failed to create worksheet {worksheet_name}: {str(e)}")
    
    def load_main_data(self) -> pd.DataFrame:
        """Load main data from Google Sheets."""
        if not self.conn:
            return pd.DataFrame()
            
        try:
            df = self.conn.read(worksheet=self.worksheets["main_data"], ttl=0)
            
            # No system columns needed
                
            return df
            
        except Exception as e:
            st.warning(f"Could not load existing data: {str(e)}")
            # Return empty DataFrame
            return pd.DataFrame()
    
    def load_prompt_config(self) -> pd.DataFrame:
        """Load prompt configuration from Google Sheets."""
        if not self.conn:
            return pd.DataFrame()
            
        try:
            df = self.conn.read(worksheet=self.worksheets["prompt_config"], ttl=0)
            
            # Convert boolean columns from float to boolean
            if not df.empty:
                boolean_columns = ['replace_mode', 'web_search', 'is_active']
                for col in boolean_columns:
                    if col in df.columns:
                        df[col] = df[col].astype(bool)
            
            return df
            
        except Exception as e:
            st.warning(f"Could not load prompt configuration: {str(e)}")
            return pd.DataFrame({
                "column_name": [],
                "prompt_text": [],
                "replace_mode": [],
                "web_search": [],
                "is_active": []
            })
    
    def save_main_data(self, data: pd.DataFrame) -> bool:
        """Save main data to Google Sheets."""
        if not self.conn:
            st.error("No Google Sheets connection available")
            return False
            
        try:
            self.conn.update(worksheet=self.worksheets["main_data"], data=data)
            return True
            
        except Exception as e:
            st.error(f"Failed to save data: {str(e)}")
            logging.error(f"Save error: {str(e)}")
            return False
    
    def save_prompt_config(self, config: pd.DataFrame) -> bool:
        """Save prompt configuration to Google Sheets."""
        if not self.conn:
            st.error("No Google Sheets connection available")
            return False
            
        try:
            self.conn.update(worksheet=self.worksheets["prompt_config"], data=config)
            return True
            
        except Exception as e:
            st.error(f"Failed to save prompt configuration: {str(e)}")
            return False
    
    def save_extraction_data(self, tag_type: str, data: pd.DataFrame) -> bool:
        """Save extracted content to appropriate worksheet."""
        if not self.conn:
            return False
            
        worksheet_key = f"extract_{tag_type.lower()}"
        if worksheet_key not in self.worksheets:
            # Create new extraction worksheet for custom tags
            self.worksheets[worksheet_key] = f"Extract_{tag_type.title()}"
            self._create_worksheet(self.worksheets[worksheet_key], worksheet_key)
        
        try:
            # Add extraction timestamp
            data["extraction_date"] = datetime.now().isoformat()
            
            self.conn.update(worksheet=self.worksheets[worksheet_key], data=data)
            return True
            
        except Exception as e:
            st.error(f"Failed to save {tag_type} extractions: {str(e)}")
            return False
    
    def load_extraction_data(self, tag_type: str) -> pd.DataFrame:
        """Load extracted content from specified worksheet."""
        if not self.conn:
            return pd.DataFrame()
            
        worksheet_key = f"extract_{tag_type.lower()}"
        if worksheet_key not in self.worksheets:
            return pd.DataFrame()
            
        try:
            df = self.conn.read(worksheet=self.worksheets[worksheet_key], ttl=0)
            return df
            
        except Exception as e:
            st.warning(f"Could not load {tag_type} extractions: {str(e)}")
            return pd.DataFrame()
    
    def create_backup(self, data: pd.DataFrame, suffix: str = "") -> bool:
        """Create a backup of current data before making changes."""
        if not self.conn:
            return False
            
        try:
            backup_name = f"Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
            self.conn.update(worksheet=backup_name, data=data)
            logging.info(f"Created backup: {backup_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create backup: {str(e)}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and info."""
        status = {
            "connected": self.conn is not None,
            "spreadsheet_url": self.spreadsheet_url,
            "worksheets": list(self.worksheets.values()) if self.conn else [],
            "last_check": datetime.now().isoformat()
        }
        
        if self.conn:
            try:
                # Test connection by reading a small amount of data
                _ = self.conn.read(
                    worksheet=self.worksheets["main_data"],
                    ttl=0,
                    usecols=[0],
                    nrows=1
                )
                status["test_read_success"] = True
            except Exception as e:
                status["test_read_success"] = False
                status["error"] = str(e)
        
        return status
