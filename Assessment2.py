import streamlit as st
import os
from openai import OpenAI
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("No OpenAI API key found in .env file.")
        st.stop()
    return OpenAI(api_key=api_key)

def initialize_session_state():
    if 'step' not in st.session_state:
        st.session_state.step = 0
    if 'text' not in st.session_state:
        st.session_state.text = None
    if 'results' not in st.session_state:
        st.session_state.results = {}
    if 'show_download' not in st.session_state:
        st.session_state.show_download = False

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def get_example_files():
    examples_dir = "test_files"
    if os.path.exists(examples_dir):
        return [f for f in os.listdir(examples_dir) if f.endswith('.pdf')]
    return []

def analyze_with_gpt(client, prompt, text):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\nText: {text[:2000]}..."
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error with GPT analysis: {str(e)}")
        return None

def create_report(results):
    report = []
    report.append("=" * 50)
    report.append("RENTAL AGREEMENT ANALYSIS REPORT")
    report.append("=" * 50)
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for title, content in results.items():
        report.append("\n" + "=" * 30)
        report.append(title.upper())
        report.append("=" * 30 + "\n")
        report.append(content)
        report.append("\n")
    
    return "\n".join(report)

def main():
    st.title("Rental Agreement Analyzer")
    initialize_session_state()
    client = get_openai_client()

    # File Upload Section
    if st.session_state.text is None:
        st.header("Document Upload")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Example files
            example_files = get_example_files()
            if example_files:
                example = st.selectbox(
                    "Select an example file",
                    ["Choose a file..."] + example_files
                )
                if example != "Choose a file...":
                    with open(os.path.join("test_files", example), 'rb') as f:
                        text = extract_text_from_pdf(f)
                        if text:
                            st.session_state.text = text
                            st.success(f"Example file loaded: {example}")
        
        with col2:
            # File uploader
            uploaded_file = st.file_uploader("Or upload your own PDF", type="pdf")
            if uploaded_file:
                text = extract_text_from_pdf(uploaded_file)
                if text:
                    st.session_state.text = text
                    st.success("File uploaded successfully!")

    # Analysis Section
    if st.session_state.text is not None:
        steps = {
            "Initial Analysis": {
                "prompt": """Analyze this rental agreement and extract:
                1. Rental property address
                2. Monthly rent amount
                3. Lease term
                4. Security deposit amount
                5. Tenant names""",
                "key": "analysis"
            },
            "Legal Validation": {
                "prompt": """Check for potential legal issues regarding:
                1. Fair housing compliance
                2. Legal rent increase provisions
                3. Security deposit regulations
                4. Maintenance responsibilities
                5. Privacy rights""",
                "key": "validation"
            },
            "Summary": {
                "prompt": """Create a plain language summary including:
                1. Key dates and deadlines
                2. Main tenant responsibilities
                3. Landlord obligations
                4. Important restrictions
                5. Termination conditions""",
                "key": "summary"
            },
            "Recommendations": {
                "prompt": """Suggest improvements considering:
                1. Clarity improvements
                2. Additional protections needed
                3. Modern considerations
                4. Legal compliance
                5. Dispute resolution""",
                "key": "recommendations"
            }
        }

        # Process each step
        for title, info in steps.items():
            with st.expander(f"{title}", expanded=True):
                if info["key"] not in st.session_state.results:
                    progress_placeholder = st.empty()
                    progress_placeholder.info(f"Processing {title.lower()}...")
                    result = analyze_with_gpt(client, info["prompt"], st.session_state.text)
                    if result:
                        st.session_state.results[info["key"]] = result
                        progress_placeholder.empty()  # Clear progress message
                        st.success(f"{title} completed!")
                        st.write(result)
                else:
                    st.success(f"{title} completed!")
                    st.write(st.session_state.results[info["key"]])

        # Show results and download section
        if len(st.session_state.results) == len(steps):
            st.session_state.show_download = True

        if st.session_state.show_download:
            st.header("Analysis Complete")
            
            # Download section in a container
            with st.container():
                report_content = create_report(st.session_state.results)
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.download_button(
                        "📥 Download Complete Report",
                        report_content,
                        file_name=f"rental_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key="download_btn"
                    )
                
                with col2:
                    if st.button("🔄 Start New Analysis"):
                        st.session_state.clear()
                        st.rerun()

if __name__ == "__main__":
    main()
