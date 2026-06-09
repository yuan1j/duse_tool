import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_helper import ai_helper

print("=" * 70)
print("  字段级别 AI 一键优化功能 - 测试验证")
print("=" * 70)

test_cases = [
    {
        "名称": "姓名字段",
        "field": {"field_name": "姓名", "field_label": "申请人姓名", "field_type": "text"},
        "测试值": "张",
        "描述": "短姓名优化为完整姓名"
    },
    {
        "名称": "邮箱字段",
        "field": {"field_name": "email", "field_label": "邮箱", "field_type": "email"},
        "测试值": "test",
        "描述": "不完整邮箱补全"
    },
    {
        "名称": "电话字段",
        "field": {"field_name": "tel", "field_label": "联系电话", "field_type": "tel"},
        "测试值": "138",
        "描述": "不完整电话号码补全"
    },
    {
        "名称": "数字字段",
        "field": {"field_name": "amount", "field_label": "金额", "field_type": "number"},
        "测试值": "abc",
        "描述": "无效数字生成合理值"
    },
    {
        "名称": "日期字段",
        "field": {"field_name": "date", "field_label": "申请日期", "field_type": "date"},
        "测试值": "20241301",
        "描述": "无效日期格式修正"
    },
    {
        "名称": "下拉选择字段",
        "field": {"field_name": "dept", "field_label": "所属部门", "field_type": "select",
                 "field_options": ["研发部", "市场部", "销售部", "财务部"]},
        "测试值": "研发",
        "描述": "从选项中匹配最接近的值"
    },
    {
        "名称": "多行文本字段(短)",
        "field": {"field_name": "desc", "field_label": "项目说明", "field_type": "textarea"},
        "测试值": "项目进展顺利",
        "描述": "简短描述扩充为完整段落"
    },
    {
        "名称": "多行文本字段(空)",
        "field": {"field_name": "remark", "field_label": "备注说明", "field_type": "textarea"},
        "测试值": "",
        "描述": "空值生成推荐内容"
    },
    {
        "名称": "部门字段(文本)",
        "field": {"field_name": "department", "field_label": "部门", "field_type": "text"},
        "测试值": "",
        "描述": "文本字段根据标签智能推荐"
    },
    {
        "名称": "状态字段",
        "field": {"field_name": "status", "field_label": "状态", "field_type": "text"},
        "测试值": "进行",
        "描述": "状态字段智能识别"
    },
]

print("\n📋 测试1: 单个字段优化")
print("-" * 70)
for i, tc in enumerate(test_cases, 1):
    result = ai_helper.optimize_field(tc["field"], tc["测试值"])
    print(f"\n{i}. {tc['名称']}")
    print(f"   字段类型: {tc['field']['field_type']}")
    print(f"   原始值: '{tc['测试值']}'")
    print(f"   优化后: '{result}'")
    print(f"   描述: {tc['描述']}")

print("\n" + "=" * 70)
print("📋 测试2: 字段推荐值生成")
print("-" * 70)
for i, tc in enumerate(test_cases, 1):
    result = ai_helper.recommend_field_value(tc["field"])
    print(f"\n{i}. {tc['名称']} → 推荐值: '{result}'")

print("\n" + "=" * 70)
print("📋 测试3: 字段类别识别")
print("-" * 70)
for i, tc in enumerate(test_cases, 1):
    category = ai_helper._detect_field_category(tc["field"])
    print(f"{i}. {tc['名称']} → 识别类别: {category}")

print("\n" + "=" * 70)
print("✅ 所有字段级别 AI 优化功能测试完成!")
print("=" * 70)

print("\n💡 功能说明:")
print("  • 每个字段现在都有独立的「🔮 AI一键优化」按钮")
print("  • 点击按钮后，AI 根据字段类型和标签智能优化当前字段内容")
print("  • 如果字段为空，会生成推荐值")
print("  • 如果字段有内容，会根据规则优化/补全内容")
print("  • 支持文本、数字、日期、邮箱、电话、下拉选择、多行文本等所有类型")
print("  • 同时保留了全局「✨ AI一键填报」和「✨ 全部AI一键填报」功能")
print("=" * 70)
