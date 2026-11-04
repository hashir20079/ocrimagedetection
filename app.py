import os
from flask import Flask, render_template, request
import google.generativeai as genai
import markdown
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'report_image' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['report_image']
    
    # Grab the API key inputted by the user from the form
    user_api_key = request.form.get('api_key', '').strip()
    
    # Fallback to environment variable if the input field was left blank
    active_api_key = user_api_key if user_api_key else os.environ.get("GEMINI_API_KEY")
    
    if not active_api_key or active_api_key == "YOUR_GEMINI_API_KEY":
        return "<h3>Error:</h3><p>Gemini API Key is missing. Please enter your API key in the form or set it in your environment variables.</p><br><a href='/'>Back</a>", 400
    
    if file.filename == '':
        return "No selected file", 400
        
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            # Configure Gemini dynamically with the active API key for this request
            genai.configure(api_key=active_api_key)
            img = Image.open(filepath)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Exhaustive prompt to automatically detect client and extract all fields
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
            
            response = model.generate_content([img, prompt])
            html_receipt = markdown.markdown(response.text)
            
            return render_template('upload.html', extracted_data=html_receipt)
            
        except Exception as e:
            return f"<h3>Error processing image with AI:</h3><p>{str(e)}</p><br><a href='/'>Back</a>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
