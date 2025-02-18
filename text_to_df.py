import os
import re
import pandas as pd

# Function to process each file
def text_to_df(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = file.read()
        
    # Extract sections from the lines
    lines = data.split("\n")
    sections = extract_sections(lines)

    # Define a function to extract structured data from the text
    def extract_sections(lines):
        sections = []
        section = []
        for line in lines:
            if line.startswith("==="):
                if section:
                    sections.append(section)
                    section = []
            else:
                section.append(line.strip())
        if section:
            sections.append(section)
        return sections

    # Extract sections from the lines
    sections = extract_sections(lines)

    # Extract structured data from sections
    structured_data = []
    current_speaker = None
    current_position = None
    speech = []

    for section in sections:
        if "Participants" in section[0]:
            for i in range(1, len(section)):
                if section[i].startswith("*"):
                    current_speaker = section[i].replace("*", "").strip()
                    current_position = section[i+1].strip()
        elif "Presentation" in section[0] or "Questions and Answers" in section[0]:
            for line in section[1:]:
                if line.startswith("----"):
                    if current_speaker and speech:
                        structured_data.append([current_speaker, current_position, " ".join(speech)])
                        speech = []
                elif line.startswith("Operator"):
                    current_speaker = "Operator"
                    current_position = ""
                    speech = [line.replace("Operator", "").strip()]
                elif line.endswith("]"):
                    # Extract speaker and position
                    line_parts = line.split(",")
                    current_speaker = line_parts[0].split("  ")[-1].strip()
                    if len(line_parts) > 1:
                        current_position = line_parts[1].strip()
                    else:
                        current_position = ""
                else:
                    speech.append(line)
            if speech:
                structured_data.append([current_speaker, current_position, " ".join(speech)])
                speech = []
    
    # Extract date
    date_pattern = re.compile(r"([A-Z]+ \d{1,2}, \d{4})")
    date_match = date_pattern.search(data)
    if date_match:
        extracted_date = date_match.group(1)
    else:
        extracted_date = None
        
    # Convert structured data into a DataFrame
    df = pd.DataFrame(structured_data, columns=["Speaker", "Position", "Speech"])
    df['Date'] = extracted_date
    df["Speech"] = df["Speech"].apply(lambda x: re.sub(r'\[\d+\]', '', x).strip())
    df["Position"] = df["Position"].apply(lambda x: re.sub(r'\[\d+\]', '', x).strip())
    df[["Affiliation", "Position"]] = df["Position"].str.split(" - ", expand=True)
    df["Position"] = df["Position"].fillna("")

    # Drop all rows after the found index (including the row with "Definitions")
    definitions_index = df[df["Speech"].str.contains("Definitions")].index
    if not definitions_index.empty:
        df = df.iloc[:definitions_index[0]]

    # Remove empty rows
    df = df[df["Speech"].str.strip() != ""]

    # Rearrange columns
    df = df[['Date','Speaker','Affiliation','Position','Speech']]
    
    return df

# Main code
directory_path = "shareWithContainer/KHH/data/2021/"  
for file_name in os.listdir(directory_path):
    if file_name.endswith(".txt"):
        file_path = os.path.join(directory_path, file_name)
        df = process_file(file_path)
        output_name = file_name.replace(".txt", ".csv")
        df.to_csv(os.path.join(directory_path, output_name), index=False)