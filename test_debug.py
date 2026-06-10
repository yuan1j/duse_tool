# -*- coding: utf-8 -*-
"""精准模拟用户场景测试：英文标签的表单 + AI 输出英文 key 的 JSON"""
import sys, re, json
sys.path.insert(0, ".")

from ai_helper import AIHelper

# ========== 模拟用户创建的表单（英文标签）==========
# 这就是用户在"新增字段"对话框中填写的内容
test_fields = [
    {"field_name": "employee_name",    "field_label": "Employee Name",         "field_type": "text",     "is_required": True},
    {"field_name": "employee_id",      "field_label": "Employee ID",           "field_type": "text",     "is_required": True},
    {"field_name": "age",              "field_label": "Age",                   "field_type": "number",   "is_required": False},
    {"field_name": "email_address",    "field_label": "Email Address",         "field_type": "email",    "is_required": True},
    {"field_name": "phone_number",     "field_label": "Phone Number",          "field_type": "tel",      "is_required": False},
    {"field_name": "date_of_birth",    "field_label": "Date of Birth",         "field_type": "date",     "is_required": False},
    {"field_name": "hire_date",        "field_label": "Hire Date",             "field_type": "date",     "is_required": False},
    {"field_name": "department",       "field_label": "Department",            "field_type": "text",     "is_required": False},
    {"field_name": "job_title",        "field_label": "Job Title",             "field_type": "text",     "is_required": False},
    {"field_name": "employment_type",  "field_label": "Employment Type",       "field_type": "text",     "is_required": False},
    {"field_name": "salary_usd",       "field_label": "Salary (USD)",          "field_type": "number",   "is_required": False},
    {"field_name": "office_location",  "field_label": "Office Location",       "field_type": "text",     "is_required": False},
    {"field_name": "skills",           "field_label": "Skills",                "field_type": "textarea", "is_required": False},
    {"field_name": "emergency_contact","field_label": "Emergency Contact",     "field_type": "text",     "is_required": False},
    {"field_name": "emergency_phone",  "field_label": "Emergency Contact Phone","field_type": "tel",     "is_required": False},
    {"field_name": "bio_notes",        "field_label": "Biography / Notes",     "field_type": "textarea", "is_required": False},
]

# ========== 模拟 AI 的真实回复（从用户截图中提取）==========
ai_reply = """好的，感谢提供信息！我们已经收集到所有必填字段的信息。如果还有其他需要补充或修改的内容，请告诉我。否则，我们将结束本次表单填写。

{"Employee Name": "李四", "Employee ID": "EMP-00456", "Age": 28, "Email Address": "lisi@example.com", "Phone Number": "13812345678", "Date of Birth": "1994-05-15", "Hire Date": "2018-03-22", "Department": "Engineering", "Job Title": "软件工程师", "Employment Type": "Full-time", "Salary (USD)": 85000, "Office Location": "Headquarters", "Skills": "Python, Java, SQL, AWS", "Emergency Contact": "王五", "Emergency Contact Phone": "13987654321", "Biography / Notes": "拥有5年的软件开发经验，擅长后端开发和系统架构设计。"}"""

# ========== 手动模拟 _run_conversation_step 的解析逻辑 ===========
# 注意：这里用 PATCH 过的 AIHelper，不调用真正的 Dashscope API
class _FakeClient:
    enabled = True
    def chat(self, *args, **kwargs):
        return ai_reply

helper = AIHelper()
helper._client = _FakeClient()

print(f"\n{'='*70}")
print(f"【测试场景】英文标签表单 + AI 输出英文 key 的 JSON")
print(f"{'='*70}")
print(f"\nForm fields ({len(test_fields)}):")
for f in test_fields:
    print(f"  field_name='{f['field_name']}'  field_label='{f['field_label']}'")

print(f"\nAI reply preview:\n  {ai_reply[:150]}...")

# --- 现在手动走一遍解析逻辑，打印每一步 ---
ai_text_clean = ai_reply.strip()
parsed_json = {}

# Step 1: JSON extraction
jmatch = re.search(r'\{[\s\S]*\}', ai_text_clean)
print(f"\n--- Step 1: JSON extraction ---")
if jmatch:
    json_candidate = jmatch.group(0)
    print(f"  JSON found (chars {jmatch.start()}-{jmatch.end()}), len={len(json_candidate)}")
    try:
        parsed_json = json.loads(json_candidate)
        if isinstance(parsed_json, dict):
            print(f"  JSON parsed OK: {len(parsed_json)} keys")
            print(f"  Keys: {list(parsed_json.keys())}")
        else:
            print(f"  ERROR: JSON parsed but not a dict: {type(parsed_json)}")
            parsed_json = {}
    except Exception as e:
        print(f"  ERROR: json.loads failed: {e}")
        parsed_json = {}
else:
    print("  ERROR: No JSON block found in AI reply!")

# Step 2: Key matching
print(f"\n--- Step 2: Key matching ---")
field_name_map = {}
field_label_map = {}
for f in test_fields:
    fn = f.get("field_name")
    fl = f.get("field_label")
    if fn:
        field_name_map[fn] = f
    if fl:
        field_label_map[fl] = f

print(f"  field_name_map keys: {list(field_name_map.keys())}")
print(f"  field_label_map keys: {list(field_label_map.keys())}")

updated_values = {}
for key, raw_val in parsed_json.items():
    target_field = field_name_map.get(key) or field_label_map.get(key)
    if target_field is None:
        # try fuzzy
        for fl, fld in field_label_map.items():
            if fl and (fl in key or key in fl):
                target_field = fld
                break
    if target_field:
        fn = target_field["field_name"]
        updated_values[fn] = str(raw_val)
        print(f"  ✓ '{key}' → field_name='{fn}' (label='{target_field['field_label']}') → '{raw_val}'")
    else:
        print(f"  ✗ '{key}' → NO MATCH (tried exact + fuzzy on labels)")

print(f"\n--- Results ---")
print(f"  Parsed & matched: {len(updated_values)}/{len(test_fields)} fields")
print(f"  Missing fields:")
for f in test_fields:
    if f["field_name"] not in updated_values:
        print(f"    - '{f['field_name']}' (label='{f['field_label']}')")

if len(updated_values) >= 10:
    print(f"\n  ✅ OK, 至少解析到 10 个字段")
else:
    print(f"\n  ❌ FAILED: 解析到的字段不足 10 个")
    print(f"     问题出在 key 匹配！JSON keys 与表单 label/name 不匹配")
    print(f"     示例: JSON key='Employee Name' vs form_label='Employee Name'")
    # Check for subtle issues
    for json_key in list(parsed_json.keys())[:3]:
        for form_label in list(field_label_map.keys())[:5]:
            if json_key == form_label:
                print(f"     EXACT MATCH FOUND: '{json_key}' == '{form_label}'")
            else:
                pass
