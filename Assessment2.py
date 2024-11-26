import streamlit as st
import os
from openai import OpenAI
import tempfile
import time
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def get_openai_client():
    """Initialize OpenAI client with API key from .env file"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("No OpenAI API key found in .env file. Please check your configuration.")
        st.stop()
    return OpenAI(api_key=api_key)

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'agreement_text' not in st.session_state:
        st.session_state.agreement_text = ""
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = {}
    if 'progress' not in st.session_state:
        st.session_state.progress = 0

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {str(e)}")
        return None

def analyze_agreement(client, text):
    """Analyze rental agreement using OpenAI API"""
    try:
        prompt = f"""Analyze the following rental agreement and extract key information:
        Text: {text[:2000]}...
        Please extract:
        1. Rental property address
        2. Monthly rent amount
        3. Lease term
        4. Security deposit amount
        5. Tenant names
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        return None

def validate_terms(client, text):
    """Validate rental agreement terms"""
    try:
        prompt = f"""Review the following rental agreement terms and identify any potential issues:
        Text: {text[:2000]}...
        Check for:
        1. Fair housing compliance
        2. Legal rent increase provisions
        3. Security deposit regulations
        4. Maintenance responsibilities
        5. Privacy rights
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error during validation: {str(e)}")
        return None

def generate_summary(client, text):
    """Generate summary of rental agreement"""
    try:
        prompt = f"""Create a plain language summary of this rental agreement:
        Text: {text[:2000]}...
        Include:
        1. Key dates and deadlines
        2. Main tenant responsibilities
        3. Landlord obligations
        4. Important restrictions
        5. Termination conditions
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return None

def suggest_modifications(client, text):
    """Suggest modifications to the agreement"""
    try:
        prompt = f"""Review this rental agreement and suggest potential modifications to protect both parties:
        Text: {text[:2000]}...
        Consider:
        1. Clarity improvements
        2. Additional protections needed
        3. Modern considerations (e.g., remote work, etc.)
        4. Local law compliance
        5. Dispute resolution procedures
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error suggesting modifications: {str(e)}")
        return None

def create_download_report(report_content):
    """Create a formatted text report"""
    report = []
    report.append("=" * 50)
    report.append("RENTAL AGREEMENT ANALYSIS REPORT")
    report.append("=" * 50)
    report.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for section, content in report_content.items():
        report.append("\n" + "=" * 30)
        report.append(section.upper())
        report.append("=" * 30 + "\n")
        report.append(content)
        report.append("\n")
    
    return "\n".join(report)

def main():
    st.title("Rental Agreement Analyzer")
    initialize_session_state()
    
    # Initialize OpenAI client
    client = get_openai_client()
    
    # Progress bar
    progress_text = "Operation in progress. Please wait."
    if st.session_state.progress > 0:
        progress_bar = st.progress(st.session_state.progress / 100, text=progress_text)
    
    # Step 1: Upload Document
    if st.session_state.current_step == 0:
        st.header("Step 1: Upload Rental Agreement")
        st.info("Please upload your rental agreement PDF file to begin analysis.")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None:
            with st.spinner('Processing document...'):
                text = extract_text_from_pdf(uploaded_file)
                if text:
                    st.success("Document uploaded and processed successfully!")
                    st.session_state.agreement_text = text
                    st.session_state.current_step = 1
                    st.session_state.progress = 20
                    time.sleep(1)
                    st.rerun()
    
    # Step 2: Initial Analysis
    elif st.session_state.current_step == 1:
        st.header("Step 2: Initial Analysis")
        with st.spinner('Analyzing agreement...'):
            analysis = analyze_agreement(client, st.session_state.agreement_text)
            if analysis:
                st.success("Analysis completed!")
                st.session_state.processed_data['analysis'] = analysis
                st.write(analysis)
                st.session_state.current_step = 2
                st.session_state.progress = 40
                if st.button("Continue to Validation"):
                    st.rerun()
    
    # Step 3: Legal Validation
    elif st.session_state.current_step == 2:
        st.header("Step 3: Legal Validation")
        with st.spinner('Validating terms...'):
            validation = validate_terms(client, st.session_state.agreement_text)
            if validation:
                st.success("Validation completed!")
                st.session_state.processed_data['validation'] = validation
                st.write(validation)
                st.session_state.current_step = 3
                st.session_state.progress = 60
                if st.button("Continue to Summary"):
                    st.rerun()
    
    # Step 4: Generate Summary
    elif st.session_state.current_step == 3:
        st.header("Step 4: Summary Generation")
        with st.spinner('Generating summary...'):
            summary = generate_summary(client, st.session_state.agreement_text)
            if summary:
                st.success("Summary generated!")
                st.session_state.processed_data['summary'] = summary
                st.write(summary)
                st.session_state.current_step = 4
                st.session_state.progress = 80
                if st.button("Continue to Final Report"):
                    st.rerun()
    
    # Step 5: Final Report
    elif st.session_state.current_step == 4:
        st.header("Step 5: Final Report")
        with st.spinner('Preparing final report...'):
            modifications = suggest_modifications(client, st.session_state.agreement_text)
            if modifications:
                final_report_data = {
                    'Initial Analysis': st.session_state.processed_data['analysis'],
                    'Legal Validation': st.session_state.processed_data['validation'],
                    'Summary': st.session_state.processed_data['summary'],
                    'Recommendations': modifications
                }

                try:
                    # Generate report content
                    report_content = create_download_report(final_report_data)
                    
                    st.success("Final report ready!")
                    st.session_state.progress = 100
                    
                    # Display report preview
                    st.write("### Report Preview")
                    for section, content in final_report_data.items():
                        with st.expander(f"{section}"):
                            st.write(content)
                    
                    # Add download button
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"rental_agreement_analysis_{timestamp}.txt"
                    st.download_button(
                        label="Download Report",
                        data=report_content,
                        file_name=filename,
                        mime="text/plain"
                    )
                    
                    if st.button("Start New Analysis"):
                        st.session_state.current_step = 0
                        st.session_state.progress = 0
                        st.session_state.agreement_text = ""
                        st.session_state.processed_data = {}
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")

if __name__ == "__main__":
    main()
