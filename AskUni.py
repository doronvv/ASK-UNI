import streamlit as st
import google.generativeai as genai
import pandas as pd
import warnings
import os

# --- 1. הגדרות וטיפול באזהרות ---
warnings.filterwarnings("ignore")
st.set_page_config(page_title="בוט תנאי קבלה", layout="wide", page_icon="🎓")

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
    
    # --- עדכון שמות הקבצים החדשים כאן ---
    # ודא שהקבצים בגיטהאב נקראים בדיוק כך (כולל .csv)
    path_admission = os.path.join(current_dir, "bgu_1.csv") 
    path_projects = os.path.join(current_dir, "bgu_2.csv")

    # טעינת קובץ קבלה (bgu_1)
    try:
        if os.path.exists(path_admission):
            data_dict["admission"] = pd.read_csv(path_admission)
        else:
            data_dict["admission"] = None
    except:
        data_dict["admission"] = None

    # טעינת קובץ פרויקטים (bgu_2)
    try:
        if os.path.exists(path_projects):
            data_dict["projects"] = pd.read_csv(path_projects)
        else:
            data_dict["projects"] = None
    except:
        data_dict["projects"] = None

    return data_dict

# טעינת המידע
all_data = load_data()

# הצגת שגיאות ברורות אם קבצים חסרים
if all_data["admission"] is None:
    st.error("⚠️ שגיאה: לא מצאתי את הקובץ bgu_1.csv")
if all_data["projects"] is None:
    st.error("⚠️ שגיאה: לא מצאתי את הקובץ bgu_2.csv")

# --- 4. הגדרת המודל בצורה מאובטחת ---
# הקוד הזה בודק אם יש מפתח ב-Secrets של הענן.
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

# --- 5. ממשק המשתמש ---
st.title("🎓 בוט מידע: אוניברסיטת בן גוריון")
st.write("שאל אותי בחופשיות על תנאי קבלה או אתר פרויקטים של חשמל.")
st.info("""
💡 **שאל אותי על תנאי קבלה או על פרויקטים מסווגים**
* שאל אותי בחופשיות על תנאי קבלה או אתר פרויקטים של חשמל
""")
with st.expander("📌 לחץ כאן כדי לראות שאלות לדוגמה"):
    st.write("1. מה תנאי הקבלה ______ (שם התואר שאתה מחפש)?")
    st.write("2. איזה תארים יש בהנדסה?")
    st.write("3. יש פרויקט בשם AskUni ?")
    st.write("4. מי המנחה של פרויקט AskUni?")
    st.write("5. באיזה נושא פרויקט ASKUNI עוסק ?")
st.caption("הבוט מבוסס על נתונים רשמיים אך עשויים לחול שינויים.")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. לוגיקה (עם הוספת הזיכרון) ---
if prompt := st.chat_input("מה תרצה לדעת?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner('בודק נתונים...'):
            try:
                context = ""
                # בניית ההקשר למודל מתוך הקבצים
                if all_data["admission"] is not None:
                    context += f"\n=== נתוני קבלה (Admission) ===\n{all_data['admission'].to_string()}\n"
                if all_data["projects"] is not None:
                    context += f"\n=== נתוני פרויקטים (Projects) ===\n{all_data['projects'].to_string()}\n"
                
                if context == "":
                    st.error("אין נתונים זמינים במערכת.")
                    st.stop()

                # --- השינוי שביצעתי כאן: בניית מחרוזת זיכרון ---
                history_str = ""
                for msg in st.session_state.messages:
                    role_name = "משתמש" if msg["role"] == "user" else "עוזר"
                    history_str += f"{role_name}: {msg['content']}\n"

                # עדכון הפרומפט שיכלול גם את ההיסטוריה
                full_prompt = (
                    f"אתה יועץ לימודים מומחה באוניברסיטת בן גוריון.\n"
                    f"ענה על השאלה אך ורק לפי הנתונים המצורפים למטה.\n"
                    f"אם המידע לא קיים בנתונים, תגיד שאתה לא יודע.\n"
                    f"אל תמציא מידע שלא מופיע בטבלאות.\n\n"
                    f"הנתונים:\n{context}\n\n"
                    f"--- היסטוריית השיחה (הקשר) ---\n"
                    f"{history_str}\n" 
                    f"------------------------------\n"
                    f"שאלה: {prompt}\n"
                    f"תשובה (בעברית):"
                )
                
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"שגיאה: {e}")
