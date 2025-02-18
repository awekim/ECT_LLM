import pandas as pd
import re
import os

base_dir = "I:/Data_for_practice/ECT2001_2021/"
output_base_dir = "I:/Data_for_practice/ECT2001_2021_df/"

def extract_date_from_filename(filename):
    match = re.search(r"(\d{4}-[A-Za-z]{3}-\d{2})", filename)
    return match.group(1) if match else "Unknown Date"

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

def process_transcript(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = file.read()

    participants_data = []
    category = None   
    current_name = None  

    for line in data.split("\n"):
        line = line.strip()
        
        if "Corporate Participants" in line:
            category = "Corporate Participants"
        elif "Conference Call Participants" in line:
            category = "Conference Call Participants"
        
        elif line.startswith("*"):
            current_name = line[1:].strip()
            participants_data.append([current_name, "", "", category])
    
    df_par = pd.DataFrame(participants_data, columns=['Name', 'Organization', 'Title', 'Category'])
    
    lines = data.split("\n")
    sections = extract_sections(lines)

    structured_data = []
    current_speaker = None
    current_position = None
    speech = []

    for section in sections:
        if "Presentation" in section[0] or "Questions and Answers" in section[0]:
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

    df = pd.DataFrame(structured_data, columns=["Speaker", "Position", "Speech"])
    extracted_date = extract_date_from_filename(os.path.basename(file_path))
    df['Date'] = extracted_date

    df["Speech"] = df["Speech"].apply(lambda x: re.sub(r'\[\d+\]', '', x).strip())
    df["Position"] = df["Position"].apply(lambda x: re.sub(r'\[:digit:{1,}]', '', str(x)).strip())
    df["Position"] = df["Position"].apply(lambda x: re.sub(r'\[\d+\]', '', x).strip())

    definitions_index = df[df["Speech"].str.contains("Definitions")].index
    if not definitions_index.empty:
        df = df.iloc[:definitions_index[0]]

    df = df[df["Speech"].str.strip() != ""]
    return df, df_par

if __name__ == "__main__":
    for year in range(2001, 2022):
        year_dir = os.path.join(base_dir, str(year))
        output_year_dir = os.path.join(output_base_dir, str(year))
        os.makedirs(output_year_dir, exist_ok=True)
        
        if os.path.exists(year_dir):
            for file_name in os.listdir(year_dir):
                if file_name.endswith(".txt"):
                    file_path = os.path.join(year_dir, file_name)
                    df, df_par = process_transcript(file_path)
                    output_name = file_name.replace(".txt", ".csv")
                    df.to_csv(os.path.join(output_year_dir, output_name), index=False)
                    df_par_output_name = file_name.replace(".txt", "_participants.csv")
                    df_par.to_csv(os.path.join(output_year_dir, df_par_output_name), index=False)
                    print(f"Processed {file_name} -> {output_name}, {df_par_output_name}")

