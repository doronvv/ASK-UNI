import streamlit as st
import google.generativeai as genai
import pandas as pd
import warnings
import os  # <--- הוספנו את זה כדי לזהות מיקומים במחשב

# --- 1. הגדרות וטיפול באזהרות ---
warnings.filterwarnings("ignore")

st.set_page_config(page_title="בוט תנאי קבלה ופרויקטים", layout="wide", page_icon="🎓")

# --- 2. סידור RTL (עברית) ---
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; }
    .stChatMessage { text-align: right; direction: rtl; }
    p, h1, h2, h3 { text-align: right; }
</style>
""", unsafe_allow_html=True)


# --- 3. טעינת הטבלאות (הגרסה המתוקנת והחכמה) ---
@st.cache_data
def load_data():
    data_dict = {}

    # משיג את הנתיב של התיקייה שבה נמצא הקובץ הזה (AskUni.py)
    # זה פותר את הבעיה שהטרמינל לא מוצא את הקבצים
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # בניית הנתיב המלא לקבצים
    path_admission = os.path.join(current_dir, "bgu_admission_complete.csv")
    path_projects = os.path.join(current_dir, "Projects_Classified.csv")

    # טעינת קובץ קבלה
    try:
        df_admission = pd.read_csv(path_admission)
        data_dict["admission"] = df_admission
    except Exception:
        data_dict["admission"] = None

    # טעינת קובץ פרויקטים
    try:
        df_projects = pd.read_csv(path_projects)
        data_dict["projects"] = df_projects
    except Exception:
        data_dict["projects"] = None

    return data_dict


# טעינת הנתונים למשתנה
all_data = load_data()

# בדיקה והצגת שגיאות אם קבצים חסרים
if all_data["admission"] is None:
    st.error("⚠️ לא הצלחתי למצוא את הקובץ: bgu_admission_complete.csv (וודא שהוא באותה תיקייה עם הקוד)")
if all_data["projects"] is None:
    st.error("⚠️ לא הצלחתי למצוא את הקובץ: Projects_Classified.csv (וודא שהוא באותה תיקייה עם הקוד)")

# --- 4. הגדרת המודל ---
api_key = "YOUR_API_KEY"
genai.configure(api_key="AIzaSyDE1qKjnw4qpjALtD7713rM0hq1w8P02HE")
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 5. ממשק המשתמש ---
st.title("🎓 בוט מידע: קבלה ופרויקטים")
st.write("שאל אותי על תנאי קבלה או על פרויקטים מסווגים.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. הלוגיקה החכמה ---
if prompt := st.chat_input("הקלד את השאלה שלך כאן..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        with st.chat_message("assistant"):
            with st.spinner('מחפש בנתונים...'):

                # הכנת המידע למודל
                context_str = ""

                if all_data["admission"] is not None:
                    context_str += f"\n--- טבלת תנאי קבלה (Admission) ---\n{all_data['admission'].to_string()}\n"

                if all_data["projects"] is not None:
                    context_str += f"\n--- טבלת פרויקטים (Projects) ---\n{all_data['projects'].to_string()}\n"

                if context_str == "":
                    context_str = "אין נתונים זמינים כרגע."

                # בניית ההנחיה המלאה
                full_prompt = (
                    f"אתה עוזר חכם. יש לך גישה לשתי טבלאות נתונים שונות (מופיעות למטה).\n"
                    f"1. טבלת תנאי קבלה.\n"
                    f"2. טבלת פרויקטים.\n"
                    f"ענה על שאלת המשתמש אך ורק על סמך המידע בטבלאות האלו.\n"
                    f"אם המידע לא מופיע באף אחת מהטבלאות, ציין זאת במפורש.\n\n"
                    f"המידע מהטבלאות:\n{context_str}\n\n"
                    f"שאלה: {prompt}"
                )

                # שליחה לגוגל
                response = model.generate_content(full_prompt)
                st.markdown(response.text)

        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"שגיאה בקבלת תשובה: {e}")