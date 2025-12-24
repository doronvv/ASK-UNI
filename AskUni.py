import streamlit as st
import google.generativeai as genai
import pandas as pd
import warnings
import os

# --- 1. הגדרות וטיפול באזהרות ---
warnings.filterwarnings("ignore")
st.set_page_config(page_title="בוט מידע אקדמי - בן גוריון", layout="wide", page_icon="🎓")

# --- 2. עיצוב RTL (מימין לשמאל) ---
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; }
    .stChatMessage { text-align: right; direction: rtl; }
    p, h1, h2, h3, div { text-align: right; }
    .stTextInput > div > div > input { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- 3. טעינת נתונים חכמה ---
@st.cache_data
def load_data():
    data_dict = {}
    
    # מוצא את התיקייה הנוכحية של הקובץ
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # --- הגדרת שמות הקבצים ---
    # bgu_1 = קבלה (כמו שהיה בענן)
    # bgu_2 = פרויקטים (כמו שהיה בענן)
    # grades.csv = הקובץ החדש שהוספת
    path_admission = os.path.join(current_dir, "bgu_1.csv") 
    path_projects = os.path.join(current_dir, "bgu_2.csv")
    path_grades = os.path.join(current_dir, "grades.csv")

    # טעינת קובץ קבלה
    try:
        if os.path.exists(path_admission):
            data_dict["admission"] = pd.read_csv(path_admission)
        else:
            data_dict["admission"] = None
    except:
        data_dict["admission"] = None

    # טעינת קובץ פרויקטים
    try:
        if os.path.exists(path_projects):
            data_dict["projects"] = pd.read_csv(path_projects)
        else:
            data_dict["projects"] = None
    except:
        data_dict["projects"] = None

    # טעינת קובץ ציונים (החדש)
    try:
        if os.path.exists(path_grades):
            data_dict["grades"] = pd.read_csv(path_grades)
        else:
            data_dict["grades"] = None
    except:
        data_dict["grades"] = None

    return data_dict

# טעינת המידע
all_data = load_data()

# הצגת שגיאות ברורות אם קבצים חסרים
if all_data["admission"] is None:
    st.error("⚠️ שגיאה: לא מצאתי את הקובץ bgu_1.csv")
if all_data["projects"] is None:
    st.error("⚠️ שגיאה: לא מצאתי את הקובץ bgu_2.csv")
if all_data["grades"] is None:
    st.error("⚠️ שגיאה: לא מצאתי את הקובץ grades.csv (וודא שהעלית אותו ל-GitHub)")

# --- 4. הגדרת המודל בצורה מאובטחת ---
# שימוש ב-Secrets של הענן
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.text_input("הכנס מפתח Google API:", type="password")

if not api_key:
    st.warning("נא להזין מפתח API כדי שהבוט יוכל לעבוד.")
    st.stop()

# הגדרת המודל
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 5. ממשק המשתמש (מעודכן לפי הבקשה שלך) ---
st.title("🎓 בוט מידע: בן גוריון")
st.subheader("תנאי קבלה | ספר פרויקטים | ממוצעי קורסים")

st.info("""
💡 **שאל אותי בחופשיות על:**
* תנאי קבלה למחלקות השונות
* פרויקטים (הנדסת חשמל ומחשבים)
* ממוצעי ציונים בקורסים (חדש!)
""")

with st.expander("📌 לחץ כאן לשאלות לדוגמה"):
    st.write("**קבלה:** מה תנאי הקבלה להנדסת חשמל ?")
    st.write(" מה תנאי הקבלה ______ (שם התואר שאתה מחפש)?")
    st.write(" איזה תארים יש בהנדסה?")
    st.write("**פרויקטים:** מי המנחה של פרויקט AskUni?")
    st.write("באיזה נושא פרויקט ASKUNI עוסק ?")
    st.write("**ציונים:** מה היה הממוצע בקורס חדווא 1 בשנת ____(שנים בין 2025-2022) אפשר להוסיף גם סמסטר?")
    st.write("**משולב:** מה הממוצע בפיזיקה 1 ומי מלמד את זה?")

st.caption("הבוט מבוסס על נתונים רשמיים, אך ייתכנו שינויים.")
st.caption("שימו לב - כל המידע שמסופק עשוי להכיל טעויות וחשוב לבדוק ולאמת מידע חשוב באמצעות אתר האוניברסיטה")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. לוגיקה (כולל ציונים וזיכרון) ---
if prompt := st.chat_input("מה תרצה לדעת?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner('מעבד נתונים...'):
            try:
                context_str = ""
                # 1. נתוני קבלה
                if all_data["admission"] is not None:
                    context_str += f"\n=== נתוני קבלה (Admission) ===\n{all_data['admission'].to_string()}\n"
                # 2. נתוני פרויקטים
                if all_data["projects"] is not None:
                    context_str += f"\n=== נתוני פרויקטים (Projects) ===\n{all_data['projects'].to_string()}\n"
                # 3. נתוני ציונים (החדש)
                if all_data["grades"] is not None:
                    context_str += f"\n=== טבלת ממוצעי קורסים וציונים (Grades) ===\n{all_data['grades'].to_string()}\n"
                
                if context_str == "":
                    st.error("אין נתונים זמינים במערכת.")
                    st.stop()

                # בניית היסטוריית השיחה
                history_str = ""
                for msg in st.session_state.messages:
                    role_name = "משתמש" if msg["role"] == "user" else "עוזר"
                    history_str += f"{role_name}: {msg['content']}\n"

                # הפרומפט המלא
                full_prompt = (
                    f"אתה עוזר חכם ואדיב לסטודנטים בבן גוריון.\n"
                    f"יש לך גישה ל-3 טבלאות נתונים:\n"
                    f"1. תנאי קבלה.\n"
                    f"2. פרויקטים.\n"
                    f"3. ציונים וממוצעי קורסים (Grades).\n\n"
                    f"הנחיות:\n"
                    f"- ענה אך ורק על סמך המידע בטבלאות המצורפות.\n"
                    f"- אם שאלו על ציון בקורס, חפש לפי שם הקורס או המספר שלו בטבלת הציונים. שים לב לשנה ולסמסטר.\n"
                    f"- אם המידע לא קיים, ציין זאת.\n\n"
                    f"המידע מהטבלאות:\n{context_str}\n\n"
                    f"--- היסטוריית השיחה (הקשר) ---\n"
                    f"{history_str}\n" 
                    f"------------------------------\n"
                    f"שאלה נוכחית: {prompt}\n"
                    f"תשובה (בעברית):"
                )
                
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"שגיאה: {e}")
