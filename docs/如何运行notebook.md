# 在 VS Code 里打开和运行演示 notebook

## 第一次准备（只做一次）

1. **装扩展**：打开 VS Code，左边栏点「扩展」图标（四个小方块），搜索并安装 **Python** 和 **Jupyter**（都是 Microsoft 出的）。
2. **打开项目文件夹**：菜单 `File → Open Folder…`，选 `Desktop/Data science project`，点「打开」。
3. **确认依赖已装好**：菜单 `Terminal → New Terminal`，在下面的终端里输入（一行一行来）：

   ```bash
   source .venv/bin/activate
   ```

   ```bash
   pip install -r requirements.txt
   ```

   行首出现 `(.venv)` 就说明虚拟环境开着。已经装过的包会显示 "Requirement already satisfied"，没关系。

## 每次演示

1. 左边文件列表里点开 `notebooks` → `furniture_nowcast_demo.ipynb`。
2. **选内核**：点右上角的「Select Kernel」（或者显示着一个 Python 版本的按钮）→「Python Environments…」→ 选带 **.venv** 的那个（路径里有 `Data science project/.venv`）。
   - 如果列表里没有 .venv：按 `Cmd + Shift + P`，输入 `Python: Select Interpreter`，选 `.venv`，再回来选内核。
3. 点上方工具栏的 **Run All**（▶▶），等大约 1 分钟，所有表和图都会出来。
4. 也可以一格一格跑：点某一格，按 `Shift + Enter` 运行并跳到下一格。演示时这样更好讲。

## 常见问题

- **图里的中文是方框**：重启内核（工具栏 Restart）再 Run All。
- **ModuleNotFoundError**：内核没选对，回到第 2 步，确认选的是 .venv。
- **找不到文件 (FileNotFoundError)**：确认打开的是整个 `Data science project` 文件夹，而不是只打开了 notebook 文件。

## 应该看到的关键数字

| 模型 | 测试 RMSE（同比） | 相对 AR |
|---|---|---|
| AR 基准 | 4.48 | 0 |
| Ridge 全特征 | 3.91 | −13% |
| Ridge 搜索+零售调查 | 3.77 | −16% |
