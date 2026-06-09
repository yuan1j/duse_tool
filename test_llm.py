import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_helper import ai_helper

print("=" * 72)
print("  通用数据填报系统 v2.0 - AI大模型集成测试")
print("=" * 72)

print("\n【系统状态检测】")
print("-" * 72)
print(f"当前 AI 模式: {'✅ Dashscope 大模型已启用' if ai_helper.is_using_llm() else '⚠️  大模型未启用，正在使用本地规则生成'}")

api_key = os.environ.get("DASHSCOPE_API_KEY", "")
if api_key:
    print(f"DASHSCOPE_API_KEY: ✅ 已配置 ({len(api_key)} 字符)")
else:
    print("DASHSCOPE_API_KEY: ❌ 未配置（将使用本地规则）")
    print("  提示: Windows PowerShell 执行 $env:DASHSCOPE_API_KEY='sk-xxxxxx'")
    print("        Windows CMD 执行 set DASHSCOPE_API_KEY=sk-xxxxxx")
    print("        Linux/Mac 执行 export DASHSCOPE_API_KEY=sk-xxxxxx")

print(f"默认模型: {os.environ.get('DASHSCOPE_MODEL', 'qwen-plus')}")
print(f"高速模型: {os.environ.get('DASHSCOPE_FAST_MODEL', 'qwen-turbo')}")

print("\n【测试1: 单个字段智能推荐】")
print("-" * 72)

test_fields = [
    {"field_name": "name", "field_label": "申请人姓名", "field_type": "text"},
    {"field_name": "email", "field_label": "联系邮箱", "field_type": "email"},
    {"field_name": "phone", "field_label": "手机号码", "field_type": "tel"},
    {"field_name": "dept", "field_label": "所属部门", "field_type": "select",
     "field_options": ["研发部", "市场部", "销售部", "财务部", "人力资源部"]},
    {"field_name": "amount", "field_label": "申请金额", "field_type": "number"},
    {"field_name": "date", "field_label": "申请日期", "field_type": "date"},
    {"field_name": "status", "field_label": "状态", "field_type": "text"},
    {"field_name": "project", "field_label": "项目名称", "field_type": "text"},
    {"field_name": "desc", "field_label": "项目说明", "field_type": "textarea"},
]

for i, field in enumerate(test_fields, 1):
    result = ai_helper.recommend_field_value(field)
    label = field["field_label"]
    ftype = field["field_type"]
    print(f"  {i:02d}. {label:12s} ({ftype:8s}) → {result}")

print("\n【测试2: 字段内容优化】")
print("-" * 72)

optimize_cases = [
    ({"field_name": "desc", "field_label": "项目说明", "field_type": "textarea"},
     "项目进展顺利"),
    ({"field_name": "reason", "field_label": "申请原因", "field_type": "textarea"},
     "需要改进流程"),
    ({"field_name": "opinion", "field_label": "领导意见", "field_type": "textarea"},
     "同意"),
    ({"field_name": "name", "field_label": "姓名", "field_type": "text"},
     ""),
]

for i, (field, value) in enumerate(optimize_cases, 1):
    optimized = ai_helper.optimize_field(field, value)
    label = field["field_label"]
    print(f"  {i:02d}. {label}:")
    print(f"      原始: '{value}'")
    print(f"      优化: '{optimized}'")

print("\n【测试3: 批量一键填报】")
print("-" * 72)

filled = ai_helper.auto_fill_all(test_fields)
for i, field in enumerate(test_fields, 1):
    key = field["field_name"]
    value = filled.get(key, "")
    label = field["field_label"]
    print(f"  {i:02d}. {label:12s} → {value}")

print("\n【测试4: 字段类别识别能力】")
print("-" * 72)

for field in test_fields:
    cat = ai_helper._detect_field_category(field)
    print(f"  {field['field_label']:12s} → 识别为: {cat}")

print("\n" + "=" * 72)
print("✅ 测试完成")
print("=" * 72)
print("\n💡 使用建议:")
print("  1. 启用大模型: 配置 DASHSCOPE_API_KEY 环境变量")
print("  2. 切换模型:")
print("     - 追求速度: $env:DASHSCOPE_MODEL='qwen-turbo'")
print("     - 追求质量: $env:DASHSCOPE_MODEL='qwen-plus'")
print("     - 追求最强: $env:DASHSCOPE_MODEL='qwen-max'")
print("  3. 启动应用: python app.py")
print("=" * 72)
