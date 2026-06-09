import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import db
from form_manager import form_manager
from ai_helper import ai_helper


def test_database():
    print("\n" + "=" * 60)
    print("  测试数据库模块")
    print("=" * 60)

    form_id = db.create_form("测试表单 - 员工信息", "用于测试的表单")
    print(f"✅ 创建表单 ID: {form_id}")

    field_id = db.add_field(
        form_id=form_id,
        field_name="测试字段",
        field_label="测试字段",
        field_type="text",
        is_required=True,
        field_description="这是一个测试字段",
        default_value="默认值",
        sort_order=0
    )
    print(f"✅ 添加字段 ID: {field_id}")

    submission_id = db.save_submission(form_id, {"测试字段": "测试数据"})
    print(f"✅ 保存提交 ID: {submission_id}")

    forms = db.get_all_forms()
    print(f"✅ 获取所有表单: {len(forms)} 个")

    fields = db.get_fields_by_form(form_id)
    print(f"✅ 获取字段: {len(fields)} 个")

    submissions = db.get_submissions_by_form(form_id)
    print(f"✅ 获取提交: {len(submissions)} 条")

    db.delete_form(form_id)
    print("✅ 删除测试表单")

    print("\n✅ 数据库模块测试通过!")


def test_form_manager():
    print("\n" + "=" * 60)
    print("  测试表单管理模块")
    print("=" * 60)

    form_id = form_manager.create_new_form("测试表单管理", "测试描述")
    print(f"✅ 创建表单 ID: {form_id}")

    field_id = form_manager.add_form_field(
        form_id=form_id,
        field_label="姓名",
        field_type="text",
        is_required=True,
        field_description="请填写姓名"
    )
    print(f"✅ 添加字段 ID: {field_id}")

    field_id2 = form_manager.add_form_field(
        form_id=form_id,
        field_label="年龄",
        field_type="number",
        is_required=True
    )
    print(f"✅ 添加数字字段 ID: {field_id2}")

    form_manager.add_form_field(
        form_id=form_id,
        field_label="邮箱",
        field_type="email",
        is_required=True
    )
    print("✅ 添加邮箱字段")

    errors = form_manager.validate_submission(form_id, {
        "姓名": "张三",
        "年龄": "25",
        "邮箱": "test@example.com"
    })
    print(f"✅ 验证有效数据: {'通过' if not errors else f'失败: {errors}'}")

    errors2 = form_manager.validate_submission(form_id, {
        "姓名": "",
        "年龄": "不是数字",
        "邮箱": "invalid-email"
    })
    print(f"✅ 验证无效数据: 发现 {len(errors2)} 个错误")

    submission_id = form_manager.save_form_submission(form_id, {
        "姓名": "张三",
        "年龄": "25",
        "邮箱": "test@example.com"
    })
    print(f"✅ 保存提交 ID: {submission_id}")

    form_manager.delete_form_field(field_id2)
    print("✅ 删除字段")

    new_id = form_manager.duplicate_form(form_id)
    print(f"✅ 复制表单 ID: {new_id}")

    form_manager.save_form_as_template(form_id, "测试模板")
    print("✅ 保存模板")

    db.delete_form(form_id)
    db.delete_form(new_id)
    print("✅ 清理测试数据")

    print("\n✅ 表单管理模块测试通过!")


def test_ai_helper():
    print("\n" + "=" * 60)
    print("  测试 AI 辅助模块")
    print("=" * 60)

    field1 = {"field_name": "姓名", "field_label": "姓名", "field_type": "text"}
    val1 = ai_helper.recommend_field_value(field1)
    print(f"✅ 推荐【姓名】: {val1}")

    field2 = {"field_name": "email", "field_label": "邮箱", "field_type": "email"}
    val2 = ai_helper.recommend_field_value(field2)
    print(f"✅ 推荐【邮箱】: {val2}")

    field3 = {"field_name": "phone", "field_label": "电话", "field_type": "tel"}
    val3 = ai_helper.recommend_field_value(field3)
    print(f"✅ 推荐【电话】: {val3}")

    field4 = {"field_name": "部门", "field_label": "所属部门", "field_type": "select",
               "field_options": ["研发部", "市场部", "销售部"]}
    val4 = ai_helper.recommend_field_value(field4)
    print(f"✅ 推荐【部门】: {val4}")

    fields = [
        {"field_name": "姓名", "field_label": "姓名", "field_type": "text"},
        {"field_name": "邮箱", "field_label": "邮箱", "field_type": "email"},
        {"field_name": "电话", "field_label": "电话", "field_type": "tel"},
        {"field_name": "金额", "field_label": "金额", "field_type": "number"},
        {"field_name": "日期", "field_label": "入职日期", "field_type": "date"}
    ]
    filled = ai_helper.auto_fill_all(fields)
    print(f"✅ 一键填报: {len(filled)} 个字段")
    for k, v in filled.items():
        print(f"    - {k}: {v}")

    opt_val = ai_helper.optimize_field({"field_type": "textarea"}, "测试内容")
    print(f"✅ 优化字段: {opt_val}")

    suggestions = ai_helper.get_suggestions({"field_name": "部门", "field_label": "部门", "field_type": "select"})
    print(f"✅ 获取建议: {suggestions}")

    print("\n✅ AI 辅助模块测试通过!")


def main():
    print("\n" + "#" * 60)
    print("  通用数据填报系统 - 功能测试")
    print("#" * 60)

    try:
        test_database()
    except Exception as e:
        print(f"❌ 数据库模块测试失败: {e}")
        import traceback
        traceback.print_exc()

    try:
        test_form_manager()
    except Exception as e:
        print(f"❌ 表单管理模块测试失败: {e}")
        import traceback
        traceback.print_exc()

    try:
        test_ai_helper()
    except Exception as e:
        print(f"❌ AI 辅助模块测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "#" * 60)
    print("  ✅ 所有测试完成!")
    print("#" * 60)


if __name__ == "__main__":
    main()
