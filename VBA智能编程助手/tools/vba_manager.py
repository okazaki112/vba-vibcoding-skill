"""
Excel VBA 管理工具 - VBA-vibcoding核心组件
提供 VBA 模块的增删改查、运行等功能

使用方法:
    python vba_manager.py <命令> [参数]

命令:
    list <文件路径>              - 列出所有 VBA 模块
    create <文件路径> [工作表名] [行数] [列数] - 新建 .xlsm 并写入测试数据（默认 20 行 6 列）
    read <文件路径> <模块名>      - 读取模块代码
    write <文件路径> <模块名> <代码文件>  - 写入/覆盖模块
    delete <文件路径> <模块名>    - 删除模块
    run <文件路径> <宏名> [参数...] - 运行宏
    export <文件路径> <模块名> <输出文件> - 导出模块
    import <文件路径> <模块文件> [新名称] - 导入模块

示例:
    python vba_manager.py list "D:\\test.xlsm"
    python vba_manager.py create "D:\\new.xlsm" "测试数据" 20 6
    python vba_manager.py read "D:\\test.xlsm" "Module1"
    python vba_manager.py write "D:\\test.xlsm" "MyModule" "code.bas"
    python vba_manager.py run "D:\\test.xlsm" "MyModule.Hello"
    python vba_manager.py export "D:\\test.xlsm" "Module1" "backup.bas"

前置要求:
    - pip install pywin32
    - Excel需启用"信任对VBA工程对象模型的访问"
    - 文件必须是.xlsm格式
"""

import win32com.client as win32
import os
import sys
import json
import random


def get_excel_app():
    """获取 Excel 实例（优先使用已打开的）"""
    try:
        excel = win32.GetActiveObject("Excel.Application")
        return excel
    except:
        excel = win32.DispatchEx("Excel.Application")
        excel.Visible = True
        return excel


def get_workbook(excel, file_path):
    """获取工作簿（优先找已打开的）"""
    file_path = os.path.abspath(file_path)
    
    for wb in excel.Workbooks:
        try:
            if wb.FullName.upper() == file_path.upper() or \
               wb.Name == os.path.basename(file_path):
                return wb
        except:
            continue
    
    # 没找到，打开文件
    if os.path.exists(file_path):
        return excel.Workbooks.Open(file_path)
    else:
        raise FileNotFoundError(f"文件不存在: {file_path}")


def create_workbook(file_path, sheet_name="测试数据", rows=20, cols=6):
    """新建 .xlsm 工作簿并写入测试数据（表头 + 随机业务数据行）"""
    excel = get_excel_app()

    try:
        file_path = os.path.abspath(file_path)
        if not file_path.lower().endswith(".xlsm"):
            return {"success": False, "error": "目标文件必须以 .xlsm 结尾（.xlsx 无法保存 VBA）"}
        if os.path.exists(file_path):
            return {"success": False, "error": "文件已存在，拒绝覆盖: " + file_path}
        if not str(sheet_name).strip():
            sheet_name = "测试数据"
        rows = max(1, min(int(rows), 1000))
        cols = max(1, min(int(cols), 30))

        headers = ["编号", "名称", "类别", "数量", "单价", "金额"]
        while len(headers) < cols:
            headers.append("字段" + str(len(headers) + 1))
        headers = headers[:cols]

        rng = random.Random()
        cats = ["华东", "华南", "华北", "西南"]
        qty_i = headers.index("数量") if "数量" in headers else None
        price_i = headers.index("单价") if "单价" in headers else None
        amount_i = headers.index("金额") if "金额" in headers else None

        data = [headers]
        for i in range(1, rows + 1):
            row = [None] * cols
            for c, h in enumerate(headers):
                if h == "编号":
                    row[c] = i
                elif h == "名称":
                    row[c] = "产品" + str(rng.randint(100, 999))
                elif h == "类别":
                    row[c] = rng.choice(cats)
                elif h == "数量":
                    row[c] = rng.randint(1, 500)
                elif h == "单价":
                    row[c] = round(rng.uniform(1, 200), 2)
                else:
                    row[c] = rng.choice(["A类", "B类", "C类"]) if c % 2 else rng.randint(1, 99)
            if amount_i is not None and qty_i is not None and price_i is not None:
                row[amount_i] = round(row[qty_i] * row[price_i], 2)
            data.append(row)

        wb = excel.Workbooks.Add()
        prev_alerts = excel.DisplayAlerts
        excel.DisplayAlerts = False
        try:
            ws = wb.Worksheets(1)
            ws.Name = sheet_name
            ws.Range(ws.Cells(1, 1), ws.Cells(rows + 1, cols)).Value = data
            for idx in range(wb.Worksheets.Count, 1, -1):
                wb.Worksheets(idx).Delete()
            wb.SaveAs(file_path, 52)  # 52 = xlOpenXMLWorkbookMacroEnabled (.xlsm)
        finally:
            excel.DisplayAlerts = prev_alerts

        return {"success": True, "file": file_path, "sheet": sheet_name,
                "rows": rows, "cols": cols, "note": "已写入表头与测试数据"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def list_modules(file_path):
    """列出所有 VBA 模块"""
    excel = get_excel_app()
    
    try:
        wb = get_workbook(excel, file_path)
        vb_project = wb.VBProject
        
        modules = []
        for comp in vb_project.VBComponents:
            type_map = {1: "模块", 2: "类模块", 3: "窗体", 100: "文档"}
            modules.append({
                "name": comp.Name,
                "type": type_map.get(comp.Type, "其他"),
                "type_id": comp.Type,
                "lines": comp.CodeModule.CountOfLines if comp.Type in [1, 2, 100] else 0
            })
        
        return {"success": True, "file": wb.Name, "modules": modules}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_module(file_path, module_name):
    """读取模块代码"""
    excel = get_excel_app()
    
    try:
        wb = get_workbook(excel, file_path)
        vb_project = wb.VBProject
        
        comp = vb_project.VBComponents(module_name)
        code = comp.CodeModule.Lines(1, comp.CodeModule.CountOfLines)
        
        return {"success": True, "module": module_name, "code": code}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_module(file_path, module_name, code_file):
    """写入/覆盖模块"""
    excel = get_excel_app()
    
    try:
        wb = get_workbook(excel, file_path)
        vb_project = wb.VBProject
        
        # 读取代码文件
        with open(code_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 删除旧模块
        try:
            old_comp = vb_project.VBComponents(module_name)
            vb_project.VBComponents.Remove(old_comp)
        except:
            pass
        
        # 创建新模块
        new_comp = vb_project.VBComponents.Add(1)  # 1=标准模块
        new_comp.Name = module_name
        new_comp.CodeModule.AddFromString(code)
        
        # 保存
        wb.Save()
        
        return {"success": True, "module": module_name, "lines": len(code.splitlines())}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_module(file_path, module_name):
    """删除模块"""
    excel = get_excel_app()
    
    try:
        wb = get_workbook(excel, file_path)
        vb_project = wb.VBProject
        
        comp = vb_project.VBComponents(module_name)
        vb_project.VBComponents.Remove(comp)
        wb.Save()
        
        return {"success": True, "deleted": module_name}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_macro(file_path, macro_name, *args):
    """运行宏"""
    excel = get_excel_app()
    
    try:
        wb = get_workbook(excel, file_path)
        
        # 执行宏
        if args:
            result = excel.Application.Run(macro_name, *args)
        else:
            result = excel.Application.Run(macro_name)
        
        return {"success": True, "macro": macro_name, "result": str(result) if result else None}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def export_module(file_path, module_name, output_file):
    """导出模块"""
    excel = get_excel_app()
    
    try:
        wb = get_workbook(excel, file_path)
        vb_project = wb.VBProject
        
        comp = vb_project.VBComponents(module_name)
        comp.Export(output_file)
        
        return {"success": True, "module": module_name, "output": output_file}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def import_module(file_path, module_file, new_name=None):
    """导入模块"""
    excel = get_excel_app()
    
    try:
        wb = get_workbook(excel, file_path)
        vb_project = wb.VBProject
        
        comp = vb_project.VBComponents.Import(module_file)
        if new_name:
            comp.Name = new_name
        
        wb.Save()
        
        return {"success": True, "imported": comp.Name}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "list" and len(sys.argv) >= 3:
            result = list_modules(sys.argv[2])

        elif command == "create" and len(sys.argv) >= 3:
            sheet_name = sys.argv[3] if len(sys.argv) > 3 else "测试数据"
            rows = sys.argv[4] if len(sys.argv) > 4 else 20
            cols = sys.argv[5] if len(sys.argv) > 5 else 6
            result = create_workbook(sys.argv[2], sheet_name, rows, cols)

        elif command == "read" and len(sys.argv) >= 4:
            result = read_module(sys.argv[2], sys.argv[3])
        
        elif command == "write" and len(sys.argv) >= 5:
            result = write_module(sys.argv[2], sys.argv[3], sys.argv[4])
        
        elif command == "delete" and len(sys.argv) >= 4:
            result = delete_module(sys.argv[2], sys.argv[3])
        
        elif command == "run" and len(sys.argv) >= 4:
            result = run_macro(sys.argv[2], sys.argv[3], *sys.argv[4:])
        
        elif command == "export" and len(sys.argv) >= 5:
            result = export_module(sys.argv[2], sys.argv[3], sys.argv[4])
        
        elif command == "import" and len(sys.argv) >= 4:
            new_name = sys.argv[4] if len(sys.argv) > 4 else None
            result = import_module(sys.argv[2], sys.argv[3], new_name)
        
        else:
            print(f"❌ 未知命令或参数不足: {command}")
            print(__doc__)
            sys.exit(1)
        
        # 输出 JSON 结果
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()