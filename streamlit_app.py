import streamlit as st
import sqlite3
import re
import pandas as pd
import os
from io import StringIO

# قائمة الحروف العربية للتنقل
arabic_letters = ['ا', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'هـ', 'و', 'ي']

# Function to normalize Arabic text
def normalize_arabic(text):
    # Normalize Arabic characters
    text = re.sub("[إأآا]", "ا", text)
    text = re.sub("ى", "ي", text)
    text = re.sub("ؤ", "و", text)
    text = re.sub("ئ", "ي", text)
    text = re.sub("ة", "ه", text)
    # Remove diacritics
    text = re.sub(r'[\u064B-\u065F]', '', text)
    return text

# تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect('keywords.db')
    c = conn.cursor()
    # التحقق من أن الجدول يحتوي على الأعمدة المطلوبة (المعنى، المثال، الملاحظة)
    c.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY,
            keyword TEXT UNIQUE,
            meaning TEXT NOT NULL,
            example TEXT NOT NULL,
            note TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Import keywords from the keywords1.csv file automatically
def import_from_csv():
    file_path = 'keywords 1.csv'
    if os.path.isfile(file_path):
        data = pd.read_csv(file_path, encoding='utf-8-sig')
        
        conn = sqlite3.connect('keywords.db')
        c = conn.cursor()
        
        # Insert each row into the database
        for index, row in data.iterrows():
            keyword = normalize_arabic(row['keyword'])
            meaning = row['meaning']
            example = row['example']
            note = ' '
            c.execute("INSERT OR IGNORE INTO keywords (keyword, meaning, example, note) VALUES (?, ?, ?, ?)", 
                      (keyword, meaning, example, note))
        
        conn.commit()
        conn.close()
        st.success(" ")
    else:
        st.warning(" ")

# التحقق من وجود الكلمة في قاعدة البيانات (مع التطبيع)
def check_keyword(keyword):
    normalized_keyword = normalize_arabic(keyword)  # Normalize the input keyword
    conn = sqlite3.connect('keywords.db')
    c = conn.cursor()
    c.execute("SELECT keyword FROM keywords")  # Fetch all keywords
    all_keywords = c.fetchall()

    # Normalize all keywords from the database and compare
    for db_keyword in all_keywords:
        if normalize_arabic(db_keyword[0]) == normalized_keyword:
            conn.close()
            return True  # Keyword found in the database
    conn.close()
    return False  # Keyword not found

# إضافة الكلمة إلى قاعدة البيانات مع المعنى والمثال والملاحظة (مع التطبيع)
def add_keyword(keyword, meaning, example, note=None):
    keyword = normalize_arabic(keyword)  # Apply normalization to keyword
    conn = sqlite3.connect('keywords.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO keywords (keyword, meaning, example, note) VALUES (?, ?, ?, ?)", (keyword, meaning, example, note))
        conn.commit()
        st.success(f"تمت إضافة الكلمة '{keyword}' إلى قاعدة البيانات.")
        
        # Append the data to a CSV file for backup
        append_to_csv(keyword, meaning, example)

    except sqlite3.IntegrityError:
        st.error(f"خطأ: الكلمة '{keyword}' موجودة بالفعل.")
    finally:
        conn.close()

# جلب الكلمات التي تبدأ بحرف معين مع المعنى والمثال
def fetch_keywords_by_letter(letter):
    letter = normalize_arabic(letter)  # Apply normalization
    conn = sqlite3.connect('keywords.db')
    c = conn.cursor()
    c.execute("SELECT keyword, meaning, example FROM keywords WHERE keyword LIKE ?", (letter + '%',))
    keywords = c.fetchall()
    conn.close()
    return keywords

# Append the new keyword to a CSV file for backup
def append_to_csv(keyword, meaning, example):
    file_path = 'keywords_backup.csv'
    # Create a DataFrame for the new data
    new_data = pd.DataFrame([[keyword, meaning, example]], columns=['الكلمة', 'المعنى', 'المثال'])

    # If file doesn't exist, create it with headers; otherwise, append
    if not os.path.isfile(file_path):
        new_data.to_csv(file_path, index=False, mode='w', encoding='utf-8-sig')
    else:
        new_data.to_csv(file_path, index=False, mode='a', header=False, encoding='utf-8-sig')

# Function to count the number of keywords in the database
def count_keywords():
    conn = sqlite3.connect('keywords.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM keywords")
    count = c.fetchone()[0]
    conn.close()
    return count

# Function to export all keywords from the database to a downloadable CSV file
def export_keywords_to_csv():
    conn = sqlite3.connect('keywords.db')
    c = conn.cursor()
    c.execute("SELECT keyword, meaning, example FROM keywords")
    all_keywords = c.fetchall()
    conn.close()

    # Create a DataFrame from the fetched data
    df = pd.DataFrame(all_keywords, columns=['الكلمة', 'المعنى', 'المثال'])
    
    # Create a CSV in memory (no need to save to disk)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_data = csv_buffer.getvalue()
    
    # Return the CSV data for download
    return csv_data

# تهيئة قاعدة البيانات وتحديثها عند التشغيل
init_db()
import_from_csv()  # Import the keywords from the CSV automatically on startup

# مركزية العنوان فقط وجعل باقي الواجهة باللغة العربية باستخدام CSS
st.markdown(
    """
    <style>
    .main {
        max-width: 700px;
        margin: 0 auto;
        padding: 20px;
        text-align: right;
        direction: rtl;
    }
    h1 {
        text-align: center;
    }
    .stTextInput > div, .stButton > div, .stSelectbox > div {
        display: flex;
        justify-content: flex-end;
    }
    .stAlert, .stSelectbox {
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# واجهة Streamlit
st.markdown('<div class="main">', unsafe_allow_html=True)

# Center the title using built-in h1 tag with CSS applied
st.title('معجم الكلمات العامية')

# # Example usage within Streamlit to display the keyword count
# st.subheader('إجمالي عدد الكلمات في قاعدة البيانات')
# keyword_count = count_keywords()
# st.write(f"إجمالي عدد الكلمات المسجلة: {keyword_count}")

# # زر لتصدير جميع الكلمات إلى CSV وتحميله إلى الجهاز المحلي
# csv_data = export_keywords_to_csv()
# st.download_button(label="تصدير جميع الكلمات إلى CSV", data=csv_data, file_name='all_keywords_export.csv', mime='text/csv')

# إدخال الكلمة
keyword = st.text_input('أدخل كلمة:', '').strip()

# Process keyword input
if keyword:
    final_keyword = normalize_arabic(keyword)
    keyword_exists = check_keyword(final_keyword)

    if keyword_exists:
        st.success(f"الكلمة '{final_keyword}' مسجلة بالفعل.")
    else:
        st.warning(f"الكلمة '{final_keyword}' غير موجودة. يرجى إضافة التفاصيل أدناه.")

        # Collect the additional fields (meaning, example, and optional note)
        meaning = st.text_input('أدخل معنى الكلمة:')
        example = st.text_input('أدخل مثالاً عن استخدام الكلمة:')
        note = st.text_area('أدخل ملاحظة (اختياري):')

        # زر لإضافة الكلمة
        if st.button(f'اضغط هنا لإضافة الكلمة "{final_keyword}"'):
            if meaning and example:
                add_keyword(final_keyword, meaning, example, note)
            else:
                st.error("يرجى إدخال معنى الكلمة ومثال.")
else:
    st.error("يرجى إدخال كلمة صالحة.")

# قائمة منسدلة لاختيار الحرف
selected_letter = st.selectbox('استعرض الكلمات حسب الحرف الأول', arabic_letters, index=0)  # الافتراضي إلى 'ا'

# جلب الكلمات التي تبدأ بالحرف المحدد مع المعنى والمثال
st.subheader(f"الكلمات التي تبدأ بالحرف '{selected_letter}' هي")
keywords = fetch_keywords_by_letter(selected_letter)

# Display the retrieved keyword in red, meaning and example in default style
if keywords:
    for keyword, meaning, example in keywords:
        # Make the retrieved keyword red
        st.markdown(f"<strong style='color:red;'>{keyword}</strong>  |  **المعنى**: {meaning}  |  **المثال**: {example}", unsafe_allow_html=True)

