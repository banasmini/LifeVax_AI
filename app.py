
import json
import re
import pandas as pd
import streamlit as st

# ============================================================
# LIFE VAX AI
# Lightweight Adult Immunization Gap Assessment
# ============================================================

st.set_page_config(
    page_title="LifeVax AI",
    page_icon="💉",
    layout="wide"
)

# ============================================================
# IMPORTANT
# ============================================================
# This is an IDEATHON PROTOTYPE.
#
# The rules below are DEMONSTRATION rules.
# They are NOT clinical recommendations.
#
# Before real-world deployment, replace these rules with
# clinician-reviewed, versioned Indian adult-immunization
# guidelines.
# ============================================================


# ============================================================
# SMALL KNOWLEDGE BASE
# ============================================================
# We deliberately keep this tiny.
# NO large CSV.
# NO large database.
# NO large ML model.
# ============================================================

VACCINES = {

    "Influenza": {
        "description":
            "Adult influenza vaccination information.",
        "why":
            "Influenza vaccination may be relevant to adults depending on age, clinical context and current guidelines."
    },

    "Hepatitis B": {
        "description":
            "Adult hepatitis B vaccination information.",
        "why":
            "Hepatitis B vaccination may be relevant depending on previous vaccination and risk context."
    },

    "Td/Tdap": {
        "description":
            "Tetanus, diphtheria and pertussis vaccination information.",
        "why":
            "Adult vaccination history may need review depending on previous doses and guideline context."
    },

    "Pneumococcal": {
        "description":
            "Adult pneumococcal vaccination information.",
        "why":
            "Pneumococcal vaccination may be relevant for older adults and some risk groups."
    },

    "HPV": {
        "description":
            "Adult HPV vaccination information.",
        "why":
            "HPV vaccination relevance depends on age, previous vaccination and clinical context."
    },

    "Zoster": {
        "description":
            "Adult herpes-zoster vaccination information.",
        "why":
            "Zoster vaccination may be relevant depending on age and clinical context."
    },

    "Typhoid": {
        "description":
            "Adult typhoid vaccination information.",
        "why":
            "Typhoid vaccination may be relevant depending on travel or exposure context."
    }
}


HISTORY_OPTIONS = [
    "Documented",
    "Incomplete",
    "Unknown",
    "Conflicting"
]


RISK_OPTIONS = [
    "None / not sure",
    "Chronic medical condition",
    "Healthcare / occupational exposure",
    "Travel / exposure context",
    "Immunocompromising clinical context"
]


# ============================================================
# RULE ENGINE
# ============================================================

def vaccine_relevance(vaccine, age, risks):

    risk_text = " ".join(risks).lower()

    # Influenza
    if vaccine == "Influenza":
        return True, "Included for general adult vaccine awareness."

    # Td/Tdap
    if vaccine == "Td/Tdap":
        return True, "Included for adult vaccination-history review."

    # Hepatitis B
    if vaccine == "Hepatitis B":

        relevant = any(
            x in risk_text
            for x in [
                "chronic",
                "healthcare",
                "occupational",
                "immunocompromising"
            ]
        )

        return relevant, "Risk context selected for prototype review."

    # Pneumococcal
    if vaccine == "Pneumococcal":

        relevant = (
            age >= 50
            or
            any(
                x in risk_text
                for x in [
                    "chronic",
                    "immunocompromising"
                ]
            )
        )

        return relevant, "Age/risk context triggered prototype review."

    # HPV
    if vaccine == "HPV":

        relevant = 18 <= age <= 45

        return relevant, "Age falls within the prototype demonstration range."

    # Zoster
    if vaccine == "Zoster":

        relevant = age >= 50

        return relevant, "Age triggered prototype review."

    # Typhoid
    if vaccine == "Typhoid":

        relevant = (
            "travel" in risk_text
            or
            "exposure" in risk_text
        )

        return relevant, "Travel/exposure context triggered prototype review."

    return False, "No prototype trigger."


# ============================================================
# ASSESSMENT FUNCTION
# ============================================================

def assess_vaccine(vaccine, history, age, risks):

    relevant, relevance_reason = vaccine_relevance(
        vaccine,
        age,
        risks
    )

    # -----------------------------
    # DOCUMENTED
    # -----------------------------

    if history == "Documented":

        status = "Confirmed"

        reason = (
            "The user reports this vaccination as documented."
        )

        next_step = (
            "Keep the vaccination record available and "
            "verify details with a healthcare professional when appropriate."
        )

    # -----------------------------
    # CONFLICTING
    # -----------------------------

    elif history == "Conflicting":

        status = "Uncertain"

        reason = (
            "The vaccination history contains conflicting information."
        )

        next_step = (
            "Reconcile available records with a healthcare professional."
        )

    # -----------------------------
    # INCOMPLETE
    # -----------------------------

    elif history == "Incomplete":

        if relevant:

            status = "Potential gap / clinical review"

            reason = (
                "The vaccination history is incomplete and "
                "this vaccine is relevant under the prototype rule."
            )

            next_step = (
                "A healthcare professional should review previous "
                "doses, dates and applicable guidelines."
            )

        else:

            status = "Incomplete"

            reason = (
                "The vaccination history is incomplete."
            )

            next_step = (
                "Try to complete or verify the vaccination history."
            )

    # -----------------------------
    # UNKNOWN
    # -----------------------------

    else:

        if relevant:

            status = "Potential gap / clinical review"

            reason = (
                "Vaccination history is unknown and this vaccine "
                "is relevant under the prototype rule."
            )

            next_step = (
                "Verify records and discuss the result with "
                "a qualified healthcare professional."
            )

        else:

            status = "Unknown"

            reason = (
                "Vaccination history is unknown."
            )

            next_step = (
                "Try to recover vaccination records."
            )

    return {

        "vaccine": vaccine,

        "status": status,

        "history": history,

        "relevant": "Yes" if relevant else "No",

        "reason": reason,

        "context": relevance_reason,

        "next_step": next_step
    }


# ============================================================
# GEMINI — HISTORY EXTRACTION
# ============================================================

def extract_history_with_gemini(
    api_key,
    model_name,
    user_text
):

    from google import genai

    client = genai.Client(
        api_key=api_key
    )

    vaccine_names = list(VACCINES.keys())

    prompt = f"""
You are a structured data extraction component.

This is NOT a medical diagnosis system.

Extract ONLY vaccination history explicitly stated
by the user.

Do not infer vaccination.
Do not recommend vaccines.
Do not provide medical advice.

Allowed vaccines:

{json.dumps(vaccine_names)}

Return ONLY valid JSON.

Format:

{{
  "vaccines": {{
    "Influenza": "Documented|Incomplete|Unknown|Conflicting",
    "Hepatitis B": "Documented|Incomplete|Unknown|Conflicting",
    "Td/Tdap": "Documented|Incomplete|Unknown|Conflicting",
    "Pneumococcal": "Documented|Incomplete|Unknown|Conflicting",
    "HPV": "Documented|Incomplete|Unknown|Conflicting",
    "Zoster": "Documented|Incomplete|Unknown|Conflicting",
    "Typhoid": "Documented|Incomplete|Unknown|Conflicting"
  }}
}}

If the user did not mention a vaccine:
use "Unknown".

User statement:

{user_text}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )

    text = response.text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"^```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```$",
        "",
        text
    ).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end >= 0:
        text = text[start:end+1]

    data = json.loads(text)

    result = {}

    for vaccine in VACCINES:

        value = data["vaccines"].get(
            vaccine,
            "Unknown"
        )

        if value not in HISTORY_OPTIONS:
            value = "Unknown"

        result[vaccine] = value

    return result


# ============================================================
# GEMINI — REPORT EXPLANATION
# ============================================================

def explain_report_with_gemini(
    api_key,
    model_name,
    age,
    risks,
    results
):

    from google import genai

    client = genai.Client(
        api_key=api_key
    )

    simplified = []

    for result in results:

        simplified.append({

            "vaccine":
                result["vaccine"],

            "status":
                result["status"],

            "reason":
                result["reason"],

            "next_step":
                result["next_step"]
        })

    prompt = f"""
You are the explanation layer of LifeVax AI.

This is a non-diagnostic prototype.

The rule engine has already generated
the results.

DO NOT change the statuses.

DO NOT prescribe vaccines.

DO NOT give doses or schedules.

DO NOT tell the user to self-vaccinate.

Explain the results in simple language.

Age:
{age}

Risk context:
{risks}

Results:
{json.dumps(simplified)}

Keep the explanation under 150 words.
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )

    return response.text


# ============================================================
# STREAMLIT UI
# ============================================================

st.title("💉 LifeVax AI")

st.subheader(
    "AI-assisted Adult Immunization Gap Assessment"
)

st.caption(
    "National Level Ideathon 5.0 — Prototype"
)


# ============================================================
# SAFETY MESSAGE
# ============================================================

st.warning(
    "Prototype only. This application is not a diagnostic "
    "or prescribing system. Results should be discussed with "
    "a qualified healthcare professional."
)


# SIDEBAR
# ============================================================

# Read Gemini API key securely from Streamlit Secrets
try:
    secret_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    secret_api_key = ""

with st.sidebar:

    st.header("⚙️ Settings")

    enable_ai = st.checkbox(
        "Enable Gemini AI",
        value=bool(secret_api_key)
    )

    if secret_api_key:
        api_key = secret_api_key
        st.success("Gemini API configured securely.")
    else:
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            disabled=not enable_ai
        )

    model_name = st.text_input(
        "Gemini model",
        value="gemini-3.7-flash",
        disabled=not enable_ai
    )


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    [
        "🔎 Explore Adult Vaccines",
        "🧾 Assess My Immunization",
        "🧪 Demo Cases"
    ]
)


# ============================================================
# TAB 1
# ============================================================

with tab1:

    st.header(
        "Explore Adult Vaccines"
    )

    st.write(
        "Explore the small vaccine knowledge base used "
        "by the prototype."
    )

    vaccine = st.selectbox(
        "Select vaccine",
        list(VACCINES.keys())
    )

    info = VACCINES[vaccine]

    st.markdown(
        f"### {vaccine}"
    )

    st.write(
        info["description"]
    )

    st.markdown(
        "**Why it may matter**"
    )

    st.write(
        info["why"]
    )


# ============================================================
# TAB 2
# ============================================================

with tab2:

    st.header(
        "Assess My Immunization"
    )

    col1, col2 = st.columns(2)

    # -------------------------
    # PERSONAL PROFILE
    # -------------------------

    with col1:

        age = st.number_input(
            "Age",
            min_value=18,
            max_value=100,
            value=30
        )

    with col2:

        risks = st.multiselect(
            "Relevant context",
            RISK_OPTIONS,
            default=[
                "None / not sure"
            ]
        )


    # -------------------------
    # INPUT METHOD
    # -------------------------

    input_method = st.radio(
        "How do you want to enter vaccination history?",
        [
            "Structured form",
            "Natural language"
        ],
        horizontal=True
    )


    # ========================================================
    # STRUCTURED FORM
    # ========================================================

    if input_method == "Structured form":

        st.subheader(
            "Vaccination history"
        )

        history = {}

        col1, col2 = st.columns(2)

        vaccine_list = list(VACCINES.keys())

        for i, vaccine in enumerate(vaccine_list):

            column = (
                col1
                if i % 2 == 0
                else col2
            )

            with column:

                history[vaccine] = st.selectbox(
                    vaccine,
                    HISTORY_OPTIONS,
                    index=2,
                    key=f"history_{vaccine}"
                )


    # ========================================================
    # NATURAL LANGUAGE
    # ========================================================

    else:

        st.subheader(
            "Describe your vaccination history"
        )

        user_text = st.text_area(
            "Example",
            placeholder=(
                "I completed hepatitis B in college. "
                "I am not sure about tetanus. "
                "I don't have records for the other vaccines."
            ),
            height=150
        )

        history = {
            vaccine: "Unknown"
            for vaccine in VACCINES
        }

        if st.button(
            "✨ Extract vaccination history"
        ):

            if not enable_ai:

                st.error(
                    "Enable Gemini AI from the sidebar."
                )

            elif not api_key:

                st.error(
                    "Please enter your Gemini API key."
                )

            elif not user_text.strip():

                st.error(
                    "Please enter some vaccination history."
                )

            else:

                try:

                    with st.spinner(
                        "Reading vaccination history..."
                    ):

                        history = (
                            extract_history_with_gemini(
                                api_key,
                                model_name,
                                user_text
                            )
                        )

                    st.session_state[
                        "extracted_history"
                    ] = history

                    st.success(
                        "History extracted. Please review it."
                    )

                except Exception as e:

                    st.error(
                        f"Gemini error: {e}"
                    )


        if "extracted_history" in st.session_state:

            history = (
                st.session_state[
                    "extracted_history"
                ]
            )

            table = pd.DataFrame({

                "Vaccine":
                    list(history.keys()),

                "History":
                    list(history.values())

            })

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True
            )


    # ========================================================
    # ASSESS BUTTON
    # ========================================================

    st.divider()

    if st.button(
        "🩺 Generate Immunization Gap Report",
        type="primary"
    ):

        results = []

        for vaccine in VACCINES:

            result = assess_vaccine(

                vaccine,

                history.get(
                    vaccine,
                    "Unknown"
                ),

                age,

                risks
            )

            results.append(
                result
            )

        st.session_state[
            "results"
        ] = results

        st.session_state[
            "age"
        ] = age

        st.session_state[
            "risks"
        ] = risks


    # ========================================================
    # REPORT
    # ========================================================

    if "results" in st.session_state:

        results = (
            st.session_state[
                "results"
            ]
        )

        st.header(
            "📋 Immunization Gap Report"
        )

        # Summary table

        table = pd.DataFrame({

            "Vaccine":
                [
                    x["vaccine"]
                    for x in results
                ],

            "Status":
                [
                    x["status"]
                    for x in results
                ],

            "History":
                [
                    x["history"]
                    for x in results
                ],

            "Prototype Relevance":
                [
                    x["relevant"]
                    for x in results
                ]
        })

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True
        )


        # Detailed explanation

        st.subheader(
            "Why?"
        )

        for result in results:

            status = result["status"]

            if status == "Confirmed":
                icon = "🟢"

            elif status == "Incomplete":
                icon = "🟡"

            elif status == "Unknown":
                icon = "🔵"

            elif status == "Uncertain":
                icon = "🟠"

            else:
                icon = "🔴"

            with st.expander(
                f"{icon} {result['vaccine']} — {status}"
            ):

                st.write(
                    "**Assessment:**"
                )

                st.write(
                    result["reason"]
                )

                st.write(
                    "**Context:**"
                )

                st.write(
                    result["context"]
                )

                st.write(
                    "**Next step:**"
                )

                st.write(
                    result["next_step"]
                )


        # ====================================================
        # AI EXPLANATION
        # ====================================================

        if enable_ai:

            if st.button(
                "🤖 Explain Report with Gemini"
            ):

                if not api_key:

                    st.error(
                        "Enter your Gemini API key."
                    )

                else:

                    try:

                        with st.spinner(
                            "Generating explanation..."
                        ):

                            explanation = (
                                explain_report_with_gemini(
                                    api_key,
                                    model_name,
                                    st.session_state["age"],
                                    st.session_state["risks"],
                                    results
                                )
                            )

                        st.info(
                            explanation
                        )

                    except Exception as e:

                        st.error(
                            f"Gemini error: {e}"
                        )


        st.success(
            "Use this report as a discussion aid with "
            "a qualified healthcare professional."
        )


# ============================================================
# TAB 3
# ============================================================

with tab3:

    st.header(
        "🧪 Synthetic Demo Cases"
    )

    st.write(
        "These are tiny synthetic cases for the Ideathon demo. "
        "No large patient dataset is loaded."
    )


    demo_cases = {

        "Case 1 — Unknown history": {

            "age": 27,

            "risks":
                ["None / not sure"],

            "history":
                {
                    vaccine: "Unknown"
                    for vaccine in VACCINES
                }
        },


        "Case 2 — Older adult": {

            "age": 58,

            "risks":
                [
                    "Chronic medical condition"
                ],

            "history":
                {
                    "Influenza": "Unknown",
                    "Hepatitis B": "Incomplete",
                    "Td/Tdap": "Unknown",
                    "Pneumococcal": "Unknown",
                    "HPV": "Unknown",
                    "Zoster": "Unknown",
                    "Typhoid": "Unknown"
                }
        },


        "Case 3 — Travel context": {

            "age": 34,

            "risks":
                [
                    "Travel / exposure context"
                ],

            "history":
                {
                    "Influenza": "Documented",
                    "Hepatitis B": "Documented",
                    "Td/Tdap": "Unknown",
                    "Pneumococcal": "Unknown",
                    "HPV": "Incomplete",
                    "Zoster": "Unknown",
                    "Typhoid": "Unknown"
                }
        }
    }


    selected_case = st.selectbox(
        "Select demo patient",
        list(demo_cases.keys())
    )


    case = demo_cases[
        selected_case
    ]


    st.write(
        f"**Age:** {case['age']}"
    )

    st.write(
        f"**Context:** {', '.join(case['risks'])}"
    )


    demo_results = []

    for vaccine in VACCINES:

        demo_results.append(

            assess_vaccine(

                vaccine,

                case["history"][vaccine],

                case["age"],

                case["risks"]

            )
        )


    demo_table = pd.DataFrame({

        "Vaccine":
            [
                x["vaccine"]
                for x in demo_results
            ],

        "History":
            [
                x["history"]
                for x in demo_results
            ],

        "Result":
            [
                x["status"]
                for x in demo_results
            ]
    })


    st.dataframe(
        demo_table,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "LifeVax AI | National Level Ideathon 5.0 | "
    "Lightweight prototype"
)
