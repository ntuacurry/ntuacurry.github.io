
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
                    cellMiss.className = "describe-area";

                    cellMiss.setAttribute("colspan", "2");

                    cellGrade.textContent = item.missGrade;
                    cellText.textContent = `${itemSum}. ${item.missText}`;

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
                    cellMiss.className = "describe-area";

                    cellMiss.setAttribute("colspan", "2");

                    cellGrade.textContent = item.missGrade;
                    cellText.textContent = `${itemSum}. ${item.missText}`;

                    itemSum += 1;
                };
            });
        });

        // 從 localStorage 取得選取的項目資料
        const selectedData = JSON.parse(localStorage.getItem("checkedItems") || "[]");

        const rows = tbodyCheck.querySelectorAll("tr");

        rows.forEach(row => {
            const textCell = row.querySelector(".content");
            const checkCell = row.querySelector(".check");
            const describeCell = row.querySelector(".describe-area");

            if (textCell && checkCell && describeCell) {
                const rawText = textCell.textContent.trim();

                // 嘗試在 selectedData 中找有沒有對應的條文
                const match = selectedData.find(item => rawText.endsWith(item.text.trim()));

                if (match) {
                    checkCell.textContent = "X";
                    describeCell.innerHTML = match.describe.replace(/\n/g, "<br>");
                }
            }
        });

        // 建議事項填入
        const adviseContentTd = document.querySelector(".advise-area");
        const adviseText = localStorage.getItem("adviseText") || "";
        if (adviseContentTd && adviseText) {
            adviseContentTd.innerHTML = adviseText.replace(/\n/g, "<br>");
        }
    })