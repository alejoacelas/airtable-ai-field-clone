# Testing Guide - AI Spreadsheet Interface

## Pre-Testing Setup

### 1. Create a Google Sheet for Testing

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new blank spreadsheet
3. Name it "AI Spreadsheet Test" or similar
4. Copy the spreadsheet ID from the URL (the long string between `/d/` and `/edit`)
   - Example URL: `https://docs.google.com/spreadsheets/d/1abc123def456.../edit`
   - Sheet ID: `1abc123def456...`

### 2. Share Sheet with Service Account

1. In your Google Sheet, click "Share" (top right)
2. Add this email as an editor: `leep-airtable-clone@gen-lang-client-0925934161.iam.gserviceaccount.com`
3. Make sure "Editor" permissions are selected
4. Click "Send" (no notification needed)
5. **Copy the share link** from the address bar or "Copy link" button

### 3. Update Configuration

1. Edit `.streamlit/secrets.toml`
2. Replace `YOUR_GOOGLE_SHEETS_SHARE_LINK_HERE` with your share link:

```toml
spreadsheet = "https://docs.google.com/spreadsheets/d/1abc123def456.../edit?usp=sharing"
```

**Note:** You can paste ANY of these formats:
- Full share link: `https://docs.google.com/spreadsheets/d/1abc123.../edit?usp=sharing`
- Edit link: `https://docs.google.com/spreadsheets/d/1abc123.../edit#gid=0`  
- Just the ID: `1abc123def456...`

The app will automatically extract the sheet ID!

### 4. Install Dependencies

```bash
cd /Users/alejo/Code/airtable-clone
pip install -r requirements.txt
```

## Testing Phase 1: Basic Connection & Structure

### Test 1: Launch Application

```bash
streamlit run app.py
```

**Expected Results:**
- ✅ Streamlit app opens in browser (usually `http://localhost:8501`)
- ✅ Title shows "📊 AI Spreadsheet Interface"
- ✅ Sidebar shows connection status
- ✅ Main area has tabs: "Main Data", "Sources", "Reasoning", "Annotations", "Answer"

**Troubleshooting:**
- If import errors occur, run `pip install -r requirements.txt` again
- If Google Sheets connection fails, verify the service account email was added as editor

### Test 2: Google Sheets Connection

**Expected Results:**
- ✅ Sidebar shows "🟢 Google Sheets Connected"
- ✅ If connection fails, shows "🔴 Not Connected" with retry button
- ✅ Link to open spreadsheet appears in sidebar (if connected)

**What to Check in Google Sheets:**
- ✅ New worksheets should be automatically created:
  - `Main_Data`
  - `Prompt_Config`
  - `Extract_Sources`
  - `Extract_Reasoning`
  - `Extract_Annotations`
  - `Extract_Answer`

### Test 3: Initial Data Display

**Expected Results:**
- ✅ Prompt Configuration table shows with sample columns
- ✅ Main Data Editor shows sample data (3 rows with sample_column)
- ✅ Data editor allows adding/deleting rows
- ✅ Extraction tabs show "No extractions yet" messages

## Testing Phase 2: Data Management

### Test 4: Edit Data in Data Editor

1. In the "Main Data" tab, click in the data editor
2. Modify existing sample data
3. Add new rows using the "+" button
4. Delete rows using the "🗑️" icon

**Expected Results:**
- ✅ Changes are immediately reflected in the interface
- ✅ New rows get automatic IDs and timestamps
- ✅ Session state persists changes during page interactions

### Test 5: Configure Prompts

1. In the Prompt Configuration table:
2. Change "LOCKED" to a custom prompt like "Analyze this data: {sample_column}"
3. Toggle the "Replace All" checkbox
4. Enable/disable "Web Search" option
5. Toggle "Active" status

**Expected Results:**
- ✅ All changes are saved in session state
- ✅ Column references (e.g., `{sample_column}`) are preserved
- ✅ Configuration updates immediately

### Test 6: Save to Google Sheets

1. Click "💾 Save to Sheets" in the sidebar
2. Check your Google Sheet in the browser

**Expected Results:**
- ✅ "✅ Main data saved" and "✅ Prompt configuration saved" messages appear
- ✅ Data appears in the `Main_Data` worksheet with system columns:
  - `_id`, `_created_at`, `_updated_at`, `sample_column`, and any custom columns
- ✅ Prompt config appears in `Prompt_Config` worksheet
- ✅ Timestamps are automatically added/updated
- ✅ "Last saved" time appears in sidebar

### Test 7: Load from Google Sheets

1. Manually edit some data directly in your Google Sheet
2. Return to the Streamlit app
3. Click "🔄 Load from Sheets"

**Expected Results:**
- ✅ "✅ Data loaded from Google Sheets" message
- ✅ Manual changes from Google Sheets appear in the app
- ✅ Page refreshes to show updated data

### Test 8: Add Custom Columns

1. In the data editor, add a new column by typing in the header
2. Add some sample data to the new column
3. Save to Google Sheets
4. Check the Prompt Configuration table

**Expected Results:**
- ✅ New column appears in data editor
- ✅ New column automatically appears in Prompt Configuration with default settings
- ✅ New column is saved to Google Sheets
- ✅ Column can be configured with custom prompts

## Testing Phase 3: Error Handling & Edge Cases

### Test 9: Connection Recovery

1. Temporarily revoke access to the Google Sheet
2. Try to save data
3. Re-grant access
4. Click "🔄 Retry Connection"

**Expected Results:**
- ✅ Clear error messages when connection fails
- ✅ Retry button works to restore connection
- ✅ App gracefully handles connection issues

### Test 10: Large Data Sets

1. Add many rows (try 50-100) to test performance
2. Save to Google Sheets
3. Load from Google Sheets

**Expected Results:**
- ✅ App remains responsive with larger datasets
- ✅ Save/load operations complete successfully
- ✅ Data integrity maintained

### Test 11: Special Characters & Data Types

1. Add data with special characters, emojis, line breaks
2. Test with numeric data, dates, booleans
3. Save and reload

**Expected Results:**
- ✅ Special characters preserved
- ✅ Data types handled correctly
- ✅ No data corruption during save/load cycles

## Testing Phase 4: UI/UX Validation

### Test 12: Tab Navigation

1. Click through all tabs: Main Data, Sources, Reasoning, Annotations, Answer
2. Verify content in each tab

**Expected Results:**
- ✅ Smooth tab switching
- ✅ Extraction tabs show appropriate "no data" messages
- ✅ Main Data tab shows all components correctly

### Test 13: Responsive Design

1. Resize browser window
2. Test on different screen sizes if possible

**Expected Results:**
- ✅ Interface adapts to different screen sizes
- ✅ Tables remain usable at various widths
- ✅ Sidebar functionality preserved

### Test 14: Session Persistence

1. Make changes to data
2. Navigate between tabs
3. Refresh the page (F5)

**Expected Results:**
- ✅ Data persists across tab navigation
- ✅ **Note:** Data will be lost on page refresh (this is expected - data should be saved to Sheets for persistence)

## Success Criteria Summary

✅ **Phase 1 Foundation Complete** if all these work:
- Google Sheets connection established
- Data editor with add/delete functionality
- Prompt configuration table
- Save/load to Google Sheets
- Session state management
- Basic error handling
- Multi-tab interface

## Common Issues & Solutions

### Issue: "Could not connect to Google Sheets"
**Solution:** 
- Verify service account email is added as editor to your sheet
- Check that the spreadsheet ID in secrets.toml is correct
- Ensure the sheet is not private/restricted

### Issue: "Module not found" errors
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Data not saving to Google Sheets
**Solution:**
- Check browser console for errors
- Verify sheet permissions
- Try creating a fresh Google Sheet

### Issue: Interface doesn't load properly
**Solution:**
- Clear browser cache
- Try incognito/private browsing mode
- Check browser console for JavaScript errors

## Next Steps After Testing

Once Phase 1 testing is complete, the foundation will be ready for:
- **Phase 2**: OpenAI API integration
- **Phase 3**: Batch processing and XML extraction
- **Phase 4**: Advanced features and optimization

---

**Note:** This testing covers Phase 1 functionality only. AI prompt execution will be available in Phase 2.