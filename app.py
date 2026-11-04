import os
import io
from flask import Flask, render_template, request
import google.generativeai as genai
import markdown
from PIL import Image

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'report_image' not in request.files:
            return "Error: No file part in request.", 400
        
        file = request.files['report_image']
        user_api_key = request.form.get('api_key', '').strip()
        
        if not user_api_key:
            return "Error: Please paste your Gemini API key into the form field.", 400
        
        if file.filename == '':
            return "Error: No image selected for upload.", 400
            
        # Read image securely into memory (never saves to server disk, vanishes on refresh)
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))
        
        # Configure Gemini with user-provided key
        genai.configure(api_key=user_api_key)
        
        prompt = """
        Analyze this handwritten field service report completely.
        1. Automatically detect and extract the Client Name / Category (e.g., UBL, HBL BANK, etc.) from the report.
        2. Transcribe every single detail visible on the form into a thorough receipt breakdown. Include:
           - Detected Client Category / Name
           - Report Header Info (Complaint #, Date, In/Out Times)
           - Customer Information (Customer Name, Address, Contact Person, Cell Number, Branch Code)
           - UPS Condition Section (Working Load %, PM Done, Rating, Pieces, Ch.V, UPS C.B Input Amps, Out/P Amps, Stabilizer, Isolation)
           - Site Condition Section (UPS Input/Output Volts, Neutral/Earth Volts, Genset Rating & O/V, Frequency, Environment)
           - Action Taken Section (Installation details, Checked boxes, Received boxes, UPS/Battery/AVR/Isolation models and serial numbers)
           - Details of Work / Issues Found (Full text)
           - Customer Remarks (Full text)
           - Signatures & Names (Customer Rep Name, Engineer Name)
        
        Do not skip any field, numbers, or cell numbers. Present all extracted data cleanly.
        """
        
        # Using stable gemini-1.5-flash to eliminate version/deprecation 404 errors
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([img, prompt])
        
        html_receipt = markdown.markdown(response.text)
        return render_template('upload.html', extracted_data=html_receipt)
        
    except Exception as e:
        # This catches any crash and prints the exact reason on your screen instead of a blank 500 error
        return f"<h3>Application Error Caught:</h3><p style='color:red;'>{str(e)}</p><br><a href='/'>← Go Back</a>", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
