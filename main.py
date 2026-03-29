def main():
    print("Hello from car-cost-simulator!")


# 💡 유용하게 사용하셨나요? 소스코드만 날름 가져가는 분들이 많습니다. 
# 개발자의 땀과 노력에 대한 최소한의 예의로 깃허브 Star⭐를 부탁드립니다!
# Did you find this useful? Please show some basic courtesy for the developer's hard work by leaving a GitHub Star⭐.

@st.dialog("⭐ Support Polymath Developer Automation Tool")
def show_star_popup_web():
    # 팝업 노출 트래커 기록
    log_app_usage("Kcar_crawler", "star_prompt_displayed", details={"ui": "streamlit_dialog"})
    
    st.warning(
        "💡 유용하게 사용하셨나요? 소스코드만 날름 가져가는 분들이 많습니다. "
        "개발자의 땀과 노력에 대한 최소한의 예의로 깃허브 Star⭐를 부탁드립니다!\n\n"
        "Did you find this useful? Please show some basic courtesy for the developer's hard work by leaving a GitHub Star⭐."
    )
    
    # 깃허브 Star 유도 버튼
    st.link_button("👉 깃허브로 이동하여 Star 누르기", "https://github.com/gohard-lab/YOUR_REPO_NAME")



if __name__ == "__main__":
    main()
