import fitz
import docx
import io
import string
import random

#------------------------------User_Id-Generator----------------------------#
def generate_unique_id():
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=8))

#-------------------------------to_snake_case-------------------------------#
def to_snake_case(col):
    return col.strip().replace(" ", "_").lower()
#-----------------------Campaign-Template-Validator-------------------------#
def validate_template(template: str, campaign_columns: list[str]) -> list[str]:
    errors = []
    try:
        # Check balanced braces
        open_braces = template.count('{')
        close_braces = template.count('}')
        if open_braces != close_braces:
              errors.append(f"Unmatched braces: {{ count = {open_braces} vs }} count = {close_braces}")

        # Extract placeholders
        formatter = string.Formatter()
        placeholders = {field_name for _, field_name, _, _ in formatter.parse(template) if field_name}

        # Find placeholders not in columns
        for ph in placeholders:
                if ph not in campaign_columns:
                        errors.append(f"Placeholder {{{ph}}} is not in campaign_columns")
        return errors
    except Exception as e:
        errors.append(f"error in validate_template function: {str(e)}")

#---------------------------------------------------------------------------#
# Extract text from in-memory .txt
def extract_text_from_txt(file_stream):
    return file_stream.read().decode('utf-8')

# Extract text from in-memory .pdf
def extract_text_from_pdf(file_stream):
    text = ""
    with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# Extract text from in-memory .docx
def extract_text_from_docx(file_stream):
    doc = docx.Document(io.BytesIO(file_stream.read()))
    return " ".join([para.text for para in doc.paragraphs])