#!/usr/bin/env python3
"""Test script to validate OpenAI API integration using ai_processor.py."""

import asyncio
import sys
from ai_processor import (
    setup_openai_client,
    execute_single_prompt,
    build_prompt_with_references,
    extract_xml_content,
    PromptJob,
    execute_batch_prompts
)

async def test_basic_connection():
    """Test basic OpenAI connection and simple prompt."""
    print("🔌 Testing OpenAI connection...")
    
    try:
        client, model = setup_openai_client()
        print(f"✅ Client initialized successfully")
        print(f"📋 Using model: {model}")
        
        # Simple test prompt
        test_prompt = "Say 'Hello from OpenAI!' and nothing else."
        
        response = await execute_single_prompt(
            client=client,
            prompt=test_prompt,
            model=model
        )
        
        print(f"🤖 Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_prompt_templating():
    """Test prompt templating with column references."""
    print("\n🎯 Testing prompt templating...")
    
    # Sample row data
    row_data = {
        "name": "John Doe",
        "age": "30", 
        "city": "San Francisco",
        "occupation": "Software Engineer"
    }
    
    # Test different template formats
    templates = [
        "Analyze this person: {name} is {age} years old from {city}.",
        "Profile: {{name}} works as {{occupation}} in {{city}}.",
        "Bio: {name} is {age:unknown age} from {city:unknown city}.",
        "Summary for {name:Anonymous}: Age {age}, Location {city}, Job {occupation:Unemployed}"
    ]
    
    for i, template in enumerate(templates, 1):
        result = build_prompt_with_references(template, row_data)
        print(f"Template {i}: {template}")
        print(f"Result {i}:   {result}")
        print()
    
    return True

async def test_xml_extraction():
    """Test XML content extraction from responses."""
    print("🏷️  Testing XML extraction...")
    
    # Mock AI response with XML tags
    mock_response = """
    Here's my analysis:
    
    <reasoning>
    The user appears to be a tech professional based in San Francisco.
    Given the age and location, they likely work in the startup ecosystem.
    </reasoning>
    
    <answer>
    John Doe is a 30-year-old Software Engineer from San Francisco.
    </answer>
    
    <sources>
    Based on provided profile information.
    </sources>
    """
    
    tags_to_extract = ["reasoning", "answer", "sources", "annotations"]
    extracted = extract_xml_content(mock_response, tags_to_extract)
    
    for tag, content in extracted.items():
        print(f"📝 {tag.upper()}:")
        if content:
            print(f"   {content}")
        else:
            print(f"   (not found)")
        print()
    
    return True

async def test_ai_with_xml_response():
    """Test actual AI call with XML-structured response."""
    print("🤖 Testing AI with XML response format...")
    
    try:
        client, model = setup_openai_client()
        
        prompt = """
        Analyze this data: A 25-year-old data scientist named Alice from New York.
        
        Please provide your response in this format:
        
        <reasoning>Your analysis process</reasoning>
        <answer>Your main conclusion</answer>
        <sources>Any assumptions made</sources>
        """
        
        response = await execute_single_prompt(
            client=client,
            prompt=prompt,
            model=model
        )
        
        print(f"🤖 Full Response:")
        print(response)
        print("\n" + "="*50)
        
        # Extract XML content
        tags = ["reasoning", "answer", "sources"]
        extracted = extract_xml_content(response, tags)
        
        print("📊 Extracted Content:")
        for tag, content in extracted.items():
            print(f"\n🏷️  {tag.upper()}:")
            print(f"   {content if content else '(empty)'}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI test failed: {e}")
        return False

async def test_batch_processing():
    """Test batch processing with multiple prompts."""
    print("\n⚡ Testing batch processing...")
    
    try:
        client, model = setup_openai_client()
        
        # Create sample jobs
        jobs = [
            PromptJob(
                row_index=0,
                column_name="analysis",
                prompt="Analyze: Software Engineer, 30, San Francisco",
                needs_search=False
            ),
            PromptJob(
                row_index=1,
                column_name="analysis", 
                prompt="Analyze: Teacher, 35, Boston",
                needs_search=False
            ),
            PromptJob(
                row_index=2,
                column_name="analysis",
                prompt="Analyze: Doctor, 40, Chicago", 
                needs_search=False
            )
        ]
        
        print(f"📋 Processing {len(jobs)} jobs...")
        
        def progress_callback(completed, total):
            print(f"   Progress: {completed}/{total}")
        
        results = await execute_batch_prompts(
            client=client,
            model=model,
            jobs=jobs,
            max_concurrent_requests=2,
            progress_callback=progress_callback
        )
        
        print(f"\n📊 Batch Results:")
        for result in results:
            if result.error:
                print(f"❌ Row {result.row_index}: {result.error}")
            else:
                print(f"✅ Row {result.row_index}: {result.text[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 OpenAI AI Processor Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Prompt Templating", test_prompt_templating),
        ("XML Extraction", test_xml_extraction),
        ("AI with XML Response", test_ai_with_xml_response),
        ("Batch Processing", test_batch_processing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 30)
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! OpenAI integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and API key.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())