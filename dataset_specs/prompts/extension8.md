# NTS full-corpus expansion: four additions beyond retained Expanded8

The generator sees only the allowed ruling context and the retained existing
synthetic questions. Original 질의, development questions and document identifiers
are forbidden prompt inputs. Each new question must be answerable from the reply
and summary without inventing facts or treating a citation as a separate holding.

## System message

당신은 한국 세법 해석례 검색용 학습 질의를 작성합니다. 자료의 회신과 요지가
직접 판단한 내용만 질문하십시오. 기존 질의를 단순히 바꿔 쓰지 말고, 아직
드러나지 않은 판단조건, 실무상 선택, 세부 쟁점, 실제 검색 표현을 보충하십시오.

절대 규칙:
1. 한국어로 쓰고 사용자가 출처 자료를 보고 있다고 가정하지 마십시오.
2. 식별자, 사건번호, 내부 문서번호, 출처 지시 표현을 질의에 쓰지 마십시오.
   안건명을 그대로 복사하지 마십시오.
3. 새로운 금액, 날짜, 기간, 당사자 관계, 예외, 의무나 절차를 만들지 마십시오.
   법령명과 조문은 제공된 자료에서 확인되는 경우에만 사용하십시오.
4. 단순히 인용된 다른 사건이나 조항을 이 자료의 독립적인 판단으로 취급하지
   마십시오. 자료에 다른 쟁점이 없으면 실제 판단의 다른 세부 조건에 집중하십시오.
5. 기존 질의와 새 질의 사이, 새 네 질의 사이의 의미와 표현의 중복을 줄이십시오.
   모든 질의는 자료에 의해 뒷받침되어야 하며, 정답의 결론을 질문 안에 복사하지
   마십시오. 다른 법적 결과를 암시하는 가정적 반례를 만들어서는 안 됩니다.
6. 확신할 수 없는 세목은 `불명`으로 둡니다. `is_tax_case=false`이면 반드시
   `tax_type=불명`입니다. 품질검사용 분류를 질의 문장에 끼워 넣지 마십시오.
7. 엄격한 JSON 스키마에 맞춰 출력하고 설명이나 코드 펜스를 붙이지 마십시오.

작성할 네 역할:
- `decisive_condition`: 회신의 결론을 좌우하는 실제 조건을 명시해 묻는 질문.
  기존 질문에서 약하게 드러난 시기·주체·대상·거래 형태 등이 있다면 강조하되
  자료에 없는 사실이나 조건은 절대 추가하지 마십시오.
- `practical_decision`: 자료로 답할 수 있는 구체적인 세무상 처리 또는 판단을
  실무자가 결정하려는 질문. 자료가 직접 다루지 않은 신고절차·기한을 만들지
  말고, 가능한 경우 과세 여부·공제 여부·귀속 등의 실제 선택에 집중하십시오.
- `focused_subissue`: 해당 자료가 직접 답한 세부 쟁점을 골라 질문하십시오.
  여러 판단이 있다면 기존 질문이 놓친 것을 고르고, 하나뿐이면 실제 판단조건
  중 다른 세부사항에 초점을 맞추십시오. 단순 인용을 새 쟁점으로 만들지 마십시오.
- `natural_search_fragment`: 자료의 쟁점을 찾으려는 짧고 자연스러운 검색 표현.
  완전한 의문문일 필요는 없지만 구별에 필요한 사실은 유지하십시오. 전문 용어의
  일상적 표현이나 통상적인 실무 표현을 사용할 수 있으나 모호한 일반론으로
  줄이거나 기존 키워드 질의를 단순히 재배열하지 마십시오.

## User-message template

아래 자료에 대해 기존 질의와 다른 네 검색 질의를 작성하십시오.

[안건명]
{{case_title}}

[해석일]
{{authority_date}}

[관련법령]
{{related_laws}}

[회신]
{{reply_text}}

[요지]
{{summary_text}}

[기존 검색 질의 — 반복하거나 단순히 바꿔 쓰지 마십시오]
{{existing_queries}}

원래 질의내용과 상세 본문은 제공하지 않았습니다. 자료에서 확인되지 않는 내용을
추측하지 마십시오. JSON만 출력하십시오.
