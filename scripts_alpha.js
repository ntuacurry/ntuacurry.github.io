
const checkList = document.querySelector(".checkList");
const tbodyCheck = checkList.querySelector("tbody");

const typeCount = {};
fetch("https://ntuacurry.github.io/missing_alpha.json")
    .then(response => response.json())
    .then(data => {
        let i = 0;

        data.forEach(item => {
            i += 1;

            if (typeCount[item.missType]) {
                typeCount[item.missType]++;
            } else {
                typeCount[item.missType] = 1;
            }
        });
        
        let itemSum = 1;
        Object.keys(typeCount).forEach(key => {
            const row = tbodyCheck.insertRow();
            const cell = row.insertCell(0);
            cell.className = "category";
            cell.setAttribute("rowspan", `${typeCount[key]}`);
            cell.textContent = key;
            
            let j = 0;
            data.forEach(item => {
                if (item.missType == key && j == 0) {
                    const cellGrade = row.insertCell(1);
                    const cellText = row.insertCell(2);
                    const cellCheck = row.insertCell(3);
                    const cellMiss = row.insertCell(4);

                    cellGrade.className = "type";
                    cellText.className = "content";
                    cellCheck.className = "check";
                    cellMiss.className = "describe";

                    cellMiss.setAttribute("colspan", "2");

                    cellGrade.textContent = item.missGrade;
                    cellText.textContent = `${itemSum}. ${item.missText}`;

                    addRadioAndTextarea(cellCheck, cellMiss, itemSum);

                    itemSum += 1;
                    j = 1;
                } else if (item.missType == key){
                    const rowMiss = tbodyCheck.insertRow();
                    const cellGrade = rowMiss.insertCell(0);
                    const cellText = rowMiss.insertCell(1);
                    const cellCheck = rowMiss.insertCell(2);
                    const cellMiss = rowMiss.insertCell(3);

                    cellGrade.className = "type";
                    cellText.className = "content";
                    cellCheck.className = "check";
                    cellMiss.className = "describe";

                    // cellText.setAttribute("colspan", "2");
                    cellMiss.setAttribute("colspan", "2");

                    cellGrade.textContent = item.missGrade;
                    cellText.textContent = `${itemSum}. ${item.missText}`;

                    addRadioAndTextarea(cellCheck, cellMiss, itemSum);

                    itemSum += 1;
                };
            });
        });
    })

function addRadioAndTextarea(cellCheck, cellMiss, index) {
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = `radio-${index}`; // 保持唯一性，單獨可取消
    radio.dataset.index = index;

    const textarea = document.createElement("textarea");
    textarea.style.display = "none";
    cellMiss.appendChild(textarea);

    let previouslyChecked = false;

    radio.addEventListener("click", function () {
        if (radio.checked && previouslyChecked) {
        radio.checked = false;
        textarea.style.display = "none";
        previouslyChecked = false;
        } else {
        textarea.style.display = radio.checked ? "block" : "none";
        previouslyChecked = radio.checked;
        }
    });

    cellCheck.appendChild(radio);
    }

// 跳轉到列印頁的功能
function saveCheckedData() {
    const result = [];

    const rows = document.querySelectorAll(".checkList tbody tr");

    rows.forEach(row => {
        const radio = row.querySelector("input[type='radio']");
        const text = row.querySelector(".content")?.textContent || "";
        const textarea = row.querySelector("textarea");

        if (radio && radio.checked) {
            result.push({
                text: text.trim(),
                describe: (textarea?.value || "").trim()
            });
        }
    });

    // 🔹 取得建議事項文字
    const adviseText = document.querySelector(".advise")?.value || "";

    // 🔹 存入 localStorage
    localStorage.setItem("checkedItems", JSON.stringify(result));
    localStorage.setItem("adviseText", adviseText);

    // 🔹 跳轉到結果頁面
    window.open("阿爾法食品安全衛生評核紀錄表 列印頁.html");
}