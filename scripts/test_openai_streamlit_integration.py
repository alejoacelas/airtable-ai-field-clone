#!/usr/bin/env python3
"""Test integration between Streamlit app and AI processor."""

import asyncio
import pandas as pd
from ai_processor import (
    setup_openai_client,
    build_prompt_with_references, 
    execute_batch_prompts,
    PromptJob,
    extract_xml_content
)

async def simulate_spreadsheet_ai_workflow():
    """Simulate the complete workflow: data -> prompts -> AI -> extraction."""
    
    print("🧪 Simulating Spreadsheet AI Workflow")
    print("=" * 50)
    
    # Step 1: Sample spreadsheet data (like from Google Sheets)
    print("📊 Step 1: Sample Data")
    sample_data = pd.DataFrame({
        'name': ['Alice Johnson', 'Bob Smith', 'Carol Davis'],
        'age': [25, 35, 28],
        'occupation': ['Data Scientist', 'Teacher', 'Doctor'],
        'city': ['New York', 'Boston', 'Chicago'],
        'analysis': ['', '', '']  # This will be filled by AI
    })
    
    print(sample_data)
    print()
    
    # Step 2: Prompt configuration (like from prompt config table)
    print("🎯 Step 2: Prompt Configuration")
    prompt_template = """
    Analyze this person's profile:
    Name: {name}
    Age: {age}
    Occupation: {occupation}
    Location: {city}
    
    Provide your analysis in this format:
    <reasoning>Your analytical process</reasoning>
    <answer>Key insights about this person</answer>
    <sources>Assumptions made</sources>
    """
    
    print("Template:", prompt_template[:100] + "...")
    print()
    
    # Step 3: Build prompts with data substitution
    print("🔧 Step 3: Building Prompts")
    jobs = []
    for index, row in sample_data.iterrows():
        # Convert row to dict for template substitution
        row_dict = row.to_dict()
        
        # Build prompt with column references
        filled_prompt = build_prompt_with_references(prompt_template, row_dict)
        
        # Create job for batch processing
        job = PromptJob(
            row_index=index,
            column_name='analysis',
            prompt=filled_prompt,
            needs_search=False
        )
        jobs.append(job)
        
        print(f"Row {index} prompt: {filled_prompt[:80]}...")
    
    print()
    
    # Step 4: Execute AI batch processing
    print("🤖 Step 4: AI Processing")
    try:
        client, model = setup_openai_client()
        
        def progress_callback(completed, total):
            print(f"   Progress: {completed}/{total} completed")
        
        results = await execute_batch_prompts(
            client=client,
            model=model, 
            jobs=jobs,
            max_concurrent_requests=2,
            progress_callback=progress_callback
        )
        
        print(f"✅ Processed {len(results)} rows")
        print()
        
    except Exception as e:
        print(f"❌ AI processing failed: {e}")
        return False
    
    # Step 5: Update spreadsheet data with results
    print("📝 Step 5: Updating Data")
    for result in results:
        if result.error:
            print(f"❌ Row {result.row_index}: {result.error}")
            sample_data.at[result.row_index, 'analysis'] = 'ERROR'
        else:
            # Store the full AI response
            sample_data.at[result.row_index, 'analysis'] = result.text
            print(f"✅ Row {result.row_index}: Updated with {len(result.text)} characters")
    
    print()
    print("Updated data:")
    print(sample_data[['name', 'occupation', 'city']]) # Show key columns
    print()
    
    # Step 6: Extract XML content for tabs
    print("🏷️  Step 6: XML Extraction for Tabs")
    extraction_tabs = {
        'reasoning': [],
        'answer': [],
        'sources': []
    }
    
    for index, row in sample_data.iterrows():
        analysis_text = row['analysis']
        if analysis_text and analysis_text != 'ERROR':
            extracted = extract_xml_content(analysis_text, ['reasoning', 'answer', 'sources'])
            
            for tag, content in extracted.items():
                extraction_tabs[tag].append({
                    'row_id': index,
                    'name': row['name'],
                    'content': content
                })
    
    # Display extracted content (like in Streamlit tabs)
    for tab_name, extractions in extraction_tabs.items():
        print(f"\n📋 {tab_name.upper()} Tab:")
        for item in extractions:
            print(f"   Row {item['row_id']} ({item['name']}): {item['content'][:100]}...")
    
    print()
    print("🎉 Workflow simulation complete!")
    return True

async def test_column_references():
    """Test various column reference formats."""
    print("\n🔗 Testing Column References")
    print("-" * 30)
    
    test_data = {
        'name': 'John Doe',
        'age': '30',
        'city': 'San Francisco',
        'notes': ''  # Empty field
    }
    
    test_cases = [
        "Hello {name} from {city}!",
        "Age: {{age}} years old",
        "Info: {name} is {age:unknown} from {city:somewhere}",
        "Notes: {notes:No notes available}",
        "Complex: {name} ({age}) lives in {city} - Notes: {notes:None}"
    ]
    
    print("Test data:", test_data)
    print()
    
    for i, template in enumerate(test_cases, 1):
        result = build_prompt_with_references(template, test_data)
        print(f"Test {i}:")
        print(f"  Template: {template}")
        print(f"  Result:   {result}")
        print()
    
    return True

async def main():
    """Run integration tests."""
    tests = [
        ("Column References", test_column_references),
        ("Full Workflow Simulation", simulate_spreadsheet_ai_workflow)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("=" * 60)
        try:
            await test_func()
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
    
    print("\n✅ Integration testing complete!")

if __name__ == "__main__":
    asyncio.run(main())