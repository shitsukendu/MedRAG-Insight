import os
import re
import faiss
import pandas as pd

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "medical_documents",
    "medlineplus_health_topics.csv"
)

FAISS_PATH = os.path.join(
    BASE_DIR,
    "vector_store",
    "medlineplus_index.faiss"
)


# ============================================================
# 2. LOAD MEDICAL KNOWLEDGE BASE
# ============================================================

medical_df = pd.read_csv(DATA_PATH)


# ============================================================
# 3. LOAD EMBEDDING MODEL
# ============================================================

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# 4. LOAD FAISS VECTOR DATABASE
# ============================================================

medlineplus_index = faiss.read_index(
    FAISS_PATH
)


# ============================================================
# 5. LOAD LANGUAGE MODEL
# ============================================================

model_name = "google/flan-t5-base"

tokenizer = AutoTokenizer.from_pretrained(
    model_name
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    model_name
)


# ============================================================
# 6. BACKEND STATUS
# ============================================================

print("MedRAG Insight backend loaded successfully!")
print("Medical topics:", len(medical_df))
print("FAISS vectors:", medlineplus_index.ntotal)


# ============================================================
# 7. PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text.strip()


# ============================================================
# 8. EXTRACT MEDICAL FINDINGS
# ============================================================

def extract_findings(report_text):

    # -------------------------
    # Age
    # -------------------------

    age_match = re.search(
        r"Age\s*:\s*(\d+)",
        report_text,
        re.IGNORECASE
    )


    # -------------------------
    # Blood Pressure
    # -------------------------

    bp_match = re.search(
        r"Blood Pressure\s*:\s*([\d/]+)",
        report_text,
        re.IGNORECASE
    )


    # -------------------------
    # Blood Glucose
    # -------------------------

    glucose_match = re.search(
        r"Blood Glucose\s*:\s*(\d+(?:\.\d+)?)",
        report_text,
        re.IGNORECASE
    )


    # -------------------------
    # Symptoms
    # -------------------------

    symptoms_match = re.search(
        r"(?:Clinical Information|Symptoms)\s*:\s*(.*)",
        report_text,
        re.IGNORECASE
    )


    age = (
        age_match.group(1)
        if age_match
        else "Not available"
    )


    blood_pressure = (
        bp_match.group(1)
        if bp_match
        else "Not available"
    )


    blood_glucose = (
        glucose_match.group(1)
        if glucose_match
        else "Not available"
    )


    symptoms = (
        symptoms_match.group(1).strip()
        if symptoms_match
        else "Not available"
    )


    findings = {

        "Age": age,

        "Symptoms": symptoms,

        "Blood Pressure": blood_pressure,

        "Blood Glucose": blood_glucose
    }


    return findings


# ============================================================
# 9. SEARCH MEDLINEPLUS
# ============================================================

def search_medlineplus(query, top_k=5):

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")


    distances, indices = medlineplus_index.search(
        query_embedding,
        top_k
    )


    results = []


    for rank, idx in enumerate(indices[0]):

        results.append({

            "rank": rank + 1,

            "title": medical_df.iloc[idx]["title"],

            "summary": medical_df.iloc[idx]["summary"],

            "also_called": medical_df.iloc[idx]["also_called"],

            "group": medical_df.iloc[idx]["group"],

            "primary_institute":
                medical_df.iloc[idx]["primary_institute"],

            "distance":
                float(distances[0][rank])
        })


    return results


# ============================================================
# 10. RETRIEVE CLINICAL KNOWLEDGE
# ============================================================

def retrieve_clinical_knowledge(
    findings,
    top_k=2
):

    clinical_fields = [

        "Symptoms",

        "Blood Pressure",

        "Blood Glucose"
    ]


    clinical_knowledge = {}


    for field in clinical_fields:

        value = findings.get(
            field,
            "Not available"
        )


        if value == "Not available":

            continue


        # -------------------------
        # Create search query
        # -------------------------

        if field == "Symptoms":

            query = value

        elif field == "Blood Pressure":

            query = f"blood pressure {value}"

        elif field == "Blood Glucose":

            query = f"blood glucose {value}"


        results = search_medlineplus(
            query,
            top_k=top_k
        )


        clinical_knowledge[field] = results


    return clinical_knowledge


# ============================================================
# 11. CLINICAL INTERPRETATION
# ============================================================

def interpret_clinical_findings(findings):

    interpretations = {}


    # ========================================================
    # BLOOD PRESSURE
    # ========================================================

    bp = findings.get(
        "Blood Pressure",
        "Not available"
    )


    if bp != "Not available" and "/" in bp:

        try:

            systolic, diastolic = map(
                int,
                bp.split("/")
            )


            if systolic >= 140 or diastolic >= 90:

                interpretations["Blood Pressure"] = (

                    f"The reported blood pressure is "
                    f"{bp} mmHg. "

                    "This reading is in a range that may "
                    "be considered high and may warrant "
                    "professional medical evaluation."
                )


            elif systolic >= 130 or diastolic >= 80:

                interpretations["Blood Pressure"] = (

                    f"The reported blood pressure is "
                    f"{bp} mmHg. "

                    "This reading is above the normal range "
                    "and may warrant discussion with a "
                    "healthcare professional."
                )


            else:

                interpretations["Blood Pressure"] = (

                    f"The reported blood pressure is "
                    f"{bp} mmHg."
                )


        except ValueError:

            interpretations["Blood Pressure"] = (

                f"The reported blood pressure is "
                f"{bp} mmHg."
            )


    # ========================================================
    # BLOOD GLUCOSE
    # ========================================================

    glucose = findings.get(
        "Blood Glucose",
        "Not available"
    )


    if glucose != "Not available":

        try:

            glucose_value = float(glucose)


            if glucose_value >= 126:

                interpretations["Blood Glucose"] = (

                    f"The reported blood glucose is "
                    f"{glucose} mg/dL. "

                    "Depending on how and when the test "
                    "was performed, this value may warrant "
                    "further medical evaluation. "

                    "A single result alone does not "
                    "establish a diagnosis."
                )


            elif glucose_value >= 100:

                interpretations["Blood Glucose"] = (

                    f"The reported blood glucose is "
                    f"{glucose} mg/dL. "

                    "The interpretation depends on whether "
                    "the test was fasting or non-fasting."
                )


            else:

                interpretations["Blood Glucose"] = (

                    f"The reported blood glucose is "
                    f"{glucose} mg/dL."
                )


        except ValueError:

            interpretations["Blood Glucose"] = (

                f"The reported blood glucose is "
                f"{glucose} mg/dL."
            )


    # ========================================================
    # SYMPTOMS
    # ========================================================

    symptoms = findings.get(
        "Symptoms",
        "Not available"
    )


    if symptoms != "Not available":

        interpretations["Symptoms"] = (

            f"Reported symptoms: {symptoms}. "

            "These symptoms can have different causes "
            "and should be interpreted in the appropriate "
            "clinical context."
        )


    return interpretations


# ============================================================
# 12. GENERATE RAG EXPLANATION
# ============================================================

def generate_report_rag_explanation(
    findings,
    clinical_knowledge
):

    context_parts = []


    for finding, results in clinical_knowledge.items():

        context_parts.append(

            f"Report Finding: "
            f"{finding}: "
            f"{findings[finding]}"
        )


        for result in results[:2]:

            context_parts.append(

                f"MedlinePlus Topic: "
                f"{result['title']}\n"

                f"Medical Information: "
                f"{result['summary']}"
            )


    context = "\n\n".join(
        context_parts
    )


    # ========================================================
    # RAG PROMPT
    # ========================================================

    prompt = f"""

You are a medical information assistant.

Analyze the provided medical report findings using ONLY
the MedlinePlus information provided below.

REPORT AND MEDICAL INFORMATION:

{context}

Instructions:

- Explain the reported findings in simple language.
- Clearly distinguish report values from general medical information.
- Do not diagnose any disease.
- Do not prescribe medication.
- Do not invent medical information.
- Do not make unsupported conclusions.
- If a finding may require professional evaluation,
  mention that.
- Keep the explanation concise and easy to understand.

Final Explanation:

"""


    # ========================================================
    # TOKENIZE
    # ========================================================

    inputs = tokenizer(

        prompt,

        return_tensors="pt",

        truncation=True,

        max_length=512
    )


    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    outputs = model.generate(

        **inputs,

        max_new_tokens=180,

        num_beams=5,

        no_repeat_ngram_size=3
    )


    # ========================================================
    # DECODE
    # ========================================================

    explanation = tokenizer.decode(

        outputs[0],

        skip_special_tokens=True
    )


    return explanation


# ============================================================
# 13. PREPARE TOP SOURCES
# ============================================================

def prepare_top_sources(
    clinical_knowledge
):

    sources = []


    for finding, results in clinical_knowledge.items():

        if len(results) > 0:

            top_result = results[0]


            sources.append({

                "finding": finding,

                "topic": top_result["title"],

                "source": "MedlinePlus",

                "distance":
                    top_result["distance"]
            })


    return sources


# ============================================================
# 14. COMPLETE REPORT ANALYSIS
# ============================================================

def analyze_report_with_rag(pdf_path):

    # --------------------------------------------------------
    # Step 1: Extract PDF text
    # --------------------------------------------------------

    report_text = extract_text_from_pdf(
        pdf_path
    )


    # --------------------------------------------------------
    # Step 2: Extract findings
    # --------------------------------------------------------

    findings = extract_findings(
        report_text
    )


    # --------------------------------------------------------
    # Step 3: Clinical interpretation
    # --------------------------------------------------------

    interpretations = interpret_clinical_findings(
        findings
    )


    # --------------------------------------------------------
    # Step 4: Retrieve medical knowledge
    # --------------------------------------------------------

    clinical_knowledge = retrieve_clinical_knowledge(

        findings,

        top_k=2
    )


    # --------------------------------------------------------
    # Step 5: Generate RAG explanation
    # --------------------------------------------------------

    rag_explanation = generate_report_rag_explanation(

        findings,

        clinical_knowledge
    )


    # --------------------------------------------------------
    # Step 6: Prepare sources
    # --------------------------------------------------------

    sources = prepare_top_sources(

        clinical_knowledge
    )


    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {

        "findings": findings,

        "interpretations": interpretations,

        "rag_explanation": rag_explanation,

        "sources": sources
    }


# ============================================================
# 15. BACKEND TEST
# ============================================================

if __name__ == "__main__":

    test_pdf = os.path.join(

        BASE_DIR,

        "sample_medical_report.pdf"
    )


    print("\n")
    print("=" * 60)
    print("PDF EXTRACTION TEST")
    print("=" * 60)


    extracted_text = extract_text_from_pdf(

        test_pdf
    )


    print(
        extracted_text[:1000]
    )


    print("\n")
    print("=" * 60)
    print("FINDINGS TEST")
    print("=" * 60)


    findings = extract_findings(

        extracted_text
    )


    print(findings)


    print("\n")
    print("=" * 60)
    print("CLINICAL INTERPRETATION TEST")
    print("=" * 60)


    interpretations = interpret_clinical_findings(

        findings
    )


    for key, value in interpretations.items():

        print(f"\n{key}:")
        print(value)


    print("\n")
    print("=" * 60)
    print("MEDRAG INSIGHT BACKEND READY")
    print("=" * 60)