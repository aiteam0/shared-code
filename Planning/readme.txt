
/* 코드 블록 overflow 처리 - 코드 스니펫이 화면을 넘어가는 문제 해결 */
.stCode, pre, code {
    overflow-x: auto;
    word-wrap: break-word;
    white-space: pre-wrap;
    max-width: 100%;
    box-sizing: border-box;
}

/* 채팅 메시지 내 코드 블록 특별 처리 */
.css-1c7y2kd pre, .css-1c7y2kd code {
    overflow-x: auto;
    word-wrap: break-word;
    white-space: pre-wrap;
    max-width: 100%;
    background: rgba(0, 0, 0, 0.05);
    padding: 0.5rem;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
}

/* 인라인 코드 스타일링 */
code:not(pre code) {
    background: rgba(0, 102, 204, 0.1);
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-size: 0.9em;
}
