# Forensic Report AI Project

## Overview
Ye ek Flask web application hai jisme forensic/postmortem reports (PDF/TXT) upload kar ke unka text extract karke forensic details aur NLP based named entities dikhaye jaate hain. Extracted data SQLite DB me save hota hai.

## Features
- Upload forensic/postmortem reports PDF ya TXT format me.
- Automatic text extraction using pdfplumber aur file read.
- Postmortem report content validation keywords ki madad se.
- Natural Language Processing ke zariye forensic entities extraction.
- SQLite me report archive aur browsing ki facility.
- Live animated matrix-style background UI.

## Installation

1. Repository clone karo:
git clone <repo_url>
cd forensic_report_ai_project

2. Virtual environment banao aur activate karo:
python3 -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows

3. Required packages install karo:
pip install -r requirements.txt

4. SpaCy model download karo (agar pehle se install nahi kiya hai):
python -m spacy download en_core_web_sm

5. `.env` file banao jo environment variables rakhe (sample niche diya gaya hai).

6. Flask app run karo:

7. Browser me jao aur URL access karo:  
[http://localhost:8080](http://localhost:8080)

## Project Structure

forensic_report_ai_project/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── utils/
│   │   └── nlp_utils.py
│   ├── templates/
│   │   ├── index.html
│   │   ├── result.html
│   │   ├── report_detail.html
│   │   └── reports_list.html
│   └── uploads/
├── data/
│   └── forensic_reports.db
├── requirements.txt
├── README.md
├── config.yaml
└── .env


## Usage

- Report upload karo, extracted forensic info dekho.
- Saved reports ka list aur unke detail dekho.
- UI me forensic-themed background animation enjoy karo.

## Contributing

Issues aur pull requests welcome hain.  
Feature requests aur bug reports ke liye repo issues use karo.

## License

MIT License

