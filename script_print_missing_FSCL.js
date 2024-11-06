const endDateDisplay = document.getElementById("endDate");
const endScoreDisplay = document.getElementById("endScore");
const checkPersonDisplay = document.getElementById("checkPerson");

const endDate = sessionStorage.getItem("endDate");
const endScore = sessionStorage.getItem("endScore");
const checkPerson = sessionStorage.getItem("checkPerson");
endDateDisplay.textContent = endDate;
endScoreDisplay.textContent = endScore + "分";
checkPersonDisplay.textContent = checkPerson;

// 假設這段程式碼在第二個頁面中
document.addEventListener("DOMContentLoaded", function () {
    // 遍歷每個 reason-descript 項目並填入對應的 td
    for (let i = 1; i <= 24; i++) {
        const combinedText = sessionStorage.getItem(`reason-descript-${i}`);

        if (combinedText) {
            const targetCell = document.getElementById(`reason-${i}`);
            if (targetCell) {
                targetCell.textContent = combinedText;
                console.log(`填入 reason-${i}: ${combinedText}`);
            }
        }
    }
});
