const locationDisplay = document.getElementById("location");
const dateDisplay = document.getElementById("date");

const branch = sessionStorage.getItem("branch");
const restaurant = sessionStorage.getItem("restaurant");
locationDisplay.textContent = branch + "分公司 " + restaurant;

const date = sessionStorage.getItem("date");
dateDisplay.textContent = date;

// 從 sessionStorage 讀取 purposes 和 classes
const purposes = JSON.parse(sessionStorage.getItem('purposes')) || [];
const classes = JSON.parse(sessionStorage.getItem('classes')) || [];

// 遍歷目的和類別，讀取狀態並填充相應文字
purposes.forEach(purpose => {
	classes.forEach(className => {
		const key = `${className}-${purpose}`;
		const isChecked = sessionStorage.getItem(key) === "true"; // 檢查 checkbox 狀態
		const cellId = `${purpose}-${className}`;
		document.getElementById(cellId).innerText = isChecked ? '✓' : ''; // 若勾選則顯示勾勾，否則顯示空
	});
});

// 自動將沒有任何選項被勾選的條文改為NA
document.addEventListener("DOMContentLoaded", function() {
    // 選取所有行
    const rows = document.querySelectorAll("table tr");

    // 遍歷每一行
    rows.forEach(row => {
        // 選取當前行中所有的 checkbox-column 儲存格
        const checkboxCells = row.querySelectorAll("td.checkbox-column");

        // 如果該行有三個 checkbox-column 儲存格，則進行處理
        if (checkboxCells.length === 3) {
            // 檢查是否所有 checkbox-column 儲存格都為空
            const allEmpty = Array.from(checkboxCells).every(cell => cell.textContent.trim() === "");

            // 如果所有儲存格都為空，進行合併
            if (allEmpty) {
                // 合併三個儲存格，並填入 "NA"
                checkboxCells[0].setAttribute("colspan", "3");
                checkboxCells[0].textContent = "NA";

                // 移除剩餘的兩個儲存格
                checkboxCells[1].remove();
                checkboxCells[2].remove();
            }
        }
    });
});
