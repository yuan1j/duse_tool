import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def init_database():
    print("=" * 60)
    print("  通用数据填报系统 - 数据库初始化")
    print("=" * 60)

    if os.path.exists("data_entry_system.db"):
        print("\n⚠️  检测到已存在的数据库文件")
        choice = input("是否删除并重新创建？(y/n): ").strip().lower()
        if choice == 'y':
            os.remove("data_entry_system.db")
            print("✅ 已删除旧数据库")
        else:
            print("ℹ️  保留现有数据库，退出初始化")
            return

    from db import DatabaseManager, db
    from form_manager import form_manager

    global db, form_manager
    db = DatabaseManager()
    form_manager.db = db

    print("\n📝 创建示例表单...")

    form1_id = form_manager.create_new_form(
        name="员工信息登记表",
        description="用于新员工入职时填写基本信息，包括个人资料、联系方式等"
    )
    print(f"  ✅ 已创建表单【员工信息登记表】 ID: {form1_id}")

    fields_1 = [
        ("姓名", "text", True, "请填写真实姓名", None),
        ("性别", "select", True, "请选择性别", "男,女"),
        ("出生日期", "date", True, "格式：YYYY-MM-DD", None),
        ("身份证号", "text", True, "18位身份证号码", None),
        ("手机号码", "tel", True, "11位手机号码", None),
        ("电子邮箱", "email", True, "常用工作邮箱", None),
        ("入职日期", "date", True, "格式：YYYY-MM-DD", None),
        ("所属部门", "select", True, "请选择所属部门", "研发部,市场部,销售部,人力资源部,财务部,运营部"),
        ("职位", "text", True, "请填写职位名称", None),
        ("紧急联系人", "text", False, "紧急联系人姓名", None),
        ("紧急联系电话", "tel", False, "紧急联系人电话", None),
        ("备注说明", "textarea", False, "其他需要说明的事项", None)
    ]

    for label, ftype, required, desc, options in fields_1:
        opt_list = [o.strip() for o in options.split(",")] if options else None
        db.add_field(
            form_id=form1_id,
            field_name=label,
            field_label=label,
            field_type=ftype,
            is_required=required,
            field_options=opt_list,
            field_description=desc,
            sort_order=fields_1.index((label, ftype, required, desc, options))
        )
    print(f"  ✅ 已添加 {len(fields_1)} 个字段")

    form2_id = form_manager.create_new_form(
        name="日常考勤打卡表",
        description="用于日常考勤记录，包含工作时间、工作内容等信息"
    )
    print(f"  ✅ 已创建表单【日常考勤打卡表】 ID: {form2_id}")

    fields_2 = [
        ("日期", "date", True, "打卡日期，格式：YYYY-MM-DD", None),
        ("姓名", "text", True, "请填写姓名", None),
        ("所属部门", "select", True, "请选择部门", "研发部,市场部,销售部,人力资源部,财务部,运营部"),
        ("上班时间", "text", True, "格式：HH:MM", "09:00"),
        ("下班时间", "text", False, "格式：HH:MM", "18:00"),
        ("工作内容", "textarea", True, "今日主要工作内容和完成情况", None),
        ("工作时长(小时)", "number", False, "实际工作小时数", None),
        ("加班时长(小时)", "number", False, "加班小时数", "0"),
        ("工作状态", "select", True, "今日工作状态", "正常,请假,出差,外勤,其他"),
        ("备注", "textarea", False, "其他需要说明的事项", None)
    ]

    for label, ftype, required, desc, default in fields_2:
        db.add_field(
            form_id=form2_id,
            field_name=label,
            field_label=label,
            field_type=ftype,
            is_required=required,
            field_description=desc,
            default_value=default,
            sort_order=fields_2.index((label, ftype, required, desc, default))
        )
    print(f"  ✅ 已添加 {len(fields_2)} 个字段")

    form3_id = form_manager.create_new_form(
        name="项目进度周报",
        description="用于每周项目进度汇报，包含项目信息、进度情况、问题风险等"
    )
    print(f"  ✅ 已创建表单【项目进度周报】 ID: {form3_id}")

    fields_3 = [
        ("项目名称", "text", True, "请填写项目名称", None),
        ("项目编号", "text", False, "项目编号（如有）", None),
        ("汇报周期", "text", True, "例如：第12周 / 2024-03-18至2024-03-24", None),
        ("负责人", "text", True, "项目负责人姓名", None),
        ("本周完成进度(%)", "number", True, "0-100之间的数字", None),
        ("本周主要工作", "textarea", True, "详细描述本周完成的主要工作内容", None),
        ("下周工作计划", "textarea", True, "下周计划完成的工作事项", None),
        ("问题与风险", "textarea", False, "当前遇到的问题或潜在风险", None),
        ("需要的支持", "textarea", False, "需要上级或其他部门提供的支持", None),
        ("备注说明", "textarea", False, "其他补充说明", None)
    ]

    for label, ftype, required, desc, default in fields_3:
        db.add_field(
            form_id=form3_id,
            field_name=label,
            field_label=label,
            field_type=ftype,
            is_required=required,
            field_description=desc,
            default_value=default if default else None,
            sort_order=fields_3.index((label, ftype, required, desc, default))
        )
    print(f"  ✅ 已添加 {len(fields_3)} 个字段")

    print("\n📦 保存表单模板...")
    db.save_template(
        template_name="员工信息登记表模板",
        form_data={"name": "员工信息登记表", "description": "标准员工信息表"},
        fields_data=[{"field_label": f[0], "field_type": f[1], "is_required": f[2],
                      "field_description": f[3], "field_options": [o.strip() for o in f[4].split(",")] if f[4] else None}
                     for f in fields_1]
    )
    print("  ✅ 已保存【员工信息登记表模板】")

    db.save_template(
        template_name="考勤打卡模板",
        form_data={"name": "日常考勤打卡表", "description": "标准考勤表"},
        fields_data=[{"field_label": f[0], "field_type": f[1], "is_required": f[2],
                      "field_description": f[3]} for f in fields_2]
    )
    print("  ✅ 已保存【考勤打卡模板】")

    print("\n" + "=" * 60)
    print("  ✅ 数据库初始化完成！")
    print("=" * 60)
    print(f"\n📊 统计信息:")
    all_forms = db.get_all_forms()
    print(f"  表单总数: {len(all_forms)}")
    for f in all_forms:
        fields = db.get_fields_by_form(f["id"])
        submissions = db.get_submissions_by_form(f["id"])
        print(f"    - {f['name']}: {len(fields)}字段, {len(submissions)}条记录")

    all_templates = db.get_all_templates()
    print(f"  模板总数: {len(all_templates)}")

    print("\n🚀 现在可以运行以下命令启动系统:")
    print("   python app.py")
    print("   然后在浏览器中打开: http://localhost:7860")
    print("=" * 60)


if __name__ == "__main__":
    init_database()
