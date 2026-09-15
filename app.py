import streamlit as st
import os

from backend import analyze_report_with_rag


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MedRAG Insight",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# THEME CSS
# ============================================================

st.markdown("""
<style>

/* =========================================================
   GLOBAL
   ========================================================= */

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}


/* Remove unnecessary Streamlit top decoration */

header[data-testid="stHeader"] {
    background: transparent !important;
}




/* =========================================================
   AUTHENTICATION
   ========================================================= */

.brand {
    text-align: center;
    font-size: 36px;
    font-weight: 800;
    margin-top: 35px;
    margin-bottom: 5px;
}

.tagline {
    text-align: center;
    color: #b8b8b8;
    margin-bottom: 30px;
}


/* =========================================================
   DASHBOARD
   ========================================================= */

.dashboard-title {
    font-size: 38px;
    font-weight: 800;
    margin-bottom: 5px;
}

.dashboard-subtitle {
    color: #b8b8b8;
    margin-bottom: 30px;
}


/* =========================================================
   FEATURE CARDS
   ========================================================= */

.stat-card {
    padding: 22px;
    border-radius: 16px;
    border: 1px solid rgba(231, 76, 92, 0.42);
    background: rgba(231, 76, 92, 0.065);
    text-align: center;
    min-height: 155px;
    transition: all 0.2s ease;
}

.stat-card:hover {
    border-color: rgba(231, 76, 92, 0.75);
    background: rgba(231, 76, 92, 0.10);
    transform: translateY(-2px);
}

.stat-card h2 {
    margin-bottom: 8px;
}

.stat-card b {
    font-size: 19px;
}

.stat-card p {
    color: #b5b5b5;
}


/* =========================================================
   CONTENT CARD
   ========================================================= */

.content-card {
    padding: 22px;
    border-radius: 16px;
    border: 1px solid rgba(231, 76, 92, 0.38);
    background: rgba(231, 76, 92, 0.055);
    margin-bottom: 20px;
}

.card-title {
    font-size: 21px;
    font-weight: 700;
    margin-bottom: 12px;
}


/* =========================================================
   RED PRIMARY BUTTON
   ========================================================= */

div.stButton > button[kind="primary"] {

    background: linear-gradient(
        135deg,
        #e74c5c,
        #d9364f
    ) !important;

    color: #ffffff !important;

    border: none !important;

    border-radius: 10px !important;

    font-weight: 700 !important;

    transition: all 0.2s ease !important;
}


div.stButton > button[kind="primary"]:hover {

    background: linear-gradient(
        135deg,
        #d9364f,
        #c92f46
    ) !important;

    color: #ffffff !important;

    border: none !important;

    transform: translateY(-1px);

    box-shadow:
        0 5px 18px rgba(217, 54, 79, 0.25);
}


/* =========================================================
   NORMAL BUTTONS
   ========================================================= */

div.stButton > button {

    border-radius: 10px !important;

    transition: all 0.2s ease !important;
}


/* =========================================================
   INPUT FIELDS
   ========================================================= */

div[data-baseweb="input"] {
    border-radius: 9px !important;
}


/* =========================================================
   FILE UPLOADER
   ========================================================= */

section[data-testid="stFileUploaderDropzone"] {

    border: 1px dashed rgba(231, 76, 92, 0.60) !important;

    border-radius: 12px !important;

    background: rgba(231, 76, 92, 0.035) !important;
}

section[data-testid="stFileUploaderDropzone"]:hover {

    border-color: #e74c5c !important;

    background: rgba(231, 76, 92, 0.07) !important;
}


/* =========================================================
   DISCLAIMER
   ========================================================= */

.disclaimer {

    padding: 18px;

    border-radius: 14px;

    border: 1px solid rgba(220, 170, 60, 0.5);

    background: rgba(220, 170, 60, 0.08);

    margin-top: 25px;

    color: #d0d0d0;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

.sidebar-brand {
    font-size: 24px;
    font-weight: 800;
}


/* =========================================================
   METRIC AREA
   ========================================================= */

[data-testid="stMetric"] {

    background: rgba(231, 76, 92, 0.045);

    border: 1px solid rgba(231, 76, 92, 0.25);

    border-radius: 12px;

    padding: 12px;
}


/* =========================================================
   EXPANDER
   ========================================================= */

[data-testid="stExpander"] {

    border: 1px solid rgba(231, 76, 92, 0.30) !important;

    border-radius: 12px !important;
}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 768px) {

    .dashboard-title {
        font-size: 29px;
    }

    .brand {
        font-size: 30px;
        margin-top: 20px;
    }

    .stat-card {
        margin-bottom: 15px;
    }

}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "auth_page" not in st.session_state:
    st.session_state.auth_page = "Sign In"

if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"


# ============================================================
# AUTHENTICATION
# ============================================================

if not st.session_state.authenticated:

    # ========================================================
    # CENTER AUTH CONTENT
    # ========================================================

    left, center, right = st.columns([1, 1.15, 1])

    with center:

        st.markdown(
            '<div class="brand">🩺 MedRAG Insight</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="tagline">'
            'AI-Powered Medical Report Analysis'
            '</div>',
            unsafe_allow_html=True
        )


        # ====================================================
        # SIGN IN
        # ====================================================

        if st.session_state.auth_page == "Sign In":

            st.subheader("Welcome Back")

            email = st.text_input(
                "Email",
                placeholder="Enter your email"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )


            if st.button(
                "Sign In",
                type="primary",
                use_container_width=True
            ):

                if email.strip() and password.strip():

                    st.session_state.authenticated = True

                    st.session_state.current_page = "🏠 Dashboard"

                    st.rerun()

                else:

                    st.warning(
                        "Please enter your email and password."
                    )


            st.write("")

            st.markdown(
                "Don't have an account?"
            )


            if st.button(
                "Create an Account",
                use_container_width=True
            ):

                st.session_state.auth_page = "Sign Up"

                st.rerun()


        # ====================================================
        # SIGN UP
        # ====================================================

        else:

            st.subheader("Create Your Account")

            name = st.text_input(
                "Full Name",
                placeholder="Enter your name"
            )

            email = st.text_input(
                "Email",
                placeholder="Enter your email"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Confirm your password"
            )


            if st.button(
                "Create Account",
                type="primary",
                use_container_width=True
            ):

                if not name.strip():

                    st.warning(
                        "Please enter your name."
                    )

                elif not email.strip():

                    st.warning(
                        "Please enter your email."
                    )

                elif not password.strip():

                    st.warning(
                        "Please enter a password."
                    )

                elif password != confirm_password:

                    st.error(
                        "Passwords do not match."
                    )

                else:

                    st.success(
                        "Account created successfully!"
                    )

                    st.session_state.auth_page = "Sign In"

                    st.rerun()


            st.write("")

            st.markdown(
                "Already have an account?"
            )


            if st.button(
                "Back to Sign In",
                use_container_width=True
            ):

                st.session_state.auth_page = "Sign In"

                st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

else:

    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.markdown(
            '<div class="sidebar-brand">🩺 MedRAG Insight</div>',
            unsafe_allow_html=True
        )

        st.caption(
            "Medical Intelligence Platform"
        )

        st.divider()


        st.markdown("### Navigation")


        # Dashboard

        if st.button(
            "🏠 Dashboard",
            use_container_width=True
        ):

            st.session_state.current_page = "🏠 Dashboard"

            st.rerun()


        # New Analysis

        if st.button(
            "📄 New Analysis",
            use_container_width=True
        ):

            st.session_state.current_page = "📄 New Analysis"

            st.rerun()


        # History

        if st.button(
            "🕘 History",
            use_container_width=True
        ):

            st.session_state.current_page = "🕘 History"

            st.rerun()


        st.divider()


        st.markdown(
            "### 🛡️ Knowledge Base"
        )

        st.caption(
            "Powered by medical information "
            "retrieved from MedlinePlus."
        )


        st.divider()


        # Logout

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            st.session_state.authenticated = False

            st.session_state.auth_page = "Sign In"

            st.session_state.current_result = None

            st.session_state.current_page = "🏠 Dashboard"

            st.rerun()


    # ========================================================
    # CURRENT PAGE
    # ========================================================

    page = st.session_state.current_page


    # ========================================================
    # DASHBOARD
    # ========================================================

    if page == "🏠 Dashboard":

        st.markdown(
            '<div class="dashboard-title">'
            'Medical Intelligence Dashboard'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="dashboard-subtitle">'
            'Analyze medical reports and retrieve '
            'relevant medical information.'
            '</div>',
            unsafe_allow_html=True
        )


        # ====================================================
        # FEATURE CARDS
        # ====================================================

        col1, col2, col3 = st.columns(3)


        with col1:

            st.markdown(
                '<div class="stat-card">'
                '<h2>📄</h2>'
                '<b>Report Analysis</b>'
                '<p>Extract medical findings from reports</p>'
                '</div>',
                unsafe_allow_html=True
            )


        with col2:

            st.markdown(
                '<div class="stat-card">'
                '<h2>🧠</h2>'
                '<b>AI + RAG</b>'
                '<p>Retrieve relevant medical knowledge</p>'
                '</div>',
                unsafe_allow_html=True
            )


        with col3:

            st.markdown(
                '<div class="stat-card">'
                '<h2>📚</h2>'
                '<b>Trusted Sources</b>'
                '<p>Powered by MedlinePlus knowledge</p>'
                '</div>',
                unsafe_allow_html=True
            )


        st.write("")


        # ====================================================
        # START NEW ANALYSIS
        # ====================================================

        st.markdown(
            '<div class="content-card">'
            '<div class="card-title">'
            '🚀 Start a New Analysis'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

        st.write(
            "Upload a medical report to extract "
            "important findings and generate an "
            "educational AI-powered explanation."
        )


        if st.button(
            "📄 Analyze a Medical Report",
            type="primary",
            use_container_width=True
        ):

            st.session_state.current_page = "📄 New Analysis"

            st.rerun()


    # ========================================================
    # NEW ANALYSIS
    # ========================================================

    elif page == "📄 New Analysis":

        st.markdown(
            '<div class="dashboard-title">'
            'Medical Report Analysis'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="dashboard-subtitle">'
            'Upload a PDF medical report for analysis.'
            '</div>',
            unsafe_allow_html=True
        )


        # ====================================================
        # UPLOAD REPORT
        # ====================================================

        st.markdown(
            '<div class="card-title">'
            '📤 Upload Report'
            '</div>',
            unsafe_allow_html=True
        )


        uploaded_file = st.file_uploader(
            "Choose a medical report",
            type=["pdf"],
            help="Upload a PDF medical report."
        )


        if uploaded_file is not None:

            st.success(
                f"Selected: {uploaded_file.name}"
            )


            if st.button(
                "🔍 Analyze Report",
                type="primary",
                use_container_width=True
            ):

                temp_path = os.path.join(
                    os.path.dirname(
                        os.path.abspath(__file__)
                    ),
                    "uploaded_report.pdf"
                )


                with open(
                    temp_path,
                    "wb"
                ) as f:

                    f.write(
                        uploaded_file.getbuffer()
                    )


                with st.spinner(
                    "Analyzing report..."
                ):

                    try:

                        result = analyze_report_with_rag(
                            temp_path
                        )

                        st.session_state.current_result = result


                        st.session_state.analysis_history.append(
                            {
                                "filename": uploaded_file.name,
                                "result": result
                            }
                        )


                        st.success(
                            "Analysis completed successfully!"
                        )


                    except Exception as e:

                        st.error(
                            f"Analysis failed: {str(e)}"
                        )


        # ====================================================
        # RESULTS
        # ====================================================

        if st.session_state.current_result:

            result = st.session_state.current_result

            findings = result.get(
                "findings",
                {}
            )

            interpretations = result.get(
                "interpretations",
                {}
            )

            explanation = result.get(
                "rag_explanation",
                ""
            )

            sources = result.get(
                "sources",
                []
            )


            # =================================================
            # EXTRACTED FINDINGS
            # =================================================

            st.markdown(
                '<div class="card-title">'
                '📊 Extracted Findings'
                '</div>',
                unsafe_allow_html=True
            )


            c1, c2, c3, c4 = st.columns(4)


            with c1:

                st.metric(
                    "Age",
                    findings.get(
                        "Age",
                        "N/A"
                    )
                )


            with c2:

                st.metric(
                    "Blood Pressure",
                    findings.get(
                        "Blood Pressure",
                        "N/A"
                    )
                )


            with c3:

                st.metric(
                    "Blood Glucose",
                    findings.get(
                        "Blood Glucose",
                        "N/A"
                    )
                )


            with c4:

                symptom_status = (
                    "Detected"
                    if findings.get(
                        "Symptoms",
                        "Not available"
                    ) != "Not available"
                    else "N/A"
                )

                st.metric(
                    "Symptoms",
                    symptom_status
                )


            # =================================================
            # CLINICAL INTERPRETATION
            # =================================================

            st.markdown(
                '<div class="card-title">'
                '🩻 Clinical Interpretation'
                '</div>',
                unsafe_allow_html=True
            )


            if interpretations:

                for key, value in interpretations.items():

                    st.markdown(
                        f"**{key}**"
                    )

                    st.write(
                        value
                    )

            else:

                st.info(
                    "No clinical interpretation available."
                )


            # =================================================
            # AI EXPLANATION
            # =================================================

            st.markdown(
                '<div class="card-title">'
                '🧠 AI-Powered Explanation'
                '</div>',
                unsafe_allow_html=True
            )


            if explanation:

                st.write(
                    explanation
                )

            else:

                st.info(
                    "No AI explanation available."
                )


            # =================================================
            # TRUSTED SOURCES
            # =================================================

            st.markdown(
                '<div class="card-title">'
                '📚 Retrieved Sources'
                '</div>',
                unsafe_allow_html=True
            )


            if sources:

                for source in sources:

                    if isinstance(source, dict):

                        finding = source.get(
                            "finding",
                            "Medical Finding"
                        )

                        topic = source.get(
                            "topic",
                            "Medical Topic"
                        )

                        source_name = source.get(
                            "source",
                            "Medical Source"
                        )

                        st.write(
                            f"**{finding}** → "
                            f"{topic} — "
                            f"{source_name}"
                        )

                    else:

                        st.write(
                            str(source)
                        )

            else:

                st.info(
                    "No trusted sources were retrieved."
                )


            # =================================================
            # DISCLAIMER
            # =================================================

            st.markdown(
                '<div class="disclaimer">'
                '<b>⚠️ Medical Disclaimer</b><br><br>'
                'This application provides educational and '
                'informational content only. It does not '
                'provide a medical diagnosis or prescribe '
                'treatment. Consult a qualified healthcare '
                'professional for medical decisions.'
                '</div>',
                unsafe_allow_html=True
            )


    # ========================================================
    # HISTORY
    # ========================================================

    elif page == "🕘 History":

        st.markdown(
            '<div class="dashboard-title">'
            'Analysis History'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="dashboard-subtitle">'
            'Your reports analyzed during this session.'
            '</div>',
            unsafe_allow_html=True
        )


        if not st.session_state.analysis_history:

            st.info(
                "No reports analyzed yet."
            )


        else:

            for item in reversed(
                st.session_state.analysis_history
            ):

                result = item.get(
                    "result",
                    {}
                )

                findings = result.get(
                    "findings",
                    {}
                )


                with st.expander(
                    f"📄 {item.get('filename', 'Medical Report')}"
                ):

                    st.write(
                        f"**Age:** "
                        f"{findings.get('Age', 'N/A')}"
                    )

                    st.write(
                        f"**Blood Pressure:** "
                        f"{findings.get('Blood Pressure', 'N/A')}"
                    )

                    st.write(
                        f"**Blood Glucose:** "
                        f"{findings.get('Blood Glucose', 'N/A')}"
                    )