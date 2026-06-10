# -*- coding: utf-8 -*-
"""端到端测试：验证 AIHelper 多轮对话解析逻辑正确性。"""

import json, re, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_helper import AIHelper


class FakeClient:
    """模拟 AI 返回预设回复。"""
    def __init__(self, responses):
        self._responses = list(responses)
        self._idx = 0

    def chat(self, messages, use_fast=True, max_tokens=1500):
        if self._idx < len(self._responses):
            r = self._responses[self._idx]
            self._idx += 1
            return r
        return "好的。\n\n{}"


# 模拟的表单字段
FIELDS = [
    {"field_name": "employee_name",   "field_label": "Employee Name",        "field_type": "text",   "is_required": True,  "field_options": None},
    {"field_name": "employee_id",     "field_label": "Employee ID",          "field_type": "text",   "is_required": True,  "field_options": None},
    {"field_name": "age",             "field_label": "Age",                  "field_type": "number", "is_required": False, "field_options": None},
    {"field_name": "email",           "field_label": "Email Address",        "field_type": "text",   "is_required": True,  "field_options": None},
    {"field_name": "phone",           "field_label": "Phone Number",         "field_type": "text",   "is_required": False, "field_options": None},
    {"field_name": "dob",             "field_label": "Date of Birth",        "field_type": "date",   "is_required": False, "field_options": None},
    {"field_name": "hire_date",       "field_label": "Hire Date",            "field_type": "date",   "is_required": False, "field_options": None},
    {"field_name": "department",      "field_label": "Department",           "field_type": "select", "is_required": True,
     "field_options": ["Engineering", "Sales", "Marketing", "HR"]},
    {"field_name": "job_title",       "field_label": "Job Title",            "field_type": "text",   "is_required": True,  "field_options": None},
    {"field_name": "employment_type", "field_label": "Employment Type",      "field_type": "select", "is_required": True,
     "field_options": ["Full-time", "Part-time", "Contract"]},
    {"field_name": "salary",          "field_label": "Salary (USD)",         "field_type": "number", "is_required": False, "field_options": None},
    {"field_name": "office_location", "field_label": "Office Location",      "field_type": "text",   "is_required": False, "field_options": None},
    {"field_name": "skills",          "field_label": "Skills",               "field_type": "text",   "is_required": False, "field_options": None},
    {"field_name": "emergency_contact", "field_label": "Emergency Contact",  "field_type": "text",   "is_required": False, "field_options": None},
    {"field_name": "emergency_phone", "field_label": "Emergency Contact Phone", "field_type": "text", "is_required": False, "field_options": None},
    {"field_name": "bio",             "field_label": "Biography / Notes",    "field_type": "text",   "is_required": False, "field_options": None},
]


def run_test(name, ai_reply, expected_values):
    """
    运行单次测试：AI 返回给定的 ai_reply，验证解析到的 values 字典中是否包含 expected_values。
    """
    print(f"\n{'='*70}")
    print(f"测试: {name}")
    print(f"{'='*70}")

    helper = AIHelper()
    helper._client = FakeClient([ai_reply])

    # 启动对话（第一步 AI 会返回初始问好）
    ai_msg_1, vals_1, done_1, msgs_1 = helper.start_conversation_fill(
        FIELDS, form_name="员工信息表", existing_values={}
    )
    print(f"  启动后: {len(vals_1)} 个字段（预期全部为空）")

    # 第二步：用户发送消息，AI 返回带字段的回复
    helper._client = FakeClient([ai_reply])
    ai_msg_2, vals_2, done_2, msgs_2 = helper.continue_conversation_fill(
        msgs_1, FIELDS, "用户提供的信息", existing_values=vals_1
    )

    # 统计
    filled = {k: v for k, v in vals_2.items() if v and str(v).strip()}
    print(f"  解析到 {len(filled)} 个非空字段")

    ok_count = 0
    fail_count = 0
    for field_name, expected in expected_values.items():
        actual = vals_2.get(field_name, "")
        if str(actual) == str(expected):
            ok_count += 1
            print(f"    ✓ {field_name}: '{actual}'")
        else:
            fail_count += 1
            print(f"    ❌ {field_name}: 期望='{expected}', 实际='{actual}'")

    status = "✅ PASS" if fail_count == 0 else "❌ FAIL"
    print(f"  结果: {status} ({ok_count}/{len(expected_values)} 匹配)")
    return fail_count == 0


if __name__ == "__main__":
    all_pass = True

    # 测试1: 完整 JSON（英文 label 作为 key）—— 用户报告的核心场景
    ai_reply_1 = (
        "好的，感谢配合！我们开始吧。\n\n"
        "{\"Employee Name\": \"李四\", \"Employee ID\": \"EMP-00456\", \"Age\": 28, "
        "\"Email Address\": \"lisi@example.com\", \"Phone Number\": \"13812345678\", "
        "\"Date of Birth\": \"1994-05-15\", \"Hire Date\": \"2018-03-22\", "
        "\"Department\": \"Engineering\", \"Job Title\": \"软件工程师\", "
        "\"Employment Type\": \"Full-time\", \"Salary (USD)\": 85000, "
        "\"Office Location\": \"Headquarters\", \"Skills\": \"Python, Java, SQL, AWS\", "
        "\"Emergency Contact\": \"王五\", \"Emergency Contact Phone\": \"13987654321\", "
        "\"Biography / Notes\": \"拥有5年的软件开发经验，擅长后端开发和系统架构设计。\"}"
    )
    expected_1 = {
        "employee_name": "李四",
        "employee_id": "EMP-00456",
        "age": "28",
        "email": "lisi@example.com",
        "phone": "13812345678",
        "dob": "1994-05-15",
        "hire_date": "2018-03-22",
        "department": "Engineering",
        "job_title": "软件工程师",
        "employment_type": "Full-time",
        "salary": "85000",
        "office_location": "Headquarters",
        "skills": "Python, Java, SQL, AWS",
        "emergency_contact": "王五",
        "emergency_phone": "13987654321",
        "bio": "拥有5年的软件开发经验，擅长后端开发和系统架构设计。",
    }
    all_pass &= run_test("完整 JSON (英文 label)", ai_reply_1, expected_1)

    # 测试2: "标签：值" 格式（无 JSON 后备）
    ai_reply_2 = (
        "好的，我收到了您提供的信息。\n\n"
        "Employee Name：张三\n"
        "Employee ID：EMP-11111\n"
        "Age：30\n"
        "Email Address：zhangsan@example.com\n"
        "Department：Engineering\n"
        "Job Title：高级工程师\n"
    )
    expected_2 = {
        "employee_name": "张三",
        "employee_id": "EMP-11111",
        "age": "30",
        "email": "zhangsan@example.com",
        "department": "Engineering",
        "job_title": "高级工程师",
    }
    all_pass &= run_test("标签:值 后备格式", ai_reply_2, expected_2)

    # 测试3: JSON key 大小写与空白不一致
    ai_reply_3 = (
        "好的。\n\n"
        "{\"employee name\": \"王小二\", \"EMPLOYEE ID\": \"EMP-22222\", \"email  address\": \"wang@test.com\"}"
    )
    expected_3 = {
        "employee_name": "王小二",
        "employee_id": "EMP-22222",
        "email": "wang@test.com",
    }
    all_pass &= run_test("JSON key 大小写/空白 不一致", ai_reply_3, expected_3)

    # 测试4: 部分字段
    ai_reply_4 = (
        "好的，以下是您提供的部分信息：\n\n"
        "{\"Employee Name\": \"测试用户\", \"Department\": \"Sales\"}"
    )
    expected_4 = {
        "employee_name": "测试用户",
        "department": "Sales",
    }
    all_pass &= run_test("部分字段 JSON", ai_reply_4, expected_4)

    # 总结
    print(f"\n{'='*70}")
    print(f"总结果: {'✅ 全部通过' if all_pass else '❌ 有失败'}")
    print(f"{'='*70}\n")
    sys.exit(0 if all_pass else 1)
