import streamlit as st
import sys
import os
import glob

sys.path.insert(0, "/app")

st.set_page_config(page_title="Social Content — GFCRI", page_icon="", layout="wide")

from dashboard.style import inject_css, metric_card, COLORS

inject_css()

st.markdown("# Social Content")
st.caption("Auto-generated content for WeChat Official Account and Zsxq")

output_dir = "/app/output"

if not os.path.exists(output_dir):
    st.info("No social content generated yet. Content is created during each daily analysis run.")
    st.stop()

html_files = sorted(glob.glob(f"{output_dir}/wechat_*.html"), reverse=True)
txt_files = sorted(glob.glob(f"{output_dir}/zsxq_*.txt"), reverse=True)
img_files = sorted(glob.glob(f"{output_dir}/gfcri_card_*.png"), reverse=True)

tab1, tab2, tab3 = st.tabs(["WeChat Article", "Zsxq Post", "Share Card"])

with tab1:
    st.markdown("### WeChat Official Account Preview")
    if html_files:
        latest = html_files[0]
        date_str = os.path.basename(latest).replace("wechat_", "").replace(".html", "")
        st.caption(f"Date: {date_str}")

        with open(latest, "r", encoding="utf-8") as f:
            html_content = f.read()

        st.components.v1.html(html_content, height=900, scrolling=True)

        st.download_button(
            "Download HTML", data=html_content,
            file_name=os.path.basename(latest), mime="text/html",
        )
    else:
        st.info("No WeChat article generated yet.")

with tab2:
    st.markdown("### Zsxq Post Preview")
    if txt_files:
        latest = txt_files[0]
        date_str = os.path.basename(latest).replace("zsxq_", "").replace(".txt", "")
        st.caption(f"Date: {date_str}")

        with open(latest, "r", encoding="utf-8") as f:
            text_content = f.read()

        st.code(text_content, language=None)

        st.download_button(
            "Download Text", data=text_content,
            file_name=os.path.basename(latest), mime="text/plain",
        )

        st.markdown("---")
        st.caption("Copy the text above and paste directly into Zsxq.")
    else:
        st.info("No Zsxq post generated yet.")

with tab3:
    st.markdown("### Share Card Preview")
    if img_files:
        latest = img_files[0]
        date_str = os.path.basename(latest).replace("gfcri_card_", "").replace(".png", "")
        st.caption(f"Date: {date_str}")

        st.image(latest, width=400)

        with open(latest, "rb") as f:
            img_data = f.read()
        st.download_button(
            "Download PNG", data=img_data,
            file_name=os.path.basename(latest), mime="image/png",
        )
    else:
        st.info("No share card generated yet.")
