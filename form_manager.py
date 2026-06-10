import re
from datetime import datetime
from db import db
from ai_helper import ai_helper


class FormManager:
    def __init__(self):
        self.db = db

    def create_new_form(self, name, description=None):
        if not name or not name.strip():
            raise ValueError("表单名称不能为空")
        if len(name) > 100:
            raise ValueError("表单名称不能超过100个字符")
        return self.db.create_form(name.strip(), description.strip() if description else None)

    def add_form_field(self, form_id, field_label, field_type, is_required=False,
                       field_options=None, field_description=None, default_value=None, sort_order=None):
        if not form_id:
            raise ValueError("表单ID不能为空")
        if not field_label or not field_label.strip():
            raise ValueError("字段标签不能为空")

        field_label = field_label.strip()
        field_name = self._generate_field_name(field_label, form_id)

        existing_fields = self.db.get_fields_by_form(form_id)
        if sort_order is None:
            sort_order = len(existing_fields)

        return self.db.add_field(
            form_id=form_id,
            field_name=field_name,
            field_label=field_label,
            field_type=field_type,
            is_required=is_required,
            field_options=field_options,
            field_description=field_description,
            default_value=default_value,
            sort_order=sort_order
        )

    def _generate_field_name(self, label, form_id):
        base_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', label.strip())
        base_name = base_name.lower()
        if not base_name:
            base_name = f"field_{datetime.now().strftime('%H%M%S')}"

        existing_fields = self.db.get_fields_by_form(form_id)
        existing_names = [f["field_name"] for f in existing_fields]

        field_name = base_name
        counter = 1
        while field_name in existing_names:
            field_name = f"{base_name}_{counter}"
            counter += 1

        return field_name

    def update_form_field(self, field_id, **kwargs):
        if not field_id:
            raise ValueError("字段ID不能为空")
        return self.db.update_field(field_id, **kwargs)

    def delete_form_field(self, field_id):
        if not field_id:
            raise ValueError("字段ID不能为空")
        return self.db.delete_field(field_id)

    def get_form_with_fields(self, form_id):
        form = self.db.get_form(form_id)
        if not form:
            return None
        fields = self.db.get_fields_by_form(form_id)
        form["fields"] = fields
        return form

    def validate_submission(self, form_id, submission_data):
        errors = []
        fields = self.db.get_fields_by_form(form_id)

        if not fields:
            errors.append("当前表单没有定义任何字段")
            return errors

        for field in fields:
            field_name = field["field_name"]
            field_label = field["field_label"]
            field_type = field["field_type"]
            is_required = bool(field["is_required"])
            value = submission_data.get(field_name, "")

            value_str = str(value) if value is not None else ""

            if is_required and not value_str.strip():
                errors.append(f"【{field_label}】为必填项，请填写")
                continue

            if not value_str.strip():
                continue

            validation_error = self._validate_field_value(field, value_str)
            if validation_error:
                errors.append(validation_error)

        return errors

    def _validate_field_value(self, field, value):
        field_type = field["field_type"]
        field_label = field["field_label"]

        if field_type == "number":
            try:
                float(value)
            except (ValueError, TypeError):
                return f"【{field_label}】必须是有效的数字"

        elif field_type == "date":
            if not self._validate_date_format(value):
                return f"【{field_label}】日期格式不正确，请使用 YYYY-MM-DD 格式"

        elif field_type == "email":
            if not self._validate_email(value):
                return f"【{field_label}】邮箱格式不正确"

        elif field_type == "tel":
            if not self._validate_phone(value):
                return f"【{field_label}】电话号码格式不正确"

        elif field_type == "select":
            options = field.get("field_options") or []
            if options and value not in options:
                return f"【{field_label}】请从有效选项中选择"

        return None

    def _validate_date_format(self, value):
        patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{4}/\d{2}/\d{2}$',
            r'^\d{4}年\d{1,2}月\d{1,2}日$'
        ]
        if not any(re.match(p, value.strip()) for p in patterns):
            return False

        try:
            match = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', value)
            if match:
                year, month, day = map(int, match.groups())
                datetime(year, month, day)
                return True
        except (ValueError, TypeError):
            pass
        return False

    def _validate_email(self, value):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value.strip()))

    def _validate_phone(self, value):
        digits_only = re.sub(r'[^\d]', '', value)
        if len(digits_only) == 11 and digits_only.startswith(('13', '14', '15', '16', '17', '18', '19')):
            return True
        if 7 <= len(digits_only) <= 15:
            return True
        return False

    def save_form_submission(self, form_id, submission_data):
        errors = self.validate_submission(form_id, submission_data)
        if errors:
            raise ValueError("\n".join(errors))

        fields = self.db.get_fields_by_form(form_id)
        cleaned_data = {}
        for field in fields:
            field_name = field["field_name"]
            value = submission_data.get(field_name, "")
            if field["field_type"] == "number" and value:
                try:
                    cleaned_data[field_name] = float(value)
                except (ValueError, TypeError):
                    cleaned_data[field_name] = value
            else:
                cleaned_data[field_name] = str(value) if value is not None else ""

        return self.db.save_submission(form_id, cleaned_data)

    def get_recommendations_for_form(self, form_id):
        fields = self.db.get_fields_by_form(form_id)
        if not fields:
            return {}
        return ai_helper.batch_recommend(fields)

    def auto_fill_form(self, form_id, existing_values=None):
        fields = self.db.get_fields_by_form(form_id)
        if not fields:
            return {}
        return ai_helper.auto_fill_all(fields, existing_values)

    def optimize_single_field(self, field_id, current_value=None):
        field = self.db.get_field(field_id)
        if not field:
            raise ValueError("字段不存在")
        return ai_helper.optimize_field(field, current_value)

    def get_field_suggestions(self, field_id, count=3):
        field = self.db.get_field(field_id)
        if not field:
            raise ValueError("字段不存在")
        return ai_helper.get_suggestions(field, count)

    # ============================================================
    #  多轮对话式一键填报
    # ============================================================

    def start_conversation_fill(self, form_id, existing_values=None):
        form = self.db.get_form(form_id)
        if not form:
            raise ValueError("表单不存在")
        fields = self.db.get_fields_by_form(form_id)
        if not fields:
            raise ValueError("该表单暂无可填字段")
        ai_message, values, done, new_messages = ai_helper.start_conversation_fill(
            fields, form_name=form.get("name"), existing_values=existing_values
        )
        return {
            "form": form,
            "fields": fields,
            "ai_message": ai_message,
            "values": values,
            "done": done,
            "messages": new_messages,
        }

    def continue_conversation_fill(self, form_id, messages, user_input, existing_values=None):
        fields = self.db.get_fields_by_form(form_id)
        if not fields:
            raise ValueError("该表单暂无可填字段")
        ai_message, values, done, new_messages = ai_helper.continue_conversation_fill(
            messages, fields, user_input, existing_values=existing_values
        )
        return {
            "fields": fields,
            "ai_message": ai_message,
            "values": values,
            "done": done,
            "messages": new_messages,
        }

    def finalize_conversation_fill(self, form_id, values):
        fields = self.db.get_fields_by_form(form_id)
        if not fields:
            raise ValueError("该表单暂无可填字段")
        return ai_helper.finalize_conversation_fill(fields, values)

    def save_form_as_template(self, form_id, template_name):
        if not template_name or not template_name.strip():
            raise ValueError("模板名称不能为空")

        form = self.db.get_form(form_id)
        if not form:
            raise ValueError("表单不存在")

        fields = self.db.get_fields_by_form(form_id)
        return self.db.save_template(template_name.strip(), form, fields)

    def load_template_to_new_form(self, template_id, new_form_name=None):
        if not template_id:
            raise ValueError("模板ID不能为空")
        return self.db.load_template_to_form(template_id, new_form_name)

    def export_form_data_as_dict(self, form_id):
        form = self.db.get_form(form_id)
        if not form:
            raise ValueError("表单不存在")

        fields = self.db.get_fields_by_form(form_id)
        submissions = self.db.get_submissions_by_form(form_id)

        return {
            "form_info": form,
            "fields": fields,
            "submissions": submissions,
            "submission_count": len(submissions)
        }

    def get_form_statistics(self, form_id):
        submissions = self.db.get_submissions_by_form(form_id)
        fields = self.db.get_fields_by_form(form_id)

        stats = {
            "total_submissions": len(submissions),
            "total_fields": len(fields),
            "required_fields": sum(1 for f in fields if f["is_required"]),
            "field_types": {}
        }

        for field in fields:
            ft = field["field_type"]
            stats["field_types"][ft] = stats["field_types"].get(ft, 0) + 1

        if submissions:
            latest = submissions[0]
            stats["last_submission_time"] = latest["created_at"]
        else:
            stats["last_submission_time"] = None

        return stats

    def search_forms(self, keyword):
        if not keyword or not keyword.strip():
            return self.db.get_all_forms()
        keyword = keyword.strip().lower()
        all_forms = self.db.get_all_forms()
        return [
            f for f in all_forms
            if keyword in (f.get("name") or "").lower()
            or keyword in (f.get("description") or "").lower()
        ]

    def move_field_order(self, field_id, direction):
        field = self.db.get_field(field_id)
        if not field:
            return False

        form_id = field["form_id"]
        current_order = field["sort_order"]
        fields = self.db.get_fields_by_form(form_id)

        if direction == "up" and current_order > 0:
            target_order = current_order - 1
            for f in fields:
                if f["sort_order"] == target_order and f["id"] != field_id:
                    self.db.update_field(f["id"], sort_order=current_order)
                    break
            self.db.update_field(field_id, sort_order=target_order)
            return True
        elif direction == "down" and current_order < len(fields) - 1:
            target_order = current_order + 1
            for f in fields:
                if f["sort_order"] == target_order and f["id"] != field_id:
                    self.db.update_field(f["id"], sort_order=current_order)
                    break
            self.db.update_field(field_id, sort_order=target_order)
            return True
        return False

    def duplicate_form(self, form_id, new_name=None):
        form = self.db.get_form(form_id)
        if not form:
            raise ValueError("表单不存在")

        fields = self.db.get_fields_by_form(form_id)
        new_form_name = new_name or f"{form['name']} (副本)"
        new_form_id = self.db.create_form(new_form_name, form.get("description"))

        for field in fields:
            self.db.add_field(
                form_id=new_form_id,
                field_name=field["field_name"],
                field_label=field["field_label"],
                field_type=field["field_type"],
                is_required=bool(field["is_required"]),
                field_options=field.get("field_options"),
                field_description=field.get("field_description"),
                default_value=field.get("default_value"),
                sort_order=field["sort_order"]
            )

        return new_form_id


form_manager = FormManager()
