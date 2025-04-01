# Python與C#語法對照教材

## 目錄
1. [簡介](#簡介)
2. [環境設置](#環境設置)
3. [基本語法](#基本語法)
   - [變數與數據類型](#變數與數據類型)
   - [運算符](#運算符)
   - [註釋](#註釋)
   - [輸入與輸出](#輸入與輸出)
4. [流程控制](#流程控制)
   - [條件語句](#條件語句)
   - [循環語句](#循環語句)
5. [集合類型](#集合類型)
   - [數組/列表](#數組列表)
   - [字典/哈希表](#字典哈希表)
   - [元組](#元組)
   - [集合](#集合)
6. [函數](#函數)
   - [函數定義與調用](#函數定義與調用)
   - [參數傳遞](#參數傳遞)
   - [返回值](#返回值)
   - [lambda表達式](#lambda表達式)
7. [異常處理](#異常處理)
8. [物件導向程式設計](#物件導向程式設計)
   - [類的定義](#類的定義)
   - [繼承](#繼承)
   - [多型](#多型)
   - [封裝](#封裝)
   - [抽象類與接口](#抽象類與接口)
9. [文件操作](#文件操作)
10. [字符串處理](#字符串處理)
11. [日期和時間](#日期和時間)
12. [進階主題](#進階主題)
    - [LINQ與列表推導式](#linq與列表推導式)
    - [非同步編程](#非同步編程)
    - [事件與委託](#事件與委託)
    - [泛型](#泛型)
13. [總結與資源](#總結與資源)

## 簡介

本教材旨在為具備Python基礎知識的程式設計師提供快速學習C#的參考指南。通過對比Python與C#的語法差異和相似之處，您將能夠更高效地掌握C#程式設計。

Python和C#都是現代化的高級程式設計語言，但它們有著不同的設計哲學和應用場景：

- **Python**：解釋型語言，動態類型，強調簡潔和可讀性，廣泛用於數據分析、人工智能、Web開發和自動化腳本等領域。
- **C#**：編譯型語言，靜態類型，由Microsoft開發，主要用於Windows應用程序開發、遊戲開發（Unity）、企業級應用和Web應用程序等。

讓我們開始探索這兩種語言的差異和共同點。

## 環境設置

### Python環境設置

Python可以在官方網站（python.org）下載安裝，安裝後即可在命令行中使用`python`命令運行程式：

```python
# 創建一個簡單的Python程式 hello.py
print("Hello, World!")

# 在命令行中執行
# python hello.py
```

**輸出結果：**
```
Hello, World!
```

### C#環境設置

C#程式需要.NET環境，可以通過以下幾種方式設置：

1. 安裝Visual Studio（推薦初學者）
2. 安裝.NET SDK，使用命令行或Visual Studio Code開發

一個簡單的C#程式：

```csharp
// 創建一個簡單的C#程式 Program.cs
using System;

namespace HelloWorld
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello, World!");
        }
    }
}

// 在命令行中編譯和執行
// dotnet new console -o HelloWorld
// cd HelloWorld
// dotnet run
```

**輸出結果：**
```
Hello, World!
```

## 基本語法

### 變數與數據類型

#### Python變數與數據類型

Python是動態類型語言，變數無需聲明類型，可以隨時更改類型。

```python
# 變數定義
name = "小明"      # 字串
age = 25          # 整數
height = 175.5    # 浮點數
is_student = True # 布林值

# 查看變數類型
print(type(name))
print(type(age))
print(type(height))
print(type(is_student))

# 動態變更類型
x = 10
print(f"x是整數: {x}")
x = "現在是字串"
print(f"x現在是: {x}")
```

**輸出結果：**
```
<class 'str'>
<class 'int'>
<class 'float'>
<class 'bool'>
x是整數: 10
x現在是: 現在是字串
```

#### C#變數與數據類型

C#是靜態類型語言，變數必須聲明類型，且一旦確定，類型不能更改。

```csharp
using System;

class Program
{
    static void Main()
    {
        // 變數定義
        string name = "小明";     // 字串
        int age = 25;            // 整數
        double height = 175.5;   // 浮點數
        bool isStudent = true;   // 布林值
        
        // 查看變數類型
        Console.WriteLine(name.GetType());
        Console.WriteLine(age.GetType());
        Console.WriteLine(height.GetType());
        Console.WriteLine(isStudent.GetType());
        
        // 變更變數值但不能變更類型
        int x = 10;
        Console.WriteLine($"x是整數: {x}");
        
        // 以下會導致編譯錯誤
        // x = "現在是字串";  // 錯誤！
        
        // 如果需要改變類型，需要定義新變數或使用var關鍵字
        var y = 10;
        Console.WriteLine($"y是整數: {y}");
        // y = "現在是字串"; // 仍然錯誤！var只是類型推論，一旦確定不可更改
        
        // 必須定義新變數
        string xAsString = "現在是字串";
        Console.WriteLine($"新變數: {xAsString}");
    }
}
```

**輸出結果：**
```
System.String
System.Int32
System.Double
System.Boolean
x是整數: 10
y是整數: 10
新變數: 現在是字串
```

#### 基本數據類型對照

| Python類型 | C#類型 | 描述 |
|-----------|--------|------|
| `int` | `int`, `long` | 整數 |
| `float` | `float`, `double`, `decimal` | 浮點數 |
| `str` | `string`, `char` | 字符串/字符 |
| `bool` | `bool` | 布林值 |
| `bytes` | `byte[]` | 字節序列 |
| `None` | `null` | 空值 |
| `list` | `List<T>` | 列表/數組 |
| `tuple` | `Tuple<T...>`, `ValueTuple<T...>` | 元組 |
| `dict` | `Dictionary<TKey, TValue>` | 字典/哈希表 |
| `set` | `HashSet<T>` | 集合 |

### 運算符

#### Python運算符

```python
# 算術運算符
a, b = 10, 3
print(f"加法: {a + b}")         # 13
print(f"減法: {a - b}")         # 7
print(f"乘法: {a * b}")         # 30
print(f"除法: {a / b}")         # 3.3333...
print(f"整數除法: {a // b}")    # 3
print(f"取餘: {a % b}")         # 1
print(f"次方: {a ** b}")        # 1000

# 比較運算符
print(f"等於: {a == b}")        # False
print(f"不等於: {a != b}")      # True
print(f"大於: {a > b}")         # True
print(f"小於: {a < b}")         # False
print(f"大於等於: {a >= b}")    # True
print(f"小於等於: {a <= b}")    # False

# 邏輯運算符
x, y = True, False
print(f"and: {x and y}")        # False
print(f"or: {x or y}")          # True
print(f"not: {not x}")          # False

# 賦值運算符
c = 5
c += 3  # c = c + 3
print(f"加法賦值: {c}")         # 8
c -= 2  # c = c - 2
print(f"減法賦值: {c}")         # 6
```

**輸出結果：**
```
加法: 13
減法: 7
乘法: 30
除法: 3.3333333333333335
整數除法: 3
取餘: 1
次方: 1000
等於: False
不等於: True
大於: True
小於: False
大於等於: True
小於等於: False
and: False
or: True
not: False
加法賦值: 8
減法賦值: 6
```

#### C#運算符

```csharp
using System;

class Program
{
    static void Main()
    {
        // 算術運算符
        int a = 10, b = 3;
        Console.WriteLine($"加法: {a + b}");         // 13
        Console.WriteLine($"減法: {a - b}");         // 7
        Console.WriteLine($"乘法: {a * b}");         // 30
        Console.WriteLine($"除法: {(double)a / b}"); // 3.3333...
        Console.WriteLine($"整數除法: {a / b}");     // 3
        Console.WriteLine($"取餘: {a % b}");         // 1
        Console.WriteLine($"次方: {Math.Pow(a, b)}");// 1000

        // 比較運算符
        Console.WriteLine($"等於: {a == b}");        // False
        Console.WriteLine($"不等於: {a != b}");      // True
        Console.WriteLine($"大於: {a > b}");         // True
        Console.WriteLine($"小於: {a < b}");         // False
        Console.WriteLine($"大於等於: {a >= b}");    // True
        Console.WriteLine($"小於等於: {a <= b}");    // False

        // 邏輯運算符
        bool x = true, y = false;
        Console.WriteLine($"與: {x && y}");          // False
        Console.WriteLine($"或: {x || y}");          // True
        Console.WriteLine($"非: {!x}");              // False

        // 賦值運算符
        int c = 5;
        c += 3;  // c = c + 3
        Console.WriteLine($"加法賦值: {c}");         // 8
        c -= 2;  // c = c - 2
        Console.WriteLine($"減法賦值: {c}");         // 6
    }
}
```

**輸出結果：**
```
加法: 13
減法: 7
乘法: 30
除法: 3.3333333333333335
整數除法: 3
取餘: 1
次方: 1000
等於: False
不等於: True
大於: True
小於: False
大於等於: True
小於等於: False
與: False
或: True
非: False
加法賦值: 8
減法賦值: 6
```

#### 運算符對照表

| 操作 | Python | C# |
|------|--------|---|
| 加法 | `+` | `+` |
| 減法 | `-` | `-` |
| 乘法 | `*` | `*` |
| 除法 | `/` | `/` |
| 整數除法 | `//` | `/`（當操作數為整數時） |
| 取餘 | `%` | `%` |
| 次方 | `**` | `Math.Pow()` |
| 等於 | `==` | `==` |
| 不等於 | `!=` | `!=` |
| 大於 | `>` | `>` |
| 小於 | `<` | `<` |
| 大於等於 | `>=` | `>=` |
| 小於等於 | `<=` | `<=` |
| 邏輯與 | `and` | `&&` |
| 邏輯或 | `or` | `\|\|` |
| 邏輯非 | `not` | `!` |
| 位元與 | `&` | `&` |
| 位元或 | `\|` | `\|` |
| 位元異或 | `^` | `^` |
| 位元非 | `~` | `~` |

### 註釋

#### Python註釋

```python
# 這是單行註釋

"""
這是多行註釋
用三個引號包裹
可以跨越多行
"""

def sample_function():
    """這是函數的文檔字符串（docstring）
    用於說明函數的功能、參數和返回值
    """
    pass
```

#### C#註釋

```csharp
// 這是單行註釋

/*
 * 這是多行註釋
 * 用 /* 和 */ 包裹
 * 可以跨越多行
 */

/// <summary>
/// 這是XML文檔註釋
/// 用於生成API文檔
/// </summary>
/// <param name="x">參數x的說明</param>
/// <returns>返回值的說明</returns>
public int SampleFunction(int x)
{
    return x * 2;
}
```

### 輸入與輸出

#### Python輸入輸出

```python
# 輸出
print("Hello, World!")
name = "小明"
age = 25
print("姓名：" + name + "，年齡：" + str(age))  # 連接字符串
print("姓名：%s，年齡：%d" % (name, age))      # %格式化
print("姓名：{}，年齡：{}".format(name, age))  # format方法
print(f"姓名：{name}，年齡：{age}")           # f-string（推薦）

# 輸入
user_input = input("請輸入您的名字: ")
print(f"您好，{user_input}!")

# 類型轉換
age_input = input("請輸入您的年齡: ")
age = int(age_input)  # 將字符串轉換為整數
print(f"明年您將會 {age + 1} 歲")
```

**輸出結果（假設用戶輸入"張三"和"30"）：**
```
Hello, World!
姓名：小明，年齡：25
姓名：小明，年齡：25
姓名：小明，年齡：25
姓名：小明，年齡：25
請輸入您的名字: 張三
您好，張三!
請輸入您的年齡: 30
明年您將會 31 歲
```

#### C#輸入輸出

```csharp
using System;

class Program
{
    static void Main()
    {
        // 輸出
        Console.WriteLine("Hello, World!");
        string name = "小明";
        int age = 25;
        Console.WriteLine("姓名：" + name + "，年齡：" + age);  // 連接字符串
        Console.WriteLine("姓名：{0}，年齡：{1}", name, age);   // 索引格式化
        Console.WriteLine($"姓名：{name}，年齡：{age}");       // 字符串插值（推薦）

        // 輸入
        Console.Write("請輸入您的名字: ");
        string userInput = Console.ReadLine();
        Console.WriteLine($"您好，{userInput}!");

        // 類型轉換
        Console.Write("請輸入您的年齡: ");
        string ageInput = Console.ReadLine();
        int ageValue = int.Parse(ageInput);  // 將字符串轉換為整數
        // 更安全的轉換方式：
        // int ageValue;
        // if (int.TryParse(ageInput, out ageValue))
        // {
        //     Console.WriteLine($"明年您將會 {ageValue + 1} 歲");
        // }
        // else
        // {
        //     Console.WriteLine("輸入無效，請輸入數字");
        // }
        Console.WriteLine($"明年您將會 {ageValue + 1} 歲");
    }
}
```

**輸出結果（假設用戶輸入"張三"和"30"）：**
```
Hello, World!
姓名：小明，年齡：25
姓名：小明，年齡：25
姓名：小明，年齡：25
請輸入您的名字: 張三
您好，張三!
請輸入您的年齡: 30
明年您將會 31 歲
```

## 流程控制

### 條件語句

#### Python條件語句

```python
# if-elif-else
x = 10

if x > 10:
    print("x大於10")
elif x == 10:
    print("x等於10")
else:
    print("x小於10")

# 三元運算符
status = "成年" if x >= 18 else "未成年"
print(status)

# 邏輯運算短路
result = x > 5 and "x大於5" or "x小於等於5"
print(result)
```

**輸出結果：**
```
x等於10
未成年
x大於5
```

#### C#條件語句

```csharp
using System;

class Program
{
    static void Main()
    {
        // if-else if-else
        int x = 10;

        if (x > 10)
        {
            Console.WriteLine("x大於10");
        }
        else if (x == 10)
        {
            Console.WriteLine("x等於10");
        }
        else
        {
            Console.WriteLine("x小於10");
        }

        // 三元運算符
        string status = x >= 18 ? "成年" : "未成年";
        Console.WriteLine(status);

        // 邏輯運算短路
        string result = x > 5 ? "x大於5" : "x小於等於5";
        Console.WriteLine(result);

        // switch語句
        switch (x)
        {
            case 5:
                Console.WriteLine("x是5");
                break;
            case 10:
                Console.WriteLine("x是10");
                break;
            default:
                Console.WriteLine("x是其他值");
                break;
        }

        // C# 7.0+支援模式匹配的switch
        object obj = 10;
        switch (obj)
        {
            case int i when i > 5:
                Console.WriteLine($"obj是大於5的整數: {i}");
                break;
            case string s:
                Console.WriteLine($"obj是字符串: {s}");
                break;
            case null:
                Console.WriteLine("obj是null");
                break;
            default:
                Console.WriteLine("obj是其他類型");
                break;
        }
    }
}
```

**輸出結果：**
```
x等於10
未成年
x大於5
x是10
obj是大於5的整數: 10
```

### 循環語句

#### Python循環語句

```python
# for循環
print("for循環遍歷列表：")
fruits = ["蘋果", "香蕉", "橙子"]
for fruit in fruits:
    print(fruit)

# 使用range
print("\n使用range生成數列：")
for i in range(1, 5):  # 1, 2, 3, 4
    print(i)

# while循環
print("\nwhile循環：")
count = 0
while count < 3:
    print(f"count = {count}")
    count += 1

# break和continue
print("\nbreak和continue：")
for i in range(5):
    if i == 1:
        continue  # 跳過1
    if i == 4:
        break  # 在4時結束循環
    print(i)

# 列表推導式
print("\n列表推導式：")
squares = [x**2 for x in range(1, 6)]
print(squares)

# 帶條件的列表推導式
even_squares = [x**2 for x in range(1, 11) if x % 2 == 0]
print(even_squares)
```

**輸出結果：**
```
for循環遍歷列表：
蘋果
香蕉
橙子

使用range生成數列：
1
2
3
4

while循環：
count = 0
count = 1
count = 2

break和continue：
0
2
3

列表推導式：
[1, 4, 9, 16, 25]
[4, 16, 36, 64, 100]
```

#### C#循環語句

```csharp
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        // foreach循環
        Console.WriteLine("foreach循環遍歷列表：");
        List<string> fruits = new List<string> { "蘋果", "香蕉", "橙子" };
        foreach (string fruit in fruits)
        {
            Console.WriteLine(fruit);
        }

        // for循環
        Console.WriteLine("\n使用for循環：");
        for (int i = 1; i < 5; i++)  // 1, 2, 3, 4
        {
            Console.WriteLine(i);
        }

        // while循環
        Console.WriteLine("\nwhile循環：");
        int count = 0;
        while (count < 3)
        {
            Console.WriteLine($"count = {count}");
            count++;
        }

        // do-while循環（Python沒有對應的循環）
        Console.WriteLine("\ndo-while循環：");
        int j = 0;
        do
        {
            Console.WriteLine($"j = {j}");
            j++;
        } while (j < 3);

        // break和continue
        Console.WriteLine("\nbreak和continue：");
        for (int i = 0; i < 5; i++)
        {
            if (i == 1)
                continue;  // 跳過1
            if (i == 4)
                break;  // 在4時結束循環
            Console.WriteLine(i);
        }

        // LINQ查詢（類似列表推導式）
        Console.WriteLine("\nLINQ查詢：");
        List<int> squares = Enumerable.Range(1, 5).Select(x => x * x).ToList();
        foreach (int square in squares)
        {
            Console.Write($"{square} ");
        }
        Console.WriteLine();

        // 帶條件的LINQ查詢
        List<int> evenSquares = Enumerable.Range(1, 10)
                                         .Where(x => x % 2 == 0)
                                         .Select(x => x * x)
                                         .ToList();
        foreach (int square in evenSquares)
        {
            Console.Write($"{square} ");
        }
        Console.WriteLine();
    }
}
```

**輸出結果：**
```
foreach循環遍歷列表：
蘋果
香蕉
橙子

使用for循環：
1
2
3
4

while循環：
count = 0
count = 1
count = 2

do-while循環：
j = 0
j = 1
j = 2

break和continue：
0
2
3

LINQ查詢：
1 4 9 16 25 
4 16 36 64 100 
```

## 集合類型

### 數組/列表

#### Python列表

```python
# 創建列表
fruits = ["蘋果", "香蕉", "橙子"]
print(f"fruits列表: {fruits}")

# 訪問元素
print(f"第一個水果: {fruits[0]}")
print(f"最後一個水果: {fruits[-1]}")

# 修改元素
fruits[1] = "梨"
print(f"修改後的列表: {fruits}")

# 添加元素
fruits.append("葡萄")
print(f"添加後的列表: {fruits}")

# 插入元素
fruits.insert(1, "芒果")
print(f"插入後的列表: {fruits}")

# 移除元素
removed_fruit = fruits.pop()  # 移除最後一個元素
print(f"移除的水果: {removed_fruit}")
print(f"移除後的列表: {fruits}")

# 指定位置移除
del fruits[1]  # 移除第二個元素
print(f"刪除後的列表: {fruits}")

# 切片
print(f"切片 fruits[1:3]: {fruits[1:3]}")

# 列表長度
print(f"列表長度: {len(fruits)}")

# 檢查存在
print(f"'蘋果'是否在列表中: {'蘋果' in fruits}")

# 排序
numbers = [3, 1, 4, 1, 5, 9]
numbers.sort()
print(f"排序後的數字: {numbers}")

# 反轉
numbers.reverse()
print(f"反轉後的數字: {numbers}")

# 複製列表
numbers_copy = numbers.copy()
print(f"複製的列表: {numbers_copy}")
```

**輸出結果：**
```
fruits列表: ['蘋果', '香蕉', '橙子']
第一個水果: 蘋果
最後一個水果: 橙子
修改後的列表: ['蘋果', '梨', '橙子']
添加後的列表: ['蘋果', '梨', '橙子', '葡萄']
插入後的列表: ['蘋果', '芒果', '梨', '橙子', '葡萄']
移除的水果: 葡萄
移除後的列表: ['蘋果', '芒果', '梨', '橙子']
刪除後的列表: ['蘋果', '梨', '橙子']
切片 fruits[1:3]: ['梨', '橙子']
列表長度: 3
'蘋果'是否在列表中: True
排序後的數字: [1, 1, 3, 4, 5, 9]
反轉後的數字: [9, 5, 4, 3, 1, 1]
複製的列表: [9, 5, 4, 3, 1, 1]
```

#### C#列表與數組

```csharp
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        // 數組（固定大小）
        string[] fruitArray = new string[] { "蘋果", "香蕉", "橙子" };
        Console.WriteLine($"水果數組: [{string.Join(", ", fruitArray)}]");

        // 列表（可變大小）
        List<string> fruits = new List<string> { "蘋果", "香蕉", "橙子" };
        Console.WriteLine($"fruits列表: [{string.Join(", ", fruits)}]");

        // 訪問元素
        Console.WriteLine($"第一個水果: {fruits[0]}");
        Console.WriteLine($"最後一個水果: {fruits[fruits.Count - 1]}");

        // 修改元素
        fruits[1] = "梨";
        Console.WriteLine($"修改後的列表: [{string.Join(", ", fruits)}]");

        // 添加元素
        fruits.Add("葡萄");
        Console.WriteLine($"添加後的列表: [{string.Join(", ", fruits)}]");

        // 插入元素
        fruits.Insert(1, "芒果");
        Console.WriteLine($"插入後的列表: [{string.Join(", ", fruits)}]");

        // 移除元素
        string removedFruit = fruits[fruits.Count - 1];
        fruits.RemoveAt(fruits.Count - 1);  // 移除最後一個元素
        Console.WriteLine($"移除的水果: {removedFruit}");
        Console.WriteLine($"移除後的列表: [{string.Join(", ", fruits)}]");

        // 指定位置移除
        fruits.RemoveAt(1);  // 移除第二個元素
        Console.WriteLine($"刪除後的列表: [{string.Join(", ", fruits)}]");