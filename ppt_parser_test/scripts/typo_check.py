import google.generativeai as genai
import time  # 시간 측정을 위해 추가

# API 키 설정
genai.configure(api_key="YOUR_API_KEY")  # 여기에 실제 API 키를 입력하세요

def check_spelling(text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    아래 문장의 맞춤법, 오타, 띄어쓰기를 교정해 줘. 교정된 문장만 출력해.
    문장: '{text}'
    """
    
    start_time = time.time()  # 시작 시간 기록
    response = model.generate_content(prompt)
    end_time = time.time()    # 끝난 시간 기록
    
    elapsed_time = end_time - start_time  # 경과 시간 계산
    print(f"검사 소요 시간: {elapsed_time:.2f}초")  # 초 단위 출력
    
    # 응답에서 교정된 텍스트를 추출
    corrected_text = response.text.strip()
    return corrected_text

# # 사용 예시
# sentence = "어제는 친구랑 같이 도서관에 갔다 왓다. 도서관에 들어가자마자 조용한 분위기 때문에 말한마디도 크게 하기가 망설여 졌다. 나는 평소에 읽고 싶엇던 소설책을 찾으려 했지만 찾는 책이 어디있는지 잘 모르겠어서 한참을 헤메였다. 결국 사서에게 물어보고 책을 찾았는데 책이 생각보다 두껍고 내용이 어려워서 읽는데 시간이 많이 걸릴거 같았다. 친구는 이미 자기 자리에서 노트북을 켜고 공부를 시작했는데 나는 책장을 넘기면서 내용에 집중햇다. 잠시후 밖을 보니 해가 점점 저물고 있었고 도서관안은 더 조용해 졌다. 그때 나는 ‘내일은 더 일찍 와서 공부해야지’ 라는 생각이 들엇다."
# corrected_sentence = check_spelling(sentence)

# print("원본 문장:", sentence)
# print("교정된 문장:", corrected_sentence)
