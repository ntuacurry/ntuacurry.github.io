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