const API_BASE_URL = "http://127.0.0.1:8000";


// =====================================================
// STATE
// =====================================================

let currentQuestions = [];

let currentContent = "";

let currentQuizMode = "normal";

let lastAnalysis = null;

/*
เก็บประวัติผลการทำแบบทดสอบ

ตัวอย่าง:

[
    {
        mode: "normal",
        correct: 3,
        total: 5,
        percentage: 60
    },
    {
        mode: "remedial",
        correct: 4,
        total: 5,
        percentage: 80
    }
]
*/

let scoreHistory = [];


// =====================================================
// DOM
// =====================================================

const contentInput =
    document.getElementById(
        "lesson-content"
    );

const questionCountInput =
    document.getElementById(
        "question-count"
    );

const questionTypeInput =
    document.getElementById(
        "question-type"
    );

const difficultyInput =
    document.getElementById(
        "difficulty-level"
    );


const generateButton =
    document.getElementById(
        "btn-generate"
    );

const generateButtonText =
    document.getElementById(
        "btn-text"
    );

const generateSpinner =
    document.getElementById(
        "btn-spinner"
    );


const errorBox =
    document.getElementById(
        "error-box"
    );

const errorMessage =
    document.getElementById(
        "error-message"
    );


const quizSection =
    document.getElementById(
        "quiz-section"
    );

const questionsContainer =
    document.getElementById(
        "questions-container"
    );

const quizBadge =
    document.getElementById(
        "quiz-badge"
    );

const quizTitle =
    document.getElementById(
        "quiz-title"
    );

const quizModeText =
    document.getElementById(
        "quiz-mode-text"
    );


const progressText =
    document.getElementById(
        "progress-text"
    );

const progressFill =
    document.getElementById(
        "progress-fill"
    );


const submitQuizButton =
    document.getElementById(
        "btn-submit-quiz"
    );


const scoreSection =
    document.getElementById(
        "score-section"
    );

const scoreUser =
    document.getElementById(
        "score-user"
    );

const scoreMax =
    document.getElementById(
        "score-max"
    );

const scorePercentage =
    document.getElementById(
        "score-percentage"
    );

const scoreFeedback =
    document.getElementById(
        "score-feedback"
    );


const learningDashboard =
    document.getElementById(
        "learning-dashboard"
    );

const dashboardContent =
    document.getElementById(
        "dashboard-content"
    );


// =====================================================
// INITIAL
// =====================================================

console.log(
    "QuizGen AI loaded successfully"
);


// =====================================================
// GENERATE NORMAL QUIZ
// =====================================================

generateButton.addEventListener(
    "click",
    generateQuiz
);


async function generateQuiz() {

    hideError();


    const content =
        contentInput.value.trim();


    if (!content) {

        showError(
            "กรุณากรอกเนื้อหาบทเรียนก่อน"
        );

        return;
    }


    setGenerateLoading(true);


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/quiz/generate`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        content:
                            content,

                        question_count:
                            Number(
                                questionCountInput.value
                            ),

                        question_type:
                            questionTypeInput.value,

                        difficulty:
                            difficultyInput.value
                    })
                }
            );


        const result =
            await response.json();


        console.log(
            "Generate response:",
            result
        );


        if (!response.ok) {

            throw new Error(
                getErrorMessage(
                    result,
                    "ไม่สามารถสร้างข้อสอบได้"
                )
            );
        }


        if (
            !Array.isArray(
                result.questions
            )
        ) {

            throw new Error(
                "Backend ไม่ได้ส่งรายการข้อสอบกลับมา"
            );
        }


        if (
            result.questions.length === 0
        ) {

            throw new Error(
                "AI ไม่ได้สร้างข้อสอบกลับมา"
            );
        }


        /*
        เมื่อสร้างข้อสอบใหม่จากเนื้อหาหลัก
        ให้ถือว่าเป็น Session ใหม่
        */

        scoreHistory = [];

        lastAnalysis = null;


        learningDashboard.classList.add(
            "hidden"
        );


        currentQuestions =
            result.questions;

        currentContent =
            content;

        currentQuizMode =
            "normal";


        renderQuiz();


    } catch (error) {

        console.error(error);

        showError(
            `เกิดข้อผิดพลาด: ${error.message}`
        );

    } finally {

        setGenerateLoading(false);

    }
}


// =====================================================
// RENDER QUIZ
// =====================================================

function renderQuiz() {

    hideError();


    questionsContainer.innerHTML =
        "";


    if (
        currentQuizMode ===
        "remedial"
    ) {

        quizTitle.textContent =
            "🔄 แบบทดสอบแก้จุดอ่อน";

        quizModeText.textContent =
            "ข้อสอบชุดนี้สร้างจากหัวข้อที่ AI วิเคราะห์ว่าควรทบทวน";

        quizBadge.textContent =
            `${currentQuestions.length} ข้อ`;

    } else {

        quizTitle.textContent =
            "📝 แบบทดสอบ";

        quizModeText.textContent =
            "แบบทดสอบจากเนื้อหาบทเรียน";

        quizBadge.textContent =
            `${currentQuestions.length} ข้อ`;

    }


    currentQuestions.forEach(
        (question, index) => {

            const questionElement =
                document.createElement(
                    "div"
                );


            questionElement.className =
                "quiz-question";


            const options =
                Array.isArray(
                    question.options
                )
                    ? question.options
                    : [];


            const optionsHTML =
                options
                    .map(option => {

                        return `

                            <label class="quiz-option">

                                <input
                                    type="radio"
                                    name="question-${index}"
                                    value="${escapeAttribute(option)}"
                                >

                                <span>
                                    ${escapeHtml(option)}
                                </span>

                            </label>

                        `;

                    })
                    .join("");


            questionElement.innerHTML = `

                <div class="question-number">
                    ข้อ ${index + 1}
                </div>

                <div class="question-text">
                    ${escapeHtml(
                        question.question
                    )}
                </div>

                <div class="options">
                    ${optionsHTML}
                </div>

            `;


            questionsContainer.appendChild(
                questionElement
            );


            const radioButtons =
                questionElement.querySelectorAll(
                    'input[type="radio"]'
                );


            radioButtons.forEach(
                radio => {

                    radio.addEventListener(
                        "change",
                        updateProgress
                    );

                }
            );

        }
    );


    quizSection.classList.remove(
        "hidden"
    );


    scoreSection.classList.add(
        "hidden"
    );


    removeAnalysisDetails();


    updateProgress();


    quizSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// =====================================================
// PROGRESS
// =====================================================

function updateProgress() {

    const total =
        currentQuestions.length;


    if (total === 0) {

        progressText.textContent =
            "0 / 0 ข้อ";

        progressFill.style.width =
            "0%";

        return;
    }


    let answered =
        0;


    for (
        let index = 0;
        index < total;
        index++
    ) {

        const selected =
            document.querySelector(
                `input[name="question-${index}"]:checked`
            );


        if (selected) {

            answered++;

        }
    }


    const percentage =
        Math.round(
            (answered / total) * 100
        );


    progressText.textContent =
        `${answered} / ${total} ข้อ`;


    progressFill.style.width =
        `${percentage}%`;
}


// =====================================================
// SUBMIT QUIZ
// =====================================================

submitQuizButton.addEventListener(
    "click",
    submitQuiz
);


async function submitQuiz() {

    hideError();


    if (
        currentQuestions.length === 0
    ) {

        showError(
            "ยังไม่มีข้อสอบ"
        );

        return;
    }


    const answers =
        [];


    for (
        let index = 0;
        index < currentQuestions.length;
        index++
    ) {

        const selected =
            document.querySelector(
                `input[name="question-${index}"]:checked`
            );


        if (!selected) {

            showError(
                `กรุณาตอบข้อ ${index + 1} ก่อนส่งคำตอบ`
            );


            const questionElement =
                document
                    .querySelector(
                        `input[name="question-${index}"]`
                    )
                    ?.closest(
                        ".quiz-question"
                    );


            questionElement
                ?.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });


            return;
        }


        const question =
            currentQuestions[index];


        answers.push({

            question:
                question.question,

            options:
                question.options,

            answer:
                question.answer,

            explanation:
                question.explanation || "",

            topic:
                question.topic || "",

            user_answer:
                selected.value

        });

    }


    setSubmitLoading(true);


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/quiz/analyze`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        questions:
                            answers
                    })
                }
            );


        const result =
            await response.json();


        console.log(
            "Analyze:",
            result
        );


        if (!response.ok) {

            throw new Error(
                getErrorMessage(
                    result,
                    "ไม่สามารถวิเคราะห์ผลได้"
                )
            );
        }


        lastAnalysis =
            result.data;


        saveScoreHistory(
            result.data
        );


        renderScore(
            result.data
        );


        renderDashboard();


    } catch (error) {

        console.error(error);

        showError(
            `เกิดข้อผิดพลาดในการวิเคราะห์: ${error.message}`
        );

    } finally {

        setSubmitLoading(false);

    }
}


// =====================================================
// SCORE HISTORY
// =====================================================

function saveScoreHistory(data) {

    scoreHistory.push({

        attempt:
            scoreHistory.length + 1,

        mode:
            currentQuizMode,

        correct:
            data.correct_count,

        total:
            data.total_questions,

        percentage:
            Number(
                data.score_percentage
            ),

        weakTopics:
            data.weak_topics.map(
                item => item.topic
            )

    });


    console.log(
        "Score History:",
        scoreHistory
    );
}


// =====================================================
// RENDER SCORE
// =====================================================

function renderScore(data) {

    scoreUser.textContent =
        data.correct_count;


    scoreMax.textContent =
        data.total_questions;


    scorePercentage.textContent =
        `${data.score_percentage}%`;


    const percentage =
        Number(
            data.score_percentage
        );


    if (percentage >= 80) {

        scoreFeedback.innerHTML = `

            <div class="feedback-success">

                🎉 ทำได้ดีมาก
                มีความเข้าใจเนื้อหาในระดับดี

            </div>

        `;

    } else if (percentage >= 50) {

        scoreFeedback.innerHTML = `

            <div class="feedback-warning">

                👍 ทำได้ดี
                แต่ยังมีบางหัวข้อที่ควรทบทวนเพิ่มเติม

            </div>

        `;

    } else {

        scoreFeedback.innerHTML = `

            <div class="feedback-error">

                📖 ควรทบทวนเนื้อหาบางหัวข้อ
                ก่อนทำแบบทดสอบอีกครั้ง

            </div>

        `;

    }


    scoreSection.classList.remove(
        "hidden"
    );


    renderAnalysisDetails(
        data
    );


    scoreSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// =====================================================
// ANALYSIS DETAIL
// =====================================================

function renderAnalysisDetails(data) {

    removeAnalysisDetails();


    const analysisDiv =
        document.createElement(
            "div"
        );


    analysisDiv.id =
        "analysis-details";


    const weakTopicsHTML =
        data.weak_topics.length > 0

            ? data.weak_topics
                .map(topic => `

                    <div class="weak-topic">

                        <h4>
                            ⚠️
                            ${escapeHtml(
                                topic.topic
                            )}
                        </h4>

                        <p>
                            <strong>
                                จำนวนข้อที่ผิด:
                            </strong>

                            ${topic.wrong_count}
                        </p>

                        <p>
                            <strong>
                                สาเหตุ:
                            </strong>

                            ${escapeHtml(
                                topic.reason
                            )}
                        </p>

                        <p>
                            <strong>
                                คำแนะนำ:
                            </strong>

                            ${escapeHtml(
                                topic.recommendation
                            )}
                        </p>

                    </div>

                `)
                .join("")

            : `

                <p>
                    🎉 ไม่พบหัวข้อที่เป็นจุดอ่อน
                </p>

            `;


    const wrongQuestionsHTML =
        data.wrong_questions.length > 0

            ? data.wrong_questions
                .map(item => `

                    <div class="wrong-question">

                        <h4>
                            ข้อ ${item.question_index}
                        </h4>

                        <p>
                            ${escapeHtml(
                                item.question
                            )}
                        </p>

                        <p>
                            <strong>
                                คำตอบของคุณ:
                            </strong>

                            ${escapeHtml(
                                item.user_answer
                            )}
                        </p>

                        <p>
                            <strong>
                                คำตอบที่ถูก:
                            </strong>

                            ${escapeHtml(
                                item.correct_answer
                            )}
                        </p>

                        <p>
                            <strong>
                                คำอธิบาย:
                            </strong>

                            ${escapeHtml(
                                item.explanation
                            )}
                        </p>

                    </div>

                `)
                .join("")

            : `

                <p>
                    🎉 ไม่มีข้อที่ตอบผิด
                </p>

            `;


    const recommendations =
        Array.isArray(
            data.study_recommendations
        )

            ? data.study_recommendations

            : [];


    const recommendationsHTML =
        recommendations
            .map(item => `

                <li>
                    ${escapeHtml(item)}
                </li>

            `)
            .join("");


    analysisDiv.innerHTML = `

        <div class="analysis-box">

            <h3>
                🧠 AI วิเคราะห์ผล
            </h3>

            <p>

                ${escapeHtml(
                    data.overall_analysis ||
                    "ไม่มีข้อมูลการวิเคราะห์"
                )}

            </p>

        </div>



        <div class="weak-topic-box">

            <h3>
                ⚠️ หัวข้อที่ควรทบทวน
            </h3>

            ${weakTopicsHTML}

        </div>



        <div class="recommendation-box">

            <h3>
                📚 คำแนะนำในการเรียน
            </h3>

            <ul>
                ${recommendationsHTML}
            </ul>

        </div>



        <div class="wrong-question-box">

            <h3>
                ❌ ข้อที่ตอบผิด
            </h3>

            ${wrongQuestionsHTML}

        </div>



        ${
            data.weak_topics.length > 0

                ? `

                    <div class="remedial-action">

                        <button
                            id="btn-remedial"
                            class="btn-primary"
                            type="button"
                        >

                            🔄 สร้างข้อสอบแก้จุดอ่อน

                        </button>

                    </div>

                `

                : ""
        }

    `;


    scoreSection.appendChild(
        analysisDiv
    );


    const remedialButton =
        document.getElementById(
            "btn-remedial"
        );


    if (remedialButton) {

        remedialButton.addEventListener(
            "click",
            generateRemedialQuiz
        );

    }
}


// =====================================================
// REMOVE ANALYSIS
// =====================================================

function removeAnalysisDetails() {

    const analysis =
        document.getElementById(
            "analysis-details"
        );


    if (analysis) {

        analysis.remove();

    }
}


// =====================================================
// GENERATE REMEDIAL QUIZ
// =====================================================

async function generateRemedialQuiz() {

    hideError();


    if (!lastAnalysis) {

        showError(
            "ยังไม่มีผลการวิเคราะห์"
        );

        return;
    }


    const weakTopics =
        lastAnalysis.weak_topics
            .map(
                item => item.topic
            )
            .filter(Boolean);


    if (
        weakTopics.length === 0
    ) {

        showError(
            "ไม่พบหัวข้อที่ต้องทบทวน"
        );

        return;
    }


    const button =
        document.getElementById(
            "btn-remedial"
        );


    if (button) {

        button.disabled =
            true;

        button.textContent =
            "กำลังสร้างข้อสอบแก้จุดอ่อน...";

    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/quiz/remedial`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        original_content:
                            currentContent,

                        weak_topics:
                            weakTopics,

                        question_count:
                            Number(
                                questionCountInput.value
                            ),

                        difficulty:
                            difficultyInput.value

                    })
                }
            );


        const result =
            await response.json();


        console.log(
            "Remedial:",
            result
        );


        if (!response.ok) {

            throw new Error(
                getErrorMessage(
                    result,
                    "ไม่สามารถสร้างข้อสอบแก้จุดอ่อนได้"
                )
            );
        }


        if (
            !Array.isArray(
                result.questions
            ) ||
            result.questions.length === 0
        ) {

            throw new Error(
                "Backend ไม่ได้ส่งข้อสอบแก้จุดอ่อนกลับมา"
            );
        }


        currentQuestions =
            result.questions;


        currentQuizMode =
            "remedial";


        renderQuiz();


    } catch (error) {

        console.error(error);


        showError(
            `เกิดข้อผิดพลาด: ${error.message}`
        );

    } finally {

        if (button) {

            button.disabled =
                false;

            button.textContent =
                "🔄 สร้างข้อสอบแก้จุดอ่อน";

        }

    }
}


// =====================================================
// LEARNING DASHBOARD
// =====================================================

function renderDashboard() {

    if (
        scoreHistory.length === 0
    ) {

        learningDashboard
            .classList.add(
                "hidden"
            );

        return;
    }


    learningDashboard
        .classList.remove(
            "hidden"
        );


    const firstAttempt =
        scoreHistory[0];


    const latestAttempt =
        scoreHistory[
            scoreHistory.length - 1
        ];


    const improvement =
        latestAttempt.percentage -
        firstAttempt.percentage;


    let improvementText =
        "0%";


    let improvementClass =
        "same";


    let improvementIcon =
        "➖";


    if (improvement > 0) {

        improvementText =
            `+${improvement.toFixed(0)}%`;

        improvementClass =
            "good";

        improvementIcon =
            "📈";

    } else if (improvement < 0) {

        improvementText =
            `${improvement.toFixed(0)}%`;

        improvementClass =
            "bad";

        improvementIcon =
            "📉";

    }


    const historyHTML =
        scoreHistory
            .map(item => {

                const modeText =
                    item.mode === "remedial"

                        ? "🔄 แบบทดสอบแก้จุดอ่อน"

                        : "📝 แบบทดสอบครั้งแรก";


                return `

                    <div class="history-item">

                        <div>

                            <div class="history-mode">

                                ครั้งที่
                                ${item.attempt}

                            </div>

                            <small>
                                ${modeText}
                            </small>

                        </div>


                        <div class="history-score">

                            ${item.correct}
                            /
                            ${item.total}

                            (${item.percentage}%)

                        </div>

                    </div>

                `;

            })
            .join("");


    dashboardContent.innerHTML = `

        <div class="dashboard-grid">


            <div class="dashboard-card">

                <div class="dashboard-label">
                    คะแนนครั้งแรก
                </div>

                <div class="dashboard-value">
                    ${firstAttempt.percentage}%
                </div>

            </div>



            <div class="dashboard-card">

                <div class="dashboard-label">
                    คะแนนล่าสุด
                </div>

                <div class="dashboard-value">
                    ${latestAttempt.percentage}%
                </div>

            </div>



            <div class="dashboard-card">

                <div class="dashboard-label">
                    การเปลี่ยนแปลง
                </div>

                <div
                    class="
                        dashboard-value
                        ${improvementClass}
                    "
                >

                    ${improvementIcon}

                    ${improvementText}

                </div>

            </div>


        </div>



        <div class="score-comparison">

            <h3>
                📊 เปรียบเทียบคะแนน
            </h3>


            <div class="comparison-row">

                <div class="comparison-name">
                    ครั้งแรก
                </div>

                <div class="comparison-bar">

                    <div
                        class="comparison-fill"
                        style="
                            width:
                            ${firstAttempt.percentage}%;
                        "
                    ></div>

                </div>

                <div class="comparison-score">

                    ${firstAttempt.percentage}%

                </div>

            </div>



            <div class="comparison-row">

                <div class="comparison-name">
                    ครั้งล่าสุด
                </div>

                <div class="comparison-bar">

                    <div
                        class="comparison-fill"
                        style="
                            width:
                            ${latestAttempt.percentage}%;
                        "
                    ></div>

                </div>

                <div class="comparison-score">

                    ${latestAttempt.percentage}%

                </div>

            </div>

        </div>



        <div class="history-section">

            <h3>
                🕒 ประวัติการทำแบบทดสอบ
            </h3>

            <div class="history-list">

                ${historyHTML}

            </div>

        </div>

    `;
}


// =====================================================
// GENERATE LOADING
// =====================================================

function setGenerateLoading(
    loading
) {

    generateButton.disabled =
        loading;


    if (loading) {

        generateButtonText.textContent =
            "กำลังสร้างข้อสอบ...";


        generateSpinner
            .classList.remove(
                "hidden"
            );

    } else {

        generateButtonText.textContent =
            "✨ สร้างข้อสอบ";


        generateSpinner
            .classList.add(
                "hidden"
            );

    }
}


// =====================================================
// SUBMIT LOADING
// =====================================================

function setSubmitLoading(
    loading
) {

    submitQuizButton.disabled =
        loading;


    if (loading) {

        submitQuizButton.textContent =
            "🧠 AI กำลังวิเคราะห์...";

    } else {

        submitQuizButton.textContent =
            "✅ ส่งคำตอบ";

    }
}


// =====================================================
// ERROR
// =====================================================

function showError(
    message
) {

    errorMessage.textContent =
        message;


    errorBox.classList.remove(
        "hidden"
    );


    errorBox.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
}


function hideError() {

    errorBox.classList.add(
        "hidden"
    );

}


// =====================================================
// ERROR MESSAGE
// =====================================================

function getErrorMessage(
    result,
    fallback
) {

    if (!result) {

        return fallback;

    }


    if (
        typeof result.detail ===
        "string"
    ) {

        return result.detail;

    }


    if (
        typeof result.message ===
        "string"
    ) {

        return result.message;

    }


    if (
        Array.isArray(
            result.detail
        )
    ) {

        return result.detail
            .map(item => {

                return (
                    item.msg ||
                    JSON.stringify(item)
                );

            })
            .join(", ");

    }


    return fallback;
}


// =====================================================
// SECURITY
// =====================================================

function escapeHtml(
    value
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        value ?? "";


    return div.innerHTML;
}


function escapeAttribute(
    value
) {

    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        );
}