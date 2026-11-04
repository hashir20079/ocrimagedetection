@app.route('/upload', methods=['POST'])
def upload_file():
    if 'report_image' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['report_image']
    
    # Get the API key directly from the form input field
    user_api_key = request.form.get('api_key', '').strip()
    
    # If the user didn't enter a key, stop and show an error
    if not user_api_key:
        return "<h3>Error:</h3><p>Please enter your Gemini API key in the form.</p><br><a href='/'>Back</a>", 400
    
    if file.filename == '':
        return "No selected file", 400
        
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            # Configure Gemini using the key provided by the user
            genai.configure(api_key=user_api_key)
            img = Image.open(filepath)
            
            # Exhaustive prompt for field service reports
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
            
            # Future-proof model selection fallback loop
            models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
            response = None
            last_exception = None
            
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content([img, prompt])
                    break 
                except Exception as model_err:
                    last_exception = model_err
                    continue
            
            if response is None:
                raise last_exception
                
            html_receipt = markdown.markdown(response.text)
            return render_template('upload.html', extracted_data=html_receipt)
            
        except Exception as e:
            return f"<h3>Error processing image with AI:</h3><p>{str(e)}</p><br><a href='/'>Back</a>"
